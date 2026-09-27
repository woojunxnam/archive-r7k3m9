# T45_18 Integer execution

All modules -> one desired MES and one desired MNQ state -> frozen lock governor -> one integer target per symbol (0/1/2; 3 only as a scaling diagnostic). No module sends its own order. The overlay is a separate virtual sleeve. Broker net target = Champion target + overlay target.

Execution clock (frozen):

|                           | 0                                                                                                                                                                                                    |
|:--------------------------|:-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| CASH_REFERENCE_CLOSE      | 16:00:00 ET = close of the 1m bar end-stamped 16:00                                                                                                                                                  |
| LAST_ALLOWED_EXECUTION    | 16:15:00 ET                                                                                                                                                                                          |
| LAST_CAUSAL_EXECUTION_BAR | decision on bars end-stamped <= 16:14, fill at the OPEN of the 1m bar end-stamped 16:15 (first trade after 16:14:00)                                                                                 |
| LOCKED_OVERNIGHT_INTERVAL | from the 16:15-bar-open fill to the next RTH open (open of the 1m bar end-stamped 09:31); no strategy order in between                                                                               |
| NEXT_EXECUTABLE_OPEN      | 09:30 ET; a pre-planned exit fills at the RTH open print; any decision using the open fills at the open of the bar end-stamped 09:32                                                                 |
| generic_rule              | decision at minute T uses bars end-stamped <= T; fill at the open of bar T+1 +/- 1 tick; entries never use an earlier price; if the bar is missing, the entry is skipped (forward fallback <= 3 min) |
| early_close_sessions      | entries whose bar does not exist are skipped; reductions may fill at the last existing bar                                                                                                           |
| overnight_path_features   | NONE                                                                                                                                                                                                 |
| overnight_trading         | NONE (position locked)                                                                                                                                                                               |

Fill fallbacks: entries use forward fills <= 3 min and are otherwise skipped. Reductions may use <= 15 min, or the last bar on an early close. A position carried into a contract-switch session pays a 2-side roll during RTH before the lock.

