# RTX 3070 Ti — the bench list

**Written 2026-09-22.** A shop machine, so **it ships, date unknown**, and its items outrank the
5060 Ti's on any day it is reachable. Shared protocol: [`GPU-BENCH-RULES.md`](GPU-BENCH-RULES.md).

✅ **EVERY ITEM IS COLLECTED, 2026-09-24. Session D ended PASS at 23:53** (C0–C13; C8 on 09-23).
Imported to `data/frequency-sweeps/rtx3070ti-sessiond-20260924/`. Scored as registered:
- **4a ✅ PASS** (1222.5 MHz);
- **4b ⛔ FAIL**, so the joint verdict is *the control also moves, and the attribution fails*;
- **8a ✅ PASS** (1170 MHz);
- **8b ⛔ FAIL** (Edit 1's floor reaches 1230 MHz);
- 8c reported.

**Nothing more to run on this card.** Before it ships Saturday: **uninstall MSI Afterburner and
delete its Profiles folder.** The session's own cleanup already verified stock power, core and
memory.

| document | what it is |
|---|---|
| **⌨️ Commands, below in this file** | 🆕 **the commands, in order, as of 2026-09-23**: read these at the machine |
| [`SESSION-D-COMMANDS.md`](SESSION-D-COMMANDS.md) | the reasoning behind each command. ⚠️ Its §3 build steps and Edit 1 description predate the as-built curves; where it disagrees with this file, this file is right |
| [`SESSION-D-RUNSHEET.md`](../data/frequency-sweeps/rtx3070ti-20260825/SESSION-D-RUNSHEET.md) | the design, the stock curve as measured, why each edit is shaped as it is, what each outcome means |
| [`REGISTERED-PREDICTIONS.md`](REGISTERED-PREDICTIONS.md) §4a–4b | the predictions. ⛔ **Read the amendment under §4b**: the design reversed from extending the floor to shortening it on 2026-09-13, and the control's dose is 263 MHz, not the ≥300 registered. Cite the runsheet's commits for the numbers |
| `analysis/score_session_d.py` | 🆕 **the scoring, written before the data**: `python analysis/score_session_d.py <results dir>`. Needs every sweep's voltage extract. It will not score the session unless stock run 1's median is **1485** |

🔑 **Session D is the single item that changes what the paper can claim.** The causal result is
one chip. This makes it two chips and two architectures, with the negative control. After the
2026-09-22 narrowing (Mendes et al., SBAC-PAD 2020, already moved an optimum), **the control is
the part of the design nobody has published**. A Session D without run 3 buys much less.

⚠️ **Logging is by hand on this machine.** The HWiNFO automation is not on the USB kit.

---

## 🛠️ Curves — ✅ ALL THREE BUILT AND DECODED, 2026-09-23

Built by Raymond at the machine, saved, and decoded from the saved store:
`data/afterburner-profiles/3070ti-profiles-20260923/` (full point table in its README). **Do not
rebuild or re-save them.** The commands below check that the store is still byte-identical before any
sweep.

| slot | curve | as built |
|---|---|---|
| **P1** | **STOCK** | every offset 0 |
| **P2** | **Edit 1: the manipulation** | **1200 MHz flat from 725 to 825 mV**, the whole floor band (0.812–0.825 V). Then a **forced ramp** at +60 MHz per point (1215 at 831 → 1575 at 869 mV), rejoining stock at 875 mV. ⚠️ 718.75 mV sits at 1200, 15 MHz above stock |
| **P3** | **Edit 2: the negative control** | stock through 818.75 mV, then **flat 1500 MHz from 825 mV up** |

All three: power limit default, memory +0. The differences from the runsheet are registered as
**Amendment 2** under `REGISTERED-PREDICTIONS.md` §4b, before collection. The predictions are unchanged.

### ✅ RESOLVED: why Edit 1 "would not apply"

**Afterburner (or the driver) will not let a point sit more than ~60 MHz below its right-hand
neighbour.** A cap at 1200 through 825 mV with stock (~1530) at 831 mV is a ~330 MHz step, so it
filled in a ramp. The first build put that ramp **below** 825 mV, inside the floor band. The rebuild
keeps the band flat at 1200 and puts the ramp **above** it, where it does no harm to the test.
Inferred from the saved file and Raymond's screenshots, not from documentation.

---

## ⌨️ Commands — Session D, in order

🛑 **On the SHOP MACHINE with the 3070 Ti, in PowerShell opened as Administrator.** Not on the local
box. Copy one block at a time. ⏱️ **Count the hours first** (go / no-go table below): ~5 h 40 for
everything.

### C0 · Two gates that void the session if wrong

```powershell
nvidia-smi --query-gpu=name,driver_version,power.limit,power.default_limit,power.max_limit --format=csv,noheader
```

Must read **290 / 290 / 320 W**, the **SILENT** BIOS. 310 / 310 / 350 W is the OC BIOS: flip the
switch back, reboot, check again. Write the driver version down (09-04 ran on 610.88).

```powershell
nvidia-smi pmon -c 5 -s u
```

Baseline **under ~5%**, encoder and decoder **0**. Instant Replay off; browsers, Discord, Steam and
media players closed. **Then leave the machine alone except for the steps below.**

### C1 · Bind the kit (the USB is labelled ESD-USB)

```powershell
$kit = (Get-Volume | Where-Object FileSystemLabel -eq 'ESD-USB').DriveLetter + ':\headroom-kit'; cd $kit; $kit; Test-Path "$kit\python\python.exe"
```

Must print the kit path and `True`. **Every path below derives from `$kit`**; never type a drive
letter.

```powershell
$ab = "${env:ProgramFiles(x86)}\MSI Afterburner\MSIAfterburner.exe"
function Show-Load { $p = Start-Process "$kit\python\python.exe" -ArgumentList "$kit\tools\frequency-sweep\gpu_workload.py","--workload","gemm","--iterations","400","--json" -PassThru -WindowStyle Hidden; while (-not $p.HasExited) { Start-Sleep 1; nvidia-smi --query-gpu=clocks.sm,clocks.mem,power.draw --format=csv,noheader } }
```

`Show-Load` runs `gemm` for **~30 s** and prints core clock, memory clock and power once a second
while it runs. **Ignore the first 3–4 lines**, which are Python starting up from the USB at idle
clocks. It is the witness used after every profile change. ✅ Tested 2026-09-23 on the 5060 Ti from
this kit: 32 s, 27 of 31 samples at full load. ⛔ A first version (200 iterations, a fixed 10 s
print) caught almost no load at all, so a quick witness has to be run to be trusted.

### C2 · The profile store must be the one that was decoded

```powershell
(Get-FileHash (Get-ChildItem "${env:ProgramFiles(x86)}\MSI Afterburner\Profiles\VEN_10DE*.cfg").FullName).Hash.Substring(0,16)
```

Must print **`1B08C2D0854460FF`**. ⛔ Anything else means a slot changed after it was decoded: stop,
copy the `Profiles` folder to the USB again, and do not sweep until it has been re-checked.

### C3 · Start HWiNFO once, from the kit

```powershell
Start-Process "$kit\HWiNFO64.exe"
```

**Sensors only**, and leave it open all session. The kit's INI logs every 0.50 s. ⚠️ **Logging is by
hand here:** before **every** run below, click the **logging button** in the Sensors window and save
the log as `$kit\results\hwinfo-<run label>.csv`. Click it again when the run finishes. **One log
per run, never spanning two curves.**

### C4 · Run 1 — STOCK (~62 min)

```powershell
& $ab -profile1 -q; Start-Sleep 8; Show-Load
```

**Witness:** core peaks near **~1763 MHz**, memory **9251** (sometimes 9501). ⚠️ **The 2026-09-23
shakedown's stock witnesses peaked 1770 / 1785 / 1800 / 1890 MHz** (maximum sample, unlocked), with
1935 read back after a clock reset, so a cool card boosts well past 1763. The bench app's stock
ceiling is therefore 2115, not 1900; the 1700 floor is what separates stock from Edit 2. Then start the HWiNFO log
`hwinfo-rtx3070ti-sessiond-stock-1.csv`, and:

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-stock-1" -AppliedSettings "STOCK P1, profile store 1b08c2d0854460ff, SILENT BIOS verified at 290 W, memory +0, IR off, baseline under 5 pct, iterations matched to rtx3070ti-suite-20260904" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120 -ExpectedMemoryClockMhz 9501
```

Stop the HWiNFO log.

⛔ **Memory reads 9251, not 9501, and that is stock.** Corrected 2026-09-23: loaded memory on this
card is **9251 MHz at 186 of 192** committed points and 9501 at 6. This line said "9501" until
then, from reading the top of the range as typical. `-ExpectedMemoryClockMhz 9501` still passes
either state (its tolerance is ±400). ⚠️ That tolerance would also pass a small memory offset
(+250 reads ~9750), so **it is not what proves memory is stock. The C2 profile-hash check is**: all
three decoded slots carry memory +0.

### C5 · Run 2 — EDIT 1, the manipulation (~62 min)

```powershell
& $ab -profile2 -q; Start-Sleep 8; nvidia-smi -lgc 1395,1395; Show-Load; nvidia-smi -rgc
```

**Witness, read in HWiNFO while `Show-Load` prints:** at a locked 1395 MHz, **GPU Core Voltage reads
~0.850 V** on Edit 1, against ~0.812 V at stock. The peak clock cannot tell P2 from stock, because
the top of the curve is unchanged; the voltage can. ⛔ If it reads ~0.812, the edit did not take. Then
start `hwinfo-rtx3070ti-sessiond-edit1-2.csv`, and:

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-edit1-2" -AppliedSettings "EDIT 1 P2 as built: 725-825 mV capped at 1200 MHz, forced ramp +60 MHz per point 831-869 mV, stock from 875 mV, 718.75 mV at 1200 (+15 over stock); store 1b08c2d0854460ff; SILENT BIOS, PL default, memory +0" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120 -ExpectedMemoryClockMhz 9501
```

Stop the log. **Registered:** the median optimum moves **1485 → 1170 or 1275 MHz**.

### C6 · Run 3 — EDIT 2, the negative control (~62 min). 🛑 Never cut this one

```powershell
& $ab -profile3 -q; Start-Sleep 8; Show-Load
```

**Witness:** core peaks at **~1500 MHz**, not ~1763. Then start `hwinfo-rtx3070ti-sessiond-edit2-3.csv`, and:

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-edit2-3" -AppliedSettings "EDIT 2 NEGATIVE CONTROL P3 as built: stock through 818.75 mV, flat 1500 MHz from 825 mV up (825 mV is 15 under stock); store 1b08c2d0854460ff; SILENT BIOS, PL default, memory +0" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120 -ExpectedMemoryClockMhz 9501
```

Stop the log. Every target above 1500 achieves ~1500: **that clipping is the evidence the edit took**.
**Registered:** the optimum stays at **~1485–1500 MHz achieved**.

### C7 · Run 4 — STOCK again, the drift bracket (~62 min). 🥈 Second to cut

```powershell
& $ab -profile1 -q; Start-Sleep 8; Show-Load
```

**Witness:** core peaks near **~1763 MHz** again. Start `hwinfo-rtx3070ti-sessiond-stock-4.csv`, and:

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-stock-4" -AppliedSettings "STOCK P1 reverted after both edits, witnessed by peak core, store 1b08c2d0854460ff, SILENT BIOS, PL default, memory +0" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120 -ExpectedMemoryClockMhz 9501
```

Stop the log. Run 4 must return to run 1 within ~1.5%.

### C8 · Descending stock fine sweep (~12 min). 🥇 First to cut

Still on P1. Start `hwinfo-rtx3070ti-sessiond-finefloor-desc.csv`, and:

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -Descending -SessionLabel "rtx3070ti-sessiond-finefloor-desc" -WorkloadCommand "$kit\python\python.exe $kit\tools\frequency-sweep\gpu_workload.py --workload gemm --json" -MinFrequencyMhz 1200 -MaxFrequencyMhz 1590 -FrequencyCount 10 -OutputDirectory "$kit\results\finefloor-desc" -AppliedSettings "STOCK P1, SILENT BIOS, PL default, memory +0 - fine floor 1200-1590 DESCENDING, same grid as rtx3070ti-silent-gemm-fine 2026-08-27, thermal control as in 4d"
```

**Check the banner counts DOWN from 1590.** Stop the log.

### C9 · Revert, verify, clean up. Never skip

```powershell
& $ab -profile1 -q; Start-Sleep 8; nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader; Show-Load
```

**Verify three ways:** power reads **290 / 290 W**, memory under load **9251** (sometimes 9501), core peaking near
**~1763 MHz**. Then, since the PC is being sold: **uninstall MSI Afterburner and delete its
`Profiles` folder** (both are already preserved in the repo). The kit itself installs nothing.

### C10 · Bring it back

Everything is already on the USB: the sweeps in `$kit\results\`, the HWiNFO logs beside them. Bring
the USB. **The voltage join and scoring (`analysis/score_session_d.py`) happen on the local box.**
Nothing at the machine decides whether the prediction held.

### C11–C13 · Section 8 extras, added 2026-09-23 (bench app only)

`docs/REGISTERED-PREDICTIONS.md` §8 was registered before any of this data existed. The extras run
**after `stock-4`**, in the spare part of the 8 h window, and are ticked in `sessiond-3070ti.json`:
- **C11 (§8c):** stock fine pair, 1200–1590 MHz, ascending then descending. Exploratory.
- **C12 (§8b):** an Edit 1 fine sweep, 1050–1590 MHz, 13 points, with voltage.
- **C13 (§8a):** the `edit1-5` replicate suite, then `stock-6`, then a stock-4 → stock-6 drift gate.

They add ~2.5 h, so the whole session is ~7 h. They are run by the app only; there are no hand
commands for them.

---

## Session D — the order, ~5 h 40

| # | what | time | cut? |
|---|---|---|---|
| 0 | Confirm the **SILENT BIOS** position (290 W) and a quiet machine | 5 min | never |
| 1 | ✅ ~~Install Afterburner; snapshot the store~~ **Done 2026-09-23.** Now: **check the store hash** (C2) | 2 min | never |
| 2 | ✅ ~~Build P1, P2, P3~~ **Built and decoded 2026-09-23** | — | — |
| 3 | Apply P1, **verify stock three ways**. ⛔ **Do NOT calibrate**: reuse the 09-04 iteration counts in `SESSION-D-COMMANDS.md` §4 | 5 min | never |
| 4 | **Run 1: stock suite** | 62 min | never |
| 5 | **Run 2: Edit 1 suite**, the manipulation. Predicted: median optimum **1485 → 1170 or 1275 MHz** | 62 min | never |
| 6 | **Run 3: Edit 2 suite**, the negative control. Predicted: stays at **~1485–1500 achieved**; the six clipped rows count as one bin | 62 min | 🛑 **never** |
| 7 | **Run 4: stock again**, closes the drift bracket; must return to run 1 within ~1.5% | 62 min | 🥈 second cut |
| 8 | Descending stock fine sweep, §4d on a third architecture | 12 min | 🥇 first cut |
| 9 | Revert, **verify stock three ways**, uninstall Afterburner and its profile store | 15 min | never |

### Go / no-go: count the hours at the machine BEFORE installing anything

| hours available | do |
|---|---|
| **5½+** | everything |
| **~4½** | cut step 8, then step 7 |
| **under ~4¼** | ⛔ **do not start.** Keep Session D whole for a day that has the hours |

⚠️ **The one exception:** if the card is leaving for good, a stock + Edit 1 pair still replicates
the *treatment* on a second chip. Write it up as that, **never as the controlled design**.

**Cutting run 4 does not invalidate the result.** The prediction is a shift of two or three grid
points (1485 → 1275 or 1170 on a 105 MHz grid), and cross-session drift (~1.47% on `gemm`) does not move a grid point. It weakens the write-up;
it does not void it.

---

## Also possible on this card, only after Session D

| item | time | why |
|---|---|---|
| Put `tools/hwinfo-logging/` on the kit | desk work | would remove the per-run log clicks here. Not a one-line sync: the wrapper uses the Python on `PATH`, not the kit's bundled interpreter, and writes to a fixed `C:` folder |

## Before the card ships — every time

**Revert to stock and verify three ways:** power limit, memory clock under load, and peak core
reaching **~1763 MHz**. Then **remove Afterburner and its profile store.** A driver reset silently
clears Afterburner offsets, so a settings string proves nothing.
