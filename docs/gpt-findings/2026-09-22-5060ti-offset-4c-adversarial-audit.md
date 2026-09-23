# Adversarial audit of the RTX 5060 Ti NVML offset result (Job 9)

2026-09-22. Read-only reanalysis of the three committed 4c sweep CSVs and voltage extracts in
`data/frequency-sweeps/5060ti-nvml-offset-20260922/`, against the **precollection** §6 in
`git show d0b9724:docs/REGISTERED-PREDICTIONS.md`. A1 and A2 used offset 0; B used −300 MHz.
Each arm contains 15 points from **one RTX 5060 Ti**, one `gemm` sweep per arm. Numbers below are
recomputed from those CSVs unless identified as registration or repository interpretation. No GPU
test was run.

## Verdict on the registered test

The narrow, observable prediction holds. B reports 0.720 V through **1245 MHz achieved**, then
0.730 V at **1290 MHz**; its floor boundary is bracketed by those points and contains the
registered ~1270 MHz. B is not flat across the whole tested band. A2 and A1 report the same VID at
all **15/15** targets; the largest A2/A1 throughput difference is **0.785%**, within the registered
~1% validity check. This is one session, not 15 independent replications.

The frequency pairing survives a different rule, but its precision must be described in **VID
codes**, not physical millivolts:

| Pairing rule | Comparable pairs | Result | Boundary |
|---|---:|---|---|
| Linear interpolation of A1 VID at B **achieved** clock +300 MHz | 8 | maximum absolute residual **2.02 mV** | B's ninth shifted point is 8 MHz beyond A1's highest achieved clock; do not extrapolate |
| Linear interpolation of A1 VID at B **target** +300 MHz | 8 | maximum absolute residual **2.26 mV** | B's ninth shifted target is 7 MHz beyond A1's highest target |
| Nearest A1 achieved clock to B achieved +300 MHz, restricted to the same 8 in-range points | 8 | **8/8 identical VID codes** | Nearest clock may miss the requested frequency by several MHz |
| Registered six-grid-step pairing, B point *i* against A1 point *i+6* | 9 | **9/9 identical VID codes** | Target clocks differ from an exact +300 by 0–8 MHz; achieved clocks by 0–9 MHz |

The six-step rule follows the registration's reason for choosing 50 MHz nominal spacing, although
the actual NVIDIA target grid is uneven. Only **3/9** target pairs are exactly 300 MHz apart.
Thus the README's “8 points” counts only interpolation inside measured A1 coverage, not every
six-step pair. These pairing choices do **not** change the pass/fail verdict. The interpolation
residuals of 1–2 mV are constructed between 5 mV VID codes; they are not a measurement of
sub-code agreement or of a 2 mV physical rail difference. The one-code tolerance is coarse: it
can accept neighboring codes, and the exact-code result under nearest/grid pairing is the
stronger description of this lookup data. The floor boundary itself is located only to the
**45 MHz gap** between the adjacent achieved B points, plus any unobserved transition within it.

## What the voltage evidence means

The experiment demonstrates that this card's **reported VID lookup** changes with locked core
frequency under the −300 MHz NVML P0 offset, and that its queried codes are consistent with
stock codes about 300 MHz higher on the curve over the overlap. It also shows that the lock still
held at the tested targets and that returning the offset to zero restored the observed A1 VID
sequence in A2.

The reported voltage is a coarse lookup, not sensed rail voltage (`CLAUDE.md`, voltage-grid and
load-test sections). The pairing therefore does **not** show equality of delivered voltage,
identical controller commands, physical rail response, or the whole electrical/machine state. It
cannot identify the exact implementation of the NVML shift, infer behavior at other offsets or
workloads, or establish a 300 MHz shift outside this measured band. The A2 return is evidence for
the read-back/reset and observed VID restoration, not a direct rail check.

## Was 4d superseded?

The **literal power-equality criterion is unsuitable**, but the broad validation question is not
fully answered by 4c. The criterion appears in `CLAUDE.md` at `059ce16` (2026-09-18), and in the
worklist at `de03ea1` (2026-09-20), which dates its design to 2026-09-09. It says power at locked
*f* with −300 should match power at *f*+300 without the offset. The wording does not describe a
same-frequency power comparison. The precollection 4c registration (`d0b9724`) calls 4d an
offset-validation pair,
then adds a separate VID precondition. The “4d superseded” conclusion first appears with the 4c
result (`9c1af3f`).

