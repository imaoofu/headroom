# Session D — the commands, in order

**RTX 3070 Ti, the causal replication.** Written 2026-09-20 for use at the machine.
Reasoning, predictions and what each outcome means: `SESSION-D-RUNSHEET.md`, beside this file on
the kit. **This page is only the commands.**

🛑 **These run on the SHOP MACHINE with the 3070 Ti in it. Not on the local box.**

⛔ **Count the hours first.** Full session ~5 h 40. Below ~4 h 25, do not start — a manipulation
without its control is worth well under half the pair. Cut order if time runs short: drop a
replicate, **never Edit 2**.

---

## 0 · Before anything — two gates that void the session if wrong

### The BIOS switch

```powershell
nvidia-smi --query-gpu=name,driver_version,power.limit,power.default_limit,power.max_limit --format=csv,noheader
```

| power reads | |
|---|---|
| **290 / 290 / 320 W** | ✅ **SILENT** — proceed |
| 310 / 310 / 350 W | ⛔ **OC** — every number this session predicts against is a silent measurement. Switch back, reboot, re-check |

🔑 This card is dual-BIOS, was **found in SILENT and returned to SILENT**, and the 1485 MHz
optimum, the 0.812–0.819 V floor and the ~1763 MHz power cap are all silent-position figures. A
flipped switch would produce a clean-looking run that answers a different question.

**Write the driver version down.** The suite this session is compared against ran on **610.88**.

### The machine is quiet

```powershell
nvidia-smi pmon -c 5 -s u
```

Baseline **under ~5%**, encoder and decoder **0**. Instant Replay / ShadowPlay off; browsers,
Discord, Steam, media players closed. ⚠️ A passing 10% guard is not enough — a 6% baseline still
cost 10.3% at 1545 MHz once. **Then leave the machine alone for the rest of the session.**

---

## 1 · Kit

```powershell
Get-Volume | Where-Object DriveLetter
```

```powershell
$kit = "D:\headroom-kit"; cd $kit; Test-Path "$kit\python\python.exe"
```

⚠️ **Bind `$kit` once and derive every path from it.** Mixing `D:` and `F:` in one command line
already cost an hour on the 2060 Super, and produced thirteen clean-looking idle points.

```powershell
& "$kit\python\python.exe" "$kit\preflight.py"
```

---

## 2 · Snapshot the Afterburner profile store — BEFORE the first edit

Install Afterburner, then:

```powershell
$dest = "$kit\results\afterburner-3070ti-$(Get-Date -Format yyyyMMdd)"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item "${env:ProgramFiles(x86)}\MSI Afterburner\Profiles\*.cfg" $dest -Force
Get-FileHash "$dest\*.cfg" -Algorithm SHA256 | Format-List Path,Hash
```

**A slot number is not an identity.** There is no tool for this — copy verbatim, record the hashes.

---

## 3 · ⛔ Do NOT calibrate

**The iteration counts for this exact card already exist**, from `rtx3070ti-suite-20260904` — the
twelve-workload run that produced the **1485 MHz** median optimum this session predicts against.

🔑 Re-calibrating changes the work per point, so run 1 would stop being comparable to the run that
produced the number being predicted against. Reusing them makes run 1 a **same-card, same-config,
same-work replicate of 09-04** — a sixteen-day drift check, free.

```
4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120
```

Positional, matching `copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm`.

---

## 4 · The four suites, ~62 min each

🛑 **Start a NEW HWiNFO log before each run and stop it after.** One log must never span two
curves — the join bins by core clock and cannot separate them afterwards. **NVML exposes no
voltage at all, so HWiNFO is the only evidence a curve edit actually took**, and a driver reset
silently clears Afterburner offsets.

### Run 1 — stock baseline

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-stock-1" -AppliedSettings "STOCK, SILENT BIOS verified at 290 W, no Afterburner curve applied, memory stock, IR off, baseline under 5 pct, iterations matched to rtx3070ti-suite-20260904" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120
```

### Run 2 — EDIT 1, the manipulation

Apply first: **every curve point at or below 0.825 V → 1200 MHz. Everything at 0.831 V and above
untouched.** Dragging points *down* only; instability is not reachable by construction.

⛔ **The boundary is 0.825, not 0.819** — corrected 2026-09-20. The fine sweep reads 0.825 V at
1200 MHz, inside the floor, and 825 mV is a real point on this card's 6.25 mV grid. Leaving it at
stock would leave the floor reaching ~1500 MHz and the manipulation would test nothing.

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-edit1-2" -AppliedSettings "EDIT 1 - every curve point at or below 0.825 V set to 1200 MHz, 0.831 V and above left at stock, SILENT BIOS, PL default, memory stock" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120
```

**Registered prediction:** the median optimum moves **down from 1485 → 1170 or 1275 MHz**.

### Run 3 — EDIT 2, the negative control

**Flatten everything from 0.831 V upward to a constant 1500 MHz. Leave 0.825 V and below at
stock.**

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-edit2-3" -AppliedSettings "EDIT 2 NEGATIVE CONTROL - 0.831 V and above flattened to 1500 MHz, 0.825 V and below left at stock, SILENT BIOS, PL default, memory stock" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120
```

⚠️ **Every target above 1500 will achieve ~1500. That clipping is the evidence the edit took, not
a failed run.**

**Registered prediction:** the optimum **stays at 1485**.

### Run 4 — stock again, closes the bracket

Revert the curve first.

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-stock-4" -AppliedSettings "STOCK reverted after both edits and verified three ways, SILENT BIOS, PL default, memory stock" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations 4099,4291,3230,2462,843,2113,3511,2327,616,135,432,120
```

⛔ **If run 4 does not return to run 1 within ~1.5%, the session is drift-contaminated and the
manipulation result is not interpretable.** Report that rather than the effect.

---

## 5 · Before the card ships

```powershell
nvidia-smi --query-gpu=power.limit,power.default_limit,clocks.max.graphics --format=csv,noheader
```

```powershell
nvidia-smi --query-gpu=clocks.sm,clocks.mem --format=csv,noheader -l 1
```

**Verify the revert three ways** — power limit reads stock, memory clock under load reads stock,
peak core reaches its stock ceiling (~1763 MHz achieved). 🛑 A driver reset silently clears
Afterburner offsets, so a card can report a tuned settings string while running stock silicon.
That has already happened once here and would have produced a whole sweep of mislabelled data.

Then **uninstall Afterburner and delete its profile store.** The kit installs nothing and leaves
nothing behind; this session does, and that is the part to undo.

---

## Reading it

| result | verdict |
|---|---|
| optimum → **1170 / 1275**, control unmoved | ✅ **the causal claim replicates on a second chip and architecture** |
| optimum moves **and** the control moves | ⛔ attribution to the floor region is wrong — a bigger finding, and it must be reported |
| optimum does not move | ⛔ refutes the claim off the 5060 Ti; report as the headline, and the 5060 Ti result becomes single-chip |
| run 4 ≠ run 1 | ⚠️ drift-contaminated — report nothing about the effect |

🔑 **This edit moves the floor DOWN (−300 MHz) where the 5060 Ti moved it UP (+465).** Deliberate:
it rules out *"any curve edit pushes the optimum upward"*, which a same-direction replication
could not do.

⚠️ **Whatever happens, this is still one chip per architecture.** A successful replication makes
the claim "causal on two chips across two architectures", not "general".
