"""TEST44 step 1: frozen V6 sleeves through 2026-05-27, champion control / D0 reproduction, TEST43 failure attribution."""
import json
import os
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
import t44_common as TC  # noqa: E402
from t43 import lab, portfolio as PF, sleeves as S  # noqa: E402
import p03_portfolio_dev as PD  # noqa: E402


def main():
    TC.setup()
    os.makedirs(f"{TC.T44}/sleeves", exist_ok=True)
    C = S.candidates()
    daily, meta = {}, {}
    for cid in TC.ELIG + TC.SHADOW:
        b, res, d = S.run_sleeve(C[cid], end=TC.END)
        des = S.desired(res)
        assert b.session_date.max() <= TC.END
        pd.DataFrame({"t": b.t.values, "sd": b.session_date.values, "rth": b.in_rth.values, "pos": res["pos"].astype(float),
                      "desired": des}).to_parquet(f"{TC.T44}/sleeves/sleeve_{cid}.parquet")
        daily[cid] = d.pnl
        dev = (b.session_date <= lab.DEV_END).values
        meta[cid] = {"inst": C[cid]["inst"], "max_desired_DEV": float(des[dev].max()),
                     "mean_desired_when_active_DEV": float(des[dev & (des > 0)].mean()),
                     "active_share_DEV": float((des[dev] > 0).mean()), "cand_sha256": S.cand_hash(C[cid])}
        print(cid, meta[cid], flush=True)
    D = pd.DataFrame(daily).fillna(0.0)
    D.to_csv(f"{TC.T44}/sleeve_daily_standalone.csv")
    json.dump(meta, open(f"{TC.T44}/sleeve_meta.json", "w"), indent=1)
    # ---- frozen TEST43 portfolios reproduced on the extended data (CHAMPION_CONTROL_V1 = P1 CONS; D0 = P2B MOD)
    fin = json.load(open(os.path.join(TC.ROOT, "out", "p", "freeze", "TEST43P_FINAL_PORTFOLIOS.json")))
    bk = PF.Book(TC.END, TC.ELIG)
    rows = []
    for role, tag in (("SECONDARY_2", "CHAMPION_CONTROL_V1"), ("PRIMARY", "D0_CURRENT_TEST43"), ("SECONDARY_1", "D0b_TEST43_P2")):
        P = fin["portfolios"][role]
        w = {c: m["contract_weight"] for c, m in P["members"].items()}
        r = bk.run(w, gov=PD.gov_for(P["risk_envelope"]))
        d = bk.daily(r)
        d.to_csv(f"{TC.T44}/daily_{tag}.csv")
        np.save(f"{TC.T44}/pos_{tag}.npy", r["pos"]); np.save(f"{TC.T44}/D_{tag}.npy", r["D"])
        hold = d[(d.index >= "2025-10-01") & (d.index <= TC.END)].pnl.sum()
        rows.append({"portfolio": tag, "frozen_role": role, "envelope": P["risk_envelope"], "former_holdout_net": float(hold)})
        print(tag, "former holdout net", round(hold, 2))
    pd.DataFrame(rows).to_csv(f"{TC.T44}/t44_frozen_reproduction.csv", index=False)


if __name__ == "__main__":
    main()
