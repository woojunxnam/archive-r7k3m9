#!/bin/bash
cd /home/user/archive-r7k3m9/mes_grid_research
python scripts/run4_a.py wave1b 1 > results/RUN4_OVERNIGHT/a_wave1b.log 2>&1
python scripts/run4_a.py wave1c 1 > results/RUN4_OVERNIGHT/a_wave1c.log 2>&1
