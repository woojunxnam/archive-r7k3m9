"""TRACK A - deterministic forward-shadow runner for C43-CORE, T55 and T61-R1C_ATOMIC_CAP6.

Usage
  forward (first OOS session 2026-09-29; run after each session close, causal END-stamped America/New_York 1m bars):
      python shadow/forward_shadow.py forward --es <canonical_1m_ES.parquet> --mnq <canonical_1m_MNQ.parquet> --through YYYY-MM-DD
  replay QA on research data only (<= 2026-05-27; never forward data):
      python shadow/forward_shadow.py replay --end 2026-05-27 --report-start 2026-01-02

Every run: (1) frozen/t61_r1c integrity check - fail closed on any hash change; (2) a fresh workspace with a byte-identical copy of the
frozen source + artifacts and the given canonical files; (3) shadow_engine.py in a subprocess; (4) run manifest with all hashes.
Forward mode writes ONLY sessions >= 2026-09-29; sessions 2026-05-28 .. 2026-09-28 are engine warm-up (state continuity) and are never
written or reported.  Never places orders (no broker connection exists in this code)."""
import argparse
import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__)); LAB = os.path.abspath(os.path.join(HERE, ".."))
PKG = os.path.join(LAB, "frozen", "t61_r1c")
sys.path.insert(0, PKG)
import verify_frozen  # noqa: E402

OOS_START = "2026-09-29"; RESEARCH_END = "2026-05-27"
CANON = {"ES": "2b4f41b124ab8772866088f87a86c6cc456ecbb2a9ede6b0bccbc24fbc454116", "MNQ": "66204b12cd4270f18b05e46045c9b8daf62c033620cfb0f170dbdb8b882ecea2"}


def sha(p):
    return verify_frozen.sha(p)


def build_ws(ws, es, mnq):
    if os.path.exists(ws):
        shutil.rmtree(ws)
    shutil.copytree(os.path.join(PKG, "src"), os.path.join(ws, "src"))
    shutil.copytree(os.path.join(PKG, "artifacts", "out"), os.path.join(ws, "out"))
    os.makedirs(os.path.join(ws, "data"))
    for inst, p in (("ES", es), ("MNQ", mnq)):
        os.symlink(os.path.abspath(p), os.path.join(ws, "data", f"canonical_1m_{inst}.parquet"))
    for d in ("out/program", "out/HIGH_EXPOSURE_PROGRAM", "out/mnq", "out/p123", "reports"):
        os.makedirs(os.path.join(ws, d), exist_ok=True)
    # the workspace copy must be byte-identical to the frozen package
    for root, _, fs in os.walk(os.path.join(ws, "src")):
        for f in fs:
            if f.endswith(".py"):
                a = os.path.join(root, f); b = os.path.join(PKG, os.path.relpath(a, ws))
                if sha(a) != sha(b):
                    raise verify_frozen.FrozenIntegrityError(f"workspace copy differs: {a}")


def run(mode, es, mnq, data_end, report_start, out_dir):
    verify_frozen.verify(check_live=True, check_data=(mode == "replay"))
    hs = {"ES": sha(es), "MNQ": sha(mnq)}
    if mode == "replay":
        if data_end > RESEARCH_END or hs != CANON:
            raise SystemExit("replay mode is restricted to the hash-verified research data <= 2026-05-27")
    else:
        if report_start < OOS_START or data_end < OOS_START:
            raise SystemExit("forward mode reports sessions >= 2026-09-29 only")
    out_dir = os.path.abspath(out_dir); ws = os.path.join(out_dir, "_workspace")
    build_ws(ws, es, mnq)
    cfg = {"mode": mode, "data_end": data_end, "report_start": report_start, "data_sha256": hs, "out_dir": os.path.abspath(out_dir),
           "frozen_manifest_sha256": open(os.path.join(PKG, "T61_R1C_MANIFEST.sha256")).read().split()[0]}
    json.dump(cfg, open(os.path.join(ws, "run_config.json"), "w"), indent=1)
    env = dict(os.environ, SHADOW_WS=ws, PYTHONHASHSEED="0")
    r = subprocess.run([sys.executable, os.path.join(HERE, "shadow_engine.py")], env=env, cwd=ws)
    if r.returncode != 0:
        raise SystemExit(f"shadow engine failed ({r.returncode})")
    verify_frozen.verify(check_live=True, quiet=True)                     # still intact after the run
    outs = sorted(f for f in os.listdir(out_dir) if not f.startswith("_"))
    man = {**cfg, "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "engine_sha256": sha(os.path.join(HERE, "shadow_engine.py")), "runner_sha256": sha(os.path.abspath(__file__)),
           "outputs": {f: sha(os.path.join(out_dir, f)) for f in outs}, "orders_sent": 0, "LIVE_AUTHORIZATION": "NO"}
    json.dump(man, open(os.path.join(out_dir, "RUN_MANIFEST.json"), "w"), indent=1)
    shutil.rmtree(ws)
    return man


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["forward", "replay"])
    ap.add_argument("--es", default=os.path.join(LAB, "data", "canonical_1m_ES.parquet"))
    ap.add_argument("--mnq", default=os.path.join(LAB, "data", "canonical_1m_MNQ.parquet"))
    ap.add_argument("--through"); ap.add_argument("--end"); ap.add_argument("--report-start")
    ap.add_argument("--out")
    a = ap.parse_args()
    if a.mode == "forward":
        end = a.through; rs = OOS_START
        out = a.out or os.path.join(LAB, "out", "forward_shadow", f"through_{end}")
    else:
        end = a.end or RESEARCH_END; rs = a.report_start or end
        out = a.out or os.path.join(LAB, "out", "forward_shadow_qa", f"replay_{end}")
    os.makedirs(out, exist_ok=True)
    print(json.dumps(run(a.mode, a.es, a.mnq, end, rs, out), indent=1)[:800])


if __name__ == "__main__":
    main()
