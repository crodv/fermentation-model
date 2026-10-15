"""Frozen comparisons of nutrition structure, theta and archived CO2 parameters.

The notebook supplies audited inputs; this module never fits or writes results.
"""
from dataclasses import replace
import hashlib
import math

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from IPython.display import Markdown, display

from shared import run_new_must_glycerol_estimability_doe as base
from laboratory_2026 import run_co2_matrix_cross_validation_2026 as co2_cross


FAMILIES = {
    'vigente': 'Referencia: rampa + gain + transitorio',
    'directa': 'Opción 1: nutrición directa, sin transitorio',
    'directa_transitorio': 'Opción 2: nutrición directa + transitorio',
}
THETA_LABELS = {'theta_full': 'theta_full', 'theta_antiguo': 'theta antiguo (6 defaults)'}
THETA_COLORS = {'theta_full': '#0072B2', 'theta_antiguo': '#D55E00'}
PARAM_LABELS = {'antiguos': 'Parámetros antiguos', 'nuevos': 'Parámetros nuevos: curva azul'}
REFERENCE_N = 0.14


def file_hash(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def chemical_bracket(core):
    """Same predicted G+F/E bracket as the production-block audit."""
    time = core.index.to_numpy(float)
    sugar = (core['G'] + core['F']).to_numpy(float)
    ethanol = core['E'].to_numpy(float)
    active = (sugar <= sugar[0] - 5.0) | (ethanol >= ethanol[0] + 2.0)
    indices = np.flatnonzero(active)
    if not len(indices):
        lower = upper = float(time[0])
    else:
        upper_i = int(indices[0])
        lower, upper = float(time[max(upper_i - 1, 0)]), float(time[upper_i])
    return lower, upper


def driver_for_theta(batch, theta, time):
    """Construct both N counterfactuals, retaining every recorded N jump."""
    no_n = replace(batch, pulses={**batch.pulses, 'N': tuple()})
    stub = pd.DataFrame({'batch': [batch.batch], 'matrix': ['natural'],
        'calibratable': [True], 'chemistry_last_h': [float(time[-1])], 't_h': [0.]})
    cache_map, _ = co2_cross.build_driver_cache({batch.batch: no_n}, {'natural': theta}, stub)
    template = cache_map[batch.batch]
    assert np.array_equal(template.time_h, time)
    core = base.simulate(batch, theta, time)
    assert core is not None and np.isfinite(core.to_numpy(float)).all()
    production = co2_cross.co2_model.co2_production_g_l_h(theta, batch, core, time)
    biomass = np.maximum(core['X'].to_numpy(float), 0.)
    e, g, f = (core[state].to_numpy(float) for state in ('E', 'G', 'F'))
    temp = template.temperature_used_c
    csat = 1.69 * np.exp(-.032 * (temp - 20.)) * np.exp(.0016 * np.maximum(e, 0.))
    csat *= np.exp(-.0012 * np.maximum(g + f, 0.))
    o2_sat = np.array([co2_cross.co2_model.o2_saturation_mg_l(t, ee, gg, ff, 1.)
        for t, ee, gg, ff in zip(temp, e, g, f)])
    schedule = batch.pulses['N']
    lower, upper = chemical_bracket(core)
    cache = replace(template, base_qprod_g_l_h=np.asarray(production, float),
        n_pulse_qprod_increment_g_l_h=production - template.base_qprod_no_n_pulse_g_l_h,
        biomass_g_l=biomass, n_pulse_biomass_increment_g_l=biomass - template.biomass_no_n_pulse_g_l,
        n_pulse_time_h=float(schedule[0][0]) if schedule else np.nan,
        n_pulse_amount_kg_m3=sum(dose for _, dose in schedule),
        csat_base_g_l=csat, o2_saturation_base_mg_l=o2_sat,
        chemical_activity_lower_h=lower, chemical_activity_upper_h=upper,
        chemical_activity_center_h=.5 * (lower + upper),
        chemical_activity_scale_h=max(1., (upper - lower) / (2. * math.log(9.))))
    # Check the model's discontinuous input convention at each actual event.
    probes = np.array([0., *[t for t, _ in schedule]])
    before = base.simulate(batch, theta, probes, sample_event_order='sample_before_action')
    after = base.simulate(batch, theta, probes, sample_event_order='action_before_sample')
    for event, dose in schedule:
        assert np.isclose(after.loc[event, 'N'] - before.loc[event, 'N'], dose, rtol=0., atol=1e-12)
    return cache, core


def pulse_kernel(time, event, rise, decay, normalization):
    u = np.maximum(np.asarray(time) - event, 0.)
    if normalization == 'grid_max':
        raw = (1. - np.exp(-u / rise)) * np.exp(-u / decay)
        peak = float(raw.max())
    else:
        assert normalization == 'analytic_peak'
        raw = -np.expm1(-u / rise) * np.exp(-u / decay)
        u_peak = rise * np.log1p(decay / rise)
        peak = -np.expm1(-u_peak / rise) * np.exp(-u_peak / decay)
    assert peak > 0.
    return raw / peak


def pool_from_production(time, csat, qprod, k_release):
    """Use the same dissolved-pool update for all production formulations."""
    dissolved = np.zeros(len(time))
    qout = np.zeros(len(time))
    for j, dt in enumerate(np.diff(time), start=1):
        previous = dissolved[j - 1]
        release = .05 + .95 * previous / max(previous + csat[j], 1e-12)
        qout[j] = min(k_release * previous * release, previous / dt + qprod[j - 1])
        dissolved[j] = max(previous + dt * (qprod[j - 1] - qout[j]), 0.)
    mass_error = float(np.max(np.abs(np.diff(dissolved) - np.diff(time) * (qprod[:-1] - qout[1:]))))
    assert mass_error < 1e-10
    assert (dissolved >= 0.).all() and (qout >= 0.).all()
    return dissolved, qout, mass_error


def predict(cache, params, family, schedule, manual_onset=None):
    assert family in FAMILIES
    if manual_onset is not None:
        cache = replace(cache, chemical_activity_lower_h=0., chemical_activity_upper_h=float(manual_onset))
    forward = dict(
        k_release_h=params['kCO2_release_h'], sat_scale=params['CO2sat_scale'],
        o2_qmax_mg_gdw_h=params['O2_qmax_mg_gdw_h'], o2_initial_scale=params['O2_initial_scale'],
        chemistry_aligned=True, nitrogen_boost_transition=family == 'vigente',
        pulse_t_rise_h=params['pulse_t_rise_h'], pulse_activity_gain=params['pulse_activity_gain'],
        continuous_release=True, bounded_chemical_activation=True,
        chem_activation_start_fraction=params['chem_activation_start_fraction'],
        chem_activation_duration_fraction=params['chem_activation_duration_fraction'])
    baseline_output, qbase, oxygen, phi = co2_cross.raw_qgas_grid_prediction(cache, **forward)
    time = cache.time_h
    ramp = co2_cross._pulse_utilization_fraction(cache, params['pulse_t_rise_h'])
    activity = 1. + (params['pulse_activity_gain'] - 1.) * ramp
    if family == 'vigente':
        qbio = np.maximum(activity * cache.base_qprod_no_n_pulse_g_l_h
                         + ramp * cache.n_pulse_qprod_increment_g_l_h, 0.)
        biomass = np.maximum(cache.biomass_no_n_pulse_g_l
                             + ramp * cache.n_pulse_biomass_increment_g_l, 0.)
    else:
        qbio = np.maximum(cache.base_qprod_g_l_h, 0.)
        biomass = np.maximum(cache.biomass_g_l, 0.)
        activity = np.ones(len(time))
        ramp = np.ones(len(time))  # direct input; this diagnostic is unused in the equations.
    uptake = params['O2_qmax_mg_gdw_h'] * biomass * oxygen / (co2_cross.O2_K_MG_L + oxygen)
    fferm = co2_cross.O2_CRABTREE_FLOOR + (1. - co2_cross.O2_CRABTREE_FLOOR) * phi
    qresp = co2_cross.co2_model.CO2_G_PER_MG_O2_RESP * uptake
    lower, upper = cache.chemical_activity_lower_h, cache.chemical_activity_upper_h
    activation = co2_cross._bounded_smoothstep_activation(time, lower, upper,
        params['chem_activation_start_fraction'], params['chem_activation_duration_fraction'])
    assert np.allclose(qbase, activation * (fferm * qbio + qresp), rtol=1e-11, atol=1e-12)
    multiplier = np.ones(len(time))
    if family != 'directa':
        for event, dose in schedule:
            multiplier += params['A'] * dose / REFERENCE_N * pulse_kernel(
                time, event, params['tau_rise_h'], params['tau_decay_h'], params['kernel_normalization'])
    if schedule:
        assert np.array_equal(multiplier[time < schedule[0][0]], np.ones(np.sum(time < schedule[0][0])))
    qin = qbase * multiplier
    csat = params['CO2sat_scale'] * cache.csat_base_g_l
    dissolved, qout, mass_error = pool_from_production(time, csat, qin, params['kCO2_release_h'])
    if family == 'directa':
        assert np.allclose(qout, baseline_output, rtol=1e-11, atol=1e-12)
    return pd.DataFrame(dict(t_h=time, qbio=qbio, qbase=qbase, q_input=qin,
        qresp=qresp, f_ferm=fferm, O2_mg_l=oxygen, activation=activation,
        transient_multiplier=multiplier, dissolved_g_l=dissolved,
        csat_g_l=csat, predicted=params['matrix_gain'] * qout)), {
            'gate_lower_h': lower, 'gate_upper_h': upper,
            'gate_start_h': lower + params['chem_activation_start_fraction'] * (upper - lower),
            'gate_end_h': (lower + params['chem_activation_start_fraction'] * (upper - lower)
                          + max(params['chem_activation_duration_fraction'] * (upper - lower), .25))
                         if upper > lower else upper,
            'mass_error': mass_error,
        }


def onset(time, values, threshold):
    above = np.asarray(values) >= threshold
    for i in range(len(above) - 2):
        if above[i:i + 3].all():
            return float(np.asarray(time)[i])
    return np.nan


def auc(time, values):
    t, y = np.asarray(time), np.asarray(values)
    dt = np.diff(t)
    keep = (dt > 0.) & (dt <= 1.5)
    return float(np.sum(.5 * (y[:-1] + y[1:]) * dt * keep))


def metrics_for_curve(observed, curve, pulse_h):
    time = observed['t_h'].to_numpy(float)
    y = observed['co2_rate_g_l_h'].to_numpy(float)
    pred = np.interp(time, curve.t_h, curve.predicted)
    early = y[time <= 12.]
    baseline = float(np.median(early)) if len(early) else 0.
    threshold = max(.05, baseline + .10 * (float(y.max()) - baseline))
    rows = []
    windows = {'completo': np.ones(len(time), bool), 'pre_pulso': time < pulse_h,
               'pulso_24h': (time >= pulse_h) & (time <= pulse_h + 24.), 'cola': time > pulse_h + 24.}
    for window, keep in windows.items():
        tt, yy, pp = time[keep], y[keep], pred[keep]
        if len(tt) < 3:
            continue
        rmse = float(np.sqrt(np.mean((pp - yy) ** 2)))
        onset_obs, onset_pred = onset(tt, yy, threshold), onset(tt, pp, threshold)
        observed_auc = auc(tt, yy)
        rows.append(dict(window=window, n=len(tt), RMSE_g_l_h=rmse,
            NRMSE_peak=rmse / max(float(y.max()), 1e-12),
            onset_error_h=onset_pred - onset_obs,
            peak_predicted_g_l_h=float(pp.max()), peak_observed_g_l_h=float(yy.max()),
            AUC_relative_error=(auc(tt, pp) - observed_auc) / max(observed_auc, 1e-12)))
    return rows


def role_for(lab, param_set, mode):
    if mode == 'onset_manual':
        return 'Diagnóstico condicionado; no holdout predictivo'
    if lab in ('LAB019', 'LAB020', 'LAB021'):
        return ('Datos de calibración previa de los parámetros nuevos' if param_set == 'nuevos'
                else 'Evaluación con parámetros históricos; datos ya explorados')
    return 'Evaluación externa ya explorada; ICs proxy y dosis supuesta'


def compare_all(batches, time_grids, observed, theta_sets, param_sets, manual_onsets):
    caches, cores, curves = {}, {}, {}
    rows, gate_rows = [], []
    for lab, batch in batches.items():
        for theta_name, theta in theta_sets.items():
            caches[(lab, theta_name)], cores[(lab, theta_name)] = driver_for_theta(batch, theta, time_grids[lab])
    for mode in ('gate_predicho', 'onset_manual'):
        labs = tuple(batches) if mode == 'gate_predicho' else tuple(manual_onsets)
        for family in FAMILIES:
            for param_name, params in param_sets.items():
                for theta_name in theta_sets:
                    for lab in labs:
                        schedule = batches[lab].pulses['N']
                        curve, gate = predict(caches[(lab, theta_name)], params, family, schedule,
                                              manual_onsets[lab] if mode == 'onset_manual' else None)
                        key = (mode, family, param_name, theta_name, lab)
                        curves[key] = curve
                        attributes = dict(mode=mode, family=family, param_set=param_name,
                            theta=theta_name, lab=lab, role=role_for(lab, param_name, mode))
                        gate_rows.append({**attributes, **gate})
                        for metric in metrics_for_curve(observed[lab], curve, schedule[0][0]):
                            rows.append({**attributes, **metric})
    assert len(curves) == 108  # 72 main comparisons + 36 conditioned diagnostics.
    return dict(caches=caches, cores=cores, curves=curves, theta_sets=theta_sets,
                metrics=pd.DataFrame(rows), gates=pd.DataFrame(gate_rows))


def parameter_table(param_sets, family):
    rows = []
    for name in param_sets['antiguos']:
        used = not (family != 'vigente' and name in ('pulse_t_rise_h', 'pulse_activity_gain'))
        used &= not (family == 'directa' and name in ('A', 'tau_rise_h', 'tau_decay_h', 'kernel_normalization'))
        rows.append({'parameter': name, 'uso': 'activo' if used else 'no interviene',
            'antiguos': param_sets['antiguos'][name] if used else ('0 (M_N=1)' if name == 'A' else '—'),
            'nuevos': param_sets['nuevos'][name] if used else ('0 (M_N=1)' if name == 'A' else '—')})
    return pd.DataFrame(rows)


def equations(family, mode):
    production = {
        'vigente': r'q_{\mathrm{bio}}=[(1+(g-1)r)q_{\mathrm{bio},0}+r(q_{\mathrm{bio},N}-q_{\mathrm{bio},0})]_+,\quad X_{\mathrm{eff}}=[X_0+r(X_N-X_0)]_+',
        'directa': r'q_{\mathrm{bio}}=q_{\mathrm{bio},N},\quad X_{\mathrm{eff}}=X_N',
        'directa_transitorio': r'q_{\mathrm{bio}}=q_{\mathrm{bio},N},\quad X_{\mathrm{eff}}=X_N',
    }[family]
    transient = (r'M_N=1,\quad T_N=0,\quad A=0' if family == 'directa' else
        r'M_N=1+T_N,\quad T_N=A\sum_j\frac{\Delta N_j}{0.14}\frac{(1-e^{-u_j/\tau_r})e^{-u_j/\tau_d}}{\mathcal N_j},\quad u_j=\max(t-t_j,0)')
    gate = ('Bracket de G+F/E **simulados**, independiente de CO2 observado.' if mode == 'gate_predicho'
            else 'Bracket **[0, onset manual observado]**: diagnóstico condicionado.')
    return rf'''**Ecuaciones de esta figura — {FAMILIES[family]}.** {gate}

$$q_{{\mathrm{{bio}},k}}=Y_{{CO_2/E}}X_k\,a_\beta(T)\,\frac{{1}}{{1+i_E(T)E_k}}\left[\beta_{{G0}}\frac{{G_k}}{{G_k+K_G(T)}}+\beta_{{F0}}\frac{{F_k}}{{F_k+K_F(T)}}\frac{{1}}{{1+i_G(T)G_k}}\right],\quad k\in\{{0,N\}}.$$
$$K_G=\frac{{\beta_{{G0}}}}{{s_G}}a_K(T),\quad K_F=\frac{{\beta_{{F0}}}}{{s_F}}a_K(T),\quad r=\operatorname{{clip}}((t-t_p)/t_{{rise}},0,1).$$
$$ {production} $$
$$r_{{O_2}}=q_{{O_2,max}}X_{{eff}}\frac{{O}}{{0.25+O}},\quad \dot O=-r_{{O_2}},\quad O(0)=\alpha_O O_{{sat}}(0),\quad \phi_{{ana}}=\frac{{0.75^2}}{{0.75^2+O^2}},\quad f_{{ferm}}=0.08+0.92\phi_{{ana}}.$$
$$q_{{resp}}=\frac{{44.01}}{{32000}}r_{{O_2}},\quad a=3z^2-2z^3,\quad z=\operatorname{{clip}}\left(\frac{{t-[L+s(U-L)]}}{{\max(d(U-L),0.25)}},0,1\right).$$
$$q_{{base}}=a\,[f_{{ferm}}q_{{bio}}+q_{{resp}}],\quad q_{{prod}}=M_Nq_{{base}},\quad {transient}.$$
$$C_{{sat}}=s_{{CO_2}}1.69e^{{-0.032(T-20)}}e^{{0.0016E_N}}e^{{-0.0012(G_N+F_N)}},\quad q_{{out}}=k C\left(0.05+0.95\frac{{C}}{{C+C_{{sat}}}}\right),\quad \dot C=q_{{prod}}-q_{{out}},\quad q_{{pred}}=g_{{matrix}}q_{{out}}.$$

Se integra el pool con Euler y límite de CO2 disponible; C(0)=0. En las familias con transitorio, la normalización antigua es el máximo del kernel en la grilla de este LAB; la nueva es el máximo analítico, en u*=tau_r log(1+tau_d/tau_r). La forma del gate usa sus fracciones s/d antiguas o nuevas. Las tablas siguientes muestran los valores efectivos; los parámetros retirados se marcan como «no interviene».

La actualización implementada, con h=t_i-t_(i-1), es:
$$q_{{out,i}}=\min\!\left[k C_{{i-1}}\left(0.05+0.95\frac{{C_{{i-1}}}}{{C_{{i-1}}+C_{{sat,i}}}}\right),\frac{{C_{{i-1}}}}{{h}}+q_{{prod,i-1}}\right],\quad C_i=[C_{{i-1}}+h(q_{{prod,i-1}}-q_{{out,i}})]_+.$$
'''


def show_comparison(result, batches, observed, theta_table, param_sets, family, labs, mode,
                    param_names=('antiguos', 'nuevos'), manual_onsets=None):
    display(Markdown(equations(family, mode)))
    display(parameter_table(param_sets, family)[['parameter', 'uso', *param_names]])
    display(Markdown('**Vector cinético usado por cada color (17 parámetros):**'))
    display(theta_table)
    display(Markdown('**Condiciones iniciales comunes y eventos de esta figura:**'))
    display(pd.DataFrame([{'lab': lab, **batches[lab].initials} for lab in labs]))
    display(pd.DataFrame([{'lab': lab, 'event_h': event, 'delta_N_kg_m3': dose,
        'dose_status': 'referencia supuesta' if lab in ('LAB016','LAB017','LAB018') else 'YAN registrado en Excel'}
        for lab in labs for event, dose in batches[lab].pulses['N']]))
    selected = result['gates'].query('family == @family and mode == @mode and lab in @labs and param_set in @param_names')
    display(selected[['lab','param_set','theta','gate_lower_h','gate_upper_h','gate_start_h','gate_end_h']].round(4))
    group_label = 'LAB016–018' if 'LAB016' in labs else 'LAB019–021'
    mode_label = 'gate predicho' if mode == 'gate_predicho' else 'onset manual — diagnóstico'
    fig = plt.figure(figsize=(15 if len(param_names) == 2 else 12, 11.7), layout='constrained')
    gs = fig.add_gridspec(4, len(param_names), height_ratios=[.17, 1, 1, 1])
    header = fig.add_subplot(gs[0, :]); header.set_axis_off()
    for row, lab in enumerate(labs):
        for col, param_name in enumerate(param_names):
            ax = fig.add_subplot(gs[row + 1, col])
            obs = observed[lab]
            ax.plot(obs.t_h, obs.co2_rate_g_l_h, color='black', lw=1.5, label='Observado válido')
            for theta_name in THETA_LABELS:
                curve = result['curves'][(mode,family,param_name,theta_name,lab)]
                ax.plot(curve.t_h, curve.predicted, color=THETA_COLORS[theta_name], lw=1.8,
                        label=THETA_LABELS[theta_name])
            for j, (event, _) in enumerate(batches[lab].pulses['N']):
                ax.axvline(event, color='#C44E52', ls='--', lw=.8,
                           label='Nutrición' if j == 0 else None)
            if manual_onsets is not None:
                ax.axvline(manual_onsets[lab], color='0.4', ls=':', lw=1.,
                           label='Referencia onset manual')
            ax.set_title(f'{lab} — {PARAM_LABELS[param_name]}', fontsize=10)
            ax.set_xlim(0., float(curve.t_h.max())); ax.set_ylim(bottom=0.)
            ax.set_xlabel('t desde inoculación [h]')
            ax.set_ylabel(r'CO$_2$ [g L$^{-1}$ h$^{-1}$]')
            ax.grid(alpha=.25)
            if row == 0 and col == 0:
                handles, labels = ax.get_legend_handles_labels()
                header.legend(handles, labels, loc='center', ncol=4, frameon=False, fontsize=9)
    fig.suptitle(f'{FAMILIES[family]}\n{group_label} · {mode_label} · sin reajuste', fontsize=13)
    display(fig); plt.close(fig)
    metrics = result['metrics'].query('family == @family and mode == @mode and lab in @labs and param_set in @param_names')
    display(Markdown('**Métricas descriptivas completas y papel de los datos:**'))
    display(metrics.query('window == "completo"')[['lab','param_set','theta','role',
        'RMSE_g_l_h','NRMSE_peak','onset_error_h','peak_predicted_g_l_h','AUC_relative_error']].round(4))
    display(metrics.groupby(['param_set','theta','window'], sort=False)[['RMSE_g_l_h','NRMSE_peak']].median().round(4))


def compare_transient_location(reference, params):
    """Move the transient to q_bio, optionally omitting respiratory CO2 only."""
    time = reference.t_h.to_numpy()
    activation = reference.activation.to_numpy()
    fferm = reference.f_ferm.to_numpy()
    qbio = reference.qbio.to_numpy()
    qresp = reference.qresp.to_numpy()
    multiplier = reference.transient_multiplier.to_numpy()
    csat = reference.csat_g_l.to_numpy()
    inputs = {
        'actual': reference.q_input.to_numpy(),
        'transitorio_bio': activation * (fferm * (multiplier * qbio) + qresp),
        'sin_respiracion': activation * fferm * (multiplier * qbio),
    }
    assert np.allclose(inputs['actual'] - inputs['transitorio_bio'],
        activation * (multiplier - 1.) * qresp, rtol=1e-10, atol=2e-15)
    assert np.allclose(inputs['transitorio_bio'] - inputs['sin_respiracion'],
        activation * qresp, rtol=1e-10, atol=2e-15)
    curves, rows = {}, []
    for name, qprod in inputs.items():
        curve = reference.drop(columns=['qbase']).copy()
        curve['qbio'] = qbio if name == 'actual' else multiplier * qbio
        curve['qresp'] = qresp if name != 'sin_respiracion' else 0.
        curve['q_input'] = qprod
        dissolved, qout, mass_error = pool_from_production(time, csat, qprod, params['kCO2_release_h'])
        curve['dissolved_g_l'] = dissolved
        curve['predicted'] = params['matrix_gain'] * qout
        if name == 'actual':
            assert np.array_equal(curve.predicted.to_numpy(), reference.predicted.to_numpy())
            assert np.array_equal(dissolved, reference.dissolved_g_l.to_numpy())
        for field in ('O2_mg_l','f_ferm','activation','transient_multiplier','csat_g_l'):
            assert np.array_equal(curve[field].to_numpy(),reference[field].to_numpy())
        curves[name] = curve
        rows.append(dict(variant=name,
            max_delta_qprod_g_l_h=float(np.max(np.abs(qprod-inputs['actual']))),
            max_delta_qpred_g_l_h=float(np.max(np.abs(curve.predicted-reference.predicted))),
            delta_production_g_l=float(np.sum(np.diff(time)*(qprod[:-1]-inputs['actual'][:-1]))),
            mass_error=mass_error))
    return curves, pd.DataFrame(rows)


def show_transient_location(manual_result, batches, observed, theta_table, param_sets, onsets, labs):
    """One figure: three production models per panel, two theta columns."""
    labels = {'actual': 'Modelo original: transitorio sobre producción total',
        'transitorio_bio': 'Modificación: transitorio dentro de q_bio',
        'sin_respiracion': 'Modificación: transitorio en q_bio, sin respiración'}
    styles = {'actual': dict(color='0.35',lw=3.4,ls='-'),
        'transitorio_bio': dict(color='#0072B2',lw=2.4,ls=(0,(6,3))),
        'sin_respiracion': dict(color='#D55E00',lw=1.6,ls=':')}
    display(Markdown('**Parámetros antiguos compartidos por las tres curvas:**'))
    display(parameter_table(param_sets,'vigente')[['parameter','uso','antiguos']])
    display(theta_table)
    display(pd.DataFrame([{'lab':lab, **batches[lab].initials} for lab in labs]))
    display(pd.DataFrame([{'lab':lab,'event_h':event,'delta_N_kg_m3':dose}
        for lab in labs for event,dose in batches[lab].pulses['N']]))
    display(manual_result['gates'][['lab','theta','gate_start_h','gate_end_h']].assign(
        onset_manual_h=lambda df:df.lab.map(onsets)))
    fig = plt.figure(figsize=(15,11.7),layout='constrained')
    gs = fig.add_gridspec(len(labs)+1,2,height_ratios=[.22,*[1 for _ in labs]])
    header = fig.add_subplot(gs[0,:]); header.set_axis_off()
    curves, difference_rows, metric_rows = {}, [], []
    for row,lab in enumerate(labs):
        for col,theta_name in enumerate(THETA_LABELS):
            reference = manual_result['curves'][('onset_manual','vigente','antiguos',theta_name,lab)]
            candidates, differences = compare_transient_location(reference,param_sets['antiguos'])
            differences['lab'], differences['theta'] = lab,theta_name
            difference_rows.append(differences)
            ax = fig.add_subplot(gs[row+1,col])
            obs = observed[lab]
            ax.plot(obs.t_h,obs.co2_rate_g_l_h,color='black',lw=1.5,zorder=5,
                    label='CO2 observado válido')
            for name,curve in candidates.items():
                curves[(lab,theta_name,name)] = curve
                ax.plot(curve.t_h,curve.predicted,label=labels[name],**styles[name])
                full = next(item for item in metrics_for_curve(observed[lab],curve,batches[lab].pulses['N'][0][0])
                    if item['window'] == 'completo')
                metric_rows.append(dict(lab=lab,theta=theta_name,variant=name,**full))
            for j,(event,_) in enumerate(batches[lab].pulses['N']):
                ax.axvline(event,color='#8E44AD',ls='--',lw=1.2,
                           label='Pulso nutricional' if j == 0 else None)
            ax.axvline(onsets[lab],color='0.65',ls=':',lw=.8,label='Onset manual')
            ax.set_title(f'{lab} — {THETA_LABELS[theta_name]}',fontsize=10)
            ax.set_xlim(0.,reference.t_h.max()); ax.set_ylim(bottom=0.)
            ax.set_xlabel('t desde inoculación [h]')
            ax.set_ylabel(r'Flujo CO$_2$ [g L$^{-1}$ h$^{-1}$]')
            ax.grid(alpha=.25)
            if row == 0 and col == 0:
                handles,legend_labels = ax.get_legend_handles_labels()
                header.legend(handles,legend_labels,loc='center',ncol=2,frameon=False,fontsize=9)
    fig.suptitle('LAB019–021 · ubicación del transitorio y retiro de CO2 respiratorio\n'
        'Parámetros antiguos · onset manual · rampa + gain conservados · sin reajuste',fontsize=13)
    display(fig); plt.close(fig)
    differences = pd.concat(difference_rows,ignore_index=True)
    display(Markdown('**Diferencias frente al modelo actual (sin redondear a cero):**'))
    display(differences[['lab','theta','variant','max_delta_qprod_g_l_h',
        'max_delta_qpred_g_l_h','delta_production_g_l','mass_error']].style.format({
            name:'{:.3e}' for name in ('max_delta_qprod_g_l_h','max_delta_qpred_g_l_h',
                                     'delta_production_g_l','mass_error')}))
    display(Markdown('**Métricas sobre el mismo CO2 observado válido:**'))
    metrics = pd.DataFrame(metric_rows)
    display(metrics[['lab','theta','variant','RMSE_g_l_h','NRMSE_peak','AUC_relative_error']].round(6))
    display(Markdown('Las curvas pueden superponerse: se usan línea sólida, trazos y puntos para '
        'identificarlas. La curva negra muestra el CO2 observado válido. Las líneas verticales '
        'morada y gris indican nutrición y onset manual. '
        'Las diferencias cuantitativas anteriores permiten evaluar cambios pequeños sin alterar la escala.'))
    assert len(curves) == len(labs)*2*3
    return dict(curves=curves,differences=differences,metrics=metrics)


def show_chemistry(result, batches, chem, theta_table):
    display(Markdown(r'''**Ecuaciones y parámetros de esta figura de estados cinéticos.** La capa de CO2 no modifica estos estados; son comunes a las tres familias para un mismo theta.

$$\dot X=(\mu-k_d)X,\quad \dot X_d=k_dX,\quad \dot N=-q_N f_N X,\quad f_N=a_\mu(T)\frac{N}{N+K_N(T)}.$$
$$\dot G=-X[q_{XG}f_N+q_{EG}\varphi_G+m(T)\chi\,G/(G+F)],\quad \dot F=-X[q_{XF}f_N+q_{EF}\varphi_F+m(T)\chi\,F/(G+F)].$$
$$\dot E=X(\beta_{G0}\varphi_G+\beta_{F0}\varphi_F),\quad \dot{Gly}=X(\gamma_{G0}\varphi_G+\gamma_{F0}\varphi_F),\quad \chi=(G+F)/(G+F+1).$$
$$\mu=\mu_0 f_N,\quad \varphi_G=a_\beta\frac{G}{G+K_G}\frac{1}{1+i_E(T)E},\quad \varphi_F=a_\beta\frac{F}{F+K_F}\frac{1}{1+i_G(T)G}\frac{1}{1+i_E(T)E}.$$
$$T_d(E)=-0.0001E^3+0.0049E^2-0.1279E+315.89,\quad k_d=\begin{cases}K_{d0}\exp\!\left[\frac{C_{de}E+E_{td}(T_K-305.65)}{305.65RT_K}\right],&T_K\ge T_d(E),\\0,&T_K<T_d(E).\end{cases}$$

Los factores de fermentación son los definidos en las figuras de CO2; N recibe saltos exactos en los eventos publicados. No se ajusta theta con estos datos. Las ICs y dosis son las mismas que en las figuras LAB019–021.
'''))
    display(theta_table)
    display(pd.DataFrame([{'lab':lab, **batches[lab].initials} for lab in ('LAB019','LAB020','LAB021')]))
    display(pd.DataFrame([{'lab':lab,'event_h':event,'delta_N_kg_m3':dose}
        for lab in ('LAB019','LAB020','LAB021') for event,dose in batches[lab].pulses['N']]))
    fig = plt.figure(figsize=(15, 11.1), layout='constrained')
    gs = fig.add_gridspec(4,3,height_ratios=[.17,1,1,1])
    header = fig.add_subplot(gs[0,:]); header.set_axis_off()
    for row, lab in enumerate(('LAB019','LAB020','LAB021')):
        measured = chem[chem.lab.eq(lab)]
        for col, (state, observed_col, label, factor) in enumerate((
            ('GF','GF_g_l','G+F [g/L]',1.), ('E','E_g_l','Etanol [g/L]',1.),
            ('N','YAN_mg_l','YAN [mg/L]',1000.))):
            ax = fig.add_subplot(gs[row+1,col])
            for theta_name in THETA_LABELS:
                core = result['cores'][(lab,theta_name)]
                if float(core.index[-1]) < float(batches[lab].time[-1]) - 1e-9:
                    core = base.simulate(batches[lab],result['theta_sets'][theta_name],batches[lab].time)
                    assert core is not None
                values = core.G + core.F if state == 'GF' else core[state]
                ax.plot(core.index, values * factor, color=THETA_COLORS[theta_name],
                        label=THETA_LABELS[theta_name])
            valid = measured[measured[observed_col].notna()]
            ax.scatter(valid.t_h, valid[observed_col], color='black', s=22, label='Química medida')
            for event, _ in batches[lab].pulses['N']:
                ax.axvline(event,color='#C44E52',ls='--',lw=.8)
            ax.set_title(f'{lab} — {label}')
            ax.set_xlabel('t desde inoculación [h]'); ax.set_ylabel(label)
            ax.set_xlim(0., float(core.index[-1])); ax.set_ylim(bottom=0.)
            ax.grid(alpha=.25)
            if row == 0 and col == 0:
                handles, labels = ax.get_legend_handles_labels()
                header.legend(handles,labels,loc='center',ncol=3,frameon=False)
    fig.suptitle('Chequeo cinético independiente de la reformulación de CO2 — sin ajuste',fontsize=13)
    display(fig); plt.close(fig)
