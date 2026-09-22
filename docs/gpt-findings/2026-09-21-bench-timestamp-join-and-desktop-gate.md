# Bench timestamp join and desktop-control gate — 2026-09-21

## Task and result

Raymond asked for the priority work in `docs/agents/GPT-BENCH-OPERATOR.md` during an unattended
hour, then asked that the correct MSI Afterburner curve be applied and whether HWiNFO could be
controlled directly. The brief's first priority was implemented: `Invoke-FrequencySweep.ps1` now
writes each benchmark's `window_start_unix` and `window_end_unix` to the sweep CSV, and
`join_hwinfo_voltage.py` automatically joins complete new sweeps to HWiNFO by those windows.
Old CSVs still use clock bins. A partially stamped sweep or an empty time window is refused.
This changes no committed measurement or historical voltage extract.

The unattended hardware work did **not** start. Native desktop control is available, but launching
HWiNFO from its installed app entry produced a Windows permission window titled
`HWiNFO(R) 64 is requesting your permission`. The computer-use safety rule prohibits acting on
that prompt. The operator must authorize HWiNFO before a future unattended session.

## Verification and provenance

- The benchmark already emits `timed_region_start_unix` and `timed_region_end_unix` in
  `tools/frequency-sweep/gpu_workload.py`; the sweep already reads those values for power
  windowing. The new CSV fields preserve those same values, including when sparse sweep power
  telemetry forces its average to fall back to the process window.
- A synthetic end-to-end test gives two targets the **same achieved clock** and different timed
  windows. The time join returns separate 0.700 and 0.800 V medians with two samples each. A
  wrong UTC offset returns nonzero and writes no extract. A second synthetic log written in the
  host's local time joins without an offset argument and records the inferred offset in the
  extract. Existing clock-join tests still pass.
- A read-only legacy regression check copied the 2026-09-09 stock sweep CSV to a temporary
  directory and rejoined its original HWiNFO log with the historical 25 MHz tolerance explicitly
  set. All 13 rows matched the committed voltage extract on target, voltage, crossbar, and sample
  count. The current default correctly refused that grid as contested; the explicit width
  reproduced the historical method. The temporary copy was removed, and `data/` was untouched.
- The new dated HWiNFO parser read **23 local raw logs, 38,273 samples total**, without a date or
  time parse failure, including after the UTC-offset provenance field was added. This verifies
  the formats present locally, not every HWiNFO locale.
- `python run_tests.py`: **835 checks across 24 suites, all passed**, using the project's Python
  3.12 executable. `analysis/audit_claims.py`: **284 of 284 claims verified**.
  `build_data_manifest.py --check` and `verify_citations.py --check` passed. The PowerShell
  sweep file parsed with zero syntax errors. These are software checks, not a hardware trial.
- The live Afterburner per-device profile store and the saved
  `data/afterburner-profiles/5060ti-profiles-20260918/` file had the same SHA-256,
  `E5CBE0ECD89D899C26748871FC9133DE40AC413776B5B7353144ED53F8C8B2CA`.
  The saved record identifies Profile 3 as stock. A read-only `nvidia-smi` check on 2026-09-21
  reported the RTX 5060 Ti at **200.00 W** versus a **180.00 W** default. That rules out the
  stock power limit being live; it does **not** identify which tuned profile is live.
- The installed `HWiNFO64.INI` already contained `SensorInterval=500`, the half-second interval
  required by the stock fine-sweep block. HWiNFO was not running when checked.
- `docs/AFTERBURNER-PROFILES.md` still said Profile 3 was verified only on disk. The
  2026-09-09 stock-bracket README and session JSON record its application probe at 11:38
  (200 → 180 W, 13801 MHz memory, 2640 MHz peak core). That stale warning was corrected in the
  guide with the old wording retained and dated; a repository search found no other copy of the
  obsolete application warning.

## Limits and next check

No curve was applied, no HWiNFO log was started, and no GPU sweep was run. Time joining has not
yet been verified against a newly collected HWiNFO log and sweep CSV. HWiNFO writes local
Date/Time without a time zone; the join uses the current computer's local zone by default and
accepts an explicit `--hwinfo-utc-offset` for logs collected elsewhere. The first hardware run
should check that the new CSV stamps fall inside the log and that each point receives samples.
The stamps bound the benchmark's wall-clock region, including short monitoring pauses, while the
throughput denominator subtracts those pauses. The brief's earlier claim that they describe the
exact active-work interval was corrected in place.

For the stock fine-sweep block in `docs/GPU-WORKLIST-5060TI.md`, apply the saved Profile 3 only
after the run is selected, then confirm the 180 W limit and stock memory clock. The slot contents
were verified on disk, but this session did not verify an application of that slot.

## Hardware-session preparation after the UAC block

`docs/agents/2026-09-21-5060TI-STOCK-FINESWEEP-PREP.md` records the exact 4i, 4b and 4h commands,
distinct HWiNFO log names, stock Profile 3 signature, and stop checks. Three `-DryRun` invocations
on the local RTX 5060 Ti exited successfully without changing GPU state: 4i selected 13 ascending
targets from 1380 to 1755 MHz, 4b selected the same 13 in reverse, and 4h selected 13 targets from
1530 to 1620 MHz. The three target-sequence previews omitted the workload command; a separate 4i
`-DryRun` also accepted the exact prepared GEMM workload string. None executes the benchmark, so
the full measurement path remained unverified on hardware. ✅ **2026-09-22 update (Claude):**
all 61 sweeps run that day time-joined — 775 points, none empty, minimum 13 samples. The live limit still read 200.00 W in
the previews. The planned 4c NVML offset write remains gated by its unexercised hardware path.
