# Frequency sweeps

Output of `tools/frequency-sweep/Invoke-FrequencySweep.ps1`. One CSV of per-frequency rows
plus one JSON of session metadata per run.

These are committed for the same reason the stability runs are: the measurements *are* the
contribution. Published consumer DVFS datasets sweep at or above stock and structurally cannot
locate an efficiency optimum (see commit `14b4c46`), so open data that sweeps below stock is the
thing this project has to offer. Smoke-test output is excluded via `.gitignore`; anything else
kept here needs an entry below saying what it is and whether it is dataset-grade.

## Before trusting any run

Check `distinct_clocks_measured` against `frequencies_planned` in the session JSON, and
`lock_miss_direction` per row in the CSV:

- `none` — the lock held.
- `below` — the card could not sustain the requested clock (power/thermal). Ordinary, and
  expected at the top of the range, where max boost is a bin no card actually holds.
- `above` — **the clock cap was not applied at all.** nvidia-smi cannot exceed its own cap, so
  something outside it owns the V/F curve. Overshooting points collapse onto the same achieved
  clock, so the run yields fewer distinct frequencies than the row count suggests, with
  duplicates quietly overweighting one frequency.

Reset any overclocking utility to stock before collecting data intended for the dataset.

## Runs

### `20260815-234947_verify-3pt-stock` — first usable sweep

Same 3-point grid, Afterburner reset to stock. All three targets locked or undershot honestly, so
this measured **3 distinct frequencies**. Baseline utilisation 3.6%, no throttle flags at any point.

| Target | Achieved | Throughput | Power | Efficiency |
|---|---|---|---|---|
| 1237 MHz | 1235.9 MHz | 6.68 TFLOP/s | 51.97 W | 128.5 GFLOP/J |
| 2167 MHz | 2143.8 MHz | 12.21 TFLOP/s | 107.44 W | 113.6 GFLOP/J |
| 3090 MHz | 2617.6 MHz | 15.40 TFLOP/s | 167.03 W | 92.2 GFLOP/J |

It also settled the cause of the previous run's lock failure. `-lgc 2167` gave 2942 MHz with the
flattened curve applied and 2143.8 MHz with it reset — same script, same grid, one variable. The
V/F override is the cause, not merely consistent with the symptom.

**Two findings, both provisional at three points on one unit:**

1. Efficiency falls monotonically with frequency; the lowest point measured is **39.4% more
   efficient** than sustained max boost. Same direction and comparable magnitude to the V100's
   44.4%, and a lower bound rather than an estimate — the optimum was bracketed, not located.
2. **The 40% sweep floor is too high.** Efficiency is still climbing at 1236 MHz, which is exactly
   the signature this project uses in commit `14b4c46` to disqualify other consumer datasets. The
   floor needs lowering before any optimum is claimed here.

Still only `gemm`. `membw` has never been swept, so the compute-vs-memory-bound contrast that the
two-workload design exists to test remains untested.

### `20260815-233703_verify-3pt` — TOOL VERIFICATION, NOT DATASET

Three-point sweep run to verify the benchmark measures anything real. It does, and the run is
kept as evidence, but **it is not dataset material and must not be pooled with real sweeps.**

What it established: fixed-work duration tracks core clock (2.38× the clock gave 2.57× the
throughput), so the performance metric is valid. It also quantified the power-window fix on live
data — 8.6% recovered at 1236 MHz against 22.8% at 2942 MHz, confirming the bias was
frequency-dependent rather than a constant offset.

Two reasons it is not dataset-grade:

1. **An MSI Afterburner profile was active**, with the V/F curve flattened at ~3010 MHz above
   925 mV. `-lgc 2167` was overridden to 2942 MHz. `-lgc 1237` held, being below the curve's
   ~1900 MHz floor where the override does not reach. So 2 of 3 targets landed on the same
   clock and the run measured **2 distinct frequencies, not 3**.
2. **It predates the detection columns.** This CSV was written by the version of the script
   before `lock_miss_direction`, `lock_miss_mhz`, `power_avg_process_w` and
   `distinct_clocks_measured` existed. The columns that would flag problem 1 are absent from the
   file itself, which is precisely why this note exists.

Background desktop load (Wallpaper Engine, browser, Discord, Spotify) was also present at ~6%
baseline utilisation — under the script's 10% guard, but not a quiet machine.
