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

## Prior registrations, recorded elsewhere

Kept here as pointers so the practice is visible in one place. These were registered in their own
data READMEs before this file existed.

| experiment | registered prediction | outcome |
|---|---|---|
| `abba-20260908` | the optimum moves with the floor region of the curve | ✅ **+465 MHz in 12 of 12 workloads** |
| `repair-suite-p2-20260909` | changing the curve *above* the floor moves the optimum **not at all** | ✅ optimum unmoved despite a 570 MHz change |
| `rtx3060-20260910` | the rule holds on a different architecture | ✅ holds — ⛔ but the floor **voltage** does not transfer (0.756 V, not 0.720) |
