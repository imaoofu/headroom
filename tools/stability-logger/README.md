# GPU Stability Logger

Records what a GPU actually did during a stress test, and writes a verdict plus a machine-readable
session record.

**Requires:** Windows, an NVIDIA GPU with drivers installed. Nothing else — no Python, no packages.
It calls `nvidia-smi`, which ships with the driver.

---

## Usage

```powershell
.\Log-GpuStability.ps1 -SessionLabel "build07-uv900" -AppliedSettings "900mV @ 2700MHz, mem +500" -TestMethod "OCCT 3D Adaptive" -DurationSeconds 900
```

The intended workflow:

1. Apply the clock/voltage settings you want to test, **by hand**, in MSI Afterburner.
2. Start this logger, telling it what you applied via `-AppliedSettings`.
3. Start your stress test — OCCT, FurMark, 3DMark, or a real game.
4. Let it run. It writes a verdict when the duration elapses.

### Parameters

| Parameter | Default | Notes |
|---|---|---|
| `-SessionLabel` | `unlabeled` | Short name; becomes part of the filename. |
| `-AppliedSettings` | *(warns if unset)* | What you set, in your own words. **Nothing can reconstruct this later.** |
| `-TestMethod` | *(warns if unset)* | What stress test is running alongside. |
| `-DurationSeconds` | `600` | How long to sample. |
| `-IntervalSeconds` | `1` | Seconds between samples. |
| `-OutputDirectory` | `..\..\data\stability-runs` | Where logs land. |

### Exit codes

`0` = CLEAN · `1` = FLAGGED · `2` = UNSTABLE · `3` = INCONCLUSIVE — so this can be driven from a
batch script later. `INCONCLUSIVE` is deliberately non-zero: a caller treating "not 0" as failure
will correctly stop on a run whose stress test died.

---

## Output

Two files per run, named `<timestamp>_<label>_*`:

**`_samples.csv`** — one row per sample: timestamp, elapsed seconds, SM clock, memory clock, power
draw, temperature, GPU/memory utilisation, fan speed, memory used, throttle bitmask, and the decoded
throttle reasons.

**`_session.json`** — the run's metadata and summary: GPU identity, driver and VBIOS version, what
settings were applied, the verdict and its flags, and min/avg/max for clock, power and temperature.

Since schema `0.2.0` it also carries **loaded-only statistics**, and those are the ones to read
first: `loaded_fraction`, `loaded_samples`, `sm_clock_avg_loaded_mhz`, `power_avg_loaded_w`,
`temperature_avg_loaded_c` and their min/max. Whole-run averages blend load with idle and describe
neither — on a 25-second test run that was only 23% idle, whole-run power read 135.91 W against
168.88 W actually drawn under load, a 24% understatement. Same failure the frequency sweep had
before it windowed power to the benchmark's timed region.

Every sample is flushed to disk immediately rather than buffered. If the machine hard-locks, the
truncated log is the evidence — the last timestamp is roughly when it died.

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `CLEAN` | Nothing went visibly wrong, **and** the card was genuinely loaded for most of the run. |
| `INCONCLUSIVE` | Nothing went wrong, but the GPU was under load for under half the samples. The run says nothing either way. |
| `FLAGGED` | Thermal or hardware throttling seen, or the run ended early. Not necessarily instability. |
| `UNSTABLE` | A display-driver crash/reset event, or telemetry queries started failing. |

**Why `INCONCLUSIVE` exists.** A verdict computed over an idle card is worthless in a way that looks
exactly like success. An hour-long run on 2026-08-16 finished its workload after 13 minutes and idled
for the remaining 47; the session reported `CLEAN` with `sm_clock_avg` 1699 MHz, `power_avg` 39.3 W
and `util_avg` 24.9% — all plausible figures, none describing the loaded period (2970 MHz, 118 W,
98%). Nothing distinguished *"survived an hour of load"* from *"the load died after 13 minutes."*

That is precisely the event this tool exists to catch: **a stress test that crashes leaves the GPU
idle for the remainder**, so the failure mode and the success signature were identical.

**A CLEAN verdict is not proof of stability.** Undervolt failures routinely take hours to appear, and
a single clean 10-minute run is weak evidence. Report it as "no failure observed in N minutes," never
as "stable."

---

## Non-goals, on purpose

**It does not apply GPU settings.** A script that sweeps voltage unattended can hard-lock or
destabilise a machine mid-test, and on a customer's build that is not an acceptable failure mode.
Automating the sweep is a decision to make deliberately later — not one to inherit by accident from
a logging tool.

**It cannot see a crash that takes the whole machine down instantly.** It infers one from a truncated
log, which is weaker evidence than a recorded event. The verdict says so when it happens.

