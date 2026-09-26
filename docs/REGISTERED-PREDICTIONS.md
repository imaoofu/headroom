# Registered predictions

**Predictions written down, committed, and timestamped BEFORE the measurement exists.**

This file is a commitment device. A mechanism that explains results after the fact explains
anything; one that states a number in advance can be wrong in public. Two arms of the load-floor
result were already registered this way — `abba-20260908` and `repair-suite-p2-20260909` both name
the predicted optimum in their READMEs ahead of the data — and this file is where that practice
lives from now on, so a reader does not have to take the claim on trust.

**Rules.**

1. An entry is committed **before** the profile is built or the sweep is run. The commit date is the
   evidence. ⛔ **Never edit a prediction after data exists** — add a result block underneath it and
   leave the original wording alone, wrong or right.
2. Every entry states **what would refute it**, not only what it expects.
3. Every entry states a **safety envelope** before anything is applied to the card.
4. A refuted prediction stays in this file with the refutation written under it. That is the point.

---

## 1. The floor ladder — registered 2026-09-11. Rung B ✅ COLLECTED 2026-09-23, HOLDS; rung C PENDING

**Status: profiles not yet built, no data collected.**

### What is being tested

The load-floor mechanism currently rests on configurations that produce **only two distinct predicted
values** — 1530 MHz and 2002 MHz. That is the limitation `analysis/models/predict_from_curve.py`
states about itself: *"configuration is close to a binary variable here."* A rule that has only ever
been asked a yes/no question has not been asked much.

This adds two intermediate rungs so the configuration axis becomes a **four-point monotone ladder**
instead of a switch.

### Design

Both new profiles are **P5's curve with only the region below ~850 mV raised by a fixed offset.**
Everything at and above 860 mV is P5, unchanged and byte-identical.

That region is the right one to move because **P5 below 840 mV is exactly stock** — all 63 points
at or below 840 mV are identical to Profile 3 to the megahertz (1447 / 1530 / 1695 / 1852 / 1987 MHz
at 700 / 720 / 760 / 800 / 840 mV) — and P4 is stock **+465 to +472** across the same span.

⚠️ **The two points at 845 and 850 mV are NOT stock** (+202 and −2 against Profile 3), and 845 mV is
also where P5's curve steps *backward* — 2362 MHz at 845, 2180 at 850. Leave both alone; they sit
above the load floor and outside the region this experiment moves.

| rung | offset below 850 mV | source | clock at 0.720 V | **predicted optimum** |
|---|---|---|---|---|
| A | +0 | P5 / P2 / stock — **have it** | 1530 | 1545 |
| **B** | **+170** | **to build** | ~1700 | **1702** |
| **C** | **+320** | **to build** | ~1850 | **1852** |
| D | +472 | P4 — **have it** | 2002 | 2010 |

⚠️ **Precision is not required.** The prediction depends only on which grid point the floor extent is
nearest to, and the grid steps are ~150 MHz wide. The acceptance windows for the **720 mV** point:

- **Rung B predicts 1702** for any floor extent in **1624–1777 MHz**
- **Rung C predicts 1852** for any floor extent in **1778–1931 MHz**

Aim at 1700 and 1850; anywhere inside those windows registers the same prediction.

### The predictions

**Primary, and the one that counts:**

> **The median efficiency optimum across the twelve-workload suite equals the grid point nearest the
> frequency the applied curve reaches at 0.720 V — 1702 MHz on rung B and 1852 MHz on rung C.**

This has held on **4 of 4** configurations measured so far (stock, split, repair, full tune), median
exact every time.

**Secondary, calibrated against what the mechanism currently achieves per sweep:**

> **At least 7 of the 12 workloads land individually on the predicted grid point** on each rung.

Observed rates on existing configurations are **83% stock, 75% repair, 69% split, 62% full tune**, so
7 of 12 (58%) sits just below the worst case seen. A rung that comes in materially under that is
information even if the median is right.

**Tertiary, the reason the ladder is worth more than another replicate:**

> **The predicted optimum moves monotonically with the offset, and the four measured optima are
> 1545 / 1702 / 1852 / 2010 — evenly spaced, one grid step apart.**

A switch that flips is weak evidence. A quantity that tracks a knob across four levels is not.

### ⛔ What refutes this

- **The median on either new rung lands on a different grid point.** Not "is a bit off" — the median
  is a grid point, so it either matches or it does not.
- **The optima do not increase monotonically** across A → B → C → D.
- **Both new rungs land on the same grid point as each other**, which would mean the optimum snaps
  between two states rather than tracking the curve — the mechanism would be a threshold effect, not
  the relationship claimed.
- **`reduce` is excluded from none of this.** It is sub-optimal in 16 of 16 existing sweeps and is
  expected to miss here too; a prediction that quietly drops its worst case is not a prediction.

### Safety envelope — check before applying

🛑 **Nothing in the profile set is stability tested, and the one hard crash on record is 875 mV at
3000 MHz.** The envelope argument is what makes this design safe rather than the numbers being small:

- **Below 850 mV**, every point of both new curves lies **between stock (+0) and P4 (+472)** at the
  same voltage. Both bounding configurations have run multi-hour suites without a failure.
- **At and above 860 mV**, both curves are **P5 unchanged**, which has also run multi-hour suites.

So no point of either curve is outside a region already exercised for hours. **This is interpolation
inside a tested envelope, not extrapolation past it.**

⛔ **Do NOT build these with the global Core Clock slider.** A global offset raises the top of the
curve too: at +320 the card would reach 3030 MHz at roughly 890 mV, against a known crash at 875 mV /
3000 MHz. **The top of the curve must not move.** Raise the sub-850 mV points only.

### Pre-run verification, to be done before any sweep

Decode each saved profile from `Profiles\*.cfg` and confirm mechanically:

1. Clock at 720 mV falls inside the rung's acceptance window above.
2. Every point at or above 860 mV is **identical to P5**.
3. Every point below 850 mV lies between stock and P4 at the same voltage.
4. The curve is monotonic across the 850/860 boundary.
5. Snapshot the profile store to `data/afterburner-profiles/` **before** collecting, as
   `abba-20260908` had to learn — a slot number is not an identity.

### Result

*(filled after collection, without editing anything above)*

✅ **Rung B, collected 2026-09-23 — primary and secondary both HOLD.**
`data/frequency-sweeps/5060ti-rungB-suite-20260923/`, twelve workloads, unattended, profile store
verified byte-identical to the rung B snapshot and +2500 memory witnessed live at every point.

| registered | measured |
|---|---|
| **primary:** median optimum 1702 | ✅ **1702** |
| **secondary:** at least 7 of 12 on 1702 | ✅ **9 of 12**. copy and bgemm32 at 1852, `reduce` at 2167; none excluded |
| **tertiary:** 1545 / 1702 / 1852 / 2010, monotone | 🟡 **3 of 4 rungs on their points (A, B, D), in order.** C is not collected, so this is not scored |

**Refutation did not occur** for rung B: its median is the predicted grid point. The "both new rungs
on one point" refutation needs rung C. ⚠️ **One chip, one suite, a ~155 MHz grid**; twelve workloads
are repeated outcomes on one card.

**Also measured, not registered:** `gemm` holds 0.720 V through **1695 MHz achieved** on rung B,
where P5 had already risen to 0.755, and matches P5's VID codes from 2317 to 2782 MHz. That is the
above-floor equivalence the pre-run check below could not establish from the file. Details and the
missed-lock pattern above 2317 MHz are in the data README.

**Rung C** can now be built into P1: the rung B store is preserved in its snapshot.

⛔ **Pre-run verification of rung B, 2026-09-22 (built into P1, decoded from the live store).**
Check 1 passes: 720 mV reads **1702**, inside 1624–1777. Check 2 passes: everything at 850 mV and above is
P5. Check 4 passes: 850 → 860 mV rises. ⛔ **Check 3 FAILS, and the fault is in this registration,
not the build.** "Every point below 850 mV lies between stock and P4" is impossible at **650–690 mV**,
because **P4 IS stock there**, so any raised rung exceeds it: rung B has 997 MHz at 650 mV against P4's
817. The card never runs below 0.720 V under load, so this matters at light load only. But the
envelope argument above is false at those points. ~~⚠️ **845 mV is unresolved.**~~ ✅ **Resolved
2026-09-22:** the editor shows 2362, +0, and a re-save was byte-identical, so the stored (+176, 2362) is
the same state, mispaired by the decoder at an offset boundary. Check 5 is done: snapshot
`data/afterburner-profiles/5060ti-profiles-20260922-rungB/`. **Rung B is ready for collection.**

---

## 2. Profile 1 — ✅ COLLECTED 2026-09-22, THE PREDICTION HOLDS

**Status: swept.** `data/frequency-sweeps/5060ti-p1-suite-20260922/`, twelve workloads
× 13 frequencies, unattended, operator absent.

> **Measured median optimum: 2010 MHz — the registered grid point. Seven of twelve workloads
> land on it individually** (attention, bgemm64, bgemm128, bgemm256, bgemm1024, conv, copy).
> The other five: gemm 1852, bgemm32 1545, layernorm 2167, softmax 2167, reduce 2475.

✅ **Checked by an outside audit against the pre-collection revision `1f6f3d6`, 2026-09-22.** The
registered test was **the median alone**: 2010 MHz, refuted by any other grid point. It passed.
⚠️ **The 7 of 12 is descriptive. No per-workload threshold was registered, so it is not a second
success.** And the test is **coarse**: the registration expected P1 and P4 floor extents 30 MHz
apart, which a ~155 MHz grid cannot resolve. P1 and P4 also differ in power limit and memory
together. Record: `docs/gpt-findings/2026-09-22-5060ti-session-results-audit.md`.

🔑 **What it tests that nothing else did.** The manipulation moved the floor and the optimum
followed; the negative control moved the curve *above* the floor and it did not. **P1 holds the
floor region fixed and changes POWER LIMIT (180 W against P4's 200 W) and MEMORY (+2000 against
+2500)** — the two variables neither existing arm touches. The optimum did not move.

⚠️ **Two variables at once, so a movement would not have identified which caused it.** That
asymmetry is what makes the test admissible: the prediction is refuted *by movement*, whatever its
cause, because the mechanism claims the floor extent is sufficient. **State it that way, never as a
clean single-variable control.**

✅ **Provenance is independently witnessed, not asserted.** P1 carries memory +2000 where stock
carries +0, so the memory clock confirms the profile was live: **13801 MHz before, 15801 after
applying, 13801 after reverting.** The runner refused to sweep unless the post-apply reading
cleared stock, and reverted in a `finally`. ⚠️ Check the memory **maximum**, not the average — the
average is diluted by 810 MHz idle samples between iterations and looks alarming without meaning
anything.

