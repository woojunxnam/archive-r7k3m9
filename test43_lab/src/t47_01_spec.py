"""T47_02 predeclared spec dump (runs BEFORE any economic TEST47 computation)."""
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import t47_common as C  # noqa: E402

p = os.path.join(C.T47, "T47_02_predeclared_spec.json")
d = {"written_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z", "research_data_end": "2026-05-27", **C.SPEC}
json.dump(d, open(p, "w"), indent=1)
h = hashlib.sha256(open(p, "rb").read()).hexdigest()
open(p + ".sha256", "w").write(h + "\n")
print(h)
