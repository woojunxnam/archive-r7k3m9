import glob, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
from run3_lib import run_batch
from run3_p45 import jobs, extra
R = os.path.join(os.path.dirname(__file__), "..", "results", "RUN3_P45")
done = set()
for f in glob.glob(os.path.join(R, "summary_part*.csv")):
    done |= set(pd.read_csv(f).name)
js = [j for j in jobs() if j[0] not in done]
print(len(js), "remaining", flush=True)
n = int(os.environ.get("PART", "3"))
run_batch(f"RUN3_P45c", js, procs=int(os.environ.get("PROCS", "2")), extra_feature_fn=extra)
