# Session B — SILENT BIOS with voltage telemetry

**Purpose: test a prediction this repository recorded before the measurement existed.**

Session A measured SILENT throughput but ran HWiNFO only in the **OC** position, so there is no
voltage log for SILENT. §5.5.1 attributes the OC BIOS's +23.11% matched-frequency power draw to
voltage on the strength of an inference. This session turns that into a measurement.

> At fixed frequency and fixed work, dynamic power goes as V². If the whole gap is voltage, the
> SILENT floor should sit at **0.819 / √1.2311 = 0.738 V**.

**Both outcomes are publishable and one of them is bad for the paper. Decide nothing after the
fact:**

| SILENT floor reads | Conclusion |
|---|---|
| **near 0.738 V** | Mechanism confirmed. §5.5.1 stops being an inference. |
| **near 0.819 V** (same as OC) | Voltage does **not** explain the power gap. §5.5.1 needs rewriting. |
| anything else | Report the number. Do not fit a story to it. |

---

## 0. Before you touch anything

- [ ] **Confirm which BIOS position the card is actually in.** It was *returned* to SILENT after
      Session A, but the last sweeps of that session ran in OC, so verify rather than assume:

      nvidia-smi --query-gpu=vbios_version,power.limit,power.default_limit,power.max_limit,clocks.max.graphics --format=csv,noheader -i 0

      **Expected for SILENT:** `94.04.5a.00.91, 290.00 W, 290.00 W, 320.00 W, 2115 MHz`
      If it reads `94.05.5a.00.bd` / 310 / 310 / 350 / 2190 it is still in **OC** — shut down
      fully, flip the switch, power back on, and re-check. Do not flip a running machine.

- [ ] **Turn NVIDIA Instant Replay OFF, and check it again before *each* of the three sweeps.**
      Not once per session. On 2026-08-23 it read 0% before one run and a sustained 14% forty
      minutes later in the same session because someone switched it back on.
      `NVIDIA app > Settings > Instant Replay > OFF`. Also OBS replay buffer, Discord/Steam
      recording, Xbox Game Bar.

- [ ] **Close everything heavy.** The sweep refuses above 10% baseline utilisation and names the
      offending process. Note the guard reads *utilisation only* — it cannot see a process merely
      holding VRAM, so also check `nvidia-smi` shows memory near idle.

- [ ] **Do not touch the customer's clocks, voltage, fan curve, or Afterburner profile.** This
      session changes nothing but the BIOS switch, and that goes back where it was found.

- [ ] Copy `F:\headroom-kit` to the machine's own drive — e.g. `C:\headroom-kit`. Session A ran
      from `C:\headroom-kit` and the workload paths below assume it.

---

## 1. Start HWiNFO first

Portable HWiNFO 8.52-6060 from the kit folder. **Sensors-only mode, nothing installed.**

- [ ] **Set the polling interval to 500 ms.** Session A ran at 2000 ms by mistake and got only
      5–10 loaded samples per grid point — enough for a median, thin for anything else. 500 ms
      gives ~4× that. The two sessions will differ in sample density; that does not affect a
      median but must be stated when they are compared.
- [ ] Start logging to CSV **before** the sweep and stop it **after**. One log per sweep, named to
      match — `hwinfo-silent-gemm-matched2130.csv`, etc.
- [ ] Confirm all four columns are present, by name, in the NVIDIA sensor block:
      `GPU Core Voltage [V]`, `GPU Clock [MHz]`, `GPU Crossbar Clock [MHz]`, `GPU Power [W]`.
      They were all present on this machine in Session A, crossbar included.

---

## 2. The three sweeps

Elevated PowerShell. **Sweep 3 is the one that tests the prediction** — if time runs short,
protect that one.

Common workload path (as used in Session A):

```powershell
$WL = "C:\headroom-kit\python\python.exe C:\headroom-kit\tools\frequency-sweep\gpu_workload.py"
```

### Sweep 1 — `gemm`, matched grid (~15 min)

