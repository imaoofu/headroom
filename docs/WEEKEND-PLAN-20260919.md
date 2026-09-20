# Weekend plan — everything that needs Raymond at a machine

**Written 2026-09-16 for the weekend of 19–21 September. ⛔ REVISED 2026-09-19 (late Saturday):
SATURDAY DID NOT HAPPEN.** The three-card window has collapsed to **one working day, Sunday
2026-09-20**, so this is no longer a weekend plan — it is a one-day plan, and the ordering below
changed because of it.

🔑 **This list is ONLY the hardware-bound work.** Everything else — the paper edits, the proposal,
the dataset README — is in `docs/TODO-20260918.md` and none of it needs a card. **With one day left
that rule hardens: nothing at a desk touches bench time, and desk work is not a fallback for a
sweep that fits.**

---

## ⛔ What the lost day actually costs, stated plainly

The original plan spent Saturday on the 3070 Ti, Sunday morning on the 2060 Super and Sunday
afternoon on the 5060 Ti. **Those three blocks do not compress into one day, and they cannot be run
in parallel** — see the kit constraint below. So something is not getting done, and the useful
question is which.

**The ordering rule is unchanged and it decides this: what expires first.**

| card | expires? | one-day verdict |
|---|---|---|
| **RTX 3070 Ti** | ✅ **yes — it ships** | 🥇 **gets the day** |
| **RTX 2060 Super** | ✅ yes, shop machine | 🥈 twenty minutes of it, at the front |
| **RTX 5060 Ti** | ❌ **never — it is the local box** | 🥉 **drops out entirely.** It is reachable every day this project continues |

⚠️ **The 5060 Ti section is kept below, demoted, for one reason only:** if Sunday at the shop
collapses, it is a real GPU day that needs no travel. It is **Plan B, not overflow.**

🛑 **ONE THING TO CONFIRM BEFORE ANYTHING ELSE: when does the 3070 Ti actually ship?** This file has
never recorded a date, and every priority on it rests on that card being the thing that expires. If
it is still reachable next weekend, the ordering below is wrong and the 5060 Ti items come forward.

---

## 🛑 The constraint that kills parallelism — one kit, one machine

**There is one collection kit on one USB stick, and a suite runs *from* it** —
`$kit\python\python.exe` and `$kit\tools\...`. It cannot be unplugged while a 62-minute suite is
running, and the kit installs nothing and leaves nothing behind, so no shop machine holds a local
copy.

⛔ **Therefore the 3070 Ti and the 2060 Super are strictly serial**, and the long unattended suite
blocks inside Session D are **not** slots the 2060 Super can fill. Plan those twenty minutes at the
front or not at all.

✅ **The 5060 Ti is the exception** — it is the local machine with a full checkout and needs no kit.
But it is also the machine the operator sits at, and 2026-09-18 measured that ordinary desk work on
it depresses throughput **9.38% at every point**. **A 5060 Ti sweep and desk work are mutually
exclusive**, which is the other half of why it is Plan B.

---

## The honest budget

| block | measured time | card |
|---|---|---|
| Suite calibration | ~10 min | per card, once |
| **12-workload suite** | **~62 min** | any |
| gemm + membw pair | ~11 min | any |
| 13-point fine sweep | ~12 min | any |
| Stability soak | 30 min + setup | any |
| Afterburner install + snapshot | ~15 min | shop machines only |
| One curve edit | ~10 min | by hand |
| Revert, verify, uninstall | ~20 min | shop machines only |

⚠️ **Preflight is ~3 minutes and it is per RUN, not per machine.** Instant Replay went 0% → 14%
inside one session once because someone switched it back on. Re-check every time.

---

# 🛑 THE GO / NO-GO, AND IT IS THE MOST IMPORTANT LINE ON THIS PAGE

**Session D needs ~5 h 40 min end to end. The shortest version that is still worth running is
~4 h 25 min.** Below that the session does not produce the thing it exists to produce.