Across all **nine** six-step pairs, B power is **8.94–11.34 W lower** than A1 power. At the first
pair, B is **49.98 W at 1004.2 MHz**, A1 **60.34 W at 1295.2 MHz**, while both report 0.720 V.
Equal voltage requests at different operating frequencies give no reason to expect equal dynamic
power; other power components and measurement conditions also matter. Equality is not physically
*impossible* in every conceivable system, so “cannot hold” is too categorical. It is not a valid
prediction of a shifted V/F lookup, and its failure does not refute that lookup shift.

Consequently, it is reasonable to **retire 4d's stated power-equality test**, but not to say its
entire machine-state question was answered “directly” by VID pairing. If that wider question
matters, it needs a new, explicit matched-clock comparison of offset and a separately configured
curve, with reported VID, XBAR, throughput and power as distinct outcomes. That would still not
measure rail voltage without separate instrumentation. No such new test is specified or run here.

## XBAR across all 15 points

At the same target index, B XBAR exceeds A1 XBAR at **15/15** points, by **30–338 MHz**. A1 and A2
XBAR differ by at most **15 MHz** at the same index. For the **nine** six-step shifted pairs, the
XBAR residual B − A1(*i+6*) in MHz is:

| B target MHz | 1005 | 1057 | 1102 | 1155 | 1200 | 1252 | 1297 | 1350 | 1402 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| XBAR residual MHz | 0 | **+30** | −4 | −15 | −8 | +15 | −8 | −3.5 | 0 |

So **8/9** shifted-grid XBAR values agree within the A1/A2 control's maximum 15 MHz difference;
the 1057 MHz B point misses by 30 MHz. Interpolation at achieved +300 MHz gives **eight** in-range
pairs, with residuals from −21.1 to +22.8 MHz. The highest **six** B points have no A1 observation
at their +300 MHz position, so there is no across-all-15 shifted-XBAR validation. Within the
0.720 V B floor alone, XBAR rises **1245 → 1462 MHz** across six points. XBAR cannot be treated as
a function of the displayed VID code alone.

The data support a qualitative association of XBAR with the shifted curve configuration over
the measured overlap. “XBAR tracked where on the V/F curve the card sat, not the core clock” is
too categorical for one sweep and one offset: the 30 MHz exception, incomplete shifted coverage,
and absence of an XBAR intervention prevent a mechanism or mediation conclusion.

## Verification and limits

Source data: the A1, B and A2 `_sweep_voltage.csv` and `_sweep.csv` files in the directory above;
the registered design from commit `d0b9724`; history in `de03ea1`, `059ce16`, `9c1af3f`.
The nine-code pairing, interpolation residuals, power gaps and XBAR residuals were independently
recomputed from the extracts. The VID interpretation is from the repository's established
load-test and voltage-grid work, not independently verified by rail instrumentation in this job.

Before this archive write, `python run_tests.py` passed **925 checks across 28 suites**;
`audit_claims.py` passed **284/284** claims; the data-manifest, citation and measurement-hash
checks passed (**1,124** hashes). No data, paper, registration, GPU setting or runner was changed.
The result remains **N=1 chip, one A–B–A session, one workload, one offset**; VID and XBAR source
semantics beyond what the repository established were not independently instrumented here.

## Review by Claude, 2026-09-22 — accepted; three narrowings applied, verdict unchanged

**Recomputed here, all exact:** 9 of 9 six-step pairs report identical VID codes (target gaps 292–300
MHz); B draws 8.94–11.34 W less at all nine pairs; B's XBAR exceeds A1's at 15 of 15 points by
30–338 MHz; the shifted-pair XBAR residuals are 0, +30, −4, −15, −8, +15, −8, −3.5 and 0; A2 vs A1
XBAR differs by at most 15 MHz.

**Applied** in the 4c README, CLAUDE.md, the ledger (a correction under §6's result), HANDOFF,
ROADMAP, the worklist and RELATED-WORK §10:
1. "within 2–3 mV" → **identical VID codes at 9 of 9 pairs**. The millivolts were interpolation
   between 5 mV codes, and the data show a shifted lookup, not the delivered voltage.
2. 4d: "cannot hold as worded" and "answered directly" → **not a valid prediction: retire the test,
   but its machine-state question stays open.**
3. XBAR "tracked the operating point, not the core clock" → **associated with the shifted curve over
   the overlap**, with the one 30 MHz miss and no intervention stated.

🔑 **The pattern is worth naming: every overreach here was in the prose around a result that held.**
The registered test passed cleanly. The wording then outran it on the same evening, three times.
