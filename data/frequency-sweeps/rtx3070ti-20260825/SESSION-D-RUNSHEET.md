# Session D — the causal replication on the RTX 3070 Ti

**Work off this sheet at the machine.** Predictions are already registered in
`docs/REGISTERED-PREDICTIONS.md` §4 — do not read them for the first time here, and do not change
them after seeing a result.

**Why this session exists:** every confirmation of the load-floor rule on this card so far is
*observational*. Only the 5060 Ti has a causal arm, which makes the headline result n=1 chip. This
session makes it two chips and two architectures.

⚠️ **Use the SILENT BIOS.** Every number below is measured from the silent-BIOS runs of 2026-08-27.
The OC BIOS has a similar floor but the 1500/1545 boundary was established on silent, and the
prediction is derived from it.

---

## The stock curve, as measured on this card

Not from a spec sheet — read out of `hwinfo-silent*/…_voltage.csv` in this directory.

| core MHz | measured V | | core MHz | measured V |
|---|---|---|---|---|
| 855 | 0.819 | | 1455 | 0.812 |
| 960 | 0.819 | | 1485 | 0.812 ← **measured optimum** |
| 1065 | 0.812 | | **1500** | **0.812 ← floor ENDS** |
| 1170 | 0.819 | | 1545 | 0.831 ← first rise |
| 1275 | 0.819 | | 1590 | 0.850 |
| 1380 | 0.812 | | 1695 | 0.894 |
| 1410 | 0.812 | | 1800+ | 0.931, **clips to ~1763** |

**Floor voltage 0.812–0.819 V** (±6 mV is one sensor step, so treat these as one value) **held
across 645 MHz**, 855 → 1500. Median suite optimum **1485 MHz**, 7 of 12 workloads picking it —
one grid step below the floor end, exactly as the rule says.

⛔ **THE FLOOR BAND IS THREE CODES WIDE, NOT TWO — CORRECTED 2026-09-20, AND IT MOVES THE EDIT
BOUNDARY BELOW.** The coarse sweep sees only {0.812, 0.819}, but the **fine** sweep — the one that
located the floor end at 1500 — reads **0.825 V at 1200 MHz**, inside the flat region. On this
card's **6.25 mV** grid the codes run 812.5 / 818.75 / **825.0** / 831.25, so a boundary written as
*"≤ 0.819 versus ≥ 0.831"* leaves **825 mV unassigned** — and 825 mV is a real, draggable point in
the curve editor. 🔑 **An unassigned point is not a formatting detail here:** left at stock during
Edit 1 it would still reach ~1500 MHz at floor voltage, so the floor would not actually shorten and
the manipulation would test nothing. **Both edits below now use 0.825 as the boundary**, which is
exhaustive on the grid with no point unnamed.

🔑 **The card is POWER-CAPPED at ~1763 MHz.** Only ~263 MHz of usable range exists above the floor
end. That single fact constrains the negative control below, and it is why this session's control
is smaller in magnitude than the 5060 Ti's 570 MHz. Say so in the write-up rather than quietly
comparing them.

---

## The two edits

Both are in the **safe** direction. Neither raises voltage, neither raises the power limit, neither
touches memory. In curve-editor terms you are dragging points **down**, never up.

### EDIT 1 — shorten the floor (this is 4a)

> **At every curve point at or below 0.825 V, set the clock to 1200 MHz. Leave every point at
> 0.831 V and above exactly at stock.**

Stock reaches 1500 MHz at floor voltage; after the edit it reaches only 1200 MHz there, so voltage
must begin rising at **1200 instead of 1500** — the floor end moves **−300 MHz**.

| curve point | stock clock | set to |
|---|---|---|
| **below 0.812 V** | low | 🛑 **DO NOT TOUCH — see below** |
| 0.812 V | ~1500 | **1200** |
| 0.819 V | 1500 | **1200** |
| **0.825 V** | **~1500** | **1200** ⬅ was unassigned until 2026-09-20 |
| 0.831 V and above | 1545 → 1763 | **unchanged** |

