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

`0` = CLEAN · `1` = FLAGGED · `2` = UNSTABLE — so this can be driven from a batch script later.

---

## Output

Two files per run, named `<timestamp>_<label>_*`:

**`_samples.csv`** — one row per sample: timestamp, elapsed seconds, SM clock, memory clock, power
draw, temperature, GPU/memory utilisation, fan speed, memory used, throttle bitmask, and the decoded
throttle reasons.

**`_session.json`** — the run's metadata and summary: GPU identity, driver and VBIOS version, what
settings were applied, the verdict and its flags, and min/avg/max for clock, power and temperature.

Every sample is flushed to disk immediately rather than buffered. If the machine hard-locks, the
truncated log is the evidence — the last timestamp is roughly when it died.

---

## Verdicts

| Verdict | Meaning |
|---|---|
| `CLEAN` | Nothing went visibly wrong during the sampling window. |
| `FLAGGED` | Thermal or hardware throttling seen, or the run ended early. Not necessarily instability. |
| `UNSTABLE` | A display-driver crash/reset event, or telemetry queries started failing. |

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

**Not yet tested under real load, and the verdict logic for throttling and driver crashes has never
fired against a real event.** Until it has caught a deliberately-induced failure, treat the detector
itself as unvalidated. **The interactive Ctrl+C keypress path specifically has not been empirically
tested either** — it can't be simulated from a non-interactive shell, only reasoned through and
tested in its degraded form. First real run is the first real test of it.

Three bugs were found and fixed by smoke testing, all invisible on inspection:

- Throttle reasons were decoded through an `[ordered]` dictionary indexed by integer, which does a
  **positional** lookup rather than a key lookup in PowerShell. Every reason came back shifted by
  one — `0x1` reported as `ApplicationsClocksSetting` instead of `GpuIdle`.
- `| Select-Object -First 1` on the `nvidia-smi` call stopped the pipeline early, killing the process
  mid-write and producing a spurious exit code 255 on every otherwise-successful run.
- `[Console]::TreatControlCAsInput = $true`, added to fix the Ctrl+C behaviour above, itself threw
  "the handle is invalid" and crashed the whole script when no real console was attached. Now
  wrapped so it degrades to "no early-stop available" instead of failing the run.
