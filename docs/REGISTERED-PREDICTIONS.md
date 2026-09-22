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

## 1. The floor ladder — PENDING, registered 2026-09-11

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

*(empty — to be filled after collection, without editing anything above)*

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

## 4a. 3070 Ti — the replication. **The single highest-value prediction in this document.**

> **Extend the stock floor upward by reshaping only the curve at and below 0.819 V, and the median
> suite optimum will move with the new floor end, in the same direction and by a comparable
> fraction of the shift.**

Success is the optimum tracking the new floor end to within one grid step. ⛔ **A movement in the
wrong direction, or no movement, refutes the causal claim on a second chip and must be reported as
the headline** — the 5060 Ti result would then be a single-chip curiosity rather than a mechanism.

## 4b. 3070 Ti — the negative control, run in the same session or not at all

> **Change the curve only ABOVE the floor voltage, by at least 300 MHz, and the optimum will not
> move.**

⚠️ **The manipulation without its control is worth much less than half the experiment.** A council
reviewer specifically defended this design: sharing chip, session and operator is what a negative
control is *for*. If the session is cut short, run 4b, not a second replicate of 4a.

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
