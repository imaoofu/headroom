# Headroom Bench

Build-only implementation for the shop USB kit. Sync it with `tools/collection-kit/Sync-Kit.ps1`; the kit must already carry its Python environment and `HWiNFO64.exe`. On the shop PC, double-click `RUN-BENCH.bat` at the kit root and accept one UAC prompt. The app opens with Session D preselected. Drag rows to reorder, untick optional runs, double-click a row to edit its JSON, or add a custom sweep. The custom form asks for expected loaded core and memory ranges so it can witness the selected profile before measuring. Press Start. A yellow row differs from the shipped catalog, and the exact change is saved in the session JSON.

The window polls at 1 Hz and keeps measurement work in `Run-Plan.ps1`. Its controls are Start, Pause after step, Stop, and Continue for hands-on steps. The engine can also run without a window from an elevated PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\bench-app\Run-Plan.ps1 -PlanPath C:\absolute\plan.json
```

The session finish estimate uses the current time and unfinished steps, including the current step's remaining estimate. On a resume it skips completed runs and recalculates from the new attempt. An overrunning step is labelled as such. The window shows labelled GPU readings and displays `finalState` checks for HWiNFO logging, clock reset and any surviving bench processes. A red line means cleanup could not verify a stopped state; the session JSON has the details.

For a dry run, supply `-DryRun -MockPath C:\absolute\mock.json -SessionPath C:\absolute\session.json`. Dry runs use mocked telemetry and never call HWiNFO, Afterburner, or a GPU-setting command. The window also accepts `-DryRun -MockPath` for a UI rehearsal.

The app records `bench-plan-<stamp>.json`, `bench-session-<stamp>.json`, a state file, control file, and output text under the USB's `results` folder. A failed or interrupted session may be resumed when reopening the window or with `-Resume -SessionPath <existing session> -PlanPath <original plan>`. Completed steps in completed runs are skipped; an incomplete run starts again, with fresh log and sweep paths. Existing measurement files are never overwritten.

## Session D mapping to C0-C10

- C0 power/quiet gates, C1 kit resolution, C2 exact `1B08C2D0854460FF` profile hash, and C3 launching HWiNFO plus a Sensors-window confirmation are one preflight run.
- C4-C7 are the four 12-workload suites, with the worklist's labels, settings strings, iteration list, memory-clock witness and separate voltage logs. After C7, a 1.5% stock-return gate uses the same per-workload median absolute matched-target throughput change as `score_session_d.py`.
- C5 adds a **separate short HWiNFO log for the locked 1395 MHz voltage witness**. The original worklist asks the person to read voltage in the Sensors window before the suite log starts; an independent short log allows an auditable automated check without spanning profiles.
- C8 uses explicit `gemm` 120 iterations, equal to `gpu_workload.py`'s default, and the worklist's 1200-1590 MHz descending ten-point grid.
- C9 verifies 290/290/320 W and stock core/memory under load. The engine then resets clocks, stops logging, applies P1 and repeats the stock witness. Only after that does it ask the person to uninstall Afterburner and remove its Profiles folder. C10 is the instruction to bring back the USB; scoring stays on the local machine.

✅ **Live-tested 2026-09-23 on the local RTX 5060 Ti** (Ryzen 9700X, driver 616.92), with
`catalog/localtest-5060ti.json`, launched by Raymond from `RUN-BENCH.bat` on the USB and ending
**PASS** after two resumes. It exercised, for real:
- the power, quiet-GPU and profile-hash gates;
- a Sensors confirmation step;
- Afterburner profile apply;
- a locked-clock witness reading **0.720 V** from HWiNFO;
- **HWiNFO 8.52-6060 logs started and stopped automatically**, eight times;
- a one-workload `Collect.ps1` suite (13/13 points);
- a 4-point descending sweep;
- resume twice;
- the cleanup revert and its stock witness.

It found four defects, all fixed the same evening:
- ⛔ **a CPU with integrated graphics adds a second "GPU Core Voltage" column**, and the reader failed
  every sample. The Ryzen iGPU read 0.725 V, inside the witness window, so picking it would have
  passed on the wrong GPU;
- ⛔ **PS 5.1 lost the child's exit code**, so a completed suite was reported as failed;
- the resume offer could pick a `.state.json` or `.control.json` sibling;
- a resumed session showed FAIL while running.

⚠️ **Still not tested live:**
- the drift gate;
- Stop in the middle of a suite;
- the manual HWiNFO fallback;
- the run-list chooser with several matching lists;
- **anything on a shop machine or on the 3070 Ti catalog itself**.

A shop machine may differ in ways this PC cannot show.

The Session D catalog limits custom sweeps to 405-2115 MHz, the SILENT-BIOS range recorded for this card. The engine checks those bounds again against the live supported-clock table before starting. A different card or BIOS needs its own measured bounds in its catalog.
