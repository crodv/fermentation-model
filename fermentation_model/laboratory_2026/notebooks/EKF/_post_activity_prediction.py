"""Fixed-parameter, full-horizon restarts for the pre-EKF diagnostic.

No optimizer, parameter changes, automatic lag model or Kalman filter.
The two nitrogen counterfactuals and their absolute event clock are retained.
"""
from dataclasses import replace

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp

from shared import run_new_must_glycerol_estimability_doe as base
from shared import run_secondary_joint_campaign_doe as joint
from laboratory_2026 import run_co2_matrix_cross_validation_2026 as co2_cross

CONFIG = dict(rtol=2e-9, atol=2e-11, max_step_h=.5, grid_h=.25)
CHANNELS = dict(N='N_kg_m3', G='G_g_l', F='F_g_l', GF='GF_g_l',
                E='E_g_l', Gly='Gly_g_l')


def integrate_core(batch, theta, time):
    """Official RHS; exact sample-before-action jumps; no repeated solvers per grid point."""
    time = np.asarray(time, float)
    state = base.initial_vector(batch).copy()
    offsets_idx = [base.STATE_NAMES.index(s) for s in ('Xd', 'Gly')]
    offsets = state[offsets_idx].copy()
    state[offsets_idx] = 0.
    events = base._pulse_events(batch, time[0], time[-1])
    records = {float(time[0]): state.copy()}
    current = float(time[0])
    if current in events:
        state += events[current]
    jump_error = 0.
    for boundary in sorted({float(time[-1]), *[e for e in events if e > current]}):
        if boundary <= current:
            continue
        requested = time[(time > current) & (time <= boundary)]
        sol = solve_ivp(lambda t, y: base.rhs(t, y, theta, batch),
            (current, boundary), state, t_eval=np.unique(np.r_[requested, boundary]),
            method='LSODA', rtol=CONFIG['rtol'], atol=CONFIG['atol'],
            max_step=CONFIG['max_step_h'])
        if not sol.success:
            raise RuntimeError(sol.message)
        records.update({float(t): y.copy() for t, y in zip(sol.t, sol.y.T)})
        state = sol.y[:, -1].copy()
        current = boundary
        if boundary in events:
            before = state.copy()
            state += events[boundary]
            jump_error = max(jump_error, float(np.max(np.abs(state-before-events[boundary]))))
    values = np.vstack([records[float(t)] for t in time])
    values[:, offsets_idx] += offsets
    assert np.isfinite(values).all() and values.min() > -1e-7
    assert jump_error < 1e-12
    result = pd.DataFrame(np.maximum(values, 0.), index=time, columns=base.STATE_NAMES)
    result.attrs['jump_error'] = jump_error
    return result


def production(theta, batch, core):
    out = []
    for t, row in core.iterrows():
        terms = base.kinetic_terms(theta, base.temperature_at(batch, t),
            row.X, row.N, row.G, row.F, row.E)
        out.append(joint.CO2_G_PER_G_ETHANOL * (terms['beta_g']+terms['beta_f']) * row.X)
    return np.asarray(out)


def csat(batch, core, params):
    temp = np.interp(core.index, batch.time, batch.temperature_c)
    return (params['CO2sat_scale'] * 1.69 * np.exp(-.032*(temp-20.))
            * np.exp(.0016*core.E.to_numpy())
            * np.exp(-.0012*(core.G+core.F).to_numpy()))


def release(cd, saturation, params):
    return params['kCO2_release_h'] * cd * (.05+.95*cd/max(cd+saturation, 1e-12))


def dissolved_from_flow(flow, saturation, params):
    """Invert the frozen observation equation, using a past-flow summary only."""
    r = max(float(flow), 0.) / (params['matrix_gain']*params['kCO2_release_h'])
    b = .05*saturation-r
    return float((np.sqrt(b*b+4*r*saturation)-b)/2.)


