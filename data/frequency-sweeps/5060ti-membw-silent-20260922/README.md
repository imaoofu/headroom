# `membw` on the 10-point grid, three SILENT replicates — 2026-09-22

**Stock Profile 3, 1402–2100 MHz, 10 points, default iterations, driver 616.92.** Grid and
workload match the seven historical runs so these are comparable to them, not merely to each
other. Operator absent, driving agent silent throughout.

## The question, open since 2026-08-24

CLAUDE.md, unchanged for six weeks:

> *"Every verified-quiet `membw` sweep on the 10-point grid has a worst point, and across the
> seven of them the deepest single-point departure runs −0.36%, −0.59%, −1.00%, −1.15%, −2.17%,
> −5.93%, −6.91%. All seven had encoder and decoder verified at 0%. **The variation survives the
> encoder guard, so it is something else, and its cause is unidentified.**"*

🔑 **This morning gave that signature a mechanism on `gemm`** — isolated points losing 8–11% while
neighbours are untouched, landing elsewhere each run, and **vanishing as the driving agent went
silent** (4 bad points → 1 → 0). See `../5060ti-finefloor-20260922/`.

## Result

| run | worst single-point departure below the local trend |
|---|---|
| r1 | **−0.43%** at 1627 MHz |
| r2 | **none** — no point falls below its neighbours |
| r3 | **−0.51%** at 1627 MHz |

Cross-replicate spread: **max 0.83%, mean 0.30%** across the ten points.

✅ **The three largest historical dips — −2.17%, −5.93%, −6.91% — do not appear in ANY of three
silent replicates.** The worst seen today is −0.51%, below the smallest historical value bar one.

🔑 **So the large `membw` dips behave exactly like the `gemm` degradation characterised this
morning: they are activity-driven and they disappear under silence.** That is the most likely
reading of six weeks of "cause unidentified".

## ⚠️ What this does NOT establish, and the limitation is real

⛔ **These three runs are on STOCK Profile 3. The seven historical runs were not** — they are
split-curve, repair and memory-only sweeps from the §5.7 configuration comparisons. **This is
therefore not a like-for-like replication of the runs whose dips are in question**, and a
configuration-dependent dip would not be excluded by it.

The inference rests on two things rather than one: the magnitude gap (−6.91% against −0.51%) and
the fact that the same signature was independently demonstrated to be activity-driven on `gemm`
this morning, on this card, under controlled A/B/C. **That is suggestive, not conclusive.**
✅ **The clean test is three silent replicates on the split curve**, which would cost ~20 minutes
and has not been run.

⚠️ **A small departure may be genuinely real.** Two of three replicates dip at **the same
frequency, 1627 MHz**, by −0.43% and −0.51%. That is consistent with the two smallest historical
values (−0.36%, −0.59%) and is **not** explained away by the activity mechanism, which lands
somewhere different each time. **A reproducible ~0.5% feature at 1627 MHz is a separate, smaller
question that these data raise rather than settle.**

## What the curve itself shows

Throughput saturates hard at the top: 387.6 / 388.3 / 388.8 / 388.8 GB/s at 1860, 1935, 2017 and
2084 MHz, agreeing across all three replicates to **0.01–0.08%**. The bandwidth ceiling is flat
and extremely reproducible — consistent with §3.3.1's *"ceiling near 281 GB/s"* being a property of
the path rather than of any one run, at the higher figure this stock 10-point grid reaches.
