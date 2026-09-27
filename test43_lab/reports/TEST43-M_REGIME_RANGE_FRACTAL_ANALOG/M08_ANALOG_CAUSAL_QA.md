# M08 Analog causal QA

TEST43-M — REGIME + NESTED RANGE + HISTORICAL ANALOG MECHANISM LAB. HOLDOUT_OPENED = NO.


* Library strictly before the query block in every block of every run: True
  (`M08_analog_library_meta__*.csv`, 6 runs).
* Dependence control: mean raw neighbours = k, mean independent sessions ~0.95k (k=50) (see M09 tables).
* Real-data prefix invariance of the range/state features used by the analog:
| inst | dev_bars | feature_cols_checked | feature_cols_mismatch | dev_events | val_build_dev_events | events_identical |
|---|---|---|---|---|---|---|
| ES | 664407 | 105 | 0 | 917621 | 917621 | True |
| MNQ | 663074 | 105 | 0 | 921631 | 921631 | True |
* **Rejected metric (look-ahead artefact):** a within-session (session-demeaned) IC produced 0.18 for STATE_ONLY;
  diagnosed as leakage (session mean uses the rest of the session; raw pos_rth alone scores -0.30). Removed. Likewise the
  session-paired tercile spread. Only pooled, control-residual IC is used.
* Standardisation constants from the first 250 sessions only; outcome labels are never features.

