# Adversarial audit: the curve predictor and its regret metric

**Date:** 2026-09-20  
**Repository state audited:** `61bcdc14306585f611ddbdf45d62cdcf30aa04ad`  
**Status:** GPT lead for independent recomputation. This is not a paper correction and does not
become an established project result until someone here reproduces it.

## Verdict

The published four-row table is numerically reproducible from the committed inputs. Its main
interpretation is too strong.

`predict_from_curve.py` is a two-action lookup on this corpus: it selects 1545 MHz for stock,
split, and repair, and 2010 MHz for full tune. The hindsight per-configuration baseline selects the
same two actions, so their exact tie is an identity of discrete choices on this grid. It is not an
independent replication of the physical mechanism.

The whole 2.90x advantage over the global 1545 MHz constant comes from the single full-tune
configuration. Remove full tune and all three non-oracle strategies become identical: 0.626% mean
regret, 11.939% worst regret, and 77.8% exact matches over 144 repeated curves. The informative
configuration-level contrast is therefore one altered configuration on one chip, repeated four
times over the same twelve workloads.

Cross-validation does not change the selected bins, but it does not cure the central problem.
There is no genuinely held-out configuration. The predictor first appeared in commit `1ddcd0c` on
2026-09-09 after the configurations and outcome data used by the 192-sweep table had been observed.
The intermediate floor ladder and Profile 1 tests registered in commit `a2192af` remain uncollected.
A later stock `r10` suite is prospective at the run level and again selects 1545 MHz, but stock is
the same branch on which the mechanism and the global constant agree.

The 74.0% exact-match rate is grid-dependent. The coarse suite grid is 150-158 MHz wide. On the one
later clean fine-grid check, a 13-point stock GEMM sweep at roughly 30 MHz spacing, the current
decoded-curve rule selects commanded 1537 MHz while the measured argmax is 1410 MHz. Exact match is
0/1 and regret is still only 0.622%. One workload cannot estimate how much of 74.0% would survive a
fine grid, but it directly shows that exact equality and low regret are different claims.

Perturbing the 720 mV parameter by one observed voltage code does nothing to the table. The raw log
for this card uses 5 mV reported steps; 715, 720, and 725 mV all produce the same two actions and the
same scores. In fact every integer threshold from 711 through 741 mV maps to the same actions. The
coarse grid therefore cannot identify 720 mV as the special parameter. This robustness is a
quantisation result, not evidence that the physical floor was located precisely.

The V100 result is consistent with this audit. The ridge model and held-out fixed baseline make the
same choice for 32 of 33 workloads. On `CNN_1.5M` the ridge model alone moves from 952 to 885 MHz and
loses; it never improves a choice. The consumer predictor does not model workload identity either.
The two analyses therefore do not give opposite answers about workload modelling. They both show
that a coarse discrete action is dominated by a constant or configuration lookup in the data at
hand. What remains unsettled is whether a workload-specific correction, especially for `reduce`,
would transfer to a new run, configuration, chip, or workload.

## Recomputed headline table

The repository script was run without modification and then recomputed independently from the
paths in `CONFIGURATION_RUNS`.

| strategy | mean regret | worst regret | exact | scored curves |
|---|---:|---:|---:|---:|
| oracle | 0.000% | 0.000% | 100.0% | 192 |
| curve read at 720 mV | 0.675% | 11.939% | 74.0% | 192 |
| best constant per configuration, same-data hindsight | 0.675% | 11.939% | 74.0% | 192 |
| best single constant, same-data hindsight | 1.961% | 13.479% | 60.9% | 192 |

The raw exact count is 142/192. The mechanism and per-configuration baseline choose 1545 MHz on
144 curves and 2010 MHz on 48. The global baseline chooses 1545 MHz on all 192.

The score is unbalanced by run count: stock contributes 84 curves, full tune 48, split 48, and
repair 12. Equal weighting across the four configurations gives 0.820% for the mechanism and
2.107% for the global constant. The difference remains 1.286 points because full tune is exactly
one quarter of both the raw rows and the equally weighted configuration average, and the strategies
are identical on the other three configurations.

### What the 2.90x contains

| configuration | runs | curves | mechanism mean | global-1545 mean | mechanism action |
|---|---:|---:|---:|---:|---:|
| stock | 7 | 84 | 0.426% | 0.426% | 1545 |
| split | 4 | 48 | 0.834% | 0.834% | 1545 |
| repair | 1 | 12 | 1.200% | 1.200% | 1545 |
| full tune | 4 | 48 | 0.822% | 5.966% | 2010 |

