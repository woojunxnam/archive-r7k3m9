"""TEST96 data layer: canonical 1m NQ / YM / RTY (full-contract, back-adjusted, END-stamped NY) reconstructed from exact 1 MB chunks, SHA-verified
fail-closed, placed on the SAME session grid as ES / MNQ (TEST45 panel).  Research data <= 2026-05-27 only.
Execution economics: NQ signal -> MNQ contract ($2/pt, tick 0.25 = $0.50);  YM -> MYM ($0.5/pt, tick 1.0 = $0.50);  RTY -> M2K ($5/pt, tick 0.1 = $0.50).
The ES / MNQ instrument indices (k = 0, 1) are unchanged; extra instruments are appended in-process only."""
import hashlib
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

SHA = {"NQ": "e6298965fb7ba71efd9114c4f303e393eb9d8e0ae2ddb290aa42daae0c64c663",
       "RTY": "7539af4407ca8c5e149c4b9e006ac691323b7a736bfc5fbe2788bfd2a6246999",
       "YM": "edde4419b90e6545bb8f170bbf009622275ef1b1ad5fbe974952364e3ea0a6d5"}
NCH = {"NQ": 43, "RTY": 39, "YM": 40}
DATA_DIR = os.path.join(os.path.abspath(C45.ROOT), "data")
XPROF = {"NQ": dict(symbol="MNQ", point_value=2.0, tick=0.25, tick_value=0.50), "YM": dict(symbol="MYM", point_value=0.5, tick=1.0, tick_value=0.50),
         "RTY": dict(symbol="M2K", point_value=5.0, tick=0.1, tick_value=0.50)}
MARGIN = {"MES": 1500.0, "MNQ": 2000.0, "MYM": 1000.0, "M2K": 700.0}     # approximate intraday-independent initial margin / contract (reporting only)


def reconstruct(inst):
    """concatenate chunks by filename order, require the exact SHA256; write data/canonical_1m_<inst>.parquet.  Fail closed."""
    out = os.path.join(DATA_DIR, f"canonical_1m_{inst}.parquet")
    if os.path.exists(out) and hashlib.sha256(open(out, "rb").read()).hexdigest() == SHA[inst]:
        return out
    parts = [os.path.join(DATA_DIR, "mb1", f"canonical_1m_{inst}.parquet.mb1.part{i:03d}") for i in range(NCH[inst])]
    miss = [p for p in parts if not os.path.exists(p)]
    if miss:
        raise RuntimeError(f"{inst}: missing chunks {[os.path.basename(p)[-7:] for p in miss]}")
    b = b"".join(open(p, "rb").read() for p in parts)
    h = hashlib.sha256(b).hexdigest()
    if h != SHA[inst]:
        raise RuntimeError(f"{inst}: SHA mismatch {h} != {SHA[inst]} (fail closed)")
    open(out, "wb").write(b)
    return out


def register():
    """append NQ / YM / RTY to the TEST45 instrument tables (in-process)."""
    if "YM" in C45.INSTS:
        return
    for i in ("NQ", "YM", "RTY"):
        reconstruct(i)
        C45.DATA[i] = (f"data/canonical_1m_{i}.parquet", SHA[i]); C45.PROF[i] = XPROF[i]
    C45.INSTS = ("ES", "MNQ", "NQ", "YM", "RTY")
    C45.PV = np.array([C45.PROF[i]["point_value"] for i in C45.INSTS]); C45.TICKV = np.array([C45.PROF[i]["tick_value"] for i in C45.INSTS])


def panel():
    """TEST45 panel (ES / MNQ sessions) extended with NQ / YM / RTY arrays on the same session grid (cached)."""
    register()
    pth = os.path.join(C45.ROOT, "out", "t96", "panel_x.npz"); os.makedirs(os.path.dirname(pth), exist_ok=True)
    P = dict(C45.build_panel())
    if os.path.exists(pth):
        z = np.load(pth, allow_pickle=True); P.update({k: z[k] for k in z.files}); return P
    X = {}
    for i in ("NQ", "YM", "RTY"):
        A, se, roll_in = C45._panel_inst(i, P["sessions"])
        for f in A:
            X[f"{i}_{f}"] = A[f]
        X[f"{i}_se"] = se; X[f"{i}_roll_in"] = roll_in
    np.savez_compressed(pth, **X); P.update(X)
    return P


_C = {}


def load(names=("ES", "MNQ", "NQ", "YM", "RTY")):
    """box_common.Inst objects for all instruments (ES / MNQ from the standard loader)."""
    import box_common as B
    import t47_engine as E
    if "I" not in _C:
        Is = dict(B.load()); P = panel()
        for i in ("NQ", "YM", "RTY"):
            Is[i] = B.Inst(E.Mkt(P, i), i)
        _C["I"] = Is
    return {k: _C["I"][k] for k in names}


if __name__ == "__main__":
    for i in ("NQ", "YM", "RTY"):
        print(i, reconstruct(i))
    Is = load()
    for k, I in Is.items():
        cov = float(np.isfinite(I.FP[:, 0]).mean()); vol = float((I.V[:, :] > 0).mean())
        print(k, I.pv, I.cs, I.cs4, I.n, I.sess[0].date(), I.sess[-1].date(), "open-cov", round(cov, 4), "vol>0", round(vol, 3), "C_end", I.C[-1, -1], "atr", round(I.atr[-1], 2))
