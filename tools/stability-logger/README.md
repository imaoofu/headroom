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

## Protocol notes

Fill this in once a stress-test protocol is chosen, and then **do not vary it**. Consistency across
runs matters more than which test gets picked, because the whole point is comparing runs to each
other.

- Stress test and settings used: *(to be decided)*
- Duration per run: *(to be decided)*
- Warm-up period before logging starts: *(to be decided)*
- Ambient conditions to note: *(to be decided)*

**Always log a stock baseline for each machine before testing tuned settings.** A tuned result with
no stock comparison from the same chip measures nothing.

---

## Verified status

Tested on an RTX 5060 Ti (driver 610.88, VBIOS 98.06.4e.40.b4) — two short runs at idle. CSV and JSON
output confirmed well-formed; throttle-reason decoding confirmed correct against a known idle state.

**Not yet tested under real load, and the verdict logic for throttling and driver crashes has never
fired against a real event.** Until it has caught a deliberately-induced failure, treat the detector
itself as unvalidated.

Two bugs were found and fixed by that smoke test, both invisible on inspection:

- Throttle reasons were decoded through an `[ordered]` dictionary indexed by integer, which does a
  **positional** lookup rather than a key lookup in PowerShell. Every reason came back shifted by
  one — `0x1` reported as `ApplicationsClocksSetting` instead of `GpuIdle`.
- `| Select-Object -First 1` on the `nvidia-smi` call stopped the pipeline early, killing the process
  mid-write and producing a spurious exit code 255 on every otherwise-successful run.
