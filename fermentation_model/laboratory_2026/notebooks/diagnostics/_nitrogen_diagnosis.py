"""Chemical nitrogen diagnosis, with fixed-parameter full-horizon scenarios.

No gas data, optimizer or Kalman filter. The model RHS and pulse convention are
the official ones. A constant observation background is an explicit hypothesis.
"""
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from shared import run_new_must_glycerol_estimability_doe as model

CONFIG = dict(grid_h=.25, rtol=2e-9, atol=2e-11, max_step_h=.5,
              after_event_h=1e-5, depletion_g_l=.005)
SCENARIOS = {
    'referencia': ('base', 1.),
    'X0_x0.5': ('X0', .5), 'X0_x2': ('X0', 2.),
    'qN_x0.5': ('qN', .5), 'qN_x2': ('qN', 2.),
    'crecimiento_x0.8': ('growth', .8), 'crecimiento_x1.2': ('growth', 1.2),
    'sN_x0.5': ('sN', .5), 'sN_x2': ('sN', 2.),
    'T_menos2C': ('T', -2.), 'T_mas2C': ('T', 2.),
    'remanente_10': ('background', .010),
    'remanente_20': ('background', .020),
    'remanente_30': ('background', .030),
}


def load_recent_batches(chem, temperature_path, t0, fermenters, pulses):
    """Reproduce the raw-temperature convention without opening any gas file."""
    parts = []
    for chunk in pd.read_csv(temperature_path, usecols=['timestamp','fermentador','T'],
                             chunksize=500_000, low_memory=False):
        stamp = pd.to_datetime(chunk.timestamp, errors='coerce')
        keep = stamp.between(t0-pd.Timedelta(hours=6), t0+pd.Timedelta(hours=170))
        if keep.any():
            part = chunk.loc[keep].copy()
            part['timestamp'] = stamp.loc[keep]
            part['T'] = pd.to_numeric(part['T'], errors='coerce')
            parts.append(part)
    temperature = pd.concat(parts, ignore_index=True)
    batches, audit = {}, []
    cols = dict(N='N_kg_m3',G='G_g_l',F='F_g_l',E='E_g_l',Gly='Gly_g_l',
                X='X_viable_g_l',Xd='Xd_g_l')
    for lab, fermenter in fermenters.items():
        measured = chem.loc[chem.lab.eq(lab) & ~chem.is_NUT].sort_values('t_h')
        first = measured.loc[measured['sample'].eq('1')].iloc[0]
        horizon = float(measured.t_h.max())
        time = np.unique(np.r_[0.,measured.t_h.to_numpy(float),horizon])
        temp = temperature.loc[temperature.fermentador.eq(fermenter)].dropna(subset=['T']).sort_values('timestamp')
        th = (temp.timestamp-t0).dt.total_seconds().to_numpy()/3600.
        initials = {s:float(first[c]) for s,c in cols.items()}
        # Preserve the total-count initial X proxy used by the existing recent notebooks.
        initials['X'] = float(first.X_total_g_l)
        obs = {s:np.array([float(measured.loc[measured.t_h.eq(t),c].iloc[0])
                          if measured.t_h.eq(t).any() else np.nan for t in time])
               for s,c in cols.items()}
        batches[lab] = model.BatchData(medium='natural',batch=lab,time=time,
            temperature_c=np.interp(time,th,temp['T'].to_numpy(float)),initials=initials,
            observations=obs,pulses={**{s:() for s in model.INPUT_CHANNELS},'N':tuple(pulses[lab])})
        # Retain the same quarter-hour raw-temperature interpolation as the prior diagnostic.
        dense = make_grid(batches[lab])
        batches[lab] = replace(batches[lab],time=dense,
            temperature_c=np.interp(dense,th,temp['T'].to_numpy(float)),
            observations={s:np.array([obs[s][np.flatnonzero(time==t)[0]] if t in time else np.nan
                                      for t in dense]) for s in model.STATE_NAMES})
        audit.append(dict(lab=lab,cohort='reciente',start_h=0.,end_h=horizon,
            initial_sample_original_h=float(first.sample_t_h),
            X0_source='Oculyze total crudo x 0.03; proxy incierto',
            temperature_hold_after_h=max(0.,horizon-float(th.max())),
            pulses=repr(pulses[lab]),**initials))
    return batches,pd.DataFrame(audit)


