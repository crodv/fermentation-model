# Fermentation modeling workspace

This directory contains the fermentation campaigns, their shared dynamic
model, the model-based design of experiments (MBDoE) workflows and the CO2
response layer used for the current natural-must calibration and validation
work.

## Start here

1. Read `REPOSITORY_MAP.md` to locate a campaign, experiment, runner or result.
2. Use `campaigns/experiments.csv` as the master fermentation registry.
3. Use `campaigns/workflows.csv` to find the authoritative Python entry point
   and its output directory.
4. Read `REPRODUCIBILITY.md` before reporting new parameter estimates, FIM
   comparisons or profile-likelihood results.

## Campaigns and data

| Campaign | Workspace | Raw data | State |
| --- | --- | --- | --- |
| Laboratory 2025 | `laboratory_2025/` | `data/Laboratorio 2025/` | complete CCD |
| Pilot 2025 | `pilot_2025/` | `data/Piloto 2025/` | complete paired vintage; owns the CO2 solubility model |
| Laboratory 2026 | `laboratory_2026/` | `data/Laboratorio 2026/` | calibration, validation and CO2 cross-matrix analysis |
| Pilot 2026 | `pilot_2026/` | `data/Piloto 2026/` | data integration and gated adaptive design |

`data/mem2026/` holds the newer natural-must measurements for batches
LAB013–LAB018 (Oculyze `report.csv` tables and accompanying exports) and
`data/Multiplicador 2026/` holds multiplier-stage measurements. Historical
campaign data remain valid project inputs: `legacy/` freezes superseded code
only, never experimental data.

Raw files are immutable. Processed tables, parameters, figures and FIM outputs
belong to a workflow-owned results directory.

## Scientific layering

- Upstream fermentation kinetics are calibrated per must medium (synthetic and
  natural) from historical and 2026 DOE data by the
  `laboratory_2026/run_estimability_*` runners.
- The CO2 response layer is calibrated afterwards on top of those upstream
  drivers by `run_co2_matrix_cross_validation_2026.py`, reusing the
  `pilot_2025` CO2 solubility model.
- Current work is oriented primarily to natural must, cross-matrix validation
  and hold-out assessment with the 2026 batches.

`docs/CO2_MODEL_EXPLANATION.md` documents the CO2 model in depth.

## Code and result ownership

- `shared/`: reusable data loading, fermentation/glycerol, secondary-metabolite,
  aroma and partition code. Shared priors and outputs are in `shared/results/`.
- `laboratory_2026/`: experimental data analysis, estimability by medium,
  Lot 1/Lot 2 processing, CO2 cross-matrix calibration and validation, and the
  sequential MBDoE design history. Outputs are in `laboratory_2026/results/`.
- `pilot_2025/`: pilot-specific integrated model and support layer. Outputs are
  in `pilot_2025/results/`.
- `pilot_2026/`: pilot-2026 data integration and gated adaptive-design
  workspace.
- `legacy/`: frozen superseded science and administrative rendition artifacts.
- `docs/`: scientific documentation, presentations and session-history
  material. `docs/history/` is non-normative historical context.

The `fermentation_model/` root intentionally contains no active `.py` files and
no generic `results/` directory. This makes ownership visible from the path.

## Authoritative current endpoints

### CO2 cross-matrix calibration and validation (current focus)

- Runner: `laboratory_2026/run_co2_matrix_cross_validation_2026.py`
- Notebook:
  `laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.ipynb`
  (the `.executed.ipynb` sibling keeps the outputs of a full run)
- Results: `laboratory_2026/results/co2_matrix_cross_validation_2026/`

The nutrient-pulse calendar for the historical natural-must analysis is a
versioned input at
`data/Laboratorio 2026/raw_data/Fernanda Folch.ics` and is resolved through
repository-relative paths.

Run from the repository root:

```powershell
python fermentation_model\laboratory_2026\run_co2_matrix_cross_validation_2026.py
```

### Laboratory 2026 selected design (MBDoE stage)

- Runner:
  `laboratory_2026/run_final_operational_doe_volume_constrained.py`
- Notebook:
  `laboratory_2026/notebooks/fermentation_final_operational_doe_volume_constrained.ipynb`
- Results:
  `laboratory_2026/results/final_operational_doe_volume_constrained/`
- Frozen execution handoff:
  `laboratory_2026/results/design_execution_bundle_2026-06-09/`

```powershell
python fermentation_model\laboratory_2026\run_final_operational_doe_volume_constrained.py
```

### Pilot 2025 integrated model

- Runner: `pilot_2025/run_pilot_2025_co2_solubility_integrated_doe.py`
- Notebook: `pilot_2025/pilot_2025_co2_solubility_integrated_doe.ipynb`
- Results: `pilot_2025/results/co2_solubility_integrated_doe/`

```powershell
python fermentation_model\pilot_2025\run_pilot_2025_co2_solubility_integrated_doe.py
```

## Structural audit

From the repository root:

```powershell
python fermentation_model\tools\campaign_audit.py --check-hashes
python -m pytest fermentation_model\tests -q
```

The audit rejects active Python files or ambiguous results placed back in the
`fermentation_model/` root.
