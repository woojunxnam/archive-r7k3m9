"""Phase 1-3 pipeline: data QA, 3m build, V5.3.3 baseline replay, benchmarks.

Usage: python run_p123.py PATH/canonical_1m_ES.parquet OUTDIR
"""
import json
import os
import sys
import time

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from t43 import bars as B, bench, metrics as M, qa, v533  # noqa: E402


def build(path, outdir):
    m1 = B.normalise_1m(pd.read_parquet(path))
    b = B.add_clock(B.aggregate_3m(m1))
    # margin reference price: raw (unadjusted) price if cum_adjustment known
    if "cum_adjustment" in b.columns:
        b["raw_o"] = b["o"] - b["cum_adjustment"].astype(float)
    b.to_parquet(os.path.join(outdir, "ES_3m_bars.parquet"))
    return m1, b


def arrays(b):
    a = B.to_arrays(b)
    if "roll_adjacent" in b.columns:
        a["roll_day"] = b["roll_adjacent"].fillna(False).astype(bool).values
    if "raw_o" in b.columns:
        a["mref"] = b["raw_o"].values.astype(np.float64)
    return a


def main(path, outdir):
    os.makedirs(outdir, exist_ok=True)
    t0 = time.time()
    rep = qa.run_qa(path, os.path.join(outdir, "01_DATA_QA"))
    print("QA done", {k: rep[k] for k in ("rows", "first_dt", "last_dt", "duplicate_dt", "bad_ohlc_rows", "sessions")})
    m1, b = build(path, outdir)
    a = arrays(b)
    print("3m bars", len(b), "rth bars", int(b.in_rth.sum()))
    res = v533.run(a, v533.make_params())
    s = M.summarize(b, res, label="V533_BASELINE_FULL")
    s.update(res["counter_dict"])
    att = M.reason_attribution(res, v533.REASONS)
    att.to_csv(os.path.join(outdir, "02_BASELINE_REASON_ATTRIBUTION.csv"), index=False)
    d = M.daily_table(b, res["equity"], res["pos"], "session")
    d.to_csv(os.path.join(outdir, "02_BASELINE_DAILY.csv"))
    fills = pd.DataFrame({"bar": res["f_bar"], "t": b["t"].values[res["f_bar"]], "side": res["f_side"],
                          "qty": res["f_qty"], "px": res["f_px"],
                          "reason": [v533.REASONS[k] for k in res["f_reason"]], "realized": res["f_real"]})
    fills.to_parquet(os.path.join(outdir, "02_BASELINE_FILLS.parquet"))
    with open(os.path.join(outdir, "02_BASELINE_SUMMARY.json"), "w") as f:
        json.dump(s, f, indent=1, default=float)
    print(json.dumps(s, indent=1, default=float))
    rows = []
    for n in (1, 10, 16, 24, 32, 40):
        sb, _ = bench.summarize_const(b, n, roll_day=a.get("roll_day"))
        rows.append(sb)
    pd.DataFrame(rows).to_csv(os.path.join(outdir, "03_BENCHMARKS_CONST.csv"), index=False)
    print(pd.DataFrame(rows).to_string())
    print("elapsed", time.time() - t0)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
