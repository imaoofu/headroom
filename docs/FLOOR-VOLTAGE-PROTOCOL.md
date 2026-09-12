# Measuring a card's load-floor voltage

**Ten minutes per card, stock settings only, nothing tuned.** This is the cheapest measurement in
the project and the one with the most leverage, because the load-floor voltage is the single
parameter that **does not transfer between cards** and therefore gates every application of the
load-floor mechanism to hardware it has not seen.

| card | arch | node | SMs | TDP | memory | floor voltage | floor holds to |
|---|---|---|---|---|---|---|---|
| MSI Ventus 2X RTX 2060 Super | Turing (TU106) | 12 nm | 34 | 175 W | GDDR6 | **0.631 V** | ⚠️ 975 or 1035 |
| Zotac RTX 5060 Ti Twin Edge OC | Blackwell (GB206) | 5 nm | 36 | 180 W | GDDR7 | **0.720 V** | 1552 MHz |
| ASUS RTX 3060 Phoenix 12 GB | Ampere (GA106) | 8 nm | 28 | 170 W | GDDR6 | **0.756 V** | 1260 MHz |
| RTX 3070 Ti | Ampere (GA104) | 8 nm | 48 | 290 W | GDDR6X | **0.812 V** | 1500 MHz |

⛔ **This table said "n = 2" and omitted the 3070 Ti when this file was written on 2026-09-11.** That
was wrong, and wrong in the way this project keeps warning about: the third measurement was already
in the paper (§5.5) and in `data/frequency-sweeps/rtx3070ti-20260825/`, and I asserted a sample size
without counting it. **n = 3.**

🔑 **AND THE THIRD CARD IS THE INTERESTING ONE, because it breaks the obvious story.** The 3060 and
the 3070 Ti are **the same architecture on the same process node** and their floors differ by
**56 mV** — a larger gap than the **36 mV** between the 8 nm parts and the 5 nm one.

> **Process node does not determine the load-floor voltage, in any direction.**

⛔ **n = 4 as of 2026-09-12, and the node story is dead.** The 12 nm Turing part returns the
**lowest** floor of the four, 89 mV below the next. Ordered by node — 12, 8, 8, 5 nm — the floors run
0.631, 0.756, 0.812, 0.720 V: not monotone, and not monotone in the reverse direction either. Two
parts sharing an architecture *and* a node already differed by 56 mV before this card was measured.

⚠️ **A fourth card also found the limit of the measurement itself.** The 2060 Super holds its floor
across **more than 570 MHz** and leaves it **6 mV at a time**, so where the floor *ends* — the
quantity the mechanism actually needs — is undecidable at this sensor's resolution. Record the span
and the exit step, not just the value: a floor is only useful if the curve leaves it sharply.

Four points is still not a dataset. But it is enough to rule things out, which is worth more than
enough to fit something.

---

## Why this is the measurement worth standardising

`analysis/models/predict_from_curve.py` predicts a card's efficiency optimum as **the highest
frequency its V/F curve reaches at the load-floor voltage**. That rule has held on two
architectures. The *constant* has not: borrowing the 5060 Ti's 0.720 V for the 3060 predicts
~1530 MHz against a true optimum of 1260 — a **270 MHz error**, worse than guessing a constant.

So the mechanism is currently **measure-then-predict**, not predict. If the floor voltage turns out
to be predictable from a spec sheet — process node, architecture, memory type, TDP — the whole thing
becomes zero-measurement on an unseen card. That is a real ML target with a real payoff, and it
needs roughly **5 to 8 cards** before it can even be looked at honestly.

⚠️ **Do not fit anything to fewer than that, and say n out loud every time.**

---

## 🛑 Consent and safety

**This protocol locks core clocks.** That is a temporary, reversible change to GPU state, not a
tune: it never touches voltage, power limit, memory clock, or any overclock, and the sweep tool
resets clocks through a `try/finally` that also unwinds on Ctrl+C. Clock locks do not survive a
reboot, which is the backstop.

- ✅ **Machines Raymond owns:** run it.
- ⚠️ **A customer's or friend's machine: ask first, in plain words, and take no for an answer.**
  `CLAUDE.md` puts business reputation above data, and that ordering does not change because a
  measurement is cheap. The RTX 3060 and RTX 3070 Ti data were both collected this way, with the
  owner's agreement.
- ⛔ **Never as part of a paid job the customer did not ask for.** A build is not consent.

**The card runs at or BELOW stock the entire time.** The frequencies probed are in the lower half of
the supported range, so the card is underclocked throughout — the opposite of a stress test. Peak
observed on the reference machine was 60 °C / 132 W against an 88 °C ceiling.

---

## The procedure

Everything runs from the USB collection kit. **Nothing is installed on the host.**

### 1. Preflight

Plug in the kit and run `RUN-ME.bat`, which calls `preflight.py`. It checks the GPU is visible,
the baseline is quiet, and free VRAM is sufficient.

⚠️ **Close Wallpaper Engine, browsers and media players, and switch off NVIDIA Instant
Replay / ShadowPlay.** Instant Replay is invisible at idle and depresses mid-band throughput by
~3%. It does not affect the *voltage* reading this protocol is after, but the same run produces an
efficiency curve, and that curve is contaminated without this step.

