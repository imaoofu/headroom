# RTX 5060 Ti — the bench list

**Every open item on the local box, and nothing else.** Written 2026-09-20. Drawn from
[`GPU-WORKLIST.md`](GPU-WORKLIST.md), which remains the list for all four cards; this one exists
because the 5060 Ti's items sequence differently from every other card's.

**Twelve items, ~8 h 35 of bench time.** None of it expires.

---

## 🔑 Why this card's list is ordered differently

**The 3070 Ti and the 2060 Super are ordered by when they leave. This card never leaves**, so Tier
0 does not exist here and two other pressures take over:

**1. ⛔ Contamination is the dominant risk, not scheduling.** This is the machine Raymond works on.
On 2026-09-18 his own test-suite and git runs alongside a sweep depressed throughput **9.38% at
every point**, after a clean preflight — and a point-to-point residual cannot find it afterwards,
because it is blind to a uniform offset. **On the shop machine you walk away; here you have to
choose not to use your own computer.** That makes evening and unattended runs worth more here than
anywhere else.

**2. 🔑 Setup cost dominates the short items.** Five of the twelve are 10–15 minutes of actual
sweeping wrapped in a preflight, an HWiNFO session and a profile check. **Run alone they cost
~30 minutes each; batched they cost their run time.** The blocks below exist for that reason and
are the main thing this document adds over the master list.

⚠️ **Set `HEADROOM_SKIP_HOOKS=1` for the session.** The PostToolUse gate is only 0.18 s, but 0.18 s
of this machine is not nothing while it is the instrument.

**3. 🆕 2026-09-21 — the boundaries are automated, so "contamination" now means the operator's
OTHER work, not the run's own setup.** `tools/hwinfo-logging/Invoke-LoggedSweep.ps1` does preflight
→ log start → sweep → log stop as one elevated scheduled task, triggered by `schtasks /run`. That
removes the operator from every boundary in this list **except an Afterburner curve change**, which
is still by hand. 🔑 **Which means the items that batch cleanly are the ones with no profile change
— Block 1 is exactly that**, and it is now runnable start to finish without anyone at the desk.

⚠️ **The wrapper has never driven a real sweep.** Every test was `-WhatIfOnly` or the logging tool
alone. **Make the first live run a short watched one** — 4i at 13 points is ~15 minutes — and only
then leave a session unattended.

---

## 🛑 The five-slot problem, in the order it actually binds

Afterburner has five slots and all five are occupied by configurations that committed data
references. `data/afterburner-profiles/5060ti-profiles-20260918/` holds **Profile1–5.cfg
verbatim**, so this is a **sequencing** problem, not a scarcity one.

| slot | configuration | mem | freed by |
|---|---|---|---|
| P1 | flattened, 180 W | +2000 | ⛔ **4k — an un-run registered prediction** |
| P2 | repair | +2500 | never; §5.7 depends on it, and 4l soaks it |
| P3 | **stock** | +0 | never; every stock comparison in the repository |
| P4 | full tune | +2500 | never; the treatment arm of the causal result |
| P5 | split | +2500 | never; 18.24 TFLOP/s, the fastest on record |

🔑 **P1 is the only slot that ever comes free, and 4k is what frees it.** Three items need a
profile that does not exist — 4j's memory-matched curve and the two ladder rungs — so **4k gates
all three**, not by tier but by hardware.

**Every time:** snapshot the store dated before the edit, never overwrite an older snapshot, and
compare `source_sha256` between snapshots rather than comparing curves.

---

## The preflight — once per block, not once per run

```powershell
nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader
nvidia-smi pmon -c 5 -s u
```

1. **180.00 W means Profile 3 (stock). 200 W means it is not.**
2. **Baseline under ~5%, read from `pmon`, not the aggregate** — on 2026-09-18 the aggregate said
   "something" and `pmon` named `dwm.exe`.
3. **Instant Replay / ShadowPlay off**, encoder and decoder 0. Invisible at idle; cost 10.3% at
   1545 MHz once.
4. ⛔ **Then leave the machine alone.** A passing preflight says nothing about what happens during
   the run.
5. **One HWiNFO log per configuration.** Historical joins bin by core clock and cannot separate
   configurations in one log. New benchmark-window joins can separate complete new sweeps, but
   separate logs keep each configuration's provenance explicit.

