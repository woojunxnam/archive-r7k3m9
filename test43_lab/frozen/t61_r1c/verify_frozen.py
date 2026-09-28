"""Fail-closed integrity guard for the permanently frozen T61-R1C_ATOMIC_CAP6 package.

verify() re-hashes every file listed in T61_R1C_HASH_INDEX.csv:
  * the frozen copy inside frozen/t61_r1c/ must match the recorded sha256;
  * the live file it was copied from (lab-relative `live_path`) must still be byte-identical (so no research edit can silently
    change the code a shadow run imports);
  * the manifest itself must match T61_R1C_MANIFEST.sha256.
Any mismatch or missing file raises FrozenIntegrityError.  Standard library only (no dependency on the research code)."""
import csv
import hashlib
import os
import sys

PKG = os.path.dirname(os.path.abspath(__file__))
LAB = os.path.abspath(os.path.join(PKG, "..", ".."))


class FrozenIntegrityError(RuntimeError):
    pass


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify(check_live=True, check_data=False, quiet=False):
    bad = []
    mf = os.path.join(PKG, "T61_R1C_MANIFEST.json"); ms = os.path.join(PKG, "T61_R1C_MANIFEST.sha256")
    if not (os.path.exists(mf) and os.path.exists(ms)):
        raise FrozenIntegrityError("manifest or manifest hash missing")
    if open(ms).read().split()[0] != sha(mf):
        bad.append("T61_R1C_MANIFEST.json")
    rows = list(csv.DictReader(open(os.path.join(PKG, "T61_R1C_HASH_INDEX.csv"))))
    if not rows:
        raise FrozenIntegrityError("empty hash index")
    n_live = 0
    for r in rows:
        if r["kind"] == "reference_only":                        # large canonical data: hash reference, checked on demand
            if check_data:
                p = os.path.join(LAB, r["live_path"])
                if not os.path.exists(p) or sha(p) != r["sha256"]:
                    bad.append(r["live_path"])
            continue
        fp = os.path.join(PKG, r["frozen_path"])
        if not os.path.exists(fp) or sha(fp) != r["sha256"]:
            bad.append(r["frozen_path"])
        if check_live and r["live_path"]:
            lp = os.path.join(LAB, r["live_path"])
            n_live += 1
            if not os.path.exists(lp) or sha(lp) != r["sha256"]:
                bad.append("LIVE:" + r["live_path"])
    if bad:
        raise FrozenIntegrityError("T61-R1C frozen package integrity FAILED (fail closed): " + ", ".join(bad))
    if not quiet:
        print(f"T61-R1C frozen package OK: {len(rows)} entries, {n_live} live files byte-identical")
    return True


if __name__ == "__main__":
    try:
        verify(check_data="--data" in sys.argv)
    except FrozenIntegrityError as e:
        print(e); sys.exit(2)
