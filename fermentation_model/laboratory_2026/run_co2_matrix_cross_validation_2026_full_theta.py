from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
FERMENTATION_MODEL_DIR = SCRIPT_DIR.parent
ROOT_DIR = FERMENTATION_MODEL_DIR.parent
RESULTS_DIR = (
    SCRIPT_DIR
    / "results"
    / "co2_matrix_cross_validation_2026_full_theta_sccm_corrected"
)
PLOT_DIR = RESULTS_DIR / "figures"
NOTEBOOK_DIR = SCRIPT_DIR / "notebooks"
NOTEBOOK_PATH = NOTEBOOK_DIR / "co2_solubility_o2_cross_matrix_2026_full_theta.ipynb"
EXECUTED_NOTEBOOK_PATH = (
    NOTEBOOK_DIR / "co2_solubility_o2_cross_matrix_2026_full_theta.executed.ipynb"
)

os.environ.setdefault("MPLBACKEND", "Agg")
_BOOTSTRAP_RUNTIME_DIR = RESULTS_DIR / ".jupyter_runtime"
_BOOTSTRAP_RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("JUPYTER_RUNTIME_DIR", str(_BOOTSTRAP_RUNTIME_DIR))
os.environ.setdefault("IPYTHONDIR", str(_BOOTSTRAP_RUNTIME_DIR / "ipython"))
os.environ.setdefault("JUPYTER_ALLOW_INSECURE_WRITES", "1")

import matplotlib.pyplot as plt
import nbformat
import numpy as np
import pandas as pd
from nbclient import NotebookClient