---

# BLOCK 1 — the stock fine-sweep block. **~65 min, four items.**

🔑 **This is the highest-value hour on the list and it did not exist as a unit before today.** Four
items share stock Profile 3, one band and one preflight. Each run needs its own HWiNFO log. Two of them are Tier 3
and would never justify a session of their own; inside this block they cost only their run time.

**CORRECTED 2026-09-21.** The heading previously said *"no Afterburner at all"* and this paragraph
said *"one HWiNFO session"*. That assumed Profile 3 would already be live and used "session" for
the shared bench block. The live card read 200 W on 2026-09-21, versus the stock 180 W default,
so applying and verifying saved Profile 3 is required before this block. The protocol has always
required a separate HWiNFO log per run. Neither application nor logging occurred during this
correction.

⛔ **Set `SensorInterval=500` in the main machine's `HWiNFO64.INI` before starting, and run the
whole block at it.** The machine normally logs at **2.00 s**, giving only 5–9 samples per point.
The kit uses 0.50 s and gets four times that.

✅ **That one change restructures the block's logic, and for the better.** 4b was specified as a
descending run to compare against the **2026-09-18** ascending sweep. Run inside this block it
compares against **4i's ascending run instead** — same session, same sampling rate, same day — which
removes the ~1.47% cross-session drift *and* the sampling difference at the same time. **Two
confounds gone for no extra minutes.**

| order | id | run | min | tier |
|---|---|---|---|---|
| 1 | **4i** | ascending fine floor **1380–1760**, 13 pts, at 0.50 s | 15 | 3 |
| 2 | **4b** | **descending** same band, same rate | 15 | 2 |
| 3 | **4h** | **1530–1620**, 13 pts, ~7.5 MHz | 15 | 3 |
| 4 | **4c** | ascending same band with a **−300 MHz NVML P0 offset** | 10 | **1** |

**New HWiNFO log per run.** New stamped sweeps join by benchmark time automatically. For an older
sweep without stamps, 🛑 **join with `--clock-tolerance 7`** — the ±25 MHz default shares samples
on a grid this fine, and the clock join refuses rather than doing it silently.

### 4i — does the 5 mV grid dither?

The 2060 Super dithers **23–26% between adjacent codes**; whether this card does is unknown, and
5–9 samples per point cannot answer it. **If it dithers, sub-code voltage resolution is available
on the card that matters most.** This run is also the block's ascending reference.

### 4b — the floor, measured the other direction

**The floor the whole project rests on has only ever been measured ascending.** 0.720 V flat across
1378–1560; if descending agrees, that is the cheapest possible confirmation it is not a warm-up
artifact.

| result | reading |
|---|---|
| descending agrees with 4i | ✅ the shape belongs to the V/F curve |
| the floor follows the cold end | ⛔ thermal — **every floor extent on all four cards** needs re-reading |

⚠️ **Do not oversell it.** The 3060's floor is flat across a **10.2 °C** warm-up, under one 6 mV
code, so the confound is already partly bounded.

### 4h — state the floor end as a number

Today it is a bracket: **1560** holds 0.720 V, **1590** is the first rise. ⚠️ **Changes no verdict**
— the suite grid is 158 MHz and the rule needs only half a step. This is so the file stops carrying
a bracket after having carried an inferred "1537" for weeks.

### 4c — 🛑 the gate. Ten minutes that decide twenty-five.

**Guerreiro et al., TPDS 2019, read in full:** the observed voltage response depends on **how** the
frequency is changed — two regions through NVML, but *"the voltage stays constant across all
frequencies"* through clock offsets. ⚠️ Their offset path is `nvidia-settings` Powermizer on
Maxwell/Pascal/Kepler, not `nvmlDeviceSetClockOffsets` on Blackwell, so it does not transfer
automatically.

**Negative offset only** — lower clock at every voltage, so a given clock takes *more* voltage.
Instability is not reachable in that direction.

| result | verdict |
|---|---|
| two regions survive | ✅ **4d is meaningful — run it** |
| flat throughout | ⛔ **stop and write it up.** A Blackwell confirmation of a published Maxwell/Pascal/Kepler finding is worth more than the pair it cancels |

---

