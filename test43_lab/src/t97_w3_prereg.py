"""TEST97 Wave-3 preregistration (final wave of this program; after Wave-1/2 and FT2 Phase 3/4, before Wave-3 economics)."""
import datetime, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E
SPEC = {"state": "Wave 2: persistence = magnitude except FT2 (breakout + STRONG follow-through), whose strategy failed sample / plateau; compression "
                 "adds nothing intraday (M03) -> intraday NR / VCP / multi-bar contraction are SATURATED near neighbours; Donchian = M02 scale family "
                 "(done); Darvas / box = TEST70-78 (saturated); Livermore pivot = TEST95 L2 (failed)",
        "W3_V1_WILLIAMS_VOL_BREAKOUT [FRESH]": "level = session open + k x prior-day RTH range, k in 0 / .1 / .2 / .3 / .5 / .75; event = first completed 5m close "
                                                "above the level (09:35..15:00); response curve over k; family null: the same close above the open (k = 0) "
                                                "population at the same minute distribution (does range scaling add information?)",
        "W3_V2_CRABEL_DAILY_NR_ORB [NEW framing of M08]": "M08 close-confirmed ORB (15 min) split by PRIOR-DAY state: NR4 / NR7 (prior RTH range lowest of 4 / "
                                                           "7) / inside day vs none; incremental = NR minus non-NR excess (null A)",
        "W3_V3_RASCHKE_FIRST_PULLBACK": "thrust = close > prior 60-bar high (new momentum high); FIRST later bar whose low touches EMA20 or VWAP the same "
                                        "session, then first bullish close above the prior bar high -> entry; compare vs chase entry at the thrust "
                                        "(same sessions) and null A / B1",
        "edge_rule": "unchanged; primary null A plus family null", "strategy": "only an EVENT_EDGE family proceeds (Phase 3 / portfolio gate)",
        "stop_rule": "TEST97 closes after Wave 3 unless a survivor appears; the Tom / Livermore / momentum thesis universe is not declared exhausted"}
if __name__ == "__main__":
    p = os.path.join(E.OUT, "TEST97_WAVE3_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
