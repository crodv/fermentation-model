# Computational reproducibility

The objective is that a result can be traced to one Git commit, one immutable
input snapshot and one explicit model/solver configuration.

## Conda environment

The canonical environment name is `fermentation`, matching
`fermentation_model/environment.yml`. From an Anaconda or Miniforge prompt:

```powershell
conda env create -f fermentation_model\environment.yml
conda activate fermentation
idaes get-extensions
python -c "import pyomo.environ as pyo; print(pyo.SolverFactory('ipopt').available())"
```

`idaes get-extensions` installs the IDAES binary extensions, including the
supported IPOPT distribution.

Windows PATH note: native DLL resolution can depend on the order of the
environment's `Library\bin` directory and the IDAES extensions directory in
`PATH`. The verified operational setup, including the required ordering and
troubleshooting of native crashes such as `0xC06D007F`, is documented in
`AGENTS.md` at the repository root.

## Reference environment

The verified scientific reference environment for the currently committed
results:

| Component | Version |
| --- | --- |
| Python | 3.11.16 |
| NumPy | 1.26.4 |
| SciPy | 1.13.1 |
| pandas | 2.2.2 |
| matplotlib | 3.9.2 |
| Pyomo | 6.10.1 |
| ipykernel | 7.3.0 |
| pytest | 9.1.1 |

`environment.yml` intentionally stays unpinned apart from `python=3.11`; the
table above is the reference combination behind the committed results. Full
environment exports (`conda env export --from-history`,
`conda list --explicit`) are optional future artifacts that may be generated
and committed to freeze the environment; they are not part of the repository
today.

## Working directory

Run runners and tests from the repository root. Runner-generated notebooks
execute with the repository root as their kernel working directory.

```powershell
python fermentation_model\laboratory_2026\run_co2_matrix_cross_validation_2026.py
python -m pytest fermentation_model\tests -q
```

## Canonical versioned inputs

- `data/Laboratorio 2026/raw_data/Fernanda Folch.ics`: nutrient-pulse calendar
  for the historical natural-must analysis. It is versioned in the repository
  and resolved through repo-relative paths; no external download is required.
- Lot 2 CO2 loading prefers the filtered `CO2_FILT_*` exports whenever they
  are readable; raw CO2 files are used only as a fallback for uncovered
  intervals (labelled `raw_rolling_median_fallback` in the QC tables).
- `data/mem2026/` contains the LAB013–LAB018 natural-must measurements
  (Oculyze `report.csv` tables and accompanying exports) used for current
  analysis and validation work.

## Reference CO2 run

The committed CO2 cross-matrix results were produced by
`fermentation_model/laboratory_2026/run_co2_matrix_cross_validation_2026.py`
with:

- seed `20260812`
- multistart `n_starts=5`
- `max_nfev=300`

The analysis notebook is
`laboratory_2026/notebooks/co2_solubility_o2_cross_matrix_2026.ipynb`; its
`.executed.ipynb` sibling keeps the outputs of the full execution as narrative
evidence.

## Before every scientific run

1. Select campaign and experiment IDs from `campaigns/experiments.csv`.
2. Copy `config/local_ipopt_reference.json` to a run-specific configuration and
   fill every required field listed there.
3. Confirm raw-data integrity:

   ```powershell
   python fermentation_model\tools\campaign_audit.py --check-hashes
   ```

4. Capture the execution context:

   ```powershell
   python fermentation_model\tools\capture_run_context.py `
     --config path\to\run_config.json `
     --output path\to\results\run_manifest.json
   ```

5. Store solver logs, parameter estimates, objective contributions, residuals,
   FIM diagnostics and figures beside that manifest.

## Tests

`pytest` is the primary test tool:

```powershell
python -m pytest fermentation_model\tests -q
```

Operational context at the time of this update: 116 passed / 3 failed /
14 warnings. The three failures are known campaign-registry and historical
raw-tree checks pending a later registry revision; they are operational
context, not a permanent acceptance requirement.

## Scientific acceptance gates

- The selected local optimum must be reproducible from the recorded initial
  guess and solver options.
- No profile-likelihood point may improve the baseline objective beyond the
  declared numerical tolerance. If it does, rebase the optimum first.
- Parameters at bounds must be reported explicitly.
- FIM and eigenvalue comparisons must use the same parameter scaling and
  measurement-error model.
- Calibration and validation experiment sets must be listed separately.
- Executed notebooks are narrative evidence; they are not the source of model
  functions and must never be imported by cell index.

## What is not authoritative

Particle-swarm and broad multistart files are retained for traceability but are
not part of the preferred scientific workflow. Administrative `AXX` bundles
are renditions/deliverables and are excluded from model provenance.
