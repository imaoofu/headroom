# Adversarial audit of the load-floor causal claim

**Audit date:** 2026-09-19

**Scope:** repository evidence for the claim that the energy-efficiency optimum on four consumer
NVIDIA GPUs is causally set by the top of the voltage-frequency curve's low-voltage region.

## Verdict

The repository contains strong evidence for a **configuration-level effect on one RTX 5060 Ti**:
switching between two complete Afterburner profiles in one ABBA session changed the median
twelve-workload efficiency optimum from 1537 to 2002 MHz. All twelve paired workload optima moved
upward. The ABBA order, repeated endpoints, common power limit, common memory offset, common driver,
and common workload protocol make ordinary linear session drift a poor explanation for that result.

The repository does **not** isolate the top of a physical voltage floor as the mediator. The
intervention was a switch between complete saved profiles whose curves differ outside the proposed
floor region; the ABBA run had no voltage telemetry; later HWiNFO voltage evidence is consistent
with a coarse requested or target-voltage value and is not documented as a rail measurement; and
the negative control preserves only the median while several individual workload optima move.

The four-GPU wording also combines unlike evidence. Only the RTX 5060 Ti received a curve
intervention. The RTX 3070 Ti and RTX 3060 results are stock-curve associations. The RTX 2060 Super
prediction was refuted as registered and became undecidable only after a finer follow-up located an
ambiguous floor exit. The causal experimental unit is therefore **one chip and one profile contrast**.
The twelve workloads are repeated outcomes on that intervention, not twelve independent chips.

A defensible sentence from the current evidence is:

> On one GB206 board, switching between two complete V/F profiles in an ABBA session shifted the
> median twelve-workload throughput-per-watt optimum by 465 MHz, with all twelve workload optima
> moving upward; stock measurements on two other boards place their coarse-grid median optima near
> exits in the reported voltage curve, but the present data do not isolate physical rail-voltage
> floor mediation, and the fourth board is undecidable.

## Corrections to the headline claim

| Claim | What the repository establishes |
|---|---|
| "On four consumer GPUs ... we reshape the curve" | Four GPUs were observed, but the curve was manipulated only on one RTX 5060 Ti. |
| "+465 MHz in 12 of 12 workloads" | The **median** shift was +465 MHz and all 12 shifts were positive. Only 6 of 12 were exactly +465 MHz; the rest ranged from +79 to +540 MHz. |
| "A larger edit above it moved the optimum by 0" | The negative-control **median** stayed at 1537 MHz. Individual optima were not invariant. P2 differs from the stock bracket in 4 of 12 workloads; against the two P5 ABBA legs it differs in 3 of 12 and 5 of 12, respectively; against their per-workload mean it differs in 6 of 12. |
| "Every prediction was registered before collection" | The decisive P4/P5 load-floor interpretation was post hoc. The ABBA run registered a different prediction, that the deeper undervolt would leave less than 27.5% headroom; it failed, with 34.32% for P4 versus 28.27% for P5. The ABBA README and commit both call the floor result unplanned. Later P2, stock-bracket, RTX 3060, and RTX 2060 tests were prospective in different senses. |
| "The 5060 Ti floor ends at 1537 MHz" | It was never measured there. The fine stock sweep reports 0.720 V through 1560 MHz and 0.730 V at 1590 MHz, so the exit is bounded between those points. The 1537 MHz suite optimum is the nearest lower coarse-grid point, not the measured endpoint. |
| "Voltage floor" as a measured physical rail state | The causal run inferred voltage from decoded profile tables and logged no HWiNFO voltage. Public documentation does not identify HWiNFO's NVIDIA field as rail voltage, and the project's load test found no response to a 71 W board-power change. "Reported or decoded VID region" is supported; "measured rail-voltage floor" is not. |

The current paper's detailed section already corrects the 12-of-12 wording: it says six workloads
moved exactly 465 MHz and all twelve moved in the same direction. The abstract-level contribution
statement still uses the overstrong version.

## Where the comparisons share controls

### P4 versus P5: the main manipulation

The strongest comparison is `abba-20260908`:

- Same physical RTX 5060 Ti, driver 616.64, 200 W enforced limit, +2500 MHz memory offset, workload
  implementations, iteration counts, 13-point frequency grid, and measurement code.
- Four suites in P4/P5/P5/P4 order. Averaging the outer P4 legs and inner P5 legs cancels a linear
  time trend by construction.
- Profile identity was checked from memory clock and matched-clock power in the resulting data.
- Both P4 legs have a 2002 MHz median and both P5 legs have a 1537 MHz median. The large median
  difference therefore does not depend on one anomalous leg.

These controls make a broad profile effect credible. They do not make the treatment a single-region
edit:

- P4 is about 465 MHz above P5 at 700 and 800 mV, but it is about 100 MHz **below** P5 around 875 and
  925 mV.
