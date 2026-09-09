# Repository map

Status date: 2026-09-08.

This is the canonical navigation map for the fermentation work. Every active
artifact has one explicit owner: the shared model layer or one experimental
campaign. There is no generic `fermentation_model/results/` directory and no
active Python module in the `fermentation_model/` root.

## Directory tree

```text
fermentation_model/
├── README.md                  orientation and entry points
├── REPOSITORY_MAP.md          this ownership/dependency map
├── REPRODUCIBILITY.md         environment and run-manifest rules
├── environment.yml            conda environment definition
├── campaigns/                 machine-readable campaign/experiment registry
├── config/                    solver and run-manifest configuration
├── context/                   external reference material (Zenteno model)
├── data/                      immutable experimental sources
├── docs/                      scientific docs, presentations, session history
├── shared/                    reusable model package and shared results
├── laboratory_2025/           Laboratory 2025 campaign metadata
├── pilot_2025/                Pilot 2025 code, notebooks and results
├── laboratory_2026/           Laboratory 2026 code, notebooks and results
├── pilot_2026/                Pilot 2026 integration and gated adaptive-design workspace
├── presentation_co2_ekf_2026/ CO2/EKF 2026 presentation build workspace
├── legacy/                    frozen superseded work and rendition bundles
├── tools/                     repository audit and run-context capture
└── tests/                     structural and provenance checks
```

## Where to start

| Question | Start at | Then follow |
| --- | --- | --- |
| What campaigns exist? | `campaigns/campaigns.csv` | campaign `README.md` |
| Where is one fermentation? | `campaigns/experiments.csv` | its `raw_location` |
| Which runner is authoritative? | `campaigns/workflows.csv` | `path` and `authoritative_output` |
| Are raw files unchanged? | `campaigns/raw_data_manifest.csv` | `tools/campaign_audit.py --check-hashes` |
| How do I reproduce a result? | `REPRODUCIBILITY.md` | run config and `run_manifest.json` |
| Is an old artifact still current? | nearest `README.md` | otherwise treat `legacy/` as frozen |

Note: the operational registry CSVs predate the CO2 cross-matrix layer and the
`data/mem2026/` batches and are pending a dedicated registry revision.

## Ownership by layer

### Immutable data

```text
data/Laboratorio 2025/
data/Piloto 2025/
data/Laboratorio 2026/
data/Piloto 2026/
data/Multiplicador 2026/
data/mem2026/            LAB013–LAB018 natural-must measurements
```

Analysis code never writes into `data/`. Derived normalized tables belong to
the results directory of the workflow that created them.

### Shared model

```text
shared/
├── paths.py
├── new_must_data_loader.py
├── run_new_must_glycerol_estimability_doe.py
├── run_new_must_overnight_validation.py
├── run_secondary_metabolite_data_review.py
├── run_secondary_joint_campaign_doe.py
├── run_secondary_v2_model_evaluation.py
├── aroma_partition_unifac.py
└── results/
```

`shared/paths.py` is the single path contract. Shared modules must import
canonical directories from it instead of deriving data or result ownership from
their own file location.

### Laboratory 2026

```text
laboratory_2026/
├── run_co2_matrix_cross_validation_2026.py
├── run_estimability_historical_by_medium.py
├── run_estimability_historical_synthetic_plus_lot2.py
├── run_estimability_old_vs_lot1.py
├── run_lot2_data_preview.py
├── run_final_operational_doe_v2.py
├── run_final_operational_doe_volume_constrained.py
├── run_lot1_actual_mbdoe_reassessment.py
├── run_lot1_pulse_timing_mbdoe.py
├── run_lot1_express_optimal_sampling.py
├── create_*.py
├── notebooks/
└── results/
```

Notebook families under `laboratory_2026/notebooks/`:

- CO2 cross-matrix: `co2_solubility_o2_cross_matrix_2026(.executed).ipynb`
- Estimability by medium/stage: `fermentation_estimability_*`
- Lot previews: `fermentation_lot1_data_preview`,
  `fermentation_lot2_data_preview`
- Natural-must 2026 batches: `lab013_015_natural_must_co2_model_analysis`,
  `lab016_018_natural_must_holdout`, `lab016_018_co2_temperature_visualization`
- CO2 filtering diagnostics: `co2_filter_delay_analysis_lab2026`,
  `lab090226_lab290226_co2_offline_filter_analysis`
