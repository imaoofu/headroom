# Harness development runs, 2026-08-23

**None of these are stability results.** They are the runs that built and verified
`Invoke-StabilityProtocol.ps1`, kept because two of them are the evidence for claims now written
into that script's comments.

| run | what it was for |
|---|---|
| `difftest`, `reprotest` | isolating why the logger died when started by the harness — `Start-Process -ArgumentList` not quoting a settings string containing spaces |
| `smoketest` | the run that exposed the defect: a full six-minute load phase against a dead logger, which then reported `FLAGGED` from a process that never sampled anything |
| `negcontrol` | **evidence for the duty-cycle problem.** 25.0% of one-second samples below 50% utilisation, mean 75.1%, in a repeating pattern of ~8 loaded samples then ~2 idle |
| `dutycheck` | **evidence for the fix.** Same protocol with raised iteration counts: 3.1% below 50%, mean 95.2%, `loaded_fraction` 0.9686 |
| `verdictcheck` | confirming the telemetry verdict is read from the logger's `session.json` rather than its unreliable exit code |

## The defect these exist to document

The harness could not distinguish *"the telemetry says fine"* from *"there is no telemetry."* It
appeared three times in one afternoon, in three different forms:

1. The logger died on parameter binding and the harness ran a full load phase anyway, then read
   the dead process's exit code of `1`, mapped it through its own verdict table to `FLAGGED`, and
   printed a combined verdict. Had the code been `0` it would have said `CLEAN`.
2. After adding a start check, the exit code came back `$null` and `ContainsKey($null)` **threw**,
   discarding a complete four-minute run at the final step.
3. After guarding the null, the verdict degraded to `UNKNOWN` — and `UNKNOWN` **passed**, so a run
   with no readable telemetry verdict was reported `CLEAN`.

Fixed by reading the verdict from the logger's own `session.json`, and by treating `UNKNOWN` as
`INCONCLUSIVE` rather than as a pass. `Test-ProtocolCatchesDeadLogger.ps1` is the positive control
that holds all of this in place.

## Correction: these runs were on the SPLIT curve, not the original tune

Every `applied_settings` field in this folder says "original tune, memory +2500, core curve flat
~3010 MHz above ~925 mV". **That is wrong.** A locked-clock probe at 18:26 measured 2975.9 MHz
mean / 2977 max at a 3090 target with memory at 16301 — the split-curve signature. The original
tune reads ~2947 MHz, and that is what the 13:03 and 14:43 collection-kit sweeps actually recorded
earlier the same day.

So the configuration was changed at some point between 14:43 and 17:58 and the declarations were
written from a stale assumption rather than from a measurement. The operator corrected it; the
probe confirmed it.

The fields are left unedited, as everywhere else in this project. What they record is what was
declared at the time, and that is the point of them.

**This does not affect what these runs were for.** They exist to document a harness defect and a
duty-cycle measurement, neither of which depends on which V/F curve was loaded. The throughput
figures in them — gemm at 18.20-18.22 TFLOP/s — should be read as split-curve numbers, and are
consistent with the 18.22-18.24 that section 5.7.6 reports for that configuration.

**Third wrong configuration declaration in one day**, after `clocks.max.memory` was misread as
proving the memory offset absent, and after Instant Replay was said to have re-enabled itself.
Each was caught by measuring rather than by anyone noticing the declaration looked wrong. The
lesson is not that people are careless — it is that a declaration is a claim, and this project
already owns cheap probes that settle these in under two minutes:

    core clock at a locked 3090 target : ~2610 stock | ~2947 tuned | ~2977 split
    memory clock under load            : 13801 stock | 16301 at +2500

Run them before writing the field, not after being contradicted.

## `20260823-182730_ogtune_*` — an aborted run, and the label is wrong

Killed about four minutes in, so there is a partial `_samples.csv` and no `_session.json`, meaning
no verdict was ever computed. Do not treat it as a result.

**The label is also wrong.** It says `ogtune`; the card had the split curve applied, which is why
the run was stopped. Filed here rather than deleted so the aborted attempt stays visible, and
renamed to nothing - a file renamed after the fact is a file that lies about its own history.

The real run on this configuration is `20260823-183256_splitcurve_*`, in the parent directory,
correctly labelled and probed before it started.
