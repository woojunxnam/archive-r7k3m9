"""TEST97 Wave-2 preregistration (after Wave-1 clue analysis, before Wave-2 economics)."""
import datetime, hashlib, json, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import t97_engine as E
SPEC = {"motivation": "reports/TEST97_PLUS/T97_W1_FAILURE_CLUE_ANALYSIS.md - persistence clue; must beat a MULTI-BAR magnitude null",
        "NULL_Bk": "mean forward return of non-event bars in cell (year x 6 time buckets x decile of k-bar cumulative displacement (c[b]-c[b-k])/ATR_d x "
                   "tercile of k-bar high-low range / ATR_d), k = length of the event structure",
        "W2_P1_PERSISTENCE_LADDER": "run length L(b) = consecutive bars ending at b that are bull, close in upper half, higher low; events at L = 1..5 exactly; "
                                    "primary null Bk with k = L; response curve over L",
        "W2_P2_FOLLOWTHROUGH_GRADIENT": "N=12 breakout bar b followed by bar b+1 in strength tiers (bear / weak bull / bull body>=.5 / STRONG); entry after b+1; "
                                        "null Bk with k = 2 (two-bar displacement)",
        "W2_P3_SHALLOW_SECOND_LEG": "impulse = any STRONG bar (breakout not required) -> 1-6 bar pullback -> resumption (Wave-1 M05 logic); depth tiers "
                                    "<38.2 / 38.2-61.8 / >61.8%; null Bk with k = bars from impulse to resumption",
        "W2_P4_TOD_MAP": "P1 / P2 by time bucket (descriptive)",
        "edge_rule": "unchanged (Wave-1 EVENT_EDGE) but evaluated against NULL_Bk as primary",
        "strategy_stage": "only a family with EVENT_EDGE vs Bk and a coherent response proceeds to Phase 3 (fixed-horizon next-open strategy, costs, SLIP4, "
                          "delay, missed entries, walk-forward, portfolio gate vs MAIN) and Phase 4 (single / blind DCA / recovery / pyramid on the same events)",
        "stop_rule": "if no family beats NULL_Bk, the persistence clue is declared MAGNITUDE (beta-of-move) and the momentum-burst branch is closed for TEST97"}
if __name__ == "__main__":
    p = os.path.join(E.OUT, "TEST97_WAVE2_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