# BLOCK 2 — only if 4c passed. **25 min.**

## 4d — the NVML offset validation pair

Designed 2026-09-09, **never run**. Power at a locked *f* with a −300 MHz offset against power at
*f*+300 with none. ⛔ **The write has never been exercised on this card** — reading back works, and
that is all. **Claim nothing about its effect until this runs.**

---

# BLOCK 3 — the slot chain. **~4 h 35, and the order is forced by hardware.**

⛔ **4k → 4j → 4e → 4f.** Each step writes into P1, so each needs the previous one finished and
snapshotted. Nothing here can be reordered.

## 4k — the Profile 1 suite. **65 min. Tier 2, and it unblocks the rest.**

`docs/REGISTERED-PREDICTIONS.md` §2, registered 2026-09-11, **status: not yet swept.**

> **P1's median optimum is 2010 MHz — the same grid point as P4** — because their floor extents are
> 1972 and 2002 MHz, 30 MHz apart against a ~150 MHz grid, and the mechanism claims the optimum is
> set by the floor extent alone.

🔑 **It is a control on POWER LIMIT, the one variable neither existing arm touches.** The
manipulation moved the floor and the optimum followed; the negative control moved the curve above
the floor and it did not. P1 holds the floor region fixed and changes power (180 vs 200 W) and
memory (+2000 vs +2500).

⚠️ **Two variables at once**, so movement will not say which did it — **but the prediction is
refuted by movement regardless**, because the mechanism claims the floor extent is sufficient.
**Refuted by: a median optimum on any grid point other than 2010.**

✅ Safety: P1 is existing and unmodified, milder than P4 at every voltage above 850 mV.

## 4j — memory-matched flattened-vs-stock. **~45 min including the build.**

**The largest confound behind the §5.7 retraction.** The only committed pair carrying voltage and
XBAR telemetry differs by **2500 MHz of memory clock** — flattened logs MCLK 16301, stock logs
13801 — so *"DRAM sits at 16301 throughout"* was never true of that pair.

**Build:** load P4, set the memory slider to **+0**, save into P1. One slider, core curve untouched,
and +2500 → +0 is strictly the safe direction.

⚠️ **The operator must be present twice**, once per configuration, because one HWiNFO log must never
span two. Not an unattended run.

⛔ **What it does NOT settle: mediation.** That needs direct XBAR intervention at fixed core curve
and fixed MCLK, which needs runtime XBAR control this card does not have. **4j removes a confound;
it does not restore the retracted chain.**

## 4e / 4f — the two floor-ladder rungs. **82 min each.**

`docs/REGISTERED-PREDICTIONS.md` §1, registered 2026-09-11, **profiles never built.** Turns the
causal result from *directional* into **quantitative** — *"the optimum moves proportionally"* —
which the outside reader named as the thing that would most strengthen the mechanistic claim.

Both are **P5's curve with only the region below ~850 mV raised by a fixed offset**; everything at
and above 860 mV stays byte-identical to P5.

| rung | offset below 850 mV | clock at 0.720 V | predicted optimum | acceptance window |
|---|---|---|---|---|
| A | +0 | 1530 | 1545 | ✅ already have it (P5 / P2 / stock) |
| **B (4e)** | **+170** | ~1700 | **1702** | floor extent 1624–1777 |
| **C (4f)** | **+320** | ~1850 | **1852** | floor extent 1778–1931 |
| D | +472 | 2002 | 2010 | ✅ already have it (P4) |

🔑 **Each rung is a full twelve-workload suite**, because the prediction is *"at least 7 of the 12
workloads land individually on the predicted grid point on each rung."* Two workloads cannot test
that.

⚠️ **Leave 845 and 850 mV alone** — they are not stock (+202 and −2 against P3), 845 is where P5's
curve steps backward, and both sit above the load floor and outside the region this moves.

🛑 **No ladder profile is stability tested, and none may resemble the 875 mV @ 3 GHz that crashed
the driver** — eleven reset events, and the reset silently cleared the Afterburner offsets.

---

# BLOCK 4 — independent of the slot chain, run whenever

## 4l — stability-soak the repaired curve (P2). **35 min.**

**The split curve and the original tune were each soaked for thirty minutes on 2026-08-23. The
repaired curve never has been**, and §5.7 carries its result.

