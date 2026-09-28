"""Move a Drive-download JSON (saved by the harness, never displayed) into the raw-ledger quarantine, decode the base64
payload and print ONLY: target name, byte-size-free SHA256 and authority hash match.  No content is ever printed."""
import base64, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from t46_sanitize_ledgers import AUTH
src, name = sys.argv[1], sys.argv[2]
Q = "/home/user/quarantine_raw_ledgers"
d = json.load(open(src))
b = base64.b64decode(d["content"])
open(os.path.join(Q, name), "wb").write(b)
os.remove(src)
h = hashlib.sha256(b).hexdigest()
print(json.dumps({"target": name, "drive_title": d.get("title"), "raw_sha256": h,
                  "authority_hash_match": "YES" if AUTH.get(name) == h else "NO"}))
