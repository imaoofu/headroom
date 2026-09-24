# Headroom Bench

Build-only implementation for the shop USB kit. Sync it with `tools/collection-kit/Sync-Kit.ps1`; the kit must already carry its Python environment and `HWiNFO64.exe`. On the shop PC, double-click `RUN-BENCH.bat` at the kit root and accept one UAC prompt. The app opens with Session D preselected. Drag rows to reorder, untick optional runs, double-click a row to edit its JSON, or add a custom sweep. The custom form asks for expected loaded core and memory ranges so it can witness the selected profile before measuring. Press Start. A yellow row differs from the shipped catalog, and the exact change is saved in the session JSON.

The window polls at 1 Hz and keeps measurement work in `Run-Plan.ps1`. Its controls are Start, Pause after step, Stop, and Continue for hands-on steps. The engine can also run without a window from an elevated PowerShell:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools\bench-app\Run-Plan.ps1 -PlanPath C:\absolute\plan.json
```

For a dry run, supply `-DryRun -MockPath C:\absolute\mock.json -SessionPath C:\absolute\session.json`. Dry runs use mocked telemetry and never call HWiNFO, Afterburner, or a GPU-setting command. The window also accepts `-DryRun -MockPath` for a UI rehearsal.

The app records `bench-plan-<stamp>.json`, `bench-session-<stamp>.json`, a state file, control file, and output text under the USB's `results` folder. A failed or interrupted session may be resumed when reopening the window or with `-Resume -SessionPath <existing session> -PlanPath <original plan>`. Completed steps in completed runs are skipped; an incomplete run starts again, with fresh log and sweep paths. Existing measurement files are never overwritten.

## Session D mapping to C0-C10

- C0 power/quiet gates, C1 kit resolution, C2 exact `1B08C2D0854460FF` profile hash, and C3 launching HWiNFO plus a Sensors-window confirmation are one preflight run.
- C4-C7 are the four 12-workload suites, with the worklist's labels, settings strings, iteration list, memory-clock witness and separate voltage logs. After C7, a 1.5% stock-return gate uses the same per-workload median absolute matched-target throughput change as `score_session_d.py`.
- C5 adds a **separate short HWiNFO log for the locked 1395 MHz voltage witness**. The original worklist asks the person to read voltage in the Sensors window before the suite log starts; an independent short log allows an auditable automated check without spanning profiles.
- C8 uses explicit `gemm` 120 iterations, equal to `gpu_workload.py`'s default, and the worklist's 1200-1590 MHz descending ten-point grid.
- C9 verifies 290/290/320 W and stock core/memory under load. The engine then resets clocks, stops logging, applies P1 and repeats the stock witness. Only after that does it ask the person to uninstall Afterburner and remove its Profiles folder. C10 is the instruction to bring back the USB; scoring stays on the local machine.

The app has **not** been live-tested on a GPU or on HWiNFO 8.52-6060. Its first live trial needs supervision on the local 5060 Ti, with a card-specific catalog. PowerShell 5.1 dry runs and parser checks are the verification path until then.

The Session D catalog limits custom sweeps to 405-2115 MHz, the SILENT-BIOS range recorded for this card. The engine checks those bounds again against the live supported-clock table before starting. A different card or BIOS needs its own measured bounds in its catalog.
