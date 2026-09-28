"""run one nested GA lane: python prog_run_lane.py <lane_module> <out_dir> <test>"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prog_common as P  # noqa: E402
import prog_ga as PG  # noqa: E402

if __name__ == "__main__":
    lane, out, test = sys.argv[1:4]
    S, n = PG.run_lane(lane, out)
    P.budget(test, genomes=n, note=f"nested GA lane {lane}")
    print(S.drop(columns=["genome"], errors="ignore").round(2).to_string())
    print("UNIQUE_GENOMES", n)