**Original registration follows, unedited:**

P1 is easy to mis-remember as the memory-only profile. It is not: it carries the **same +478 MHz
floor offset as P4**, giving a floor extent of **1972 MHz**. It differs from P4 in **power limit
(100% / 180 W against 111% / 200 W)**, **memory (+2000 against +2500)** and **plateau (2962 against
3030)**.

> **Prediction: P1's median optimum is 2010 MHz — the same grid point as P4** — because 1972 and 2002
> are 30 MHz apart against a ~150 MHz grid, and the mechanism claims the optimum is set by the floor
> extent alone.

🔑 **This is a control on power limit, the one variable neither existing arm touches.** The
manipulation arm moved the floor and the optimum followed; the negative control moved the curve above
the floor and it did not move. P1 holds the floor region fixed and changes power and memory.

⚠️ **It is a two-variable contrast.** That weakens it as a test of *cause* — if the optimum moves, it
will not say which variable did it — but not as a test of the *prediction*, because the mechanism
claims the floor extent is sufficient. Any movement refutes it regardless.

**Refuted by:** a median optimum on any grid point other than 2010.

**Safety:** P1 is an existing, unmodified profile that is milder than P4 at every voltage above
850 mV (lower plateau, lower power limit). No new territory.

### Result

*(empty)*

---

## 3. RTX 2060 Super — PENDING, registered 2026-09-11

**Status: card available, nothing measured.** Turing, **TSMC 12 nm**, 34 SMs, 175 W TDP, 256-bit
GDDR6, 1650 MHz rated boost. A **third architecture and a third process node**, and the first
Turing part this project will sweep itself.

Procedure: `docs/FLOOR-VOLTAGE-PROTOCOL.md`. ⚠️ **Measure the floor FIRST, register the derived
prediction, and only then read the efficiency optimum** — the whole value of this run is that the
prediction is made between two measurements rather than after both.

### 3a. The floor voltage — DECLINED, deliberately

> **This project cannot predict the RTX 2060 Super's load-floor voltage, and does not try.**

Registering a refusal matters as much as registering a number. The floor voltage does **not**
transfer — 0.720 V on Blackwell, 0.756 V on Ampere — and borrowing either would be the exact error
`predict_from_curve.py` warns about. If this run later looks like a success, this paragraph is the
record that the constant was measured and not foreseen.

### 3b. A node hypothesis, registered ONLY so it can be refuted

> **Weak hypothesis, n = 2: floor voltage rises with process node size. 4N reads 0.720 V and
> Samsung 8 nm reads 0.756 V, so 12 nm Turing should read ABOVE 0.756 V.**

⛔ **Two points define a line trivially and this is barely a hypothesis.** It is written down because
a cheap prediction that can be killed is worth more than an expensive one that cannot, and because
if the 2060 Super reads *below* 0.756 the node story is dead on the third card instead of surviving
to a paper. **Refuted by any reading at or below 0.756 V.**

#### ⛔ Correction, same day: this was registered on a miscounted sample, and existing data already weakens it

**The wording above stands unedited, as the rules of this file require.** What follows is the record
that it was written badly.

**n was 3, not 2.** The RTX 3070 Ti's floor — **0.812 V**, holding to 1500 MHz — was already measured
in `data/frequency-sweeps/rtx3070ti-20260825/` and already stated in §5.5 of the paper when the
hypothesis above was written. It was not consulted. **A sample size was asserted rather than
counted**, which is the exact failure this project has a rule against.

🔑 **And the omitted card contradicts the hypothesis.** The RTX 3060 and the RTX 3070 Ti are **the
same architecture on the same process node**, and their floors differ by **56 mV** — larger than the
**36 mV** between the 8 nm parts and the 5 nm one. **Within-node spread exceeds between-node
difference, so node alone cannot determine the floor voltage.** The prediction "12 nm should read
above 0.756 V" may still come true, but it would no longer be evidence for the reason it was
offered.

**Revised, and deliberately weaker:** among the two Ampere parts the floor rises with die size and
power class — 28 SMs / 170 W at 0.756, 48 SMs / 290 W at 0.812 — with architecture plausibly setting
an offset on top. ⚠️ **That is monotone across two points and is a direction to test, not a
prediction.** The 2060 Super at 34 SMs / 175 W on an older node is a reasonable probe of it, and
**no point estimate is registered for it.**

⚠️ **The original 3b remains the thing to score.** If the card reads at or below 0.756 V, 3b is
refuted outright. If above, 3b survives on a test it was too weak to deserve.

### 3c. The mechanism — the real test

> **Once the floor voltage and floor extent are measured, the median efficiency optimum across the
> workload set will be the grid point nearest the floor extent.**

Held on **5 of 5** configurations across two architectures. This is the first chance to break it on
a third. **Refuted by a median landing on any other grid point.**

⚠️ **Stated as a rule rather than a number because the grid is not known until the card reports its
supported clocks.** The derived number goes in the Result block below, written **before** the
efficiency column is read.

### 3d. 🔑 The wrong-range prediction — the sharpest thing this card can do

This is the one worth caring about. `data/external/gtx2070s-*.csv` is a **published** DVFS dataset
for the RTX 2070 Super: same architecture, same 12 nm node, same generation, a near-sibling part. It
sweeps **95–118% of rated boost** and reports a mean headroom gap of **3.34%**, with 20% of apps
optimal at its ceiling.

`CLAUDE.md` argues that figure is an artefact of sweeping the wrong range — that the optimum lives
*below* stock, where that dataset never goes. That argument has never been tested on the same
architecture.

> **Sweeping a 12 nm Turing card from 40% of its supported range will find a stock-to-optimum
> efficiency gap far larger than the 3.34% the published 2070 Super dataset reports — specifically,
> greater than 15 points.**

Basis for 15: the V100 gave 44.4 points and the 5060 Ti's own headroom runs 30–57 points. Fifteen is
deliberately conservative, well under every consumer measurement this project has made.

⛔ **What refutes it:** a gap at or below 15 points would mean Turing genuinely lacks the headroom
this project claims consumer silicon has, and the "published consumer datasets sweep the wrong
range" contribution would need rewriting rather than defending.

⚠️ **It is a sibling, not the same chip.** The 2060 Super has 34 SMs against the 2070 Super's 40 and
a lower boost clock, so this compares architecture-and-range, not part-for-part. A difference could
in principle be the part rather than the range — but the published sweep's floor sits *above* stock,
so it structurally cannot locate an optimum below stock regardless of which part it ran on. That
asymmetry is what makes the comparison worth making anyway.

### Safety

Stock only. No profile, no curve, no overclock, no power-limit change. The card is **underclocked
throughout** — the protocol probes the lower half of the range. Clock locks reset through
`try/finally` and do not survive a reboot.

### Result — floor reading, 2026-09-12

**Written before any efficiency optimum was computed, which is the point of the entry.** Collected
on an MSI Ventus 2X RTX 2060 Super, driver **616.92** — the same driver as the RTX 3060 run. Power
limit **175 W default / 185 W maximum**; the default matches the reference 175 W TDP exactly, so
there is no raised board power and the card is **consistent with reference trim, not confirmed**.
Die **TU106-410**, 34 of the 2070's 36 SMs.

Joined from the `asfound` `gemm` sweep, with the HWiNFO log **truncated to the sweep window
(11:47:25–12:01:25)** because the log ran on through the suite calibration afterwards and that
free-boost load would otherwise have polluted the clock bins.

| target MHz | 855 | 960 | 1065 | 1170 | 1275 | 1380 | 1485 | 1590 |
|---|---|---|---|---|---|---|---|---|
| core V | 0.637 | **0.631** | 0.644 | 0.669 | 0.694 | 0.725 | 0.769 | 0.819 |

⛔ **NO FLOOR WAS OBSERVED INSIDE THE SWEPT RANGE.** The protocol anticipates this case and requires
it be recorded rather than papered over. Voltage rises essentially from the first grid point: the two
lowest readings are 0.637 V at 855 MHz and 0.631 V at 960 MHz, **6 mV apart, which is one step of
this sensor's resolution**, and from 1065 MHz upward it climbs monotonically with no flat region
anywhere.

**This is the first of four cards not to show a floor**, against 0.720 V holding to 1552 MHz on the
5060 Ti, 0.756 V to 1260 MHz on the 3060, and 0.812 V to 1500 MHz on the 3070 Ti. Its lowest reading
is also far below all three.

### The prediction this licenses, registered now

The mechanism says the optimum is the highest frequency the curve reaches at the load floor. If this
card's floor sits **at or below ~0.631 V and therefore at or below 960 MHz** — the reading the data
supports — then:

> **The median suite optimum should land at the BOTTOM of the grid, 855 or 960 MHz.**

⛔ **What refutes it:** a median optimum materially above 960 MHz. That would mean either the rule
fails on Turing, or the floor lies below the swept range and the rule cannot be applied without
sweeping lower — and those two are **not distinguishable from this data**, which is a limit of this
run rather than a hedge.

⚠️ **The swept range starts at 855 MHz** (`-MinFrequencyPercent 40` of a ~2115 MHz ceiling). A floor
below that is invisible here. **A confirmation would therefore be weaker evidence than the 3060's**,
where the floor was visible as five flat points *inside* the range with the optimum at their top
edge. Landing on the bottom grid point is consistent with the mechanism; it is also what a card
would do if its efficiency simply kept improving all the way down.

### ⚠️ And one methodological finding from this run

The `asfound` run's `gemm` and `membw` joins return **byte-identical voltages and byte-identical
sample counts** for every point where their achieved clocks match. They are not two measurements —
`join_hwinfo_voltage.py` bins by core clock with no time filter, one log covered both sweeps, and
both visit the same targets, so the two joins read **the same pooled samples**.

🔑 **This retracts a claim written into §5.5.7 of the paper the previous day**, where the same
artifact on the 3060's `gemm` and `copy` joins was presented as confirming the floor is
workload-independent. The floor *values* are unaffected — voltage at a locked clock is a property of
the applied curve and pooling samples taken there reads it correctly. What is gone is any use of two
joins from one log as independent confirmation. **Demonstrating workload-independence needs a
separate HWiNFO log per workload, which no run in this study has.**

---

---

## Outcomes — RTX 2060 Super, scored 2026-09-12

**Two refuted, one held, one correctly declined.** Full record in
`data/frequency-sweeps/rtx2060s-20260912/README.md`. Nothing above this line has been edited.

