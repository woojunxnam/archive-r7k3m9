#!/bin/bash
# run A waves sequentially after wave1 (PID 1065) finishes
cd /home/user/archive-r7k3m9/mes_grid_research
while kill -0 1065 2>/dev/null; do sleep 30; done
python scripts/run4_a.py wave2 3 > results/RUN4_OVERNIGHT/a_wave2.log 2>&1
echo "wave2 exit $?" >> results/RUN4_OVERNIGHT/a_wave2.log
