"""TEST84+ CAUSAL VOLUME-PROFILE / AUCTION-VALUE LAB + MOMENTUM-FOLLOW LANE + PRESS-WINNER LANE - program preregistration.
Written before any profile / momentum / pyramiding economics."""
import datetime
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import t45_common as C45  # noqa: E402

AP = os.path.join(os.path.abspath(C45.ROOT), "out", "AUCTION_PROFILE_LAB")

SPEC = {
    "program": "TEST84+ AUCTION-PROFILE / MOMENTUM-FOLLOW / PRESS-WINNER", "research_data_end": "2026-05-27", "T61": "frozen; no forward OOS",
    "closed_not_reopened": ["box-bottom mean reversion", "box-top momentum", "SEQ2 rescue", "near-zero-velocity box subgroup", "generic rebound / bottom families"],
    "DATA_LIMITATIONS": {
        "volume_at_price": "NOT available: 1m OHLCV only -> every profile is an APPROXIMATION built by an explicit allocation proxy",
        "signal_execution_parity": "ES signal = full ES contract volume -> MES execution (parity OK). Nasdaq: canonical full NQ volume is NOT in the "
                                   "research data set; the NQ signal uses MNQ volume as a documented proxy (micro-contract participation; thin in 2019) "
                                   "-> MNQ execution. Any NQ profile result carries flag NQ_VOLUME_PROXY=MNQ.",
        "prices": "back-adjusted continuous series (profiles are relative within / across adjacent sessions on one adjustment basis)"},
    "clock": "decision grid = closes of completed 5m RTH bars (09:40 .. 15:55, grid j = 5b+4); entry = next 1m open (j+1); exits FPb; 1 contract; "
             "costs 0.62 + 1 tick per side, SLIP4 = 4 ticks; one event per (type, session) = first occurrence",
    "profiles": {"proxies": {"VP-A": "whole 1m volume at typical price (H+L+C)/3", "VP-B": "uniform over the bins spanned by L..H",
                             "VP-C": "triangular over L..H peaking at the typical price"},
                 "bins": "width = f x prior-session ATR_d, f base 0.02 (neighbours 0.015, 0.03); absolute bin grid",
                 "types": {"P1": "prior completed RTH", "P2": "developing RTH (completed bars only)", "P3": "rolling 30m", "P4": "rolling 60m",
                           "P5": "rolling 120m", "P6": "prior 2 completed RTH"},
                 "value_area": "70% (neighbours 65 / 75), grown from POC by the larger adjacent bin; POC ties -> bin nearest the profile median",
                 "nodes": "on P1 smoothed (3-bin mean): HVN = local max >= 1.5 x median non-zero bin; LVN = local min <= 0.5 x median lying between two HVNs",
                 "relative_volume": "last-30m volume / median of the same 30m window over the previous 20 sessions (causal)"},
    "PROFILE_EVENTS (TEST85)": {
        "PA1_POC_UP": "P4 POC now - P4 POC 30 min earlier >= 0.05 ATR_d (neighbours 0.03 / 0.08)",
        "PA2_VALUE_UP_ALL": "P4 POC, VAH and VAL all higher than 30 min earlier",
        "PB1_VAH_POKE": "first 5m bar whose high > P1 VAH", "PB2_VAH_CLOSE": "first 5m close > P1 VAH", "PB3_VAH_TWO": "two consecutive 5m closes > P1 VAH",
        "PB4_VAH_ACCEPT": "5m close > P1 VAH AND >= 30% of P2 volume above P1 VAH (neighbours 20% / 40%)",
        "PC1_DPOC_UP": "P2 POC - P2 POC 30 min earlier >= 0.05 ATR_d", "PC2_DPOC_MULTI": ">= 2 upward and 0 downward P2 POC shifts across the last 60 min (5m samples)",
        "PD_HVN_LVN_TRAVEL": "close leaves the upper edge of a P1 HVN into the LVN corridor below the next higher P1 HVN; target = next HVN lower edge "
                             "(report travel probability, time, MFE, MAE, target-exit vs time-hold)",
        "PE_LVN_BREAK": "close crosses above a P1 LVN centre having been below it within 15 min, 15m move >= 0.10 ATR_d (control D = ordinary breakout)",
        "PF_RISING_POC_PULLBACK": "PC1 true within the last 30 min AND P4 VAL up; 5m low <= P2 VAH and close >= P2 POC after a higher session high",
        "PG_UP_STACK": "P2 VAL > P1 VAH (first time after 10:30); diagnostic classes at 12:00: UP_STACK / OVERLAP / DOWN_STACK",
        "PH_VALUE_COMPRESS_EXPAND": "P4 VA width 30 min earlier < 0.10 ATR_d (neighbours 0.08 / 0.12) AND P4 POC up >= 0.05 ATR_d since; "
                                    "PH_PRICE_NULL: same with P4 high-low range < 0.20 ATR_d and range midpoint up",
        "PI_PRICE_POC_CONFIRM": "new session-high close after 10:30 AND P2 POC up >= 0.05 ATR_d over 30 min; PI_DIVERGE: new high without POC up",
        "PJ_VOLUME_MOMENT_LEAD": "P4 volume-weighted median up >= 0.05 ATR_d over 30 min while close <= prior 60m high (value before breakout)"},
    "MOMENTUM_EVENTS (TEST85M)": {
        "M1_OPEN_IMPULSE": "at 10:00: return since open >= 0.30 ATR_d (neighbours 0.20 / 0.40)",
        "M2_QUALITY_HI / M2_QUALITY_LO": "M1 with path efficiency since open >= 0.5 / < 0.5",
        "M3_PERSIST / M3_ONE_TIME": "at 11:30: return since open >= 0.30 ATR_d and share of 1m closes above session VWAP since 10:00 >= 0.8 / < 0.5",
        "M5_SECOND_IMPULSE": "impulse (15m return >= 0.25 ATR_d) -> pause >= 10 min without new high, pullback <= 50% of impulse -> new session-high close",
        "M6_FAILED_PULLBACK": "session return >= 0.40 ATR_d and above VWAP; pullback >= 0.15 ATR_d from the session high staying above VWAP; resumption "
                              "close >= pullback low + 50% of the pullback",
        "M7_MTF_{5,5_15,5_60,5_15_60}": "first 5m decision after 10:30 with positive 5m / 15m / 60m returns (subsets as named)",
        "M8_AGREE / M8_DIVERGE": "M1 with the other index also >= 0.30 of its ATR_d since open / not",
        "M9_PRICE_VALUE / M9_PRICE_ONLY": "M3_PERSIST with / without P2 POC up >= 0.05 ATR_d over the last 60 min (control 5 = price only)",
        "M10_VALUE_FOLLOWS / M10_VALUE_LAGS": "at 11:30 session up >= 0.30 ATR_d with P2 POC above its 10:30 value / not",
        "M68_ACCEL / M68_DECEL": "at 11:00: 10:00-11:00 return > 09:30-10:00 return > 0 / 0 < second-hour return < first-hour return",
        "M4_DECAY_EXIT (diagnostic)": "for M3_PERSIST: exit at the first close below session VWAP vs hold to 16:15"},
    "horizons": ["+15m", "+30m", "+60m", "+120m", "11:00*", "13:00*", "16:00", "16:15", "next open"],
    "controls": {"A_MATCHED": "instrument x year x vol tercile x HTF bull, same entry / exit minute",
                 "B_MOMENTUM (primary)": "A + session-return bucket at the decision minute (-inf,-0.5,-0.2,0,0.2,0.5,inf) ATR_d",
                 "C_VOLUME": "A + relative-volume tercile at the decision minute (no profile location)",
                 "D_SHORT_MOMENTUM": "A + last-15m return bucket (-inf,-0.1,-0.03,0.03,0.1,inf) ATR_d (ordinary breakout of similar magnitude)"},
    "qualification": {"profile": "net > 0, SLIP4 net > 0, B excess > 0 overall and >= 4/5 folds, C > 0, D > 0, A > 0, n >= 300, min fold n >= 40, "
                                 "B excess > 0 under >= 2 of 3 proxies (base bins / VA)",
                      "momentum": "net > 0, SLIP4 > 0, B excess > 0 overall and >= 4/5 folds, D > 0, A > 0, n >= 300, min fold n >= 40",
                      "horizon": "structural: 30m, 60m, 16:00, 16:15 (next open only if an RTH horizon qualifies)"},
    "strategies TEST86-90": "only for qualifying mechanisms; 1 contract, first event per session, next-open fill, hold the qualifying horizon; entry-speed "
                            "variants: immediate / one 5m-bar acceptance / one retest where logical",
    "plateau": {"value_area": [65, 75], "bin_f": [0.015, 0.03], "acceptance_fraction": [0.20, 0.40], "poc_threshold": [0.03, 0.08],
                "impulse_threshold": [0.20, 0.40], "hold": "adjacent structural horizon", "proxy": "the other two proxies",
                "definition": "all neighbours net > 0 and >= 60% of base, B excess > 0 in >= 75% of neighbours"},
    "gate": ["B excess > 0", "matched A excess > 0", ">= 4/5 folds net > 0", "remove-top3 > 0", "SLIP4 > 0", "+1 bar delay > 0", "20% missed > 0",
             "max year share <= 50%", "plateau PASS", ">= 300 trades, >= 40 per fold", "profile: >= 2/3 proxies"],
    "T61_additive": "TEST65 incremental gate on T61-R1C + module (residual capacity only: MNQ 6 - T61, MES 8 - T61, never trims T61) AND "
                    "MINIMUM MEANINGFUL INCREMENT: incremental >= +10 $/day (2019-07+ and 2021+) AND combined ret/DD >= T61 ret/DD",
    "PRESS_WINNER (TEST94 lane)": {
        "base": "the best QUALIFYING momentum mechanism (fold-median B excess at its horizon); if none qualifies the lane runs as a NON-PROMOTABLE "
                "DIAGNOSTIC on M1_OPEN_IMPULSE (declared now) to measure marginal add EV only",
        "state_machine": "FLAT -> PROBE (1 unit) -> WINNER_1 .. MAX_PRESS -> DECAY -> EXIT",
        "add_rule": "ALL of: campaign unrealised P&L > 0; close > session VWAP; a NEW trigger event; spacing and speed satisfied; units < ladder max",
        "add_triggers": {"A_NEW_HIGH": "new campaign-high close", "B_SECOND_IMPULSE": "M5-type second impulse after the last add",
                         "C_SHALLOW_PULLBACK": "pullback >= 0.10 ATR_d from the campaign high, low above the last add price, resumption close > pullback low + 50%",
                         "D_VALUE_ACCEPT": "A_NEW_HIGH AND P2 POC up >= 0.05 ATR_d over 30 min", "E_CROSS_INDEX": "A_NEW_HIGH AND other index at a new session high"},
        "ladders": {"L1": [1, 2, 3], "L2": [1, 2, 3, 4], "L3": [1, 2, 4, 6], "L4": [1, 2, 3, 4, 6]},
        "speed": {"FAST": "next trigger", "MEDIUM": ">= 5 min", "SLOW": ">= 15 min"}, "spacing_ATR": [0.0, 0.10, 0.25],
        "exit": {"R0": "full exit at the first close below session VWAP or 16:15", "R1": "reduce to 1 unit at the first close below VWAP; full exit on a "
                 "close below the initial entry price or 16:15"},
        "no_loser_adding": "hard constraint, audited (violations must be 0)",
        "overnight": "RTH first; overnight carry policies (full / half / base unit / flat) ONLY if the RTH press passes",
        "controls": {"FRONTLOAD": "same average units, all bought at the probe entry, same exit", "CONSTANT": "1 and 2 units throughout"},
        "marginal": "per-unit ledger: ADD_k P&L from its fill to its exit minus costs; MARGINAL_ADD_EV per add level",
        "max_units": 6},
    "ML_GA": "ML only if a deterministic mechanism qualifies (economic targets, feature-availability audit + prefix invariance first); GA only if "
             "deterministic economics survive and ML / parameter exploration is justified",
    "prefix_invariance": "TEST84: every profile feature at T recomputed with data after T removed must be identical (fail closed)",
    "stopping": "A survivor frozen / B distinct mechanisms fail matched-momentum economics / C profile alpha explained by momentum, volume level or proxy",
    "budget_priority": "momentum ~50%, profile ~35%, integrated ~15%; no bottom research",
    "prior_budget": {"hypotheses": 1702, "ml_configs": 207, "genomes": 777629},
}

if __name__ == "__main__":
    d = os.path.join(AP, "TEST84"); os.makedirs(d, exist_ok=True)
    p = os.path.join(d, "TEST84_PLUS_PREREGISTRATION.json")
    if os.path.exists(p):
        raise SystemExit("exists")
    json.dump({"written_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), **SPEC}, open(p, "w"), indent=1)
    h = hashlib.sha256(open(p, "rb").read()).hexdigest(); open(p + ".sha256", "w").write(h + "\n"); print(h)
