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
