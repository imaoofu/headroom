# DRAFT ONLY: RTX 5060 Ti NVML offset ladder (worklist 4o)

⛔ **SUPERSEDED 2026-09-22 by the live registration, `docs/REGISTERED-PREDICTIONS.md` §7, which
runs 0 / −150 / −300 / 0.** The −450 rung below was dropped. Kept as the record of what was
proposed and why it changed; score against §7, not against this file.

Written 2026-09-22 **before any 4o data**. This file is a proposal for review. It is not part of
`docs/REGISTERED-PREDICTIONS.md` and does not register an experiment until accepted there in a
commit before collection. The runner is
`tools/hwinfo-logging/experiments/Run-OffsetLadder.ps1`; **do not execute the draft runner**.

## Question and fixed design

On this one RTX 5060 Ti, does a negative NVML P0 graphics offset relocate the median efficiency
optimum according to the already observed stock 0.720 V floor boundary? Worklist 4c found a
−300 MHz shift in the *reported VID lookup* in one `gemm` A–B–A session. That is the motivation,
not a fresh or independent calibration of the prediction here.

Apply stock MSI Afterburner Profile 3 **before** any offset; verify 13801 MHz memory clock under
load. Keep the stock 180 W enforced power limit, 200 W maximum, one driver, one card, HWiNFO at
0.50 s, no desktop activity during sweeps. Run the standard twelve workloads in this fixed order:
`copy`, `reduce`, `softmax`, `layernorm`, `bgemm32`, `bgemm64`, `bgemm128`, `bgemm256`,
`bgemm1024`, `attention`, `conv`, `gemm`. At each of **0, −150, −300, −450 MHz**, run one ascending
13-point sweep per workload from **1237–3090 MHz**. Actual targets from the committed stock suite
are `1237, 1395, 1545, 1702, 1852, 2010, 2167, 2317, 2475, 2625, 2782, 2932, 3090`.
The offset setter accepts only nonpositive offsets down to −500 MHz and verifies every write by
read-back. Reset to 0 in `finally` and verify again. The four suites contain **48 sweeps**, but
only **one chip and one suite per rung**.

The iteration counts are copied from the `workload_command` field of **both rep1 and rep2**
`*_sweep.json` files in `data/frequency-sweeps/5060ti-stock-repro-20260922/`. Both passes agree:

| workload | iterations | workload | iterations |
|---|---:|---|---:|
| copy | 2660 | reduce | 2870 |
| softmax | 2600 | layernorm | 1597 |
| bgemm32 | 2673 | bgemm64 | 2661 |
| bgemm128 | 2467 | bgemm256 | 1579 |
| bgemm1024 | 414 | attention | 147 |
| conv | 151 | gemm | 120 |

For each workload and rung, exclude failed benchmark or missed-lock rows and require all 13
targets to remain. Compute efficiency as timed benchmark throughput divided by windowed mean
power at each target. Choose the target with maximum efficiency for that workload. The **primary
statistic is the ordinary median of those 12 target optima**; do not round a median between grid
points to a grid point. Report the individual 12 optima and achieved clocks, but do not score a
per-workload count as a second test: identical stock suites reproduced only 9/12 individual
optima (`5060ti-stock-repro-20260922/README.md`). Require each sweep's own HWiNFO voltage extract
for validity and report VID patterns separately. The extract is a lookup, not rail voltage.

## Predictions fixed from committed data

The stock fine sweep brackets the floor end at **1567–1575 MHz achieved**
(`data/frequency-sweeps/5060ti-finefloor-20260922/`; the bracket predates this draft). Apply
“floor end − offset magnitude”, then choose the *nearest available target* in the fixed 13-point
grid. This is a grid-level prediction, not a claim that the fine-grid efficiency argmax lies at
the physical floor boundary. The 155 MHz coarse grid can make the top-of-floor rule appear exact.

| NVML offset | floor-end bracket predicted from 1567–1575 | primary median optimum predicted | separability |
|---|---:|---:|---|
| 0 MHz | 1567–1575 MHz | **1545 MHz** | baseline |
| −150 MHz | 1417–1425 MHz | **1395 MHz** | one distinct lower grid point |
| −300 MHz | 1267–1275 MHz | **1237 MHz** | one distinct lower grid point |
| −450 MHz | 1117–1125 MHz | **1237 MHz** | **same lowest grid point as −300**; no further downward median can be resolved |

