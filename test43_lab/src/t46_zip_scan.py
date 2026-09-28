"""Scan a Drive-downloaded zip (harness-saved JSON, never displayed) for members whose SHA256 equals an INDEX6 authority
hash; extract ONLY those to the raw quarantine.  Prints only matched target names + member paths.  No content printed."""
import base64, hashlib, io, json, os, sys, zipfile
sys.path.insert(0, os.path.dirname(__file__))
from t46_sanitize_ledgers import AUTH
src = sys.argv[1]
Q = "/home/user/quarantine_raw_ledgers"
d = json.load(open(src)); b = base64.b64decode(d["content"]); os.remove(src)
inv = {v: k for k, v in AUTH.items()}
z = zipfile.ZipFile(io.BytesIO(b))
found = []
for m in z.namelist():
    if m.endswith("/"):
        continue
    data = z.read(m); h = hashlib.sha256(data).hexdigest()
    if h in inv:
        open(os.path.join(Q, inv[h]), "wb").write(data); found.append({"target": inv[h], "member": m})
print(json.dumps({"zip": d.get("title"), "members": len(z.namelist()), "authority_matches": found}))
