"""Reproduce selected notebook-02 scenarios for the monochrome v2 summary.

Run from the activated fermentation environment. No fitting, notebook edits,
or result-directory writes. Numeric checks use the saved notebook outputs.
"""
import hashlib
import json
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = next(p for p in HERE.parents if (p / 'fermentation_model').is_dir())
NB = HERE.parent / '02_nutrition_structure_comparison.source.ipynb'
notebook = json.loads(NB.read_text(encoding='utf-8'))
scope = {'__name__': '__co2_summary_v2__'}

for index in (1, 3, 8, 9, 10, 11, 13, 15, 19):
    print(f'Reproducing notebook cell {index}', flush=True)
    code = ''.join(notebook['cells'][index]['source'])
    if index != 1:
        scope['display'] = lambda *args, **kwargs: None
    exec(compile(code, str(NB) + f':cell-{index}', 'exec'), scope)

result, manual = scope['RESULT'], scope['RECENT_MANUAL_RESULT']
comparison, parameters = scope['comparison'], scope['PARAM_SETS']
observed, batches = scope['OBSERVED'], scope['BATCHES']
main = result['metrics'].query('mode == "gate_predicho" and window == "completo"').copy()
main['group'] = np.where(main.lab.isin(scope['EXTERNAL_LABS']), 'external', 'recent')
medians = main.groupby(['group', 'family', 'param_set', 'theta']).RMSE_g_l_h.median()
expected = {
    ('external', 'vigente', 'antiguos', 'theta_full'): .4272,
    ('external', 'vigente', 'antiguos', 'theta_antiguo'): .2046,
    ('external', 'vigente', 'nuevos', 'theta_full'): .1094,
    ('external', 'vigente', 'nuevos', 'theta_antiguo'): .1931,
    ('recent', 'vigente', 'antiguos', 'theta_full'): .3245,
    ('recent', 'vigente', 'antiguos', 'theta_antiguo'): .2047,
    ('recent', 'vigente', 'nuevos', 'theta_full'): .1370,
    ('recent', 'vigente', 'nuevos', 'theta_antiguo'): .1391,
}
for key, value in expected.items():
    assert abs(float(medians.loc[key]) - value) < 5.1e-5, (key, medians.loc[key], value)

plt.style.use('default')
plt.rcParams.update({'font.family': 'serif', 'font.size': 8,
                     'axes.titlesize': 8.5, 'axes.labelsize': 8,
                     'xtick.labelsize': 7.5, 'ytick.labelsize': 7.5,
                     'legend.fontsize': 7.5, 'axes.linewidth': .6,
                     'pdf.fonttype': 42})

def finish_axes(ax, title):
    ax.set_title(title, pad=3)
    ax.set(xlim=(0, 160), ylim=(0, None), xlabel='Tiempo desde inoculación [h]')
    ax.set_ylabel(r'CO$_2$ [g L$^{-1}$ h$^{-1}$]')
    ax.grid(color='.88', linewidth=.45)
    ax.set_axisbelow(True)
    ax.spines[['top', 'right']].set_visible(False)

styles = {
    ('antiguos', 'theta_full'): {'color': '.25', 'ls': '-', 'lw': 1.45},
    ('antiguos', 'theta_antiguo'): {'color': '.25', 'ls': (0, (5, 2)), 'lw': 1.25},
    ('nuevos', 'theta_full'): {'color': '.60', 'ls': '-', 'lw': 1.45},
    ('nuevos', 'theta_antiguo'): {'color': '.60', 'ls': (0, (5, 2)), 'lw': 1.25},
}
labels = {('antiguos', 'theta_full'): 'Antiguos / full',
          ('antiguos', 'theta_antiguo'): 'Antiguos / defaults',
          ('nuevos', 'theta_full'): 'Nuevos / full',
          ('nuevos', 'theta_antiguo'): 'Nuevos / defaults'}
fig, axes = plt.subplots(1, 2, figsize=(6.55, 1.85))
for ax, lab in zip(axes, ('LAB017', 'LAB019')):
    obs = observed[lab]
    ax.plot(obs.t_h, obs.co2_rate_g_l_h, color='black', lw=.85, label='Observado válido')
    for (param, theta), style in styles.items():
        curve = result['curves'][('gate_predicho', 'vigente', param, theta, lab)]
        ax.plot(curve.t_h, curve.predicted, label=labels[(param, theta)], **style)
    for event, _ in batches[lab].pulses['N']:
        ax.axvline(event, color='.45', ls=':', lw=.65)
    finish_axes(ax, lab + ' · activación predicha')
handles, legend_labels = axes[0].get_legend_handles_labels()
handles.append(Line2D([], [], color='.45', ls=':', lw=.65))
legend_labels.append('Pulso N')
fig.legend(handles, legend_labels, loc='upper center', ncol=3,
           frameon=False, columnspacing=1.5, handlelength=2.5, bbox_to_anchor=(.52, 1.01))
