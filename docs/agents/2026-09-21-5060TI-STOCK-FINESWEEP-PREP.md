# RTX 5060 Ti stock fine-sweep session — prepared 2026-09-21

✅ **EXECUTED 2026-09-22** by Claude through `tools/hwinfo-logging/`, unattended — results in
`data/frequency-sweeps/5060ti-finefloor-20260922/`. Kept as the preparation record.

**Status as written 2026-09-21: prepared, not run.** HWiNFO is stopped behind a Windows permission prompt. Raymond
must approve that prompt before logging can be checked. No Afterburner profile was applied and no
sweep was started during this preparation. The live card reported a 200.00 W limit; stock Profile 3
must be applied and verified before a stock run.

The source protocol is [the 5060 Ti worklist](../GPU-WORKLIST-5060TI.md), with the command strings
in [the sweep queue](../5060TI-SWEEP-QUEUE.md). This sheet brings the 4i, 4b, and 4h commands
together with the boundary checks for one session. It does not authorize a 4c offset write:
that write has never been exercised on this card, and its result gates later experiments.

## Before starting

1. Approve HWiNFO's Windows permission prompt and confirm its sensor window opens. The installed
   `C:\Program Files\HWiNFO64\HWiNFO64.INI` already reads `SensorInterval=500`; verify the live
   logging interval remains 0.50 s. Do not use a log from another run.
2. Verify the installed per-device Afterburner profile store still matches the saved 2026-09-18
   snapshot (SHA-256 `E5CBE0ECD89D899C26748871FC9133DE40AC413776B5B7353144ED53F8C8B2CA`).
   The saved Profile 3 has 122 curve points, **zero** nonzero curve offsets, +0 core, +0 memory,
   and PL 100% = 180 W. Apply exactly
   `& "C:\Program Files (x86)\MSI Afterburner\MSIAfterburner.exe" -profile3 -q`, wait 6 seconds,
   then read
   `nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader`. Both values must
   be **180.00 W**. A historical application probe measured 13801 MHz memory under load; verify
   that stock memory signature during the new session rather than inferring it from the slot name.
3. Run `nvidia-smi pmon -c 5 -s u`. The baseline `sm` readings must be under about 5%, with `enc`
   and `dec` both zero. Stop if the screen capture or another process keeps the card busy.
4. Use one fresh HWiNFO CSV **per run**, start it just before the sweep, stop it after completion,
   and record its exact path. Keep the desktop idle while a sweep runs, including no screenshots or
   status polling. The sweep script resets clock locks in its cleanup path.

## Commands, in order

Run from an elevated PowerShell after HWiNFO logging is active. The sweep's completion banner
prints its exact CSV and JSON paths. Use these HWiNFO paths if the session runs on 2026-09-21:

| Run | New HWiNFO log path |
|---|---|
| 4i | `data/HWiNFO-Data/hwinfo-20260921-4i-stock-asc-050s.csv` |
| 4b | `data/HWiNFO-Data/hwinfo-20260921-4b-stock-desc-050s.csv` |
| 4h | `data/HWiNFO-Data/hwinfo-20260921-4h-stock-floorend-050s.csv` |

Use the actual session date in the filenames if the session starts later. Never append two runs to
one log. The three runs are estimated at roughly 15 minutes each, plus setup, boundaries, and
post-run checks.

```powershell
$py   = "C:\Users\Raymond\AppData\Local\Programs\Python\Python312\python.exe"
$repo = "C:\Users\Raymond\Documents\headroom"
$wl   = "$py $repo\tools\frequency-sweep\gpu_workload.py --workload gemm --json"

# 4i: ascending stock reference, 1380–1760 MHz, 13 points
& "$repo\tools\frequency-sweep\Invoke-FrequencySweep.ps1" -SessionLabel "5060ti-finefloor-gemm-asc-050s" -WorkloadCommand $wl -MinFrequencyMhz 1380 -MaxFrequencyMhz 1760 -FrequencyCount 13 -AppliedSettings "stock Profile 3, PL 180 W default, ascending order, HWiNFO 0.50 s"

# Stop 4i's HWiNFO log, check its CSV, then start a fresh log for 4b.
# 4b: documented descending command; confirm banner begins 1755, 1725, 1695.
& "$repo\tools\frequency-sweep\Invoke-FrequencySweep.ps1" -Descending -SessionLabel "5060ti-finefloor-gemm-desc" -WorkloadCommand $wl -MinFrequencyMhz 1380 -MaxFrequencyMhz 1760 -FrequencyCount 13 -AppliedSettings "stock Profile 3, PL 180 W default, DESCENDING order, thermal control for 4d"

# Stop 4b's HWiNFO log, check its CSV, then start a fresh log for 4h.
# 4h: documented floor-end bracket command.
& "$repo\tools\frequency-sweep\Invoke-FrequencySweep.ps1" -SessionLabel "5060ti-floorend-gemm" -WorkloadCommand $wl -MinFrequencyMhz 1530 -MaxFrequencyMhz 1620 -FrequencyCount 13 -AppliedSettings "stock Profile 3, PL 180 W default, floor-end bracket 1530-1620"
```

The commands above are an ordered reference, **not** a block to paste all at once. Start and stop
the matching HWiNFO log at each marked boundary. Stop the sequence if a run reports a driver reset,
a failed workload, clock-cap overshoot, missing timestamps, or a missing/inactive HWiNFO log.
Do not relabel uncertain data. After each run, check all 13 CSV rows for
`window_start_unix < window_end_unix`, `bench_ok`, and `power_window_applied`; then time-join that
run to its own HWiNFO log and confirm all 13 points receive samples. A synthetic test covers the
new join, but no newly collected hardware run has exercised it yet.

## Recorded pre-session state

On 2026-09-21 the card was identified as an NVIDIA GeForce RTX 5060 Ti. The installed per-device
profile file matched the saved snapshot by SHA-256. `nvidia-smi` reported **200.00 W current** and
**180.00 W default**; this does not identify which tuned slot was active. HWiNFO was not running.
The current state must be read again immediately before applying Profile 3.
