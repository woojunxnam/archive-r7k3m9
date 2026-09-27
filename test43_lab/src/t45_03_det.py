"""TEST45 Phase 8 deterministic session overlays S0-S6 + addendum CONTROL_A..E (predeclared broad thresholds from the
prompt/addendum buckets, not searched).  Everything is an overlay ADDED to CHAMPION_CONTROL_V1 in the same account."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_overlay as O  # noqa: E402

OUT = os.path.join(C.T45, "det"); os.makedirs(OUT, exist_ok=True)
G = O.G
GAP = -0.5          # predeclared: GAP_LOCK <= -0.5 ATR ("large negative gap", prompt bucket edge)
FLUSH = -0.3        # predeclared: 30m selloff <= -0.3 ATR ("large opening selloff")
CRASH = -1.5        # predeclared crash guard (H5): no trade below -1.5 ATR

SPECS = {
    "CONTROL_A unconditional +1 locked 16:15->next open": G(c_on=1, c_time="16:14"),
    "CONTROL_B GAP_LOCK<=-0.5ATR +1 09:32->16:00": G(m_on=1, m_gap_hi=GAP),
    "CONTROL_B' GAP_CASH<=-0.5ATR +1 09:32->16:00": G(m_on=1, m_gap_kind="cash", m_gap_hi=GAP),
    "CONTROL_C 30m selloff<=-0.3ATR +1 10:01->16:00": G(m_on=1, m_w=30, m_flush_hi=FLUSH),
    "CONTROL_D GAP_LOCK<=-0.5 & 30m selloff<=-0.3 +1": G(m_on=1, m_w=30, m_gap_hi=GAP, m_flush_hi=FLUSH),
    "S1 = CONTROL_A (late-RTH unconditional carry, decide 15:45)": G(c_on=1, c_time="15:45"),
    "S2 gap-down rebound + crash guard": G(m_on=1, m_gap_hi=GAP, m_gap_lo=CRASH),
    "S3 opening-flush rebound + crash guard": G(m_on=1, m_w=30, m_flush_hi=FLUSH, m_flush_lo=CRASH),
    "S4 gap+flush combined + crash guard": G(m_on=1, m_w=30, m_gap_hi=GAP, m_flush_hi=FLUSH, m_gap_lo=CRASH),
    "S4b gap+flush+reclaim50%": G(m_on=1, m_w=30, m_gap_hi=GAP, m_flush_hi=FLUSH, m_reclaim=0.5),
    "S5a late conditional boost (RTH ret<0 -> 2) decide 15:45": G(c_on=1, c_time="15:45", c_feat="rth_ret", c_dir=-1, c_thr=0.0, c_boost=2),
    "S5b late boost (V6 champion long -> 2) [informed by T45_03]": G(c_on=1, c_time="15:45", c_feat="champ_pos", c_dir=1, c_thr=0.0, c_boost=2),
    "S5c late boost (mom60<0 -> 2) [informed by T45_03]": G(c_on=1, c_time="15:45", c_feat="mom60", c_dir=-1, c_thr=0.0, c_boost=2),
    "S6 S5a + open manager (keep if GAP_LOCK<=-0.75 until 12:00)": G(c_on=1, c_time="15:45", c_feat="rth_ret", c_dir=-1, c_thr=0.0, c_boost=2,
                                                                     o_rule="KEEP_ADVERSE", o_thr=-0.75, o_until="12:00"),
    "S6b S1 + open manager (keep if GAP_LOCK<=-0.75 until 12:00)": G(c_on=1, c_time="15:45", o_rule="KEEP_ADVERSE", o_thr=-0.75, o_until="12:00"),
    "S6c S1 + gap-down rebound (combined close-build + open)": G(c_on=1, c_time="15:45", m_on=1, m_gap_hi=GAP, m_gap_lo=CRASH),
}


def main():
    from t43.instruments import PROFILES  # noqa: F401
    P = C.build_panel()
    bank = O.Bank(P)
    rows, per = [], []
    daily = {}
    ch = bank.bench.champ
    s0 = {"name": "S0 CHAMPION_CONTROL_V1 (unchanged)", **C.dstats(ch)}
    s0.update({f"blk_{k}": v for k, v in O.block_avgs(ch, bank.sess.values).items()})
    rows.append(s0)
    for nm, ge in SPECS.items():
        for inst in ("ES", "MNQ", "BOTH"):
            g2 = dict(ge, inst=inst)
            o, pr, pnl = O.report(g2, bank, f"{nm} [{inst}]")
            o["inst"] = inst; o["family"] = nm.split(" ")[0]
            rows.append(o); per += pr
            daily[f"{nm} [{inst}]"] = pnl
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T45_08_overlays.csv", index=False)
    pd.DataFrame(per).to_csv(f"{OUT}/T45_08_overlays_by_period.csv", index=False)
    pd.DataFrame(daily, index=bank.sess).to_parquet(f"{OUT}/T45_08_overlay_daily.parquet")
    json.dump({k: {kk: (vv if not isinstance(vv, float) or np.isfinite(vv) else str(vv)) for kk, vv in v.items()} for k, v in SPECS.items()},
              open(f"{OUT}/T45_08_specs.json", "w"), indent=1)
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 200)
    print(R[["name", "avg", "total", "max_dd", "worst", "matched_beta_excess", "session_matched_beta_excess", "incr_avg", "incr_max_dd",
             "corr_champion", "SLIP4_total", "outer_blocks_median", "outer_blocks_min", "outer_blocks_pos", "blk_O2_2022", "blk_O5_2025_26"]].round(2).to_string())


if __name__ == "__main__":
    main()