def pulse_history(time, schedule, params):
    """Historical grid_max is evaluated on the ORIGINAL full grid, never restarted."""
    ramp = (np.clip((time-schedule[0][0])/params['pulse_t_rise_h'], 0., 1.)
            if schedule else np.zeros(len(time)))
    multiplier = np.ones(len(time))
    for event, dose in schedule:
        u = np.maximum(time-event, 0.)
        raw = (1.-np.exp(-u/params['tau_rise_h']))*np.exp(-u/params['tau_decay_h'])
        peak = raw.max()
        if peak > 0:
            multiplier += params['A']*dose/params['N_ref_g_l']*raw/peak
    return ramp, multiplier


def finish(batch, theta, core, core0, params, gate, ramp, multiplier, cd0, oxygen0):
    time = core.index.to_numpy(float)
    qn, q0 = production(theta, batch, core), production(theta, batch, core0)
    biomass = np.maximum(core0.X.to_numpy()+ramp*(core.X-core0.X).to_numpy(), 0.)
    oxygen = np.zeros(len(time))
    oxygen[0] = oxygen0
    for i, dt in enumerate(np.diff(time)):
        uptake = params['O2_qmax_mg_gdw_h']*biomass[i]*oxygen[i]/(co2_cross.O2_K_MG_L+oxygen[i])
        oxygen[i+1] = max(oxygen[i]-dt*uptake, 0.)
    k, h = co2_cross.O2_ANA_K_MG_L, co2_cross.O2_ANA_HILL
    phi = k**h/(k**h+oxygen**h)
    fferm = co2_cross.O2_CRABTREE_FLOOR+(1.-co2_cross.O2_CRABTREE_FLOOR)*phi
    activity = 1.+(params['pulse_activity_gain']-1.)*ramp
    qbio = multiplier*np.maximum(activity*q0+ramp*(qn-q0), 0.)
    qprod = gate*fferm*qbio  # Same simplified structure as co2_local_observability.
    saturation = csat(batch, core, params)
    cd, qout = np.zeros(len(time)), np.zeros(len(time))
    cd[0] = cd0
    qout[0] = release(cd0, saturation[0], params)
    for i, dt in enumerate(np.diff(time), 1):
        qout[i] = min(release(cd[i-1], saturation[i], params), cd[i-1]/dt+qprod[i-1])
        cd[i] = max(cd[i-1]+dt*(qprod[i-1]-qout[i]), 0.)
    mass_error = float(np.max(np.abs(np.diff(cd)-np.diff(time)*(qprod[:-1]-qout[1:]))))
    assert mass_error < 1e-10 and np.isfinite(cd).all()
    out = core.copy()
    out['GF'] = out.G+out.F
    out['Cd'], out['O2'] = cd, oxygen
    out['predicted'] = params['matrix_gain']*qout
    out['qprod'], out['qgas'], out['qbio'] = qprod, qout, qbio
    out['gate'], out['ramp'], out['multiplier'] = gate, ramp, multiplier
    out['csat'], out['temperature_C'] = saturation, np.interp(time, batch.time, batch.temperature_c)
    out.attrs['mass_error'] = mass_error
    return out


def baseline(batch, theta, time, params):
    core = integrate_core(batch, theta, time)
    no_n = replace(batch, pulses={**batch.pulses, 'N': ()})
    core0 = integrate_core(no_n, theta, time)
    sugar, ethanol = (core.G+core.F).to_numpy(), core.E.to_numpy()
    crossed = np.flatnonzero((sugar <= sugar[0]-6.) | (ethanol >= ethanol[0]+2.))
    i = int(crossed[0]) if len(crossed) else 0
    lower, upper = float(time[max(0, i-1)]), float(time[i])
    gate = co2_cross._bounded_smoothstep_activation(time, lower, upper,
        params['chem_activation_start_fraction'], params['chem_activation_duration_fraction'])
    ramp, multiplier = pulse_history(time, batch.pulses['N'], params)
    init = batch.initials
    oxygen0 = params['O2_initial_scale']*co2_cross.co2_model.o2_saturation_mg_l(
        base.temperature_at(batch, time[0]), init['E'], init['G'], init['F'], 1.)
    frame = finish(batch, theta, core, core0, params, gate, ramp, multiplier, 0., oxygen0)
    return dict(frame=frame, core=core, core0=core0, gate_bracket=(lower, upper))