All improvement over the global constant is in the last row. On this sample, “configuration
information” means distinguishing full tune from the three configurations that map to the global
constant. Calling it a two-level classifier evaluated 192 times is substantively accurate, though
the code implements a curve-to-frequency lookup rather than a statistical classifier.

## Effective sample size

There is no single effective `n` for the table because the design crosses repeated workloads with
an unbalanced number of run legs nested within configuration. The relevant units have to be stated
for each comparison.

| comparison | displayed denominator | relevant effective units | held-out evidence in headline |
|---|---:|---|---:|
| oracle versus measured argmax | 192 curves | descriptive upper bound; 16 run legs, 12 recurring workloads, 4 configurations, 1 chip | not applicable |
| mechanism exact/regret score | 192 curves | 4 configuration decisions, only 2 distinct actions; 16 run legs and 12 repeated workloads; 1 chip | 0 configurations |
| mechanism versus per-configuration hindsight | 192 curves | 4 fitted configuration constants, only 2 distinct fitted values; 1 chip | 0 configurations |
| mechanism versus global hindsight | 192 curves | 4 configuration clusters, but only 1 informative configuration because the other 3 use the global action; 1 chip | 0 configurations |
| V100 ridge versus fixed | 33 workloads | 33 held-out workload folds on 1 V100 and 1 configuration | 33 workloads, 0 chips |

Thus 192 is a valid count of scored curves, not a count of independent tests of the curve
mechanism. For the 2.90x comparison, the treatment-level evidence is one distinctive configuration.
For hardware generalisation, effective `n` is one chip.

## Fairer baselines

The hindsight baselines are optimistically biased in their own favour because they are fit and
scored on the same curves. That makes them strong descriptive comparators, but they cannot establish
out-of-sample equivalence. Replacing them with held-out fits gives the following results.

| evaluation | folds | mechanism mean / exact | global fixed mean / exact | per-config mean / exact |
|---|---:|---:|---:|---:|
| leave one workload out | 12 | 0.675% / 74.0% | 1.961% / 60.9% | 0.675% / 74.0% |
| leave one run leg out, all 192 for global | 16 | 0.675% / 74.0% | 1.961% / 60.9% | unavailable for repair |
| leave one run leg out, comparable non-repair subset | 15 scored folds, 180 curves | 0.640% / 73.9% | not the relevant comparator | 0.640% / 73.9% |
| leave one configuration out | 4 | 0.675% / 74.0% | 1.961% / 60.9% | undefined for unseen configuration |

Every training fold selects the same bins as the in-sample fit. This is a useful stability check,
but leave-one-configuration-out is not honest validation of the mechanism itself: only the
baseline is refit. The 720 mV rule and the decision to use the curve at that value were developed
with the held configuration already known.

An externally fixed 1545 MHz policy scores exactly like the global hindsight row: 1.961% mean,
13.479% worst, and 60.9% exact. The repository does not contain a preregistration that designates
1545 MHz as the global comparator for this 192-curve analysis, so it should not be relabelled
preregistered after the fact.

The closest genuinely later evidence is `suite-replicate-r10-20260918`, committed in `ea47cc9`,
nine days after the predictor. On its twelve stock workloads, the mechanism, fixed 1545 MHz, and
same-run hindsight optimum all select 1545 MHz and score 0.674% mean regret, 5.299% worst, and 75.0%
exact. This supports repeatability of the stock action across a driver update. It cannot distinguish
curve reading from a fixed constant.

## Grid dependence of “ties exactly”

The coarse target differences are 150, 157, or 158 MHz. A continuous floor estimate only has to
fall within roughly half a bin of the hindsight choice to count as the same prediction. The present
rule is correspondingly tolerant:

- 142/192 curves put the mechanism action at the raw argmax.
- 150/192 are within 0.5% regret, 154/192 within 1%, and 167/192 within 2%.
- The mechanism action ranks second on 22 curves and third on 17.
- On 104/192 curves, the best and second-best sampled points are within 2% efficiency. On 56/192
  they are within 1%.

The exact-match statistic will generally fall as the grid is refined because a broad near-optimal
region is divided into more labels. The available clean fine-grid record demonstrates this for one
case:

| record | workload/configuration | grid | predicted command | raw argmax | regret | exact |
|---|---|---|---:|---:|---:|---:|
| `20260918-202543_5060ti-finefloor-gemm-r2_sweep.csv` | GEMM / stock | 13 points, about 30 MHz | 1537 | 1410 | 0.622% | 0/1 |