### 3a — floor voltage declined ✅ correctly

The measured floor is **0.631 V**, **89 mV below the next lowest of four cards**. Nothing in this
project would have predicted that, and the entry declining to try is the record that it was measured
rather than foreseen.

### 3b — "12 nm should read above 0.756 V" ⛔ REFUTED

**0.631 V. Not above 0.756 — the lowest of all four cards, by a wide margin.** The oldest and
largest process node returned the *lowest* floor voltage, which is the opposite of the direction
registered.

🔑 **The node hypothesis is dead, and it was already weak.** The correction appended to 3b on the day
it was written noted that two Ampere parts sharing an architecture *and* a node differ by 56 mV. A
Turing part now reads 89 mV below either. **Process node does not determine the load-floor voltage,
in any direction, and the four measurements are 0.631 / 0.720 / 0.756 / 0.812 V against nodes of
12 / 5 / 8 / 8 nm.**

### 3c — "median optimum lands on the grid point nearest the floor extent" ⛔ REFUTED AS REGISTERED

Registered: **855 or 960 MHz.** Measured: **1065 MHz**, 5 of 12 workloads on the median.

⚠️ **It was refuted for a reason worth keeping: the prediction was made from a sweep that never
reached the floor.** The `asfound` grid starts at 855 MHz, the floor's top edge is near 975, and the
voltage column read as "still falling" when it was in fact already flat. I recorded "no floor
observed" and derived "floor at or below 960" from it. A low-range sweep from 405 MHz found the
floor immediately.

🔑 **And with the floor located, the rule is neither confirmed nor refuted — it is UNDECIDABLE here**,
which is a third outcome this project had not met:

| floor extent as read | nearest grid point | vs measured 1065 |
|---|---|---|
| 975 MHz — strict, last point at the 0.631 V minimum | 960 | ✗ one step out |
| 1035 MHz — allowing one 6 mV sensor step | 1065 | ✅ exact |

**The verdict turns on a single step of sensor resolution.** The card holds 0.631 V across
**570+ MHz** and leaves it 6 mV at a time; the RTX 3060 by contrast jumps 0.756 → 0.787 V, a 31 mV
step with no ambiguity. **The rule needs a crisp exit from the floor and this card does not supply
one.** That is a boundary condition on the mechanism, not a failure of it — and it is not a
retrofitted excuse, because the ambiguity is visible in the voltage column itself rather than
inferred from the answer.

⛔ **The registration stands refuted regardless.** A prediction that needed a second sweep to become
arguable was wrong when it was made.

### 3d — "gap greater than 15 points" ✅ HELD, and it is the day's strongest result

**41.57% mean efficiency gain**, median 37.22%, every one of twelve workloads above 19%, `copy` at
83.81%.

Against the published **RTX 2070 Super** dataset — same architecture, same 12 nm node, near-sibling
die — which sweeps 95–118% of boost and reports **3.34%**. **A factor of 12.4.**

🔑 **This is the wrong-range argument tested on the architecture it criticises.** Until today it
compared different architectures and asserted the swept range was the difference. A Turing card
swept from 40% now returns a Turing number twelve times the published Turing number, and the
threshold was registered before the card was measured.

---

## Prior registrations, recorded elsewhere

Kept here as pointers so the practice is visible in one place. These were registered in their own
data READMEs before this file existed.

| experiment | registered prediction | outcome |
|---|---|---|
| `abba-20260908` | ⛔ **NOT the optimum — see the correction below** | the optimum result was **unplanned**; the registered prediction **failed** |
| `repair-suite-p2-20260909` | changing the curve *above* the floor moves the optimum **not at all** | ✅ **median** unmoved despite a 570 MHz change; **3–6 of 12 individual workloads move** |

⛔ **THE FIRST ROW WAS FALSE AND IS CORRECTED 2026-09-19.** It read *"the optimum moves with the
floor region of the curve — ✅ +465 MHz in 12 of 12 workloads"*, in the one file whose entire job is
to record what was registered **in advance**.

**What `abba-20260908` actually registered** is in its own sweep JSONs: a **dose-response**
prediction, that Profile 4 — the deeper undervolt — would leave **less than P5's 27.5%** remaining
headroom. **It failed**, and in the opposite direction: 34.32% against 28.27%.

**The load-floor result was found afterwards, in that run's data.** The run's own README says *"It
was not planned"* and commit `0ca60ea` says *"RESULT 1, and it was not planned."* 🔑 **Both were
written honestly at the time; the error was committed later, when this ledger summarised them.**

✅ **Two things keep it from being a bare post-hoc fit.** The 0.720 V floor used to predict +465 was
measured on **other data** rather than fitted to this outcome, and the follow-ups — P2, the RTX 3060,
the RTX 2060 Super — **were** registered before collection. ⚠️ The 2060 Super's was **refuted as
registered**, and a later finer measurement cannot convert that into a success.

🛑 **Found by an outside adversarial audit, verified here by recomputation**, not by internal
review — which had read this table repeatedly. Full record:
`docs/gpt-findings/2026-09-19-load-floor-causal-claim-adversarial-audit.md`.
| `rtx3060-20260910` | the rule holds on a different architecture | ✅ holds — ⛔ but the floor **voltage** does not transfer (0.756 V, not 0.720) |

---

# 4. 🔑 THE CROSS-CHIP CAUSAL REPLICATION — registered 2026-09-13, BEFORE any card is touched

**Registered because two cards became available at once and both leave soon.** An RTX 3070 Ti
(Ampere GA104) and an RTX 2060 Super (Turing TU106), both owned outright — see the ownership
correction below. This is the experiment the 2026-09-13 council session named as the single thing
blocking the paper, and it had been recorded as impossible.

⛔ **THE BLOCKER WAS A MISCLASSIFICATION, NOT A RULE.** `rtx3060-20260910/README.md` states these
were machines Raymond "does not own", and `rtx3070ti-20260825/README.md` calls its card "a
customer's machine". **Both descriptions are wrong.** These are builds assembled to sell; nobody
else owns them while they are on the bench and no third party's data is on them. The safety
invariant — *never automate tuning on machines Raymond does not own* — was never engaged. 🔑 **This
is the second time this project has treated a recorded blocker as real without rechecking it**, and
CLAUDE.md's own warning about that is in the coverage section.

## What is already known, and therefore what is being predicted rather than explored

Both cards' stock floors are already measured, which is what makes these predictions registrable:

| card | floor voltage | stock floor holds to | measured median optimum | rule verdict so far |
|---|---|---|---|---|
| RTX 3070 Ti (GA104) | **0.812–0.819 V** | **1500 MHz** | **1485 MHz** | ✅ observational, holds |
| RTX 2060 Super (TU106) | **0.631 V** | **975 or 1035 MHz** | **1065 MHz** | ⚠️ undecidable |

**Every prior confirmation of the rule on these two cards is OBSERVATIONAL.** Only the 5060 Ti has
a causal arm. That is the n=1 that the council said a reviewer would name in thirty seconds.

## 4a. 3070 Ti — the replication. **The single highest-value prediction in this document.** — COLLECTED 2026-09-24: ✅ PASS (4b ⛔ FAIL; see the result under 4b)

> **Extend the stock floor upward by reshaping only the curve at and below 0.819 V, and the median
> suite optimum will move with the new floor end, in the same direction and by a comparable
> fraction of the shift.**

Success is the optimum tracking the new floor end to within one grid step. ⛔ **A movement in the
wrong direction, or no movement, refutes the causal claim on a second chip and must be reported as
the headline** — the 5060 Ti result would then be a single-chip curiosity rather than a mechanism.

## 4b. 3070 Ti — the negative control, run in the same session or not at all — COLLECTED 2026-09-24: ⛔ FAIL, the control also moved

> **Change the curve only ABOVE the floor voltage, by at least 300 MHz, and the optimum will not
> move.**

⚠️ **The manipulation without its control is worth much less than half the experiment.** A council
reviewer specifically defended this design: sharing chip, session and operator is what a negative
control is *for*. If the session is cut short, run 4b, not a second replicate of 4a.

### ⛔ AMENDMENT, recorded 2026-09-22: the design changed BEFORE collection, and this file never said so

**Found by GPT while writing the Session D scorer (`docs/gpt-findings/2026-09-22-session-d-scorer.md`),
verified here against git.** 4a and 4b above are unedited, as the rules require. **They do not
describe the experiment that will run.**

| | registered above, 2026-09-11 | what will run: `SESSION-D-RUNSHEET.md` |
|---|---|---|
| 4a direction | **extend** the floor **upward** | **shorten** it **downward**: cap ≤0.825 V at 1200 MHz |
| 4a boundary | ≤0.819 V | ≤0.819 V at first (`9ab8ba6`, 09-13), **0.825 V** from `8d2a22e` (09-20) |
| 4a prediction | "moves with the new floor end… comparable fraction" | **median 1485 → 1170 or 1275 MHz**, first stated 09-13 |
| 4b dose | **at least 300 MHz** | **263 MHz**: all the range the card has above its floor |

**Why it changed:** the runsheet gives the reason in its first version (`9ab8ba6`, 2026-09-13). The
card is **power-capped at ~1763 MHz**, so an upward edit has at most +263 MHz of dose, and any result
would be entangled with the power cap. Shortening has −300 MHz available with nothing in the way,
and it is the safe direction.

✅ **What is still a genuine advance prediction:** the runsheet's numbers are committed in git on
2026-09-13 and 2026-09-20. **No Session D data exists as of this amendment.** The mechanism predicts
movement *with* the floor end in either direction, so reversing the direction tests the same
claim.

⛔ **What must be said when this is reported:**
1. §4a as worded above did **not** predict the shortening direction or the 1170/1275 numbers.
   **Cite the runsheet's commits for those, not this file.**
2. The control's dose is **263 MHz, below the 300 MHz registered.** Report the shortfall. Do not
   round it away.

🔑 **How it got in: the same way as the 2026-09-19 registration error.** The run record was right and
the ledger that summarises it drifted. This time the runsheet even said *"predictions are already
registered in §4, do not change them"* while describing the opposite edit. **Whenever a runsheet
changes a design, amend this file in the same commit.**

### ⛔ AMENDMENT 2, recorded 2026-09-23: the curves as BUILT, before collection

