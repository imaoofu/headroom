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