def restart(batch, theta, reference, start, initials, cd0, oxygen0, params):
    """Carry past-pulse counterfactual contrast; apply each future pulse exactly once."""
    full = reference['frame']
    time = full.index[full.index >= start].to_numpy(float)
    assert time[0] == start
    past_pulses = [(t, d) for t, d in batch.pulses['N'] if t < start]
    history_delta = ((reference['core'].loc[start]-reference['core0'].loc[start]).to_dict()
                     if past_pulses else {s: 0. for s in base.STATE_NAMES})
    no_n_initials_raw = {s: initials[s]-history_delta[s] for s in base.STATE_NAMES}
    clipped = {s: v for s, v in no_n_initials_raw.items() if v < 0.}
    no_n_initials = {s: max(v, 0.) for s, v in no_n_initials_raw.items()}
    future = {channel: tuple((t, d) for t, d in events if t >= start)
              for channel, events in batch.pulses.items()}
    bt = replace(batch, time=time, temperature_c=np.interp(time, batch.time, batch.temperature_c),
        initials=initials, pulses=future,
        observations={s: np.full(len(time), np.nan) for s in base.STATE_NAMES})
    bt0 = replace(bt, initials=no_n_initials, pulses={**future, 'N': ()})
    core, core0 = integrate_core(bt, theta, time), integrate_core(bt0, theta, time)
    suffix = full.loc[time]
    out = finish(bt, theta, core, core0, params, suffix.gate.to_numpy(),
        suffix.ramp.to_numpy(), suffix.multiplier.to_numpy(), cd0, oxygen0)
    out.attrs.update(counterfactual_clipped=clipped, past_pulses=past_pulses,
                     future_pulses=future['N'], core0=core0)
    return out


def initial_from_sample(chem, lab, sample):
    row = chem.loc[chem.lab.eq(lab) & chem['sample'].eq(str(sample))].iloc[0]
    start = float(row.t_h)
    values = dict(N=float(row.N_kg_m3), E=float(row.E_g_l), Gly=float(row.Gly_g_l),
                  X=float(row.X_total_g_l), Xd=float(row.Xd_g_l))
    direct = np.isfinite(row.G_g_l) and np.isfinite(row.F_g_l)
    if direct:
        values.update(G=float(row.G_g_l), F=float(row.F_g_l))
        gf_source, fraction_source_time = 'G medido; F=GF-G', start
    else:
        earlier = chem.loc[chem.lab.eq(lab) & (chem.t_h < start) & ~chem.soft_flag_GF
                           & chem.G_g_l.notna() & chem.F_g_l.notna()].sort_values('t_h')
        previous = earlier.iloc[-1]
        fraction = float(previous.G_g_l/(previous.G_g_l+previous.F_g_l))
        values.update(G=float(row.GF_g_l)*fraction, F=float(row.GF_g_l)*(1.-fraction))
        gf_source = f'GF medido; reparto supuesto heredado de m{previous["sample"]}'
        fraction_source_time = float(previous.t_h)
    assert np.isfinite(list(values.values())).all() and min(values.values()) >= 0.
    return values, dict(lab=lab, sample=str(sample), start_h=start, GF_direct=bool(direct),
        GF_source=gf_source, fraction_source_time_h=fraction_source_time,
        X_source='Oculyze total crudo x 0.03: centro exploratorio, no biomasa fiable',
        **values)