OCCT GPU:3D **Adaptive**, **error detection on**, via
`tools/stability-logger/Invoke-StabilityProtocol.ps1`. Say **"no failure observed in N minutes"**,
never "stable" — error detection cannot see GDDR7's silent retries.

## 4m — the `reduce` residual: mechanism or suite position? **45 min.**

**From the 2026-09-20 predictor audit.** The curve predictor misses **all 16 `reduce` curves and
every raw optimum is ABOVE the prediction** — stock 1702/1852, split 1852/2010, repair 2167, full
tune 2167–2625. Mean regret 4.790%, worst 11.939%. ⚠️ **`gemm` behaves differently** — exact on full
tune four times, scattered elsewhere — so grouping them as "the 70% residual" hides a systematic
displacement inside a run-sensitive one.

⛔ **The confound: 14 of 16 run legs use the identical suite order**, so workload identity is almost
perfectly aligned with position, thermal history and session duration.

**The discriminator:** fine-sweep `reduce` and one matched workload **in randomised order, with
replication**, under at least two curve extents.

| result | reading |
|---|---|
| `reduce` keeps a stable positive offset across orders | ✅ a mechanism limit or a real workload property |
| the offset follows run position or session | ⛔ a benchmark artifact — and **every per-workload residual in the project inherits it** |

## 4g — the >30-minute soak. **90 min, unattended. 🔑 Start it last, or overnight.**

Every tuned configuration behind the headline numbers has been soaked for exactly thirty minutes,
and undervolt failures routinely take hours to surface. ✅ **This is the one item that runs while
the machine is otherwise unusable anyway** — which on this card is the scarce resource.

---

## Suggested order, if there is no other constraint

| | what | min | why here |
|---|---|---|---|
| 1 | **Block 1** — 4i, 4b, 4h, 4c | 65 | cheapest hour on the list; 4c gates Block 2 |
| 2 | **4d**, if 4c passed | 25 | expires as a question the moment 4c answers it the other way |
| 3 | **4k** | 65 | Tier 2, and the only thing that frees a slot |
| 4 | **4j** | 45 | repairs the largest live confound |
| 5 | **4l** | 35 | short, independent, no slot needed |
| 6 | **4m** | 45 | decides whether every per-workload residual is trustworthy |
| 7 | **4e**, **4f** | 164 | the expensive pair; directional → quantitative |
| 8 | **4g** | 90 | unattended, start it when you stop working |

**Total ~8 h 35.** ⚠️ **Nothing here is a fallback for bench time on a card that leaves.** If the
3070 Ti or the 2060 Super is reachable on a given day, those outrank every item on this page —
see [`GPU-WORKLIST.md`](GPU-WORKLIST.md).

---

## What is deliberately NOT on this list

⛔ **Re-running 4a as a fresh item.** Done twice on 2026-09-18 —
`data/frequency-sweeps/5060ti-finefloor-20260918/`. **4i is not a re-run for its own sake**; it is
the same band at four times the sampling rate, to answer a question the 2.00 s logs cannot.

⛔ **The voltage-shortfall test.** Refuted 2026-08-21 — raising the curve's top point to 0.925 V
*lowered* the ceiling by 21.9 MHz. Voltage, thermals, power and throttling are all eliminated and
the deficit is still unexplained. **Do not re-run it.**

⛔ **Anything chasing the wandering `membw` dip.** It lands on a different frequency each time; it
is transient, not a property of the curve, and the encoder guard does not explain it.

⛔ **More `membw` configuration rankings at n≤3.** Between configurations 0.56%, within one
configuration up to 0.98% — **the curves are closer together than one curve is to itself.**

---

## The rules that do not bend

1. **Preflight every block**, then leave the machine alone.
2. **Always log a stock baseline** before testing tuned settings.
3. **Change one variable at a time.** Core curve, memory and power limit are three variables.
4. **Iteration counts constant across every frequency in a sweep.**
5. **Snapshot the profile store before the first edit**, dated, never overwriting.
6. **One HWiNFO log per configuration.**
7. **A driver reset silently clears Afterburner offsets.** If one happens mid-suite, that suite is
   stock silicon wearing a tuned settings string. **Re-run rather than keep the data.**
8. **A null is a result** and gets written up as one.