**No Session D data exists as of this amendment.** The three curves were built at the machine on
2026-09-23 and decoded from the saved store: `data/afterburner-profiles/3070ti-profiles-20260923/`
(the curve file's SHA-256 begins `1b08c2d0854460ff`). They differ from the runsheet in three places,
all forced or found by the build:

| | runsheet | **as built** |
|---|---|---|
| Edit 1, ≤0.825 V | capped at 1200 | ✅ **1200 from 725 to 825 mV**, the whole floor band (0.812–0.825 V) |
| Edit 1, 0.831–0.869 V | "unchanged", at stock | ⛔ **a forced ramp below stock**: 1215, 1275, 1335, 1395, 1455, 1515, 1575 (stock 1530 → 1620), rejoining stock at 875 mV |
| Edit 1, 718.75 mV | stock 1185 | ⚠️ **1200, 15 MHz above stock**, a light-load point below the floor |
| Edit 2, 0.825 V | stock 1515 | **1500**, 15 MHz under stock |
| Edit 2, ≥0.831 V | flat 1500 | ✅ flat 1500 |

**Why the ramp:** the driver, or Afterburner, would not accept a single step from 1200 at 825 mV to
stock at 831. Inferred from the file, not documented: **no point may sit more than ~60 MHz below its
right-hand neighbour.** The first build put the ramp below 825 mV, inside the floor band, and was
rebuilt so the band stays flat.

**The predictions do not change, and here is why each still applies:**
- **Edit 1's floor end is 1200 MHz**, at every code in the floor band. The runsheet's prediction,
  **median 1485 → 1170 or 1275**, was made for exactly that floor end.
- **Edit 2's floor end moves from ~1515 to 1500** at 825 mV, inside the restated prediction's
  **~1485–1500 MHz achieved** band. Its dose is unchanged: the card's ~1763 MHz ceiling is cut to 1500.

⚠️ **What must be said when this is reported:** Edit 1 is **not a floor-only edit.** It also lowers
0.831–0.869 V, which is part of the region Edit 2 edits. The contrast that survives is the one the
design needs: **Edit 1 changes the clock at the floor voltage (1485–1515 → 1200) and Edit 2 does
not** (at most −15 MHz). The 718.75 mV point is outside the safe-by-construction envelope by 15 MHz,
the same kind of exception as rung B's 650–690 mV points, and is recorded rather than rebuilt.

### Provenance note, 2026-09-24, still before any Session D data

Session D's first launch stopped at its store-hash gate. Afterburner had added `[Defaults]` and
`[Settings]` sections to the 3070 Ti's profile store. **`Profile1`–`Profile3` are identical, key for
key, to the store decoded in Amendment 2**, so the curves above are the curves that will run. The
gate now expects the new whole-file hash `cce75e81fe322380`.
`data/afterburner-profiles/3070ti-profiles-20260924-afterburner-rewrite/README.md`. **Nothing in the
design or the predictions changes.** ⛔ *Superseded the same day, still before data: the gate hashes
only the `[Profile1]`–`[Profile3]` sections, `A1159941DA541EB9`, which is what Session D ran against.*

### Result, collected 2026-09-24 — 4a ✅ PASS, 4b ⛔ FAIL: the control also moved, so the attribution fails on this chip

**Scored by `python analysis/score_session_d.py data/frequency-sweeps/rtx3070ti-sessiond-20260924`**,
the scorer committed before collection. Its output, unedited:

| | value |
|---|---|
| eligibility | **VALID**: stock baseline 1485 MHz as registered; stock-1 → stock-4 worst workload change **0.619%** (limit 1.5%); floor verified on all four suites |
| stock-1 median optimum | **1485 MHz** |
| **4a**, Edit 1 (`edit1-2`) | **1222.5 MHz**, inside the registered 1170–1275 → ✅ **PASS** |
| **4b**, Edit 2 (`edit2-3`) | **1432.5 MHz**, outside the registered 1485–1500 → ⛔ **FAIL** |
| stock-4 median optimum | **1485 MHz** |
| joint verdict | ⛔ **CONTROL_ALSO_MOVES_ATTRIBUTION_FAILS** |

🛑 **Report it as registered: the manipulation moved the optimum as predicted, but the negative
control moved it too, so this chip does not attribute the move to the floor region.** 4b said the
control "is what makes the manipulation worth more than half the experiment", and it did not hold.

**Descriptive context.** None of it changes the verdict, and it is recorded so the verdict is read
correctly.
- **The control's 1432.5 is a six-six split.** The twelve optima fall 1065, 1170, 1275, 1275,
  1380, 1380 | 1485, 1485, 1485, 1500, 1500, 1500, so the median sits between two grid points. All
  three stock suites have seven or more workloads at 1485 or above.
- **Per-workload optima are noisy between identical stock suites.** stock-1 and stock-4 disagree on
  **4 of 12** argmaxes (`copy`, `layernorm`, `bgemm128`, `gemm`), and stock-4 and stock-6 on **3 of
  12**. Against stock-1, the control moved 3 workloads down (`bgemm128`, `conv`, `gemm`) and 2 up
  (`copy`, `reduce`). That is the same order as stock-against-stock, but the registered test is
  the median, and stock's median did not move in any of three stock suites.
- **Edit 2 is not purely above the floor**, per Amendment 2's as-built description: *"stock
  through 818.75 mV, flat 1500 MHz from 825 mV up (825 mV is 15 under stock)"*. The 825 mV point
  is inside the registered floor band (≤0.825 V) and was lowered by 15 MHz. That was known before
  collection and does not excuse the result.
- This is the second partly moving control. The 5060 Ti's moved 4 of 12 workloads but not the
  median (CLAUDE.md, the negative-control entry). **Here the median moved as well.**

⚠️ **n = 1 chip, one session.** Driver 617.14, SILENT BIOS 290/290/320 W. The replicate of the
manipulation is §8a below; the control is not replicated.

## 4c. 2060 Super — the boundary condition, made decidable or shown not to be

> **Reshaping the floor region on a card whose voltage leaves the floor 6 mV at a time will produce
> a floor end that is EITHER sharp enough to locate — in which case the optimum should track it as
> in 4a — OR still undecidable, in which case the ambiguity is a property of the silicon and not of
> the vendor's shipped curve.**

🔑 **Both outcomes are publishable and they say different things**, which is why this is registered
as a disjunction rather than a directional bet. This is the only prediction here whose interesting
result is the negative one. ⚠️ Run the fine floor sweep (~10 min) FIRST — the manipulation cannot be
designed without knowing where the stock floor actually ends on this card.

## 4d. 2060 Super — is the load floor a property of the CURVE, or of a COLD CARD?

**Registered 2026-09-15, after the fine floor sweep and before the descending run.** Nothing about
the card has been touched since; this prediction is written from a result already in hand about a
measurement not yet made.

🔑 **WHY THIS EXISTS.** The fine sweep found the voltage **non-monotonic** — falling 0.644 → 0.631 V
from 900 to 1005 MHz, then rising to 0.662 by 1140. But the sweep runs low frequency to high, and
the card warms 42.0 → 58.7 °C while it does, **so on the falling limb frequency and warm-up are
perfectly collinear.** On the rising limb they are not: temperature has saturated within 3.2 °C
while voltage climbs 31 mV, so that half is attributable to frequency. The falling half is not.

> **Sweeping the identical 900–1140 MHz grid in DESCENDING order, on a card allowed to reach
> thermal steady state the same way, the voltage minimum will remain at 975–1005 MHz.**

| outcome | reading |
|---|---|
| minimum stays at **975–1005** | ✅ The shape belongs to the V/F curve. The non-monotonic Turing floor is real and Result 1 stands whole. |
| minimum **follows the cold end** — now the top of the grid | ⛔ It is thermal. **Every load floor this project has measured came from a low-to-high sweep**, so the 5060 Ti, 3060 and 3070 Ti floors all inherit the same confound and the floor-extent numbers need re-reading. This is the larger finding by a distance. |
| minimum flattens or moves partway | 🟡 Both contribute. Report the split and quote no single floor extent without the sweep direction beside it. |

### 🔑 Evidence gathered BEFORE the run, which moves the prior toward "not thermal"

**Recorded here rather than after, because a prior revised once the answer is known is worth
nothing.** 16 of the 22 sweeps that have ever produced a voltage extract warm by 8 °C or more, and
the 5060 Ti stock sweep that sets the project's 0.720 V floor warms **24.6 °C** — so the exposure
is real and project-wide. But the floors those sweeps report are **flat through the warm-up**:

| card | floor region | voltage across it | temperature across it |
|---|---|---|---|
| RTX 3060 | 840 → 1260 MHz, 5 points | **0.756 V, zero movement** | 38.6 → 48.8 °C (**10.2 °C**) |
| RTX 5060 Ti | 1237 → 1545 MHz, 3 points | **0.720 V, zero movement** | 41.2 → 46.3 °C (5.1 °C) |

⛔ **A 10.2 °C warm-up on the 3060 moved the reading by less than one 6 mV sensor code.** If
temperature were driving voltage at the scale seen on the 2060 Super — **13 mV across 13.5 °C**,
more than double that bound — the 3060's floor could not have come back flat across five
consecutive points.

✅ **So the flat floors are most likely genuinely flat, and the corpus is probably not in danger.**
What remains unexplained is the 2060 Super specifically. ⚠️ **This does not settle it**: the bound
comes from a *different card*, and thermal compensation is a per-controller behaviour that need not
transfer — the same trap as borrowing a floor voltage between cards. The prediction below stands
unchanged.

⚠️ **The honest prior is that this is NOT settled.** Temperature-compensated voltage is ordinary
controller behaviour, and nothing in this project has ever varied sweep direction to look for it.
✅ **Cost: one ~12 minute sweep, stock, no elevation beyond the usual clock lock, nothing applied
and nothing to clean up.** It is the cheapest experiment on the list and it can invalidate a
number that appears in the paper's headline mechanism.

🛑 **Keep the raw HWiNFO log again**, and record the per-point temperatures — they are the
independent variable this time, not a footnote.

### ⛔ Amendment, 2026-09-25, before collection: how Session E scores 4c and 4d

**Written before any Session E data exists.** The card has not been touched since 2026-09-15. The
scorer is `analysis/score_session_e.py`, committed with this amendment. Nothing above is edited:
this section fixes what the words above leave open, and records one inconsistency in them.

**4c, the manipulation (`stock-1` → `edit-2` → `stock-3`).** The prediction under Part 2 of the
run sheet is: *"the median suite optimum moves from **1065 MHz** down toward **855 MHz** (the nearest
suite grid point above the new floor end)"*, and *"if it does not move, the rule's attribution to
the floor region fails on Turing"*.
- **Scoreable** only if all of the following hold. Otherwise the result is NOT SCOREABLE, which is
  not a failure.
  - All 36 suites share one driver, the power limits read 175 / 175 / 185 W, and every sweep has
    the 13-point grid 855–2115 MHz.
  - `stock-3`'s median equals `stock-1`'s, the run sheet's rule: *"if the closing stock run does not
    match the opening one, the result is not interpretable"*.
  - No workload's median absolute matched-target throughput change from `stock-1` to `stock-3`
    exceeds **1.5%**, the Session D and §10 limit.
  - **The edit is verified in the data**: every workload of `edit-2` reads **≥ 0.668 V at every
    target**, because the edit makes every clock above 810 MHz need the 0.669 V point.
  - **Stock is verified**: every workload of both stock suites reads **0.630–0.657 V at 1065 MHz**,
    the plan's witness range.
