# RTX 5060 Ti — the remaining sweeps, in order

**Written 2026-09-18 after the fine floor ran.** This card is the local machine, so nothing here
expires — but it is where the project's headline result lives, and six of these are cheap.

🛑 **The 3070 Ti replication still outranks every item on this page.** That card leaves; this one
does not.

---

## Before ANY run — the preflight that caught today's problem

```powershell
nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader
```
Must read **180.00 W, 180.00 W**. If it reads 200 W the card is **not** on stock — apply Profile 3
(`MSIAfterburner.exe -profile3 -q`), wait 6 s, re-check.

```powershell
nvidia-smi pmon -c 5 -s u
```
🆕 **Use `pmon`, not the aggregate.** On 2026-09-18 the baseline sat at 12.6% and the aggregate
only said "something"; `pmon` named `dwm.exe` in seconds. **Baseline must be under ~5%.**

⛔ **THEN LEAVE THE MACHINE ALONE.** On 2026-09-18 the operator's own test-suite and git runs
depressed throughput by **9.38% at every point** while the preflight had passed cleanly minutes
earlier. A passing preflight says nothing about what happens during the run.

**Common variables for every command below:**
```powershell
$py   = "C:\Users\Raymond\AppData\Local\Programs\Python\Python312\python.exe"
$repo = "C:\Users\Raymond\Documents\headroom"
$wl   = "$py $repo\tools\frequency-sweep\gpu_workload.py --workload gemm --json"
```

⚠️ **Start an HWiNFO log before each run and stop it after.** One log must never span two
configurations — the join bins by core clock and cannot separate them afterwards.

---

# 🥇 4b — the descending fine floor. **12 min. Do this one first.**

**The floor the entire project rests on has only ever been measured in one direction.** Registered
as §4d. Today's ascending run gives 0.720 V flat across 1378–1560; if the descending run agrees,
that is the cheapest possible confirmation that the flat floor is real and not a warm-up artifact.

```powershell
& "$repo\tools\frequency-sweep\Invoke-FrequencySweep.ps1" -Descending -SessionLabel "5060ti-finefloor-gemm-desc" -WorkloadCommand $wl -MinFrequencyMhz 1380 -MaxFrequencyMhz 1760 -FrequencyCount 13 -AppliedSettings "stock Profile 3, PL 180 W default, DESCENDING order, thermal control for 4d"
```

**Check the banner reads `1755, 1725, 1695…`** before walking away. That ordering *is* the experiment.

| result | reading |
|---|---|
| 0.720 V still flat across the same span | ✅ the floor is a curve property; §4d resolves on this card |
| the flat region shifts with the cold end | ⛔ thermal — and **every floor extent in the project** needs re-reading |

---

# 🛑 4c — the NVML offset precondition. **10 min. Gates 4b's neighbour.**

**Guerreiro et al., TPDS 2019 (read in full): the observed voltage response depends on HOW the
frequency is changed** — two regions through NVML, but *"the voltage stays constant across all
frequencies"* through clock offsets.

⛔ **If that holds here, the offset arm and the locked arm of 4d are not the same machine state and
the pair validates nothing.** Ten minutes decides whether the next twenty-five are worth spending.

1. Apply a **−300 MHz** P0 offset (negative only — the safe direction).
2. Start a fresh HWiNFO log.
3. Run the same 1380–1760 sweep.
4. Ask: **does 0.720 V still hold flat and then rise, or is it constant everywhere?**

✅ Two regions survive → 4d is meaningful. ⛔ Voltage flat throughout → **stop, and write that up** —
it would be a Blackwell confirmation of a published Maxwell/Pascal/Kepler finding.

---

# 4d — the NVML offset validation pair. **25 min. Only if 4c passes.**

Designed 2026-09-09, never run. Power at a locked *f* with a **−300 MHz** offset against power at
*f*+300 with none. ⛔ **The write has never been exercised on this card** — reading back works, and
that is all. **Claim nothing about it until this runs.**

---

# 4e / 4f — the two floor-ladder rungs. **62 min each.**

Registered before collection, never built. Turns the causal result from *directional* into
**quantitative** — "the optimum moves **proportionally**" — which the outside reader named as the
thing that would strengthen the mechanistic claim.

🔑 **Each rung is a full 12-workload suite**, because the registered prediction is *"at least 7 of
the 12 workloads land individually on the predicted grid point on each rung."* Two workloads cannot
test that — the same defect that was found in Session D's sheet on 2026-09-16.

⚠️ **No ladder profile is stability tested**, and none may resemble the **875 mV @ 3 GHz** that
crashed the driver. Build in the safe direction only. Snapshot the profile store first.

---

# 4g — the >30-minute soak. **1–2 h, unattended. Start it last.**

Every tuned configuration behind the headline numbers has been soaked for exactly thirty minutes,
and undervolt failures routinely take hours to surface. Say **"no failure observed in N minutes"**,
never "stable".

---

# 🆕 Optional, both from today's results — 12 min each

## 4h — pin the floor end

Today brackets it between **1560** (0.720 V) and **1590** (0.730 V). A narrow sweep pins it:

```powershell
& "$repo\tools\frequency-sweep\Invoke-FrequencySweep.ps1" -SessionLabel "5060ti-floorend-gemm" -WorkloadCommand $wl -MinFrequencyMhz 1530 -MaxFrequencyMhz 1620 -FrequencyCount 13 -AppliedSettings "stock Profile 3, PL 180 W default, floor-end bracket 1530-1620"
```

~7.5 MHz steps. ⚠️ **Changes no verdict** — the suite grid is 158 MHz and the rule only needs half a
step. This is for stating the floor end as a measured number rather than a bracket.

## 4i — does the 5060 Ti dither?

Today's logs sampled at the main machine's **2.00 s**, giving only **5–9 samples per point**.
Set `SensorInterval=500` in HWiNFO (or copy the kit's `HWiNFO64.INI`) and re-run 4a for ~4× the
samples.

🔑 **The 2060 Super dithered 23–26% between adjacent codes; whether the 5060 Ti's 5 mV grid does is
unknown**, and 5–9 samples per point cannot answer it. If it dithers, sub-code voltage resolution is
available on the card that matters most.

---

## What is already done, so nobody re-runs it

| | |
|---|---|
| **4a fine floor 1380–1760** | ✅ **twice**, 2026-09-18. `data/frequency-sweeps/5060ti-finefloor-20260918/` |
| Result | 0.720 V flat across **seven points, 1378–1560**; clean monotonic rise to 0.765 at 1747 |
| Floor end | **between 1560 and 1590** — the old "1537" was never measured |
| Grid | **5 mV on this card**, not the 6.25 mV of the other three |
| Contamination | throughput ±9%, **voltage ≤5 mV** — voltage survives, throughput does not |