def make_grid(batch):
    t0,tf = float(batch.time[0]),float(batch.time[-1])
    events = [t for values in batch.pulses.values() for t,d in values if t0<=t<=tf and d>0]
    after = [t+CONFIG['after_event_h'] for t in events if t+CONFIG['after_event_h']<tf]
    dense = np.arange(t0,tf+CONFIG['grid_h']/2.,CONFIG['grid_h'])
    return np.unique(np.r_[batch.time,dense[dense<=tf],events,after,tf])


def integrate(batch,theta,time):
    """Event-exact integration of the official RHS, avoiding coarse repeated solves."""
    time = np.asarray(time,float)
    state = model.initial_vector(batch).copy()
    offset_index = [model.STATE_NAMES.index(s) for s in ('Xd','Gly')]
    offsets = state[offset_index].copy()
    state[offset_index] = 0.
    events = model._pulse_events(batch,float(time[0]),float(time[-1]))
    records = {float(time[0]):state.copy()}
    current = float(time[0]); jump_error=0.
    if current in events:
        state += events[current]
    for boundary in sorted({float(time[-1]), *[t for t in events if t>current]}):
        if boundary<=current: continue
        requested = time[(time>current)&(time<=boundary)]
        sol = solve_ivp(lambda t,y:model.rhs(t,y,theta,batch),(current,boundary),state,
            t_eval=np.unique(np.r_[requested,boundary]),method='LSODA',
            rtol=CONFIG['rtol'],atol=CONFIG['atol'],max_step=CONFIG['max_step_h'])
        if not sol.success: raise RuntimeError(sol.message)
        records.update({float(t):y.copy() for t,y in zip(sol.t,sol.y.T)})
        current=boundary;state=sol.y[:,-1].copy()
        if boundary in events:
            before=state.copy();state+=events[boundary]
            jump_error=max(jump_error,float(np.max(np.abs(state-before-events[boundary]))))
    values=np.vstack([records[float(t)] for t in time]);values[:,offset_index]+=offsets
    assert np.isfinite(values).all(), (batch.batch,'nonfinite state')
    assert jump_error<1e-12
    raw_min={s:float(values[:,i].min()) for i,s in enumerate(model.STATE_NAMES)}
    raw_max={s:float(values[:,i].max()) for i,s in enumerate(model.STATE_NAMES)}
    clipped=values.copy()
    for i,s in enumerate(model.STATE_NAMES):
        clipped[:,i]=np.clip(clipped[:,i],*model.STATE_BOUNDS[s])
    out=pd.DataFrame(clipped,index=time,columns=model.STATE_NAMES)
    out.attrs.update(jump_error=jump_error,raw_min=raw_min,raw_max=raw_max,
        physically_admissible=all(raw_min[s]>=model.STATE_BOUNDS[s][0]-1e-6 and
            raw_max[s]<=model.STATE_BOUNDS[s][1]+1e-6 for s in model.STATE_NAMES))
    return out


def variant(batch,theta,name):
    kind,value=SCENARIOS[name];th=dict(theta);bt=batch;background=0.
    if kind=='X0': bt=replace(batch,initials={**batch.initials,'X':batch.initials['X']*value})
    elif kind in ('qN','sN'): th[kind]*=value
    elif kind=='growth':
        for key in ('mu0','qN','sN'): th[key]*=value
        assert np.isclose(th['qN']/th['mu0'],theta['qN']/theta['mu0'])
        assert np.isclose(th['mu0']/th['sN'],theta['mu0']/theta['sN'])
    elif kind=='T': bt=replace(batch,temperature_c=batch.temperature_c+value)
    elif kind=='background':
        background=value
        assert batch.initials['N']>=background
        bt=replace(batch,initials={**batch.initials,'N':batch.initials['N']-background})
    return bt,th,background


