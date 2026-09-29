# Validation Checklist

A dashboard integration is NOT complete until every applicable item is green.

## Source
- [ ] Research source commit 42b8f8a1099152e86c5f424a81b6d79bb3843199 is available.
- [ ] verify_handoff.py passes.
- [ ] frozen/t61_r1c verifier passes.
- [ ] fixed_clue_basket_v1 hash index is unchanged.

## Time/data
- [ ] America/New_York session semantics confirmed.
- [ ] 1m bars treated with correct END-stamped convention.
- [ ] Signal->next-open execution verified.
- [ ] No future bar is used by C2 signal logic.
- [ ] Research cutoff 2026-05-27 is never crossed for retuning.

## T61
- [ ] Forward-shadow runner reproduces target fields.
- [ ] MNQ target <= 6.
- [ ] Overnight state is preserved.
- [ ] C43 governor and TEST53 governor states displayed.

## Basket
- [ ] Frozen member generators/models used.
- [ ] T61 priority enforced.
- [ ] MNQ total <= 6.
- [ ] MES total <= 8.
- [ ] Historical frozen ledger parity documented.

## C2
- [ ] P2_FAILED_FIRST detector parity established.
- [ ] ES->MES, NQ->MNQ, YM->MYM, RTY->M2K.
- [ ] Base = 1 micro.
- [ ] Exit = 16:15.
- [ ] No overnight C2.
- [ ] No stop/early exit added.

## Winner ADD1
- [ ] first eligible winner only.
- [ ] close > parent entry.
- [ ] >=30 min remain.
- [ ] independent-event bars C3/C5/C6/C7/C8 excluded.
- [ ] next-open fill.
- [ ] one extra micro only.
- [ ] no ADD2.

## Capacity
- [ ] Historical future-interval precheck is NOT used live.
- [ ] Causal live capacity policy preregistered.
- [ ] Causal replay completed.
- [ ] Metric delta vs research V2 reported.
- [ ] MAIN_GROWTH_V1 priority preserved.

## Dashboard safety
- [ ] READ_ONLY_SHADOW default.
- [ ] data stale state fails closed.
- [ ] source integrity fail blocks targets.
- [ ] causal allocator validation flag visible.
- [ ] broker execution remains disabled unless separately authorized.
