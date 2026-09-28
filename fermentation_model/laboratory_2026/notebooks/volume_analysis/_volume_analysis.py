"""Read-only, frozen-parameter volume sensitivity for natural LAB004--LAB012.

The 65 mL Alcolyzer loss and feed-solution volume are scenario assumptions,
not verified measurements. This module does not alter the production model.
"""

from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp


FERMENTATION_MODEL_DIR = Path(__file__).resolve().parents[3]
if str(FERMENTATION_MODEL_DIR) not in sys.path:
    sys.path.insert(0, str(FERMENTATION_MODEL_DIR))

from laboratory_2026 import run_co2_matrix_cross_validation_2026 as co2
from laboratory_2026 import run_estimability_historical_by_medium as natural
from shared import run_new_must_glycerol_estimability_doe as kinetic


THETA_PATH = (
    FERMENTATION_MODEL_DIR / "laboratory_2026" / "results"
    / "estimability_historical_natural" / "theta_natural_full.csv"
)
CO2_PARAMETER_PATH = (
    FERMENTATION_MODEL_DIR / "laboratory_2026" / "results"
    / "co2_matrix_cross_validation_2026_full_theta_sccm_corrected"
    / "three_state_co2_parameters.csv"
)
CO2_OBSERVATION_PATH = (
    FERMENTATION_MODEL_DIR / "laboratory_2026" / "results"
    / "co2_matrix_cross_validation_2026_sccm_corrected"
    / "co2_observations_hourly.csv"
)

COLORS = {
    "actual": "#333333",
    "muestras_65": "#0072B2",
    "nutricion_20": "#009E73",
    "ambos": "#D55E00",
}
STATE_UNITS = {
    "X": "kg/m³", "Xd": "kg/m³", "N": "kg/m³",
    "G": "g/L", "F": "g/L", "E": "g/L", "Gly": "g/L",
}


def load_context():
    """Load only the natural historical data; no model is refitted."""
    chemistry, original_batches, _, tables = natural.make_medium_batches("natural")
    schedule = co2.natural_nutrient_pulse_schedule(chemistry, tables["metadata"])
    batches = co2.override_natural_nutrient_pulses(original_batches, schedule)
    tables["chemistry"] = chemistry
    tables["nutrient_pulses"] = schedule
    return {batch.batch: batch for batch in batches}, tables


def load_frozen_parameters():
    rows = pd.read_csv(THETA_PATH)
    names = rows["parameter"].astype(str)
    if len(rows) != len(kinetic.FULL17) or set(names) != set(kinetic.FULL17):
        raise ValueError("theta_natural_full.csv must contain the exact 17 kinetic names")
    if names.duplicated().any():
        raise ValueError("theta_natural_full.csv contains duplicate parameters")
    theta = dict(zip(names, pd.to_numeric(rows["theta"], errors="raise")))
    fit_rows = pd.read_csv(CO2_PARAMETER_PATH)
    selected = fit_rows[
        fit_rows["state"].eq("C_full_theta_refit")
        & fit_rows["calibration_matrix"].eq("natural")
    ]
    expected = set(co2._shape_parameter_names(co2.MODEL_NAME)) | {"matrix_gain"}
    if len(selected) != len(expected) or set(selected["parameter"]) != expected:
        raise ValueError("The frozen natural CO2 fit is incomplete")
    co2_fit = dict(zip(selected["parameter"], selected["estimate"].astype(float)))
    return theta, co2_fit


