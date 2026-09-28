"""TEST96: sanitize newly recovered raw legacy ledgers (quarantine -> data_legacy/*_TO_20260527.csv) with the frozen TEST46 sanitizer.
Prints ONLY the sanitizer's allowed fields (hash match, file, sha, historical row count, max retained dates, cutoff compliance)."""
import glob, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from t46_sanitize_ledgers import sanitize
Q = "/home/user/quarantine_raw_ledgers"; OUT = os.path.join(os.path.dirname(__file__), "..", "data_legacy")
reps = []
import hashlib, pandas as pd
CUT = pd.Timestamp("2026-05-27 23:59:59")
# chart-data (bar) export: keep bars <= cutoff and only the T13-07 columns; print only row count / max date
raw = os.path.join(Q, "TS13_BATCH_YM.csv")
if os.path.exists(raw):
    d = pd.read_csv(raw, usecols=["time", "open", "high", "low", "close", "Volume", "T13-07 SIG", "T13-07 PNL"])
    t = pd.to_datetime(d.time, unit="s", utc=True).dt.tz_convert("America/New_York").dt.tz_localize(None) if pd.api.types.is_numeric_dtype(d.time) else pd.to_datetime(d.time.str[:19])
    d = d[t <= CUT].assign(time_ny=t[t <= CUT].values)
    out = os.path.join(OUT, "TS13_BATCH_YM_T1307_BARS_TO_20260527.csv"); d.to_csv(out, index=False)
    reps.append({"SOURCE": "TS13_BATCH_YM.csv", "SANITIZED_FILE": os.path.basename(out), "SANITIZED_SHA256": hashlib.sha256(open(out, "rb").read()).hexdigest(),
                 "HISTORICAL_ROW_COUNT": len(d), "MIN_RETAINED_BAR": str(d.time_ny.min()), "MAX_RETAINED_BAR": str(d.time_ny.max()), "CUTOFF_COMPLIANCE": "PASS" if d.time_ny.max() <= CUT else "FAIL"})
reps.append(sanitize(os.path.join(Q, "TS17_BATCH_YM.csv"), OUT, None, "TS17_S01.csv"))
for p in sorted(glob.glob(os.path.join(Q, "TS13_S01_YM_*.csv"))):
    reps.append(sanitize(p, OUT, "T13-07", os.path.basename(p).replace("TS13_S01_YM", "TS13_S01_T1307")))
for p in sorted(glob.glob(os.path.join(Q, "TEST20_*.csv"))):
    reps.append(sanitize(p, OUT))
json.dump(reps, open(os.path.join(OUT, "SANITIZER_REPORT_T96.json"), "w"), indent=1)
for r in reps:
    print(json.dumps(r))
