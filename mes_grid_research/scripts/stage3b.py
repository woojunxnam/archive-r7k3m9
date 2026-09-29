"""FACTORY_S3b: local robustness of the floating-recycle + recovery family found in S4b."""
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
from factory_lib import run_batch
from stage4b import FL, REC

ADD = dict(add_trigger="armed", reversal="ll_fail")


def jobs():
    out = []
    def add(base, tag, cfg):
        out.append((f"{base}__{tag}", "S3b", base, base, cfg, {}, False))
    B = "Y_fl16_16_Q_add"
    for st in (4.0, 4.5, 5.5, 6.0):
        add(B, f"step{st}", FL(16, 16, **REC(16), **ADD, rec_step=st))
    for tp in (2.5, 2.75, 3.25, 3.5):
        add(B, f"tp{tp}", FL(16, 16, **REC(16), **ADD, rec_tp=tp))
    for lx in (4.0, 4.5, 5.5, 6.0):
        add(B, f"lx{lx}", FL(16, 16, **REC(16, lx), **ADD))
    for cc, rc in ((13, 19), (14, 18), (18, 14), (19, 13)):
        add(B, f"core{cc}", FL(cc, rc, **REC(cc), **ADD))
    add(B, "rtp1.5", dict(FL(16, 16, **ADD), recovery=dict(h=16, rec_tp=1.5, rec_step=10.0, layer_x=5.0)))
    add(B, "rtp2.5", dict(FL(16, 16, **ADD), recovery=dict(h=16, rec_tp=2.5, rec_step=10.0, layer_x=5.0)))
    add(B, "rstep8", dict(FL(16, 16, **ADD), recovery=dict(h=16, rec_tp=2.0, rec_step=8.0, layer_x=5.0)))
    add(B, "rstep12", dict(FL(16, 16, **ADD), recovery=dict(h=16, rec_tp=2.0, rec_step=12.0, layer_x=5.0)))
    add(B, "grid4.5", FL(16, 16, **REC(16), **ADD, grid=4.5))
    add(B, "grid5.5", FL(16, 16, **REC(16), **ADD, grid=5.5))
    B2 = "Y_fl12_20_Q"
    for st in (4.0, 6.0):
        add(B2, f"step{st}", FL(12, 20, **REC(12), rec_step=st))
    for tp in (2.5, 3.5):
        add(B2, f"tp{tp}", FL(12, 20, **REC(12), rec_tp=tp))
    for cc, rc in ((10, 22), (14, 18)):
        add(B2, f"core{cc}", FL(cc, rc, **REC(cc)))
    return out


if __name__ == "__main__":
    js = jobs(); print(len(js))
    run_batch("FACTORY_S3b", js, procs=4)
