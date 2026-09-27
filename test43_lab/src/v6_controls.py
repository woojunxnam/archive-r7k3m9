import sys, os; sys.path.insert(0, '.')
import pandas as pd
from t43 import v6lab
cols = ['label','DV_avg_daily','DV_max_dd','DV_worst_day','DV_avg_mes','DV_avg_ex_top5','PRE23_avg_daily','P23_avg_daily','Y2022_total','DEV_avg_daily','VAL_avg_daily','peak_margin_util','fills','DV_env']
for inst in ('ES','MNQ'):
    cfgs=[]
    for N in (1,2,3,4,6,8,10):
        cfgs.append(dict(_label=f'CONST{N}', capRTH=N, capON=N, marginU=0.8, onMode=4))
    for vb in (1000,1500,2000,3000,4000,6000):
        cfgs.append(dict(_label=f'VOLT{vb}', capRTH=40, capON=40, marginU=0.8, volBudget=vb, onMode=4))
    for N in (3,4,6,8,10):
        cfgs.append(dict(_label=f'REGIME{N}', capRTH=N, capON=N, marginU=0.8, onMode=4, fBear=0.0, fNeut=0.5, fMed=1.0, fStrong=1.0))
        cfgs.append(dict(_label=f'REGIME{N}_TR', capRTH=N, capON=N, marginU=0.8, onMode=4, fBear=0.0, fNeut=0.5, fMed=1.0, fStrong=1.0, trendMult=0.5))
    for vb in (2000,3000,4000,6000):
        cfgs.append(dict(_label=f'VOLT{vb}_REG', capRTH=40, capON=40, marginU=0.8, volBudget=vb, onMode=4, fBear=0.0, fNeut=0.5, fMed=1.0, fStrong=1.0))
        for dd in (4000,8000):
            cfgs.append(dict(_label=f'VOLT{vb}_REG_DD{dd}', capRTH=40, capON=40, marginU=0.8, volBudget=vb, onMode=4, fBear=0.0, fNeut=0.5, fMed=1.0, fStrong=1.0, dd1=dd, dd2=dd*1.5, ddM1=0.5, ddM2=0.0, ddRearmTier=2, ddCooldown=3))
    df=v6lab.run_many(inst,cfgs)
    os.makedirs('../out/v6',exist_ok=True); df.to_csv(f'../out/v6/controls_{inst}.csv',index=False)
    print(inst); print(df[cols].round(1).to_string())
