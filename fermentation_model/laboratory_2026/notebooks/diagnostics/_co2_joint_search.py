"""Local, reproducible experiments for the CO2 v2 follow-up notebook.

Reads v2 data/initials, but never executes or writes the original notebook.
Chemical integration uses the shared official RHS. Experimental gas sources
are local to this module; no production equation or parameter file is changed.
"""
from __future__ import annotations

import ast
import hashlib
import json
import sys
from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

TRAIN = ("LAB019", "LAB020", "LAB021")
HOLDOUT = ("LAB016", "LAB017", "LAB018")
GAS_NAMES = ("kCO2_release_h", "CO2sat_scale", "matrix_gain")
GAS_BOUNDS = ((.03, 25.), (.35, 2.5), (.1, 20.))
CHEM_COLUMNS = dict(N="YAN_mg_l", G="G_g_l", F="F_g_l", GF="GF_g_l", E="E_g_l", Gly="Gly_g_l")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def local_lfs_content(path, root):
    """Read an already cached LFS object without hydrating/mutating the worktree."""
    with open(path, "rb") as handle:
        head = handle.read(200)
    if not head.startswith(b"version https://git-lfs.github.com/spec/v1"):
        return path
    lines = head.decode("ascii").splitlines()
    oid = next(line.split("sha256:", 1)[1] for line in lines if line.startswith("oid "))
    content = Path(root) / ".git/lfs/objects" / oid[:2] / oid[2:4] / oid
    if not content.is_file():
        raise FileNotFoundError(f"Required LFS object is absent locally: {oid}")
    assert sha256(content) == oid
    return content


def release_forward(c, p, max_step=None):
    """Conservative implicit reservoir, identical to v2 (positive root)."""
    k, scale, gain = (p[n] for n in GAS_NAMES)
    source, dt = c["source"], c["dt"]
    sat = c["sat_base"] * scale
    cd, out = np.zeros(len(source)), np.zeros(len(source))
    for i in range(1, len(source)):
        subdivisions = 1 if max_step is None else int(np.ceil(dt[i-1] / max_step))
        step = dt[i-1] / subdivisions
        inventory, released = cd[i-1], 0.
        for _ in range(subdivisions):
            a = inventory + step * source[i-1]
            aa = 1. + step * k
            b = sat[i] * (1. + .05 * step * k) - a
            root = np.sqrt(b*b + 4.*aa*a*sat[i])
            new = 2.*a*sat[i]/(root+b) if b >= 0. else (root-b)/(2.*aa)
            released += a - new
            inventory = new
        cd[i], out[i] = inventory, released/dt[i-1]
    return gain*out, cd, out


def features(t, y):
    t, y = np.asarray(t), np.asarray(y)
    peak = int(np.argmax(y))
    def run(mask, start=0):
        for i in range(max(2, start), len(t)):
            if mask[i-2:i+1].all() and np.allclose(np.diff(t[i-2:i+1]), 1.):
                return float(t[i])
        return np.nan
    return dict(peak_h=float(t[peak]), peak=float(y[peak]),
                onset_h=run(y >= .05), fall_h=run(y < .05, peak+2))


