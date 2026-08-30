# The first real instability this project has produced — 2026-08-30

An undervolt deliberately set past the edge crashed the display driver, and the stability
logger's crash detector was verified against it. Until this run every stability artifact in the
repository came from a session that went fine, and §3.5's classifier had never seen a genuine
hardware failure.

## What was applied

| | |
|---|---|
| Core | MSI Afterburner V/F curve, **875 mV pinned at 3000 MHz**, flattened at and above |
| Memory | **+2500 offset**, left applied from earlier |
| Power limit | 180 W, default |
| Intent | **Deliberately too low a voltage for 3 GHz.** Not a configuration under evaluation |

⚠️ **The `-AppliedSettings` string recorded in the samples file says the memory was untouched, and
that is WRONG.** It was written from `nvidia-smi --query-gpu=clocks.max.memory`, which reports the
stock maximum P-state clock and does **not** move with an Afterburner offset. The operator
corrected it, and this run's own telemetry settles it: **16301 MHz** at 12:36:12, against 13801
for stock under load. The right field is the achieved memory clock under load, which is what every
other README in this project uses. Recorded here because a settings string nothing verifies is the
failure this project keeps meeting.

## What happened, from the run's own samples

```
12:36:12   sm=1665  mem=16301  24.57 W  util=99   None
12:36:13   sm=2970  mem=16301  92.21 W  util=100  None
12:36:14   sm=2970  mem=16301  24.05 W  util=100  None     <- power collapses, util still 100%
           ... no samples for ~4 s: nvlddmkm 153 x4, then 14 ...
12:36:18   sm=1837  mem=14001  23.03 W  util=0    Unrecognised:0x0000000000000400
12:36:33   sm=2640  mem=13801  52.03 W  util=100  Unrecognised:0x0000000000000400
```

Three things are legible in that sequence and each is worth stating separately.

**The failure signature is a power collapse under sustained reported utilisation.** At 12:36:14 the
card still reports 2970 MHz and 100% utilisation while power falls from 92.21 W to 24.05 W. Work
had already stopped; the utilisation counter had not noticed. That is §5.4.3's finding — that
`utilization.gpu` decouples from throughput — appearing in a failure rather than in a measurement.

**The driver reset cleared the Afterburner offsets.** Memory reads 14001 at 12:36:18 and 13801
under load thereafter, both stock. The card reverted itself; the operator did not revert it. Any
run continued past this point would have been measuring stock silicon under a settings string
claiming an undervolt.

**A throttle bit appears at the crash and persists.** `0x0000000000000400` is absent before
12:36:14 and present on every sample after. The logger does not recognise it and says so rather
than guessing, which is the correct behaviour; what it means is not established here.

## 🔑 It crashed before the benchmark started

The workload process did not launch until **12:36:28**, fourteen seconds after the first
`nvlddmkm` error at 12:36:15. Nothing this project runs was on the GPU. Ordinary desktop
compositing — a browser, a chat client, Task Manager — was enough to boost the card to ~2970 MHz
at 875 mV and kill the driver.

That is worth keeping in mind when reading §3.5: a configuration this far past the edge does not
need a stress test to expose it, and a protocol that only looks during its own load window would
have missed the event entirely had it happened five minutes earlier.

## The detector was verified against it

The logger's `Get-DisplayDriverCrashEvents` was re-run over this run's window, unmodified:

```
crash events the detector returns: 11
  11 display-driver crash/reset event(s) in the Windows System log during this run:
  12:36:15 nvlddmkm id=153 (Error); ... 12:36:17 nvlddmkm id=14 (Error); ...
verdict that follows from crashEvents.Count -gt 0:  UNSTABLE
```

**This is the first time that path has fired on a real hardware failure.** The code's own comment
records the only previous occurrence as Error 153 caused by force-killing a CUDA process — "real,
but not the hard crash the bare wording implies". This one is the hard crash.

## ⛔ What is missing, and why

**There is no `_session.json` and no `_stability_protocol.json` for this run.** The operator saw
the crash and asked for the run to be stopped; both the protocol and the logger were killed before
either could write its verdict. The verdict above is reconstructed by running the real detector
function over the same event-log window, which is sound but is not the same as the tool having
emitted it.

`_samples.csv` is complete and covers the entire event, because the logger writes with
`AutoFlush = $true` specifically so a hard lock cannot take the last samples with it. That design
choice is what makes this record exist.

**One of the eleven events is not attributable to the card.** The 12:37:21 entry falls after the
kill and is consistent with the force-killed-CUDA-process cause the code documents. The ten
between 12:36:15 and 12:36:24 precede any intervention.

## Caveats

- **n = 1, and the crash was spontaneous rather than provoked at a known load.** This establishes
  that 875 mV at 3000 MHz is unstable on this card. It establishes nothing about where the edge
  actually sits, and no threshold should be quoted from it.
- The run was never completed, so there is no throughput data, no degradation measurement, and no
  loaded-fraction figure for this configuration.
- The protocol was at version 1.2.0. The stock baseline collected earlier the same day
  (`20260830-114549_stock-baseline-20260830_*`) was collected under 1.1.0, so the two are not
  formally comparable — though 1.2.0's changes affect only the failure path.
