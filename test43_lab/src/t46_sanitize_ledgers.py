"""TEST46 mechanical ledger sanitizer (RAW legacy TradingView ledger -> HISTORICAL-ONLY ledger <= 2026-05-27).

Rules (TEST46 recovery addendum):
  * verifies the raw SHA256 against the recorded authority hash;
  * parses timestamps programmatically; keeps a trade only if its ENTRY and EXIT are both <= 2026-05-27;
  * NEVER prints, summarises or writes anything about removed rows (no removed counts/dates/prices/P&L);
  * allowed output only: SOURCE_HASH_MATCH, SANITIZED_FILE, SANITIZED_SHA256, HISTORICAL_ROW_COUNT,
    MAX_RETAINED_ENTRY_DATE, MAX_RETAINED_EXIT_DATE, CUTOFF_COMPLIANCE.
Usage:  python t46_sanitize_ledgers.py <raw_dir> <out_dir>
Works on TradingView "List of trades" exports (one Entry row + one Exit row per trade number)."""
import csv
import hashlib
import io
import json
import os
import sys

CUTOFF = "2026-05-27"
AUTH = {"LC02.csv": "5c04d9dfe6ee94fd14285d170e2f12a70180dc88c29d6e39cf17ce8745844bca",
        "LC03.csv": "d3e66f995ef0a99d698c1beffa157e0673b4688760022c32e87bfe8607ccb2c0",
        "LC05.csv": "29be9e2fc79a5f2c5054dd6e3774629f955989fc5e268defdbe1a1a0ef4fd84d",
        "TS16_S01.csv": "24ca87b40ff400fad1290498644c15a76ca9df187d1d7b5ed146748dda8dba1c",
        "TS22_S01.csv": "f5d28d51143b6edd826c0e5870c61d7a870c332dbbbc9050cb97098b896d327c",
        "T30_W01.csv": "b97a44c1eb9fe08359702deebbb20437a3d86d3e0677bb63bb4b0d7096fd6734"}


# batched multi-candidate exports: (raw file in quarantine, entry-signal selector, target ledger name)
SELECTED = [("T30_ZIP/TEST30_REGIME_CONTEXT_MASTER_V1_PRECOMPILE_NQ_LONG.csv", "T30-L1", "T30_W01.csv"),
            ("TS22_BATCH_NQ.csv", "T22-07", "TS22_S01.csv")]


def sha(b):
    return hashlib.sha256(b).hexdigest()


def sanitize(raw_path, out_dir, selector=None, out_name=None):
    name = out_name or os.path.basename(raw_path)
    raw = open(raw_path, "rb").read()
    rep = {"SOURCE": name, "SOURCE_HASH_MATCH": "YES" if AUTH.get(name) == sha(raw) else ("NO" if name in AUTH else "NO_AUTHORITY_HASH")}
    text = raw.decode("utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    head = [h.strip() for h in rows[0]]
    it, ty, dt = head.index("Trade number"), head.index("Type"), head.index("Date and time")
    trades = {}
    for r in rows[1:]:
        if not r or not r[0].strip():
            continue
        trades.setdefault(r[it].strip(), []).append(r)
    sg = head.index("Signal") if "Signal" in head else None
    keep = []
    for tn, rs in trades.items():
        ent = [r for r in rs if r[ty].strip().lower().startswith("entry")]
        if selector is not None and not (len(ent) == 1 and selector in ent[0][sg]):
            continue
        ex = [r for r in rs if r[ty].strip().lower().startswith("exit")]
        if len(ent) != 1 or len(ex) != 1:
            continue                                   # open / malformed trades are dropped silently (not reported)
        ed, xd = ent[0][dt].strip()[:10], ex[0][dt].strip()[:10]
        if ed <= CUTOFF and xd <= CUTOFF:
            keep.append((tn, rs, ed, xd))
    base = os.path.splitext(name)[0]
    out = os.path.join(out_dir, f"{base}_TO_20260527.csv")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(head)
    for _, rs, _, _ in keep:
        for r in rs:
            w.writerow([c.strip() for c in r])
    data = buf.getvalue().encode("utf-8")
    open(out, "wb").write(data)
    me = max((k[2] for k in keep), default="NONE"); mx = max((k[3] for k in keep), default="NONE")
    rep.update({"SANITIZED_FILE": os.path.basename(out), "SANITIZED_SHA256": sha(data), "HISTORICAL_ROW_COUNT": len(keep),
                "MAX_RETAINED_ENTRY_DATE": me, "MAX_RETAINED_EXIT_DATE": mx,
                "CUTOFF_COMPLIANCE": "PASS" if (me == "NONE" or me <= CUTOFF) and (mx == "NONE" or mx <= CUTOFF) else "FAIL"})
    return rep


def main():
    raw_dir, out_dir = sys.argv[1], sys.argv[2]
    os.makedirs(out_dir, exist_ok=True)
    reps = [sanitize(os.path.join(raw_dir, f), out_dir) for f in AUTH if os.path.exists(os.path.join(raw_dir, f))]
    for raw, sel, nm in SELECTED:
        if os.path.exists(os.path.join(raw_dir, raw)):
            reps.append(sanitize(os.path.join(raw_dir, raw), out_dir, sel, nm))
    json.dump(reps, open(os.path.join(out_dir, "SANITIZER_REPORT.json"), "w"), indent=1)
    for r in reps:
        print(json.dumps(r))


if __name__ == "__main__":
    main()