### 2. Start HWiNFO logging

`HWiNFO64.exe` ships on the kit. Sensors-only mode, logging to CSV:

```
F:\headroom-kit\HWiNFO64.exe
```

The kit's `HWiNFO64.INI` sets `SensorInterval=500`, so it samples at **0.50 s** — about 56 samples
per 28-second frequency point, which is ample for a per-point median.

⚠️ **The rate is not the same everywhere, and it is worth knowing which you have.** The 5060 Ti's
own logs were taken at **2.00 s** on the main machine, giving ~14 samples per point. Both work; the
kit's is better. Verified by measuring the timestamp spacing of all 17 committed HWiNFO logs rather
than by reading a setting — `CLAUDE.md` asserted "2 s polling" as a single project-wide figure until
2026-09-11 and it was never true of the kit.

Start the CSV log **before** the sweep and stop it **after**. ⛔ **One log must never span a
settings change** — the join bins samples by core clock, and a log covering two configurations
silently mixes them.

### 3. Run a single-workload sweep

```powershell
.\Collect.ps1 -Label "<vendor>-<model>-asfound" -AppliedSettings "stock, PL default, no OC" -Workloads gemm
```

Thirteen locked frequencies, ~28 s each: **about 10 minutes** including settle time. `gemm` is the
right workload here because it is compute-bound, so it holds the card at the locked clock rather
than stalling on memory.

⚠️ **Use the DEFAULT iteration count.** Do not calibrate it for this card. A count calibrated
elsewhere measures something else, and comparability across cards is the entire point of this
protocol — see `data/frequency-sweeps/rtx3060-20260910/README.md`, which kept default counts for
exactly this reason.

### 4. Stop HWiNFO, then join

```bash
python tools/frequency-sweep/join_hwinfo_voltage.py <sweep.csv> <hwinfo.csv>
```

The join discards samples below **30 W** so idle ramp-up and ramp-down — which sit at boost
voltage — cannot manufacture a voltage slope that is not there. That filter is load-bearing.

### 5. Read the floor off the joined table

**The load floor is the lowest core voltage that repeats across two or more consecutive grid points
under load.** The **floor extent** is the highest frequency still sitting at it.

Worked example, RTX 3060:

| target MHz | 840 | 945 | 1050 | 1155 | **1260** | 1365 |
|---|---|---|---|---|---|---|
| core V | 0.756 | 0.756 | 0.756 | 0.756 | **0.756** | 0.794 |

Floor **0.756 V**, extent **1260 MHz** — and the measured `gemm` optimum was 1260 MHz.

⚠️ **The load floor is not the card's minimum voltage.** The same logs show **0.650 V at idle** on
the 5060 Ti against a 0.720 V load floor. The statement the data supports is *"the card will not run
LOADED below this voltage"*, and the 30 W filter is what keeps those two things apart.

⚠️ **If the voltage never flattens**, the card has no floor inside the swept range and this protocol
records that rather than inventing a number. Write it down as "no floor observed, range X–Y MHz".
A card without a floor is a genuine test of the mechanism, not a failed measurement.

### 6. Record the card

Into the run's README, alongside the sweep:

- **Exact board**: vendor, model, SKU, and whether it is a factory-OC variant
- **Driver version** — read it off the sweep JSON, never off `CLAUDE.md`
- **Power limit**: default and enforced, in watts
- **Architecture, process node, SM count, TDP, memory type and bus width** — most of these are in
  `data/external/all-gpus.json`, so the board name is usually enough to join on
- **Floor voltage, floor extent, measured optimum** — the three numbers this exists to produce
- **Who owns the machine and that they agreed**

---

## What this feeds

Each card is **one row** toward asking whether floor voltage is predictable from specs. Revised
2026-09-11 once the 3070 Ti was counted, because the ordering it implies is not the one this section
originally listed:

1. ⛔ **Process node, ALONE — already insufficient at n = 3.** Two 8 nm Ampere dies read 0.756 and
   0.812, a 56 mV spread against 36 mV between 8 nm and 5 nm. Node may still set a *level*; it
   cannot be the whole model.
2. ✅ **Die size / power class WITHIN an architecture** — the one relationship that is monotone in
   the data so far. Among the two Ampere parts: 28 SMs / 170 W reads 0.756, 48 SMs / 290 W reads
   0.812. ⚠️ Monotone across **two points**, which is not evidence, only a direction to test.
3. **Architecture as an offset on top of that**, which would explain why the 5 nm Blackwell part
   sits below both Ampere parts despite a mid-sized die.
4. **Memory type**, confounded with everything else here — GDDR6, GDDR6X and GDDR7 appear once each.
5. **Individual-die binning**, which nothing in this project can see, because **no model has been
   measured twice**.

🔑 **The fifth is still the cheapest thing that would change what is knowable.** Two samples of the
same model separate "the floor is a property of the design" from "a property of the individual die".
If it is the latter, no spec-sheet model can work at all, and two ten-minute runs would establish
that before any effort goes into building one.

⛔ **Until n is 5 or more, this file records measurements and rules things OUT. It states no
relationship.** Any card added should have its numbers written into
`data/frequency-sweeps/<run>/README.md` and the table at the top of this file updated.
