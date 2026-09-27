set -e
cd /home/user/lab
python -W ignore src/t45_00_baseline.py > out/t45/baseline.log 2>&1
python -W ignore src/t45_02_morning.py > out/t45/morning.log 2>&1
python -W ignore src/t45_03_det.py > out/t45/det.log 2>&1
python -W ignore src/t45_04_ml.py > out/t45/ml.log 2>&1
python -W ignore src/t45_05_ga.py > out/t45/ga.log 2>&1
python -W ignore src/t45_06_gp.py > out/t45/gp.log 2>&1
python -W ignore src/t45_07_eval.py > out/t45/eval.log 2>&1
python -W ignore src/t45_08_v6carry.py > out/t45/v6carry.log 2>&1
python -W ignore src/t45_09_select.py > out/t45/select.log 2>&1
echo PIPELINE_DONE
