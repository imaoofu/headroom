# Suite replicate r3 — 2026-09-02

The third complete collection of the twelve-workload suite at stock, and the first one that makes
an **interval** possible rather than a difference. All twelve reached **13 of 13** planned
frequencies, every lock held, clocks reset cleanly. Collected in one sitting in 56 minutes by
`tools/frequency-sweep/Invoke-SuiteReplicate.ps1`.

r1 is `../stock-suite-20260829/` plus `../suite-pilot-20260829/`. r2 is
`../suite-replicate-r2-20260830/`.

## Why a third

`../suite-replicate-r2-20260830/README.md` closed by saying **"n = 2 gives a difference, not an
interval"**, and required that the third set be taken on a **different day** — because
`../memonly-gemm-20260829/` established ~1.47% cross-session drift on an unchanged configuration
against −0.05% same-session, so same-sitting repeats measure the smaller variance component and
would give intervals that are too tight.

r1 = 08-29, r2 = 08-30, r3 = **09-02**. Three days after r2, a separate power cycle, a separate
session.

## Configuration, verified rather than declared

| | |
|---|---|
| Card | Zotac RTX 5060 Ti Twin Edge OC |
| **Driver** | **616.56** — see the driver note below |
| Configuration | **STOCK** — 13801 MHz memory measured under load before collecting |
| Power limit | 180 W default, enforced |
| Precision | fp32, TF32 off |
| Baseline | encoder 0%, decoder 0%, GPU 3–4% over 8 samples / 24 s, VRAM 689 MiB, 42 °C |
| Grid | 13 points, `-MinFrequencyPercent 40`, targets 1237–3090 MHz |
| Iteration counts | `../../../tools/frequency-sweep/SUITE-ITERATIONS.md`, unchanged from r1 and r2 |

Every one of the twelve sweep JSONs records `encoder_util_pct` 0 and `decoder_util_pct` 0, so this
is a verified-quiet replicate rather than a declared-quiet one. Browsers, Discord, Spotify and
Wallpaper Engine were confirmed closed by process check immediately before launch, and no local
model server was resident — the preflight cannot see VRAM (`../../../ROADMAP.md`), so that was
checked by hand.

Drifted points: 2–4 per sweep, **all undershoot, zero overshoot**, at the top of the range where
maximum boost is a bin the card never actually holds.

## ⚠️ The driver differs between r1 and r2/r3, and not where anyone assumed

| replicate | date | driver |
|---|---|---|
| r1 | 2026-08-29 | **610.88** |
| r2 | 2026-08-30 | 616.56 |
| r3 | 2026-09-02 | 616.56 |

The update landed **between r1 and r2**, so r2/r3 are the driver-matched pair and r1 is the odd
one out. This was found only by reading the sweep JSONs; `CLAUDE.md` still records 610.88 as the
card's driver, which has been stale since 08-30.

**It does not explain the variance, and appears to run the wrong way.** Mean absolute gain
difference is **1.99 points for |r1−r2| (driver differs)** against **3.07 points for |r2−r3|
(driver matched)**. The driver-matched pair disagrees *more*. Nothing here should be attributed
to 616.56.

## 🔑 Result 1 — the deviation between trials, decomposed

This is what the third replicate buys, and the answer is not the one the project has been
assuming. Mean spread across r1/r2/r3, over all twelve workloads and thirteen frequencies:

| quantity | mean spread |
|---|---|
| throughput | **0.87%** |
| power | **2.07%** |
| efficiency (throughput per watt) | **2.08%** |
| reported efficiency gain | **4.40 percentage points** |

**Power is the dominant noise source, not throughput.** It reproduces 2.4× worse, and efficiency
tracks power almost exactly — 2.08% against 2.07% — because throughput noise is negligible beside
it. That is consistent with the paper's Limitation 4: power is a device-side, boxcar-averaged
estimate, not an external measurement.

**The gain spread follows arithmetically from that.** Gain is `100 × (peak_eff / ref_eff − 1)`.
Both terms carry ~2.08%, so their ratio carries ~2.9%, and multiplying by the ratio itself (~1.56
at the mean gain) predicts **~4.6 points**. Observed: **4.40**. The three trials agree; the metric
is simply noisy, and the amplification from power measurement to reported gain is roughly **5×**.

⚠️ **The ~0.76% figure this project quotes is THROUGHPUT reproducibility on `gemm`.** Every
efficiency result rests on power instead. Do not use 0.76% as an uncertainty on anything derived
from watts.

**A hypothesis tested and refuted while writing this up.** The reference point of the gain ratio is
the highest measured frequency, which is where the drifted points are, so it was expected to be the
noisiest term. It is the **least** noisy: 3090 MHz reproduces to 0.71% against 0.88% for every
other point averaged, and the worst point is 1237 MHz at 1.37%. The gain spread is not an artifact
of an unstable anchor.