def run(batch,theta,name):
    bt,th,background=variant(batch,theta,name)
    curve=integrate(bt,th,make_grid(batch))
    curve['GF']=curve.G+curve.F
    curve['N_pred']=curve.N+background
    curve['T_C']=np.interp(curve.index,bt.time,bt.temperature_c)
    terms=[model.kinetic_terms(th,temp,row.X,row.N,row.G,row.F,row.E)
           for temp,row in zip(curve.T_C,curve.itertuples())]
    curve['uptake_mg_l_h']=[1000*th['qN']*v['growth_factor']*x for v,x in zip(terms,curve.X)]
    curve['mu_h']=[v['mu'] for v in terms]
    kelvin=curve.T_C.to_numpy()+273.15
    kn=th['mu0']/th['sN']*np.exp(model.FIXED_CONSTANTS['EaKn']*(kelvin-293.15)/
        (293.15*model.FIXED_CONSTANTS['R']*kelvin))
    curve['n_lim']=curve.N.to_numpy()/(curve.N.to_numpy()+kn+1e-8)
    curve['KN_mg_l']=1000*kn
    dose=np.array([sum(d for t,d in bt.pulses['N'] if t<ti-1e-9) for ti in curve.index])
    inventory=curve.N+th['qN']/th['mu0']*(curve.X+curve.Xd)-dose
    drift=float(np.max(np.abs(inventory-inventory.iloc[0])))
    assert drift<2e-6,(batch.batch,name,drift)
    curve.attrs.update(background=background,theta=th,batch=bt,inventory_drift=drift)
    return curve


def observation_table(batches,chem):
    rows=[]
    for lab,batch in batches.items():
        recent=lab in set(chem.lab)
        for s in model.STATE_NAMES:
            for t,y in zip(batch.time,batch.observations[s]):
                if not np.isfinite(y): continue
                rows.append(dict(lab=lab,cohort='reciente' if recent else 'historico',
                    state=s,t_h=float(t),observed=float(y),initial_anchor=bool(t==batch.time[0]),
                    validation_eligible=not (recent and s in ('X','Xd')),
                    sigma=float(model.sigma_for_state(s,y)),component='model_observation'))
        if recent:
            measured=chem.loc[chem.lab.eq(lab)&~chem.is_NUT&chem.GF_g_l.notna()]
            for row in measured.itertuples():
                rows.append(dict(lab=lab,cohort='reciente',state='GF',t_h=float(row.t_h),
                    observed=float(row.GF_g_l),initial_anchor=bool(row.is_initial),
                    validation_eligible=True,sigma=5.,component='direct_GF_assay'))
        else:
            keep=np.isfinite(batch.observations['G'])&np.isfinite(batch.observations['F'])
            for t,g,f in zip(batch.time[keep],batch.observations['G'][keep],batch.observations['F'][keep]):
                rows.append(dict(lab=lab,cohort='historico',state='GF',t_h=float(t),observed=float(g+f),
                    initial_anchor=bool(t==batch.time[0]),validation_eligible=True,
                    sigma=5.,component='sum_of_G_F_not_independent'))
    return pd.DataFrame(rows)


def score(curve,points,pulse):
    out=[]
    for state,group in points.loc[~points.initial_anchor].groupby('state'):
        pred=np.interp(group.t_h,curve.index,curve.N_pred if state=='N' else curve[state])
        for period,keep in [('completo',np.ones(len(group),bool)),
                            ('pre_pulso',group.t_h.to_numpy()<=pulse),
                            ('post_pulso',group.t_h.to_numpy()>pulse)]:
            if not keep.any(): continue
            y=group.observed.to_numpy()[keep];p=pred[keep];err=p-y
            sigma=group.sigma.to_numpy()[keep]
            out.append(dict(state=state,period=period,n=int(keep.sum()),
                RMSE=float(np.sqrt(np.mean(err**2))),bias=float(err.mean()),
                WSSE=float(np.sum((err/sigma)**2)),
                eligible=bool(group.validation_eligible.all())))
    return out


def first_crossing(time,values,threshold=.005):
    hit=np.flatnonzero(np.asarray(values)<=threshold)
    return float(np.asarray(time)[hit[0]]) if len(hit) else np.nan


def observed_crossing(group,pulse,threshold=.005):
    """A sampling bracket, never an inferred exact depletion time."""
    data=group.loc[group.state.eq('N')&(group.t_h<=pulse)].sort_values('t_h')
    below=data.loc[data.observed<=threshold]
    if below.empty:
        return dict(observed_status='no cruce observado antes del pulso',
                    obs_lower_h=np.nan,obs_upper_h=np.nan)
    first=below.iloc[0];above=data.loc[(data.t_h<first.t_h)&(data.observed>threshold)]
    return dict(observed_status='cruce acotado por muestras' if len(above) else 'primera muestra bajo umbral',
                obs_lower_h=float(above.t_h.iloc[-1]) if len(above) else np.nan,
                obs_upper_h=float(first.t_h))


