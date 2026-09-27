"""TEST43-M Part 14: timeframe / fractal transfer summary.
Compares, per mechanism: direction of the matched-control 60m effect across the 15/30/60/120m range scales and between
3m and 5m bar resolutions, and the ordering of state-transition probabilities across scales."""
import os

import numpy as np
import pandas as pd

TAB = os.path.join(os.path.dirname(__file__), "..", "out", "m", "tables")
SC = ["15m", "30m", "60m", "120m"]


def main():
    mech = pd.concat([pd.read_csv(f"{TAB}/M04_M05_mechanism_info__{t}.csv") for t in ("ES", "MNQ", "ES5_MNQ5")])
    tr = pd.concat([pd.read_csv(f"{TAB}/M02_event_transitions__{t}.csv") for t in ("ES", "MNQ", "ES5_MNQ5")])
    rows = []
    for base in ("ES", "MNQ"):
        for e, g in mech[mech.inst.isin([base, base + "5"]) & mech.hz.isin(SC)].groupby("ev"):
            r = {"inst": base, "ev": e}
            for res in (base, base + "5"):
                gg = g[g.inst == res].set_index("hz").reindex(SC)
                tag = "3m" if res == base else "5m"
                for hz in SC:
                    r[f"{tag}_{hz}_d_ret60"] = gg.at[hz, "mean_d_ret60"]; r[f"{tag}_{hz}_t"] = gg.at[hz, "t_d_ret60"]
                    r[f"{tag}_{hz}_d_mfe60"] = gg.at[hz, "mean_d_mfe60"]; r[f"{tag}_{hz}_d_mae60"] = gg.at[hz, "mean_d_mae60"]
                s = np.sign(gg.mean_d_ret60.values)
                r[f"{tag}_sign_agree_of_4"] = int(max((s > 0).sum(), (s < 0).sum()))
                r[f"{tag}_n_sig_tcrit"] = int((gg.t_d_ret60.abs() >= gg.t_crit_placebo95).sum())
            a = np.array([r[f"3m_{h}_t"] for h in SC]); b = np.array([r[f"5m_{h}_t"] for h in SC])
            ok = ~np.isnan(a) & ~np.isnan(b)
            r["t_corr_3m_vs_5m"] = float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() >= 3 else np.nan
            r["same_sign_3m_5m_of_4"] = int((np.sign(a[ok]) == np.sign(b[ok])).sum())
            both_sig = r["3m_n_sig_tcrit"] >= 2 and r["5m_n_sig_tcrit"] >= 2 and r["3m_sign_agree_of_4"] == 4 and r["5m_sign_agree_of_4"] == 4
            r["FRACTAL_TRANSFER"] = "YES" if both_sig else "NO"
            rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(f"{TAB}/M11_timeframe_fractal_transfer.csv", index=False)
    # transition probabilities across scales / resolutions
    tr["res"] = np.where(tr.inst.str.endswith("5"), "5m", "3m"); tr["base"] = tr.inst.str.replace("5", "", regex=False)
    tp = tr[tr.hz.isin(SC)].pivot_table(index=["base", "from", "to"], columns=["res", "hz"], values="p")
    tp.to_csv(f"{TAB}/M11_transition_probabilities_by_scale.csv")
    # ordering stability: rank of transition probabilities within each (base, res, hz), Spearman vs 60m/3m
    ords = []
    for (base), g in tr[tr.hz.isin(SC)].groupby("base"):
        ref = g[(g.res == "3m") & (g.hz == "60m")].set_index(["from", "to"]).p
        for (res, hz), gg in g.groupby(["res", "hz"]):
            x = gg.set_index(["from", "to"]).p.reindex(ref.index)
            ords.append({"inst": base, "res": res, "hz": hz, "spearman_vs_3m_60m": x.rank().corr(ref.rank())})
    pd.DataFrame(ords).to_csv(f"{TAB}/M11_transition_ordering_stability.csv", index=False)
    print(out[["inst", "ev", "3m_sign_agree_of_4", "5m_sign_agree_of_4", "3m_n_sig_tcrit", "5m_n_sig_tcrit",
               "t_corr_3m_vs_5m", "same_sign_3m_5m_of_4", "FRACTAL_TRANSFER"]].to_string(index=False))
    print(pd.DataFrame(ords).round(3).to_string(index=False))


if __name__ == "__main__":
    main()
