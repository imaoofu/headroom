# Adversarial audit: RTX 5060 Ti results from 2026-09-22

**Task.** Job 1 in [GPT-PROMPT-NEXT.md](../agents/GPT-PROMPT-NEXT.md). I read the repository instructions and the five result READMEs, then recomputed the quantities below from the committed sweep and voltage CSVs. This is one RTX 5060 Ti, one day, and driver 616.92. I did not run a sweep or change GPU state.

## Verdict

The stock argmax agreement, the registered P1 median, and the 1567–1575 MHz voltage bracket reproduce. The descending sweeps support a narrow within-session null. The large isolated throughput losses are real, but these files do not identify agent activity as their cause. The six quiet `membw` runs rule out a large dip in those particular runs, not in all quiet conditions or all configurations. The 1627 MHz feature depends on how a local trend is drawn.

| README conclusion | What the committed rows support |
|---|---|
| Stock per-workload optima reproduce 9/12; winner margin median 0.99% | **Yes, on target-grid argmaxes.** Median 0.986% and 13/24 under 1% when margin is `100 × (winner − runner-up) / winner`. The corresponding runner-up denominator gives 0.996% and 12/24. |
| This recalibrates P1/P4 and the older negative control | **Only as a caution.** One stock pair cannot estimate the null distribution of movement counts for either different-profile comparison. |
| Large historical `membw` dips are activity-driven | **Cause unestablished.** None of six new silent runs has the historical 2.17–6.91% departures. The comparison is observational and mixes sessions and, for some historical runs, configurations. |
| A reproducible 1627 MHz `membw` dip occurs in 4/6 | **A shallow chord residual recurs; an actual fall in throughput does not.** All six 1627 MHz throughputs lie above 1552 MHz and below 1702 MHz. |
| Registered P1 prediction holds | **Yes, by the registered primary criterion.** The precollection text specified a median optimum of 2010 MHz and refutation by any other median grid point. It did not specify a 7/12 workload threshold. |
| Floor ends between 1567 and 1575 MHz; direction difference +0.00% | **Voltage bracket yes.** The percentage refers to throughput or benchmark time, not voltage. Quiet descending versus quiet ascending throughput differs by at most 0.082% at any of the 13 targets in the comparison I could reproduce. The README's exact range does not match that comparison. |
| Agent activity caused the isolated 8–11% losses | **No causal identification.** The losses reproduce, but agent activity, elapsed time, and run order changed together. |

## 1. Stock reproducibility and the strength of the controls

I read the 24 `*_sweep.csv` files in [the stock reproduction directory](../../data/frequency-sweeps/5060ti-stock-repro-20260922/README.md). For each workload and pass, I calculated `bench_throughput / power_avg_w` at every target and took the maximum, as [`loadSweep`](../../analysis/analyze_sweep.py) does. Nine of twelve target argmaxes agree. The flips are `bgemm1024` and `bgemm64` at 1545→1395, and `reduce` at 1852→1702 MHz. The same-target winners in the two passes have achieved clocks within 0.3 MHz; thus this is also 9/12 if achieved clocks are matched within 1 MHz. Exact floating-point equality of achieved averages is a poor definition of agreement.

The winner margins recompute to 0.986% median, 0.030% minimum, and 13/24 below 1% with the winning efficiency as denominator. All three flipped workloads have margins below 1% in both passes. The denominator matters at the cutoff: using runner-up efficiency gives 0.996% median and 12/24 below 1%. Neither convention changes the substantive point that many peaks are close.

A uniform draw from 13 points would predict only 12/13 = 0.92 matches across twelve workloads, but it is an implausible null. Ten pass-one winners and eight pass-two winners are at 1545 MHz. Permuting the workload labels while holding those observed winner frequencies fixed would yield 6.92 matches in expectation; that is an illustration of concentration, **not a p-value**, because workload labels are not exchangeable. With only two passes there is no defensible estimate of the per-workload selection probabilities among near-tied grid points.

The stock pair shows that one unchanged configuration can produce three changed argmaxes. It does not show that P1/P4's six changes or the older control's four changes have the same source. Those contrasts change profiles and were not replicated in matched blocks. Likewise the stock median of 1545 MHz occurred twice, but two passes cannot establish median stability in other configurations. The older ABBA result's 12/12 upward direction remains distinct from the three mixed-direction stock flips, while its smallest individual shift still needs replication before it is treated as precise.

## 2. The `membw` feature and the historical large losses

I read all six `*_sweep.csv` files in [the silent `membw` directory](../../data/frequency-sweeps/5060ti-membw-silent-20260922/README.md). The READMEs' 1627 MHz residuals are `100 × [throughput(1627) / mean(throughput(1552), throughput(1702)) − 1]`: stock r1/r2/r3 = −0.431%, +0.113%, −0.510%; P5 r1/r2/r3 = −0.839%, −0.852%, −0.125%. The last P5 run's worst chord residual is instead at 1552 MHz. The achieved clock is 1627 MHz in every run; the neighboring achieved clocks are 1552 and 1702 MHz, so unequal clock spacing does not explain the chord result. The commanded target is 1635 MHz.

An alternate four-neighbor cubic interpolation at 1627 MHz gives −0.665%, −0.085%, −0.706% for stock and −0.874%, −1.003%, −0.232% for P5. Its sign is negative in all six, showing that “4 of 6” depends on the trend rule and threshold. A monotonicity criterion finds zero throughput dips at 1627: each run's throughput rises from 1552 through 1627 to 1702. A broad change in slope, local curvature, or a one-point loss could each make a chord residual; these ten-point sweeps cannot distinguish them.