def interpolate_post_action(curve,targets,schedule,column='N_pred'):
    tt=curve.index.to_numpy(float);yy=curve[column].to_numpy(float);targets=np.asarray(targets,float)
    result=np.interp(targets,tt,yy)
    for event,dose in schedule:
        hit=np.flatnonzero(np.isclose(tt,event,atol=1e-9,rtol=0))
        if not len(hit): continue
        i=int(hit[0]);post=yy[i]+dose
        if i+1<len(tt):
            keep=(targets>=event)&(targets<=tt[i+1])
            result[keep]=post+(yy[i+1]-post)*(targets[keep]-event)/(tt[i+1]-event)
    return result


def analytical_components(historical_data,chem):
    old=historical_data.loc[historical_data.batch.isin([f'LAB{i:03d}' for i in range(4,13)])].copy()
    a=pd.DataFrame(dict(lab=old.batch,t_h=old.time_h,PAN=old.PAN_mg_l,
        ammonia_raw=old.NH4_mg_l,ammonia_N=.82*old.NH4_mg_l,
        YAN=old.YAN_mg_l,cohort='historico',conversion=.82,
        sample=old.sample_id,source=old.source_file,is_NUT=False,time_provisional=False))
    b=pd.DataFrame(dict(lab=chem.lab,t_h=chem.t_h,PAN=chem.PAN_mg_l,
        ammonia_raw=chem.NH3_raw_mg_l,ammonia_N=.823*chem.NH3_censored_mg_l,
        YAN=chem.YAN_mg_l,cohort='reciente',conversion=.823,
        sample=chem['sample'],source='Y15 exports + offline Excel',is_NUT=chem.is_NUT,
        time_provisional=chem.time_provisional))
    out=pd.concat([a,b],ignore_index=True)
    out['sum_check']=out.YAN-out.PAN-out.ammonia_N
    out['factor_change_082_to_0823_mg_l']=.003*out.ammonia_raw
    return out


def observed_balance(points,batches):
    rows=[]
    for lab,batch in batches.items():
        n=points.loc[points.lab.eq(lab)&points.state.eq('N')].sort_values('t_h')
        for a,b in zip(list(n.itertuples())[:-1],list(n.itertuples())[1:]):
            added=sum(d for t,d in batch.pulses['N'] if a.t_h<=t<b.t_h-1e-9)
            # Sample-before-action: an event exactly at a is included, at b excluded.
            excess=b.observed-a.observed-added
            rows.append(dict(lab=lab,cohort=a.cohort,t_a_h=a.t_h,t_b_h=b.t_h,
                N_a_mg_l=1000*a.observed,N_b_mg_l=1000*b.observed,
                added_mg_l=1000*added,excess_mg_l=1000*excess,
                apparent_net_consumption_mg_l_h=1000*(a.observed+added-b.observed)/(b.t_h-a.t_h)))
    return pd.DataFrame(rows)


def biomass_balance(points,batches,theta):
    rows=[]
    for lab,batch in batches.items():
        data=points.loc[points.lab.eq(lab)&points.state.isin(['N','X','Xd'])]
        wide=data.pivot(index='t_h',columns='state',values='observed').dropna(subset=['N','X','Xd'])
        if len(wide)<2: continue
        first=wide.iloc[0];t0=float(wide.index[0]);ratio=theta['qN']/theta['mu0']
        for t,row in wide.iterrows():
            added=sum(d for event,d in batch.pulses['N'] if t0<=event<t-1e-9)
            consumption=float(first.N+added-row.N)
            dm=float(row.X+row.Xd-first.X-first.Xd)
            rows.append(dict(lab=lab,cohort='reciente' if lab in ('LAB019','LAB020','LAB021') else 'historico',
                t_h=float(t),first_pair_h=t0,net_N_consumed_mg_l=1000*consumption,
                delta_total_biomass_g_l=dm,model_required_N_mg_l=1000*ratio*dm,
                closure_mg_l=1000*(consumption-ratio*dm),
                validation_eligible=lab not in ('LAB019','LAB020','LAB021')))
    return pd.DataFrame(rows)