def make_event_ledger(
    batch: str,
    tables: dict[str, pd.DataFrame],
    *,
    alcolyzer_ml: float = 65.0,
    feed_ml: float = 0.0,
    other_loss_ml_per_visit: float = 0.0,
    include_t0_sample: bool = True,
) -> pd.DataFrame:
    """Build a scenario ledger; E observations are only a sampling proxy.

    A finite homologated ethanol value does not independently prove that an
    Alcolyzer aliquot was removed or that it measured exactly 65 mL.
    """
    if min(alcolyzer_ml, feed_ml, other_loss_ml_per_visit) < 0:
        raise ValueError("Scenario volumes must be nonnegative")
    meta = tables["metadata"].set_index("batch")
    if batch not in meta.index:
        raise KeyError(batch)
    initial_l = float(meta.loc[batch, "reactor_volume_l"])
    chemistry = tables["chemistry"]
    visits = chemistry[chemistry["batch"].astype(str).eq(batch)].copy()
    visits = visits[pd.to_numeric(visits["time_h"], errors="coerce").notna()]
    visits = visits[~visits["sample_id"].astype(str).str.endswith("-N")]
    visits = visits.sort_values("time_h").drop_duplicates("time_h")

    events: list[dict[str, object]] = []
    for row in visits.itertuples(index=False):
        time_h = float(row.time_h)
        if time_h == 0.0 and not include_t0_sample:
            continue
        ethanol_observed = bool(np.isfinite(float(row.E_g_l)))
        loss_ml = other_loss_ml_per_visit + (alcolyzer_ml if ethanol_observed else 0.0)
        events.append({
            "batch": batch, "time_h": time_h, "order": 0,
            "event": "sample", "sample_id": str(row.sample_id),
            "ethanol_observed": ethanol_observed,
            "volume_delta_l": -loss_ml / 1000.0,
            "added_yan_g": 0.0,
            "volume_source": f"scenario: {alcolyzer_ml:g} mL per finite E observation"
                             " plus other assumed loss; not verified",
        })

    nutrient = tables["nutrient_pulses"]
    nutrient = nutrient[nutrient["batch"].astype(str).eq(batch)]
    for row in nutrient.itertuples(index=False):
        events.append({
            "batch": batch, "time_h": float(row.model_pulse_time_h), "order": 1,
            "event": "nutrition", "sample_id": "", "ethanol_observed": False,
            "volume_delta_l": feed_ml / 1000.0,
            "added_yan_g": float(row.total_yan_mg) / 1000.0,
            "volume_source": "scenario: feed-solution volume is not recorded",
        })

    ledger = pd.DataFrame(events).sort_values(["time_h", "order"]).reset_index(drop=True)
    volume = initial_l
    before, after = [], []
    for event in ledger.itertuples(index=False):
        before.append(volume)
        volume += float(event.volume_delta_l)
        if volume <= 0.0:
            raise ValueError(f"Nonpositive reactor volume for {batch} at {event.time_h} h")
        after.append(volume)
    ledger["volume_before_l"] = before
    ledger["volume_after_l"] = after
    ledger["initial_volume_l"] = initial_l
    ledger["initial_volume_source"] = str(meta.loc[batch, "reactor_volume_source"])
    return ledger


def make_ledgers(tables, *, alcolyzer_ml, feed_ml, include_t0_sample=True):
    names = sorted(tables["chemistry"]["batch"].astype(str).unique())
    return {
        name: make_event_ledger(
            name, tables, alcolyzer_ml=alcolyzer_ml, feed_ml=feed_ml,
            include_t0_sample=include_t0_sample,
        )
        for name in names
    }


def volume_at(ledger: pd.DataFrame, times, *, side: str = "left") -> np.ndarray:
    """Return V just before (left) or after (right) same-time events."""
    if side not in {"left", "right"}:
        raise ValueError(side)
    query = np.asarray(times, dtype=float)
    event_times = ledger["time_h"].to_numpy(dtype=float)
    after = ledger["volume_after_l"].to_numpy(dtype=float)
    initial = float(ledger["initial_volume_l"].iloc[0])
    positions = np.searchsorted(event_times, query, side=side) - 1
    values = np.concatenate(([initial], after))
    return values[positions + 1]