def flow_initialization(observed, start, saturation, params):
    # Hourly medians are left-labelled; a bin is available only at t_h+1 h.
    past = observed.loc[observed.co2_valid & (observed.t_h >= start-3.)
                        & (observed.t_h+1. <= start)].sort_values('t_h')
    assert len(past) >= 2, 'Insufficient completed gas bins for initialization'
    flow = float(past.co2_observed_g_l_h.median())
    assert (past.co2_observed_g_l_h >= co2_cross.CO2_DETECTION_LIMIT_G_L_H).all(), \
        'Selected chemistry sample lacks sustained detectable gas in preceding bins'
    return dissolved_from_flow(flow, saturation, params), dict(
        gas_initial_flow=flow, gas_init_first_bin_h=float(past.t_h.min()),
        gas_init_last_bin_end_h=float(past.t_h.max()+1.), n_init_gas_bins=len(past),
        activity_confirmed=True)


def scenarios(initials, cd, oxygen, saturation_oxygen, gf_direct, propagated_x):
    center = dict(initials=initials.copy(), cd=cd, oxygen=oxygen)
    out = {'central': center}
    for name, factor in [('X_x0.5', .5), ('X_x2', 2.)]:
        out[name] = {**center, 'initials': {**initials, 'X': initials['X']*factor}}
    out['X_propagada'] = {**center, 'initials': {**initials, 'X': float(propagated_x)}}
    for name, factor in [('Cd_cero', 0.), ('Cd_x0.5', .5), ('Cd_x2', 2.)]:
        out[name] = {**center, 'cd': cd*factor}
    out['O2_saturacion'] = {**center, 'oxygen': float(saturation_oxygen)}
    if not gf_direct:
        total, fraction = initials['G']+initials['F'], initials['G']/(initials['G']+initials['F'])
        for name, offset in [('fraccion_G_menos_0.10', -.1), ('fraccion_G_mas_0.10', .1)]:
            f = np.clip(fraction+offset, .01, .99)
            out[name] = {**center, 'initials': {**initials, 'G': total*f, 'F': total*(1.-f)}}
    return out


def scores(curve, chem, observed, start, pulse):
    rows = []
    for channel, column in {**CHANNELS, 'CO2': 'co2_observed_g_l_h'}.items():
        if channel == 'CO2':
            data = observed.loc[observed.co2_valid & (observed.t_h >= start)
                & (observed.t_h <= curve.index[-1]), ['t_h', column]].dropna()
            predicted = curve.predicted
        else:
            data = chem.loc[~chem.is_NUT & (chem.t_h > start)
                & (chem.t_h <= curve.index[-1]), ['t_h', column]].dropna()
            predicted = curve[channel]
        tt, yy = data.t_h.to_numpy(float), data[column].to_numpy(float)
        pp = np.interp(tt, curve.index, predicted)
        for window, keep in [('posterior_completo', np.ones(len(tt), bool)),
                             ('pre_pulso', tt < pulse), ('post_pulso', tt >= pulse)]:
            if not keep.any():
                continue
            err = pp[keep]-yy[keep]
            rows.append(dict(channel=channel, window=window, n=int(keep.sum()),
                RMSE=float(np.sqrt(np.mean(err**2))), bias=float(err.mean()),
                last_t_h=float(tt[keep][-1]), last_observed=float(yy[keep][-1]),
                last_predicted=float(pp[keep][-1]), last_error=float(err[-1])))
    return rows


def checks(curve, batch, theta):
    time = curve.index.to_numpy(float)
    doses = np.array([sum(d for t, d in batch.pulses['N'] if time[0] <= t < ti)
                      for ti in time])
    inventory = curve.N.to_numpy()+theta['qN']/theta['mu0']*(curve.X+curve.Xd).to_numpy()-doses
    error = float(np.max(np.abs(inventory-inventory[0])))
    assert error < 2e-6, error
    return dict(mass_balance_max_g_l=curve.attrs['mass_error'],
        nitrogen_inventory_max_g_l=error, final_h=float(time[-1]),
        min_state=float(curve[list(base.STATE_NAMES)+['Cd','O2']].min().min()))
