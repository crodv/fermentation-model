"""Read the three Y15 NUT samples without inventing extraction timestamps."""

from pathlib import Path
import json

import openpyxl
import pandas as pd


def load_nut_samples(data_dir, t0_by_lab, sample_time_overrides=None):
    """Return nitrogen measurements, provenance and explicit plotting-time bounds.

    Without an extraction timestamp, the plotting midpoint is provisional, assuming
    the sample was taken after pulse 2 and before its earliest nitrogen assay.
    Analysis timestamps remain separate from the unknown extraction timestamp.
    """
    data_dir = Path(data_dir)
    overrides = sample_time_overrides or {}
    wb = openpyxl.load_workbook(
        data_dir / "Mediciones-Offline-LAB019-021.xlsx", read_only=True, data_only=True
    )
    pulse_rows = [r for r in wb["Nutricion"].iter_rows(min_row=2, values_only=True)
                  if r[0] in t0_by_lab and r[2] == "Pulso 2"]
    wb.close()
    assert len(pulse_rows) == len(t0_by_lab)
    pulse = {r[0]: pd.Timestamp(r[3]) for r in pulse_rows}
    records = []
    for path in sorted(data_dir.glob("EXPAuto*.txt")) + sorted(data_dir.glob("ONLINE*.txt")):
        for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            fields = line.split("\t")
            if len(fields) < 6 or not fields[0].endswith("-NUT"):
                continue
            if fields[1] not in ("PAN", "AMMONIA", "YAN"):
                continue
            records.append(dict(sample_id=fields[0], analyte=fields[1],
                value=float(fields[3].replace(",", ".")), unit=fields[4],
                analysis_timestamp=pd.to_datetime(fields[5], dayfirst=True),
                source_file=path.name, source_line=line_no))
    raw = pd.DataFrame(records)
    assert not raw.empty, "Missing NUT exports"
    assert raw.groupby(["sample_id", "analyte"]).value.nunique().le(1).all(), "Conflicting NUT results"
    unique = raw.drop_duplicates(["sample_id", "analyte"])
    result = []
    for lab, t0 in t0_by_lab.items():
        sid = f"{lab}-NUT"
        rows = unique[unique.sample_id.eq(sid)].set_index("analyte")
        assert set(rows.index) == {"PAN", "AMMONIA", "YAN"}, sid
        assert rows.unit.eq("mg/L").all(), sid
        earliest = rows.analysis_timestamp.min()
        latest = rows.analysis_timestamp.max()
        assert earliest > pulse[lab], (lab, "NUT analysis precedes pulse")
        extraction = pd.Timestamp(overrides[lab]) if lab in overrides else pd.NaT
        provisional = pd.isna(extraction)
        lower = pulse[lab] if provisional else extraction
        upper = earliest if provisional else extraction
        if not provisional:
            assert pulse[lab] <= extraction <= earliest, (lab, "extraction outside post-pulse interval")
        plot_stamp = lower + (upper - lower) / 2
        pan = float(rows.loc["PAN", "value"])
        nh3 = float(rows.loc["AMMONIA", "value"])
        yan = pan + .823 * max(nh3, 0.)
        t0 = pd.Timestamp(t0)
        hours = lambda stamp: (stamp - t0).total_seconds() / 3600
        result.append(dict(
            lab=lab, sample="NUT", sample_id=sid, PAN_mg_l=pan,
            NH3_raw_mg_l=nh3, NH3_censored_mg_l=max(nh3, 0.),
            YAN_reported_mg_l=float(rows.loc["YAN", "value"]),
            YAN_mg_l=yan, N_kg_m3=yan / 1000.,
            sample_timestamp=extraction, plot_timestamp=plot_stamp,
            pulse_timestamp=pulse[lab], pulse_t_h=hours(pulse[lab]),
            analysis_first=earliest, analysis_PAN=rows.loc["PAN", "analysis_timestamp"],
            analysis_AMMONIA=rows.loc["AMMONIA", "analysis_timestamp"],
            analysis_YAN=rows.loc["YAN", "analysis_timestamp"],
            analysis_last=latest, time_lower_h=hours(lower), time_upper_h=hours(upper),
            plot_t_h=hours(plot_stamp), time_provisional=provisional,
            time_source=("midpoint of assumed post-pulse/pre-analysis interval; extraction unknown"
                         if provisional else "user-confirmed extraction timestamp"),
            source_files=";".join(sorted(rows.source_file.unique())),
            source_lines=json.dumps({a: int(rows.loc[a, "source_line"]) for a in rows.index}),
        ))
    frame = pd.DataFrame(result)
    assert frame.lab.nunique() == len(t0_by_lab)
    return frame
