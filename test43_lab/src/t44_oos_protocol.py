"""TEST44 append-only OOS DATA protocol (documentation + machine-checkable validators).  Reads ONLY the frozen historical
canonical files (<= 2026-05-27) to record reference invariants.  Writes out/t44/oos_protocol/TEST44_OOS_DATA_PROTOCOL.{json,md}."""
import hashlib
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t44_common as TC  # noqa: E402

OUT = os.path.join(TC.T44, "oos_protocol")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def invariants(inst):
    rel, h = TC.DATA[inst]
    p = os.path.join(TC.ROOT, rel)
    assert sha(p) == h
    d = pd.read_parquet(p)
    assert d.session_date.max() <= TC.END
    mod = d.dt.dt.hour * 60 + d.dt.dt.minute
    sw = np.where(d.contract.values[1:] != d.contract.values[:-1])[0]
    gaps = np.abs(d.o.values[sw + 1] - d.c.values[sw])
    ra = np.array(sorted(d[d.roll_adjacent].session_date.unique()), dtype="datetime64[ns]")
    ss = np.array(sorted(d.session_date.values[sw + 1]), dtype="datetime64[ns]")
    rth = d[(mod > 570) & (mod <= 960)]
    last = d.iloc[-1]
    return {"file": rel, "sha256": h, "rows": len(d), "first_dt": str(d.dt.min()), "last_dt": str(d.dt.max()),
            "columns": {c: str(t) for c, t in d.dtypes.items()},
            "contracts": list(pd.unique(d.contract)), "n_rolls": int(len(sw)),
            "last_contract": str(last.contract), "last_cum_adjustment": float(last.cum_adjustment),
            "cum_adjustment_constant_within_contract": bool((d.groupby("contract").cum_adjustment.nunique() == 1).all()),
            "first_contract_cum_adjustment": float(d.cum_adjustment.iloc[0]),
            "roll_switch_minute": sorted(set(d.dt.iloc[sw + 1].dt.strftime("%H:%M"))),
            "roll_adjacent_equals_switch_session": bool(np.array_equal(ra, ss)),
            "adjusted_gap_at_switch_pts_max": float(gaps.max()), "adjusted_gap_at_switch_pts_median": float(np.median(gaps)),
            "duplicate_dt": int(d.dt.duplicated().sum()), "monotonic_dt": bool(d.dt.is_monotonic_increasing),
            "nonzero_seconds": int((d.dt.dt.second != 0).sum()),
            "bars_ending_17:01_to_18:00": int(((mod > 17 * 60) & (mod <= 18 * 60)).sum()),
            "nonpositive_volume": int((d.v <= 0).sum()),
            "session_date_plus6h_equals_floor_dt_plus_6h": float((d.session_date_plus6h == (d.dt + pd.Timedelta(hours=6)).dt.normalize()).mean()),
            "cal_date_equals_floor_dt": float((d.cal_date == d.dt.dt.normalize()).mean()),
            "session_date_equals_plus6h_share": float((d.session_date == d.session_date_plus6h).mean()),
            "full_390_minute_RTH_share": float((rth.groupby("session_date").size() == 390).mean()),
            "trading_dates": int(d.session_date.nunique())}


