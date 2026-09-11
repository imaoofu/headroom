# Measuring a card's load-floor voltage

**Ten minutes per card, stock settings only, nothing tuned.** This is the cheapest measurement in
the project and the one with the most leverage, because the load-floor voltage is the single
parameter that **does not transfer between cards** and therefore gates every application of the
load-floor mechanism to hardware it has not seen.

| card | arch | node | floor voltage |
|---|---|---|---|
| Zotac RTX 5060 Ti Twin Edge OC | Blackwell (GB206) | TSMC 4N | **0.720 V** |
| ASUS RTX 3060 Phoenix 12 GB | Ampere (GA106) | Samsung 8 nm | **0.756 V** |

🔑 **n = 2.** Two points is not a dataset and nothing should be fitted to it. The purpose of this
protocol is to make n grow one card at a time, at a cost low enough that any machine passing
through the bench can contribute.

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

`HWiNFO64.exe` ships on the kit. Sensors-only mode, **2-second polling**, logging to CSV:

```
F:\headroom-kit\HWiNFO64.exe
```

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

Each card is **one row** toward asking whether floor voltage is predictable from specs. The obvious
candidates, in rough order of plausibility:

1. **Process node.** 4N reads 0.720, Samsung 8 nm reads 0.756. ⚠️ Two points define a line
   trivially and this ordering could reverse on the third card.
2. **Architecture / vendor library**, which is confounded with node in both samples so far.
3. **Memory type**, GDDR6 vs GDDR6X vs GDDR7.
4. **Board binning**, which would show up as spread between two samples of the same model — and
   nothing in this project has yet measured the same model twice.

🔑 **The fourth is the one worth reaching first.** Two cards of the same model would separate "the
floor is a property of the silicon design" from "the floor is a property of the individual die", and
that distinction decides whether a spec-sheet model is possible at all. It costs two ten-minute runs.

⛔ **Until n is 5 or more, this file records measurements and states no relationship.** Any card
added should have its numbers written into `data/frequency-sweeps/<run>/README.md` and the summary
table at the top of this file updated — nothing else.