- The ABBA-era P4 plateau was 3015 MHz while P5's was 3030 MHz. P4 was edited later that day; later
  runs bearing the name "Profile 4" are a different full configuration even though the low region
  stayed the same.
- The curve profiles were pre-existing hand-built configurations, not byte-identical experimental
  profiles created to differ only below a specified voltage.
- There was no HWiNFO log in the ABBA run, so the treatment is the decoded requested curve, not an
  observed delivered-voltage trajectory.
- The order was fixed rather than randomized. ABBA cancels linear drift, but not nonlinear warm-up,
  carryover, or a treatment-by-order interaction. The first P4 leg began at 39 C without the same
  preceding cooldown as the other three, which began at 33 C. Agreement between the two P4 medians
  makes this unlikely to explain the 465 MHz aggregate shift, but it remains part of the design.

### P2 versus P5: the intended negative control

P2 and P5 share the same chip, driver, 200 W limit, +2500 memory setting, low-end decoded curve at
700/720/800 mV, suite, and frequency grid. They differ by as much as 570-575 MHz at 875/925 mV. The
P2 run prospectively predicted a 1537 MHz median and obtained it.

The comparison does not share a session or replicate structure. P2 is one suite collected the next
day; P5's primary evidence is two suites from the preceding ABBA session, with an additional P5
suite elsewhere. P2 and P5 could not be distinguished by the pre-run low-frequency fingerprint, so
P2 identity was established post hoc from power in the region where the profiles diverge. No voltage
telemetry was logged.

Most important, the negative control is zero only after aggregation. The exact per-workload audit is:

| Comparison | Median difference | Workloads with a different per-workload optimum value |
|---|---:|---:|
| P2 versus stock bracket | 0 MHz | 4 of 12 |
| P2 versus P5 ABBA leg B1 | 0 MHz | 3 of 12 |
| P2 versus P5 ABBA leg B2 | 0 MHz | 5 of 12 |
| P2 versus the per-workload mean of P5 legs B1/B2 | 0 MHz | 6 of 12 |

P2 versus stock is also not a clean treatment contrast because stock uses a 180 W limit and stock
memory, while P2 uses 200 W and +2500 memory. It is still useful as evidence that the median is
insensitive to several configuration changes. It is not evidence that every workload is insensitive.

The median has a low breakdown sensitivity here because many workloads pile onto the same 1537 MHz
grid point. Several workloads can move by a full bin while the sixth and seventh ordered values, and
therefore the median, remain unchanged. A zero median shift cannot support the sentence "nothing
happens" without the per-workload qualification.

### Stock observations across GPUs

The cross-card arm shares the workload definitions and the throughput-per-watt objective. It does
not share chip, board, host, driver, power limit, frequency grid, replicate count, or voltage-log
procedure. It is evidence about predictive association, not a controlled causal replication.

- **RTX 5060 Ti:** the stock suite optimum is aggregated over five retained stock replicates. The
  floor cited by the claim auditor comes from a separate old HWiNFO-joined run; the 2026-09-18 fine
  run now bounds the exit between 1560 and 1590 MHz.
- **RTX 3070 Ti:** one twelve-workload SILENT-BIOS suite gives the 1485 MHz median. Its 1500 MHz,
  0.812 V floor comes from a separate HWiNFO run on the same card and nominal BIOS position.
- **RTX 3060:** one suite gives 1260 MHz. A HWiNFO log spans that session, but joins for different
  workloads pool the same clock-binned samples and are not independent confirmations. The stock
  association was prospective: commit `5f3791f` on 2026-09-07 specified the test before the data in
  commit `4c3a7ea` on 2026-09-10.
- **RTX 2060 Super:** one suite gives 1065 MHz. The registered prediction was 855 or 960 MHz and was
  refuted. A later fine sweep makes the rule depend on whether the endpoint is defined strictly at
  the minimum reported value or with one telemetry code of slack; the repository correctly calls
  this undecidable.

## Is the optimum located the same way in every comparison?

The base estimator is consistent: for each workload sweep, the code chooses the measured row with
maximum `throughput / power` and uses achieved clock. There is no fitted continuous optimum or
uncertainty interval in this causal claim. The aggregation and the floor measurement differ:

| Evidence row | Optimum aggregation | Floor or curve source |
|---|---|---|
| 5060 Ti stock | Mean of each workload's raw argmax over five stock suites, then median of 12 workload means | Separate HWiNFO extract; current auditor still reads the older coarse file |
| 5060 Ti P4/P5 ABBA | Mean of each workload's raw argmax over two legs per profile, then median | Decoded saved curves; no voltage telemetry in the run |
| 5060 Ti P2 | Median of 12 raw argmaxes from one suite | Decoded saved curve; no voltage telemetry |
| RTX 3070 Ti | Median of 12 raw argmaxes from one suite | Separate HWiNFO run |
| RTX 3060 | Median of 12 raw argmaxes from one suite | Same-session HWiNFO log, pooled by clock across workloads |
| RTX 2060 Super | Median of 12 raw argmaxes from one suite | Later low-range/fine run; conclusion changes under a one-code tolerance |

