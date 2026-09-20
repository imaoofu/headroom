# GPU work — the full list

**Every open item in this project that cannot be done at a desk.** Standing document, written
2026-09-19. It is not tied to a weekend: `docs/WEEKEND-PLAN-20260919.md` is a *schedule* for one
specific day and draws from this list; **this is the list.**

🔑 **Everything else is in [`docs/TODO-20260918.md`](TODO-20260918.md)** — paper edits, the
proposal, the citation gate, the dataset package. None of it needs a card, and none of it is a
fallback for bench time that was available and went unused.

**Roughly 19 hours of bench work remains. About 10 of it is on cards that leave.**

| card | remaining | expires? |
|---|---|---|
| **RTX 3070 Ti** | ~5 h 40 | ✅ **yes — it ships** |
| **RTX 2060 Super** | ~4 h 20 | ✅ yes, shop machine |
| **RTX 5060 Ti** | ~8 h 35 | ❌ never — local box |
| RTX 3060 | ~25 min | ⚠️ unknown, probably gone |

---

## How this list is ordered

Four axes, applied in this order. **They are not "importance"** — a Tier 3 item can matter more to
the paper than a Tier 0 one and still come second, because the Tier 0 one stops being possible.

| tier | rule | why it wins |
|---|---|---|
| **0** | **the card leaves** | a result you cannot collect later is not comparable to one you can |
| **1** | **it gates other work** | ten minutes that decides whether twenty-five are worth spending |
| **2** | **something in the paper is wrong or unsupported right now** | it is repairing a live claim, not adding one |
| **3** | **it adds precision or completeness** | real work, but nothing currently rests on it |

🛑 **Two questions decide the whole ordering and neither has an answer in this repository:**
**when does the 3070 Ti ship, and is the 2060 Super still on the bench?** If either is still
reachable in a month, its items drop out of Tier 0 and the 5060 Ti list comes forward.

---

## 🛑 The five-slot problem — read before building any profile

**Three items on this list need a profile that does not exist** — 4j's memory-matched flattened
curve, and the two floor-ladder rungs. **Afterburner has five slots and all five are occupied**,
and every one of them is referenced by committed data:

| slot | configuration | mem | what depends on it |
|---|---|---|---|
| P1 | flattened, 180 W | +2000 | ⛔ **an un-run registered prediction** — see 4k |
| P2 | repair | +2500 | §5.7's repair result; **never stability-soaked** — see 4l |
| P3 | **stock** | +0 | every stock comparison in the repository |
| P4 | full tune | +2500 | the treatment arm of the causal result |
| P5 | split | +2500 | the fastest configuration on record, 18.24 TFLOP/s |

✅ **This is a sequencing problem, not a scarcity problem.** `data/afterburner-profiles/5060ti-profiles-20260918/`
holds **Profile1–5.cfg verbatim**, so any slot restores by copying the file back. The rules:

1. **Snapshot the store before every edit**, dated, never overwriting an older snapshot.
2. **Compare `source_sha256` between snapshots** to confirm what changed — cheaper and stricter
   than comparing curves.
3. ⛔ **Run 4k before reusing P1.** A registered prediction against that slot has never been
   collected, and "restore it afterwards" is one forgotten step away from losing it.
4. **A slot number is not an identity.** P3 held an aggressive curve one day and stock the next.

⚠️ **The weekend plan said P1 was "the only one no live claim depends on". That was wrong** — a
registered prediction depends on it. Corrected here and there.

---

## The preflight, once — it applies to every item below

```powershell
nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader
nvidia-smi pmon -c 5 -s u
```

1. **Power limit must match the configuration you think you are running.** On the 5060 Ti stock is
   **180.00 W**; 200 W means the card is not on Profile 3.
2. **Baseline under ~5%, and use `pmon`, not the aggregate.** On 2026-09-18 the aggregate said
   "something" and `pmon` named `dwm.exe` in seconds.
3. **Instant Replay / ShadowPlay off**, encoder and decoder 0. It is invisible at idle and cost
   10.3% at 1545 MHz once.
4. ⛔ **Then leave the machine alone.** On 2026-09-18 the operator's own test-suite and git runs
   depressed throughput **9.38% at every point** after a clean preflight. **A passing preflight says
   nothing about what happens during the run**, and a point-to-point residual cannot find it
   afterwards — it is blind to a uniform offset.
