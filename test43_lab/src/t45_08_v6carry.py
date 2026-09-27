"""TEST45: simplest deterministic form of the concept that recurred in every GA/GP outer fold (T45_13/T45_15):
V6_STATE_CARRY = at decision time T, if the frozen Champion holds a long in that instrument (V6 state), lock +1 contract
until the next RTH open; otherwise flat.  Timing/threshold/instrument neighbourhood + controls on the same blocks."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C  # noqa: E402
import t45_overlay as O  # noqa: E402
import t45_sim as S  # noqa: E402
from t45_07_eval import comb_stats, outer_masks  # noqa: E402

OUT = os.path.join(C.T45, "final")


def main():
    bank = O.Bank(C.build_panel())
    om = outer_masks(bank)
    allm = np.ones(bank.n, bool); allm[:20] = False
    rows = []
    daily = {}
    specs = {}
    for inst in ("ES", "MNQ", "BOTH"):
        for t in O.C_TIMES:
            for thr, lab in ((0.0, ">0"), (1.0, ">1")):
                specs[f"V6_STATE_CARRY|{inst}|{t}|champ{lab}"] = O.G(inst=inst, c_on=1, c_time=t, c_base=0, c_feat="champ_pos", c_dir=1, c_thr=thr, c_boost=1)
            specs[f"UNCOND_CARRY|{inst}|{t}"] = O.G(inst=inst, c_on=1, c_time=t)
            specs[f"V6_STATE_CARRY_BOOST2|{inst}|{t}|champ>0"] = O.G(inst=inst, c_on=1, c_time=t, c_base=0, c_feat="champ_pos", c_dir=1, c_thr=0.0, c_boost=2)
            specs[f"V6_FLAT_CARRY (anti: carry only when Champion flat)|{inst}|{t}"] = O.G(inst=inst, c_on=1, c_time=t, c_base=0, c_feat="champ_pos", c_dir=-1, c_thr=0.5, c_boost=1)
    for nm, ge in specs.items():
        r1 = O.run(ge, bank); r4 = O.run(ge, bank, 4.0)
        p = O.daily(r1, bank.n)
        m = S.metrics(r1, bank.bench, allm)
        ba = {f: float(p[mm].mean()) for f, mm in om.items()}
        cs = comb_stats(p, bank, allm)
        o = {"rule": nm, "avg": m["avg"], "max_dd": m["max_dd"], "worst": m["worst"], "mb_excess": m["matched_beta_excess"],
             "smb_excess": m["session_matched_beta_excess"], "SLIP4_total": float(O.daily(r4, bank.n)[allm].sum()), "sides_day": m["sides"] / allm.sum(),
             **{f"outer_{k}": v for k, v in ba.items()}, "outer_median": float(np.median(list(ba.values()))), "outer_pos": int(sum(v > 0 for v in ba.values())),
             "pre2021": float(p[(bank.sess < "2021-01-01") & allm].mean()), **cs,
             "Y2020_comb_mdd": comb_stats(p, bank, C.mask_period(bank.sess, "Y2020"))["comb_mdd"],
             "Y2022_overlay_avg": float(p[C.mask_period(bank.sess, "Y2022")].mean()),
             "FH_overlay_avg": float(p[C.mask_period(bank.sess, "FORMER_HOLDOUT_USED")].mean()),
             "avg_locked": float(sum(r["q_end"][allm].mean() for r in r1.values())),
             "worst20_champ_overlay_loss_share": m["worst20_champion_overlay_loss_share"]}
        rows.append(o); daily[nm] = p
    R = pd.DataFrame(rows); R.to_csv(f"{OUT}/T45_v6_state_carry_family.csv", index=False)
    pd.DataFrame(daily, index=bank.sess).to_parquet(f"{OUT}/T45_v6_state_carry_daily.parquet")
    pd.set_option("display.width", 260); pd.set_option("display.max_rows", 200)
    print(R[["rule", "avg", "max_dd", "smb_excess", "outer_median", "outer_pos", "outer_O2_2022", "comb_ret_dd", "champ_ret_dd", "incr_avg", "corr", "comb_mdd", "comb_worst", "SLIP4_total"]].round(4).to_string())


if __name__ == "__main__":
    main()