The earlier fine sweep in the same directory was contaminated by concurrent repository work and
is not evidence about throughput location. It puts the argmax at 1597 MHz, illustrating how easily
the label can move while regret remains small.

To distinguish a correct mechanism from one that is merely within a coarse bin, register a
continuous frequency prediction before collection; use several configurations with at least four
distinct floor extents; randomise run and workload order; sweep each predicted region finely with
replication; estimate the peak and its uncertainty continuously; and test calibration slope,
offset, and regret on held-out configurations and chips. The pending intermediate ladder is the
minimum useful configuration test. A direct rail-voltage measurement would be required to turn the
decoded/requested curve threshold into a physical voltage-floor mechanism.

## Sensitivity to the 720 mV parameter

The profile snapshot was re-read at perturbed voltage thresholds and mapped to the existing suite
grid.

| threshold | stock/split/repair action | full-tune action | mean regret | exact |
|---:|---:|---:|---:|---:|
| 715 mV | 1545 | 2010 | 0.675% | 74.0% |
| 720 mV | 1545 | 2010 | 0.675% | 74.0% |
| 725 mV | 1545 | 2010 | 0.675% | 74.0% |

The one-code perturbation therefore leaves the mechanism ahead of the global baseline and tied to
the per-configuration baseline. The more important audit finding is lack of parameter resolution:
every whole-millivolt threshold from 711 to 741 produces the same table. At 710 mV the three lower
configurations drop to 1395 MHz and mean regret rises to 2.993%; at 715 mV they have already snapped
back to 1545.

The later fine voltage run also corrects the physical reading that motivated 720 mV. Reported
voltage remains 0.720 V through 1560 MHz achieved and first rises at 1590 MHz. The earlier 1530 MHz
decoded extent was not a measured endpoint. This does not change the coarse action, but it means
the table cannot validate equality between a measured transition and the optimum.

## The structured residual

`reduce` is not behaving like ordinary adjacent-bin jitter. The mechanism misses all 16 `reduce`
curves, and every raw optimum lies above the predicted action:

- stock: 1702 MHz on four runs and 1852 on three;
- split: 1852 on one run and 2010 on three;
- repair: 2167 on its only run;
- full tune: 2167 on two runs, 2317 on one, and 2625 on one.

Its mean regret is 4.790% and its worst is 11.939%. This is evidence that the single curve-derived
action does not capture this workload on the observed chip. It does not identify why.

`gemm` is different. Full tune lands exactly on 2010 in all four runs, while stock and split move
among 1395, 1545, and 1702. The clean fine-grid run later peaks at 1410. Grouping `reduce` and
`gemm` as the 70% residual pair hides the difference between a systematic upward displacement and
a flat, run-sensitive peak.

The suite order is a live confound. Fourteen of sixteen run legs use the exact order encoded in
`SUITE_WORKLOADS`: `copy`, `reduce`, ..., `gemm`. In the other two, `copy` was appended, leaving
`reduce` first and `gemm` last. Workload identity is therefore almost perfectly confounded with
position, temperature history, and session duration. The later fine-floor record also shows that
desktop contamination can move throughput by about 9% without changing the reported voltage.

A leave-one-run-out policy that learns a separate frequency for each known
configuration/workload cell scores 0.497% mean regret on the 180 curves with another same-config
run available, compared with 0.640% for the configuration-only action on those same curves. The
0.143-point improvement is a lead that repeatable workload structure exists. It does not test a new
workload, the repair configuration is excluded, and the fixed suite order remains confounded.

The clean discriminator is a preregistered, random-order, replicated fine sweep of `reduce` plus a
matched workload under several curve extents. If `reduce` keeps a stable positive offset from the
floor prediction across order and sessions, the residual is a mechanism limitation or real
workload property. If it follows run position, host load, duration, or thermal history, it is a
measurement/benchmark artifact. Direct benchmark-window energy integration and repeated points
around the peak would separate a power-estimation artifact from a genuine efficiency shift.

## Reconciliation with the V100 null

`predict_optimal_frequency.py` correctly uses leave-one-workload-out fitting. Recalculation gives:

| strategy | mean regret | worst | exact |
|---|---:|---:|---:|
| held-out best fixed frequency | 0.837 percentage points | 6.890 | 72.7% |
| held-out ridge probe model | 0.883 percentage points | 6.890 | 69.7% |