The grids also differ by card, and the 5060 Ti causal grid is roughly 155-158 MHz wide. The claim
therefore asks whether two independently coarse quantities select the same grid bin. That can be a
useful low-cost predictor, but it is less precise than equality between a physical transition and a
continuous optimum.

The repository itself documents that raw argmaxes are unstable on flat efficiency curves and uses a
quadratic vertex for a different fine-sweep analysis. That continuous estimator is not used for the
load-floor causal claim. The comparison is internally reproducible at the median level, but it is not
one uniform location procedure across all rows.

## Registration chronology

The statement that every relevant prediction was registered is not supported by the timestamps and
the run metadata.

1. Commit `5f3791f` on 2026-09-07 observed the stock association on the 5060 Ti and 3070 Ti and
   prospectively named the incoming RTX 3060 and RTX 2060 Super as tests.
2. The September 8 ABBA JSON files register a **headroom** prediction: because P4 was the deeper
   undervolt, its remaining headroom should be below P5's 27.5%. The result went the other direction.
3. The ABBA README says the load-floor result "was not planned," and commit `0ca60ea`, made after the
   11:52-15:50 collection session, also calls it unplanned. This is the decisive manipulation from
   which the +465 MHz causal interpretation was discovered.
4. The P2 negative-control prediction was written into its run metadata before collection and is a
   valid prospective follow-up. The stock bracket likewise recorded its frequency predictions.
5. The RTX 3060 stock result is a valid prospective association test. It does not manipulate the
   proposed mediator.
6. The RTX 2060 Super derived prediction was registered before reading its optimum and was refuted.
   The later finer measurement cannot turn the registered outcome into a success.

`docs/REGISTERED-PREDICTIONS.md` currently says the ABBA and P2 runs both named the predicted optimum
ahead of their data. That statement conflicts with the ABBA JSON, README, commit message, and times.
A fair summary is that the initial intervention result was post hoc and several follow-up predictions
were prospective.

## Strongest configuration-level alternative

The best alternative does not deny the ABBA result. It accepts that switching profiles caused the
efficiency curves to move and disputes only the claimed mediator.

The saved profile selects an entire requested V/F mapping. That selection can jointly change:

- requested VID and actual power at a locked core clock;
- the slope and kink of the board-power curve, which directly changes a throughput-per-watt argmax;
- firmware-selected P-state or clock-domain policy, including unobserved or partly observed fabric,
  cache, memory-controller, and crossbar behavior;
- attainable clocks and the operating distance from power, voltage, and thermal limits; and
- other profile metadata whose meaning is not fully decoded.

Under this account, the frequency at which the decoded curve leaves its lowest reported VID region
and the frequency at which efficiency peaks are two consequences of the same configuration state.
The former is a useful marker for the latter, but has not been shown to be the physical causal
mediator. The flat reported-voltage segment can label a table or firmware regime even if the rail
voltage droops with current or hidden clock domains change for another reason.

This alternative also explains why the cross-card association may predict well. NVIDIA can place a
table transition near an intended efficiency knee. Reading that transition can identify the knee
without proving that an electrically flat rail creates it. The observed power law is compatible with
the proposed mechanism, but the instrumentation has not separated requested voltage, delivered
voltage, fixed board power, leakage, and hidden-domain clocks.

The P2 control weakens simple alternatives such as "the optimum follows the plateau" or "any large
mid-band edit moves the median." It does not exclude a nonlinear configuration effect, a low-region
table-state effect, or workload-specific effects that a median hides. A 570 MHz edit in one region
need not be a larger dose of the mechanism caused by a differently shaped 100 MHz edit elsewhere.

## What the one-chip intervention rules out

On this chip and session, it rules out these narrow accounts:

- the two saved profiles have the same efficiency-optimum distribution;
- a simple linear time drift explains the 465 MHz median separation;
- the result is carried by only one workload or by one ABBA leg; and
- the plateau frequency alone determines the median optimum.

It does not rule out:

- a whole-profile or firmware-state effect rather than physical floor-voltage mediation;
- an effect specific to this GB206 sample, board, driver, or Afterburner implementation;
- nonlinear order, warm-up, or hysteresis effects;
- raw-argmax movement on a coarse grid due to shallow efficiency peaks;
- a requested-VID transition that is only a proxy for actual rail voltage; or
- workload-specific responses to the negative control.

Twelve workloads show breadth across code paths on one treated unit. They do not raise the causal
hardware sample size above one chip.

## Experiment that would separate the accounts