- Operational design: `fermentation_final_operational_doe_*`
- Progress presentation: `presentation_model_co2_progress`

Result families mirror the runners under `laboratory_2026/results/`
(`co2_matrix_cross_validation_2026/`, `estimability_historical_*`,
`lot1_*`/`lot2_*`, `final_operational_doe_*`).

The authoritative design handoff is
`laboratory_2026/results/design_execution_bundle_2026-06-09/`. The current
authoritative scientific output is
`laboratory_2026/results/co2_matrix_cross_validation_2026/`.

### Pilot campaigns

Pilot 2025 owns its integrated model, support code, notebooks and results under
`pilot_2025/`. Pilot 2026 has nine confirmed reactor/run mappings and owns the
lossless integration runner, QC tables, figures and executed loading-QC notebook
under `pilot_2026/`. Its corrected data contract includes paired wine/MIX aroma
observations, reconstructed Lot 3 operations and explicit CO2/model masks. The
processed dataset is model-ready under the confirmed rule that the MassView
Ln/min signal is already normalized and must not receive a second conversion.

Pilot 2026 also owns `adaptive_design/`, which contains the model-ready adapter,
calibration configuration and fail-closed campaign/design state. Immutable
adapter and calibration evaluations live under
`pilot_2026/results/adaptive_design_2026/`. The Phase A adapter is runtime
validated with active-process-only kinetic tables. The reduced Phase B primary
and residual-ESS CO2 calibration ran on 2026-07-17 and is computationally
`PASS`, with release `PASS_CONDITIONAL`. Alternative primary minima and
empirical model-discrepancy scales must propagate into MBDoE. PSO/IPOPT design
computation can be prepared, while physical scheduling remains blocked by
owner/Ultra review and unapproved fail-closed constraints.

### Documentation and context

- `docs/` holds scientific documentation (`CO2_MODEL_EXPLANATION.md`, the
  CO2/EKF LaTeX model, natural-must calibration notes), presentations under
  `docs/presentations/` and non-normative session-history notes under
  `docs/history/`.
- `context/` holds external reference material (Zenteno 2010 paper and Matlab
  model).
- `presentation_co2_ekf_2026/` is the build workspace for the CO2/EKF 2026
  presentation (figures, slide plan, metrics).

### Frozen history

`legacy/development_2026/` contains superseded runners, notebooks and their
matching result families. `legacy/rendicion/` and `pilot_2025/bundles/` contain
administrative AXX deliverables. Frozen source snapshots retain their original
paths intentionally and are not imported by active workflows.

## Active dependency chain

```text
data/Laboratorio 2025 + data/Laboratorio 2026
                    (+ data/mem2026 for current natural-must work)
                         │
                         ▼
             shared/new_must_data_loader.py
                         │
                         ▼
 shared/run_new_must_glycerol_estimability_doe.py
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
 secondary metabolite review   shared validation
             │
             ▼
 secondary joint/aroma model
             │
             ▼
 secondary v2 model evaluation
             │
       ┌─────┴────────────────┐
       ▼                      ▼
 laboratory_2026 runners   pilot_2025 runners
       │                      │
       ▼                      ▼
 campaign-owned results   campaign-owned results
```

### CO2 response layer (current)

```text
pilot_2025 CO2 solubility model
(run_pilot_2025_co2_solubility_integrated_doe.py)
        │
        ▼
laboratory_2026/run_co2_matrix_cross_validation_2026.py
        │  consumes lot1/lot2 processed CO2 tables, the historical
        │  natural-must batches and the versioned nutrient calendar
        ▼
laboratory_2026/results/co2_matrix_cross_validation_2026/
```

## Rules for future additions

1. Put reusable model code in `shared/`; put campaign-specific code in its
   campaign workspace.
2. Write outputs only to `shared/results/` or `<campaign>/results/`.
3. Add every experiment to `campaigns/experiments.csv`.
4. Add every active runner to `campaigns/workflows.csv`.
5. Regenerate the raw-data manifest only after intentionally adding raw files.
6. Move superseded code and its outputs together into `legacy/`.
7. Do not import code from notebooks, executed notebooks, bundles or `legacy/`.
8. Run `python fermentation_model/tools/campaign_audit.py --check-hashes`
   before committing a scientific result.