- **PASS**: `edit-2`'s median lies in **855–960 MHz** and below `stock-1`'s. That is the predicted
  grid point or one step above it, the same two-bin width 4a allowed.
- **FAIL_NO_MOVEMENT**: the median is at or above `stock-1`'s. This is the headline failure named above.
- **FAIL_PARTIAL**: the median moved down, but not into 855–960.
- `stock-1`'s median is scored against the same session, and **reported against the registered
  1065**; a different stock median is stated beside the verdict, not hidden by it.
- ⚠️ **Session E cannot decide 4c's "still undecidable" branch.** The suite grid starts at 855 MHz,
  above the edited floor end of 810, so no Session E sweep samples the edited floor end itself. The
  edit's sharpness is by construction (the 38 mV step from ≤ 0.650 to 0.669 V) and by the witness,
  not measured. Locating it would need a fine sweep under P2 around 810 MHz, which the plan does
  not contain. Report this, and do not read a PASS as having shown the floor end is sharp.

**4d, the descending sweep (`e1-desc`), against `rtx2060s-finefloor-20260915`.**
- **The minimum set** is every target whose voltage lies within **0.003 V** of the sweep's lowest
  reading. That is under half of one 6.25 mV code, so a median that falls between two codes still
  ties with the lower code. The ascending reference gives {975, 1005}.
- **Scoreable** only if all of the following hold:
  - the sweep JSON records `sweep_order: descending`;
  - its targets equal the ascending sweep's 13 (900 … 1140);
  - every target has a voltage reading;
  - it reads **0.630–0.657 V at 1065 MHz**, which confirms it ran on stock.
- **HOLDS**: every target in the minimum set lies within **975–1005 MHz**.
- **FLAT**: the minimum set contains both 900 and 1140.
- **MINIMUM_REACHES_BOTTOM**: it contains 900 (and not 1140). The falling limb has gone.
- **MINIMUM_AT_TOP**: it contains 1140 (and not 900).
- **PARTIAL**: anything else. The minimum widened or moved without reaching either end.
- ⛔ **The registered thermal outcome names the wrong end, recorded here before the data can
  choose.** The table above says a thermal minimum *"follows the cold end — now the top of the
  grid"*. But the mechanism it registers is that the falling limb (0.644 → 0.631 V from 900 to
  975 MHz) is **warm-up lowering the voltage**. A descending sweep measures 900 MHz last, on a warm
  card, so under that mechanism the limb disappears and **the minimum extends to the BOTTOM of the
  grid** (MINIMUM_REACHES_BOTTOM). A minimum at the top would need a cold card to read *lower*,
  the opposite mechanism. **Both are scored and both are reported by name.** The thermal reading
  in the table (⛔, "every floor extent needs re-reading") attaches to MINIMUM_REACHES_BOTTOM,
  and MINIMUM_AT_TOP is reported as what the registered words literally said. The error entered
  when the outcome was phrased as "follows the cold end" without working through which end a
  descending sweep measures warm.
- **Reported beside the verdict, never scored:**
  - per-point temperature in both sweeps;
  - the driver in both sweeps, since the reference ran on 616.92.

## 5. RTX 5060 Ti: do isolated throughput losses come from ACTIVITY? Registered 2026-09-22 — COLLECTED 2026-09-23, ⛔ INCOMPLETE; RE-COLLECTED 2026-09-24, ✅ NOT SUPPORTED FOR THIS PROXY

**Why.** On 2026-09-22, three stock `4i` replicates lost 8–11% at isolated points: **4, then 2, then
0** degraded points, while the driving agent went from busy to silent. An outside audit
(`docs/gpt-findings/2026-09-22-5060ti-session-results-audit.md`) found that **agent activity, run
order and time since a cold start all changed together**. The data cannot say which mattered, and
"replicate and take the maximum" rests on the answer.

**Design, fixed before collection.** Runner `tools/hwinfo-logging/experiments/Run-ActivityAB.ps1`,
scorer `analysis/score_activity_ab.py`, both committed with this entry.

- Stock Profile 3, verified by memory clock under load. `gemm`, 1380–1760 MHz, 13 points,
  ascending: the grid the losses were found on.
- **Warm-up removed:** the run waits for **30 minutes of uptime**, then does **two throwaway
  warm-up sweeps, excluded from scoring**.
- **Order balanced:** **S A A S × 3**, giving 6 silent and 6 active runs, so a linear time trend
  cancels.
- **Only activity differs.** Active runs start `Start-ActivityLoad.ps1` once the GPU is under
  load. It is a logged proxy for the agent's work: `nvidia-smi pmon` every 5 s, plus a 2 s CPU
  burst and a full-screen capture every 15 s. Both conditions do identical load-detection polling.

**Scoring, fixed now.**
- Envelope: the best throughput at each target across the 12 scored runs.
- Degraded point: **more than 2% below** the envelope.
- D_A and D_S are the degraded-point totals in active and silent runs.

| outcome | rule | meaning |
|---|---|---|
| **activity supported** | D_A ≥ D_S + 4 **and** ≥ 3 of 6 active runs hit | the proxy reproduces the losses on a warm card, with order balanced |
| **not supported for this proxy** | D_A ≤ D_S + 1 | the scripted activity adds nothing. ⚠️ It does **not** clear real agent activity, which also streams into an app window |
| inconclusive | anything between | report both totals, no verdict |
| other cause | D_S ≥ 3 | losses occur in silence on a warm card |
| none at all | D_A + D_S = 0 | cold start and real activity are still **not separated** |

**Prediction, made now:** **activity supported.** The 2026-09-22 losses fell as activity fell, and
did not track temperature.

⛔ **If a threshold proves wrong after the data exists, report the registered verdict AND the
revised one, never only the revised one.** One chip, one session, a scripted proxy.

**To run:** Raymond opens HWiNFO and its Sensors window, which needs UAC. Then, from an elevated
shell: `powershell -ExecutionPolicy Bypass -File tools\hwinfo-logging\experiments\Run-ActivityAB.ps1`
(~85 minutes plus the uptime wait). The driving agent stays silent until it exits.

### ⛔ Revised BEFORE collection, 2026-09-22 — five defects fixed; design and thresholds unchanged

An outside preflight review (`docs/gpt-findings/2026-09-22-activity-ab-preflight.md`) found five
defects. Each was reproduced here before fixing. **Two of them could have produced a wrong
registered verdict:**

1. **An exact 2% tie counted as degraded.** `100 × (1 − 98/100)` is 2.0000000000000018 in floating
   point. Four ties could print "SUPPORTED". "More than 2%" is now tested without subtraction.
2. **An active run was scored without proof that the activity ran.** A dead generator would have
   turned "active" into silent, and could have produced a false null. The generator now logs its
   start, every action's success, and its reason for stopping. The scorer requires that log to cover
   the sweep with no gap over 15 s, or the run is invalid.
3. **The stock gate was one-sided.** It accepted any lower memory clock. It now requires 13801 ± 200
   MHz and a 180 W power limit.
4. **An incomplete collection still printed a registered verdict.** It now prints **INCOMPLETE — NO
   REGISTERED VERDICT** unless two warm-ups and twelve valid runs exist in S A A S × 3 order.
5. **The grid was not validated** and blocks used the post-exclusion index. Every run must now carry
   the registered 13 points, and blocks follow the recorded order.

The generator is also stopped in a `finally` block, its time limit went from 15 to 20 minutes, the
exact sweep CSV path is recorded per run, and the uptime and block counts are constants rather than
parameters. **12 synthetic checks** in `analysis/test_score_activity_ab.py`; the tie check was
confirmed to fail on the old comparison. **No threshold, condition or prediction changed.**

### ⛔ Result, collected 2026-09-23 — INCOMPLETE, NO REGISTERED VERDICT

`data/frequency-sweeps/5060ti-activity-ab-20260923/`. Nothing above was edited. All 14 sweeps ran
(two warm-ups, then S A A S × 3), uptime gate met, stock verified, every wrapper exit 0.

**The registered scorer withholds its verdict:** in **3 of 6 ACTIVE runs (03, 06, 11)** the generator
started **0.1–0.2 s after** the first measured window opened, so activity is not proven across that
window. Every other validity check passed. The cause is the runner's load trigger: it waited for GPU
utilisation ≥ 50%, which in those three runs was the sweep's own first point. **The rule is not
relaxed after the fact.** A re-run should start the generator before the sweep.

**Descriptive only, and labelled as such:** there were **zero degraded points in all twelve scored
runs, active and silent, and none in either warm-up**. The worst point anywhere is **0.14%** below the
envelope, against 8–11% on 2026-09-22. That is the same whether the three late runs are excluded or
included. Had the collection been complete, the rules above would have printed *NOT SUPPORTED FOR THIS
PROXY* and *no losses at all*. **That is a counterfactual, not a result.**

It points away from this proxy and toward the cold start, or toward some part of real agent activity
the script does not imitate. It does not separate those two. ⚠️ One chip, one session.

### ⛔ Revised BEFORE re-collection, 2026-09-24: one change, the generator trigger

**No re-collection data exists as of this amendment.** Nothing above, the 2026-09-23 result
included, is edited.

**The only change:** an ACTIVE run's generator now starts when the sweep wrapper's HWiNFO log file
appears, instead of when GPU utilisation first reaches 50%. The wrapper creates that file only
after its preflight passes and before the sweep begins. HWiNFO's own growth check then takes several
seconds, so the generator is running before the first measured window. SILENT runs wait for the
same file and start nothing, so the waiting is identical in both conditions.

**Unchanged:**
- the design (two warm-ups, then S A A S × 3);
- the grid, the uptime gate and the stock checks;
- the generator itself;
- the scorer, `analysis/score_activity_ab.py`, and every threshold in it.

The scorer's rule that an active run is invalid if its generator started after the first measured
window still applies, and now should never trip.