## Result 2 — per-workload spread, which is what §5.5 needs

| workload | r1 | r2 | r3 | spread |
|---|---|---|---|---|
| `attention` | 55.6% | 56.2% | 56.4% | **0.9** |
| `conv` | 76.1% | 74.5% | 75.0% | 1.6 |
| `bgemm128` | 37.5% | 37.5% | 35.6% | 2.0 |
| `bgemm1024` | 61.0% | 58.7% | 58.5% | 2.5 |
| `layernorm` | 55.4% | 58.1% | 55.5% | 2.7 |
| `copy` | 51.3% | 51.3% | 47.2% | 4.1 |
| `softmax` | 65.6% | 65.0% | 70.3% | 5.3 |
| `reduce` | 40.4% | 37.3% | 42.6% | 5.3 |
| `gemm` | 58.1% | 57.3% | 52.8% | 5.3 |
| `bgemm32` | 76.6% | 73.5% | 71.2% | 5.4 |
| `bgemm64` | 81.1% | 73.0% | 77.8% | 8.1 |
| `bgemm256` | 41.8% | 44.4% | 34.5% | **9.9** |

Mean 4.40, median 4.68, max 9.89.

🛑 **No ordering of workloads by efficiency gain is supported across gaps smaller than about five
points.** The headline effect is untouched — every workload gains 34–81% and that is far outside
this noise — but a sentence ranking two workloads whose gains differ by three points is reading
noise.

## Result 3 — the optima are stable, and move by one grid step when they move

Seven of twelve sit at 1545 MHz in all three replicates. Five moved: `copy` (1545/1702/1545),
`softmax` (1545/1395/1545), `bgemm128` (1702/1545/1545), `reduce` held 1852 throughout, and `gemm`
(1395/1395/1702). Every movement is one grid step, and two of them return to where they started.

This is the third independent route to the same conclusion `../dense-grid-20260829/` reached: the
efficiency curves are flat near their peaks, so the argmax wanders with sampling. **Nothing here
should be read as a workload changing its preferred frequency.**

## What this does NOT establish

- **n = 3 is three points, not a distribution.** The spreads above are ranges over three
  measurements. They are the right order of magnitude for an interval and should not be quoted as
  a confidence interval.
- **One chip.** Everything here is the same physical 5060 Ti.
- **The monotone-looking drifts are not established as trends.** `softmax` reads 65.6 → 65.0 → 70.3
  and `gemm` 58.1 → 57.3 → 52.8, which look directional, but three points cannot distinguish a
  trend from noise and no claim is made that they are one.
- **The power-noise finding is from these three replicates only**, and power reproducibility may
  differ on another card, another driver, or another ambient temperature.

## A collection-tool defect found on the way

The first launch attempt **refused**, reporting a memory clock under load of 810 MHz — an idle
P-state — rather than 13801. The card was at stock throughout: a direct probe immediately
afterwards showed the clock reaching 13801 within 2.1 s of process launch, and the second attempt
passed the same check.

The preflight spawns `gpu_workload.py` and polls the memory clock 25 times at 400 ms, so its
window is **10 seconds from process launch** — which includes Python start-up, `import torch`,
CUDA init and a 3 GB allocation. On that attempt the page cache had just been thrashed by two
14.25 GB llama.cpp model loads and a 452-package npm reinstall, so a cold `import torch` plausibly
consumed the whole budget. That explanation is **inferred, not proven** — the failed attempt's
start-up was not instrumented.

**It failed safe.** The check cannot produce a false PASS from a short window; it can only refuse.
No data was collected on that attempt. But a false refusal will recur on any slow cold start, and
the fix is to poll until the clock rises rather than for a fixed count. Not changed here, because
a data-collection tool should not be edited between replicates of the same experiment.

## A naming collision worth knowing about

`bgemm64-r3` exists **twice** in this repository: this replicate's sweep, and
`../suite-replicate-r2-20260830/20260830-160225_5060ti-stock-suite-bgemm64-r3_sweep.csv`, which is
the third of four `bgemm64` repeats collected during the r2 session to characterise that one
workload. A recursive glob for `*-r3_sweep.csv` matches both. Analysis code should resolve
replicates by directory, not by tag.

Two further files elsewhere in `../` end in `-r3_sweep.json` from unrelated August runs
(`tuned-gemm-clean-r3`, `splitcurve-gemm-clean-r3`).

**And r1 cannot be globbed at all.** Its `gemm` sweep is named `stock-gemm-1237grid`, not
`stock-suite-gemm`, so a `*gemm*` pattern silently matches `bgemm1024` instead and produces a
plausible wrong number. It did, once, while this replicate was being analysed. Resolve r1 by an
explicit filename map.