🛑 **"AT OR BELOW 0.825 V" MUST NOT BE READ AS "EVERY POINT DOWN TO THE LEFT EDGE OF THE EDITOR".**
The curve editor carries points well below 0.812 V whose stock clocks are far *under* 1200 MHz.
Setting those **to** 1200 raises them — the unsafe direction — and asks the card for 1200 MHz at
~0.70 V. ⚠️ **This project has already crashed a display driver exactly that way**: 875 mV pinned
at 3000 MHz on the 5060 Ti, eleven driver-reset events, and the reset silently cleared the
Afterburner offsets so the run would have measured stock silicon under a tuned settings string.

✅ **Touch only 0.812, 0.819 and 0.825 V.** Nothing below 0.812 V is ever applied under load — the
card clamps to its floor, which is what "load floor" means and what the whole session is about — so
leaving them at stock costs the experiment nothing and keeps every edit in the down-only direction.

✅ **Why this is the safe direction, and why it is also the better experiment.** After the edit the
card uses *more* voltage for any given clock than stock, so instability is not possible by
construction. And the 5060 Ti manipulation moved the floor **up** (+465 MHz); moving it **down**
here tests the same claim in the opposite direction, which rules out "any curve edit pushes the
optimum upward". A same-direction replication could not do that.

**Registered prediction (4a):** the median suite optimum moves down from **1485 MHz** to the grid
point nearest the new floor end — **1170 or 1275 MHz** on the 105 MHz suite grid.
⛔ No movement, or upward movement, **refutes the causal claim on a second chip** and is the
headline if it happens.

### EDIT 2 — the negative control (this is 4b)

> **Flatten everything from 0.831 V upward to a constant 1500 MHz. Leave every point at or below
> 0.825 V at STOCK (i.e. reaching 1500 MHz).**

| curve point | stock clock | set to |
|---|---|---|
| ≤ 0.825 V | ~1500 | **unchanged (stock)** |
| 0.831 V | 1545 | **1500** |
| 0.850 V | 1590 | **1500** |
| 0.894 V | 1695 | **1500** |
| 0.931 V and above | ~1763 | **1500** |

That is a **−263 MHz** change at the top, which is all the range this card has above its floor.

**Registered prediction (4b):** the optimum stays at **1485 MHz**. The whole floor region is
untouched, so if the optimum moves, the rule's attribution to the *floor* region is wrong.

⚠️ **Expect the top of the sweep to clip.** Every target above 1500 will achieve ~1500. That is
intended and is the evidence the edit took — it is not a failed run.

🔑 **Run the control or do not run the session.** A manipulation without its control is worth well
under half the pair. If time runs short, drop a replicate, never Edit 2.

---

## Order of operations — A/B/B/A

Drift between sessions on one unchanged configuration has been measured at ~1.47% on `gemm`, which
is larger than several effects this project reports. A/B/B/A brackets it.

⛔ **THIS TABLE SAID "gemm, membw" UNTIL 2026-09-16 AND IT COULD NOT HAVE TESTED ITS OWN
PREDICTION.** 4a is registered on the **median suite optimum** — *"moves down from 1485 MHz"*, a
figure that comes from the twelve-workload suite with **7 of 12 workloads** on the median. Two
workloads produce no median of twelve and nothing comparable to 1485. The session would have run,
looked successful, and answered a different question.

| # | config | workloads | why |
|---|---|---|---|
| 1 | **stock** | **full 12-workload suite** | today's baseline — do NOT reuse the 08-27 sweeps |
| 2 | **Edit 1** | **full suite** | the manipulation |
| 3 | **Edit 2** | **full suite** | the negative control |
| 4 | **stock** | **full suite** | closes the bracket; must match run 1 |

**The suite is `copy, reduce, softmax, layernorm, bgemm32, bgemm64, bgemm128, bgemm256, bgemm1024,
attention, conv, gemm`** — and it measures **60–64 minutes per configuration**, from the two
twelve-workload suites already collected. Budget four hours of sweeping, not one.

🔑 **The Edit-1 replicate is what got dropped, not the control.** This sheet's own rule is "drop a
replicate, never Edit 2", and at 61 minutes a run that rule now has teeth. Runs 1 and 4 bracket
drift between them, which is the job the replicate was mostly doing.

