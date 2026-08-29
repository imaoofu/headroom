# Session C — the workload suite at stock, on the 3070 Ti

**Purpose: the paired cross-chip run.** With the identical suite collected at stock on both cards,
the unit of analysis becomes the *workload* rather than the chip, and §5.6.2's leave-one-workload-out
design becomes applicable to hardware this project measured itself. That is the answer to "n = 1
chip", and it needs no third card.

**Both cards must be at stock or the pairing does not hold.** A tuned 5060 Ti against a stock
3070 Ti compares two tunings as much as two architectures. The 5060 Ti was reverted 2026-08-29 and
verified at 13801 MHz memory under load; the 3070 Ti is a customer machine and is stock by rule.

**The fan-RPM item is DONE and is not part of this session.** It was already in the Session A and B
logs and cooling is now excluded (§5.5.1.1). Nothing here is blocked on the card any more, which
means a session that gets cut short costs far less than it would have.

---

## Constraints that shape everything below

| | |
|---|---|
| Machine | Somebody else's. **Stock only — no curve changes, no memory offset, no power-limit changes.** |
| VRAM | **8 GB.** The suite is sized to ~1.2 GB per workload for exactly this reason. |
| Iteration counts | **Must be re-derived on this card.** `SUITE-ITERATIONS.md` holds 5060 Ti counts and they do not transfer. |
| Time | ~10–15 min per sweep. Eleven suite workloads is 2–3 hours. Prioritised below so a truncated session still yields something. |

---

## Step 0 — before touching the machine

Instant Replay / ShadowPlay **off**. Close browsers, media players, Discord, Steam. The kit's
preflight refuses on any encoder or decoder activity and names the offender, but finding out before
you start is cheaper than finding out after.

The kit is at `F:\headroom-kit`. It installs nothing and leaves nothing behind.

## Step 1 — calibrate on this card (no admin needed)

Iteration counts are per card. Run this first; it takes a couple of minutes and needs no elevation:

```powershell
cd F:\headroom-kit
foreach ($w in @("bgemm32","bgemm64","bgemm128","bgemm256","bgemm1024","copy","reduce","softmax","layernorm","conv","attention")) {
  .\python\python.exe .\tools\frequency-sweep\gpu_workload.py --workload $w --calibrate
}
```

**Write the numbers down.** Each prints a `--iterations N` recommendation for ~9 s of work. They go
into Step 2 and must then be held constant across every frequency in a sweep.

## Step 2 — the sweeps (elevated PowerShell, not RUN-ME.bat)

`RUN-ME.bat` passes no arguments, so it still collects the original `gemm` + `membw` pair. For the
suite, open **PowerShell as Administrator** and call `Collect.ps1` directly. It keeps the preflight,
the machine-info capture and the video-engine guard; only the workload list changes.

### ⚠️ Execution policy — do this, and do NOT change the machine's setting

Windows defaults to `Restricted`, so a freshly opened PowerShell will refuse to run `.\Collect.ps1`
with "running scripts is disabled on this system". `RUN-ME.bat` never hits this because it launches
with `-ExecutionPolicy Bypass -File`; the direct call the suite needs does.

**Start the elevated window this way** — right-click Start, *Terminal (Admin)* or *PowerShell
(Admin)*, then:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

`-Scope Process` applies to **that window only** and is gone when it closes. Nothing is written to
the registry and the machine's stored policy is untouched.

Equivalently, launch a already-bypassed window in one step:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass
```

🛑 **Never run `Set-ExecutionPolicy` with `-Scope LocalMachine` or `-Scope CurrentUser` on a
customer's machine.** That is a persistent change to somebody else's system security settings, it
survives after the machine leaves, and it is exactly the kind of thing the "leave it as you found
it" rule exists for. The process scope does the same job for the length of the session.

If a script is still refused after that with a *"not digitally signed"* message, the files picked up
a mark-of-the-web on copy. Clear it for the kit only:

```powershell
Get-ChildItem -Path F:\headroom-kit -Recurse -Include *.ps1,*.bat | Unblock-File
```

Substitute the counts from Step 1 for the placeholders. **Order matters — `-Iterations` is matched
to `-Workloads` positionally, and the script refuses to start if the lengths differ.**

### Priority 1 — the never-collected sweep, ~12 minutes

Session B planned this and never got it. It is the smallest outstanding gap in §5.5 and it goes
first because it is cheap and it completes an existing comparison rather than starting a new one.

```powershell
cd F:\headroom-kit
.\Collect.ps1 -Label "rtx3070ti-silent-membw-matched2130" `
              -Workloads membw `
              -AppliedSettings "SILENT BIOS as found, stock. VBIOS 94.04.5a.00.91. Completes the membw matched-2130 sweep Session B planned and never collected."
```

### Priority 2 — the axis ends and the roofline knee, ~50 minutes

Four workloads spanning 0 to 288 FLOP/byte. If the session ends here you still have a usable
cross-chip comparison at both ends of the axis and across the transition.

```powershell
.\Collect.ps1 -Label "rtx3070ti-stock-suite" `
              -Workloads copy,bgemm128,bgemm1024,conv `
              -Iterations <COPY>,<BGEMM128>,<BGEMM1024>,<CONV> `
              -AppliedSettings "STOCK, 3070 Ti, suite at fp32 with TF32 off. Counts calibrated on this card."
```

### Priority 3 — the rest of the suite, ~90 minutes

```powershell
.\Collect.ps1 -Label "rtx3070ti-stock-suite" `
              -Workloads bgemm32,bgemm64,bgemm256,reduce,softmax,layernorm,attention `
              -Iterations <B32>,<B64>,<B256>,<REDUCE>,<SOFTMAX>,<LAYERNORM>,<ATTENTION> `
              -AppliedSettings "STOCK, 3070 Ti, suite at fp32 with TF32 off. Counts calibrated on this card."
```

### Also worth having, if the machine is free unattended

`gemm` and `membw` at stock on this card with the suite's conditions, so the two existing workloads
sit on the same footing as the eleven new ones:

```powershell
.\Collect.ps1 -Label "rtx3070ti-stock-baseline" `
              -AppliedSettings "STOCK, 3070 Ti. gemm and membw at kit defaults, alongside the suite."
```

## Step 3 — before unplugging

Everything lands in `F:\headroom-kit\results\`. Copy the whole folder off. Also copy the raw HWiNFO
CSVs if HWiNFO was running — **do not distil and discard them.** Fan RPM was nearly lost that way
once already; the raw log carries 327 columns and costs nothing to keep.

Leave the machine as you found it.

---

## What this session cannot do

No tuning results. Nothing here touches the V/F curve, the memory offset or the power limit, so
§5.7's whole apparatus stays 5060 Ti only. That limit is stated in §6 and this session does not
change it.
