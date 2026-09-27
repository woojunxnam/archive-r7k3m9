# T45_27 Hash index

Final status:

|                                       | 0                                                                                                                                                         |
|:--------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------------------|
| CASH_REFERENCE_CLOSE                  | 16:00:00 ET (close of the 1m bar end-stamped 16:00)                                                                                                       |
| LAST_ALLOWED_EXECUTION                | 16:15:00 ET                                                                                                                                               |
| LAST_CAUSAL_EXECUTION_BAR             | decision on bars end-stamped <= 16:14; fill at the OPEN of the bar end-stamped 16:15                                                                      |
| LOCKED_OVERNIGHT_INTERVAL             | 16:15-bar-open fill -> next RTH open print (open of bar end-stamped 09:31)                                                                                |
| RTH_EXECUTION_WINDOW_CONFIRMED        | YES (09:30-16:15 custom window; fills 09:31..16:15 bar opens; 16:15 bar exists on 98.6% of sessions; pre-2021-06 CME 16:15-16:30 halt makes 16:16 absent) |
| REFERENCE_RTH_CLOSE                   | 16:00 cash reference (not 16:15)                                                                                                                          |
| OVERNIGHT_PATH_FEATURES_USED          | NO                                                                                                                                                        |
| OVERNIGHT_HOLDING_ALLOWED             | YES                                                                                                                                                       |
| OVERNIGHT_TRADING_ALLOWED             | NO                                                                                                                                                        |
| GAP_LOCK_REBOUND_EDGE                 | NO                                                                                                                                                        |
| GAP_CASH_REBOUND_EDGE                 | NO                                                                                                                                                        |
| GAP_DOWN_REBOUND_EDGE                 | NO                                                                                                                                                        |
| OPENING_FLUSH_REBOUND_EDGE            | NO                                                                                                                                                        |
| GAP_PLUS_FLUSH_EDGE                   | NO                                                                                                                                                        |
| GAP_PLUS_FLUSH_ADDS_VALUE             | NO                                                                                                                                                        |
| EXTREME_GAP_CRASH_REGIME_DETECTED     | YES (ES gaps < -1.5 ATR and extreme gap + extreme flush continue lower; MNQ extreme buckets too small)                                                    |
| LATE_RTH_BUILD_ADDS_VALUE             | NO (unconditional); conditional on the Champion's own state: historically yes, but not promotable (T45_24)                                                |
| 16_00_TO_16_15_ADDS_VALUE             | NO (segment mean ES +$1.07 / MNQ +$2.07 per contract, t~1.6, below round-trip cost)                                                                       |
| 16_15_TO_09_30_PREMIUM_CONFIRMED      | NO as alpha (gross +$5.8 ES / +$11.7 MNQ per contract-night, t 1.5-1.8; negative matched-beta excess; 2022 strongly negative)                             |
| CLOSE_TO_OPEN_PREMIUM_CONFIRMED       | NO as alpha (beta premium, not significant)                                                                                                               |
| CONDITIONAL_CLOSE_BOOST_ADDS_VALUE    | NO (R3/R4/R5 failures; best is the Champion-state conditional carry -> shadow)                                                                            |
| OPEN_INVENTORY_MANAGER_ADDS_VALUE     | NO                                                                                                                                                        |
| ES_NQ_RELATIVE_STATE_ADDS_VALUE       | NO                                                                                                                                                        |
| OVERNIGHT_LOCK_1_CONTRACT_SAFE_ENOUGH | YES (1 MES worst -$1,170; 1 MNQ -$2,006; 1+1 -$3,176)                                                                                                     |
| OVERNIGHT_LOCK_2_CONTRACT_SAFE_ENOUGH | NO (2 MNQ worst -$4,011; 2+2 -$6,351 exceeds the -$3k worst-day gate alone)                                                                               |
| BEST_SIMPLE_MODEL                     | LOGISTIC (task A carry, rank-IC 0.064)                                                                                                                    |
| BEST_TREE_MODEL                       | XGBOOST (task A carry, rank-IC 0.029)                                                                                                                     |
| BEST_REGIME_MODEL                     | 3-state Gaussian HMM (causal): carry positive only in the calm state; no tradeable gain                                                                   |
| GENETIC_OUTER_FOLD_GENERALIZATION     | PARTIAL (4/5 outer folds > 0, median $14.2/day, large inner->outer degradation; combined ret/DD below Champion)                                           |
| GENETIC_RULE_RECURRENCE               | YES (Champion-state conditional carry: every outer fold, GA and GP)                                                                                       |
| GENETIC_PARAMETER_PLATEAU_PASS        | NO                                                                                                                                                        |
| GA_ADDS_VALUE_OVER_SIMPLE_RULES       | NO                                                                                                                                                        |
| GA_ADDS_VALUE_OVER_ML                 | NO                                                                                                                                                        |
| GP_ADDS_VALUE_OVER_GA                 | NO                                                                                                                                                        |
| GENETIC_PROGRAMMING_ADDS_VALUE        | NO                                                                                                                                                        |
| GENETIC_COMPLEXITY_JUSTIFIED          | NO                                                                                                                                                        |
| ML_ADDS_VALUE_OVER_SIMPLE_RULES       | NO                                                                                                                                                        |
| BEST_PRACTICAL_MAX_MES                | 1 (research); 0 adopted - no TEST45 overlay                                                                                                               |
| BEST_PRACTICAL_MAX_MNQ                | 1 (research); 0 adopted - no TEST45 overlay                                                                                                               |
| CHAMPION_HISTORICAL_AVG_DAY           | 52.59 (2019-05..2026-05-27; former holdout 58.73)                                                                                                         |
| BEST_TEST45_HISTORICAL_AVG_DAY        | no adopted overlay; best nested-OOS evidence Champion+GA stitched 62.86 vs Champion 52.51 on 2021-2026                                                    |
| INCREMENTAL_ALPHA_VS_CHAMPION         | 0 adopted (best nested-OOS +10.4/day at worse return/DD)                                                                                                  |
| BEST_TEST45_MAX_DD                    | n/a (NONE); Champion 6,193                                                                                                                                |
| FINAL_TEST45_CHALLENGER               | NONE                                                                                                                                                      |
| TEST45_PRE_OOS_FREEZE_SHA256          | 185d1ef91ddffe494ce5826a5142af31644a4816bb2a4db72d110909ed1c2987                                                                                          |
| TEST45_NEW_OOS_RULES_SHA256           | 76941f63465306928e535df74641a29b172c9420c9e0a69852a4f1b0ed5356da                                                                                          |
| TEST44_AUTHORITIES_UNCHANGED          | YES                                                                                                                                                       |
| NEW_OOS_DATA_ACQUIRED                 | NO                                                                                                                                                        |
| NEW_OOS_OPENED                        | NO                                                                                                                                                        |
| LIVE_AUTHORIZATION                    | NO                                                                                                                                                        |