5. **One HWiNFO log per configuration**, started before and stopped after. The join bins by core
   clock and cannot separate two configurations in one log.
6. **`-AppliedSettings` describes the curve actually applied.** Nothing reconstructs it later.

---

# The master list

| id | card | item | time | tier | what it closes |
|---|---|---|---|---|---|
| **D** | 3070 Ti | **Session D — 4 suites, manipulation + control** | **5 h 40** | **0** | 🥇 one chip → **two chips, two architectures** |
| **E1** | 2060 Super | descending fine floor, 900–1140 | 20 min | **0** | §4d — is the floor a curve property or a cold card? |
| **E2** | 2060 Super | Part 2 — boundary manipulation, 3 suites | ~4 h | **0** | §4c, the Turing boundary condition. Publishable either way |
| **4c** | 5060 Ti | NVML offset precondition | 10 min | **1** | 🛑 gates 4d entirely |
| **4j** | 5060 Ti | memory-**matched** flattened-vs-stock | 35 min | **2** | the largest confound behind the §5.7 retraction |
| **4k** | 5060 Ti | **Profile 1 suite** | 65 min | **2** | a registered prediction, never collected; the only power-limit control |
| **4b** | 5060 Ti | descending fine floor, 1380–1760 | 15 min | **2** | the project's floor, measured the other direction |
| **4l** | 5060 Ti | repaired-curve (P2) stability soak | 35 min | **2** | the one configuration behind §5.7 never soaked |
| **4m** | 5060 Ti | 🆕 **`reduce` fine sweep, RANDOM order, replicated** | 45 min | **2** | the predictor misses `reduce` **16 of 16, all above**; suite order is confounded in 14 of 16 legs |
| **4d** | 5060 Ti | NVML offset validation pair | 25 min | 3 | a capability currently claimed on a read-back alone |
| **4e** | 5060 Ti | floor-ladder rung B (+170) | 82 min | 3 | *directional* → **quantitative** |
| **4f** | 5060 Ti | floor-ladder rung C (+320) | 82 min | 3 | the second rung is what makes it a ladder |
| **4g** | 5060 Ti | >30-minute soak | 90 min | 3 | "no failure in thirty minutes" becomes a real number |
| **4h** | 5060 Ti | pin the floor end, 1530–1620 | 15 min | 3 | states 1560–1590 as measured. **Changes no verdict** |
| **4i** | 5060 Ti | dither check at 0.5 s sampling | 15 min | 3 | does the 5 mV grid dither, as the 2060 Super's does? |
| **F** | 3060 | fine floor + descending twin | 25 min | 3 | ⚠️ only if the card is reachable again |

✅ **4a — the 5060 Ti fine floor — is DONE**, twice, 2026-09-18. Do not re-run it.
`data/frequency-sweeps/5060ti-finefloor-20260918/`.

---

# TIER 0 — the cards that leave

## D. RTX 3070 Ti Session D — **the single item that changes what the paper can claim**

`data/frequency-sweeps/rtx3070ti-20260825/SESSION-D-RUNSHEET.md`. Predictions §4a–4b, registered
before any card was touched. **Full step table, go/no-go threshold and cut ladder:
[`docs/WEEKEND-PLAN-20260919.md`](WEEKEND-PLAN-20260919.md).**

🔑 **The outside reader raised its value rather than lowering it.** Its verdict was that the
region-targeted manipulation **with a negative control** is the one design it could not find
published — so the replication is what stands between "compelling N=1" and an established
relationship.

⚠️ **Run 3, the control, matters more than when it was designed.** The 5060 Ti's control is
**partially leaky** — 4 of 12 workloads move, median +0. A second chip's control is the cheapest
evidence that the leak is chip-specific rather than the mechanism.

⛔ **Every configuration is a full twelve-workload suite.** §4a is registered on the **median suite
optimum**; two workloads cannot test it. The run sheet said `gemm, membw` until 2026-09-16.

⛔ **Below ~4 h 25 available, do not start it.** A manipulation without its control is worth well
under half the pair.

## E1. RTX 2060 Super — the descending fine floor. **20 minutes.**

`SESSION-E-RUNSHEET.md` Part 1b, registered §4d. Stock, nothing applied, nothing to clean up.

⛔ **Re-sync the kit first.** `-Descending` did not exist until 2026-09-15 and an older kit rejects
it as an unknown parameter.

