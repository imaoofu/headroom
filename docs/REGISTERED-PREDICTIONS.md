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

## 2. Profile 1 — PENDING, registered 2026-09-11

**Status: not yet swept.**

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

### Result

*(empty — floor voltage and extent to be written here BEFORE the efficiency optimum is read)*

---

## Prior registrations, recorded elsewhere

Kept here as pointers so the practice is visible in one place. These were registered in their own
data READMEs before this file existed.

| experiment | registered prediction | outcome |
|---|---|---|
| `abba-20260908` | the optimum moves with the floor region of the curve | ✅ **+465 MHz in 12 of 12 workloads** |
| `repair-suite-p2-20260909` | changing the curve *above* the floor moves the optimum **not at all** | ✅ optimum unmoved despite a 570 MHz change |
| `rtx3060-20260910` | the rule holds on a different architecture | ✅ holds — ⛔ but the floor **voltage** does not transfer (0.756 V, not 0.720) |
