#!/usr/bin/env python3
"""Fail-closed source verification for MAIN_GROWTH_V2 dashboard handoff."""
from __future__ import annotations
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[3]
MAN = json.loads((HERE / "03_SOURCE_MANIFEST.json").read_text())
EXPECTED_COMMIT = MAN["research_source_commit"]

def run(*args: str) -> str:
    return subprocess.check_output(args, cwd=ROOT, text=True).strip()

def main() -> int:
    errors = []
    try:
        run("git", "cat-file", "-e", f"{EXPECTED_COMMIT}^{{commit}}")
    except Exception as e:
        errors.append(f"missing research source commit {EXPECTED_COMMIT}: {e}")

    for item in MAN["canonical_sources"]:
        path = item["path"]
        expected = item["blob_sha"]
        try:
            actual = run("git", "rev-parse", f"{EXPECTED_COMMIT}:{path}")
        except Exception as e:
            errors.append(f"{path}: cannot resolve at source commit: {e}")
            continue
        if actual != expected:
            errors.append(f"{path}: blob mismatch expected={expected} actual={actual}")

    if errors:
        print("HANDOFF VERIFY: FAIL")
        for e in errors:
            print(" -", e)
        return 2

    print("HANDOFF VERIFY: PASS")
    print("research_source_commit:", EXPECTED_COMMIT)
    print("canonical_sources:", len(MAN["canonical_sources"]))
    print("NOTE: this verifies pinned research sources. Run frozen/t61_r1c verification separately for its internal hash package.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