The paired difference is entirely `CNN_1.5M`: fixed selects 952 MHz, ridge selects 885 MHz, and
ridge is worse. The strategies select the same 952 MHz on the other 32 workloads. A workload
bootstrap of the paired mean difference gives 0.000 to 0.137 percentage points at the 2.5th and
97.5th percentiles. This is a null for benefit and a small observed loss, on 33 workloads and one
V100.

The two scripts do not use identical regret definitions. V100 reports percentage-point loss in an
efficiency curve normalised to the stock point. The consumer script reports loss relative to each
curve's own peak. Recomputing V100 with the consumer definition gives 0.565% mean regret for fixed
and 0.596% for ridge, a 0.031-point loss. The verdict does not change.

There is no contradiction to resolve:

1. V100 asks whether probe features improve selection for a new workload under one hardware
   configuration. They do not in this sample.
2. The consumer script asks whether one of two configuration actions beats a single global action
   on one chip. Only full tune distinguishes them.
3. The consumer script does not test workload identity or workload features. Its residual suggests
   a possible workload correction, but no held-out new-workload model has been evaluated.

The stronger repository wording that the curve mechanism “extracts everything the configuration
axis holds” is unsupported. It extracts the same two discrete actions as a per-configuration
constant on this grid. It does not establish that all configuration-dependent variation is captured,
that workload identity is worthless, or that the result transfers to a new curve or chip.

## What was verified

- `python analysis/models/predict_from_curve.py` reproduced every headline number and action.
- The 192 input curves were reloaded directly from the committed paths, retaining configuration,
  run leg, and workload identifiers that the model's public loader discards.
- Leave-one-workload-out, leave-one-run-out, leave-one-configuration-out, equal-configuration
  weighting, full-tune removal, voltage perturbation, residual grouping, and V100 metric conversion
  were recomputed independently in a temporary script outside the repository.
- The later `r10` suite and clean fine-grid GEMM run were scored separately rather than silently
  added to the historical 192.
- Git chronology was checked with `git log --follow` and dataset-specific logs.
- Required pre-write checks passed at this repository state: 792/792 tests, 284/284 claims, data
  manifest reconciliation, and citation coverage.

## What could not be checked

- No new hardware measurement was run.
- There is no collected unseen configuration with a new floor extent, so configuration
  generalisation cannot be estimated.
- Only one clean fine-grid workload/configuration is available; the fine-grid exact-match rate for
  the twelve-workload suite is unknown.
- The committed telemetry does not establish the physical rail voltage or prove that 720 mV is a
  rail-level mediator. The predictor reads a decoded applied curve and uses a coarse reported value.
- The existing fixed-order runs cannot separate workload physics from suite position, thermal
  history, and session contamination.
- One chip cannot establish chip-to-chip, board-to-board, or architecture-level performance.

## Primary repository evidence

- [`analysis/models/predict_from_curve.py`](../../analysis/models/predict_from_curve.py)
- [`analysis/models/predict_optimal_frequency.py`](../../analysis/models/predict_optimal_frequency.py)
- [`analysis/models/README.md`](../../analysis/models/README.md)
- [`data/afterburner-profiles/5060ti-profiles-20260908b-p4-plateau-3030.json`](../../data/afterburner-profiles/5060ti-profiles-20260908b-p4-plateau-3030.json)
- [`data/frequency-sweeps/5060ti-finefloor-20260918/README.md`](../../data/frequency-sweeps/5060ti-finefloor-20260918/README.md)
- [`data/frequency-sweeps/suite-replicate-r10-20260918/README.md`](../../data/frequency-sweeps/suite-replicate-r10-20260918/README.md)
- [`data/frequency-sweeps/voltage-curve-20260908/README.md`](../../data/frequency-sweeps/voltage-curve-20260908/README.md)
- [`docs/REGISTERED-PREDICTIONS.md`](../REGISTERED-PREDICTIONS.md)
- [`docs/gpt-findings/2026-09-19-load-floor-causal-claim-adversarial-audit.md`](2026-09-19-load-floor-causal-claim-adversarial-audit.md)
- [`data/raw/README.md`](../../data/raw/README.md)

Relevant history identifiers: predictor creation `1ddcd0c`; initial ABBA result `0ca60ea`;
negative control `cc3ef9e`; registered ladder `a2192af`; fine-floor data `a1bec61`; prospective stock
`r10` `ea47cc9`.
