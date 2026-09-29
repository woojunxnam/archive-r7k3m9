import os, sys
sys.path.insert(0, os.path.dirname(__file__))
import pandas as pd
from run3_lib import run_batch
from run3_p45 import jobs, extra
done = set(pd.read_csv(os.path.join(os.path.dirname(__file__), "..", "results", "RUN3_P45", "summary_part1.csv")).name)
js = [j for j in jobs() if j[0] not in done]
print(len(js), "remaining")
run_batch("RUN3_P45b", js, procs=3, extra_feature_fn=extra)
