"""Restore canonical ES parquet from Drive MCP download dumps.

Each dump is JSON {content(base64), id, mimeType, title}. Writes raw parts to
data/raw_parts/, verifies each against the Drive manifest, concatenates in
lexical order, verifies bytes/SHA256. Never modifies source data.
"""
import base64, glob, hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS = os.path.join(ROOT, "data", "raw_parts")
OUT = os.path.join(ROOT, "data", "canonical", "canonical_1m_ES.parquet")

def main(dump_dir):
    manifest = None
    for f in sorted(glob.glob(os.path.join(dump_dir, "*.txt"))):
        d = json.load(open(f))
        b = base64.b64decode(d["content"])
        if d["title"].endswith(".json"):
            manifest = json.loads(b)
        open(os.path.join(PARTS, d["title"]), "wb").write(b)
    if manifest is None:
        manifest = json.load(open(os.path.join(PARTS, "CANONICAL_1M_ES_CHUNKS_MANIFEST.json")))
    report = []
    h = hashlib.sha256(); total = 0
    with open(OUT, "wb") as out:
        for p in sorted(manifest["parts"], key=lambda x: x["filename"]):
            b = open(os.path.join(PARTS, p["filename"]), "rb").read()
            s = hashlib.sha256(b).hexdigest()
            ok = (len(b) == p["bytes"] and s == p["sha256"])
            report.append((p["filename"], len(b), ok))
            if not ok:
                sys.exit(f"PART MISMATCH {p['filename']}")
            out.write(b); h.update(b); total += len(b)
    sha = h.hexdigest()
    print(json.dumps({"parts": len(report), "all_parts_ok": all(r[2] for r in report),
                      "bytes": total, "bytes_ok": total == manifest["source_bytes"],
                      "sha256": sha, "sha_ok": sha == manifest["source_sha256"]}, indent=1))

if __name__ == "__main__":
    main(sys.argv[1])
