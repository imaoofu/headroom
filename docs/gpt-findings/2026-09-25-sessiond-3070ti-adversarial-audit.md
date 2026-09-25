# Session D on the RTX 3070 Ti: adversarial audit before Session D2

This 2026-09-25 audit checks the one-chip Session D collection in
`data/frequency-sweeps/rtx3070ti-sessiond-20260924/` against
`docs/REGISTERED-PREDICTIONS.md` §§4a–4b and 8, including both §4 amendments.
The original §4a text predicted an *upward* floor extension, while the
precollection runsheet and amendment registered the *downward* 1170/1275 MHz
test that actually ran. The as-built 4b control has a 263 MHz dose, short of
the original ≥300 MHz, and lowers the 825 mV curve point by 15 MHz. These are
precollection deviations recorded in the ledger, not discoveries that can
change the scoring now. [The runsheet](../../data/frequency-sweeps/rtx3070ti-20260825/SESSION-D-RUNSHEET.md)
and [profile snapshot](../../data/afterburner-profiles/3070ti-profiles-20260923/README.md)
give their provenance.

## Independent calculation and registered results

I read the 72 suite sweep CSVs and their 72 `_voltage.csv` extracts directly.
For each valid point I computed `bench_throughput / power_avg_w`, selected each
workload's maximum on its **target** grid, and took the median of 12 workload
optima. For Edit 2 I replaced its six clipped high targets (1590–2115 MHz) by
one bin whose efficiency is the median of their six efficiencies, then scored
that bin as 1500 MHz. This is separate scratch Python, not a call to
`score_session_d.py`. Stock return is the largest, across workloads, of the
median absolute matched-target throughput percentage change. I then ran the
committed scorer only to compare outputs.

| Registered test | Recomputed result | Registered verdict | Difference from scorer |
|---|---:|---|---|
| Eligibility: stock-1 → stock-4 | Both medians 1485 MHz; worst workload return 0.619% against 1.5%; floor checks pass | Valid | None |
| 4a, Edit 1 (`edit1-2`) | 1222.5 MHz | **PASS**, inside 1170–1275 | None |
| 4b, Edit 2 (`edit2-3`) | 1432.5 MHz | **FAIL**, outside 1485–1500 | None |
| Joint 4a/4b | Control also moved | **Attribution fails on this chip** | None |
| 8a eligibility: stock-4 → stock-6 | Both medians 1485 MHz; worst return 1.192% against 1.5%; Edit 1 floor check passes | Valid | None |
| 8a, Edit 1 (`edit1-5`) | 1170 MHz | **PASS** | None |
| 8b, Edit 1 fine floor | 1230 MHz reads 0.819 V; 1275 reads 0.838 V | **FAIL**. A point above 1215 MHz remains in the ≤0.825 V band | No separate scorer verdict; agrees with registered result |
| 8c, stock ascending/descending fine pair | Descending minus ascending mean +0.0019%, range −0.057% to +0.104% | Exploratory, no verdict | Agrees with reported +0.00% rounded |

The stock floor spans the sampled 1485 and 1590 MHz targets; Edit 1's suite
grid spans 1170 and 1275. Edit 2's six clipped targets all remain at or below
0.825 V under load, with a per-target median achieved upper clock of
1514.25 MHz. The independent per-target median summary matches the scorer.
All three stock suite medians are 1485 MHz. This is **one chip and one Session D
collection**, with two Edit 1 suites but one Edit 2 control suite. The passing
Edit 1 results cannot establish floor-region attribution after 4b failed.

## Is 4b's failure a median artifact?

It is a real registered failure. Edit 2 has six workload optima below
1485 MHz and six at 1485/1500. The sorted middle pair is 1380/1485, yielding
1432.5 MHz. Identical stock suites have the same 1485 median, but their
per-workload argmaxes change in 4 of 12 workloads from stock-1 to stock-4,
and 3 of 12 from stock-4 to stock-6.

As a sensitivity calculation, I allowed each workload to take any of its
three observed stock optima independently and enumerated all `3^12 = 531,441`
labelled combinations. **13,122 combinations (2.47%, exactly 2/81) have a
1432.5 median**; the other 518,319 have 1485. In the actual three complete
stock suites, **0 of 3** medians leave 1485–1500. The 2.47% is conditional on
independent workload draws from just these three runs. Shared thermal or time
effects violate that assumption, and n=3 stock suites on n=1 chip cannot
calibrate a probability of 4b's outcome under a null. It does show that one
more low optimum at the middle of this distribution moves the median by half
a grid step. It does **not** authorize re-scoring 4b.