⚠️ **This re-run is not blind.** The 2026-09-23 collection is known to show zero degraded points in
every run, active and silent. That is a descriptive result without a registered verdict, and it
could shape how this one is read. So this re-run is reported **with its own registered verdict,
beside** the 09-23 INCOMPLETE, never merged with it. It runs on 2026-09-24 with the operator absent
and the driving agent idle. HWiNFO was started by `tools/hwinfo-logging/Start-HwinfoSensors.ps1`,
not by hand.

### ✅ Result of the re-collection, 2026-09-24: registered verdict NOT SUPPORTED FOR THIS PROXY

`data/frequency-sweeps/5060ti-activity-ab-20260924/`. Nothing above was edited. All 14 wrapper runs
exited 0, stock was verified, and uptime was 146–206 min.

- **Every active run is valid.** Each generator started 22.0–22.4 s before its first measured
  window. The trigger fix worked.
- **Zero degraded points in all 12 scored runs, active and silent.** The scorer printed:
  *NOT SUPPORTED FOR THIS PROXY — the scripted activity does not add losses*, and *no losses at all*.

It matches the 2026-09-23 counterfactual, and is now a registered verdict rather than a description.
⚠️ **It still does not separate a cold card from real agent activity** as the cause of 2026-09-22's
losses: the proxy is not real activity. One chip, one session.

---

## 6. RTX 5060 Ti: does the load floor survive an NVML clock offset? (worklist 4c) Registered 2026-09-22 — ✅ COLLECTED, HOLDS

**Why.** Guerreiro et al., TPDS 2019, report that voltage shows two regions (constant, then rising)
when the frequency is changed through NVML, but that *"the voltage stays constant across all
frequencies"* when it is changed through clock offsets. Their offset path was `nvidia-settings` on
Maxwell/Pascal/Kepler. **If it holds for `nvmlDeviceSetClockOffsets` on Blackwell, the planned
offset-validation pair (4d) compares two different machine states and validates nothing.**

**Design, fixed before collection.** Runner: `tools/hwinfo-logging/experiments/Run-OffsetPrecondition.ps1`.
Tool: `tools/nvml-offset/Set-NvmlClockOffset.ps1`, which accepts negative offsets only and verifies
each write by reading it back. Stock Profile 3, verified by memory clock. `gemm`, ascending,
**1000–1700 MHz, 15 points, 50 MHz apart.** Runs **A1** (no offset), **B** (**−300 MHz**
P0 graphics offset), **A2** (offset reset to 0, verified). One HWiNFO log per run, at 0.50 s.
The operator is present for the first write.

⛔ **The grid differs from the worklist's 1380–1760, deliberately.** A −300 MHz shift should move the
floor end from ~1570 to ~1270, below that band, so that band could not tell "two regions, shifted"
from "no floor". And 300 MHz is six steps of 50, so B at f pairs with A at f+300 on the same grid.

**Prediction: the offset shifts the V/F curve.** B shows **two regions**: 0.720 V held, then rising.
Its floor end sits within one grid step (50 MHz) of **~1270 MHz**, the A floor end of 1567–1575
minus 300. Equivalently, **B's voltage at target f equals A1's voltage at f+300 within one 5 mV
code**, wherever f+300 is on the grid.

**Refuted by:**
- **B's voltage constant across the whole band.** That would be Guerreiro's offset behaviour. Then 4d
  is cancelled and this gets written up as a Blackwell confirmation of their finding.
- B has two regions, but its floor end is not within 50 MHz of ~1270.

**Registered as OPEN, with no prediction:** whether a locked clock still achieves its target under
the offset, or the lock target itself shifts by 300. The achieved-clock column answers it. Either
way the voltage comparison above is made at achieved clock.

**Validity:** A2 must match A1, with voltage within one 5 mV code at every point and throughput
within ~1%. Otherwise the session drifted, or the reset did not take, and B is not interpretable.
The offset is reset in a `finally` block and read back, whatever happens.

### ✅ Result, collected 2026-09-22 — THE PREDICTION HOLDS

`data/frequency-sweeps/5060ti-nvml-offset-20260922/`. Nothing above was edited.

| registered | measured |
|---|---|
| B shows two regions | ✅ 0.720 V through **1245** achieved, rising from **1290** |
| floor end within 50 MHz of ~1270 | ✅ **1245–1290** |
| V_B(f) = V_A1(f+300) within one 5 mV code | ✅ **≤2 mV** at all 8 on-grid pairs, and **≤3 mV** at 8 pairs against the 09-22 morning stock run |
| *open:* does the lock hold under the offset? | **Yes.** Every point held; achieved clocks within 7.3 MHz of A1 |
| validity: A2 matches A1 | ✅ voltage identical at all 15 points, throughput within 0.78%, reset verified |

**Refutation did not occur:** B's voltage is not constant across the band. ⚠️ One run per condition,
one offset (−300), one workload, one chip. 4d is superseded; its criterion could not hold as worded
(see CLAUDE.md).

⛔ **Two wordings above narrowed the same evening by an outside audit** (`docs/gpt-findings/2026-09-22-5060ti-offset-4c-adversarial-audit.md`);
the verdict is unchanged. **"≤2 mV / ≤3 mV"** interpolated between 5 mV codes. The accurate form is
**identical VID codes at 9 of 9 six-step pairs**. And 4d's criterion is **not a valid prediction**
(retire it), but "superseded" overstates: its wider machine-state question is still open.

## 7. RTX 5060 Ti: does an NVML offset ladder relocate the suite optimum? (worklist 4o) Registered 2026-09-22 — COLLECTED 2026-09-23: registered verdict ⛔ INVALID; revised ✅ all hold

**Why.** 4c showed that a −300 MHz offset moves the 0.720 V floor end from 1567–1575 to 1245–1290,
on **one workload**. This asks whether the **twelve-workload median optimum** follows the floor
when the offset is changed, with no Afterburner slot and no hand-built curve. ⚠️ The curve-shift
mechanism is prior art (170tune, `RELATED-WORK.md` §10). This tests a **predictive rule on one
chip**, not the mechanism.

**Drafted by GPT (Job 10), reviewed and changed before registration.** Draft and review:
`docs/agents/DRAFT-offset-ladder-registration.md`. ⛔ **The draft's −450 rung is DROPPED.** Its
prediction, 1237, is the same grid point as −300's, so it could confirm nothing. **A closing stock
suite replaces it**, as a drift bracket. Chosen by Raymond, 2026-09-22.

**Design, fixed before collection.** Runner: `tools/hwinfo-logging/experiments/Run-OffsetLadder.ps1`.
- Apply stock Profile 3 **before** any offset. Verify memory at 13801 MHz under load and the power
  limit at 180 W enforced / 180 W default.
- **Four suites in this order: 0 / −150 / −300 / 0 MHz**, set with `Set-NvmlClockOffset.ps1`, each
  write verified by read-back. The offset is reset to 0 in `finally` and read back.
- Each suite runs the twelve standard workloads in a fixed order (`copy` … `gemm`). Each sweep is
  ascending, **13 points, 1237–3090 MHz**, with the iteration counts from
  `5060ti-stock-repro-20260922`. **48 sweeps, ~4 h** (one stock suite took 57 min on 09-22).
- HWiNFO logs at 0.50 s, one log per sweep, with the machine quiet and unattended.

**Statistic.** For each workload, take the target with the highest efficiency (timed throughput
over windowed mean power). The **ordinary median of the 12 target optima** is the statistic; a 6/6
split whose median falls between two grid points is **not** rounded. Per-workload optima are
reported but not scored, because two identical stock suites agreed on only 9 of 12.

**Predictions:** floor end 1567–1575 minus the offset, then the nearest grid target.

| suite | predicted floor end | **predicted median** | what a pass can show |
|---|---:|---:|---|
| opening 0 MHz | 1567–1575 | **1545** | baseline |
| −150 MHz | 1417–1425 | **1395** | 🔑 **the only interior test.** 1395 sits between 1237 and 1545, so a pass locates the move |
| −300 MHz | 1267–1275 | **1237** | ⚠️ **edge-limited.** 1237 is the lowest grid target, so a pass fits any optimum at or below ~1316 MHz. It shows a move of at least two steps, **not** a move to ~1270 |
| closing 0 MHz | 1567–1575 | **1545** | drift bracket, not a prediction |

**Refuted by**, per rung: any other median for opening 0, −150 or −300, including a between-grid
median from a 6/6 split. **Trend:** the medians must not increase from 0 to −150 to −300. An upward
step refutes the trend even if a rung passes.

**Validity, separate from refutation:**
- **Drift bracket.** The opening and closing stock medians must be **equal**. If they differ, the
  session drifted and **no rung is scored**. That is reported as uninterpretable, never as a pass or a
  null. Two identical stock suites on 09-22 both gave 1545.
- Every sweep must be complete, with no failed benchmark or missed lock. Each must carry the
  registered grid and iteration count, stock memory and power, one driver across all 48, and **its
  own** time-joined voltage extract.
- The runner's console log must show every offset read-back and the final reset. The CSVs cannot
  prove them.

**Limits, stated now.** One chip, one suite per rung, one session. Twelve workloads are repeated
outcomes on one card, not twelve chips. The reported voltage is a VID lookup, not rail voltage. A
global offset shifts the **whole** curve, unlike the Afterburner rungs, which edit only the floor
region. So agreement between the two ladders would show a shared predictive rule, not the same
electrical state. The grid cannot locate any optimum below 1237.

**Scorer:** `python analysis/score_offset_ladder.py <results-directory>`, after running
`join_hwinfo_voltage.py --join-by time` on each sweep against its own log.

### Result, collected 2026-09-23 — registered verdict INVALID; revised scoring reported beside it

`data/frequency-sweeps/5060ti-offset-ladder-20260923/`. Nothing above was edited. 48 of 48 sweeps
exited 0, and all five offset writes and the final reset were verified by read-back in the console log.

⛔ **Registered verdict: INVALID, by an error in this registration.** "Every sweep must be complete,
with no … missed lock" can never be met on stock: 2932 and 3090 MHz are unreachable, and the stock
suites this design was built from miss them in **24 of 24** sweeps. The scorer also required ±15 MHz
where the sweep tool defines a held lock as ±30, and checked stock memory with the average column
instead of the maximum. The maximum reads 13801–14001 at all 624 points, so memory was stock
throughout. **All three were found after collection and before any median was computed.**

✅ **Revised scoring, POST HOC** (`--revised`): keep rows that missed **below** target, use the tool's
±30 MHz, and invalidate any sweep whose optimum is a missed-lock row. None was.

