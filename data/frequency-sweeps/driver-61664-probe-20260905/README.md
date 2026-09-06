<!-- dataset-grade: no -->

# `driver-61664-probe-20260905` — one `gemm` sweep on driver 616.64

⚠️ **NOT DATASET-GRADE, and not a replicate.** One workload, one sweep, run to settle a
methodological question rather than to measure the card. Do not pool it with the r1–r6 suite.

**What it is.** 13-point `gemm` sweep, 1236–3090 MHz, stock, driver **616.64**, schema 0.3.3,
`baseline_util_pct` **18.8**, `max_baseline_allowed_pct` **99** — the guard was deliberately
overridden, which is why the run exists and why it is not dataset-grade.

---

## The question it answered

After the 616.56 → 616.64 update, `nvidia-smi utilization.gpu` reported an idle baseline of
**16–21%** on a machine whose Task Manager showed **0%** and whose desktop had not changed —
same apps, same MSI Afterburner running, same 240 Hz display as every earlier replicate. The
project's guard refuses above 10%, so r7 could not start.

**Two readings, opposite implications**: either the desktop had become a serious contaminant, or
the metric was overstating.

## The answer: the metric was overstating

Against r6's `gemm` leg (driver 616.56, same grid, same iteration count):

| | value |
|---|---|
| mean across 13 points | **+1.17%** |
| mid band ≤2010 MHz | **+1.75%** |
| points faster | **12 of 13** |
| worst point | −0.52% at 1852 MHz |

**Contamination makes runs slower. This one is faster**, and it is fastest exactly where §5.4.4
says competing load bites hardest. The achieved clocks settle it: identical to a tenth of a
megahertz at most points — 1537.0 vs 1537.0, 1695.0 vs 1695.0, 2002.0 vs 2002.0 — so no clock was
lost to a competitor.

🔑 **`utilization.gpu` is TIME-OCCUPANCY, not capacity** — the fraction of sampling windows in
which any kernel was resident. A compositor drawing at 240 Hz makes the GPU non-idle in nearly
every window while consuming almost none of it. This is a second face of §5.4.3's finding that
`utilization.gpu` decouples from real throughput; §5.4.3 saw it read *high* while throughput was
low under load, and this is the idle-side version of the same defect.

## ⛔ The elevated reading was TRANSIENT, and this README first said otherwise

**Added 2026-09-05, after a reboot.** The same machine, same driver 616.64, same 240 Hz desktop and
the same applications read **4% flat over ten samples** — back in line with the 3–4% of r1–r6. The
16–21% was **post-install settling work**, not a property of 616.64.

The first version of this file said the proxy "overstates on this driver". **That is withdrawn.**
What survives is narrower: `utilization.gpu` is an occupancy proxy, it *can* read high without
costing throughput, and the sweep above measured that directly on one occasion. Nothing here
licenses a general statement about how this driver reports utilisation.

🔑 **Operationally: if the baseline reads high, REBOOT AND RE-CHECK before raising any threshold.**
That would have resolved this in five minutes instead of an afternoon.

## The guard, and the bar it is not

⚠️ **The guard is right to exist** — it caught a 79% gaming session costing 8.03 → 4.84 TFLOP/s.

But it is the **backstop, not the bar**. CLAUDE.md's collection protocol requires a dataset-grade
sweep to run with the baseline *"stable and under ~5%"*; the tool refuses above **10%**. Those are
different numbers on purpose and **the protocol is the stricter one**, so raising the tool threshold
never makes a run acceptable — it only moves the automated floor. The protocol says as much
directly: *"A passing 10% guard is not enough; run 1 passed at 6% and still lost 10.3% at
1545 MHz."*

**This probe violated both** — 18.8% against a 5% protocol bar — which is exactly why it is filed as
not dataset-grade rather than as a replicate.

## ⛔ What this does NOT show

**It does not show that driver 616.64 is faster.** +1.17% sits inside this project's established
**~1.47% cross-session `gemm` drift** on one unchanged configuration
(`../memonly-gemm-20260829/README.md`). One workload on one day cannot separate a driver effect
from a different day. **Quote no driver conclusion from this run.**

That separation is what a full r7 suite is for: twelve workloads, same grid, same iteration counts,
against six replicates on 616.56.

## Correction recorded

The operator was asked to close applications and MSI Afterburner on the assumption that the raised
reading was contamination. It was not, and Afterburner was never the cause — closing it left the
reading *higher*. The environment had in fact been identical for r1–r6 all along. **The measurement
above was made because an attribution had already been made twice without one.**

## Related

`../suite-replicate-r6-20260905/` (the 616.56 counterpart this is compared against),
`../memonly-gemm-20260829/` (the cross-session drift figure that bounds what this can conclude).