fig.subplots_adjust(left=.080, right=.975, bottom=.235, top=.69, wspace=.30)
fig.savefig(HERE / 'theta_and_co2_layer.pdf', metadata={'Title': 'Theta and CO2 layer comparison'})
fig.savefig(HERE / 'theta_and_co2_layer.png', dpi=220)
plt.close(fig)

differences, all_candidates = [], {}
for lab in scope['RECENT_LABS']:
    for theta in ('theta_full', 'theta_antiguo'):
        reference = manual['curves'][('onset_manual', 'vigente', 'antiguos', theta, lab)]
        candidates, delta = comparison.compare_transient_location(reference, parameters['antiguos'])
        all_candidates[(lab, theta)] = candidates
        for row in delta.to_dict('records'):
            differences.append({'lab': lab, 'theta': theta, **row})
max_move = max(row['max_delta_qpred_g_l_h'] for row in differences if row['variant'] == 'transitorio_bio')
max_remove = max(row['max_delta_qpred_g_l_h'] for row in differences if row['variant'] == 'sin_respiracion')
assert max_move < 1e-14
assert np.isclose(max_remove, 3.51533797077e-6, rtol=1e-8)
fig, axes = plt.subplots(1, 2, figsize=(6.55, 1.80))
variant_styles = {'actual': {'color': '.65', 'lw': 2.5, 'ls': '-'},
                  'transitorio_bio': {'color': '.25', 'lw': 1.35, 'ls': (0, (5, 2))},
                  'sin_respiracion': {'color': 'black', 'lw': 1.0, 'ls': ':'}}
variant_labels = {'actual': 'Original: T sobre producción total',
                  'transitorio_bio': r'T dentro de $q_{bio}$',
                  'sin_respiracion': r'T dentro de $q_{bio}$, sin respiración'}
lab = 'LAB021'
for ax, theta in zip(axes, ('theta_full', 'theta_antiguo')):
    obs = observed[lab]
    ax.plot(obs.t_h, obs.co2_rate_g_l_h, color='black', lw=.8, label='Observado válido')
    for variant, curve in all_candidates[(lab, theta)].items():
        ax.plot(curve.t_h, curve.predicted, label=variant_labels[variant], **variant_styles[variant])
    ax.axvline(batches[lab].pulses['N'][0][0], color='.45', ls=':', lw=.65)
    ax.axvline(scope['RECENT_ONSET_MANUAL'][lab], color='.6', ls='-.', lw=.65)
    finish_axes(ax, 'LAB021 · theta ' + ('full' if theta == 'theta_full' else 'defaults'))
    reference = all_candidates[(lab, theta)]['actual']
    removed = all_candidates[(lab, theta)]['sin_respiracion']
    max_delta = float(np.max(np.abs(reference.predicted - removed.predicted)))
    ax.text(.98, .95, r'$\max|\Delta q_{pred}|$' + f' = {max_delta:.2e}',
            transform=ax.transAxes, ha='right', va='top', fontsize=7)
handles, legend_labels = axes[0].get_legend_handles_labels()
fig.legend(handles, legend_labels, loc='upper center', ncol=2, frameon=False,
           columnspacing=1.5, handlelength=2.6, bbox_to_anchor=(.52, 1.01))
fig.subplots_adjust(left=.080, right=.975, bottom=.24, top=.69, wspace=.30)
fig.savefig(HERE / 'transient_and_respiration.pdf', metadata={'Title': 'Transient location and respiration removal'})
fig.savefig(HERE / 'transient_and_respiration.png', dpi=220)
plt.close(fig)

manifest = {
    'source_notebook': str(NB.relative_to(ROOT)),
    'source_sha256': hashlib.sha256(NB.read_bytes()).hexdigest(),
    'source_cells': [17, 26, 40], 'reproduction_cells': [1, 3, 8, 9, 10, 11, 13, 15, 19],
    'selection': {'figure_1': ['LAB017', 'LAB019'], 'figure_2': ['LAB021']},
    'no_refitting': True, 'co2_param_sets': parameters,
    'theta_sets': scope['THETA_SETS'],
    'onset_manual_h': scope['RECENT_ONSET_MANUAL'],
    'input_initials': {lab: batch.initials for lab, batch in batches.items()},
    'input_pulses_N': {lab: batch.pulses['N'] for lab, batch in batches.items()},
    'verified_rmse_medians': {'/'.join(key): float(medians.loc[key]) for key in expected},
    'transient_location_max_difference_g_l_h': max_move,
    'respiration_removal_max_difference_g_l_h': max_remove,
    'transient_location_differences': differences,
}
assert scope['protected_before'] == {str(path): comparison.file_hash(path) for path in scope['PROTECTED_PATHS']}
(HERE / 'provenance.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
print(json.dumps({'verified_rmse': True, 'max_move': max_move, 'max_remove': max_remove}), flush=True)