def main():
    os.makedirs(OUT, exist_ok=True)
    inv = {i: invariants(i) for i in ("ES", "MNQ")}
    code = {f: sha(os.path.join(TC.SRC, f)) for f in ("t43/bars.py", "t44_common.py", "t43/v6lab.py", "t43/features.py", "t43/lab.py",
                                                       "t43/instruments.py", "t43/portfolio.py", "t43/intport.py", "t44_alloc.py", "t44_04_meta.py")}
    proto = {
        "program": "TEST44 new out-of-sample data protocol", "status": "FROZEN before any data after 2026-05-27 exists in this repository",
        "pre_oos_freeze_sha256": "3401331f1668a463008f17456f1738248434bbd8cf7a86438aee84149ceeeae4",
        "new_oos_rules_sha256": "2f74e2cafaa96cd6051b22dac25b6cdf6cf903229db7fb0bdccd3eabbf708236",
        "oos_start_session_date": "2026-05-28", "historical_last_session_date": "2026-05-27",
        "construction_rules (identical to the frozen canonical files)": {
            "source_and_lineage": "same upstream data source, fields and pipeline version that produced the frozen canonical files (TEST32 lineage audit: M0 MASSIVE_NATIVE artifact, back-adjusted, VOL_XOVER_T+1 roll). The data owner must record the upstream vendor/API identity and pipeline version with the delivery; any change of vendor, feed or pipeline version = protocol violation (fail closed).",
            "instruments": {"ES": "ES front chain (research series; executed as MES)", "MNQ": "MNQ front chain (executed as MNQ)"},
            "file_format": "ONE parquet per instrument containing the FULL history 2019-05-05 18:01 .. OOS end (append-only), same columns and dtypes as the frozen file",
            "columns": inv["ES"]["columns"],
            "timestamp": "dt = tz-naive America/New_York, bar END minute (a 1m bar stamped 09:31 covers [09:30, 09:31)); whole minutes only",
            "session_convention": "CME Globex session: bars ending 18:01 .. 17:00 next day; nothing ends in (17:00, 18:00] (no fabricated maintenance-hour bars)",
            "session_date": "canonical holiday-aware CME trading date (session_date); session_date_plus6h = floor(dt + 6h); cal_date = floor(dt); holiday/early-close sessions keep the canonical trading date",
            "gaps": "genuine gaps preserved; no interpolation, no forward-filled bars, no synthetic zero-volume bars",
            "contract_selection_and_roll": "front chain with a causal volume-crossover roll VOL_XOVER_T+1: the switch to the next contract happens at the first bar (18:01) of the session AFTER the crossover is observed; roll_adjacent = True on every bar of that switch session and only there",
            "back_adjustment": "forward-anchored additive: adj = raw + cum_adjustment; the first contract (ESM9/MNQM9 era) has cum_adjustment 0; each new contract era gets a constant cum_adjustment = previous era value minus the switch spread; historical rows NEVER change when new data are appended",
            "raw_prices": "raw (unadjusted) = adj - cum_adjustment; raw prices used ONLY for notional and margin",
            "research_pnl": "adjusted prices",
            "aggregation": "deterministic 1m -> 3m: t = floor((dt - 1 min), 3 min) (open-stamped, clock-aligned); o first, h max, l min, c last, v sum, n1m count, contract last, cum_adjustment last, roll_adjacent max, canon session_date last; empty buckets do not exist (src/t43/bars.py aggregate_3m/add_clock, unchanged)",
            "next_expected_rolls": "ESM6 -> ESU6 and MNQM6 -> MNQU6 around mid-June 2026 inside the OOS; handled by the same rule"},
        "validators (ALL must pass on the delivered files before any parsing into research objects)": [
            "raw file SHA256 recorded before parsing; file size recorded",
            "schema: identical column names and dtypes",
            "PREFIX: rows with session_date <= 2026-05-27 are value-identical (all columns) to the frozen canonical file (ES 2b4f41b1..., MNQ 66204b12...)",
            "rows appended only after 2026-05-27 17:00; dt strictly increasing; no duplicate dt; whole minutes",
            "no bar ending in (17:00, 18:00]; volume > 0 on every bar",
            "session_date_plus6h == floor(dt+6h) for every row; cal_date == floor(dt)",
            "cum_adjustment constant within each contract; first new contract era continues the frozen chain (ESM6 / MNQM6 value unchanged until the next switch)",
            "every contract switch occurs at an 18:01 bar; roll_adjacent sessions == switch sessions exactly",
            "adjusted gap at each new switch <= 2x the historical maximum (ES 34.5 pts, MNQ 53.0 pts) - otherwise fail closed for review",
            "OHLC sanity: l <= min(o,c), h >= max(o,c), positive prices",
            "3m bars rebuilt from the delivered 1m file reproduce the frozen 3m research bars for session_date <= 2026-05-27 exactly"],
        "evaluation_gate": {"minimum_completed_RTH_sessions": 120,
                            "completed_RTH_session": "a session_date >= 2026-05-28 whose ES AND MNQ 1m data both contain the 16:00 RTH closing bar",
                            "rule": "the evaluator refuses to compute or display any OOS economics before 120 completed RTH sessions exist (not weakened)"},
        "historical_reference_invariants (computed now on the frozen files only)": inv,
        "canonical_pipeline_code_sha256": code,
        "no_new_oos_data_in_repository": True,
    }
    fj = os.path.join(OUT, "TEST44_OOS_DATA_PROTOCOL.json")
    json.dump(proto, open(fj, "w"), indent=1, default=str)
    lines = ["# TEST44 OOS DATA PROTOCOL (frozen)", "", "No data after 2026-05-27 was acquired, downloaded, parsed or inspected.", "",
             f"Pre-OOS freeze `{proto['pre_oos_freeze_sha256']}`; new-OOS rules `{proto['new_oos_rules_sha256']}` (unchanged).", "",
             "## Construction rules (identical to the frozen canonical ES / MNQ files)"]
    for k, v in proto["construction_rules (identical to the frozen canonical files)"].items():
        lines.append(f"* **{k}**: {v if not isinstance(v, dict) else json.dumps(v)}")
    lines += ["", "## Validators (fail closed)"] + [f"{i + 1}. {v}" for i, v in enumerate(proto["validators (ALL must pass on the delivered files before any parsing into research objects)"])]
    lines += ["", "## Evaluation gate", f"* {json.dumps(proto['evaluation_gate'])}", "", "## Historical reference invariants (frozen files, <= 2026-05-27)"]
    for inst, v in inv.items():
        lines.append(f"### {inst}")
        lines += [f"* {k}: {v[k]}" for k in v if k not in ("columns", "contracts")]
        lines.append(f"* contracts ({len(v['contracts'])}): {', '.join(v['contracts'])}")
    lines += ["", "## Canonical pipeline code SHA256"] + [f"* `{k}` {v}" for k, v in code.items()]
    lines += ["", "Note: the upstream vendor/API identity and the contract-selection implementation live with the data owner (TEST32 lineage). "
              "This protocol requires that exact pipeline version and enforces every observable invariant above; any deviation fails closed."]
    fm = os.path.join(OUT, "TEST44_OOS_DATA_PROTOCOL.md")
    open(fm, "w").write("\n".join(lines) + "\n")
    hj, hm = sha(fj), sha(fm)
    open(os.path.join(OUT, "TEST44_OOS_DATA_PROTOCOL.sha256"), "w").write(f"{hj}  TEST44_OOS_DATA_PROTOCOL.json\n{hm}  TEST44_OOS_DATA_PROTOCOL.md\n")
    print("PROTOCOL_JSON_SHA256", hj); print("PROTOCOL_MD_SHA256", hm)


if __name__ == "__main__":
    main()