for path in (FERMENTATION_MODEL_DIR, SCRIPT_DIR, FERMENTATION_MODEL_DIR / "pilot_2025"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from shared import run_new_must_glycerol_estimability_doe as base
from laboratory_2026 import run_co2_matrix_cross_validation_2026 as historical


MODEL_NAME = historical.MODEL_NAME
THRESHOLD_RELEASE_MODEL_NAME = historical.THRESHOLD_RELEASE_MODEL_NAME
LEGACY_MODEL_NAME = historical.LEGACY_MODEL_NAME
HOLDOUTS = historical.HOLDOUTS
EXCLUDED_BATCHES = historical.EXCLUDED_BATCHES
PARAMETER_BOUNDS = historical.PARAMETER_BOUNDS

NATURAL_FULL_THETA_PATH = (
    SCRIPT_DIR / "results" / "estimability_historical_natural" / "theta_natural_full.csv"
)
SYNTHETIC_FULL_THETA_PATH = (
    SCRIPT_DIR
    / "results"
    / "estimability_historical_synthetic_plus_lot2"
    / "theta_synthetic_full.csv"
)
JOINT_FULL_THETA_PATH = (
    FERMENTATION_MODEL_DIR
    / "shared"
    / "results"
    / "new_must_glycerol_overnight_validation"
    / "theta_multistart_07.csv"
)
HISTORICAL_CORRECTED_RESULTS_DIR = historical.SCCM_CORRECTED_RESULTS_DIR
EXPECTED_KINETIC_PARAMETERS = tuple(base.FULL17)
EXPECTED_CO2_PARAMETERS = (*historical._shape_parameter_names(MODEL_NAME), "matrix_gain")
SCCM_FACTOR_G_L_H_PER_SCCM = 0.0404391928807947
STATE_DEFINITIONS = {
    "A_historical": {
        "theta": "historical partial CSV plus DEFAULT_THETA fallback",
        "co2": "saved SCCM-corrected historical CO2 parameters",
        "fit": False,
    },
    "B_full_theta_no_refit": {
        "theta": "complete matrix-specific theta CSV",
        "co2": "same saved SCCM-corrected historical CO2 parameters as A",
        "fit": False,
    },
    "C_full_theta_refit": {
        "theta": "complete matrix-specific theta CSV",
        "co2": "nine original CO2-layer parameters recalibrated",
        "fit": True,
    },
}


# Re-export the established plotting API used by the SOURCE notebook. Every call
# made by this module passes save=False and writes only into the new results tree.
plot_process_timeline_alignment = historical.plot_process_timeline_alignment
plot_sensor_zero_correction = historical.plot_sensor_zero_correction
plot_data_overview = historical.plot_data_overview
plot_sensor_filter_examples = historical.plot_sensor_filter_examples
plot_temperature_profiles = historical.plot_temperature_profiles
plot_parameter_comparison = historical.plot_parameter_comparison
plot_calibration_overlays = historical.plot_calibration_overlays
plot_activation_identifiability = historical.plot_activation_identifiability
plot_initial_release_comparison = historical.plot_initial_release_comparison
plot_onset_model_comparison = historical.plot_onset_model_comparison
plot_pulse_response_comparison = historical.plot_pulse_response_comparison
plot_validation = historical.plot_validation
plot_validation_model_comparison = historical.plot_validation_model_comparison


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _directory_sha256(path: Path) -> dict[str, str]:
    return {
        str(item.relative_to(path)).replace("\\", "/"): _sha256(item)
        for item in sorted(candidate for candidate in path.rglob("*") if candidate.is_file())
    }


def _coerce_bool_column(frame: pd.DataFrame, column: str) -> None:
    if column not in frame or frame[column].dtype == bool:
        return
    parsed = frame[column].astype(str).str.lower().map({"true": True, "false": False})
    if parsed.isna().any():
        raise ValueError(f"Could not parse every value in boolean column {column!r}")
    frame[column] = parsed


def _read_complete_theta(path: Path, label: str) -> tuple[dict[str, float], pd.DataFrame]:
    """Read exactly the 17 kinetic parameters; never consult DEFAULT_THETA."""

    if not path.is_file():
        raise FileNotFoundError(f"Required complete theta does not exist: {path}")
    raw = pd.read_csv(path)
    if {"parameter", "theta"}.issubset(raw.columns):
        parameter_column, value_column = "parameter", "theta"
        declared_source = raw.get("source", pd.Series("", index=raw.index)).astype(str)
    else:
        if raw.shape[1] != 2:
            raise ValueError(
                f"{label} theta must contain parameter/value columns; found {list(raw.columns)}"
            )
        parameter_column, value_column = raw.columns[:2]
        declared_source = pd.Series(str(path.relative_to(FERMENTATION_MODEL_DIR)), index=raw.index)

    parameters = raw[parameter_column].astype(str).str.strip()
    values = pd.to_numeric(raw[value_column], errors="raise")
    if parameters.duplicated().any():
        duplicates = sorted(parameters[parameters.duplicated(keep=False)].unique())
        raise ValueError(f"{label} theta contains duplicate parameters: {duplicates}")
    found = set(parameters)
    expected = set(EXPECTED_KINETIC_PARAMETERS)
    missing = sorted(expected - found)
    unexpected = sorted(found - expected)
    if missing or unexpected or len(raw) != len(EXPECTED_KINETIC_PARAMETERS):
        raise ValueError(
            f"{label} theta must contain exactly {len(EXPECTED_KINETIC_PARAMETERS)} expected "
            f"parameters; missing={missing}, unexpected={unexpected}, rows={len(raw)}"
        )
    if not np.isfinite(values.to_numpy(dtype=float)).all():
        raise ValueError(f"{label} theta contains non-finite values")

    theta_series = pd.Series(values.to_numpy(dtype=float), index=parameters)
    theta = {name: float(theta_series.loc[name]) for name in EXPECTED_KINETIC_PARAMETERS}
    audit = pd.DataFrame(
        {
            "theta_label": label,
            "parameter": EXPECTED_KINETIC_PARAMETERS,
            "theta": [theta[name] for name in EXPECTED_KINETIC_PARAMETERS],
            "declared_source": [
                str(declared_source.iloc[int(np.flatnonzero(parameters.eq(name))[0])])
                for name in EXPECTED_KINETIC_PARAMETERS
            ],
            "csv_path": str(path.relative_to(FERMENTATION_MODEL_DIR)).replace("\\", "/"),
        }
    )
    return theta, audit


def load_complete_theta_sets() -> tuple[dict[str, dict[str, float]], pd.DataFrame, pd.DataFrame]:
    paths = {
        "natural": NATURAL_FULL_THETA_PATH,
        "synthetic": SYNTHETIC_FULL_THETA_PATH,
        "joint": JOINT_FULL_THETA_PATH,
    }
    theta_sets: dict[str, dict[str, float]] = {}
    audits: list[pd.DataFrame] = []
    for label, path in paths.items():
        theta_sets[label], audit = _read_complete_theta(path, label)
        audits.append(audit)
    detail = pd.concat(audits, ignore_index=True)
    summary = pd.DataFrame(
        [
            {
                "theta_label": label,
                "csv_path": str(path.relative_to(FERMENTATION_MODEL_DIR)).replace("\\", "/"),
                "parameter_count": len(theta_sets[label]),
                "expected_count": len(EXPECTED_KINETIC_PARAMETERS),
                "all_17_present": set(theta_sets[label]) == set(EXPECTED_KINETIC_PARAMETERS),
                "sha256": _sha256(path),
                "simulation_use": (
                    "target natural batches"
                    if label == "natural"
                    else "target synthetic batches"
                    if label == "synthetic"
                    else "validated reference only; original cross-matrix logic has no joint driver"
                ),
            }
            for label, path in paths.items()
        ]
    )
    if not summary["all_17_present"].all():
        raise AssertionError("Complete-theta validation did not pass for every required vector")
    return theta_sets, detail, summary


def _historical_theta_audit(
    historical_theta: dict[str, dict[str, float]],
    complete_theta: dict[str, dict[str, float]],
) -> pd.DataFrame:
    sources = {
        "natural": (historical.NATURAL_THETA_PATH, None),
        "synthetic": (
            historical.SYNTHETIC_THETA_PATH,
            "historical_synthetic_plus_lot2",
        ),
    }
    rows: list[dict[str, object]] = []
    for matrix, (path, case) in sources.items():
        frame = pd.read_csv(path)
        if case is not None:
            frame = frame[frame["case"].astype(str).eq(case)].copy()
        serialized = set(frame["parameter"].astype(str))
        for parameter in EXPECTED_KINETIC_PARAMETERS:
            mode = "serialized_csv" if parameter in serialized else "DEFAULT_THETA_fallback"
            historical_value = float(historical_theta[matrix][parameter])
            expected_historical_value = (
                historical_value
                if mode == "serialized_csv"
                else float(base.DEFAULT_THETA[parameter])
            )
            if not math.isclose(
                historical_value, expected_historical_value, rel_tol=0.0, abs_tol=1e-14
            ):
                raise AssertionError(
                    f"Historical reconstruction audit failed for {matrix}/{parameter}"
                )
            rows.append(
                {
                    "matrix": matrix,
                    "parameter": parameter,
                    "historical_load_mode": mode,
                    "historical_value": historical_value,
                    "complete_theta_value": float(complete_theta[matrix][parameter]),
                    "absolute_change": float(complete_theta[matrix][parameter])
                    - historical_value,
                    "historical_csv": str(path.relative_to(FERMENTATION_MODEL_DIR)).replace(
                        "\\", "/"
                    ),
                }
            )
    return pd.DataFrame(rows)


def _scale_historical_table(frame: pd.DataFrame, ratio: float) -> pd.DataFrame:
    scaled = frame.copy()
    for column in scaled.columns:
        if "g_l_h" in str(column).lower():
            numeric = pd.to_numeric(scaled[column], errors="coerce")
            if numeric.notna().any():
                scaled[column] = numeric * ratio
    scaled["sccm_conversion"] = historical.SCCM_CORRECTED_CONVERSION.name
    return scaled


def _load_prefit_tables(ratio: float) -> dict[str, pd.DataFrame]:
    names = {
        "sensor_qc": "co2_sensor_qc_10min.csv",
        "qc_summary": "co2_sensor_qc_summary.csv",
        "sensor_zero_offsets": "sensor_zero_offsets.csv",
        "sampling_schedule": "sampling_schedule_used.csv",
        "chemical_support": "chemical_process_support.csv",
        "natural_nutrient_pulses": "natural_nutrient_pulse_details.csv",
        "nutrient_pulses": "effective_nutrient_pulses.csv",
        "exclusions": "excluded_experiments.csv",
        "inventory": "experiment_inventory.csv",
    }
    scaled_names = {"sensor_qc", "qc_summary", "sensor_zero_offsets", "inventory"}
    tables: dict[str, pd.DataFrame] = {}
    for key, filename in names.items():
        frame = pd.read_csv(historical.RESULTS_DIR / filename)
        tables[key] = _scale_historical_table(frame, ratio) if key in scaled_names else frame
    return tables


def _load_historical_co2_fits() -> tuple[dict[str, dict[str, float]], pd.DataFrame]:
    table = pd.read_csv(HISTORICAL_CORRECTED_RESULTS_DIR / "fit_parameters.csv")
    starts = pd.read_csv(HISTORICAL_CORRECTED_RESULTS_DIR / "fit_start_diagnostics.csv")
    fits: dict[str, dict[str, float]] = {}
    for matrix, group in table.groupby("calibration_matrix", sort=False):
        estimates = dict(zip(group["parameter"].astype(str), group["estimate"].astype(float)))
        missing = sorted(set(EXPECTED_CO2_PARAMETERS) - set(estimates))
        if missing:
            raise ValueError(f"Historical SCCM-corrected CO2 fit for {matrix} is missing {missing}")
        best_wsse = float(
            starts.loc[starts["matrix"].astype(str).eq(str(matrix)), "wsse_equal_batch"].min()
        )
        fits[str(matrix)] = {
            **{name: float(estimates[name]) for name in EXPECTED_CO2_PARAMETERS},
            "model": MODEL_NAME,
            "wsse_equal_batch": best_wsse,
        }
    if set(fits) != {"natural", "synthetic"}:
        raise ValueError(f"Unexpected historical CO2 matrices: {sorted(fits)}")
    return fits, table


def _fixed_parameter_residual(
    parameters: dict[str, float],
    batch_names: list[str],
    observations: pd.DataFrame,
    cache: dict[str, historical.DriverCache],
) -> np.ndarray:
    """The historical objective evaluated with every CO2 parameter frozen."""

    residuals: list[np.ndarray] = []
    for batch_name in batch_names:
        group = observations[observations["batch"].eq(batch_name)]
        raw = historical.raw_qgas_prediction(
            cache[batch_name],
            parameters["kCO2_release_h"],
            parameters["CO2sat_scale"],
            parameters["O2_qmax_mg_gdw_h"],
            parameters["O2_initial_scale"],
            chemistry_aligned=True,
            nitrogen_boost_transition=True,
            pulse_t_rise_h=parameters["pulse_t_rise_h"],
            pulse_activity_gain=parameters["pulse_activity_gain"],
            continuous_release=True,
            bounded_chemical_activation=True,
            chem_activation_start_fraction=parameters[
                "chem_activation_start_fraction"
            ],
            chem_activation_duration_fraction=parameters[
                "chem_activation_duration_fraction"
            ],
        )
        prediction = float(parameters["matrix_gain"]) * raw
        observed = group["co2_rate_g_l_h"].to_numpy(dtype=float)
        sigma_floor = (
            float(group["residual_sigma_floor_g_l_h"].iloc[0])
            if "residual_sigma_floor_g_l_h" in group
            else historical.CO2_RESIDUAL_SIGMA_FLOOR_G_L_H
        )
        sigma = max(sigma_floor, 0.10 * float(group["co2_rate_g_l_h"].max()))
        censored = group["left_censored"].astype(bool).to_numpy()
        batch_residuals: list[np.ndarray] = []
        if (~censored).any():
            batch_residuals.append((prediction[~censored] - observed[~censored]) / sigma)
        if censored.any():
            limit = group["detection_limit_g_l_h"].to_numpy(dtype=float)[censored]
            batch_residuals.append(np.maximum(prediction[censored] - limit, 0.0) / sigma)
        residuals.append(np.concatenate(batch_residuals) / math.sqrt(len(group)))

        threshold = historical._onset_threshold(group)
        observed_onset = historical._sustained_onset_h(
            group["t_h"].to_numpy(dtype=float), observed, threshold
        )
        predicted_onset = historical._sustained_onset_h(
            group["t_h"].to_numpy(dtype=float), prediction, threshold
        )
        if np.isfinite(observed_onset):
            if not np.isfinite(predicted_onset):
                predicted_onset = float(group["t_h"].max()) + historical.ONSET_SIGMA_H
            residuals.append(
                np.asarray(
                    [(predicted_onset - observed_onset) / historical.ONSET_SIGMA_H]
                )
            )

        pulse_time_h = cache[batch_name].n_pulse_time_h
        observed_peak_h = historical._postpulse_peak_time_h(
            group["t_h"].to_numpy(dtype=float), observed, pulse_time_h
        )
        predicted_peak_h = historical._postpulse_peak_time_h(
            group["t_h"].to_numpy(dtype=float), prediction, pulse_time_h
        )
        if np.isfinite(observed_peak_h):
            if not np.isfinite(predicted_peak_h):
                predicted_peak_h = min(
                    float(group["t_h"].max()),
                    pulse_time_h + historical.PULSE_PEAK_WINDOW_H,
                )
            residuals.append(
                np.asarray(
                    [
                        (predicted_peak_h - observed_peak_h)
                        / historical.PULSE_PEAK_SIGMA_H
                    ]
                )
            )
    return np.concatenate(residuals)


def _objective_table(
    state: str,
    fits: dict[str, dict[str, float]],
    observations: pd.DataFrame,
    cache: dict[str, historical.DriverCache],
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for matrix, parameters in fits.items():
        batches = historical._calibration_batch_names(matrix, observations)
        residual = _fixed_parameter_residual(parameters, batches, observations, cache)
        rows.append(
            {
                "state": state,
                "matrix": matrix,
                "wsse_equal_batch_fixed_co2": float(np.dot(residual, residual)),
                "n_residuals": len(residual),
                "matrix_gain": float(parameters["matrix_gain"]),
                "co2_refitted": bool(STATE_DEFINITIONS[state]["fit"]),
            }
        )
    rows.append(
        {
            "state": state,
            "matrix": "all",
            "wsse_equal_batch_fixed_co2": float(
                sum(row["wsse_equal_batch_fixed_co2"] for row in rows)
            ),
            "n_residuals": int(sum(row["n_residuals"] for row in rows)),
            "matrix_gain": np.nan,
            "co2_refitted": bool(STATE_DEFINITIONS[state]["fit"]),
        }
    )
    return pd.DataFrame(rows)


def _fit_by_matrix(
    observations: pd.DataFrame,
    cache: dict[str, historical.DriverCache],
    n_starts: int,
    max_nfev: int,
    seed: int,
    model_variant: str = MODEL_NAME,
) -> tuple[dict[str, dict[str, float]], pd.DataFrame]:
    fits: dict[str, dict[str, float]] = {}
    starts: list[pd.DataFrame] = []
    for matrix in ("synthetic", "natural"):
        parameters, matrix_starts = historical.fit_matrix(
            matrix,
            observations,
            cache,
            n_starts=n_starts,
            max_nfev=max_nfev,
            seed=seed,
            model_variant=model_variant,
        )
        fits[matrix] = parameters
        starts.append(matrix_starts)
    return fits, pd.concat(starts, ignore_index=True)


def _state_parameter_tables(
    state_fits: dict[str, dict[str, dict[str, float]]]
) -> tuple[pd.DataFrame, pd.DataFrame]:
    tables: list[pd.DataFrame] = []
    for state, fits in state_fits.items():
        table = historical.fit_parameter_table(fits)
        table.insert(0, "state", state)
        table["co2_refitted"] = bool(STATE_DEFINITIONS[state]["fit"])
        tables.append(table)
    parameters = pd.concat(tables, ignore_index=True)
    transitions = (
        ("A_historical", "B_full_theta_no_refit", "A_to_B"),
        ("B_full_theta_no_refit", "C_full_theta_refit", "B_to_C"),
        ("A_historical", "C_full_theta_refit", "A_to_C"),
    )
    rows: list[dict[str, object]] = []
    for left, right, transition in transitions:
        left_table = parameters[parameters["state"].eq(left)]
        right_table = parameters[parameters["state"].eq(right)]
        merged = left_table.merge(
            right_table,
            on=["calibration_matrix", "parameter"],
            suffixes=("_left", "_right"),
            validate="one_to_one",
        )
        for row in merged.itertuples(index=False):
            absolute = float(row.estimate_right - row.estimate_left)
            rows.append(
                {
                    "transition": transition,
                    "left_state": left,
                    "right_state": right,
                    "calibration_matrix": row.calibration_matrix,
                    "parameter": row.parameter,
                    "left_estimate": float(row.estimate_left),
                    "right_estimate": float(row.estimate_right),
                    "absolute_change": absolute,
                    "percent_change": 100.0 * absolute / abs(float(row.estimate_left)),
                    "left_active_bound": bool(row.active_bound_left),
                    "right_active_bound": bool(row.active_bound_right),
                }
            )
    return parameters, pd.DataFrame(rows)


def _state_metric_change_table(state_metrics: pd.DataFrame) -> pd.DataFrame:
    metrics = (
        "rmse_g_l_h",
        "nrmse_peak",
        "bias_g_l_h",
        "correlation",
        "r2",
        "predicted_peak_g_l_h",
        "predicted_peak_time_h",
        "integral_ratio_pred_over_observed_lower_bound",
        "predicted_onset_h",
        "onset_delay_h",
        "predicted_first_emission_0p005_h",
        "predicted_visual_rise_duration_h",
        "visual_rise_duration_error_h",
        "predicted_postpulse_peak_h",
        "postpulse_peak_delay_h",
    )
    keys = [
        "calibration_matrix",
        "target_matrix",
        "batch",
        "experiment_code",
        "role",
    ]
    transitions = (
        ("A_historical", "B_full_theta_no_refit", "A_to_B"),
        ("B_full_theta_no_refit", "C_full_theta_refit", "B_to_C"),
        ("A_historical", "C_full_theta_refit", "A_to_C"),
    )
    rows: list[dict[str, object]] = []
    for left, right, transition in transitions:
        merged = state_metrics[state_metrics["state"].eq(left)][keys + list(metrics)].merge(
            state_metrics[state_metrics["state"].eq(right)][keys + list(metrics)],
            on=keys,
            suffixes=("_left", "_right"),
            validate="one_to_one",
        )
        for row in merged.itertuples(index=False):
            common = {key: getattr(row, key) for key in keys}
            for metric in metrics:
                left_value = float(getattr(row, f"{metric}_left"))
                right_value = float(getattr(row, f"{metric}_right"))
                absolute = right_value - left_value
                rows.append(
                    {
                        "transition": transition,
                        **common,
                        "metric": metric,
                        "left_value": left_value,
                        "right_value": right_value,
                        "absolute_change": absolute,
                        "percent_change": (
                            100.0 * absolute / abs(left_value)
                            if np.isfinite(left_value) and abs(left_value) > 1e-12
                            else np.nan
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _integral(time_h: np.ndarray, values: np.ndarray) -> float:
    if hasattr(np, "trapezoid"):
        return float(np.trapezoid(values, time_h))
    return float(np.trapz(values, time_h))


def _shape_scale_comparison(state_predictions: pd.DataFrame) -> pd.DataFrame:
    keys = ["calibration_matrix", "target_matrix", "batch", "experiment_code", "role"]
    transitions = (
        ("A_historical", "B_full_theta_no_refit", "A_to_B"),
        ("B_full_theta_no_refit", "C_full_theta_refit", "B_to_C"),
        ("A_historical", "C_full_theta_refit", "A_to_C"),
    )
    rows: list[dict[str, object]] = []
    for left, right, transition in transitions:
        left_frame = state_predictions[state_predictions["state"].eq(left)]
        right_frame = state_predictions[state_predictions["state"].eq(right)]
        merged = left_frame.merge(
            right_frame,
            on=keys + ["time_h"],
            suffixes=("_left", "_right"),
            validate="one_to_one",
        )
        for group_key, group in merged.groupby(keys, sort=True):
            left_values = group["predicted_g_l_h_left"].to_numpy(dtype=float)
            right_values = group["predicted_g_l_h_right"].to_numpy(dtype=float)
            time_h = group["time_h"].to_numpy(dtype=float)
            denominator = float(np.dot(left_values, left_values))
            best_scale = (
                float(np.dot(left_values, right_values) / denominator)
                if denominator > 1e-16
                else np.nan
            )
            direct_rmse = float(np.sqrt(np.mean(np.square(right_values - left_values))))
            shape_rmse = float(
                np.sqrt(np.mean(np.square(right_values - best_scale * left_values)))
            )
            scale_fraction = (
                1.0 - (shape_rmse * shape_rmse) / (direct_rmse * direct_rmse)
                if direct_rmse > 1e-14
                else np.nan
            )
            corr = (
                float(np.corrcoef(left_values, right_values)[0, 1])
                if np.std(left_values) > 0 and np.std(right_values) > 0
                else np.nan
            )
            rows.append(
                {
                    "transition": transition,
                    **dict(zip(keys, group_key)),
                    "best_multiplicative_scale_right_from_left": best_scale,
                    "direct_prediction_rmse_g_l_h": direct_rmse,
                    "shape_rmse_after_best_scale_g_l_h": shape_rmse,
                    "fraction_squared_change_explained_by_scale": scale_fraction,
                    "prediction_shape_correlation": corr,
                    "integral_ratio_right_over_left": _integral(time_h, right_values)
                    / max(_integral(time_h, left_values), 1e-16),
                    "peak_ratio_right_over_left": float(np.max(right_values))
                    / max(float(np.max(left_values)), 1e-16),
                    "peak_time_change_h": float(time_h[int(np.argmax(right_values))])
                    - float(time_h[int(np.argmax(left_values))]),
                }
            )
    return pd.DataFrame(rows)


def _matrix_gain_compensation(
    state_fits: dict[str, dict[str, dict[str, float]]],
    state_predictions: pd.DataFrame,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for matrix in ("synthetic", "natural"):
        integrals: dict[str, dict[str, float]] = {}
        for state in STATE_DEFINITIONS:
            selected = state_predictions[
                state_predictions["state"].eq(state)
                & state_predictions["calibration_matrix"].eq(matrix)
                & state_predictions["target_matrix"].eq(matrix)
                & state_predictions["role"].eq("calibration")
            ]
            raw_total = 0.0
            scaled_total = 0.0
            for _, group in selected.groupby("batch", sort=True):
                raw_total += _integral(
                    group["time_h"].to_numpy(dtype=float),
                    group["raw_model_qgas_g_l_h"].to_numpy(dtype=float),
                )
                scaled_total += _integral(
                    group["time_h"].to_numpy(dtype=float),
                    group["predicted_g_l_h"].to_numpy(dtype=float),
                )
            integrals[state] = {"raw": raw_total, "scaled": scaled_total}
        gain_a = float(state_fits["A_historical"][matrix]["matrix_gain"])
        gain_c = float(state_fits["C_full_theta_refit"][matrix]["matrix_gain"])
        direct_raw_ratio = (
            integrals["B_full_theta_no_refit"]["raw"]
            / integrals["A_historical"]["raw"]
        )
        rows.append(
            {
                "matrix": matrix,
                "historical_matrix_gain": gain_a,
                "refit_matrix_gain": gain_c,
                "absolute_change": gain_c - gain_a,
                "percent_change": 100.0 * (gain_c - gain_a) / abs(gain_a),
                "direct_raw_integral_ratio_B_over_A": direct_raw_ratio,
                "gain_ratio_C_over_A": gain_c / gain_a,
                "gain_only_compensated_ratio_to_A": direct_raw_ratio * gain_c / gain_a,
                "other_co2_layer_raw_ratio_C_over_B": (
                    integrals["C_full_theta_refit"]["raw"]
                    / integrals["B_full_theta_no_refit"]["raw"]
                ),
                "final_scaled_integral_ratio_C_over_A": (
                    integrals["C_full_theta_refit"]["scaled"]
                    / integrals["A_historical"]["scaled"]
                ),
                "interpretation_guardrail": (
                    "matrix_gain is an empirical observation/scale parameter, not physical gas recovery"
                ),
            }
        )
    return pd.DataFrame(rows)


def _model_comparison(
    comparison_fits: dict[str, dict[str, float]],
    observations: pd.DataFrame,
    cache: dict[str, historical.DriverCache],
    model_variant: str,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    predictions, metrics, validation = historical.predict_and_score(
        comparison_fits, observations, cache, model_variant=model_variant
    )
    return predictions, metrics, validation


def _validation_model_comparison(
    earlier: pd.DataFrame, current: pd.DataFrame
) -> pd.DataFrame:
    keys = ["scenario", "calibration_matrix", "target_matrix", "batch", "experiment_code"]
    metrics = [
        "rmse_g_l_h",
        "nrmse_peak",
        "correlation",
        "r2",
        "integral_ratio_pred_over_observed_lower_bound",
        "observed_onset_h",
        "predicted_onset_h",
        "onset_delay_h",
        "predicted_first_emission_0p005_h",
        "observed_visual_rise_duration_h",
        "predicted_visual_rise_duration_h",
        "visual_rise_duration_error_h",
        "observed_postpulse_peak_h",
        "predicted_postpulse_peak_h",
        "observed_pulse_t_rise_h",
        "predicted_pulse_t_rise_h",
        "postpulse_peak_delay_h",
    ]
    comparison = earlier[keys + metrics].merge(
        current[keys + metrics],
        on=keys,
        suffixes=("_threshold_release", "_continuous_release"),
        validate="one_to_one",
    )
    comparison["rmse_change_continuous_minus_threshold_release"] = (
        comparison["rmse_g_l_h_continuous_release"]
        - comparison["rmse_g_l_h_threshold_release"]
    )
    comparison["abs_onset_error_change_continuous_minus_threshold_release"] = (
        comparison["onset_delay_h_continuous_release"].abs()
        - comparison["onset_delay_h_threshold_release"].abs()
    )
    comparison["abs_postpulse_peak_error_change_continuous_minus_threshold_release"] = (
        comparison["postpulse_peak_delay_h_continuous_release"].abs()
        - comparison["postpulse_peak_delay_h_threshold_release"].abs()
    )
    comparison[
        "abs_visual_rise_duration_error_change_continuous_minus_threshold_release"
    ] = (
        comparison["visual_rise_duration_error_h_continuous_release"].abs()
        - comparison["visual_rise_duration_error_h_threshold_release"].abs()
    )
    return comparison


def _filter_impact(
    observations: pd.DataFrame,
    cache: dict[str, historical.DriverCache],
    n_starts: int,
    max_nfev: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    unfiltered = observations.copy()
    unfiltered["co2_rate_g_l_h"] = unfiltered["co2_rate_raw_g_l_h"]
    unfiltered["left_censored"] = False
    fits, _ = _fit_by_matrix(
        unfiltered,
        cache,
        n_starts=max(3, min(n_starts, 5)),
        max_nfev=max_nfev,
        seed=seed,
    )
    parameters = historical.fit_parameter_table(fits)
    predictions, _, validation = historical.predict_and_score(fits, unfiltered, cache)
    common_support = predictions.drop(
        columns=["observed_g_l_h", "left_censored", "detection_limit_g_l_h"]
    ).merge(
        observations[
            [
                "batch",
                "t_h",
                "co2_rate_g_l_h",
                "left_censored",
                "detection_limit_g_l_h",
                "early_emission_threshold_g_l_h",
            ]
        ],
        left_on=["batch", "time_h"],
        right_on=["batch", "t_h"],
        how="left",
        validate="many_to_one",
    )
    rows: list[dict[str, object]] = []
    for row in validation.itertuples(index=False):
        group = common_support[
            common_support["calibration_matrix"].eq(row.calibration_matrix)
            & common_support["batch"].eq(row.batch)
        ].sort_values("time_h")
        metric = historical._metric_row(
            row.calibration_matrix,
            row.target_matrix,
            row.batch,
            group["co2_rate_g_l_h"].to_numpy(dtype=float),
            group["predicted_g_l_h"].to_numpy(dtype=float),
            group["time_h"].to_numpy(dtype=float),
            row.role,
            group["left_censored"].astype(bool).to_numpy(),
            group["detection_limit_g_l_h"].to_numpy(dtype=float),
            MODEL_NAME,
            cache[row.batch].n_pulse_time_h,
            float(group["early_emission_threshold_g_l_h"].iloc[0])
            if "early_emission_threshold_g_l_h" in group
            else historical.EARLY_EMISSION_THRESHOLD_G_L_H,
        )
        metric["scenario"] = row.scenario
        rows.append(metric)
    common_validation = pd.DataFrame(rows)
    keys = ["calibration_matrix", "target_matrix", "batch", "experiment_code"]
    metrics = ["rmse_g_l_h", "nrmse_peak", "bias_g_l_h", "correlation", "r2"]
    filtered_validation = historical.predict_and_score(
        {matrix: fit for matrix, fit in fits.items()}, observations, cache
    )[2]
    # The established comparison evaluates the unfiltered fit and the primary
    # filtered/censored fit on common support. The caller replaces the right side
    # below with the actual primary-C validation.
    placeholder = common_validation[keys + metrics].merge(
        filtered_validation[keys + metrics],
        on=keys,
        suffixes=("_unfiltered_fit_common_support", "_filtered_censored"),
    )
    return parameters, validation, common_validation, placeholder


def _reproduction_audit(
    predictions: pd.DataFrame, observations: pd.DataFrame
) -> pd.DataFrame:
    saved = pd.read_csv(HISTORICAL_CORRECTED_RESULTS_DIR / "prediction_rows.csv")
    keys = ["calibration_matrix", "target_matrix", "batch", "time_h"]
    merged = saved.merge(
        predictions,
        on=keys,
        suffixes=("_saved", "_recomputed"),
        validate="one_to_one",
    )
    if len(merged) != len(saved) or len(merged) != len(predictions):
        raise AssertionError("Historical SCCM-corrected prediction support was not reproduced")
    rows = []
    for column in ("observed_g_l_h", "predicted_g_l_h", "raw_model_qgas_g_l_h"):
        difference = (
            pd.to_numeric(merged[f"{column}_recomputed"], errors="raise")
            - pd.to_numeric(merged[f"{column}_saved"], errors="raise")
        ).abs()
        rows.append(
            {
                "quantity": column,
                "n_rows": len(difference),
                "max_absolute_difference": float(difference.max()),
                "mean_absolute_difference": float(difference.mean()),
            }
        )
    audit = pd.DataFrame(rows)
    if float(audit["max_absolute_difference"].max()) > 1e-9:
        raise AssertionError("Historical SCCM-corrected baseline was not reproduced numerically")
    return audit


def _with_state(frame: pd.DataFrame, state: str) -> pd.DataFrame:
    output = frame.copy()
    output.insert(0, "state", state)
    return output


def _save_csvs(result: dict[str, object]) -> None:
    mapping = {
        "observations": "co2_observations_hourly.csv",
        "sensor_qc": "co2_sensor_qc_10min.csv",
        "qc_summary": "co2_sensor_qc_summary.csv",
        "sensor_zero_offsets": "sensor_zero_offsets.csv",
        "sampling_schedule": "sampling_schedule_used.csv",
        "chemical_support": "chemical_process_support.csv",
        "natural_nutrient_pulses": "natural_nutrient_pulse_details.csv",
        "nutrient_pulses": "effective_nutrient_pulses.csv",
        "exclusions": "excluded_experiments.csv",
        "temperature_inputs": "temperature_model_inputs.csv",
        "temperature_alignment": "temperature_alignment_summary.csv",
        "inventory": "experiment_inventory.csv",
        "driver_diagnostics": "driver_diagnostics.csv",
        "fit_parameters": "fit_parameters.csv",
        "fit_starts": "fit_start_diagnostics.csv",
        "jacobian_identifiability": "activation_jacobian_identifiability.csv",
        "jacobian_singular_values": "activation_jacobian_singular_values.csv",
        "local_parameter_correlations": "activation_local_parameter_correlations.csv",
        "activation_profiles": "activation_objective_profiles.csv",
        "loo_activation_estimates": "activation_leave_one_batch_out_estimates.csv",
        "loo_activation_summary": "activation_leave_one_batch_out_summary.csv",
        "previous_fit_parameters": "threshold_release_fit_parameters.csv",
        "previous_fit_starts": "threshold_release_fit_starts.csv",
        "previous_predictions": "threshold_release_prediction_rows.csv",
        "previous_batch_metrics": "threshold_release_batch_metrics.csv",
        "previous_validation": "threshold_release_validation_summary.csv",
        "legacy_fit_parameters": "legacy_slow_transition_fit_parameters.csv",
        "legacy_fit_starts": "legacy_slow_transition_fit_starts.csv",
        "legacy_predictions": "legacy_slow_transition_prediction_rows.csv",
        "legacy_batch_metrics": "legacy_slow_transition_batch_metrics.csv",
        "legacy_validation": "legacy_slow_transition_validation_summary.csv",
        "source_transition_diagnostics": "source_transition_diagnostics.csv",
        "previous_source_transition_diagnostics": "threshold_release_source_diagnostics.csv",
        "legacy_source_transition_diagnostics": "legacy_slow_transition_source_diagnostics.csv",
        "model_comparison": "model_comparison_validation.csv",
        "legacy_model_comparison": "legacy_vs_nitrogen_boost_validation.csv",
        "predictions": "prediction_rows.csv",
        "batch_metrics": "batch_metrics.csv",
        "validation": "validation_summary.csv",
        "baseline_fit_parameters": "baseline_unfiltered_fit_parameters.csv",
        "baseline_validation": "baseline_unfiltered_validation_summary.csv",
        "baseline_common_support_validation": "baseline_unfiltered_fit_common_support_validation.csv",
        "filter_impact": "filter_impact_validation.csv",
        "theta_validation": "theta_validation.csv",
        "theta_validation_summary": "theta_validation_summary.csv",
        "theta_historical_audit": "theta_historical_reconstruction_audit.csv",
        "state_objectives": "three_state_objective_summary.csv",
        "state_parameters": "three_state_co2_parameters.csv",
        "state_parameter_changes": "three_state_co2_parameter_changes.csv",
        "state_predictions": "three_state_prediction_rows.csv",
        "state_batch_metrics": "three_state_batch_metrics.csv",
        "state_validation": "three_state_validation_summary.csv",
        "state_metric_changes": "three_state_batch_metric_changes.csv",
        "pairwise_shape_scale": "three_state_shape_scale_comparison.csv",
        "matrix_gain_compensation": "matrix_gain_compensation.csv",
        "identifiability_state_comparison": "identifiability_state_comparison.csv",
        "identifiability_correlations_state": "identifiability_correlations_state.csv",
        "activation_profiles_state": "activation_objective_profiles_state.csv",
        "loo_activation_estimates_state": "activation_leave_one_batch_out_estimates_state.csv",
        "loo_activation_summary_state": "activation_leave_one_batch_out_summary_state.csv",
        "state_transition_diagnostics": "three_state_source_transition_diagnostics.csv",
        "historical_reproduction_audit": "historical_reproduction_audit.csv",
        "frozen_mask_audit": "frozen_mask_audit.csv",
        "native_mask_diagnostic": "native_corrected_mask_diagnostic.csv",
    }
    for key, filename in mapping.items():
        value = result.get(key)
        if isinstance(value, pd.DataFrame):
            value.to_csv(RESULTS_DIR / filename, index=False)


def _save_figure(figure: plt.Figure, filename: str, dpi: int = 180) -> None:
    figure.savefig(PLOT_DIR / filename, dpi=dpi, bbox_inches="tight")
    plt.close(figure)


def plot_three_state_overlays(
    state_predictions: pd.DataFrame, save: bool = True
) -> plt.Figure:
    native = state_predictions[
        state_predictions["calibration_matrix"].eq(state_predictions["target_matrix"])
    ]
    batches = list(native.sort_values(["target_matrix", "batch"])["batch"].unique())
    ncols = 3
    nrows = int(math.ceil(len(batches) / ncols))
    figure, axes = plt.subplots(nrows, ncols, figsize=(14, 2.6 * nrows), squeeze=False)
    colors = {
        "A_historical": "#777777",
        "B_full_theta_no_refit": "#D55E00",
        "C_full_theta_refit": "#0072B2",
    }
    labels = {
        "A_historical": "A historical",
        "B_full_theta_no_refit": "B full theta, fixed CO2",
        "C_full_theta_refit": "C full theta, refit CO2",
    }
    for axis, batch in zip(axes.ravel(), batches):
        group = native[native["batch"].eq(batch)]
        observed = group[group["state"].eq("A_historical")]
        axis.plot(
            observed["time_h"], observed["observed_g_l_h"], color="black", lw=1.0, label="observed"
        )
        for state in STATE_DEFINITIONS:
            selected = group[group["state"].eq(state)]
            axis.plot(
                selected["time_h"],
                selected["predicted_g_l_h"],
                color=colors[state],
                lw=1.1,
                label=labels[state],
            )
        pulse = float(observed["pulse_time_h"].iloc[0]) if not observed.empty else np.nan
        if np.isfinite(pulse):
            axis.axvline(pulse, color="#CC79A7", ls=":", lw=0.8)
        axis.set_title(str(batch))
        axis.set_xlabel("time [h]")
        axis.set_ylabel("CO2 [g/L/h]")
        axis.grid(alpha=0.2)
    for axis in axes.ravel()[len(batches) :]:
        axis.set_visible(False)
    handles, labels_out = axes.ravel()[0].get_legend_handles_labels()
    figure.suptitle(
        "A/B/C prediction comparison with SCCM_CORRECTED observations",
        y=0.995,
        fontsize=14,
        fontweight="semibold",
    )
    figure.legend(
        handles,
        labels_out,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.969),
        ncol=4,
        frameon=False,
        fontsize=9,
        handlelength=2.4,
        columnspacing=1.5,
    )
    # Reserve a dedicated top band for title + legend. tight_layout alone
    # previously placed both at the same height and made them overlap.
    figure.tight_layout(rect=(0.015, 0.01, 0.985, 0.925), h_pad=1.5, w_pad=1.0)
    if save:
        PLOT_DIR.mkdir(parents=True, exist_ok=True)
        figure.savefig(PLOT_DIR / "three_state_prediction_overlays.png", dpi=180, bbox_inches="tight")
    return figure


def plot_matrix_gain_three_states(
    state_parameters: pd.DataFrame, save: bool = True
) -> plt.Figure:
    selected = state_parameters[state_parameters["parameter"].eq("matrix_gain")].copy()
    pivot = selected.pivot(
        index="calibration_matrix", columns="state", values="estimate"
    ).reindex(columns=list(STATE_DEFINITIONS))
    figure, axis = plt.subplots(figsize=(7.5, 4.2))
    pivot.plot(kind="bar", ax=axis, color=["#777777", "#D55E00", "#0072B2"])
    axis.set_ylabel("matrix_gain (empirical observation scale)")
    axis.set_xlabel("matrix")
    axis.set_title("matrix_gain: historical, full theta/no refit, full theta/refit")
    axis.grid(axis="y", alpha=0.2)
    axis.legend(frameon=False, fontsize=8)
    figure.tight_layout()
    if save:
        PLOT_DIR.mkdir(parents=True, exist_ok=True)
        figure.savefig(PLOT_DIR / "matrix_gain_three_states.png", dpi=180, bbox_inches="tight")
    return figure


def _save_suite_plots(result: dict[str, object]) -> None:
    calls = [
        (
            plot_data_overview(
                result["observations"], result["nutrient_pulses"], save=False
            ),
            "co2_data_overview.png",
        ),
        (
            plot_sensor_zero_correction(
                result["sensor_qc"], result["sensor_zero_offsets"], save=False
            ),
            "sensor_zero_offset_correction.png",
        ),
        (
            plot_sensor_filter_examples(
                result["sensor_qc"],
                result["sampling_schedule"],
                result["nutrient_pulses"],
                save=False,
            ),
            "sensor_artifact_filter_examples.png",
        ),
        (
            plot_temperature_profiles(
                result["observations"],
                result["temperature_inputs"],
                result["nutrient_pulses"],
                save=False,
            ),
            "temperature_profiles_model_input.png",
        ),
        (
            plot_process_timeline_alignment(
                result["inventory"], result["nutrient_pulses"], save=False
            ),
            "process_timeline_alignment.png",
        ),
        (
            plot_parameter_comparison(result["fit_parameters"], save=False),
            "parameter_comparison.png",
        ),
        (
            plot_activation_identifiability(
                result["activation_profiles"], result["loo_activation_summary"], save=False
            ),
            "activation_identifiability_profiles.png",
        ),
        (
            plot_validation(result["predictions"], result["validation"], save=False),
            "heldout_cross_matrix_validation.png",
        ),
        (
            plot_onset_model_comparison(
                result["batch_metrics"], result["previous_batch_metrics"], save=False
            ),
            "onset_model_comparison.png",
        ),
        (
            plot_validation_model_comparison(
                result["predictions"],
                result["previous_predictions"],
                result["validation"],
                result["previous_validation"],
                save=False,
            ),
            "heldout_model_comparison.png",
        ),
        (
            plot_initial_release_comparison(
                result["predictions"],
                result["previous_predictions"],
                result["batch_metrics"],
                result["previous_batch_metrics"],
                save=False,
            ),
            "initial_gradual_release_comparison.png",
        ),
        (
            plot_pulse_response_comparison(
                result["predictions"],
                result["previous_predictions"],
                result["batch_metrics"],
                result["previous_batch_metrics"],
                result["source_transition_diagnostics"],
                save=False,
            ),
            "nutrient_pulse_response_comparison.png",
        ),
        (
            plot_three_state_overlays(result["state_predictions"], save=False),
            "three_state_prediction_overlays.png",
        ),
        (
            plot_matrix_gain_three_states(result["state_parameters"], save=False),
            "matrix_gain_three_states.png",
        ),
    ]
    for matrix in ("synthetic", "natural"):
        calls.append(
            (
                plot_calibration_overlays(result["predictions"], matrix, save=False),
                f"calibration_overlays_{matrix}.png",
            )
        )
    for figure, filename in calls:
        _save_figure(figure, filename)


def run_analysis(
    n_starts: int = 5, max_nfev: int = 300, seed: int = 20260812
) -> dict[str, object]:
    """Run A/B/C on one corrected-SCCM observation support and save the full suite."""

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    PLOT_DIR.mkdir(parents=True, exist_ok=True)
    protected_before = {
        "legacy": _directory_sha256(historical.RESULTS_DIR),
        "sccm_corrected": _directory_sha256(HISTORICAL_CORRECTED_RESULTS_DIR),
    }

    # Required gate: all three complete CSVs are validated before any simulation.
    theta_sets, theta_validation, theta_validation_summary = load_complete_theta_sets()
    batches, historical_theta, natural_tables = historical.load_batches()
    theta_historical_audit = _historical_theta_audit(historical_theta, theta_sets)

    conversion_factor = historical.SCCM_CORRECTED_CONVERSION.factor_g_l_h_per_sccm(2.0)
    if not math.isclose(
        conversion_factor,
        SCCM_FACTOR_G_L_H_PER_SCCM,
        rel_tol=0.0,
        abs_tol=5e-16,
    ):
        raise AssertionError(
            f"Unexpected SCCM conversion {conversion_factor}; expected {SCCM_FACTOR_G_L_H_PER_SCCM}"
        )
    legacy_factor = historical.LEGACY_SCCM_CONVERSION.factor_g_l_h_per_sccm(2.0)
    conversion_ratio = conversion_factor / legacy_factor
    observations = pd.read_csv(
        HISTORICAL_CORRECTED_RESULTS_DIR / "co2_observations_hourly.csv"
    )
    _coerce_bool_column(observations, "left_censored")
    if "sccm_conversion" not in observations or not observations[
        "sccm_conversion"
    ].astype(str).eq("SCCM_CORRECTED").all():
        raise AssertionError("Primary observations are not marked SCCM_CORRECTED")

    prefit = _load_prefit_tables(conversion_ratio)
    cache_a, driver_diagnostics_a = historical.build_driver_cache(
        batches, historical_theta, observations
    )
    complete_matrix_theta = {
        "natural": theta_sets["natural"],
        "synthetic": theta_sets["synthetic"],
    }
    cache_full, driver_diagnostics = historical.build_driver_cache(
        batches, complete_matrix_theta, observations
    )
    temperature_inputs = historical.temperature_model_input_table(cache_full)
    temperature_alignment = historical.temperature_alignment_summary(
        observations, temperature_inputs
    )

    historical_fits, _ = _load_historical_co2_fits()
    predictions_a, metrics_a, validation_a = historical.predict_and_score(
        historical_fits, observations, cache_a
    )
    historical_reproduction_audit = _reproduction_audit(predictions_a, observations)
    predictions_b, metrics_b, validation_b = historical.predict_and_score(
        historical_fits, observations, cache_full
    )

    fits_c, fit_starts = _fit_by_matrix(
        observations, cache_full, n_starts, max_nfev, seed
    )
    fit_parameters = historical.fit_parameter_table(fits_c)
    predictions_c, metrics_c, validation_c = historical.predict_and_score(
        fits_c, observations, cache_full
    )
    state_fits = {
        "A_historical": historical_fits,
        "B_full_theta_no_refit": historical_fits,
        "C_full_theta_refit": fits_c,
    }
    state_predictions = pd.concat(
        [
            _with_state(predictions_a, "A_historical"),
            _with_state(predictions_b, "B_full_theta_no_refit"),
            _with_state(predictions_c, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )
    state_batch_metrics = pd.concat(
        [
            _with_state(metrics_a, "A_historical"),
            _with_state(metrics_b, "B_full_theta_no_refit"),
            _with_state(metrics_c, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )
    state_validation = pd.concat(
        [
            _with_state(validation_a, "A_historical"),
            _with_state(validation_b, "B_full_theta_no_refit"),
            _with_state(validation_c, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )
    state_objectives = pd.concat(
        [
            _objective_table("A_historical", historical_fits, observations, cache_a),
            _objective_table(
                "B_full_theta_no_refit", historical_fits, observations, cache_full
            ),
            _objective_table("C_full_theta_refit", fits_c, observations, cache_full),
        ],
        ignore_index=True,
    )
    state_parameters, state_parameter_changes = _state_parameter_tables(state_fits)
    state_metric_changes = _state_metric_change_table(state_batch_metrics)
    pairwise_shape_scale = _shape_scale_comparison(state_predictions)
    matrix_gain_compensation = _matrix_gain_compensation(state_fits, state_predictions)

    jac_a, singular_a, correlations_a = historical.jacobian_identifiability_diagnostics(
        historical_fits, observations, cache_a
    )
    profiles_a = historical.profile_activation_parameters(
        historical_fits, observations, cache_a
    )
    loo_estimates_a, loo_summary_a = historical.leave_one_batch_out_stability(
        historical_fits, observations, cache_a, seed
    )
    jac_c, singular_c, correlations_c = historical.jacobian_identifiability_diagnostics(
        fits_c, observations, cache_full
    )
    profiles_c = historical.profile_activation_parameters(fits_c, observations, cache_full)
    loo_estimates_c, loo_summary_c = historical.leave_one_batch_out_stability(
        fits_c, observations, cache_full, seed
    )
    identifiability_state_comparison = pd.concat(
        [_with_state(jac_a, "A_historical"), _with_state(jac_c, "C_full_theta_refit")],
        ignore_index=True,
    )
    identifiability_correlations_state = pd.concat(
        [
            _with_state(correlations_a, "A_historical"),
            _with_state(correlations_c, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )
    activation_profiles_state = pd.concat(
        [
            _with_state(profiles_a, "A_historical"),
            _with_state(profiles_c, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )
    loo_activation_estimates_state = pd.concat(
        [
            _with_state(loo_estimates_a, "A_historical"),
            _with_state(loo_estimates_c, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )
    loo_activation_summary_state = pd.concat(
        [
            _with_state(loo_summary_a, "A_historical"),
            _with_state(loo_summary_c, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )

    previous_fits, previous_fit_starts = _fit_by_matrix(
        observations,
        cache_full,
        n_starts=max(3, min(n_starts, 5)),
        max_nfev=max_nfev,
        seed=seed,
        model_variant=THRESHOLD_RELEASE_MODEL_NAME,
    )
    previous_fit_parameters = historical.fit_parameter_table(previous_fits)
    previous_predictions, previous_batch_metrics, previous_validation = _model_comparison(
        previous_fits, observations, cache_full, THRESHOLD_RELEASE_MODEL_NAME
    )
    legacy_fits, legacy_fit_starts = _fit_by_matrix(
        observations,
        cache_full,
        n_starts=max(3, min(n_starts, 5)),
        max_nfev=max_nfev,
        seed=seed,
        model_variant=LEGACY_MODEL_NAME,
    )
    legacy_fit_parameters = historical.fit_parameter_table(legacy_fits)
    legacy_predictions, legacy_batch_metrics, legacy_validation = _model_comparison(
        legacy_fits, observations, cache_full, LEGACY_MODEL_NAME
    )
    source_transition_diagnostics = historical.transition_diagnostics(
        fits_c, observations, cache_full, model_variant=MODEL_NAME
    )
    previous_source_transition_diagnostics = historical.transition_diagnostics(
        previous_fits,
        observations,
        cache_full,
        model_variant=THRESHOLD_RELEASE_MODEL_NAME,
    )
    legacy_source_transition_diagnostics = historical.transition_diagnostics(
        legacy_fits, observations, cache_full, model_variant=LEGACY_MODEL_NAME
    )
    state_transition_diagnostics = pd.concat(
        [
            _with_state(
                historical.transition_diagnostics(
                    historical_fits, observations, cache_a, model_variant=MODEL_NAME
                ),
                "A_historical",
            ),
            _with_state(
                historical.transition_diagnostics(
                    historical_fits, observations, cache_full, model_variant=MODEL_NAME
                ),
                "B_full_theta_no_refit",
            ),
            _with_state(source_transition_diagnostics, "C_full_theta_refit"),
        ],
        ignore_index=True,
    )
    model_comparison = _validation_model_comparison(previous_validation, validation_c)
    legacy_model_comparison = legacy_validation.merge(
        validation_c,
        on=["scenario", "calibration_matrix", "target_matrix", "batch", "experiment_code"],
        suffixes=("_legacy_slow_transition", "_continuous_release"),
        validate="one_to_one",
    )

    (
        baseline_fit_parameters,
        baseline_validation,
        baseline_common_support_validation,
        _,
    ) = _filter_impact(observations, cache_full, n_starts, max_nfev, seed)
    filter_keys = ["calibration_matrix", "target_matrix", "batch", "experiment_code"]
    filter_metrics = ["rmse_g_l_h", "nrmse_peak", "bias_g_l_h", "correlation", "r2"]
    filter_impact = baseline_common_support_validation[
        filter_keys + filter_metrics
    ].merge(
        validation_c[filter_keys + filter_metrics],
        on=filter_keys,
        suffixes=("_unfiltered_fit_common_support", "_filtered_censored"),
    )
    filter_impact["rmse_change"] = (
        filter_impact["rmse_g_l_h_filtered_censored"]
        - filter_impact["rmse_g_l_h_unfiltered_fit_common_support"]
    )

    frozen_mask_audit = pd.read_csv(
        HISTORICAL_CORRECTED_RESULTS_DIR / "frozen_mask_audit.csv"
    )
    native_mask_diagnostic = pd.read_csv(
        HISTORICAL_CORRECTED_RESULTS_DIR / "native_corrected_mask_diagnostic.csv"
    )
    result: dict[str, object] = {
        **prefit,
        "observations": observations,
        "temperature_inputs": temperature_inputs,
        "temperature_alignment": temperature_alignment,
        "driver_diagnostics": driver_diagnostics,
        "historical_driver_diagnostics": driver_diagnostics_a,
        "fits": fits_c,
        "fit_parameters": fit_parameters,
        "fit_starts": fit_starts,
        "jacobian_identifiability": jac_c,
        "jacobian_singular_values": singular_c,
        "local_parameter_correlations": correlations_c,
        "activation_profiles": profiles_c,
        "loo_activation_estimates": loo_estimates_c,
        "loo_activation_summary": loo_summary_c,
        "previous_fits": previous_fits,
        "previous_fit_parameters": previous_fit_parameters,
        "previous_fit_starts": previous_fit_starts,
        "previous_predictions": previous_predictions,
        "previous_batch_metrics": previous_batch_metrics,
        "previous_validation": previous_validation,
        "legacy_fits": legacy_fits,
        "legacy_fit_parameters": legacy_fit_parameters,
        "legacy_fit_starts": legacy_fit_starts,
        "legacy_predictions": legacy_predictions,
        "legacy_batch_metrics": legacy_batch_metrics,
        "legacy_validation": legacy_validation,
        "source_transition_diagnostics": source_transition_diagnostics,
        "previous_source_transition_diagnostics": previous_source_transition_diagnostics,
        "legacy_source_transition_diagnostics": legacy_source_transition_diagnostics,
        "model_comparison": model_comparison,
        "legacy_model_comparison": legacy_model_comparison,
        "predictions": predictions_c,
        "batch_metrics": metrics_c,
        "validation": validation_c,
        "baseline_fit_parameters": baseline_fit_parameters,
        "baseline_validation": baseline_validation,
        "baseline_common_support_validation": baseline_common_support_validation,
        "filter_impact": filter_impact,
        "theta_validation": theta_validation,
        "theta_validation_summary": theta_validation_summary,
        "theta_historical_audit": theta_historical_audit,
        "state_objectives": state_objectives,
        "state_parameters": state_parameters,
        "state_parameter_changes": state_parameter_changes,
        "state_predictions": state_predictions,
        "state_batch_metrics": state_batch_metrics,
        "state_validation": state_validation,
        "state_metric_changes": state_metric_changes,
        "pairwise_shape_scale": pairwise_shape_scale,
        "matrix_gain_compensation": matrix_gain_compensation,
        "identifiability_state_comparison": identifiability_state_comparison,
        "identifiability_correlations_state": identifiability_correlations_state,
        "activation_profiles_state": activation_profiles_state,
        "loo_activation_estimates_state": loo_activation_estimates_state,
        "loo_activation_summary_state": loo_activation_summary_state,
        "state_transition_diagnostics": state_transition_diagnostics,
        "historical_reproduction_audit": historical_reproduction_audit,
        "frozen_mask_audit": frozen_mask_audit,
        "native_mask_diagnostic": native_mask_diagnostic,
    }
    _save_csvs(result)
    _save_suite_plots(result)

    protected_after = {
        "legacy": _directory_sha256(historical.RESULTS_DIR),
        "sccm_corrected": _directory_sha256(HISTORICAL_CORRECTED_RESULTS_DIR),
    }
    if protected_before != protected_after:
        raise AssertionError("A protected historical results directory changed")
    manifest = {
        "experiment": "co2_matrix_cross_validation_2026_full_theta_sccm_corrected",
        "model": MODEL_NAME,
        "states": STATE_DEFINITIONS,
        "sccm_conversion": {
            "name": "SCCM_CORRECTED",
            "factor_g_l_h_per_sccm_at_2L": conversion_factor,
            "required_factor": SCCM_FACTOR_G_L_H_PER_SCCM,
            "MW_CO2_g_mol": historical.CORRECTED_CO2_MOLAR_MASS_G_MOL,
            "Vm_L_mol": historical.CORRECTED_MOLAR_VOLUME_L_MOL,
            "K_CO2": historical.CORRECTED_CO2_RESPONSE_FACTOR,
            "support_policy": "saved corrected observations; historical timestamps and censor mask frozen",
        },
        "theta": {
            "natural": str(NATURAL_FULL_THETA_PATH.relative_to(FERMENTATION_MODEL_DIR)).replace(
                "\\", "/"
            ),
            "synthetic": str(
                SYNTHETIC_FULL_THETA_PATH.relative_to(FERMENTATION_MODEL_DIR)
            ).replace("\\", "/"),
            "joint": str(JOINT_FULL_THETA_PATH.relative_to(FERMENTATION_MODEL_DIR)).replace(
                "\\", "/"
            ),
            "required_parameter_count": len(EXPECTED_KINETIC_PARAMETERS),
            "joint_use": "loaded and validated; not used because the original cross-matrix transfer evaluates target-matrix upstream drivers",
        },
        "co2_parameters": list(EXPECTED_CO2_PARAMETERS),
        "parameter_bounds": PARAMETER_BOUNDS,
        "objective": "unchanged full-profile + onset + post-pulse peak residual, equal batch weighting and left-censor hinge",
        "n_starts": n_starts,
        "max_nfev": max_nfev,
        "seed": seed,
        "holdouts": HOLDOUTS,
        "excluded_batches": EXCLUDED_BATCHES,
        "historical_co2_parameters_source": str(
            HISTORICAL_CORRECTED_RESULTS_DIR.relative_to(FERMENTATION_MODEL_DIR)
        ).replace("\\", "/"),
        "historical_results_unchanged": True,
        "identifiability": {
            "states": ["A_historical", "C_full_theta_refit"],
            "B_full_theta_no_refit": "not applicable because B is deliberately not an optimum",
            "methods": ["local log-Jacobian", "objective profiles", "leave-one-batch-out"],
        },
        "preserved_out_of_scope": [
            "natural delta-N 0.14 retained",
            "density-1040 timing retained",
            "nitrogen boost retained",
            "gate and O2 structure retained",
            "LAB016-LAB018 not introduced",
        ],
        "tail_metric": "not added: the established suite has no operational tail definition",
    }
    (RESULTS_DIR / "analysis_manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    result["manifest"] = manifest
    result["protected_results_unchanged"] = True
    return result


def create_notebook() -> None:
    """Clone the canonical SOURCE analysis and add explicit full-theta A/B/C sections."""

    NOTEBOOK_DIR.mkdir(parents=True, exist_ok=True)
    notebook = nbformat.read(historical.NOTEBOOK_PATH, as_version=4)
    for cell in notebook.cells:
        if cell.cell_type == "code":
            cell.outputs = []
            cell.execution_count = None

    notebook.cells[0].source = """> **NUEVA CALIBRACIÓN — FULL THETA + SCCM_CORRECTED**
>
> Los tres vectores cinéticos completos se cargan explícitamente desde CSV y se validan contra los
> 17 parámetros esperados antes de simular. Natural y sintético usan sus vectores específicos; el
> vector conjunto `theta_multistart_07.csv` se valida como referencia, pero no sustituye los drivers
> de la matriz objetivo en la transferencia cruzada porque esa es la lógica del notebook SOURCE.
>
> Toda la comparación A/B/C usa **1 SCCM = 0.0404391928807947 g L⁻¹ h⁻¹**. Los parámetros CO₂ de A
> y B son exactamente los guardados por la calibración SCCM-corregida previa; por tanto A→B aísla el
> cambio de theta. Solo C reajusta los nueve parámetros originales de la capa CO₂.
>
> Los notebooks y resultados históricos permanecen inmutables."""
    notebook.cells[1].source = """# CO₂ 2026 full theta: calibración y validación cruzada

## Resultado que se evalúa

Se conserva la suite científica A–H del SOURCE histórico y se añade la comparación explícita:

- **A — histórico:** theta parcial reconstruido con fallback a `DEFAULT_THETA` + CO₂ histórico SCCM-corregido.
- **B — corrección sin refit:** theta completo correcto + exactamente el mismo CO₂ de A.
- **C — nueva calibración:** theta completo correcto y congelado + refit exclusivo de los nueve parámetros CO₂ originales.

Datos, batches, exclusiones, holdouts, preprocesamiento, objetivo, pesos, bounds, multistart,
arquitectura, gate, O₂, pulso y comparadores se mantienen. `matrix_gain` se interpreta únicamente
como escala empírica de observación, nunca como eficiencia física de recuperación de gas.

""" + notebook.cells[1].source
    notebook.cells[3].source = notebook.cells[3].source.replace(
        "run_co2_matrix_cross_validation_2026 as analysis",
        "run_co2_matrix_cross_validation_2026_full_theta as analysis",
    )
    notebook.cells[13].source = "## Estado C — recalibración CO₂ por matriz con theta completo congelado"
    notebook.cells[15].source += (
        "\n\nEn esta sección todos los estimates corresponden al estado C. Los estados A y B "
        "comparten exactamente los parámetros CO₂ históricos; B no ejecuta fitting."
    )
    notebook.cells[18].source += (
        "\n\nLa identificabilidad se compara entre A y C, ambos óptimos de calibración. No se "
        "atribuye identificabilidad a B porque deliberadamente no es un óptimo."
    )
    notebook.cells[30].source = """## Artefactos

La ejecución guarda la suite completa histórica para el estado C y, además, theta auditados,
reconstrucción del fallback, predicciones/métricas A–B–C, cambios pareados, separación escala/forma,
compensación de `matrix_gain` e identificabilidad A versus C. Todos los artefactos se escriben en
`results/co2_matrix_cross_validation_2026_full_theta_sccm_corrected/`."""

    audit_cells = [
        nbformat.v4.new_markdown_cell(
            """## Auditoría obligatoria de theta y SCCM

Esta celda se ejecuta después de construir los drivers; si cualquiera de los tres CSV no contiene
exactamente los 17 parámetros esperados, el runner falla antes de la primera simulación. La tabla de
reconstrucción identifica las seis filas que históricamente provenían de `DEFAULT_THETA`."""
        ),
        nbformat.v4.new_code_cell(
            """display(result["theta_validation_summary"])
display(result["theta_historical_audit"])
print("SCCM_CORRECTED [g/L/h/SCCM]:", result["manifest"]["sccm_conversion"]["factor_g_l_h_per_sccm_at_2L"])
print("Historical baseline reproduced:")
display(result["historical_reproduction_audit"])"""
        ),
        nbformat.v4.new_markdown_cell(
            """## Comparación explícita A/B/C

A→B cuantifica solo el reemplazo del theta. B→C cuantifica la readaptación de la capa CO₂. A→C es
el efecto final. La descomposición escala/forma ajusta únicamente un multiplicador diagnóstico entre
dos curvas ya calculadas; no modifica B ni constituye un refit. Un valor alto de la fracción explicada
por escala indica cambio mayormente multiplicativo."""
        ),
        nbformat.v4.new_code_cell(
            """display(result["state_objectives"])
display(result["state_parameter_changes"])
display(result["matrix_gain_compensation"])
display(result["state_validation"])
display(
    result["pairwise_shape_scale"]
    .query("transition == 'A_to_B'")
    .sort_values("direct_prediction_rmse_g_l_h", ascending=False)
)
display(result["identifiability_state_comparison"])
fig = analysis.plot_three_state_overlays(result["state_predictions"], save=False)
plt.show()
fig = analysis.plot_matrix_gain_three_states(result["state_parameters"], save=False)
plt.show()"""
        ),
    ]
    notebook.cells[13:13] = audit_cells

    notebook.cells[-2].source = """print("SCCM_CORRECTED:", result["manifest"]["sccm_conversion"]["factor_g_l_h_per_sccm_at_2L"], "g/L/h/SCCM")
display(result["state_objectives"])
print()
print("matrix_gain (parámetro empírico de observación):")
display(result["matrix_gain_compensation"])

direct = result["pairwise_shape_scale"].query("transition == 'A_to_B'")
native = direct.query("calibration_matrix == target_matrix")
print()
print("Batches más sensibles a A→B (fits nativos):")
display(native.nlargest(8, "direct_prediction_rmse_g_l_h")[[
    "calibration_matrix", "target_matrix", "experiment_code", "batch", "role",
    "direct_prediction_rmse_g_l_h", "best_multiplicative_scale_right_from_left",
    "shape_rmse_after_best_scale_g_l_h", "fraction_squared_change_explained_by_scale",
    "integral_ratio_right_over_left", "peak_ratio_right_over_left", "peak_time_change_h"
]])

print()
print("Holdouts y transferencia A/B/C:")
display(result["state_validation"])
print()
print("Parámetros en límite por estado:")
display(result["state_parameters"].query("active_bound"))
print()
print("Identificabilidad local A vs C:")
display(result["identifiability_state_comparison"])
print()
print("Artefactos:", analysis.RESULTS_DIR.relative_to(ROOT))"""

    notebook.metadata.kernelspec = {
        "display_name": "Python 3",
        "language": "python",
        "name": "python3",
    }
    nbformat.write(notebook, NOTEBOOK_PATH)


def execute_notebook(timeout: int = 7200) -> None:
    runtime_dir = RESULTS_DIR / ".jupyter_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    os.environ["JUPYTER_RUNTIME_DIR"] = str(runtime_dir)
    notebook = nbformat.read(NOTEBOOK_PATH, as_version=4)
    client = NotebookClient(
        notebook,
        timeout=timeout,
        kernel_name="python3",
        resources={"metadata": {"path": str(ROOT_DIR)}},
    )
    client.execute()
    nbformat.write(notebook, EXECUTED_NOTEBOOK_PATH)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--create-only", action="store_true")
    parser.add_argument("--timeout", type=int, default=7200)
    args = parser.parse_args()
    create_notebook()
    if not args.create_only:
        execute_notebook(timeout=args.timeout)
    print(NOTEBOOK_PATH)
    if not args.create_only:
        print(EXECUTED_NOTEBOOK_PATH)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