```powershell
.\tools\collection-kit\Sync-Kit.ps1 -KitPath D:\headroom-kit
$kit = "D:\headroom-kit"; Test-Path "$kit\python\python.exe"
```

Start a **new** HWiNFO log, then:

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -Descending -SessionLabel "rtx2060s-finefloor-desc-gemm" -WorkloadCommand "$kit\python\python.exe $kit\tools\frequency-sweep\gpu_workload.py --workload gemm --json" -MinFrequencyMhz 900 -MaxFrequencyMhz 1140 -FrequencyCount 13 -AppliedSettings "stock, PL default, no OC - fine floor probe 900-1140 DESCENDING order, thermal control for 4d"
```

**Check the banner counts DOWN from 1140.** That ordering *is* the experiment.

| result | reading |
|---|---|
| minimum stays at **975–1005** | ✅ the shape belongs to the V/F curve |
| minimum **follows the cold end** | ⛔ thermal — **every floor extent on all four cards** needs re-reading |

⚠️ **Do not oversell it.** The confound is already partly bounded — the 3060's floor is flat across
a **10.2 °C** warm-up, under one 6 mV code. Twelve minutes against a small chance of a large
problem.

## E2. RTX 2060 Super Part 2 — the boundary manipulation. **~4 hours.**

Registered §4c as a **disjunction**: either the floor end becomes sharp enough to locate and the
optimum tracks it, or it stays undecidable and the ambiguity belongs to the silicon rather than the
vendor's curve. **Both outcomes are publishable**, which is why it is worth the time.

The edit (≤0.650 V → 810 MHz, ≥0.669 V untouched) makes the floor end **sharp**: reaching anything
above 810 MHz then requires crossing to 0.669 V, a **38 mV** jump instead of a 6 mV creep.

⚠️ **It cannot coexist with Session D in one day**, and Session D outranks it. The run sheet's own
advice: *"If you only have time for one thing"* — do Part 1b.

---

# TIER 1 — the gate

## 4c. The NVML offset precondition. **10 minutes, and it decides 25 more.**

**Guerreiro et al., TPDS 2019, read in full:** the observed voltage response depends on **how** the
frequency is changed — two regions through NVML, but *"the voltage stays constant across all
frequencies"* through clock offsets.

⚠️ Their offset path is `nvidia-settings` Powermizer on Maxwell/Pascal/Kepler, not
`nvmlDeviceSetClockOffsets` on Blackwell, so it does not transfer automatically. ⛔ **But if it
holds here, the offset arm and the locked arm of 4d are not the same machine state and the pair
validates nothing.**

1. Apply a **−300 MHz** P0 offset. **Negative only** — lower clock at every voltage, so a given
   clock takes *more* voltage. Instability is not reachable in that direction.
2. Start a fresh HWiNFO log.
3. Run the 1380–1760 sweep.
4. **Does 0.720 V hold flat and then rise, or is it constant everywhere?**

✅ Two regions survive → 4d is meaningful.
⛔ Flat throughout → **stop and write it up.** That is a Blackwell confirmation of a published
Maxwell/Pascal/Kepler finding, and it is worth more than the pair it cancels.

---

# TIER 2 — repairing live claims

## 4j. Memory-matched flattened-vs-stock. **~35 min, and the profile does not exist yet.**

**The largest confound behind the §5.7 retraction.** The only committed pair carrying voltage and
XBAR telemetry differs by **2500 MHz of memory clock** — the flattened run logs MCLK 16301 and the
stock run 13801 — so *"DRAM sits at 16301 throughout"* was never true of that pair.

⚠️ **There is no memory-matched pair in the five slots**: every flattened profile carries +2000 or
+2500 and stock carries +0. **Build one — load P4, set the memory slider to +0, save.** One slider,
core curve untouched, and +2500 → +0 is strictly the safe direction. ~10 min on top of the 25.

⛔ **Read the five-slot rules above first.** Snapshot, and do not take P1 before 4k has run.

⚠️ **The operator must be present twice**, once per configuration, because one HWiNFO log must
never span two. It is not an unattended run.

⛔ **What it does NOT settle: mediation.** That needs direct XBAR intervention at fixed core curve
and fixed MCLK, which needs runtime XBAR control this card does not have. 4j removes a confound; it
does not restore the retracted chain.

## 4k. The Profile 1 suite. **65 min. A registered prediction, never collected.**

`docs/REGISTERED-PREDICTIONS.md` §2, registered 2026-09-11, **status: not yet swept.**

> **P1's median optimum is 2010 MHz — the same grid point as P4** — because their floor extents are
> 1972 and 2002 MHz, 30 MHz apart against a ~150 MHz grid, and the mechanism claims the optimum is
> set by the floor extent alone.

🔑 **It is a control on POWER LIMIT, the one variable neither existing arm touches.** The
manipulation moved the floor and the optimum followed; the negative control moved the curve above
the floor and it did not. P1 holds the floor region fixed and changes power (180 W vs 200 W) and
memory (+2000 vs +2500).

⚠️ **Two variables at once**, so a movement will not say which did it — but the prediction is
refuted by movement regardless, because the mechanism claims the floor extent is sufficient.
**Refuted by: a median optimum on any grid point other than 2010.**

✅ **Safety: P1 is existing and unmodified, milder than P4 at every voltage above 850 mV.** No new
territory.

## 4b. The descending fine floor, 1380–1760. **15 min.**

**The floor the entire project rests on has only ever been measured in one direction.** The
ascending run gives 0.720 V flat across 1378–1560; if descending agrees, that is the cheapest
possible confirmation it is not a warm-up artifact.

```powershell
& "$repo\tools\frequency-sweep\Invoke-FrequencySweep.ps1" -Descending -SessionLabel "5060ti-finefloor-gemm-desc" -WorkloadCommand $wl -MinFrequencyMhz 1380 -MaxFrequencyMhz 1760 -FrequencyCount 13 -AppliedSettings "stock Profile 3, PL 180 W default, DESCENDING order, thermal control for 4d"
```

🛑 **Join with `--clock-tolerance 7`** — the ±25 MHz default shares samples on a grid this fine, and
it now refuses rather than doing it silently.

## 4l. Stability-soak the repaired curve (P2). **35 min.**

**The split curve and the original tune were each soaked for thirty minutes on 2026-08-23. The
repaired curve never has been**, and §5.7 carries its result.

OCCT GPU:3D **Adaptive**, **error detection on**, via
`tools/stability-logger/Invoke-StabilityProtocol.ps1`. Say **"no failure observed in N minutes"**,
never "stable" — error detection cannot see GDDR7's silent retries.

---

# TIER 3 — precision and completeness

## 4d. The NVML offset validation pair. **25 min. Only if 4c passes.**

Designed 2026-09-09, never run. Power at a locked *f* with a **−300 MHz** offset against power at
*f*+300 with none. ⛔ **The write has never been exercised on this card** — reading back works, and
that is all. **Claim nothing about its effect until this runs.**

## 4e / 4f. The two floor-ladder rungs. **82 min each.**

`docs/REGISTERED-PREDICTIONS.md` §1, registered 2026-09-11, **profiles never built.** Turns the
causal result from *directional* into **quantitative** — "the optimum moves **proportionally**" —
which the outside reader named as the thing that would strengthen the mechanistic claim.

Both are **P5's curve with only the region below ~850 mV raised by a fixed offset**; everything at
and above 860 mV stays byte-identical to P5.

| rung | offset below 850 mV | clock at 0.720 V | predicted optimum | acceptance window |
|---|---|---|---|---|
| A | +0 | 1530 | 1545 | ✅ have it (P5 / P2 / stock) |
| **B** | **+170** | ~1700 | **1702** | floor extent 1624–1777 |
| **C** | **+320** | ~1850 | **1852** | floor extent 1778–1931 |
| D | +472 | 2002 | 2010 | ✅ have it (P4) |

🔑 **Each rung is a full twelve-workload suite**, because the registered prediction is *"at least 7
of the 12 workloads land individually on the predicted grid point on each rung."* Two workloads
cannot test that.

⚠️ **Leave 845 and 850 mV alone** — they are not stock (+202 and −2 against P3) and 845 is where
P5's curve steps backward. They sit above the load floor and outside the region this moves.

🛑 **No ladder profile is stability tested, and none may resemble the 875 mV @ 3 GHz that crashed
the driver.** Build in the safe direction only, and snapshot the store first.

## 4g. The >30-minute soak. **1–2 h, unattended. Start it last.**

Every tuned configuration behind the headline numbers has been soaked for exactly thirty minutes,
and undervolt failures routinely take hours to surface. ✅ **This one runs while you do something
else.**

## 4m. 🆕 The `reduce` residual — mechanism or suite position? **45 min.**

**Added 2026-09-20 from the predictor audit.** The curve predictor misses **all 16 `reduce` curves
and every raw optimum is ABOVE the prediction** — stock 1702/1852, split 1852/2010, repair 2167,
full tune 2167–2625. Mean regret 4.790%, worst 11.939%. ⚠️ **`gemm` behaves differently** — exact
on full tune four times, scattered 1395/1545/1702 elsewhere — so grouping them as "the 70%
residual" hides a systematic displacement inside a run-sensitive one.

⛔ **The confound: 14 of 16 run legs use the identical suite order**, so workload identity is almost
perfectly aligned with position, thermal history and session duration.

**The discriminator:** fine-sweep `reduce` and one matched workload **in randomised order, with
replication**, under at least two curve extents.

| result | reading |
|---|---|
| `reduce` keeps a stable positive offset across orders | ✅ a mechanism limit or a real workload property |
| the offset follows run position or session | ⛔ a benchmark artifact — and **every per-workload residual in the project inherits it** |

## 4h. Pin the floor end. **15 min.**

1530–1620, 13 points, ~7.5 MHz steps. Today brackets it between **1560** (0.720 V) and **1590**
(0.730 V). ⚠️ **Changes no verdict** — the suite grid is 158 MHz and the rule only needs half a
step. This is for stating the floor end as a measured number rather than a bracket, after the file
carried an inferred "1537" for weeks.

## 4i. Does the 5060 Ti dither? **15 min.**

The 2026-09-18 logs sampled at the main machine's **2.00 s**, giving only **5–9 samples per point**.
Set `SensorInterval=500` in `HWiNFO64.INI` (the kit already uses it) and re-run 4a for ~4× the
samples. 🔑 **The 2060 Super dithered 23–26% between adjacent codes; whether the 5060 Ti's 5 mV grid
does is unknown**, and 5–9 samples cannot answer it. If it dithers, sub-code voltage resolution is
available on the card that matters most.

## F. RTX 3060 — only if it is reachable again. **25 min.**

Its floor (0.756 V, ending 1260 MHz) was read on a **105 MHz** grid — coarser than the 31 MHz the
5060 Ti now has and the 15 MHz the 2060 Super has. A fine floor plus its descending twin would put
the third architecture on the same footing. ⚠️ **Nothing currently rests on it**, and the
cross-architecture claim already stands on the coarse reading.

---

## What is deliberately NOT on this list

⛔ **Re-running 4a.** Done twice on 2026-09-18.

⛔ **The voltage-shortfall test.** Refuted 2026-08-21 — raising the curve's top point to 0.925 V
*lowered* the ceiling. Voltage, thermals, power and throttling are all eliminated and the deficit
is still unexplained. **Do not re-run it.**

⛔ **Anything that chases the wandering `membw` dip.** It lands on a different frequency each time;
it is transient, not a property of the curve, and the encoder guard does not explain it.

⛔ **More `membw` configuration rankings at n≤3.** Between configurations 0.56%, within one
configuration up to 0.98% — the curves are closer together than one curve is to itself. **No
ranking among memory-only, repair and split is supported** at this precision.

⛔ **CPU and RAM undervolting.** Scoped out, not deferred: BIOS-level, one reboot per data point,
and instability causes silent data corruption rather than a recoverable driver crash.

---

## The rules that do not bend

1. **Preflight every run**, then leave the machine alone. See the preflight block above.
2. **Always log a stock baseline per machine** before testing tuned settings. A tuned result with
   no same-chip stock comparison measures nothing.
3. **Change one variable at a time.** Core curve, memory and power limit are three variables.
4. **Iteration counts constant across every frequency in a sweep**, or the fixed-work property that
   makes duration a valid performance metric is broken.
5. **Snapshot the profile store before the first edit**, dated, never overwriting.
6. **One HWiNFO log per configuration.** Never one spanning a change.
7. **Bind `$kit` once** and derive every path from it. Mixing `D:` and `F:` in one command line has
   already cost an hour.
8. **A driver reset silently clears Afterburner offsets.** If one happens mid-suite, that suite is
   stock silicon wearing a tuned settings string. Re-run rather than keep the data.
9. **Revert and verify three ways before any card ships** — power limit, memory clock under load,
   peak core against its stock ceiling. Then remove Afterburner and its profile store.
10. **A null is a result** and gets written up as one.