102 files:

|     | file                                                                                | sha256                                                           |    bytes |
|----:|:------------------------------------------------------------------------------------|:-----------------------------------------------------------------|---------:|
|   0 | out/t45/T45_final_status.json                                                       | af4752c7e3adcf5c0ca16daee9c22092ab0e9b1923171fb135a6e72fcb0b6151 |     3633 |
|   1 | out/t45/baseline/T45_00_baseline_qa.json                                            | 402ebdc64896559515f4c7f5890053f7efbb3a9d83d9e3781106fa8dc98f5388 |     6117 |
|   2 | out/t45/baseline/T45_00_baseline_reproduction.csv                                   | d32ebbf8c13eb117779057a2e6494757aa234358bca26af9a67f6120da7e782a |     2039 |
|   3 | out/t45/baseline/champion_session_state.csv                                         | ca8e020d5ec35940c201d632c34e8d22f075ca61ddb0662ee36f559b4db9786e |   161031 |
|   4 | out/t45/baseline/daily_CHAMPION_CONTROL_V1.csv                                      | 1b237de95de4143bc7acc029a2372f7a952de03f891d9f28d59d432ca68d434b |   283322 |
|   5 | out/t45/baseline/daily_RIDGE_CHALLENGER.csv                                         | 9af2f016c281881dea9336e42b1f23923b87ab418af6f17ff0d50549417a7c88 |   244584 |
|   6 | out/t45/baseline/daily_SIMPLE_INTEGER_CHALLENGER.csv                                | 6e65acff5e262b093d211933e34e4004e15ed1ceb8221a2b25d1cc5231541ab6 |   279511 |
|   7 | out/t45/baseline/daily_XGBOOST_CHALLENGER.csv                                       | 50643dfcafe4d860188b0f93d9f9a36e4def0cccd21316e101c13139e5a3772c |   224050 |
|   8 | out/t45/det/T45_08_overlay_daily.parquet                                            | 94b34444c0292a551418fe687a93ce2d4feb92561c003b9fd391e77a455197e9 |   308199 |
|   9 | out/t45/det/T45_08_overlays.csv                                                     | a69474fdc476c090e0cb0b168f4d34d648de3ec871210d894f24e01d3ef36f9d |    38631 |
|  10 | out/t45/det/T45_08_overlays_by_period.csv                                           | 318d1da8e052b09bcb6f6a991de8f30a8861e5d3dde77ed3563e87e6bec86cc1 |   276116 |
|  11 | out/t45/det/T45_08_specs.json                                                       | aa66ad548be6eb5c18b37fc7eb7778bb92950d72a5347fb13d92116285e5fd59 |     9389 |
|  12 | out/t45/final/T45_13_ga_recurrence.csv                                              | 2b2988c3869fcebd9c67c2d8d8c751d2e59cc0cf8e65e44f6230f843a93dc778 |     3352 |
|  13 | out/t45/final/T45_13_ga_selected_behaviour_corr.csv                                 | 10c05770504e764eace88c07a72d7cf576565b2331b26b987f741ef4294bee80 |      735 |
|  14 | out/t45/final/T45_13_ga_selected_concepts.csv                                       | 645e14bfbf86023f61b9ca56c3b0077192e556c0f4c366992cca01bba8dc884f |      557 |
|  15 | out/t45/final/T45_13_nested_outer_folds.csv                                         | 755744f5a4ffc8b7e276a12f2c75d1ffe965d645afa3672707a5291ddb75ff61 |     6596 |
|  16 | out/t45/final/T45_14_ga_final_plateau.csv                                           | 269f36171049deec429ed77e50de5f427f5c673c0b695b896fd2e102985e6951 |     1672 |
|  17 | out/t45/final/T45_14_ga_fold_plateau.csv                                            | 098f39bf9bedba140fe18a6185125ec4ffbb21f08a080fcf73eebfd8b5c3c9df |      150 |
|  18 | out/t45/final/T45_19_20_combination_scaling.csv                                     | 4a722d999f87ef5cf96f6eb4c9660c26932999d344118a5ec3c796b1a0f77add |    72849 |
|  19 | out/t45/final/T45_19_module_combination.csv                                         | bb603d6857d87142098aea990d183ff4839155698ac6b3f1b74cf863fa3c50fb |     4647 |
|  20 | out/t45/final/T45_21_22_periods.csv                                                 | b801a15297ea6024338a6aaf3101c7bb182408774687e1e9880294ea60a08aff |    63807 |
|  21 | out/t45/final/T45_24_candidate_rule_audit.csv                                       | e4501aec3e5d9348c138aae8233fbfdab63ee9e53cbda43663caf3dabb41057f |    53736 |
|  22 | out/t45/final/T45_24_final_selection.json                                           | 3a176b63244ac8a1a7c3775f99b9245c8c531b624c270f2e6f4df264dceee3b5 |     2061 |
|  23 | out/t45/final/T45_ga_gp_final.json                                                  | e997ab862126fcb1e367d6ea3933c8adedaa7f1f97059499b771c14b0e25726c |     2454 |
|  24 | out/t45/final/T45_outer_block_comparison.csv                                        | 8f3d2652b7f44e2bead1576a384de64a1eb87f1aba423fff310fa7b104e86464 |    32325 |
|  25 | out/t45/final/T45_v6_state_carry_daily.parquet                                      | 1f9365daa8c964e51f882dfdc96e1db7c9ccdc2fa8cb784b5b77e46bbb1e1c7b |   695253 |
|  26 | out/t45/final/T45_v6_state_carry_family.csv                                         | 378ffe3261e4bd9bfba344dc0f51e95146b4b40e19cac25866efdd18cecfc6c0 |    57462 |
|  27 | out/t45/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.json                                 | 76941f63465306928e535df74641a29b172c9420c9e0a69852a4f1b0ed5356da |     2097 |
|  28 | out/t45/freeze/TEST45_NEW_OOS_ACCEPTANCE_RULES.sha256                               | ae31bcd97beed9d38cd62d64be748f9968678032692b03823fe88d4b8b116daf |      103 |
|  29 | out/t45/freeze/TEST45_PRE_OOS_FREEZE.json                                           | 185d1ef91ddffe494ce5826a5142af31644a4816bb2a4db72d110909ed1c2987 |     7244 |
|  30 | out/t45/freeze/TEST45_PRE_OOS_FREEZE.sha256                                         | bab33853e38b0339cef31ccd3f80fb7d095c11947e0269d5d7f62c9aed05690d |       93 |
|  31 | out/t45/ga/T45_12_ga_spec.json                                                      | 1a622e3e2e75dc905a70a861fb31851537466263f676920d9547d60f21c67462 |     2200 |
|  32 | out/t45/ga/T45_13_ga_archive.parquet                                                | 80a3a8b9fbce29842aba633f55d51f99f51d2bfe5d92eae19b973e5f748cefa5 | 25427077 |
|  33 | out/t45/ga/T45_13_ga_island_fronts.parquet                                          | cc8475ae6c144689278af60a02afd684e34fa8b91e1ed8dfee1cd2cf43d3c0c4 |   657034 |
|  34 | out/t45/ga/T45_13_ga_selected.csv                                                   | bbeea31c8640ba27f891b4855145631b83e7d3942198a5fc70cc0075c285931f |    28128 |
|  35 | out/t45/gp/T45_15_gp_archive.parquet                                                | c0332773eb79af5fb2ad7ada7557ee2cde38b7bee9cd1a225b1b6f49083d7692 | 18795370 |
|  36 | out/t45/gp/T45_15_gp_selected.csv                                                   | 60a949dbe7f07f5c541405d6bfb6a830af5c870ffcb19e41485a53e1cfdd8481 |    43876 |
|  37 | out/t45/gp/T45_15_gp_spec.json                                                      | 840922ab2608717f5c5a140ce4ec1eca773d47cd5c099005bd9e41f83f90fae5 |     1226 |
|  38 | out/t45/ml/T45_09_model_zoo_spec.json                                               | 293884c1f8930bfaea8990ca99881dc61d189d22051575b552e8d46b52612f3e |     2003 |
|  39 | out/t45/ml/T45_10_model_daily.parquet                                               | 3b7c6f3a943e230a6c79f76d027aeb222ca15cba9ac30b7b2069ab730ede1265 |   622432 |
|  40 | out/t45/ml/T45_10_model_walkforward.csv                                             | 1d3995c3ad2a3be49cf55af604f021674f1001292d188ad42c4e40266f7e9ca4 |    27873 |
|  41 | out/t45/ml/T45_10_regime_states.csv                                                 | 87e455e1c6e37cb478546b7e9e5eb5798f3b7b841c51de79142c11b9d3c58bd6 |     1459 |
|  42 | out/t45/ml/T45_11_model_ablation.csv                                                | f3001b122241da15bc7f26937d0945210c3b31aa57d0218bece8e24bb14d70d8 |    10001 |
|  43 | out/t45/ml/hmm_post.npy                                                             | c441273b2e98c43446e200a8011274676e9ef8ac9b89cad3098abf7143c664b1 |    42848 |
|  44 | out/t45/morning/T45_03_late_features.csv                                            | 1e12b2e2c6b3f3760947bb975b4b4272b31285a04c7a8fb9ee94d98afa103c06 |    24371 |
|  45 | out/t45/morning/T45_04_gap_buckets.csv                                              | 5795dad946dbacee9f0c68fcc9f34243d1019bd171d8a81f8797e2c580635b8e |    63958 |
|  46 | out/t45/morning/T45_05_flush.csv                                                    | de84d1870628b3d2e114d29657d4ab848f4463ffd23ec3c01c7bb5f691cc16c7 |    70739 |
|  47 | out/t45/morning/T45_06_matrix.csv                                                   | d24a768a31da39d9c7de568d5eb0fa5d345afc43922bc3d8bc79448e9d28c6a9 |     5337 |
|  48 | out/t45/morning/T45_07_inventory.csv                                                | a095cee379c7c02dd6b0f8de510282b623495c9f37efe09b9520d36fe82c086a |    16964 |
|  49 | out/t45/morning/T45_16_cross_index.csv                                              | 5c4a9f0cb069246d108f2a1c97a9a426feb9f6af8f0b0c65acd16d69da69afac |     1039 |
|  50 | out/t45/rerun.sh                                                                    | 004bac53a5eda19d11b78a17d7df20a44a2c9c304fe1b74984aab6ae3a071c5e |      594 |
|  51 | out/t45/session/T45_01_segments.csv                                                 | 03dad6f004a0e989069bce7c84302a8f06e3585dadfb6724eebdbde371394720 |     8875 |
|  52 | out/t45/session/T45_01_segments_by_year.csv                                         | 6f29c27719edc910e389b6505dd44c2b0d20fc82b948159496f2eef292681350 |    25542 |
|  53 | out/t45/session/T45_02_carry_by_period.csv                                          | 7ec1d7ce28f4994325ed39cd830acfcda878685e9406ecf2415b380a2a6ab3fc |    12071 |
|  54 | out/t45/session/T45_02_carry_controls.csv                                           | 9b0e46c4123823ddcc6c5283fe8e5e6530cb869bbf674bf88fe4a94a8e0c4868 |    13205 |
|  55 | out/t45/session/T45_17_lock_risk.csv                                                | 8521fa4ac5546cd2b3d852451c049a1d0ea0195e4fbb87a5d595fdfa19e955b0 |     4304 |
|  56 | out/t45/session/T45_17_worst_locks.csv                                              | 09f279257ecafa0e1c51a1f6f9eb4a6397a6dd3c691936fdec531fd3e5637151 |      884 |
|  57 | out/t45/session/T45_timestamp_qa.csv                                                | 36189344899303d757784cefc768f0d1590f4dd2e9db2f1fa769cfc23da02bf6 |     2736 |
|  58 | out/t45/session/lock_returns.npz                                                    | 52e1cfd88d06c8b7e2f7c49a4bd34377973f100ed4839ac16acc107c5a4df3c5 |    28976 |
|  59 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_00_AUTHORITY_AND_BASELINE_QA.md    | 78568a166a5dbcc6dc46a40970223647e33f8e0f967a5f716e04b759b222b3db |     4341 |
|  60 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_01_SESSION_RETURN_DECOMPOSITION.md | 808f4c9d53f36100e045de15e9915a409be5286f019fd06e2000a4d036248de6 |    24533 |
|  61 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_02_CLOSE_TO_OPEN_PREMIUM.md        | 0e08bc451fa631342deb4dba52d3884537a0154defd9db610f700b1ffac7fbfd |     8301 |
|  62 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_03_LATE_RTH_FEATURES.md            | b2043cf269d4c17fb971c30c0117acab7b191a4b4527c4af68619e74477c3f47 |     7744 |
|  63 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_04_GAP_DOWN_REBOUND.md             | e3f9045522e9c6314dc8e4966220e422ebfea300651f7d554309192e6c568c7d |    35708 |
|  64 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_05_OPENING_FLUSH_REBOUND.md        | 155d444a8daa1bcaf2ac35ede8577fc2e845c3f248bedc101a6559756eb1cae4 |    29753 |
|  65 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_06_GAP_FLUSH_MATRIX.md             | b1c121493cc1d4d5e3f3ca0fb2373fe9791a11373609c5e1fb22045f9fa073fc |     8146 |
|  66 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_07_OPEN_INVENTORY_MANAGEMENT.md    | 3ebd2ff7ac4b7416b7e428b052e7d7452c75c502315c518a98fdc412a8875e9d |    22587 |
|  67 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_08_DETERMINISTIC_OVERLAYS.md       | 945ce1cfef9bcaca7ca3682bdd3092e6f85a3d0d9544af98c0e3713b390fd41c |    18840 |
|  68 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_09_MODEL_ZOO_SPEC.md               | c6b20b39aba3045cbeadbe921846e58e2fbba71e6130c51aca8e1c7bcd9d5554 |     3191 |
|  69 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_10_MODEL_WALKFORWARD.md            | 4d0f75566b16dadded6d1d0ce76c15facfc659ed31e98f450b5fb8e89633ef22 |    17004 |
|  70 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_11_MODEL_ABLATION.md               | 83cd5351e9875b5023a079519b4ef887fa7883ae91607d2075acec4686209251 |    13333 |
|  71 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_12_GA_SPEC.md                      | 73ff68d79a4996ad76c60e8a1587329f58bf22378733fc57e755efacd9f5cbb1 |     5128 |
|  72 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_13_GA_PARETO_FRONTIER.md           | b65dc49b77fec3f1f3cd308bece69fe30f88e0b044d1d71830d3811948d6306d |    20216 |
|  73 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_14_GA_NEIGHBORHOOD_ROBUSTNESS.md   | b460776673c7ade9254fc6f3ab4a1890f7a35662420f5abba7f93d596b81d15d |     2390 |
|  74 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_15_GENETIC_PROGRAMMING.md          | 224ab46f844de0e15d7dd4a6a56d599c0faab6b5302dc84d42921dbeb82fc10c |     6731 |
|  75 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_16_ES_NQ_CROSS_INDEX.md            | 05c30d055542ba1e8b5359eb32f7e3e7b25be3196a44e83895a0fa3433944bfd |     1777 |
|  76 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_17_OVERNIGHT_LOCK_RISK.md          | d61816c2e73c6118e8a379b4b0c5d9fd6be5bfadf9adc3f0e5ed7487ec5e430a |     8474 |
|  77 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_18_INTEGER_EXECUTION.md            | 378b628a9d16984de39befb9011277669bd5919c8e101bf0e632adb692c6baeb |     3099 |
|  78 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_19_MODULE_COMBINATION.md           | 0854fc41cdb44e0d7844b33886d293f4afe9be0b7655d9cc7d4f36a42404d663 |     6151 |
|  79 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_20_SCALING_FRONTIER.md             | 7a2fc769110a79df6205e5fb2d4040d7dc697f1d19dc01119189b194f3acf65d |    24358 |
|  80 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_21_2020_2022_STRESS.md             | 8f7f4e4d121efa1136a7e21f4dc2fd8ed1ca4d396a355ffcae613c8e6a8e48e1 |    20529 |
|  81 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_22_FORMER_HOLDOUT_DIAGNOSTIC.md    | a902e9ae45f390d66118148ed726f841ea7e8c5f3001978739de68137319c89f |    13988 |
|  82 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_23_COMPLEXITY_LADDER.md            | 3578c0f5d72c723a92dacdda025037199b135d4a525a026048d1a2ff937801e8 |     1906 |
|  83 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_24_FINAL_TEST45_CANDIDATE.md       | abd32601a30a14a5020d6314cd4955d44e84c1a82e4d0faec0765afc0815fafe |    16890 |
|  84 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_25_PRE_OOS_FREEZE.md               | 7f4b3558f1e339e447704fe2af0f592a2dcf312b846816d233e6c7befa42b5b3 |     7404 |
|  85 | reports/TEST45_ES_NQ_SESSION_ALPHA_EVOLUTION/T45_26_NEW_OOS_ACCEPTANCE_RULES.md     | 339d68599b00184c14ffab1a611baf3399f2885278537d23ab8c3c2db05e4983 |     2277 |
|  86 | src/t45_00_baseline.py                                                              | ea542759d5f05845ce7d0542b88503c89cdbfa1f729669280d0607812615b17f |     6398 |
|  87 | src/t45_01_session.py                                                               | 18f7d57fd234a3039b397f8c5fee4d7b052389244eaafabc99a2b769e3bfeb8c |    10966 |
|  88 | src/t45_02_morning.py                                                               | a94088a35c57c7dc9ca03bf25d7ac87e825ca9035a6b51097f7f93263fbd4fd6 |    16877 |
|  89 | src/t45_03_det.py                                                                   | e670edd1f190299644d1f4287b1854365e59034f5537d8b003f26be51e62dd73 |     4272 |
|  90 | src/t45_04_ml.py                                                                    | 2b96c2a474d96d0b4e6144f249e5e726d9fdcf6aa4a2af7903feee7ae225bc75 |    15143 |
|  91 | src/t45_05_ga.py                                                                    | ade4f88bf44f47b70a8003d4dcf3d22a0e4df3d9b4280d6980f26757f7472347 |    15455 |
|  92 | src/t45_06_gp.py                                                                    | 23bbf7b081b77e799138d6ac46461759cc47047229a4275a167a15c4bde564ef |    14742 |
|  93 | src/t45_07_eval.py                                                                  | af19f98fe55c774acaa7301bb7491abdae662fb9df4b2c1307d9c61ce29d133e |    19086 |
|  94 | src/t45_08_v6carry.py                                                               | b03e47761d52cb6c53465d60a57fbbb4ed7fcb115fe1832a4c674e4273f3ad04 |     3355 |
|  95 | src/t45_09_select.py                                                                | d240c5986b0d0fbca7b454d1d6531b935cbe9634fbe7b2b6f6a5918167723571 |     6263 |
|  96 | src/t45_10_freeze.py                                                                | cb13731fab0c8f63ed935e942581a8686e587ae6348542cc34eb989b788170a5 |    10142 |
|  97 | src/t45_common.py                                                                   | 61121549fe3d5f921b73d9ea96bb9532e64b1a1816de125a5745000fa6152a77 |    11254 |
|  98 | src/t45_feat.py                                                                     | 28392cb9d0f7bbb15f3fafb985ab93d89a82337623412c7e08acef2de11ff86c |     3578 |
|  99 | src/t45_overlay.py                                                                  | b98093a8724a86d85596f5a919942c2af90588a7bc59fb224b3ec2cc431eb0a8 |    10849 |
| 100 | src/t45_report.py                                                                   | 914c0cf1fbec2363642a7b91f8e8783fb7114b46a1ac92ef13ed446e07197ab6 |    30986 |
| 101 | src/t45_sim.py                                                                      | d878ffe22b04ca39f35bd53a6098c5b0f8e000debaebf31ed88e9e5d233a9f23 |     7731 |

