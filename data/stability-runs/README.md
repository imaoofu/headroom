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

## ✅ Inventory gap closed, 2026-09-12

**Recorded 2026-09-11 as "the list below names one run, the directory holds six".** Every run now
has an entry. Smoke-test output is gitignored and is deliberately not listed; what follows is
everything this directory actually commits.

| run | dataset-grade? |
|---|---|
| [`20260816-135029_5060ti-oc-llm-load`](#20260816-135029_5060ti-oc-llm-load--first-run-under-real-load) | no — tool verification |
| [`20260823-183256_splitcurve`](#20260823-183256_splitcurve--split-region-curve-under-protocol-v100) | **yes** |
| [`20260823-192719_ogtune`](#20260823-192719_ogtune--original-tune-under-the-same-protocol) | **yes** |
| [`20260830-114549_stock-baseline-20260830`](#20260830-114549_stock-baseline-20260830--stock-under-protocol-v110) | **yes** |
| [`20260830-123609_uv-875mv-3ghz`](#20260830-123609_uv-875mv-3ghz--the-real-driver-crash) | no — a deliberate failure, see `README-uv-875mv-3ghz-20260830.md` |
| `harness-development-20260823/` | no — own README |
| `logger-selftest-20260820/` | no — own README |

---

## 🔑 Read this before reading any throttle column here

**Two of these runs carry a throttle bit the logger could not decode, and it went uncounted until
2026-09-12.** The mask is `0x400`. Measured across this repository:

| driver | sweeps | carrying `0x400` |
|---|---|---|
| 610.88 | 102 | **0** |
| 616.56 | 82 | **82** |
| 616.64 | 151 | 38 |
| 616.92 | 32 | 29 (and 8 also carry `0x200`) |

**It arrived with a driver update.** Zero occurrences on 610.88, every single sweep on 616.56.

⛔ **What `0x400` and `0x200` mean is NOT known, and nothing here guesses.** The decoder now reports
them as `Unknown:0x400` rather than naming them. Misnaming a throttle reason is a defect this
project has already had once, when an `[ordered]` dictionary indexed by integer did a positional
lookup and shifted every reason by one.

⚠️ **They are recorded and flagged, NOT escalated.** `0x400` covers 589 of 603 samples in a stock
baseline that is healthy by every other measure, so treating it as trouble would turn every recent
run red and teach the reader to ignore the verdict.

🔑 **The older bug was worse than "cannot name it": a mask MIXING known and unknown bits dropped
the unknown part silently.** `0x604` decoded as `SwPowerCap` with the `0x600` gone without trace.
Fixed 2026-09-12, and `unknown_throttle_samples` enters the session JSON at schema `0.3.0` —
**runs before that have no such field and cannot be audited for it**, though the raw masks are in
their samples CSV.

---

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


### `20260823-183256_splitcurve` — split-region curve under protocol v1.0.0

**Dataset-grade.** The first real stability run in this project, and the evidence behind
`CLAUDE.md`'s "the split curve passed its first stability run". Driver 610.88, VBIOS
98.06.4e.40.b4, power limit 200 W.

**The configuration was PROBED immediately before starting, not assumed** — core clock at a locked
3090 target read 2975.9 MHz mean, the split signature (the original tune reads ~2947, stock ~2610),
and memory under load read 16301 MHz, confirming the +2500 offset. That probe is why this run can
be compared to anything.

| | value |
|---|---|
| Duration | 1830.4 s of 1830 requested, 1765 samples, **0 telemetry failures** |
| Iterations | **33, zero aborted** |
| Verdict | `CLEAN`, `loaded_fraction` **0.9688** |
| SM clock, loaded | 2992.6 MHz avg, 3015 max, 1102 min |
| Power, loaded | 140.2 W avg, **196.1 W peak against a 200 W limit** |
| Temperature, loaded | 64.6 °C avg, 79 °C peak |
| Post-soak drift | `gemm` **−0.110%**, `membw` **+0.158%** |

⚠️ **`throttled_samples` is 0, and that is not the same as "nothing throttled".** 15 of 1765
samples hit `SwPowerCap`, which the logger classes as normal rather than as the card protecting
itself. The paper said the unqualified version until 2026-08-24.

**Say "no failure observed in thirty minutes", never "stable."** The 2% degradation threshold was
set before anyone knew what healthy drift looks like.

### `20260823-192719_ogtune` — original tune under the same protocol

**Dataset-grade, and the other half of a matched pair.** Forty minutes after the split run, same
card, same evening, same protocol version — which is what makes the two comparable at all. Probed
the same way: 2948.1 MHz mean at a locked 3090 target, memory 16301 MHz.

| | value |
|---|---|
| Duration | 1830.7 s, 1765 samples, 0 telemetry failures |
| Iterations | **33, zero aborted** |
| Verdict | `CLEAN`, `loaded_fraction` **0.9683** |
| SM clock, loaded | 2968.4 MHz avg, 3000 max, 2925 min |
| Power, loaded | 139.4 W avg, 193.3 W peak |
| Temperature, loaded | 64.1 °C avg, 78 °C peak |
| Post-soak drift | `gemm` **+0.104%**, `membw` **−0.283%** |
| `SwPowerCap` samples | **14 of 1765** (the split run's 15) |

🔑 **These two runs do NOT distinguish the configurations on steadiness.** All four drift figures
land between −0.283% and +0.158%, which is well inside anything this protocol can resolve. What the
pair does establish is that the split curve's `gemm` advantage reproduces under a different
protocol: **+1.41% here against +1.53% from locked sweep peaks**, agreeing to 0.12 points.

⚠️ **And the split curve's `membw` advantage vanishes at free boost** (−0.44%), because the plateau
is a property of 1402–1867 MHz and a boosting card sits at 2968–2993 MHz, above it. Do not quote
§5.7.2's −29.6% as a cost paid in normal use.

### `20260830-114549_stock-baseline-20260830` — stock under protocol v1.1.0

**Dataset-grade.** The control taken 50 minutes before the deliberate undervolt failure below.
Stock verified rather than assumed: no Afterburner offsets, `clocks.max.memory` 14001 MHz.
Driver **616.56**, the first run in this directory on the newer driver.

| | value |
|---|---|
| Duration | 630.9 s of 630 requested, 603 samples |
| Iterations | **10, zero aborted** |
| Verdict | `CLEAN`, `loaded_fraction` **0.9403** |
| SM clock, loaded | **2597.0 MHz avg**, 2752 max |
| Power, loaded | 140.3 W avg, 183.9 W peak |
| Temperature, loaded | 63.2 °C avg, 75 °C peak |
| Post-soak drift | **none computed** — 10 iterations against a 3-minute soak left no comparable window |

🔑 **589 of its 603 samples carry the undecoded `0x400` bit** described above. Nothing else about
the run looks unusual, and its 2597 MHz loaded mean matches the ~2584 MHz stock boost measured by
sweep, so this is recorded as a gap in the TOOL rather than a finding about the card.

⚠️ **`power_limit_w` reads 200 W in the session JSON while `applied_settings` says "180 W
default", and both are correct.** The field is `power.max_limit` — the highest limit settable —
not the limit in force. The sweep tool learned to record both as `power_limit_enforced_w`; the
logger has not, so read the enforced figure off `applied_settings` here.

### `20260830-123609_uv-875mv-3ghz` — the real driver crash

**NOT dataset-grade — a deliberate failure, and the only real one this project has recorded.**
875 mV pinned at 3000 MHz. Full account in `README-uv-875mv-3ghz-20260830.md`, which this list did
not link until 2026-09-12.

⛔ **There is no `_session.json` and no `_stability_protocol.json`.** The operator stopped the run
on seeing the crash, so the tool never wrote a verdict — the `UNSTABLE` verdict on record was
reconstructed by re-running the detector over the same event-log window. Sound, but not the same as
the tool having produced it. What makes the record exist at all is `AutoFlush = $true` in the
logger: `_samples.csv` covers the whole event, all 53 samples.

**The timeline, read straight off the samples:**

| t | SM clock | util | power | throttle |
|---|---|---|---|---|
| 3.3 s | 2970 MHz | 100% | **92.21 W** | None |
| 4.3 s | 2970 MHz | 100% | **24.05 W** | None |
| *4.3 → 8.4 s* | *— no samples —* | | | |
| 8.4 s onward | 1837 → ~2580 MHz | | ~180 W | **`0x400` on every remaining sample** |

🔑 **The undecoded bit appears at the first sample after the reset and never clears — 48 of 53
samples.** That is a second, independent signature of the driver reset, and nothing used it at the
time because nothing could read it. It corroborates the existing account rather than contradicting
it: the card came back at ~2580 MHz and ~180 W, which is stock at the factory default power limit,
consistent with the reset having cleared the Afterburner offsets.

⚠️ **n = 1, and the crash was spontaneous rather than provoked at a known load** — it crashed
fourteen seconds BEFORE the benchmark process launched, on desktop compositing alone. It
establishes that 875 mV at 3000 MHz is unstable on this card and **nothing about where the edge
sits. Quote no threshold from it.**