| registered | measured (revised) |
|---|---|
| opening 0: median 1545 | ✅ **1545**, 10 of 12 |
| **−150: median 1395** (the interior test) | ✅ **1395**, 9 of 12 |
| −300: median 1237 (edge-limited) | ✅ **1237**, 10 of 12 |
| drift bracket: closing = opening | ✅ **1545 = 1545** |
| trend non-increasing | ✅, strictly dropping |

The `gemm` voltage column moves one grid step per −150: the last 0.720 V point runs 1537 → 1387 → 1230
MHz achieved, and the two stock suites read identically. ⚠️ **One chip, one session, one suite per
offset.** −300's pass is edge-limited; only −150 locates the move. **Report both verdicts, always.**

## 8. 3070 Ti: a second Edit 1 suite, plus two fine-sweep checks. Registered 2026-09-23, before collection — COLLECTED 2026-09-24: 8a ✅ PASS, 8b ⛔ FAIL, 8c reported

**No data for any part of this section exists as of registration.** The 3070 Ti's shakedown
(2026-09-23 21:56) and C8 are the only data collected on this card since Amendment 2. Session D's
four registered suites have not run. These runs go on the end of the same unattended session, on
2026-09-24, **after `stock-4` closes the registered bracket**, so nothing here can change how
§4a/§4b are scored. The card is sold in about two days; there will be no later chance.

**Order in the session:**
1. `stock-4`, which is the end of §4a/§4b;
2. the stock fine pair (8c);
3. the Edit 1 fine sweep (8b);
4. `edit1-5`, the replicate suite (8a);
5. `stock-6`, its closing stock suite;
6. cleanup.

Profiles, grid, iterations and labels are those of Session D. The new labels are `rtx3070ti-sessiond-edit1-5`,
`-stock-6`, `-finefloor-asc2`, `-finefloor-desc2` and `-edit1-finefloor`.

### 8a. The replicate: `edit1-5` against `stock-4` and `stock-6`

> **The median suite optimum of `edit1-5` lies in 1170–1275 MHz inclusive**, the same bins as the
> runsheet's §4a prediction, scored by the same rule as `analysis/score_session_d.py` applies to
> `edit1-2`.

**Scoreable only if:**
- `stock-6`'s median equals `stock-4`'s;
- no workload's median absolute throughput change from `stock-4` to `stock-6` exceeds 1.5%;
- the Edit 1 floor check passes on `edit1-5` exactly as it does for `edit1-2`: no clock above
  1200 MHz, within the scorer's tolerance, reads ≤0.825 V, and every target above 1200 reads
  ≥0.831 V.

If any of these fails, the replicate is **NOT SCOREABLE**, not a failure.

**How to report it:**
- ⛔ A median at or above `stock-4`'s is **no movement, and it counts against the replication**.
- If `edit1-2` and `edit1-5` disagree, **report both**. Neither supersedes the other, and there is
  no averaging to a verdict.
- `edit1-5` is n=2 on one chip, one session. It is not a second chip.
- ⚠️ **Its stock bracket is not the design's own.** `stock-4` precedes it after ~25 min of fine
  sweeps, and `stock-6` follows it. Edit 2 is not repeated, so **§4b's control is not replicated.**

### 8b. Where Edit 1's floor ends, measured directly

**The prediction is read from the decoded curve** (Amendment 2):
- a descending locked `gemm` sweep on P2, **1050–1590 MHz, 13 points**, reads ≤0.825 V at every
  target ≤1200 MHz;
- it reads **≥0.831 V at every target above 1215 MHz**;
- at locked **1395 MHz** it reads **0.835–0.870 V**, as the shakedown's 0.850 did.

⛔ **Floor-band voltage above 1215 MHz refutes the as-built reading of Edit 1**, and would call
`edit1-2`'s floor check into question as well.

### 8c. Stock fine pair, ascending then descending. EXPLORATORY: no prediction

It uses the same grid as C8: 1200–1590 MHz, 10 points, `gemm`, 120 iterations, stock P1.

C8 on 2026-09-23 (descending) read **1.1–1.3% below** the 2026-08-27 sweep (ascending) at every
point. Direction and day are confounded in that pair. This pair puts both directions in one
session, and it is reported as the per-point difference, **with no verdict.** ⚠️ It runs after
~5 h of load, so it is warm from the start in both directions, unlike either earlier sweep.

### Results, collected 2026-09-24 — 8a ✅ PASS, 8b ⛔ FAIL, 8c reported

Data: `data/frequency-sweeps/rtx3070ti-sessiond-20260924/`. The 8a scorer was committed while
stock-4 was still collecting (`97a463a`), before any 8a data existed.

**8a ✅ PASS.** `python analysis/score_session_d.py <dir> --replicate`:
- `edit1-5` median optimum **1170 MHz**, inside 1170–1275;
- stock-4 and stock-6 medians are both **1485 MHz**;
- the worst workload's stock-4 → stock-6 change is **1.192%** (limit 1.5%);
- the Edit 1 floor check passes on `edit1-5`.

Reported beside `edit1-2`'s 4a result (**1222.5 MHz**, PASS): the two agree, and neither supersedes
the other. **n = 2 on one chip, one session. The control (4b), which failed, is not replicated.**

**8b ⛔ FAIL: floor-band voltage above 1215 MHz.** Descending locked `gemm` on P2, 1050–1590 MHz:

| target MHz | 1050–1185 (4 points) | **1230** | 1275 | 1320 | 1365 | 1410 | 1455 | 1500 | 1545–1590 |
|---|---|---|---|---|---|---|---|---|---|
| V | 0.819 | **0.819** | 0.838 | 0.844 | 0.850 | 0.850 | 0.856 | 0.863 | 0.869 |

- The first two conditions hold: ≤0.825 V at every target ≤1200 MHz, and the locked-1395 MHz witness
  read **0.850 V**, inside 0.835–0.870.
- **The second fails at 1230 MHz, which reads 0.819 V.** Edit 1's floor ends between **1230 and
  1275 MHz**, not at the as-built reading's 1200. As registered, this **refutes the as-built reading
  of Edit 1** and calls `edit1-2`'s floor check into question. That check passed on the suite grid,
  which has no point between 1170 and 1275, so it could not see 1230. It is the decoder hazard
  CLAUDE.md records: never trust `base + offset` where the offset changes.
- ⚠️ **It does not change how 4a or 8a were scored.** Their registered bins are 1170/1275, and 1170
  is still the highest suite grid point on the floor. But the floor end the predictions assumed was
  wrong by 30 to 75 MHz.

**8c, exploratory, no verdict.** Stock, `gemm`, 1200–1590 MHz, 10 points, in one session:
- **descending minus ascending averages +0.00%**, ranging −0.06% to +0.10%, at 57–60 °C in both;
- **C8 (descending, 2026-09-23) sits 0.64% below both**, −0.57% to −0.72% at every point.

So C8's 1.1–1.3% gap to the 2026-08-27 ascending sweep was **between days, not between
directions**. That matches the ~1.47% cross-session drift CLAUDE.md records on the 5060 Ti.

## 8d. 3070 Ti: the negative control, repeated. Registered 2026-09-25 00:40, before collection — AFTER 4b failed — COLLECTED 2026-09-25: ⛔ NOT SCOREABLE (grid moved); descriptively the control held

**Written after 4b's result was known, and it says so.** That is why it cannot change 4b. **4b
stays FAIL whatever this shows.** It asks one thing: does the control's move repeat?

**Why it is worth the card's last day.** 4b failed at **1432.5 MHz**, a six-six split between the
1380 and 1485 bins. Identical stock suites disagree on 3–4 of 12 per-workload argmaxes, and the
control was never replicated (§8a notes this). One repeat separates "the control moves the optimum
on this chip" from "a near-miss on a noisy median". It does not test whether Edit 2's lowered
825 mV point is responsible; that needs a different curve, and there is no time to build one.

**Design.** A new session, **Session D2**, on the same card:
- SILENT BIOS, and the same Afterburner store, pinned by the `[Profile1]`–`[Profile3]` section hash
  `A1159941DA541EB9`;
- the same grid, iterations and workloads as Session D;
- **three suites, in order:** `stock-7` (P1) → `edit2-8` (P3, Edit 2 unchanged) → `stock-9` (P1);
- labels `rtx3070ti-sessiond-stock-7`, `-edit2-8`, `-stock-9`.

It is scored by `python analysis/score_session_d.py <dir> --control-replicate`, committed before
collection. The rules are 4b's: the six clipped targets form one median-efficiency bin, and the
optimum is scored on the target grid.

> **The median suite optimum of `edit2-8` lies in 1485–1500 MHz inclusive**, 4b's prediction,
> unchanged.

**Scoreable only if:**
- `stock-7`'s median is **1485 MHz**, the registered baseline, and `stock-9`'s median equals it;
- no workload's median absolute matched-target throughput change from `stock-7` to `stock-9`
  exceeds **1.5%**;
- the control floor check passes on `edit2-8` exactly as it does for `edit2-3`.

Otherwise the result is **NOT SCOREABLE**, not a failure.

**How to report it:**
- **PASS:** "4b failed and its repeat passed. The control's move did not repeat. With one of each,
  there is no verdict on the control; the attribution stays unestablished on this chip." ⛔ **Never
  write this as the control holding.**
- **FAIL:** "the control moved twice. On this chip, changing the curve above the floor moves the
  optimum, and the floor-region attribution fails."
- Report it beside 4b, with no averaging. n = 2 control suites on one chip, on two days.
- `stock-7` against Session D's stock suites is descriptive only: a different day, with the
  ~1.5% cross-session drift this project measures.

### ⛔ Result, collected 2026-09-25 — NOT SCOREABLE: the grid was not Session D's

Session D2 ran 08:22–11:43 untouched and ended PASS. **The pre-committed scorer refused it:** the
top six targets were **1605–2130 MHz**, not Session D's 1590–2115. The seven lower targets match
exactly. The card's supported-clock table had 116 entries on Friday against 115 on Thursday; its
cause is unknown, and the same card swept 852–2130 on 2026-09-04. §8d registered Session D's grid,
so **8d is NOT SCOREABLE, not a failure, and 4b stays FAIL.** The scorer was not changed after the
data was seen.

**Descriptive only**, with the registered rules and the collected grid (the six clipped targets as
one bin):
- stock-7, edit2-8 and stock-9 medians are all **1485 MHz**;
- the worst workload's stock return is 0.563%;
- the control floor check passes on all 12.

