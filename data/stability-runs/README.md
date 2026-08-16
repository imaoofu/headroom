# Stability runs

Output of `tools/stability-logger/Log-GpuStability.ps1`. One CSV of per-sample telemetry plus one
JSON of session metadata and verdict per run.

Committed for the same reason the frequency sweeps are: an open, consistently-collected set of
consumer GPU stability results does not currently exist. Smoke-test output is excluded via
`.gitignore`; anything else kept here needs an entry below saying what it is and whether it is
dataset-grade.

## Before trusting any run

Read these three fields in the session JSON, in this order:

1. **`loaded_fraction`** — what share of samples had the GPU above 50% utilisation. **If this is
   low, nothing else in the file means anything.** A stress test that crashed or exited early
   leaves the card idle for the remainder, and the resulting averages look entirely ordinary.
2. **`verdict`** — `CLEAN` requires both "nothing went wrong" *and* "the card was actually loaded".
   `INCONCLUSIVE` means the second condition failed. See `tools/stability-logger/README.md`.
3. **`test_method`** and **`applied_settings`** — a run without these reconstructed later is close
   to worthless, and `applied_settings` is the one field nothing else can recover.

Prefer the `*_loaded_*` statistics over the whole-run ones. Whole-run averages blend load with idle
and describe neither.

## Runs

### `20260816-135029_5060ti-oc-llm-load` — first run under real load

**Not dataset-grade.** A tool-verification run, and it must not be pooled with protocol runs: the
locked protocol is OCCT GPU:3D Adaptive for 10 minutes, and this was 60 minutes of CUDA inference
(`qwen3:14b` under Ollama, driving an OpenCode session).

Recorded because it is the first time the logger has ever seen a non-idle GPU, and because it
exposed a defect in the logger itself.

| | value |
|---|---|
| Duration | 3601 s, 1760 samples, **0 telemetry failures** |
| Load pattern | one continuous 13-minute burst (0–778 s, 95% occupancy), then 47 min idle |
| SM clock under load | 2962–3000 MHz, held |
| Memory clock | 16301 MHz, zero variance |
| Power under load | 118 W avg, 139 W peak (limit 200 W) |
| Temperature under load | 58.5 °C avg, 64 °C peak |
| Throttling | none |
| Driver crashes | none |

**The overclock was stable under this load** — clocks held, no throttle events, no crash. The
applied settings were recorded *by observation* (SM 2970 MHz against ~2597 MHz stock sustained;
memory 16301 MHz against a 14001 MHz rated maximum), **not read from Afterburner. The exact offsets
are unrecorded and must be confirmed before this run is used for anything comparative.**

**This run's own verdict was wrong, and that is why it is kept.** It reported `CLEAN` with
`sm_clock_avg` 1699 MHz, `power_avg` 39.3 W and `util_avg` 24.9% — plausible figures that describe
neither the loaded period (2970 MHz, 118 W, 98%) nor anything else real, because 79% of the window
was idle. Nothing in the output distinguished *"survived an hour of load"* from *"the load died
after 13 minutes"*, which is exactly the event a stability tool exists to catch.

Fixed afterwards: `loaded_fraction` and loaded-only statistics are now recorded, and a run this
idle now returns `INCONCLUSIVE` rather than `CLEAN`. **This file predates that change** — it carries
`schema_version` 0.1.0 and has no `loaded_*` fields, which is precisely why this note exists. Under
the current code it would read `INCONCLUSIVE`.

It also established that **the `GpuIdle` throttle bit cannot be used to detect idleness**: the card
reported `0x1` on every sample while at 98% utilisation, because the driver reports `GpuIdle` for
compute-only work. See `tools/stability-logger/README.md`.
