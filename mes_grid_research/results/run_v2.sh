cd /home/user/archive-r7k3m9/mes_grid_research
while pgrep -f walkforward.py >/dev/null; do sleep 10; done
python3 scripts/stage1.py FACTORY_S1v2 > results/s1v2.log 2>&1
python3 scripts/stage3.py FACTORY_S3v2 > results/s3v2.log 2>&1
python3 scripts/stage4.py FACTORY_S4v2 > results/s4v2.log 2>&1
python3 scripts/stage4b.py FACTORY_S4b > results/s4b.log 2>&1
echo ALLDONE >> results/s4v2.log