Had the grid matched, this would read as a pass. **On this chip the control moved once (1432.5,
Session D) and held once (1485, Session D2), on consecutive days. That is a description of two
runs, not a verdict.** Lesson: a registration on this card must name the target list, because the
tool derives it from a table that changes. `data/frequency-sweeps/rtx3070ti-sessiond2-20260925/`.

## 9. RTX 5060 Ti: is the `reduce` residual a workload property or a run-order artifact? (worklist 4m) Registered 2026-09-24, before collection — ✅ COLLECTED THE SAME DAY: WORKLOAD PROPERTY

**No data for this section exists as of registration.**

**Why:** the curve predictor misses all 16 `reduce` curves, every one ABOVE the prediction. Across
twelve committed suites, stock runs put `reduce`'s optimum at 1702 or 1852 against the rule's 1545.
But 14 of the 16 `reduce` legs ran in the same suite position, second, straight after `copy`. The
two explanations predict different things:
- **a workload property** gives the same offset wherever `reduce` runs;
- **an order artifact** gives an offset that follows its position.

**Design:**
- stock Profile 3, verified by memory clock and power limit before the first sweep;
- the suite grid, 1237–3090 MHz, 13 points, ascending;
- the suite iteration counts from `5060ti-stock-repro-20260922`: `copy` 2660, `reduce` 2870;
- eight sweeps in the fixed order **R C C R R C C R**. `reduce` runs **immediately after `copy`**
  twice (sweeps 4 and 8) and **not after `copy`** twice: sweep 1 follows the stock checks and
  sweep 5 follows `reduce`. The balanced order cancels a linear drift;
- labels `5060ti-4m-NN-<workload>`.

**Scoring:** a run's optimum is the grid target with the highest throughput per watt among rows
whose lock held, as the suite analysis defines it.

| outcome | reading |
|---|---|
| all four `reduce` optima **above 1545** | **workload property**: the residual belongs to `reduce` |
| both not-after-copy runs **≤ 1545**, both after-copy runs **above** | **order artifact**: every per-workload residual in the project is suspect |
| anything else | **inconclusive**, reported as the four optima, with nothing more claimed |

⚠️ **The limits, stated now:**
- n = 2 per position, one chip, one session;
- "not after `copy`" mixes two histories (after the stock checks, and after `reduce`), and the
  suites ran `reduce` 1–2 minutes after `copy` on an already-warm card;
- `copy` is the only neighbour tested, so any other kind of order effect is not.

### ✅ Result, collected 2026-09-24: WORKLOAD PROPERTY

`data/frequency-sweeps/5060ti-reduce-order-20260924/`. Nothing above was edited.

**`reduce` optima:**
- 1702 (sweep 1, not after `copy`);
- 1702 (sweep 4, after `copy`);
- 1852 (sweep 5, not after `copy`);
- 1702 (sweep 8, after `copy`).

**All four are above 1545**, so the registered outcome is *workload property*. `copy` optima in the
same session were 1545, 1545, 1702 and 1545. The offset follows the workload, not its position.

⚠️ The curves are flat near the top: every runner-up is within 0.9–2.6% of its optimum. So "above
1545" held 4 of 4, but the exact bin (1702 against 1852) is not stable. n = 2 per position, one chip.

---

## 10. RTX 5060 Ti: the negative control, repeated in one session. Registered 2026-09-25, before collection

**Why now.** On the 3070 Ti the above-floor control moved the optimum (§4b FAIL,
2026-09-24). The 5060 Ti's control, `repair-suite-p2-20260909`, has run **once**:
- it held its median (1537 MHz);
- 4 of 12 workloads moved against the stock bracket;
- it had no same-session bracket of its own configuration.

The paper's causal claim now rests on this card, so the control is repeated before anything is
built on it. ⚠️ **It is not the original registration.** That was a single P2 suite, scored against
the P5 legs and the stock suite of earlier sessions.

**Design.** One session, operator absent, driven from the agent's elevated shell through
`tools/hwinfo-logging/Invoke-LoggedSweep.ps1`, as the 2026-09-22 to 09-24 queues were.
- **P5 → P2 → P5**, three twelve-workload suites.
- P5 (split) and P2 (repair) are **identical below 800 mV** and differ by up to 570 MHz above it,
  with the same memory (+2500) and power limit (200 W). Stock is not in the bracket, so the
  comparison changes one thing: the curve above the floor.
- Store verified before collection: all five slots are identical, section for section, to
  `data/afterburner-profiles/5060ti-profiles-20260922-rungB/`. `[Profile2]`, `[Profile3]` and
  `[Profile5]` hash to `86F30A00…`.
- The original control's work exactly: grid 1236–3090 MHz, 13 points, ascending, with its
  iteration counts, which are taken from its sweep JSONs.
- Each slot is verified under load before its suite: memory 16301 MHz and power limit 200 W for
  both. P2 and P5 are told apart by the unlocked `gemm` peak clock. The 09-09 control put P2's top
  achieved clock ~84 MHz below P5's (2888 against 2972), so the witness requires **P5 ≥ 2935 MHz**
  and **P2 ≤ 2925 MHz**. Otherwise the run stops.

> **The median suite optimum of the P2 suite equals the median of each P5 suite**, on the target
> grid, per workload by `analyze_sweep.efficiencyPeak`. It is the same rule and the same statistic
> as §4b and §8d.

**Scoreable only if:**
- the two P5 suites have the **same median**;
- no workload's median absolute matched-target throughput change between them exceeds **1.5%**;
- every slot witness passed.

Otherwise NOT SCOREABLE, which is not a failure.

**Reporting, fixed now:**
- **The per-workload count of P2 optima that differ from both P5 optima is reported beside the
  verdict, always.** A zero median shift is never written as "nothing moved" (CLAUDE.md).
- **PASS:** "the 5060 Ti's control held its median again in a same-session bracket, with *k* of 12
  workloads moving."
- **FAIL:** "the 5060 Ti's control moved in a same-session bracket. With the 3070 Ti's §4b, an
  above-floor edit moved the optimum on both chips, and the floor-region attribution is not
  established on either."
- n = 1 chip; the twelve workloads are repeated outcomes on it.

**What it cannot settle:** the manipulation. The 5060 Ti's manipulation (`abba-20260908`) was found
in a run registered for a different prediction; rung B (§1) is its registered test.

### ⛔ Amendment, 2026-09-25, before collection: the slot witness is replaced

The peak-clock witness above came from the 09-09 locked sweeps and **does not separate the slots
unlocked**. It was measured before any suite ran:
- P5's unlocked `gemm` median was 2872 MHz (max 2925) and P2's 2835 (max 2887);
- the ranges overlap, and P5 never reached the registered 2935;
- a first P5 probe recorded no loaded samples at all.

The run would have stopped at its first check.

**The replacement is `gemm` power at a locked 2475 MHz**, where the decoded curves put P2 near
928 mV and P5 near 862 mV. It was measured A–B–A–B the same morning:

| probe | slot | median power | range |
|---|---|---|---|
| a | P5 | 151.8 W | 146.9–154.3 |
| b | P2 | 176.1 W | 170.8–178.8 |
| c | P5 | 152.9 W | 148.6–156.3 |
| d | P2 | 177.4 W | 171.3–180.7 |

**The witness requires P5 ≤ 163 W and P2 ≥ 165 W** (median of loaded samples after the first six).
These are thresholds between two measured clusters 14 W apart, set from these four probes and
recorded here with them. **Nothing else in §10 changes.** No suite had run.

### ⛔ Result, collected 2026-09-25 — NOT SCOREABLE: the P5 bracket did not return

`python analysis/score_control10.py data/frequency-sweeps/5060ti-control10-20260925`, with the
scorer committed before its data was read (`b2d83b9`):
- all three medians are **1545 MHz**;
- **the P5 return fails in 11 of 12 workloads, the worst by 7.57%** (limit 1.5%);
- P2's optimum differs from both P5 optima in **4 of 12** workloads.

**No verdict on the control, as registered.**

The closing P5 suite ran uniformly slower, from −8.5% at 1237 MHz to −4.5% at 3090, with raised
idle baselines. P2 matches the opening P5 suite within ±0.1% below 2010 MHz. That is the
contamination signature. **Its cause is not established:** Codex tool processes started at 13:43
and 13:47, and the closing suite began at 13:47:32, but nothing shows Codex used the GPU.
Descriptively, against the uncontaminated opening suite, P2 holds the median with 4 of 12 moving,
the same shape as 2026-09-09. Details are in the data README. ⚠️ **A re-collection would need the
Codex and ChatGPT apps closed**, and it would be registered as an amendment before collection, as §5
was.

## Safety envelope — these cards are going to be sold

**The hardware risk of a floor manipulation is low and should be stated plainly rather than
gestured at: undervolting reduces electrical and thermal stress, and the failure mode is a driver
reset, which self-recovers and clears the offsets.** The one crash this project has induced —
875 mV pinned at 3000 MHz, deliberately past the edge — did no damage. What follows is about
leaving a card in a known-good state for a buyer, not about protecting silicon from a curve edit.

1. ⛔ **Power limit stays at stock. Never raised.** Not needed for any prediction above.
2. ⛔ **Memory clocks are not touched.** Memory is the genuinely risky axis — GDDR6X thermals on the
   3070 Ti, and silent error-correction retries that make a "stable" overclock net *slower*. No
   prediction here needs it.
3. ⛔ **Peak voltage never exceeds the stock curve's maximum.** Reshaping means moving clocks at a
   given voltage, not raising voltage.
4. ✅ **Snapshot the profile store verbatim before the first change**, into
   `data/afterburner-profiles/`, per the convention that exists because a slot number is not an
   identity.
5. ✅ **Stability protocol after the manipulation**, and **verify return to stock before shipping** —
   read back the power limit, memory clock under load, and peak core, as was done for Profile 3 on
   2026-09-09. A driver reset silently clears offsets, so a card can look tuned in its settings
   string and be running stock.
6. ⚠️ **Uninstall what was installed.** The collection kit deliberately leaves nothing behind; a
   manipulation needs Afterburner present, which does not. Remove it and its profile store.

## Order of operations, given both cards leave soon

1. **2060 Super fine floor sweep** — 10 minutes, no elevation, no manipulation. Needed for 4c and
   valuable alone as the first measured Turing V/F curve in this literature.
2. **3070 Ti: 4a then 4b.** The replication is the point; the control is what makes it mean
   something.
3. **2060 Super manipulation (4c)** only if time remains after 1 and 2.

🔑 **If only one thing gets done, do the 3070 Ti pair.** It is what converts "one chip" into
"two chips, two architectures", and that is the sentence the paper currently cannot write.
