import sys, time, itertools
import pandas as pd
sys.path.insert(0,'.')
from t43 import grid
cfgs=[]
for M in (24,28,32,36,40):
    for K in (0,8,10,12,14,16,18,20):
        if K>=M: continue
        for on in (0,1,2,3):
            c=dict(intradayMaxQty=M, coreQty=K, coreBuildMode=1 if K>0 else 0, overnightMode=on,
                   overnightMaxQty=10, _label=f"M{M}_K{K}_O{on}")
            cfgs.append(c)
t=time.time()
df=grid.run_grid(cfgs)
print(len(df), 'runs', round(time.time()-t),'s')
df.to_csv('../out/04_MAX_CORE_OVERNIGHT_GRID.csv', index=False)
cols=['label','DEV_avg_daily','DEV_max_dd','DEV_worst_day','DEV_avg_mes','VAL_avg_daily','VAL_max_dd','VAL_worst_day','margin_util','DEV_env']
print(df.sort_values('DEV_avg_daily',ascending=False)[cols].head(25).round(0).to_string())
print(df[df.label.str.match(r'M24_K0_O[0-3]$')][cols].round(0).to_string())