---

## Protocol — locked 2026-08-14, do not vary without a real reason

Consistency across runs matters more than which test was picked. Every logged run should use this
exact setup; if it ever changes, note the date it changed and don't compare across the boundary.

- **Stress test:** OCCT, GPU:3D test, **Adaptive** mode, **Error Detection enabled**.
  Chosen over FurMark because modern NVIDIA/AMD drivers detect FurMark's constant artificial load
  and can throttle it specifically, making it less representative on current-generation cards.
  OCCT's Adaptive mode uses a variable, game-like load instead. Error Detection catches outright
  compute/memory faults - it does **not** expose GDDR7's error-correction retry counter (vendors
  don't publish it), so it cannot see "silently corrected, just slower." That failure mode still
  needs a separate benchmark-score comparison (same benchmark, 3 runs, tuned vs. stock) - OCCT
  answers "is it stable," not "is the memory OC actually faster."
- **Duration per run:** 10 minutes (600s, the script's default). Enough to reach thermal
  steady-state; still weaker evidence than an hours-long soak, and the tool says so in its own
  output. Report it as "no failure observed in 10 minutes," never as "stable."
- **Warm-up:** start OCCT first, then start the logger once OCCT is actually loading the GPU -
  a run whose GPU utilisation average comes back low almost always means the logger was sampling
  before the stress test actually kicked in.
- **Always log a stock baseline for each machine before testing tuned settings.** A tuned result
  with no stock comparison from the same chip measures nothing.
- **Change one variable at a time** in Afterburner between logged runs (core curve, memory, power
  limit are three separate variables) - a config that changes all three at once can't tell you
  which change did what.

---

## Stopping a run early

Press **Ctrl+C** in the window it's running in. It writes the verdict and session JSON for
whatever was collected up to that point, flagged as a user-stopped short run rather than a full one.

This works because the script deliberately intercepts Ctrl+C as a regular keypress instead of
letting PowerShell's default handling terminate the whole process — the default behaviour would
close the CSV safely but skip the verdict and JSON entirely, which is not what "stops early" should
mean. In a non-interactive context (a scheduled task, a redirected session — not your normal use),
that interception itself isn't available; the script detects that and says so, then simply runs to
its full requested duration instead of crashing.

## Verified status

Tested on an RTX 5060 Ti (driver 610.88, VBIOS 98.06.4e.40.b4) — four short runs at idle. CSV and
JSON output confirmed well-formed; throttle-reason decoding confirmed correct against a known idle
state; graceful degradation in a non-interactive shell (no console handle) confirmed working.

**Now tested under real load (2026-08-16).** One hour of sustained CUDA inference on an
overclocked card: 1760 samples, **zero telemetry failures**, clean exit, well-formed output. The
`INCONCLUSIVE` and `CLEAN` paths were then verified directly — an idle 20-second run returns
`INCONCLUSIVE` with exit 3, and a 77%-loaded 25-second run returns `CLEAN` with exit 0.

**Still never fired against a real failure.** The throttling path has not triggered (the card never
approached its limits — 139 W peak against a 200 W limit, 64 °C), and no driver crash has occurred,
so crash detection remains unvalidated. Treat the detector as unproven for the cases it exists to
catch. **The interactive Ctrl+C keypress path is also still untested** — it can't be simulated from a
non-interactive shell, only reasoned through and tested in its degraded form.

### The `GpuIdle` bit lies under compute load

Throughout that hour the card reported throttle bitmask `0x1` = `GpuIdle` on **every sample**, while
sitting at 98% utilisation and 139 W. The decoding is correct; the driver genuinely reports
`GpuIdle` for compute-only workloads that never touch the graphics pipeline.

**So the throttle mask cannot be used to tell whether the card is busy.** The loaded/idle split is
computed from utilisation percentage instead, which works for both compute and graphics loads. This
matters for the locked OCCT protocol too — a compute-mode stress test would look idle to anything
keying off that bit.

Three bugs were found and fixed by smoke testing, all invisible on inspection:

- Throttle reasons were decoded through an `[ordered]` dictionary indexed by integer, which does a
  **positional** lookup rather than a key lookup in PowerShell. Every reason came back shifted by
  one — `0x1` reported as `ApplicationsClocksSetting` instead of `GpuIdle`.
- `| Select-Object -First 1` on the `nvidia-smi` call stopped the pipeline early, killing the process
  mid-write and producing a spurious exit code 255 on every otherwise-successful run.
- `[Console]::TreatControlCAsInput = $true`, added to fix the Ctrl+C behaviour above, itself threw
  "the handle is invalid" and crashed the whole script when no real console was attached. Now
  wrapped so it degrades to "no early-stop available" instead of failing the run.
