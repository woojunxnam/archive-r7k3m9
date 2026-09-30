#!/bin/bash
cd /home/user/archive-r7k3m9/mes_grid_research
until grep -q "DONE wave1$" results/RUN4_OVERNIGHT/a_wave1.log; do sleep 30; done
sleep 60
python scripts/run4_a.py wave3 3 > results/RUN4_OVERNIGHT/a_wave3.log 2>&1
