"""TEST44 allocation layer: sleeve demand states (0/1/2 actual contracts), cluster slots, priority rules, integer engine
runner, attribution.  Nothing here is learned from future returns."""
import json
import os

import numpy as np
import pandas as pd

import t44_common as TC
from t43 import instruments, intport, lab, portfolio as PF, v6lab
import p03_portfolio_dev as PD

INSTS = ("ES", "MNQ")
FP = pd.read_csv(os.path.join(TC.ROOT, "out", "p", "p03_fingerprint_DEV.csv")).set_index("id")   # frozen DEV stats (pre-2025)


class Engine:
    def __init__(self, sleeves=None, end=TC.END):
        TC.setup()
        self.ids = list(sleeves or TC.ELIG)
        self.bk = PF.Book(end, self.ids)
        self.T = self.bk.T
        self.meta = json.load(open(f"{TC.T44}/sleeve_meta.json"))
        self.inst = {c: self.meta[c]["inst"] for c in self.ids}
        self.des = self.bk.des
        self.inten = {c: np.clip(self.des[c] / self.meta[c]["max_desired_DEV"], 0, 1) for c in self.ids}
        T = self.T
        self.arr = dict(o=np.stack([T.ES_o.values, T.MNQ_o.values], 1), c=np.stack([T.ES_c.values, T.MNQ_c.values], 1),
                        raw=np.stack([T.ES_raw.values, T.MNQ_raw.values], 1), valid=np.stack([T.ES_valid.values, T.MNQ_valid.values], 1),
                        roll=np.stack([T.ES_roll.values, T.MNQ_roll.values], 1), atr=np.stack([T.ES_atrD.values, T.MNQ_atrD.values], 1),
                        rth=T.rth.values, sess=self.bk.sess_codes)
        profs = [instruments.PROFILES[v6lab.PROF[i]] for i in INSTS]
        self.pv = np.array([p["point_value"] for p in profs]); self.tick = np.array([p["tick_value"] for p in profs])
        self.fin = np.array([instruments.margin_frac(p, "intraday") for p in profs])
        self.fon = np.array([instruments.margin_frac(p, "overnight") for p in profs])
        self.rollc = np.array([2 * (p["commission_side"] + p["tick_value"]) for p in profs])
        self.c1 = TC.const1()

    # ------------------------------------------------------------------ demand states
    def demand(self, cid, kind="D2", theta=0.5, score=None, theta0=0.0):
        d = self.des[cid]
        on = (d > 0) & (self.inten[cid] >= theta0)          # OFF band below theta0 of the sleeve's frozen max target
        if kind == "D1":
            x = on.astype(np.int64)
        else:
            x = np.where(~on, 0, np.where(self.inten[cid] >= theta, 2, 1)).astype(np.int64)
        if score is not None:                         # meta gate: non-positive score -> demand 0
            x = np.where(score[cid] > 0, x, 0)
        return x

    def requests(self, kind="D2", theta=0.5, slots=None, agg="max", ids=None, score=None, theta0=0.0):
        ids = ids or self.ids
        n = len(self.T)
        REQ = np.zeros((n, 2), np.int64); X = np.zeros((n, 2))
        dem = {c: self.demand(c, "D1" if kind == "D1" else "D2", theta, score, theta0) for c in ids}
        cl = {}
        for c in ids:
            cl.setdefault(TC.CLUSTER[c], []).append(c)
        for k, members in cl.items():
            k_i = INSTS.index(self.inst[members[0]])
            M = np.stack([dem[c] for c in members], 1)
            mean = M.mean(1)
            X[:, k_i] += mean                            # cluster-equal desired state (fraction of a slot)
            if slots is None:
                REQ[:, k_i] += M.sum(1)
            else:
                agg_v = M.max(1) if agg == "max" else np.floor(mean + 0.5).astype(np.int64)
                REQ[:, k_i] += np.minimum(agg_v, slots)
        return REQ, X, dem

    def priority(self, rule, dem):
        n = len(self.T)
        pr = np.full((n, 2), -1e9)
        for c, d in dem.items():
            k = INSTS.index(self.inst[c])
            if rule == "EQUAL":
                v = np.zeros(n)
            elif rule == "LOW_DD":
                v = np.full(n, -FP.loc[c, "max_dd"])
            elif rule == "HIGH_MB_EXCESS":
                v = np.full(n, FP.loc[c, "excess_vs_mb"])
            elif rule == "INTENSITY":
                v = self.inten[c]
            elif rule == "CLUSTER_DIVERSITY":
                v = np.zeros(n)
            else:
                raise KeyError(rule)
            pr[:, k] = np.where(d > 0, np.maximum(pr[:, k], v), pr[:, k])
        if rule == "CLUSTER_DIVERSITY":   # keep the instrument that carries more distinct active clusters
            for k in range(2):
                cls = {TC.CLUSTER[c] for c in dem if INSTS.index(self.inst[c]) == k}
                cnt = np.zeros(n)
                for cc in cls:
                    cnt += np.max(np.stack([dem[c] > 0 for c in dem if TC.CLUSTER[c] == cc], 1), 1)
                pr[:, k] = cnt
        return pr

    # ------------------------------------------------------------------ run
    def run(self, mode, REQ, X, prio, caps=(2, 2), env="MODERATE", lam=0.25, mu=1.0, H=40, K=2, budget_frac=1.0,
            slip_ticks=1.0, commission=0.62, delay=0, m_intra=1.0, m_on=1.0, rearm=20):
        a = self.arr
        dd, w = lab.ENVELOPES[env] if env != "NONE" else (0.0, 0.0)
        out = intport.kernel(mode, a["o"], a["c"], a["raw"], a["valid"], a["roll"], a["atr"], a["rth"], a["sess"],
                             REQ, X, X, prio, np.array(caps, np.int64), self.pv, self.fin * m_intra, self.fon * m_on, self.rollc,
                             lab.INIT, 0.5, 0.6 * dd, 0.85 * dd, 0.5, 0.25, 0.8 * abs(w), 0.5, slip_ticks * 0.25, commission,
                             int(delay), lam, mu, int(H), int(K), budget_frac, int(rearm))
        keys = ["pos", "equity", "margin_util", "atr_exposure", "gov", "req", "cut", "sides", "fills"]
        return dict(zip(keys, out))

    def daily(self, r):
        return self.bk.daily(r)

    def summary(self, r, pers=("ALL", "F1_2019_2020", "F2_2021_2022", "F3_2023_2024", "F4_2025_2026", "Y2020", "Y2022", "FORMER_HOLDOUT")):
        d = self.daily(r)
        o = {}
        for p in pers:
            o.update(TC.stats(d, p, self.c1))
        n = len(d)
        o["fills_per_day"] = float(r["fills"].sum() / n); o["sides"] = float(r["sides"].sum())
        o["friction"] = float((r["sides"] * (0.62 + self.tick)).sum())
        o["peak_margin"] = float(d.mu_max.max()); o["avg_margin"] = float(d.mu_avg.mean())
        o["avg_MES"] = float(r["pos"][:, 0].mean()); o["avg_MNQ"] = float(r["pos"][:, 1].mean())
        o["max_MES"] = int(r["pos"][:, 0].max()); o["max_MNQ"] = int(r["pos"][:, 1].max())
        o["avg_atr$"] = float(d.atr_avg.mean()); o["peak_atr$"] = float(d.atr_max.max())
        o["gov_cut_bars_share"] = float((r["cut"].sum(1) > 0).mean())
        env = "EXPLORATORY"
        for name in ("CONSERVATIVE", "MODERATE", "AGGRESSIVE"):
            ddl, wl = lab.ENVELOPES[name]
            if o["ALL_max_dd"] <= ddl and o["ALL_worst"] >= wl:
                env = name; break
        o["envelope_ALL"] = env
        return o, d

    def attribution(self, r, dem, rule="LOW_DD"):
        """Per sleeve: requested contracts, received contracts (executed instrument position allocated in priority order),
        denial reasons, and realised gross contribution."""
        pos = r["pos"]; n = len(self.T)
        pr_static = {c: {"EQUAL": 0.0, "LOW_DD": -FP.loc[c, "max_dd"], "HIGH_MB_EXCESS": FP.loc[c, "excess_vs_mb"]}.get(rule, 0.0) for c in dem}
        rows = []
        for k in range(2):
            members = sorted([c for c in dem if INSTS.index(self.inst[c]) == k], key=lambda c: -pr_static[c])
            left = pos[:, k].astype(float).copy()
            dc = np.r_[0.0, np.diff(self.arr["c"][:, k])] * self.pv[k]
            req_total = np.sum([dem[c] for c in members], 0)
            for c in members:
                got = np.minimum(dem[c], left); left = left - got
                held = np.r_[0.0, got[:-1]]
                denied = dem[c] - got
                rows.append({"sleeve": c, "inst": INSTS[k], "cluster": TC.CLUSTER[c], "avg_requested": float(dem[c].mean()),
                             "avg_received": float(got.mean()), "denied_share_of_requests": float(denied.sum() / max(dem[c].sum(), 1)),
                             "denied_symbol_or_cluster_or_track": float(((denied > 0) & (r["cut"][:, k] == 0)).mean()),
                             "denied_governor_cut": float(((denied > 0) & (r["cut"][:, k] > 0)).mean()),
                             "gross_contribution": float((held * dc).sum()),
                             "instrument_requested_total_avg": float(req_total.mean()), "instrument_executed_avg": float(pos[:, k].mean())})
        return pd.DataFrame(rows)
