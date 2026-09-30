"""fill ddA_by_cap (max MTM DD of the A series by cap) into a mechanism json (for risk-budget allocations)."""
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
import run4_lib as L
mf = sys.argv[1]
mech = json.load(open(mf))
m = json.load(open(L.MANIFEST))["configs"]
dd = {}
for cid, e in m.items():
    if e["family"] == "A-SERIES" and e["note"].startswith(f"SERIES {mech['name']} cap") and "pause" not in e["note"]:
        p = L.result_path(e)
        if os.path.exists(p):
            r = json.load(open(p))
            dd[e["note"].split("cap")[1].split()[0]] = abs(r["max_mtm_dd"])
mech["ddA_by_cap"] = dd
json.dump(mech, open(mf, "w"), indent=1)
print(mech["name"], dd)