The predicted median sequence is **1545 → 1395 → 1237 → 1237 MHz**. The −150 and −300 rungs
can distinguish two successive downward steps from stock. A matching −450 median adds **no
evidence for another 150 MHz relocation**: the grid has run out below 1237. Its null-looking
plateau is expected even if the VID lookup continues shifting. A different −450 median can reveal
a failure of the model or another effect, but this grid cannot confirm the extra shift.

## Decision rules fixed before collection

- **Per rung:** if all 12 sweeps, matching metadata and voltage extracts are valid, the predicted
  median passes only on exact equality with that rung's target above. Any other median, including
  a 6/6 split whose median falls between two targets, refutes that rung's exact grid prediction.
- **Monotone trend:** the medians must be nonincreasing in offset magnitude (0, 150, 300, 450).
  Any upward adjacent step refutes monotonicity. The stronger predicted pattern also requires
  strict drops 1545→1395 and 1395→1237 and a 1237→1237 tie; ties at an earlier step fail its
  per-rung prediction even if the weak monotone criterion still passes.
- **Validity, separate from refutation:** a missing/failed sweep, a missed lock, wrong target grid,
  wrong card/driver/power or memory state, missing voltage extract, or unverified offset write or
  reset makes that session unscoreable. Do not turn incomplete data into a pass or a null.

`analysis/score_offset_ladder.py` implements the CSV/metadata/extract checks and the primary and
trend rules. The runner's read-back and final reset are operational gates; preserve its console
log because the CSV cannot independently prove the offset read-back. The scorer cannot certify
that the rail voltage changed. After collection, while the GPU is idle, time-join each sweep to
its own wrapper HWiNFO log with
`python tools/frequency-sweep/join_hwinfo_voltage.py <sweep.csv> <label-hwinfo.csv> --join-by time`,
then run `python analysis/score_offset_ladder.py <results-directory>`. Do not join one rung's log
to another rung's sweep.

## Interpretation boundary

An NVML global offset shifts the **whole** V/F lookup. The Afterburner rung B/C edits change the
floor region while retaining higher stock curve points. The ladders therefore perturb different
parts of the configuration; agreement of their grid optima would show a shared *predictive rule*
on this chip, not that the two controls create the same electrical state or have the same power
at matched clocks. Divergence could come from the upper curve, XBAR or another coupled policy.
This one-chip ladder does not identify a causal rail-voltage mechanism, hardware generality,
linearity between offsets, or a −450 optimum below the observed grid.

---

## Review by Claude, 2026-09-22 — NOT yet registered; one design change recommended

**Verified:**
- the predictions: nearest grid target to (1567–1575 − k) is 1545 / 1395 / 1237 / 1237;
- the 13 targets and 12 iteration counts against the stock-repro CSVs;
- the scorer's 10 synthetic checks pass, including a 7.3 MHz achieved offset, a 6/6 split and a
  wrong grid;
- the runner parses cleanly and is ASCII-only.

**Two runner bugs fixed, both fail-closed** (the runner would have refused to start):
1. it required the power limit to read **200 W**, but stock P3 enforces **180 W**;
2. it checked `MSIAfterburner.exe`'s exit code, which PowerShell does not reliably set for a GUI
   program. The memory-clock witness is the real verification.

⚠️ **Design problem: TWO rungs sit at the grid's floor, not one.** 1237 MHz is the LOWEST target.
So a −300 "pass" at 1237 fits **any** optimum at or below ~1316 MHz, and cannot confirm a move to
~1270 specifically. The draft notes this for −450 only. **The only interior, fully discriminating
rung is −150** (1395, between 1237 and 1545).

**Recommended before registering: 0 / −150 / −300 / 0.** Replace −450, which the draft itself says
can confirm nothing, with a **closing stock suite**. That is the same 48 sweeps, and it buys a drift
bracket: the opening and closing stock medians must agree, as in the Session D and 4c designs.
Keep −300, but state in the registration that its pass is **edge-limited**. Extending the grid
below 1237 would fix the edge, but it breaks comparability with every committed stock suite, so it
belongs in a separate design, not this one.