## Which curves moved?

The table compares Edit 2 efficiency at fixed targets with the mean of the
stock-1 and stock-4 efficiencies at the same target. The displayed values
come from whole curves, not only their argmaxes. All three suites achieved
exactly 1380 and 1485 MHz at the displayed points.

| Workload | Optimum stock-1 / Edit 2 / stock-4, MHz | Edit 2 efficiency at 1380 | At 1485 | Reading |
|---|---|---:|---:|---|
| `bgemm128` | 1380 / **1275** / 1485 | −4.15% | −3.04% | 1275 gains +4.58% against the stock pair; its 190.09 W is below 196.96/199.67 W stock. |
| `conv` | 1485 / **1380** / 1485 | +2.30% | −1.51% | 1380 rises and 1485 falls. |
| `gemm` | 1485 / **1380** / 1380 | +1.49% | −0.61% | Both changes matter; stock-4 already prefers 1380. |
| `copy` | 960 / **1170** / 1065 | +3.89% | −3.08% | Low optimum moves upward but remains below the median boundary. |
| `reduce` | 855 / **1065** / 855 | −1.72% | −1.50% | Its 1065 point gains +2.85%; it also remains below the median boundary. |
| `layernorm` | 1275 / **1275** / 1485 | +1.84% | −3.59% | 1275 gains +4.51%; stock itself changes its argmax. |

Across these six workloads at 1380 and 1485, Edit 2's throughput differs
from the stock-pair mean by −0.82% to +0.58%, recorded power by −4.68 to
+9.50 W, and temperature by −0.55 to +1.50 °C. Every achieved clock equals
its target. The efficiency changes are driven mostly by the recorded power
denominator at these points; the temperature differences do not follow one
common direction.

For `conv` at 1380 MHz, Edit 2 records 13.258 TFLOP/s and 171.22 W,
against stock-1/stock-4 at 13.205/13.158 TFLOP/s and 174.44/173.85 W.
At 1485 its throughput is also slightly higher, 14.056 against
13.995/13.956 TFLOP/s, but power is 184.08 against 183.10/177.51 W. Its
temperatures are 57.5 °C at 1380 and 57.8 °C at 1485, within 0.4 °C of the
stock observations. For `gemm`, Edit 2's 1380 power is 168.54 W against
173.22/167.06 W stock; 1485 power is 184.56 W against 183.20/181.88 W.
Its temperatures differ by at most 0.4 °C at those points. These records
implicate the measured power/throughput ratio, not an obvious achieved-clock
or temperature shift, but do not isolate why power changed.

The control's 1485 MHz **sensed voltage code is not always the stock code**.
For `conv` it is 0.812/0.819/0.812 V in stock-1/Edit 2/stock-4; for `reduce`
it is 0.819/0.812/0.819. `bgemm32` differs from stock-4 and `bgemm64`
differs from stock-1 by one 0.007 V displayed step. The other eight workloads
have the same displayed code across all three suites at 1485. These are
sensor readings, not proof of a changed physical rail. Together with the
known −15 MHz edit at 825 mV, they prevent calling Edit 2 a clean
above-floor-only intervention. The CSVs cannot attribute the control's move
specifically to that 825 mV edit, to another part of the curve, or to
run-to-run power variation.

Edit 1's two passing medians also conceal different shapes: `edit1-2` has
**2 of 12** workload optima at 1590 MHz; `edit1-5` has **5 of 12** there.
The latter is still a registered median pass, not a uniform movement of all
workloads. The second suite is on the same chip and in the same session.

## What 8b and the planned 8d repeat can settle

The 8b fine sweep directly places Edit 1's floor end **between 1230 and
1275 MHz**, rather than at the 1200 MHz as-built reading. The suite grid has
1170 then 1275 and cannot resolve 1230. Thus 8b refutes the literal
floor-end prediction and weakens a detailed mechanism story. It does **not**
alter 4a or 8a eligibility or verdicts: their precommitted bins are
1170–1275, their 1170 point remains in the floor band, and 1275 is above it.
The separate local HWiNFO 1395 MHz witness log contains 69 loaded samples,
all at 0.850 V; 1395 is not itself on the fine sweep grid. That raw log is
Git ignored, so a checkout without it can verify 8b's decisive 1230 point
from the committed extract but cannot recheck the witness.