✅ **If the day runs long, stop after run 3 and run 4 first thing next session** — but then the
bracket spans a session boundary and ~1.47% cross-session drift applies, so say so in the write-up.

⛔ **If run 4 does not come back to run 1 within ~1.5%, the session is drift-contaminated** and the
manipulation result is not interpretable. Report that rather than the effect.

**Grid: hold the suite grid constant across every run — 855 to 2115 MHz in 105 MHz steps.** A grid
that changes between configurations breaks the fixed-work property that makes duration a valid
performance metric.

⛔ **"ITERATION COUNTS MUST BE RE-DERIVED ON THIS CARD" IS CORRECTED 2026-09-20. THEY ALREADY
EXIST, FOR THIS EXACT CARD.** The line was written when no 3070 Ti suite had been collected. One
has: `rtx3070ti-suite-20260904/` is the twelve-workload run that **produced the 1485 MHz median
optimum this sheet registers its prediction against**, and every sweep JSON in it carries its
`--iterations` value.

| workload | iterations | | workload | iterations |
|---|---:|---|---|---:|
| copy | 4099 | | bgemm128 | 3511 |
| reduce | 4291 | | bgemm256 | 2327 |
| softmax | 3230 | | bgemm1024 | 616 |
| layernorm | 2462 | | attention | 135 |
| bgemm32 | 843 | | conv | 432 |
| bgemm64 | 2113 | | gemm | 120 |

🔑 **Re-calibrating would be actively worse than reusing these.** The registered prediction is
*"the median moves down from 1485"*, and 1485 is a property of the 09-04 suite at these counts.
Re-deriving changes the work per point, so run 1 would no longer be comparable to the run that
produced the number being predicted against. Reusing them makes run 1 a **same-card, same-config,
same-work replicate of 09-04** - a cross-session drift check spanning sixteen days, for free.

⚠️ **The 09-04 suite ran on driver 610.88.** Read the current driver off a new sweep JSON, never
off a document, and state the difference in the write-up. Counts describe work, not driver, so they
transfer; the *comparison* to 09-04 carries a driver gap.

✅ `SUITE-ITERATIONS.md` holds 5060 Ti counts and those still do not transfer. Calibration is now
optional here - run it only to sanity-check that ~9 s per point still holds, and then use the
table above regardless.

---

## The exact commands, and the one thing the kit does NOT have

✅ **The sweeps go through `Collect.ps1`.** This card's original suite used band **852–2130 MHz,
13 points, settle 8, measure 20**, which is the kit's default band on this GPU — so no explicit
frequency arguments are needed, and matching the original collection is what makes the comparison
valid.

```powershell
$kit = "D:\headroom-kit"; cd $kit        # check the letter with Get-Volume; it is not always the same
.\Calibrate-Suite.ps1                     # FIRST. Iteration counts are per card. ~10 min.
```

Write the twelve numbers down. Then, for each configuration, with `-Iterations` matched to
`-Workloads` **by position** and **held identical across all four runs**:

```powershell
.\Collect.ps1 -Label "rtx3070ti-sessiond-stock-1" -AppliedSettings "stock, silent BIOS" -Workloads copy,reduce,softmax,layernorm,bgemm32,bgemm64,bgemm128,bgemm256,bgemm1024,attention,conv,gemm -Iterations <n1>,<n2>,<n3>,<n4>,<n5>,<n6>,<n7>,<n8>,<n9>,<n10>,<n11>,<n12>
```

⛔ **Calibrate ONCE, at the start, on stock — never again between configurations.** A re-calibrated
count changes the work per point, which breaks the fixed-work property that makes duration a valid
performance metric and makes the four runs incomparable. This is the same rule as "hold the grid
constant", applied to the other axis.

🛑 **RUN HWiNFO LOGGING ACROSS EVERY SWEEP.** `HWiNFO64.exe` ships on the kit; its `HWiNFO64.INI`
sets `SensorInterval=500`. NVML exposes no voltage at all, so **HWiNFO is the only evidence that a
curve edit actually took** — and a driver reset silently clears Afterburner offsets, which would
otherwise produce a whole sweep of stock silicon wearing a tuned settings string.

