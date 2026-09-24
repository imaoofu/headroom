# Headroom Bench, Job 15

This builds the USB kit app requested in `docs/agents/GPT-PROMPT-NEXT.md` Job 15. It was a code and dry-run task. No GPU command, Afterburner profile, or HWiNFO control was run.

## Built

`tools/bench-app/RUN-BENCH.bat` requests one elevation and opens a Windows PowerShell 5.1 WinForms window. The window loads a preselected queue, lets the operator untick, edit, drag, or add a sweep, highlights changed rows, and writes the exact queue change into the plan. A custom sweep asks for loaded core and memory bounds, then verifies the chosen profile under load before measuring. The window shows current step, progress, estimated finish, one-second `nvidia-smi` telemetry, HWiNFO log path and latest voltage from its CSV, finished verdicts, and output. Pause, Stop, Continue, and window closing signal the headless engine.

`Run-Plan.ps1` validates plans, finds the kit by USB volume label, runs gates, applies profiles, checks loaded witnesses, starts and stops HWiNFO logs, invokes the existing `Collect.ps1` and sweep tool, and records each step. A failed gate or witness stops the queue. Cleanup resets clocks and reads back telemetry, stops logging, applies the revert profile, and runs its witness. Long suite and sweep work runs in a child process so Stop or a lost window can kill that process tree before the parent unwinds. The session, state, plan, control, and output files live under the kit's `results` directory. Resume restarts an incomplete run with fresh log and sweep paths; existing measurements are never overwritten.

The catalog generator and shipped `sessiond-3070ti.json` cover C0-C10 in `docs/GPU-WORKLIST-3070TI.md`: the 290/290/320 W SILENT-BIOS gate, quiet `pmon` gate, profile hash prefix `1B08C2D0854460FF`, all four 12-workload suites with the worklist's labels, settings and iterations, a descending ten-point 1200-1590 MHz fine sweep, stock return at 1.5%, and final three-way stock verification. `catalog/SCHEMA.md` defines the plan for later cards. `Sync-Kit.ps1` includes every runtime file.

Three intentional details differ from the literal hand-run sequence. C5 writes a separate short HWiNFO log for the locked 1395 MHz voltage witness, then a new log for the suite, so the voltage check has a saved reading without crossing profiles. C8 spells out `gemm`'s 120 default iterations. The instruction to uninstall Afterburner runs after the engine's final revert witness; uninstalling it earlier would make that safety check impossible.

## Verification

- PowerShell 5.1 and PowerShell 7 parsed every new `.ps1`; all new `.ps1` files are ASCII-only.
- Dry-run tests cover the full preselected queue, an edited preselected run and its session provenance, a failed gate, silent stock clocks after P3, manual HWiNFO fallback, a resumed failed suite, overwrite refusal, malformed plans, out-of-range sweeps, and UI startup. They use mocked telemetry and do not change GPU state.
- A saved 3070 Ti HWiNFO CSV confirmed that duplicate column names and footer rows need the dedicated tail reader. A separate growth test rejects a static CSV. Synthetic matched-target CSVs confirmed the 1.5% drift statistic, including achieved clocks different from targets. A `pmon` fixture checks that two processes at 3% each fail a 5% quiet gate.

The engine has not run live. HWiNFO 8.52-6060 button interaction, real Afterburner application, a clock lock, a physical Stop during a suite, and a sync to the actual USB kit remain unverified. A card-specific 5060 Ti catalog is needed before Claude's planned local trial. The window's controls opened in a timed dry run; visual layout on the shop PC has not been inspected.

## Review by Claude, 2026-09-23 — accepted after three fixes; still NOT run live

**Verified:** 17 of 17 tests pass and the full suite is green. Every `.ps1` parses and is ASCII. The
catalog matches the worklist on labels, iteration counts, the profile hash, the 290/290/320 W gate,
the P2 voltage witness and the drift limit. `Collect.ps1` gets `-NoPause`, so no hidden prompt can
hang a suite. The live view's three progress patterns match lines the tools really print. The
`gemm` default of 120 iterations held on 2026-08-27 and still holds. The startup
`--query-supported-clocks=graphics` query was run read-only here: 389 clocks, 180–3090 MHz, as
CLAUDE.md records. `$args` splatting in `Run-Child.ps1` works under 5.1 (tested); it is a style risk only.

**Fixed at review:**
1. ⛔ **The memory witness would have stopped Session D at its first check.** It required
   9450–9550 MHz, but loaded memory on this card reads **9251 at 186 of 192** committed points
   (9501 at 6). The floor is now 9200. The worklist carried the same error ("memory 9501"), written by
   Claude, and is corrected too.
2. **The stock core ceiling was 1820 MHz**, 35 above the 1785 peak in the committed data, and it
   guards nothing, since no profile raises the top of the curve. Now 1900.
3. ⛔ **After Stop or a closed window, the revert was applied but its witness always failed.** The
   witness polls `Check-Control`, which re-read the Stop that caused the cleanup and threw. So the card
   would be reverted but never verified, and the record would always report a failed cleanup.
   **The dry-run tests could not see it:** the dry witness skips the polling loop. Cleanup now ignores
   the control file, and a human step during cleanup is recorded as a warning instead of waited for.
   The warning field was checked by hand on a new record, on a resumed JSON record without the field,
   and on one that already had it.

**Still unverified:** everything live. A card-specific 5060 Ti catalog is needed before the first
real run here.

## First live run, 2026-09-23 — PASS after four more fixes

Raymond launched it from the USB on the local 5060 Ti with `catalog/localtest-5060ti.json`, and
Claude read the session record after each attempt. **HWiNFO 8.52-6060's log button was driven
automatically, eight times.** That was the largest unknown. Two resumes were needed and both
worked. Four defects surfaced, none of which the dry-run tests could reach, and each was fixed and
re-run:
- ⛔ a second "GPU Core Voltage" column from the CPU's integrated graphics made the reader fail on
  every sample. **The iGPU read 0.725 V, inside the witness window.** Two tests were added; the
  first fails on the old code;
- ⛔ PS 5.1 lost `ExitCode` because `Handle` was read late, so a suite that completed 13/13 was
  reported as failed. Reproduced in isolation;
- the resume offer matched the session's `.state.json` and `.control.json` siblings;
- a resumed session kept status FAIL while running.

🔑 **Every one of them was invisible to dry runs**, because the dry path mocks exactly the parts that
broke: the CSV reader on a real multi-GPU log, and a real process exit. **That is why the live run
was required before any shop use.** Not yet tested live: the drift gate, Stop mid-suite, the
manual HWiNFO fallback, and anything on a shop machine.
