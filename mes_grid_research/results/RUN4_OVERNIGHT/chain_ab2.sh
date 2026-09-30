#!/bin/bash
cd /home/user/archive-r7k3m9/mes_grid_research
python scripts/run4_port.py series results/RUN4_OVERNIGHT/mech_SALVpts10.json 1 > results/RUN4_OVERNIGHT/series_salv2.log 2>&1
python scripts/run4_port.py series results/RUN4_OVERNIGHT/mech_PASSIVE.json 1 > results/RUN4_OVERNIGHT/series_passive2.log 2>&1
python scripts/run4_fill_mech.py results/RUN4_OVERNIGHT/mech_SALVpts10.json > results/RUN4_OVERNIGHT/ab2.log 2>&1
python scripts/run4_fill_mech.py results/RUN4_OVERNIGHT/mech_PASSIVE.json >> results/RUN4_OVERNIGHT/ab2.log 2>&1
python scripts/run4_port.py ab results/RUN4_OVERNIGHT/mech_SALVpts10.json >> results/RUN4_OVERNIGHT/ab2.log 2>&1
python scripts/run4_port.py ab results/RUN4_OVERNIGHT/mech_PASSIVE.json >> results/RUN4_OVERNIGHT/ab2.log 2>&1
echo ALLDONE >> results/RUN4_OVERNIGHT/ab2.log
