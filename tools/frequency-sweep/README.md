# Frequency Sweep

Builds a frequency-power-performance curve on real consumer hardware — the equivalent of the
public V100 dataset, measured on a card you actually own.

Two pieces:

| File | Role |
|---|---|
| `Invoke-FrequencySweep.ps1` | Locks the core clock to each of N frequencies and measures power, temperature, and achieved clock. |
| `gpu_workload.py` | Fixed-work GPU benchmark. Supplies the *performance* half of the measurement. |

---

## Why a separate benchmark exists

The sweep needs a performance number at every frequency. A fixed-**time** stress test (OCCT,
FurMark, Afterburner's bundled `gpu_stressor.exe`) cannot give one — it runs for N seconds no
matter how fast the card is. A fixed-**work** benchmark does identical arithmetic every run, so
duration *is* the performance metric and efficiency falls out as `work / (duration × power)`.

Without `-WorkloadCommand`, the sweep still produces a valid power-vs-frequency curve. It just
cannot compute efficiency, and it says so in its own output.

### Two workloads, deliberately

The V100 analysis found the efficiency-optimal frequency depends on whether a workload is
compute-bound or memory-bound — correlation **−0.666** between frequency sensitivity and optimal
clock. Reproducing that contrast on consumer hardware needs both:

- **`gemm`** — large matrix multiply via cuBLAS. Compute-bound, scales nearly linearly with core
  clock. Chosen over a homemade kernel because `GeMM` is one of the 33 workloads in the published
  V100 dataset, making the two directly comparable.
- **`membw`** — large elementwise stream over VRAM. Bandwidth-bound and much *less* sensitive to
  core clock. That contrast is the point.

  Measured, not assumed — and weaker than first claimed. Over a 2.2× clock range this card gives
  an elasticity of throughput to core clock of **≈0.35** for `membw` against **≈1.09** for `gemm`.
  So `membw` is strongly sub-linear but **not flat**: it gained 35% throughput for a 123% clock
  increase. At 1236 MHz the SMs cannot issue memory requests fast enough to saturate DRAM, so the
  workload is issue-limited there rather than bandwidth-limited. Earlier wording in this file and
  in `gpu_workload.py` called it "largely insensitive", which the data does not support.

---

## Usage

**Always dry-run first.** It changes no GPU state and prints the planned grid:

```powershell
.\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-first" -DryRun
```

Then, from an **elevated** PowerShell (clock locking requires administrator rights — the script
refuses to start otherwise rather than failing halfway through with the clock pinned):

```powershell
.\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-gemm" -WorkloadCommand "python tools\frequency-sweep\gpu_workload.py --workload gemm --json"
```

Run the benchmark standalone to sanity-check it first:

```powershell
python gpu_workload.py --workload gemm
```

### Key parameters

| Parameter | Default | Notes |
|---|---|---|
| `-FrequencyCount` | 13 | Matches the V100 dataset's grid size. |
| `-MinFrequencyPercent` | 40 | Floor as a % of max clock. See below. |
| `-SettleSeconds` | 8 | Wait after locking before measuring. |
| `-MeasureSeconds` | 20 | Telemetry window per point — **only** when no `-WorkloadCommand` is given. With a workload, sampling runs as long as the workload does. |
| `-SampleIntervalSeconds` | 0.5 | Telemetry period. Power is averaged over the benchmark's timed region only (~8–10 s), so this needs to be fast enough to leave a usable number of samples inside it. |
| `-DryRun` | off | Plan only, touch nothing. |

**On `-MinFrequencyPercent`:** consumer cards report absurdly low clocks as supported — an
RTX 5060 Ti offers 180 MHz against a 3090 MHz max, under 6%. Sweeping evenly from there wastes a
third of the run on frequencies that will never be efficiency-optimal and makes a fixed-work
benchmark crawl. The V100 dataset only swept 49–100% of its max and found its optimum at 62%. The
default of 40% keeps the grid where the answer lives.

---

## Measurement integrity

Two bugs were found by benchmarking the benchmark against known hardware limits, on an
RTX 5060 Ti. Both are fixed; both are recorded here because both produced data that looked
entirely ordinary and was wrong.

**1. Monitoring was inside the timed region.** The temperature check ran every 5 iterations
between the start and stop of the performance timer. An `nvidia-smi` call is a process spawn —
**42 ms** on this machine — so at `membw`'s 600 iterations that was 120 spawns, and *over half*
the measured duration was the GPU sitting idle waiting on a subprocess.

| | before | after |
|---|---|---|
| `gemm` | 15.60 TFLOP/s | **17.62 TFLOP/s** |
| `membw` | 204.83 GB/s | **414.23 GB/s** |

Both halves were measured back-to-back on the same machine state, so the before/after
comparison is sound and the `membw` figure roughly doubling is the real size of the bug.

> **Correction.** This table originally cited "92% of its 448 GB/s" as the sanity check that
> made the corrected `membw` number credible. That comparison was wrong: these runs were taken
> while a **memory overclock was still applied**, and 448 GB/s is the *stock* rating
> (14001 MHz × 128-bit). Measured later at stock memory, the same benchmark reaches
> 343.7 GB/s — 77% of 448 GB/s, a normal stream efficiency. The bug and its magnitude are
> unaffected; only the "92% of peak" gloss was, and it is recorded here rather than edited away
> because it is the same class of mistake as the ones this section exists to document —
> a plausible number that nobody checked the conditions of.

The check is now **time-based** rather than iteration-based (an iteration cadence polls more
often on a fast card than a slow one) and its subprocess time is measured and subtracted.
`duration_seconds` is work-only; `wall_seconds` and `monitoring_overhead_seconds` are reported
alongside it so the correction is auditable.

**2. Power was averaged over a wider window than performance.** The sweep sampled power for the
whole workload *process* while taking performance from the benchmark's internal timer — so the
average included **~2.3 s of Python import and CUDA init at idle**. Replicating the sweep's exact
sampling loop: `power_avg_w` recorded **124.77 W** against **148.52 W** actually drawn under
load, a **16%** understatement of a number that efficiency divides by.

The benchmark now stamps its timed region in epoch time (`timed_region_start_unix` /
`_end_unix`) and the sweep windows its samples to that interval, recording `power_window_applied`
and keeping the whole-process figure as `power_avg_process_w` for comparison. If stamps are
missing or fewer than two samples land in the window, it falls back to the process-wide average
and says so loudly rather than reporting a diluted number silently.

**Why this mattered more than the absolute error:** both were fixed wall-clock offsets, so each
shrank as a fraction of the run when the sweep locked the clock lower — and they tilted the
efficiency curve in *opposite* directions. Overhead-in-timer penalised high frequencies (pushing
the apparent optimum down); power dilution flattered them (pushing it up). Frequency-dependent
bias in duration or power is bias in the location of the efficiency optimum, which is the single
number this project exists to measure.

### Verified end-to-end (3-point sweep, RTX 5060 Ti, `20260815-233703_verify-3pt`)

| target | achieved | duration | throughput | power (windowed) | power (process-wide) |
|---|---|---|---|---|---|
| 1237 MHz | 1236 ✅ | 19.47 s | 6.78 TFLOP/s | 52.34 W | 47.83 W |
| 2167 MHz | 2942 ❌ | 7.57 s | 17.42 TFLOP/s | 162.91 W | 132.67 W |
| 3090 MHz | 2941 | 7.69 s | 17.16 TFLOP/s | 162.62 W | 133.81 W |

**Frequency response holds.** 2.38× the clock produced 2.57× the throughput, so fixed-work
duration does track core clock and the performance metric is real. (Slightly super-linear;
the low-clock point ran 19 s and was exposed to background desktop load for longer, which is
the likeliest explanation and a reason to sweep on a quiet machine.)

**The power-window fix is worth more than the static estimate suggested**, and in the predicted
pattern: it recovered 8.6% at 1236 MHz but **22.8%** at 2942 MHz, because a fixed ~2.3 s of CUDA
init is a larger share of a 7.6 s run than a 19.5 s one. Efficiency computed from the diluted
numbers reads 141.7 vs 131.3 GFLOP/J — a 7.9% gap. Corrected: 129.5 vs 106.9 GFLOP/J — a **21.1%**
gap. The bug would have understated the consumer headroom gap by more than half.

**Still unverified:** the `membw` half. That `gemm` is clock-sensitive is now measured; that
`membw` is *insensitive* — the contrast the whole compute-vs-memory-bound comparison rests on —
has not been swept yet.

**The 40% floor is too high on this card.** In the stock-curve sweep, efficiency was still rising at
the lowest frequency measured (128.5 GFLOP/J at 1236 MHz against 92.2 at sustained max boost). An
optimum sitting on the lowest point tested is the exact signature this project uses to disqualify
other consumer datasets. Lower `-MinFrequencyPercent` before claiming an optimum.

### ⚠️ A manual OC silently destroys a sweep

In that run `-lgc 2167` produced **2942 MHz** — the cap was not applied at all, overshooting by
775 MHz. Re-running the identical grid with the Afterburner curve reset to stock produced
**2143.8 MHz, held** (`20260815-234947_verify-3pt-stock`). Same script, same targets, one variable:
the flattened V/F curve (≈3010 MHz above 925 mV) is the cause, not merely consistent with it.
1237 MHz locked normally in both runs, being below the curve's ~1900 MHz floor where the override
does not reach.

The damage is not the one bad row. **Overshooting points collapse onto the same achieved clock**,
so a grid that reports N points delivers fewer, with duplicates quietly overweighting one
frequency. That 3-point sweep measured 2 distinct clocks. On a 13-point grid, the entire middle
of the range can vanish into one value while the CSV still looks complete.

The sweep now detects this: `lock_miss_direction` separates `above` (cap not applied — investigate)
from `below` (power/thermal limits — ordinary, and expected at max boost, where 3090 MHz honestly
runs at 2941). It reports distinct-clocks-measured against planned, and names the collapsed
targets. **Reset any overclocking utility to stock before a real sweep, and check
`distinct_clocks_measured` in the session JSON before using the data.**

---

## Safety

This is the first tool in the repo that **changes GPU state** rather than only observing it, so
the reset path matters more than the measurement.

- The sweep body is wrapped in `try/finally`; the finally **always** issues `nvidia-smi -rgc`,
  then reads the clock back and reports loudly if the reset did not take.
- **Ctrl+C is intercepted** rather than allowed to terminate the process, so stopping early
  unwinds through that same reset path instead of leaving the card pinned.
- **Clock locks do not survive a reboot.** If anything ever looks wrong, restarting returns the
  card to stock. That is the backstop.
- It refuses to run un-elevated, and warns when utilisation is low with no workload supplied —
  an idle sweep measures nothing.

`gpu_workload.py` is ordinary arithmetic, the same work any game or training run does. A compute
workload has no path to permanent hardware damage, and the card enforces its own thermal and power
limits underneath anything software requests. Additional rails regardless:

- Temperature ceiling polled every `--temp-check-seconds` (default 2 s) against `--max-temp`
  (default 88 °C), aborts cleanly.
- Finite, bounded iteration count. No infinite loops.
- VRAM freed on exit including on error, so repeated sweep points don't accumulate allocations.
- It never touches clocks, voltage, or power limits — only the sweep script does, and only through
  documented `nvidia-smi` calls.

If a run crashes the display driver, that is a **finding about stability at the applied settings**,
not damage. It is also exactly what the stability logger's verdict logic is built to catch.

---

## What the control APIs actually allow

Verified directly against an RTX 5060 Ti on driver 610.88 by dumping `nvml.dll`'s export table and
calling the API through P/Invoke — not assumed from documentation.

| Capability | Status |
|---|---|
| Lock core clock (`nvidia-smi -lgc`) | **Works.** Volta+; Blackwell qualifies. Needs admin. 389 discrete clocks supported, 180–3090 MHz. |
| Set power limit | **Works.** Adjustable 150–200 W on this card (default 180 W). Needs admin. |
| Per-P-state clock offsets (`nvmlDeviceSetClockOffsets`) | **Available.** Reads SUCCESS; graphics ±1000 MHz, memory −2000/+6000 MHz. Writes return `NO_PERMISSION` un-elevated — meaning the API works and wants elevation, not that it is unsupported. |
| Global V/F offset (`nvmlDeviceGetGpcClkVfOffset`) | **NOT_SUPPORTED** on this card. Closed on consumer Blackwell. |
| Read or write **voltage** | **Impossible via NVML.** Zero voltage exports across all 260 device functions. |
| Per-point V/F curve reshaping | Undocumented NVAPI only (`ClockClientClkVfPointsSetControl`). Out of scope — can break on any driver update. |

The voltage limitation is the honest constraint on this whole project: **the sweep measures
frequency versus power, not voltage.** Any write-up must say so plainly rather than describing
this as undervolting research.