⛔ **A manipulation without its control is worth well under half the pair**, and the outside reader
was explicit that the region-targeted edit **with a negative control** is the one design it could
not find published. A three-hour Session D buys a second-chip treatment replication and **not** the
design the contribution sentence rests on.

**So: count the hours available at that machine BEFORE installing anything.**

| hours at the 3070 Ti | do this |
|---|---|
| **5½ +** | full Session D, all ten steps |
| **~4½** | Session D minus steps 9 and 8 — see the cut ladder |
| **under ~4¼** | ⛔ **do not start it.** Run the 2060 Super's twenty minutes, then go home and run the 5060 Ti items. Keep Session D whole for a day that has the hours |

⚠️ **The one exception, and it needs the answer to the shipping question above:** if the card leaves
and does not come back, a stock + Edit 1 pair is better than nothing — it replicates the *treatment*
on a second chip and a second architecture. **Write it up as that and never as the controlled
design.** This is the only circumstance in which the "run the control or do not run the session"
rule bends.

---

# 🥈 FIRST, TWENTY MINUTES — the RTX 2060 Super descending sweep

**Moved to the front of the day, because the kit cannot come back for it.** `SESSION-E-RUNSHEET.md`
Part 1b, registered §4d. Stock, nothing applied, nothing to clean up, no Afterburner.

⚠️ **Do this only if it does not push the 3070 Ti start past the go/no-go threshold above.** Twelve
minutes of sweep plus preflight plus a kit re-sync is realistically ~20 minutes at the machine, and
travel between the two boxes is on top of that.

```powershell
.\tools\collection-kit\Sync-Kit.ps1 -KitPath D:\headroom-kit
```

⛔ **The re-sync is not optional.** `-Descending` did not exist until 2026-09-15; a kit synced before
that rejects it as an unknown parameter and the run dies at the command line.

```powershell
$kit = "D:\headroom-kit"; Test-Path "$kit\python\python.exe"; Test-Path "$kit\tools\frequency-sweep\gpu_workload.py"
```

