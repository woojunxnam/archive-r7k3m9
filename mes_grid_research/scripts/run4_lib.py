"""RUN-4 overnight infrastructure: manifest, append-safe status log, resumable memory-aware worker pool.

results/RUN4_OVERNIGHT/RUN4_MANIFEST.json : every registered configuration (config_id, family, sleeve, parent, params,
                                            exec, deterministic hash, stage, kind)
results/RUN4_OVERNIGHT/RUN4_STATUS.csv    : append-only status rows (PENDING/RUNNING/COMPLETE/FAILED/SKIPPED); the
                                            last row per config_id is authoritative. On restart only unfinished
                                            configs are run again.
results/RUN4_OVERNIGHT/res/<sleeve>/<config_id>.json : one result file per config (atomic write)
All results: "ES-signal / MES-economics proxy backtest" (EXEC-1.1 conservative, ROLL-1.0).
"""
import hashlib, json, os, sys, time, traceback
from multiprocessing import Pool

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import numpy as np, pandas as pd
import psutil

from mesgrid import ENGINE_VERSION, EXEC_SPEC_VERSION, ROLL_MODEL_VERSION, DATASET_SHA256

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "RUN4_OVERNIGHT")
MANIFEST = os.path.join(OUT, "RUN4_MANIFEST.json")
STATUS = os.path.join(OUT, "RUN4_STATUS.csv")
RES = os.path.join(OUT, "res")
LABEL = "ES-signal / MES-economics proxy backtest"
STATUS_COLS = ["config_id", "family", "sleeve", "status", "start", "finish", "engine_version", "exec_spec", "dataset_hash",
               "result_path", "error"]
os.makedirs(RES, exist_ok=True)


def canon(obj):
    return json.dumps(obj, sort_keys=True, default=str, separators=(",", ":"))


def cfg_hash(obj):
    return hashlib.sha1(canon(obj).encode()).hexdigest()[:12]


def make_entry(sleeve, family, params, exec_kw=None, parent=None, kind="engine", stage="S1", fresh=("2022-01-01",),
               note="", extra=None):
    """params = strategy config (A: FactoryStrategy kwargs; B: sim spec; AB: portfolio spec)."""
    exec_kw = exec_kw or {}
    core = dict(sleeve=sleeve, kind=kind, params=params, exec=exec_kw, fresh=list(fresh or []), extra=extra or {})
    h = cfg_hash(core)
    return dict(config_id=f"{sleeve}_{h}", hash=h, sleeve=sleeve, family=family, parent=parent, kind=kind, stage=stage,
                params=params, exec=exec_kw, fresh=list(fresh or []), extra=extra or {}, note=note)


def _atomic_json(path, obj):
    tmp = path + f".tmp{os.getpid()}"
    with open(tmp, "w") as f:
        json.dump(obj, f, default=str)
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, path)


def load_manifest():
    if os.path.exists(MANIFEST):
        return json.load(open(MANIFEST))
    return dict(run="RUN-4 overnight multi-alpha factory", created=time.strftime("%Y-%m-%d %H:%M:%S"), label=LABEL,
                dataset_sha256=DATASET_SHA256, engine_version=ENGINE_VERSION, exec_spec=EXEC_SPEC_VERSION,
                roll_model=ROLL_MODEL_VERSION, configs={})