def simulate_with_volume(batch, theta, output_time, ledger, *, sample_event_order="sample_before_action", integration_max_step_h=2.0):
    """Reuse core ODE; add physically mixed jumps at recorded event times."""
    if sample_event_order not in {"sample_before_action", "action_before_sample"}:
        raise ValueError(sample_event_order)
    times = np.asarray(sorted(set(float(t) for t in output_time)), dtype=float)
    if len(times) == 0:
        raise ValueError("At least one output time is required")
    start = float(batch.time[0])
    if times[0] < start - 1e-9:
        raise ValueError("Output precedes the batch origin")
    if times[0] > start:
        times = np.insert(times, 0, start)
    events = {
        float(t): group.sort_values("order")
        for t, group in ledger.groupby("time_h", sort=True)
        if start - 1e-9 <= float(t) <= float(times[-1]) + 1e-9
    }
    timeline = sorted(set(times) | set(events))
    current = kinetic.initial_vector(batch)
    current_time = start
    records: dict[float, np.ndarray] = {}
    output_set = set(times)
    n_index = kinetic.STATE_NAMES.index("N")
    active_n_times = [float(t) for t, amount in batch.pulses.get("N", ()) if amount > 0]

    for time_h in timeline:
        if time_h > current_time + 1e-12:
            sol = solve_ivp(
                lambda t, y: kinetic.rhs(t, y, theta, batch),
                (current_time, time_h), current, t_eval=[time_h], method="LSODA",
                rtol=1e-6, atol=1e-8, max_step=float(integration_max_step_h),
            )
            if not sol.success:
                raise RuntimeError(f"Core integration failed for {batch.batch}: {sol.message}")
            current = np.asarray(sol.y[:, -1], dtype=float)
            current_time = time_h
        if sample_event_order == "sample_before_action" and time_h in output_set:
            records[time_h] = current.copy()
        event_group = events.get(time_h)
        for event in (() if event_group is None else event_group.itertuples(index=False)):
            if event.event == "sample":
                continue  # Homogeneous removal changes V and total mass, not C.
            before = float(event.volume_before_l)
            after = float(event.volume_after_l)
            current = current * (before / after)
            if any(abs(time_h - pulse_time) < 1e-7 for pulse_time in active_n_times):
                current[n_index] += float(event.added_yan_g) / after
        if sample_event_order == "action_before_sample" and time_h in output_set:
            records[time_h] = current.copy()

    values = np.vstack([records[float(t)] for t in times])
    for idx, state in enumerate(kinetic.STATE_NAMES):
        low, high = kinetic.STATE_BOUNDS[state]
        values[:, idx] = np.clip(values[:, idx], low, high)
    return pd.DataFrame(values, index=times, columns=kinetic.STATE_NAMES)


@contextmanager
def volume_simulator(ledgers):
    """Temporarily supply volume-aware core trajectories to the CO2 driver builder."""
    original_simulate = kinetic.simulate

    def simulate(batch, theta, output_time=None, **kwargs):
        if batch.batch not in ledgers:
            return original_simulate(batch, theta, output_time, **kwargs)
        if output_time is None:
            output_time = batch.time
        return simulate_with_volume(batch, theta, output_time, ledgers[batch.batch], **kwargs)

    with patch.object(kinetic, "simulate", simulate):
        yield


def load_co2_observations() -> pd.DataFrame:
    observations = pd.read_csv(CO2_OBSERVATION_PATH)
    return observations[
        observations["matrix"].eq("natural")
        & observations["batch"].astype(str).str.fullmatch(r"LAB00[4-9]|LAB01[0-2]")
    ].copy()


def build_volume_aware_cache(batches, theta, observations, ledgers):
    with volume_simulator(ledgers):
        cache, _ = co2.build_driver_cache(batches, {"natural": theta}, observations)
    return cache


def co2_prediction_sccm(cache, fit, ledger, observation_times):
    qgas = co2.raw_qgas_prediction(
        cache,
        fit["kCO2_release_h"], fit["CO2sat_scale"],
        fit["O2_qmax_mg_gdw_h"], fit["O2_initial_scale"],
        chemistry_aligned=True, nitrogen_boost_transition=True,
        pulse_t_rise_h=fit["pulse_t_rise_h"],
        pulse_activity_gain=fit["pulse_activity_gain"],
        continuous_release=True, bounded_chemical_activation=True,
        chem_activation_start_fraction=fit["chem_activation_start_fraction"],
        chem_activation_duration_fraction=fit["chem_activation_duration_fraction"],
    )
    volume_l = volume_at(ledger, observation_times, side="left")
    g_h_per_sccm = co2.SCCM_CORRECTED_CONVERSION.factor_g_l_h_per_sccm(1.0)
    return fit["matrix_gain"] * qgas * volume_l / g_h_per_sccm


def observed_processed_sccm(observations, initial_volume_l):
    """Invert the historical constant-V normalization of the saved, smoothed series."""
    g_h_per_sccm = co2.SCCM_CORRECTED_CONVERSION.factor_g_l_h_per_sccm(1.0)
    return observations["co2_rate_g_l_h"].to_numpy(dtype=float) * initial_volume_l / g_h_per_sccm