The planned Session D2 order, stock-7 → edit2-8 → stock-9, can test whether
the **same Edit 2 median move repeats on this same chip on another day**, with
an adjacent stock bracket. Its stock-7 = 1485 MHz eligibility rule is a
defensible strict check against the registered baseline: all three Session D
stock suites satisfy it. It may rule out a usable run after a day change, and
a 1485 suite median alone does not prove every workload curve is unchanged;
the registered stock-9 and 1.5% per-workload return gates add protection.
The rule should remain as registered. A passing 8d cannot retroactively turn
4b into a pass; a failing 8d would show the control move twice. Neither result
isolates the lowered 825 mV point, removes the as-built dose shortfall, or
supplies a second chip. No Session D2 sweep directory was present at this
audit's read.

## Import, joins, and record limits

All **72 suite sweeps** have 13 measured points, driver 617.14,
290/290/320 W power limits, `ok` workload verdicts, zero recorded
encoder/decoder use, and baseline utilization at most 3.4%. I found no
missing or duplicate suite targets. Every suite extract agrees with its
sweep CSV on achieved clock, throughput, power, memory clock, and both
benchmark window timestamps; all have at least 16 HWiNFO samples per point
and record UTC offset −07:00. Independently reading the locally retained raw
HWiNFO CSVs and taking in-window medians reproduces **all 936 suite points
and 43 fine points** in voltage, crossbar, and sample count: **0 of 979
disagreements**. This checks the output of the joins, not the accuracy or
physical provenance of HWiNFO's voltage sensor. The raw logs are Git ignored
and were available on this machine at audit time.

One README sentence needs tightening: its opening says that six suites and
four fine sweeps were collected from the 2026-09-24 Headroom Bench plan.
**One of those four**, `fine/finefloor-desc`, is the 2026-09-23 C8 shakedown,
as the README itself correctly discloses in its run table. Thus the folder's
76 sweeps comprise **75 from Session D and one earlier sweep**. The 8c
same-session comparison uses `finefloor-asc2` and `finefloor-desc2`, not C8.
I found no other import or join discrepancy. The Edit 1 fine sweep's 7.0%
starting baseline is already disclosed in the README; its effect on that
voltage observation has not been independently isolated.

The registered outcomes remain 4a PASS, 4b FAIL, 8a PASS, 8b FAIL, and 8c as
exploratory. On **n=1 chip**, the negative control prevents a floor-region
causal attribution. The audit used read-only data and scorer comparisons;
it did not run hardware or edit `data/`, the paper, or the registration.

## Claude's review, 2026-09-25: accepted

Re-derived here from the committed data, not taken on the audit's word:
- **The 2.47% sensitivity result:** 13,122 of 531,441 combinations give a 1432.5 MHz median, and
  the rest give 1485.
- **The curve-level changes:** `conv` +2.30% at 1380 and −1.51% at 1485; `bgemm128` −4.15% and
  −3.03%. The last differs from the audit's −3.04% by rounding.
- **The voltage codes at 1485 MHz:** `conv` reads 0.812/0.819/0.812 V and `reduce`
  0.819/0.812/0.819 V; **8 of 12** workloads carry the same code in all three suites.
- **The Edit 1 argmax shapes:** 2 of 12 at 1590 MHz in `edit1-2`, 5 of 12 in `edit1-5`.

**Applied:** the Session D README's opening sentence now says the 76 sweeps are 75 from Session D
and C8 from the day before.

**One reading this review adds.** The control's per-workload moves come through the power
denominator at unchanged clocks, and they are a few watts (`conv` at 1380: 171.2 W against 174.4
and 173.9 W). That is the size of the run-to-run power variation this project measures (2.07%,
§5.4.5). It fits what Session D2 showed the next day, when the control held its median. **It is an
interpretation, not a test, and it changes no verdict.** 4b stays FAIL, and 8d is NOT SCOREABLE
because its grid moved (`data/frequency-sweeps/rtx3070ti-sessiond2-20260925/`).