class Search:
    def __getstate__(self):
        return {k: v for k, v in self.__dict__.items() if k not in ("base", "joint", "cross", "gas")}

    def __setstate__(self, state):
        self.__dict__.update(state)
        from shared import run_new_must_glycerol_estimability_doe as base
        from shared import run_secondary_joint_campaign_doe as joint
        from laboratory_2026 import run_co2_matrix_cross_validation_2026 as cross
        import _post_activity_prediction as gas
        self.base, self.joint, self.cross, self.gas = base, joint, cross, gas

    def __init__(self, root):
        self.root = Path(root)
        self.fm = self.root / "fermentation_model"
        self.lab = self.fm / "laboratory_2026"
        for path in (self.fm, self.lab, self.fm / "pilot_2025", self.lab / "notebooks/EKF"):
            if str(path) not in sys.path:
                sys.path.insert(0, str(path))
        from shared import run_new_must_glycerol_estimability_doe as base
        from shared import run_secondary_joint_campaign_doe as joint
        from laboratory_2026 import run_co2_matrix_cross_validation_2026 as cross
        import _post_activity_prediction as gas
        self.base, self.joint, self.cross, self.gas = base, joint, cross, gas
        self.v2 = self.lab / "results/co2_lab016_021_recalibration_v2"
        self.inputs = []
        def read(name):
            path = self.v2 / name
            self.inputs.append(path)
            return pd.read_csv(path)
        self.manifest = json.loads((self.v2 / "manifest.json").read_text(encoding="utf-8"))
        self.inputs.append(self.v2 / "manifest.json")
        self.thetas = self.manifest["theta_fixed"]
        self.old = {**self.manifest["old_gas_start"],
                    "activation_start_g_l": 2., "activation_width_g_l": 8.}
        self.initials = read("initial_conditions.csv").set_index("lab")
        self.obs = read("observations.csv")
        self.chem = read("chemistry_observations_corrected_YAN.csv")
        self.density = read("density_sugar_comparison/density_sugar_points.csv")
        self.biomass = read("biomass_lab016_018.csv")
        self.previous_parameters = read("parameters.csv")
        self.previous_gas = read("gas_trajectories.csv")
        self.previous_chemistry = read("chemistry_trajectories.csv")
        self.previous_transfer = read("transfer_metrics.csv")
        self.batches = {}
        recent_path = self.fm / "data/mem2026/LAB019-021/backup_global_temperatura_completo.csv"
        self.inputs.append(recent_path)
        recent_path = local_lfs_content(recent_path, self.root)
        self.inputs.append(recent_path)
        pieces = []
        t0 = pd.Timestamp("2026-09-21 17:00:00")
        for chunk in pd.read_csv(recent_path, usecols=["timestamp", "fermentador", "T"], chunksize=400000):
            ts = pd.to_datetime(chunk.timestamp, errors="coerce")
            keep = ts.between(t0-pd.Timedelta(hours=1), t0+pd.Timedelta(hours=167))
            if keep.any():
                d = chunk.loc[keep].copy()
                d["t_h"] = (ts[keep]-t0).dt.total_seconds()/3600.
                pieces.append(d)
        recent_temp = pd.concat(pieces, ignore_index=True)
        import openpyxl  # already required by the repository
        book = self.fm / "data/mem2026/LAB016-018/LAB016-018-offline-measurements.xlsx"
        self.inputs.append(book)
        ini_sheet = pd.read_excel(book, sheet_name="CondicionesIniciales").set_index("CodigoLab")
        for lab in HOLDOUT + TRAIN:
            row = self.initials.loc[lab]
            events = ast.literal_eval(row.N_events)
            horizon = float(row.horizon_h)
            time = np.unique(np.r_[np.arange(0., horizon, .25), horizon, [t for t, _ in events]])
            if lab in HOLDOUT:
                filename = dict(LAB016="Temp_F1_LAB016.csv", LAB017="Temp_F2_LAB017.csv", LAB018="Temp_F3._LAB018.csv")[lab]
                path = self.fm / "data/mem2026/LAB016-018" / filename
                self.inputs.append(path)
                temp = pd.read_csv(path, parse_dates=["timestamp"])
                initial = ini_sheet.loc[lab]
                clock = initial.Hora if hasattr(initial.Hora, "hour") else pd.to_datetime(str(initial.Hora)).time()
                start = pd.Timestamp.combine(pd.Timestamp(initial.Fecha).date(), clock)
                temp["t_h"] = (temp.timestamp-start).dt.total_seconds()/3600.
            else:
                fermenter = dict(zip(TRAIN, ("F1", "F2", "F3")))[lab]
                temp = recent_temp[recent_temp.fermentador.eq(fermenter)].copy()
            temp = temp.sort_values("t_h")
            self.batches[lab] = base.BatchData(
                medium="natural", batch=lab, time=time,
                temperature_c=np.interp(time, temp.t_h, temp["T"]),
                initials={s: float(row[s]) for s in base.STATE_NAMES},
                pulses={**{s: () for s in base.INPUT_CHANNELS}, "N": events},
                observations={s: np.full(len(time), np.nan) for s in base.STATE_NAMES})
        assert set(self.obs.lab) == set(TRAIN + HOLDOUT)
        self.inputs += [Path(m.__file__) for m in (base, joint, cross, gas)]
        self.inputs += list((self.lab / "notebooks/diagnostics").glob("co2_lab016_021_recalibration_v2.*.ipynb"))
        # Snapshot the entire previous results tree, including prior figure files.
        self.protected = {str(p.relative_to(self.root)): sha256(p)
                          for p in set(self.inputs) | {p for p in self.v2.rglob("*") if p.is_file()}}
        self.cores, self.cache, self.theta_by_case = {}, {}, {}
        self.runs = []

    def prepare(self, name, theta, labs=TRAIN):
        self.theta_by_case[name] = theta.copy()
        for lab in labs:
            if (name, lab) in self.cache:
                continue
            bt = self.batches[lab]
            core = self.gas.integrate_core(bt, theta, bt.time)
            core0 = self.gas.integrate_core(replace(bt, pulses={**bt.pulses, "N": ()}), theta, bt.time)
            core["GF"] = core.G + core.F
            self.cores[name, lab] = core
            time = bt.time
            events = bt.pulses["N"]
            ramp, multiplier = self.histories(time, events, self.old)
            consumed = core.GF.iloc[0]-core.GF.to_numpy()
            z = np.clip((consumed-2.)/8., 0., 1.)
            gate = z*z*(3.-2.*z)
            ini = bt.initials
            oxygen0 = self.old["O2_initial_scale"]*self.cross.co2_model.o2_saturation_mg_l(
                bt.temperature_c[0], ini["E"], ini["G"], ini["F"], 1.)
            ref = self.gas.finish(bt, theta, core, core0, self.old, gate, ramp, multiplier, 0., oxygen0)
            qn, q0 = self.gas.production(theta, bt, core), self.gas.production(theta, bt, core0)
            d = self.obs[self.obs.lab.eq(lab)].sort_values("t_h")
            idx = np.searchsorted(time, d.t_h.to_numpy())-1
            w = (d.t_h.to_numpy()-time[idx]) / (time[idx+1]-time[idx])
            phi = .75**2/(.75**2+ref.O2.to_numpy()**2)
            self.cache[name, lab] = dict(
                time=time, dt=np.diff(time), source=ref.qprod.to_numpy(),
                sat_base=ref.csat.to_numpy()/self.old["CO2sat_scale"],
                qn=qn, q0=q0, ramp=ramp, multiplier=multiplier,
                gate=gate, fferm=.08+.92*phi, obs=d, idx=idx, w=w,
                events=events, core=core, reference=ref, core0_X=core0.X.to_numpy(),
                oxygen0=oxygen0, sugar_consumed=consumed)

    @staticmethod
    def histories(time, events, p):
        ramp = np.clip((time-events[0][0])/p["pulse_t_rise_h"], 0., 1.) if events else np.zeros(len(time))
        mult = np.ones(len(time))
        tr, td = p["tau_rise_h"], p["tau_decay_h"]
        up = tr*np.log1p(td/tr)
        peak = -np.expm1(-up/tr)*np.exp(-up/td)
        for event, dose in events:
            u = np.maximum(time-event, 0.)
            mult += p["A"]*dose/p["N_ref_g_l"]*(-np.expm1(-u/tr))*np.exp(-u/td)/peak
        return ramp, mult

    def source_cache(self, case, lab, p, mode="v2"):
        c = self.cache[case, lab]
        if mode == "v2":
            return c
        ramp, mult = self.histories(c["time"], c["events"], p)
        b = p["pulse_activity_gain"]
        if mode in ("v2_free", "v2_gate"):
            raw = (1.+(b-1.)*ramp)*c["q0"]+ramp*(c["qn"]-c["q0"])
        elif mode in ("positive_mix", "positive_gate"):
            # Nonnegative interpolation: at r=1, source is b*qn, not qn-(1-b)*q0.
            raw = (1.-ramp)*c["q0"]+b*ramp*c["qn"]
        elif mode == "chemical":
            raw = c["qn"]
        else:
            raise ValueError(mode)
        gate = c["gate"]
        if mode in ("v2_gate", "positive_gate"):
            z = np.clip((c["sugar_consumed"]-p["activation_start_g_l"])/p["activation_width_g_l"], 0., 1.)
            gate = z*z*(3.-2.*z)
        # The oxygen parameters remain fixed, but its state follows the changed
        # biomass interpolation when the pulse ramp duration is recalibrated.
        fferm = c["fferm"]
        if not np.array_equal(ramp, c["ramp"]):
            biomass = np.maximum(c["core0_X"]+ramp*(c["core"].X.to_numpy()-c["core0_X"]), 0.)
            oxygen = np.zeros(len(ramp))
            oxygen[0] = c["oxygen0"]
            for i, dt in enumerate(c["dt"]):
                uptake = p["O2_qmax_mg_gdw_h"]*biomass[i]*oxygen[i]/(.25+oxygen[i])
                oxygen[i+1] = max(oxygen[i]-dt*uptake, 0.)
            fferm = .08+.92*.75**2/(.75**2+oxygen**2)
        return {**c, "gate": gate, "source": gate*fferm*mult*np.maximum(raw, 0.)}

    def curve(self, case, lab, params, mode="v2", max_step=None):
        c = self.source_cache(case, lab, params, mode)
        pred, cd, qgas = release_forward(c, params, max_step)
        return pd.DataFrame(dict(t_h=c["time"], CO2=pred, Cd=cd, qgas=qgas,
                                 qprod=c["source"], qn=c["qn"], q0=c["q0"],
                                 ramp=self.histories(c["time"], c["events"], params)[0],
                                 gate=c["gate"]))

    def fit(self, case, labs=TRAIN, mode="v2", starts=2, initial=None, max_nfev=100):
        assert set(labs).issubset(TRAIN), "Holdout cannot enter optimization"
        extra = {"v2_free": ("pulse_activity_gain", "pulse_t_rise_h"),
                 "positive_mix": ("pulse_activity_gain", "pulse_t_rise_h"),
                 "v2_gate": ("activation_start_g_l", "activation_width_g_l"),
                 "positive_gate": ("pulse_activity_gain", "pulse_t_rise_h", "activation_start_g_l", "activation_width_g_l"),
                 "chemical": ("A",)}.get(mode, ())
        names = GAS_NAMES + extra
        bounds = GAS_BOUNDS + tuple({"pulse_activity_gain": (.05, 1.5),
                                     "pulse_t_rise_h": (6., 120.), "A": (.001, 1.),
                                     "activation_start_g_l": (.2, 30.),
                                     "activation_width_g_l": (2., 40.)}[n] for n in extra)
        lo, hi = np.log(np.array(bounds).T)
        def residual(x):
            p = {**self.old, **dict(zip(names, np.exp(x)))}
            parts = []
            for lab in labs:
                c = self.source_cache(case, lab, p, mode)
                pred = release_forward(c, p)[0]
                ix, w = c["idx"], c["w"]
                sampled = pred[ix]*(1.-w)+pred[ix+1]*w
                y = c["obs"].y.to_numpy()
                e = np.where(y >= .05, sampled-y, np.maximum(sampled-.05, 0.))
                parts.append(e/np.sqrt(len(e)))
            return np.concatenate(parts)
        seeds = [initial or {**self.old, "kCO2_release_h": 2., "CO2sat_scale": 1., "matrix_gain": 1.}]
        if starts > 1:
            seeds.append({**self.old, "kCO2_release_h": .15, "CO2sat_scale": 2.4, "matrix_gain": 1.})
        solutions = []
        for i, seed in enumerate(seeds):
            seed = {**self.old, **seed}
            x0 = np.clip(np.log([seed[n] for n in names]), lo+1e-9, hi-1e-9)
            sol = least_squares(residual, x0, bounds=(lo, hi), max_nfev=max_nfev,
                                ftol=2e-7, xtol=2e-7, gtol=2e-7)
            self.runs.append(dict(case=case, mode=mode, labs=",".join(labs), start=i,
                                  objective=float(sol.fun@sol.fun), success=bool(sol.success),
                                  nfev=sol.nfev, message=sol.message))
            solutions.append(sol)
        best = min(solutions, key=lambda s: s.fun@s.fun)
        p = {**self.old, **dict(zip(names, np.exp(best.x)))}
        singular = np.linalg.svd(best.jac, compute_uv=False)
        return dict(case=case, mode=mode, params=p, objective=float(best.fun@best.fun),
                    success=bool(best.success), nfev=best.nfev,
                    jacobian_ratio=float(singular[-1]/singular[0]),
                    active_bounds=",".join(n for n, x, a, b in zip(names, best.x, lo, hi)
                                           if min(x-a, b-x) < .005))

    def chemistry_metrics(self, case, labs=TRAIN):
        rows = []
        for lab in labs:
            cr = self.cores[case, lab]
            d = self.chem[self.chem.lab.eq(lab) & ~self.chem.is_NUT & self.chem.t_h.gt(0.)]
            for ch, col in CHEM_COLUMNS.items():
                pts = d[["t_h", col]].dropna()
                if not len(pts):
                    continue
                error = np.interp(pts.t_h, cr.index, cr[ch]*(1000. if ch == "N" else 1.))-pts[col].to_numpy()
                rows.append(dict(case=case, lab=lab, channel=ch, n=len(pts),
                                 RMSE=float(np.sqrt(np.mean(error**2))), bias=float(error.mean())))
        return pd.DataFrame(rows)

    def gas_metrics(self, case, params, mode="v2", labs=TRAIN):
        rows = []
        for lab in labs:
            c = self.cache[case, lab]
            curve = self.curve(case, lab, params, mode)
            d = c["obs"]
            pred = np.interp(d.t_h, curve.t_h, curve.CO2)
            error = pred-d.y.to_numpy()
            observed, predicted = features(d.t_h, d.y), features(d.t_h, pred)
            late = d.t_h.to_numpy() >= 100.
            post = d.t_h.to_numpy() >= observed["peak_h"]
            for window, mask in (("all", np.ones(len(d), bool)), ("after_peak", post), ("after_100h", late)):
                rows.append(dict(case=case, mode=mode, lab=lab, window=window, n=int(mask.sum()),
                    RMSE=float(np.sqrt(np.mean(error[mask]**2))), MAE=float(np.mean(abs(error[mask]))),
                    bias=float(error[mask].mean()), **predicted,
                    observed_fall_h=observed["fall_h"], observed_onset_h=observed["onset_h"],
                    max_decline_5h=float(np.max(np.interp(curve.t_h+5., curve.t_h, -curve.CO2)+curve.CO2))))
        return pd.DataFrame(rows)

    def checks(self, case, params, mode="v2", labs=TRAIN+HOLDOUT):
        rows = []
        for lab in labs:
            c = self.source_cache(case, lab, params, mode)
            curve = self.curve(case, lab, params, mode)
            balance = np.max(abs(np.diff(curve.Cd)-c["dt"]*(c["source"][:-1]-curve.qgas.to_numpy()[1:])))
            cr = self.cores[case, lab]
            theta = self.theta_by_case[case]
            dose = np.array([sum(d for t, d in c["events"] if t < ti) for ti in c["time"]])
            inventory = cr.N+theta["qN"]/theta["mu0"]*(cr.X+cr.Xd)-dose
            n_error = np.max(abs(inventory-inventory.iloc[0]))
            fine = self.curve(case, lab, params, mode, max_step=.0625)
            refinement = np.max(abs(curve.CO2-fine.CO2))
            assert balance < 1e-10 and n_error < 2e-6
            assert curve[["CO2", "Cd", "qprod"]].min().min() >= -1e-12
            rows.append(dict(case=case, mode=mode, lab=lab, balance=balance,
                             nitrogen_balance=n_error, refinement_max_CO2=refinement))
        return pd.DataFrame(rows)

    def verify_protected(self):
        assert all(sha256(self.root/p) == h for p, h in self.protected.items())
        return len(self.protected)
