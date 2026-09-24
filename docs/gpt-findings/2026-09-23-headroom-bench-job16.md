# Headroom Bench window fixes, Job 16

Job 16 in `docs/agents/GPT-PROMPT-NEXT.md` asked for four fixes found during the first local 5060 Ti live run. This record covers the code and dry runs only. The live-run account remains in the Job 15 finding and `tools/bench-app/README.md`.

The window now estimates finish from the current time and unfinished plan steps. Its pure display helper accounts for elapsed time, completed steps and resumed runs; it says when the current step has exceeded its estimate. Status appears as a `Status:` caption and one of the requested states, with the failure reason beneath it. Core, memory, power, temperature, utilization and logged voltage have fixed labels and units. The window still makes one `nvidia-smi` query per second.

The engine writes `finalState` to the session JSON after cleanup. It records the clock-reset command's SM clock read-back, checks the HWiNFO log button with the existing `-Status` helper and stops a log still running, and checks the processes it started for survivors. A survivor is killed and its PID recorded. The window displays the verified result or a red unresolved state. HWiNFO itself remains open.

Focused dry-run tests cover fresh and mid-run estimates, an hour-old first attempt after resume, an overrunning step, skipped steps, readings with missing fields, all eight status states, a log still running at final cleanup, and a log that cannot be stopped. Existing bench tests and the full repository suite were rerun under Windows PowerShell 5.1; the focused tests also ran under PowerShell 7. Every new PowerShell script parsed and remained ASCII-only.

No GPU-setting command, Afterburner profile, HWiNFO button, or live bench run was invoked for this job. The final `-Status` path and process-tree cleanup need Claude's supervised 5060 Ti live rerun to verify their Windows behavior. The pre-existing, uncommitted keep-awake change in `Run-Plan.ps1` was preserved. No commit or USB sync was made.

## Review by Claude, 2026-09-23 — accepted after one fix; live re-run pending

**Verified:**
- 24 of 24 bench tests pass, and every `.ps1` is ASCII.
- The keep-awake change committed earlier the same evening survives (lines 535 and 626).
- Only the `Run-Child` and witness processes are registered for the survivor check, so the
  final cleanup can never kill HWiNFO.
- The status strings the engine matches ("Logging is RUNNING." / "Logging is stopped.") are the
  ones `Invoke-HwinfoLogging.ps1` prints.

⛔ **Fixed: the final logging check would have failed every real session.** It captured the helper's
output with `2>&1`, but the helper prints with `Write-Host`, which PS 5.1 routes to the information
stream. **Run for real, that capture returned 0 lines; `*>&1` returned all of them.** So the check
would always have read "unknown" and marked a good session FAIL. The dry-run tests mock the call and
could not see it. Both helper calls now use `*>&1`, and "HWiNFO not running" is decided from the
process list rather than from printed text. Verified live with HWiNFO closed: it returns `stopped`.
The HWiNFO-open case is exercised by the live re-run.

The 5060 Ti test catalog's outputs were renamed (`20260923b`), because the app refuses to overwrite
the first run's files.
