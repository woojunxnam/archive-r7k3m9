#!/bin/bash
cd /home/user/archive-r7k3m9/mes_grid_research
until grep -q "DONE wave1b" results/RUN4_OVERNIGHT/a_wave1b.log 2>/dev/null; do sleep 30; done
python scripts/run4_a.py wave1c 1 > results/RUN4_OVERNIGHT/a_wave1c.log 2>&1