def register(entries):
    m = load_manifest()
    new = 0
    for e in entries:
        if e["config_id"] not in m["configs"]:
            m["configs"][e["config_id"]] = e
            new += 1
            append_status(dict(config_id=e["config_id"], family=e["family"], sleeve=e["sleeve"], status="PENDING"))
    m["updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _atomic_json(MANIFEST, m)
    return new


def append_status(row):
    r = {k: row.get(k, "") for k in STATUS_COLS}
    r.setdefault("engine_version", ENGINE_VERSION)
    if not r["engine_version"]:
        r["engine_version"] = ENGINE_VERSION
    if not r["exec_spec"]:
        r["exec_spec"] = EXEC_SPEC_VERSION
    if not r["dataset_hash"]:
        r["dataset_hash"] = DATASET_SHA256[:16]
    line = ",".join('"' + str(r[k]).replace('"', "'").replace("\n", " | ") + '"' for k in STATUS_COLS) + "\n"
    new = not os.path.exists(STATUS)
    fd = os.open(STATUS, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        if new:
            os.write(fd, (",".join(STATUS_COLS) + "\n").encode())
        os.write(fd, line.encode())
    finally:
        os.close(fd)


def current_status():
    if not os.path.exists(STATUS):
        return {}
    df = pd.read_csv(STATUS, dtype=str, keep_default_na=False)
    last = df.groupby("config_id").tail(1)
    return dict(zip(last.config_id, last.status))


def result_path(e):
    d = os.path.join(RES, e["sleeve"])
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, e["config_id"] + ".json")


def done_ids():
    st = current_status()
    return {k for k, v in st.items() if v == "COMPLETE"}


def _worker_wrap(args):
    fn, e = args
    t0 = time.strftime("%Y-%m-%d %H:%M:%S")
    append_status(dict(config_id=e["config_id"], family=e["family"], sleeve=e["sleeve"], status="RUNNING", start=t0))
    try:
        res = fn(e)
        res.update(config_id=e["config_id"], family=e["family"], sleeve=e["sleeve"], parent=e.get("parent"),
                   stage=e.get("stage"), label=LABEL, params=canon(e["params"]), exec=canon(e["exec"]),
                   lineage=dict(dataset=DATASET_SHA256[:16], engine=ENGINE_VERSION, exec_spec=EXEC_SPEC_VERSION, roll=ROLL_MODEL_VERSION))
        p = result_path(e)
        _atomic_json(p, res)
        append_status(dict(config_id=e["config_id"], family=e["family"], sleeve=e["sleeve"], status="COMPLETE", start=t0,
                           finish=time.strftime("%Y-%m-%d %H:%M:%S"), result_path=os.path.relpath(p, ROOT)))
        return e["config_id"], "COMPLETE", None
    except Exception as ex:  # noqa: BLE001
        err = f"{type(ex).__name__}: {ex} :: {traceback.format_exc()[-800:]}"
        append_status(dict(config_id=e["config_id"], family=e["family"], sleeve=e["sleeve"], status="FAILED", start=t0,
                           finish=time.strftime("%Y-%m-%d %H:%M:%S"), error=err))
        return e["config_id"], "FAILED", err


def run_entries(entries, fn, init_fn=None, init_args=(), nmax=3, start_workers=2, min_avail_gb=2.5, grow_avail_gb=7.0,
                log=print, tag="batch"):
    """Resumable, memory-aware execution. Skips COMPLETE configs. fn(entry)->dict runs in a worker initialised by
    init_fn(*init_args). In-flight tasks are limited adaptively by available memory."""
    done = done_ids()
    todo = [e for e in entries if e["config_id"] not in done or not os.path.exists(result_path(e))]
    log(f"[{tag}] {len(entries)} configs, {len(entries) - len(todo)} already complete, {len(todo)} to run")
    if not todo:
        return []
    results = []
    limit = start_workers
    grown_at = time.time()
    with Pool(nmax, initializer=init_fn, initargs=init_args) as pool:
        it = iter(todo)
        inflight = {}
        exhausted = False
        nfin = 0
        t_start = time.time()
        while True:
            avail = psutil.virtual_memory().available / 1e9
            if avail < min_avail_gb and limit > 1:
                limit -= 1
                log(f"[{tag}] low memory {avail:.1f} GB -> in-flight limit {limit}")
            elif avail > grow_avail_gb and limit < nmax and time.time() - grown_at > 300 and nfin >= 4:
                limit += 1
                grown_at = time.time()
                log(f"[{tag}] memory {avail:.1f} GB free -> in-flight limit {limit}")
            while not exhausted and len(inflight) < limit:
                e = next(it, None)
                if e is None:
                    exhausted = True
                    break
                inflight[e["config_id"]] = pool.apply_async(_worker_wrap, ((fn, e),))
            ready = [k for k, r in inflight.items() if r.ready()]
            for k in ready:
                r = inflight.pop(k)
                try:
                    cid, stt, err = r.get()
                except Exception as ex:  # noqa: BLE001
                    cid, stt, err = k, "FAILED", str(ex)
                    append_status(dict(config_id=k, status="FAILED", error=str(ex)))
                results.append((cid, stt, err))
                nfin += 1
                if stt == "FAILED":
                    log(f"[{tag}] FAILED {cid}: {str(err)[:300]}")
                if nfin % 10 == 0:
                    el = time.time() - t_start
                    log(f"[{tag}] {nfin}/{len(todo)} done, {el / 60:.1f} min, ~{el / nfin * (len(todo) - nfin) / 60:.0f} min left, "
                        f"mem avail {avail:.1f} GB, in-flight {limit}")
            if exhausted and not inflight:
                break
            time.sleep(0.5)
    return results


def collect(sleeve, ids=None):
    d = os.path.join(RES, sleeve)
    rows = []
    if not os.path.isdir(d):
        return pd.DataFrame()
    for f in os.listdir(d):
        if not f.endswith(".json"):
            continue
        cid = f[:-5]
        if ids is not None and cid not in ids:
            continue
        try:
            rows.append(json.load(open(os.path.join(d, f))))
        except Exception:  # noqa: BLE001
            pass
    return pd.DataFrame(rows)