Start a **new** HWiNFO log (`…-finefloor-desc-hwinfo.csv`), then:

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -Descending -SessionLabel "rtx2060s-finefloor-desc-gemm" -WorkloadCommand "$kit\python\python.exe $kit\tools\frequency-sweep\gpu_workload.py --workload gemm --json" -MinFrequencyMhz 900 -MaxFrequencyMhz 1140 -FrequencyCount 13 -AppliedSettings "stock, PL default, no OC - fine floor probe 900-1140 DESCENDING order, thermal control for 4d"
```

**Check the banner counts DOWN from 1140** before walking away. That ordering *is* the experiment.

| result | reading |
|---|---|
| minimum stays at **975–1005** | ✅ the shape belongs to the V/F curve |
| minimum **follows the cold end** (now the top) | ⛔ thermal — and **every floor extent on all four cards** needs re-reading |

⚠️ **Do not oversell it.** The confound is already partly bounded: the 3060's floor is flat across a
**10.2 °C** warm-up, moving less than one 6 mV code. This tests a card-specific oddity, not a
project-wide invalidation. **It is twelve minutes against a small chance of a large problem** — which
is why it earns the front of the day and does not earn delaying Session D.

⛔ **Part 2 of Session E — the boundary manipulation, ~3 hours — is OFF the plan.** It cannot coexist
with Session D in one day and Session D outranks it. The run sheet's own advice applies: *"If
Saturday overran, do 2a and skip 2b."*

---

# 🥇 THE REST OF THE DAY — the RTX 3070 Ti, Session D

**`data/frequency-sweeps/rtx3070ti-20260825/SESSION-D-RUNSHEET.md`. Predictions §4a–4b, registered.**

🔑 **It is the only item on this list that changes what the paper can claim** — one chip becomes two
chips and two architectures, which is the weakness a reviewer names in thirty seconds.

⚠️ **And run 3 matters more than it did when this plan was written.** The 5060 Ti's negative control
is **partially leaky** — 4 of 12 workloads move, median +0. A second chip's control is the cheapest
evidence that the leak is chip-specific rather than the mechanism.

⛔ **Read the run sheet at the machine. It was wrong until 2026-09-16 and the fix matters:** the
table said `gemm, membw`, but 4a is registered on the **median suite optimum** over twelve workloads.
Two workloads cannot test it. **Every configuration is a full suite, ~62 minutes.**

### Order, ~5 h 40 min including preflights

| # | what | time | cut? |
|---|---|---|---|
| 0 | Install Afterburner, **snapshot `Profiles\*.cfg` verbatim + SHA-256** | 15 min | never |
| 1 | `Calibrate-Suite.ps1` on **stock** — write the 12 numbers down, never re-run | 10 min | never |
| 2 | **Stock suite** — today's baseline, do not reuse the 08-27 sweeps | 62 min | never |
| 3 | Apply **Edit 1** (≤0.819 V → 1200 MHz, everything ≥0.831 V untouched) | 10 min | never |
| 4 | **Edit 1 suite** — the manipulation | 62 min | never |
| 5 | Apply **Edit 2** (flatten ≥0.831 V to 1500, floor region untouched) | 10 min | never |
| 6 | **Edit 2 suite** — the negative control | 62 min | 🛑 **never.** This is the contribution |
| 7 | Revert to stock, **verify it took three ways** | 10 min | never |
| 8 | **Stock suite** — closes the bracket, must match run 2 | 62 min | 🥈 **second cut** |
| 9 | **Descending stock fine sweep**, `-Descending` — §4d on a third architecture | 12 min | 🥇 **first cut** |
| 10 | Uninstall Afterburner and its profile store | 10 min | never |

### The cut ladder, in order, with what each one costs

**🥇 First cut — step 9, the descending fine sweep. −12 min.** §4d is being tested on the 2060 Super
at the front of the day, on the one card that actually showed the non-monotonicity. A third
architecture is corroboration, not the test.

**🥈 Second cut — step 8, the closing stock suite. −65 min.** This is the real cut and it is not
free: runs 2 and 8 bracket within-session drift, and without run 8 every comparison rests on a single
baseline taken before three hours of work.

✅ **Why the registered prediction survives it anyway.** §4a is a shift in the **median suite
optimum**, located on a ~158 MHz grid, and the effect on the 5060 Ti was **+465 MHz — three grid
points**. Cross-session drift measured on that card is **~1.47% on `gemm` throughput**, which does
not move a grid point. **The drift bracket is evidence about measurement quality, not about whether
the optimum moved.** Losing it weakens the write-up; it does not invalidate the result.

⛔ **There is no third cut.** Steps 2, 4 and 6 are the experiment. Steps 0, 1, 7 and 10 are what make
the data readable and the card shippable.

✅ **Both edits are safe by construction.** After either, the card takes *more* voltage for a given
clock than stock. You are dragging points down, never up. Instability is not reachable.

🛑 **A driver reset silently clears Afterburner offsets.** If one happens mid-suite, that suite is
stock silicon wearing a tuned settings string. Watch for it and re-run rather than keep the data.

**Separate HWiNFO log per configuration** — the join bins by core clock and one log spanning two
curves mixes them with nothing to separate them afterwards.

---

# 🔵 PLAN B — the RTX 5060 Ti, local, ~1 h 20 min of GPU work

⛔ **Not overflow. Use this only if the shop day does not happen at all**, or if the go/no-go above
says do not start Session D. **This card does not expire, and spending Sunday on it while a shipping
card sits untouched is the one scheduling mistake this page exists to prevent.**

Full commands: `docs/5060TI-SWEEP-QUEUE.md`. Run the preflight in that file first — **power limit
must read 180.00 W, and `nvidia-smi pmon -c 5 -s u` must show a baseline under ~5%.**

| # | what | time | why |
|---|---|---|---|
| **4j** | memory-**matched** flattened-vs-stock, voltage + XBAR logged | **~35 min** | 🥇 removes the single largest confound behind the §5.7 retraction |
| **4b** | descending fine floor, 1380–1760 | 12 min | the floor the project rests on, measured in the other direction |
| **4c** | NVML offset precondition | 10 min | 🛑 gates 4d; ten minutes decides whether the next twenty-five are worth spending |
| 4h | pin the floor end, 1530–1620 | 12 min | states 1560–1590 as a measured number. Changes no verdict |

## 🆕 4j costs more than 25 minutes, because the profile it needs does not exist

**Checked against `docs/AFTERBURNER-PROFILES.md` on 2026-09-19: there is no memory-matched pair in
the five slots.** Every flattened profile carries a memory overclock and stock carries none —

| profile | curve | mem boost |
|---|---|---|
| P1 | flattened | **+2000** |
| P2 | repair | **+2500** |
| P3 | **stock** | **+0** |
| P4 | full tune | **+2500** |
| P5 | split | **+2500** |

⚠️ **So 4j needs a profile built first: load P4, set the memory slider to +0, save.** That is one
slider, not a curve edit — the flattened core curve is untouched, and **+2500 → +0 is strictly the
safe direction.** Budget ~10 minutes for building and verifying it, on top of the 25.

🛑 **Afterburner has five slots and they are all occupied**, so saving overwrites one. **Snapshot
`Profiles\*.cfg` with SHA-256 before saving anything**, and overwrite **P1** — it is the least-used
configuration and the only one no live claim depends on. A slot number is not an identity; P3 held
an aggressive curve one day and stock the next.

⚠️ **4j needs the operator present twice**, once per configuration, because HWiNFO logging must start
and stop around each one and **one log must never span two configurations.** It is not an unattended
run.

⛔ **What 4j does NOT settle:** mediation. That needs direct XBAR intervention at fixed core curve and
fixed MCLK, which needs runtime XBAR control this card does not have.

---

## If Monday 2026-09-21 survives after all

The original window ran to the 21st. **If it does, the order does not change** — it extends:
Session D's dropped steps 8 and 9 come back first, then Session E Part 2 (~3 h), then the 5060 Ti
list above. ⚠️ **Do not bank on it while planning Sunday.** Plan Sunday as the only day and treat
Monday as recovered time.

---

## The rules that do not bend

1. **Preflight every run.** Instant Replay off, encoder and decoder 0, baseline under ~5%. A 6%
   baseline once cost 10.3% at 1545 MHz. **Use `nvidia-smi pmon -c 5 -s u`, not the aggregate** — on
   2026-09-18 the aggregate said "something" and `pmon` named `dwm.exe` in seconds.
2. ⛔ **Then leave the machine alone.** On 2026-09-18 the operator's own test-suite and git runs
   depressed throughput **9.38% at every point** while the preflight had passed cleanly minutes
   earlier. **A passing preflight says nothing about what happens during the run**, and a
   point-to-point residual cannot detect it afterwards — it is blind to a uniform offset.
3. **`-AppliedSettings` describes the curve actually applied.** Nothing reconstructs it later. This
   is why the earliest tuned data in this project is unusable.
4. **Snapshot the profile store before the first edit.** A slot number is not an identity.
5. **One HWiNFO log per configuration.** Never one spanning a change.
6. **Bind `$kit` once** and derive every path from it. Mixing `D:` and `F:` in one command line has
   already cost an hour on the 2060 Super.
7. **Revert and verify three ways before any card ships** — power limit, memory clock under load,
   peak core against its stock ceiling. Then remove Afterburner and its profile store.
8. **A null is a result.** If the optimum does not move on the 3070 Ti, that is the headline and it
   gets written up as one.