The telemetry does not point to a simple clock or memory-state transition at 1627. All six achieved clocks are 1627 MHz; memory maximum is 13801 MHz in stock and 16301 MHz in P5 at 1552, 1627 and 1702. For example, P5 r1 power rises 57.71→59.11→61.18 W across those three points; stock r1 reads 55.69→56.02→58.26 W. There is no isolated power collapse in those examples. These readings do not identify the cause of the shallow feature.

The six new quiet runs have no historical 2.17%, 5.93%, or 6.91% single-point chord loss. P5 gives a relevant split-curve comparison, but six absences are not a mechanism test. The historical runs were collected earlier under different combinations of profile, session conditions and agent activity, and there is no measured activity variable paired to their individual bad points. The README's “large dips are activity, not configuration” goes beyond the evidence. A randomized active/silent replay on the same profile, frequency grid and stabilized card would test that assertion.

## 3. Registered Profile 1 prediction

I checked the precollection version with `git show 1f6f3d6:docs/REGISTERED-PREDICTIONS.md`, a revision before the 2026-09-22 collection, as well as the current [registration](../REGISTERED-PREDICTIONS.md). It says: P1 median optimum **2010 MHz**, same grid point as P4; refuted by a median on any other grid point. There is **no 7/12 success rule** in §2. The 7/12 count in [P1's README](../../data/frequency-sweeps/5060ti-p1-suite-20260922/README.md) is a descriptive result, not a registered threshold.

Recomputing the argmax for each of the twelve P1 and twelve [P4](../../data/frequency-sweeps/5060ti-p4-suite-20260922/README.md) sweeps gives medians of 2010 MHz in both profiles. P1 has seven individual winners at 2010; P4 has six. Six workload winners differ between profiles. Thus the registered grid-level prediction succeeded. A shared median on a roughly 155 MHz grid is a coarse test of the proposed floor mechanism: the registration itself expected the proposed floor extents to be only 30 MHz apart, and these sweeps cannot resolve that difference. P1 and P4 also differ in power limit and memory together, with one suite each. The result does not show that floor extent is sufficient to fix each workload optimum.

## 4. Fine floor and descending comparison

Both 13-point `4h-floorend` [voltage extracts](../../data/frequency-sweeps/5060ti-finefloor-20260922/README.md) report 0.720 V at **achieved** 1567 MHz and 0.730 V at achieved 1575 MHz. The measured statement is a bracket between sampled points, on this chip under the tested settings. The files do not reveal the precise transition inside the 8 MHz gap.

The “+0.00%” figure is ambiguous because the README does not name the quantity or reference run in that table. Comparing the clean ascending r3 with descending r1 by matched **target**, descending throughput averages −0.0025%, range −0.0818% to +0.0797%, over all 13 points. Descending r2 averages −0.0115%, range −0.0607% to +0.0674%. The descending r1 **benchmark time** difference averages +0.0025%, which rounds to +0.00%; this may be the reported number. The README's stated −0.04% to +0.08% range does not follow from either direct throughput comparison. The practical null is well supported at the observed temperatures and frequencies, but it is not exact equality of throughput, voltage at every point, or behavior at other thermal states. At achieved 1620 MHz the clean ascending median voltage is 0.740 V, while descending r1 reports 0.7375 V.

## 5. Isolated losses and agent activity

Against quiet ascending r3 at matched targets, ascending r1 throughput is lower by 10.312% at 1567, 10.675% at 1597, 8.474% at 1627, and 7.998% at 1755 MHz. Ascending r2 is lower by 8.781% at 1597 and 3.270% at 1627. The README counts r2 as **one** bad point because only one is in its roughly 8–11% class; the 3.27% loss is still a visible residual. All of these percentages were recomputed from `bench_throughput` in the three ascending CSVs, not copied from the README.

The observations are consistent with transient interference: unaffected neighbors recover, locks were reported held, and the three runs got cleaner. They do not isolate **agent** activity. The prompt reports that the card had just been switched on that morning; I did not find an independent boot timestamp in the committed sweep files. Ascending r1, r2 and r3 began at 08:59, 09:07 and 09:14 in their filenames. Agent behavior, run order and elapsed time therefore co-vary. Nonmonotonic point losses rule out a *smooth uniform* warm-up drift, but not intermittent cold-session effects, background processes, or other transient conditions that fade with time. The `applied_settings` narrative is not a process-load trace.

A discriminating test would alternate or randomize active and silent intervals **after thermal stabilization**, repeat the same target points under both conditions, record actual CPU/GPU process activity and boot-relative time, and predeclare the throughput comparison. Without that reversal, “activity caused it” should remain a hypothesis. “Take the maximum of replicates” may estimate an uncontended envelope if losses are one-sided; these runs alone do not prove that assumption for future sweeps.

## Verification and limits

All numbers in the audit sections were recomputed from the named CSVs unless explicitly labeled as README or prompt claims. Profile settings, driver version, operator absence and the historical dip magnitudes were taken from the READMEs or prompt; I did not independently verify the live Afterburner profiles, raw HWiNFO logs, process load, boot time, or historical seven-run dips. I did not test other chips or run hardware. The registered wording was checked against a precollection git revision.

Before writing, with no active sweep process detected, `python run_tests.py` passed **835 checks in 24 suites**; `python analysis/audit_claims.py`, `python analysis/build_data_manifest.py --check`, and `python analysis/verify_citations.py --check` all exited 0. These gates check repository consistency, not the causal interpretation challenged here.
