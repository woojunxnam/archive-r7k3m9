"""Static Pine v6 source guard (parser-safety rules from the TEST43 program).

Checks
  1. no physical line ends with a binary operator: and, or, ==, !=, <=, >=, <, >
     (also flags trailing + - * / ? : , which are legal but risky - reported as WARN)
  2. balanced (), [], {} over the whole file, ignoring strings and // comments
  3. no two statements joined on one line (heuristic: ':=' or '=' declaration after a
     closing ')' followed by an identifier on the same line outside strings)
  4. //@version=6 present, no lookahead_on, no barmerge.lookahead_on, request.security count
Usage:  python -m t43.pine_guard FILE.pine
"""
from __future__ import annotations

import re
import sys

BIN_END = re.compile(r"(?:\band|\bor|==|!=|<=|>=|<|(?<!=)>)\s*$")
RISKY_END = re.compile(r"(?:[+\-*/?]|(?<![:=]):)\s*$")
JOINED = re.compile(r"\)\s+[A-Za-z_][A-Za-z0-9_]*\s*(?::=|=[^=])")


def strip_line(line: str) -> str:
    out = []
    in_s = None
    i = 0
    while i < len(line):
        ch = line[i]
        if in_s:
            if ch == "\\":
                i += 2
                continue
            if ch == in_s:
                in_s = None
            i += 1
            continue
        if ch in ("\"", "'"):
            in_s = ch
            out.append("S")
            i += 1
            continue
        if line.startswith("//", i):
            break
        out.append(ch)
        i += 1
    return "".join(out)


def check(src: str) -> dict:
    errors, warns = [], []
    depth = {"(": 0, "[": 0, "{": 0}
    pairs = {")": "(", "]": "[", "}": "{"}
    lines = src.splitlines()
    for n, raw in enumerate(lines, 1):
        s = strip_line(raw).rstrip()
        if not s.strip():
            continue
        if BIN_END.search(s):
            errors.append(f"L{n}: line ends with binary operator: {raw.strip()[:80]}")
        elif RISKY_END.search(s) and not s.strip().startswith("//"):
            warns.append(f"L{n}: line ends with '{s.strip()[-1]}': {raw.strip()[:80]}")
        if JOINED.search(s) and not re.match(r"^\s*(if|else|for|while|switch)\b", s):
            if "=>" not in s and "?" not in s:
                warns.append(f"L{n}: possible joined statements: {raw.strip()[:80]}")
        for ch in s:
            if ch in depth:
                depth[ch] += 1
            elif ch in pairs:
                depth[pairs[ch]] -= 1
                if depth[pairs[ch]] < 0:
                    errors.append(f"L{n}: unmatched '{ch}'")
                    depth[pairs[ch]] = 0
    for k, v in depth.items():
        if v != 0:
            errors.append(f"unbalanced '{k}' (depth {v} at EOF)")
    if "//@version=6" not in src:
        errors.append("missing //@version=6")
    if re.search(r"lookahead\s*=\s*barmerge\.lookahead_on", src):
        errors.append("lookahead_on used")
    n_sec = len(re.findall(r"request\.security\s*\(", src))
    return {"errors": errors, "warnings": warns, "request_security_calls": n_sec,
            "lines": len(lines), "status": "PASS" if not errors else "FAIL"}


if __name__ == "__main__":
    r = check(open(sys.argv[1], encoding="utf-8").read())
    for e in r["errors"]:
        print("ERROR", e)
    for w in r["warnings"][:50]:
        print("WARN ", w)
    print(r["status"], "lines", r["lines"], "request.security", r["request_security_calls"],
          "errors", len(r["errors"]), "warnings", len(r["warnings"]))
    sys.exit(0 if r["status"] == "PASS" else 1)
