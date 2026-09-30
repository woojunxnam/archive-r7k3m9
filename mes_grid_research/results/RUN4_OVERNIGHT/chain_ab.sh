#!/bin/bash
cd /home/user/archive-r7k3m9/mes_grid_research
until [ -f results/RUN4_OVERNIGHT/series_passive.log ] && grep -q "DONE series" results/RUN4_OVERNIGHT/series_passive.log; do sleep 30; done
python scripts/run4_fill_mech.py results/RUN4_OVERNIGHT/mech_SALVpts10.json > results/RUN4_OVERNIGHT/ab.log 2>&1
python scripts/run4_fill_mech.py results/RUN4_OVERNIGHT/mech_PASSIVE.json >> results/RUN4_OVERNIGHT/ab.log 2>&1
python scripts/run4_port.py ab results/RUN4_OVERNIGHT/mech_SALVpts10.json >> results/RUN4_OVERNIGHT/ab.log 2>&1
python scripts/run4_port.py ab results/RUN4_OVERNIGHT/mech_PASSIVE.json >> results/RUN4_OVERNIGHT/ab.log 2>&1
echo ALLDONE >> results/RUN4_OVERNIGHT/ab.log