The registered four-rung floor ladder is the right next design if implemented exactly as written:
new profiles should be byte-identical to P5 at and above 860 mV and differ only in the sub-850 mV
points, with intermediate predicted optima. It should be strengthened by randomized or balanced
profile order, multiple complete sequences, a fresh profile hash recorded for every leg, and the
full workload-level response reported rather than only the median.

To test **physical voltage-floor mediation**, the experiment also needs delivered core-rail voltage
or controller `READ_VOUT` verified for the exact board, sampled under the workload. HWiNFO's current
field is insufficient without documentation of its source. Pre-register three linked changes:

1. the delivered-voltage transition moves by the intended amount;
2. the relevant power-curve slope or hidden clock-domain transition moves with it; and
3. the continuous or fine-grid efficiency optimum follows dose monotonically.

If only the decoded/requested table transition and optimum move, the justified result is a
configuration-level predictor. If the delivered rail transition is measured and mediates a
dose-response while all other profile content is held fixed, the voltage-floor causal wording
becomes supportable.

## Repository consistency issues exposed by the audit

- The contribution statement in `docs/PAPER_DRAFT.md` still says "+465 MHz in 12 of 12" and "every
  prediction registered," although the detailed section and ABBA record contradict both phrasings.
- `docs/REGISTERED-PREDICTIONS.md` incorrectly characterizes the ABBA optimum prediction as
  pre-registered.
- `analysis/audit_claims.py` passes the 5060 Ti floor statement because `claims_consumer.py` still
  reads the older coarse voltage extract and renders 1552 MHz. The newer fine sweep, already in the
  repository, bounds the exit between 1560 and 1590 MHz. A green claims audit verifies the selected
  source, not that the selected source is current.
- Several files call the 6 mV grid sensor resolution. The documentation audit supports only
  "granularity of the reported voltage value" and labels requested/target VID as an inference.

This audit records the inconsistencies; it does not edit the paper or prediction ledger.

## Verification performed

Repository data were recomputed with the same `sweep()` loader and argmax definition used by
`analysis/claims_consumer.py`. The following required checks all passed before this record was
written:

- `python run_tests.py`: 792 checks across 23 suites.
- `python analysis/audit_claims.py`: 284 of 284 selected claims matched their configured sources.
- `python analysis/build_data_manifest.py --check`: 371 dataset-grade sweeps plus 3 verification
  sweeps reconciled with the paper.
- `python analysis/verify_citations.py --check`: no citation-coverage problems.

These passes do not resolve the source-selection and causal-interpretation issues described above.

## Repository sources opened

- [`data/frequency-sweeps/abba-20260908/README.md`](../../data/frequency-sweeps/abba-20260908/README.md)
  and its per-sweep JSON metadata.
- [`data/frequency-sweeps/repair-suite-p2-20260909/README.md`](../../data/frequency-sweeps/repair-suite-p2-20260909/README.md)
  and its per-sweep JSON metadata.
- [`data/frequency-sweeps/stock-bracket-20260909/README.md`](../../data/frequency-sweeps/stock-bracket-20260909/README.md).
- [`data/frequency-sweeps/5060ti-finefloor-20260918/README.md`](../../data/frequency-sweeps/5060ti-finefloor-20260918/README.md).
- [`data/frequency-sweeps/rtx3060-20260910/README.md`](../../data/frequency-sweeps/rtx3060-20260910/README.md).
- [`data/frequency-sweeps/rtx3070ti-suite-20260904/README.md`](../../data/frequency-sweeps/rtx3070ti-suite-20260904/README.md)
  and [`data/frequency-sweeps/rtx3070ti-20260825/README.md`](../../data/frequency-sweeps/rtx3070ti-20260825/README.md).
- [`data/frequency-sweeps/rtx2060s-20260912/README.md`](../../data/frequency-sweeps/rtx2060s-20260912/README.md)
  and [`data/frequency-sweeps/rtx2060s-finefloor-20260915/README.md`](../../data/frequency-sweeps/rtx2060s-finefloor-20260915/README.md).
- [`docs/AFTERBURNER-PROFILES.md`](../AFTERBURNER-PROFILES.md),
  [`docs/REGISTERED-PREDICTIONS.md`](../REGISTERED-PREDICTIONS.md), and
  [`docs/PAPER_DRAFT.md`](../PAPER_DRAFT.md).
- [`analysis/claims_consumer.py`](../../analysis/claims_consumer.py).
- [`2026-09-18-nvidia-voltage-quantisation.md`](2026-09-18-nvidia-voltage-quantisation.md).

## Remaining limits

No new hardware run was performed. No oscilloscope, board shunt, controller `READ_VOUT`, or direct
rail-voltage source was available. The audit can distinguish what the repository's design supports
from what its prose claims; it cannot identify the physical mediator from the existing telemetry.