⛔ **A separate log per configuration.** The join bins samples by core clock, so one log spanning
stock and Edit 1 mixes two curves into one table with nothing to separate them. Stop the log at
every curve change and start a new file.

Then repeat with `-Label ...-edit1-2`, `...-edit2-3`, `...-stock-4` after each curve change.
**`-AppliedSettings` must describe the curve actually applied** — it is the field nothing can
reconstruct afterwards, and the reason the earliest tuned data in this project is unusable.

⛔ **AFTERBURNER IS NOT IN THE KIT AND WILL NOT BE.** The kit installs nothing and leaves nothing
behind; that is its whole design. A manipulation needs Afterburner present on the target machine,
which means **installing it, applying curves, and removing it and its profile store afterwards**.
That is a materially larger footprint than a stock sweep and it is the part to plan for.

⚠️ **There is no script that snapshots a profile store.** The one committed snapshot
(`data/afterburner-profiles/5060ti-profiles-20260908.json`) was produced ad hoc and only
`predict_from_curve.py` reads it. For this card, **copy the raw `Profiles\*.cfg` verbatim into
`data/afterburner-profiles/` and record each file's SHA-256** — that satisfies the reconstruction
purpose with no tooling, and the device ID in the filename identifies the card.

## Before you touch anything

1. **Snapshot the Afterburner profile store verbatim** into `data/afterburner-profiles/` before the
   first edit. A slot number is not an identity — this convention exists because P3 held an
   aggressive curve one day and stock the next.
2. 🛑 **VERIFY THE BIOS SWITCH IS STILL IN SILENT, AND DO IT WITH nvidia-smi.** This card has a
   dual-BIOS switch, it was **found in SILENT and returned to SILENT**, and every number this
   session predicts against - the 1485 MHz optimum, the 0.812-0.819 V floor, the ~1763 MHz power
   cap - is a SILENT-position measurement. The two positions are distinguishable in one command,
   because they differ in power envelope:

   ```
   nvidia-smi --query-gpu=power.limit,power.default_limit,power.max_limit --format=csv,noheader
   ```

   | reads | position |
   |---|---|
   | **290 / 290 / 320 W** | ✅ SILENT - proceed |
   | 310 / 310 / 350 W | ⛔ OC - the baseline does not apply. Switch back, reboot, re-check |

   Record the position and the driver version in `-AppliedSettings`, with the driver read off a
   sweep JSON rather than from any document.
3. **Preflight:** Instant Replay / ShadowPlay **off**; browsers, Discord, Steam, media players
   closed. Verify idle baseline **under ~5%** and encoder/decoder at 0%. A passing 10% guard is not
   enough — a 6% baseline still cost 10.3% at 1545 MHz once.

## After the manipulation runs — before the card ships

4. **Stability protocol** on the final configuration. Say "no failure observed in thirty minutes",
   never "stable".
5. **Revert to stock and VERIFY IT TOOK**, three ways: power limit reads stock, memory clock under
   load reads stock, peak core reaches its stock ceiling. 🛑 **A driver reset silently clears
   Afterburner offsets**, so a card can report a tuned settings string while running stock silicon —
   that failure has already happened once in this project and would have produced a whole sweep of
   mislabelled data.
6. **Remove Afterburner and its profile store.** The collection kit installs nothing and leaves
   nothing behind; this session does, and that is the part to undo.

---

## What each outcome means

| result | reading |
|---|---|
| optimum moves to 1170/1275, control unmoved | ✅ **The causal claim replicates on a second chip and architecture.** This is the sentence the paper cannot currently write. |
| optimum moves, control ALSO moves | ⛔ The attribution to the floor region is wrong. Bigger finding than a clean pass, and it must be reported. |
| optimum does not move | ⛔ Refutes the causal claim off the 5060 Ti. Report as the headline; the 5060 Ti result becomes single-chip. |
| run 4 ≠ run 1 | ⚠️ Drift-contaminated. Report nothing about the effect. |

⚠️ **Whatever happens, this is still one chip per architecture.** A successful replication makes the
claim "causal on two chips across two architectures", not "general". The scope sentence in the
paper — *strong within-chip causal evidence, generalisation uncertain* — widens; it does not
disappear.