Same band and point count as the OC `matched2130` run, so the two are directly comparable.

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -SessionLabel "rtx3070ti-silent-gemm-matched2130-hwinfo" -WorkloadCommand "$WL --workload gemm --json" -MinFrequencyMhz 852 -MaxFrequencyMhz 2130 -FrequencyCount 13 -AppliedSettings "gigabyte rtx3070ti gaming oc rev2.0, SILENT BIOS (VBIOS 94.04.5a.00.91, 2115 MHz bin, 290 W enforced). Grid 852-2130 matching the OC matched2130 runs. HWiNFO running at 500 ms for voltage capture."
```

### Sweep 2 — `membw`, same grid (~15 min)

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -SessionLabel "rtx3070ti-silent-membw-matched2130-hwinfo" -WorkloadCommand "$WL --workload membw --json" -MinFrequencyMhz 852 -MaxFrequencyMhz 2130 -FrequencyCount 13 -AppliedSettings "gigabyte rtx3070ti gaming oc rev2.0, SILENT BIOS (VBIOS 94.04.5a.00.91, 290 W enforced). Grid 852-2130 matching the OC matched2130 runs. HWiNFO running at 500 ms."
```

### Sweep 3 — `gemm` fine, 1200–1600 MHz ⭐ **the prediction test**

Same band as the OC fine sweep on purpose. The OC floor was read from ten consecutive points here;
this is the directly comparable measurement. (SILENT's own coarse efficiency optimum is 1380 MHz —
inside this band, so it brackets correctly.)

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -SessionLabel "rtx3070ti-silent-gemm-fine" -WorkloadCommand "$WL --workload gemm --json" -MinFrequencyMhz 1200 -MaxFrequencyMhz 1600 -FrequencyCount 10 -AppliedSettings "gigabyte rtx3070ti gaming oc rev2.0, SILENT BIOS (VBIOS 94.04.5a.00.91, 290 W enforced). FINE sweep 1200-1600 MHz, same band as the OC fine sweep, to read the voltage floor. HWiNFO running at 500 ms."
```

**New this session:** the tool now records `power_limit_enforced_w` and `power_limit_default_w`.
Confirm all three appear in each session JSON — SILENT should give **290 / 290 / 320**. Session A
could not source its enforced limit from any committed file; this closes that.

---

## 3. Joining the voltage logs

Back on the analysis machine:

```bash
python tools/frequency-sweep/join_hwinfo_voltage.py <sweep.csv> <hwinfo.csv> --min-power 120
```

**Choose the threshold from the data, not from the OC session, and not from which answer it
gives.** The point of the filter is to drop idle samples between grid points, which sit at boost
voltage and would drag the medians up.

Measured in Session A, SILENT `gemm` loaded power ran **129.9 – 277.1 W** across the coarse grid
(OC ran 164.3 – 296.4 W, which is why 120 was right there). So:

- **120 W is a good starting point and anything above ~125 W will start discarding the real
  852 MHz point.** Do not raise it past that.
- The join prints `n` per point and an `X of Y samples are above N W and kept` line. **Every point
  should report n ≥ 5.** A `(no samples)` row or a sudden drop in `n` means the threshold is too
  high.
- If in doubt, run it at 30 and at 120 and compare. Differences should be confined to points where
  idle samples were obviously admitted — not to the floor's flatness.

⚠️ **This is where the prediction could be quietly corrupted.** Picking whichever threshold
produces 0.738 V would be exactly the failure mode this project has spent days guarding against.
Fix the threshold on the idle/loaded separation, write down why, then read the answer.

---

## 4. What to bring back

Into `data/frequency-sweeps/rtx3070ti-20260825/hwinfo-silent/`:

- 3 × `*_sweep.csv` + 3 × `*_sweep.json`
- 3 × HWiNFO logs
- 3 × `*_sweep_voltage.csv` from the join
- The console transcript of each run, into `logs/`
- A `README.md` recording: the VBIOS confirmed, the polling interval used, the `--min-power`
  chosen **and why**, and the measured floor — before any interpretation.

Then:

```bash
python run_tests.py && python analysis/audit_claims.py
```

New claims go in `analysis/claims_crosschip.py` — **not** `claims_consumer.py`. The two are kept
apart so a cross-chip claim cannot reach a 5060 Ti file through a shared constant.

---

## 5. Afterwards

- [ ] **Return the BIOS switch to SILENT** if you moved it, and confirm with `vbios_version`.
- [ ] Delete `C:\headroom-kit` from the customer's drive.
- [ ] Confirm no clock or power lock survived: `nvidia-smi -q -d CLOCK` should show no applications
      clocks set. The sweep resets on exit including on Ctrl-C, but verify rather than trust.
