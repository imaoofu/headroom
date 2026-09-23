# Job 10: draft NVML offset ladder, before any 4o data

2026-09-22. Wrote a **proposal**, not a live registration, at
`docs/agents/DRAFT-offset-ladder-registration.md`; a fixed runner at
`tools/hwinfo-logging/experiments/Run-OffsetLadder.ps1`; and
`analysis/score_offset_ladder.py` with synthetic fixtures in
`analysis/test_score_offset_ladder.py`. Nothing was added to
`docs/REGISTERED-PREDICTIONS.md`. The runner was **not executed**, even in preview mode, and no
GPU setting was changed.

## Committed inputs and predictions

I read the actual 13 target clocks from the stock suite CSV and all twelve iteration counts from
both rep1 and rep2 `workload_command` fields in
`data/frequency-sweeps/5060ti-stock-repro-20260922/`; both passes agree. The stock floor-end
bracket **1567–1575 MHz** is taken from the already committed fine-floor record, not refitted to
this draft. Subtracting offset magnitudes and choosing the nearest tested target yields median
target predictions **1545 / 1395 / 1237 / 1237 MHz** for 0 / −150 / −300 / −450 MHz. The last
two offsets are indistinguishable by this primary statistic on the chosen grid; −450 can reveal
an unexpected change but cannot positively confirm an additional 150 MHz relocation.

The draft fixes exact per-rung and nonincreasing-trend refutations, treats an even six/six split
as a between-grid median rather than rounding it, and requires complete sweeps and each sweep's
own voltage extract. A matching median is an N=1 chip, one-suite-per-offset result; twelve
workloads are not twelve independent chips or sessions. The lookup voltage cannot establish rail
voltage, and a global offset changes more of the curve than the Afterburner floor-only rungs.

## Implementation and checks

The runner applies stock Profile 3 before the offset, verifies stock memory under load, runs 48
logged sweeps through the existing wrapper, verifies every NVML offset write, and resets to zero
with read-back in `finally`. It refuses to touch the GPU if another measurement process is
already running. The wrapper's output is sent to `Out-Host`, so it cannot contaminate the
function's returned exit code; there is no script-level `return` inside `try`. It passes iteration
counts in the job JSON, where the wrapper constructs the benchmark command, and uses no `$args`
automatic-variable splat. These are static/code checks: **the runner was not exercised**.

The scorer uses the existing `analyze_sweep.loadSweep` efficiency calculation, requires the
registered target grid and complete per-sweep metadata/extracts, and scores target-grid optima
rather than exact achieved-clock equality. Synthetic fixtures checked a 7.3 MHz target/achieved
gap, a 6/6 median between grid points, wrong targets, a missing voltage extract, a missed lock,
and a wrong iteration count. The fixture script passed. PowerShell parsing found no syntax error.

Before writing, and again after the implementation, the repository gates passed:
`python run_tests.py`, `python analysis/audit_claims.py`,
`python analysis/build_data_manifest.py --check`,
`python analysis/verify_citations.py --check`, and
`python analysis/check_data_hashes.py --check`. Final counts are recorded in the task response.

## Still unverified

No live HWiNFO log, NVML read-back, power-state change, driver behavior, or 4o outcome was
observed. The scorer cannot independently authenticate the runner's NVML read-back from CSVs;
its console log must be preserved. The draft needs review and a precollection commit to the live
registration before any bench run. The −450 prediction is at the minimum grid boundary, so the
planned grid has no power to locate an optimum lower than 1237 MHz.

## Review by Claude, 2026-09-22

Accepted as a draft; **not registered**. Predictions and inputs verified; 10 scorer checks pass. Two
fail-closed runner bugs fixed: the 200 W power expectation (stock is 180 W), and an exit-code check
on a GUI program. **Design note added to the draft:** −300 is edge-limited as well as −450, because
1237 is the lowest grid target, so −150 is the only interior test. Recommended rungs 0 / −150 / −300
/ 0, with the closing stock suite as a drift bracket in place of the −450 rung, which can confirm
nothing. Registration waits on Raymond's choice.
