# RTX 3070 Ti — the bench list

**Written 2026-09-22.** A shop machine, so **it ships, date unknown**, and its items outrank the
5060 Ti's on any day it is reachable. Shared protocol: [`GPU-BENCH-RULES.md`](GPU-BENCH-RULES.md).

| document | what it is |
|---|---|
| [`SESSION-D-COMMANDS.md`](SESSION-D-COMMANDS.md) | **the commands, in order**: read this at the machine |
| [`SESSION-D-RUNSHEET.md`](../data/frequency-sweeps/rtx3070ti-20260825/SESSION-D-RUNSHEET.md) | the design, the stock curve as measured, why each edit is shaped as it is, what each outcome means |
| [`REGISTERED-PREDICTIONS.md`](REGISTERED-PREDICTIONS.md) §4a–4b | the predictions, registered before any edit |

🔑 **Session D is the single item that changes what the paper can claim.** The causal result is
one chip. This makes it two chips and two architectures, with the negative control. After the
2026-09-22 narrowing (Mendes et al., SBAC-PAD 2020, already moved an optimum), **the control is
the part of the design nobody has published**. A Session D without run 3 buys much less.

⚠️ **Logging is by hand on this machine.** The HWiNFO automation is not on the USB kit.

---

## 🛠️ Curves to build — all three BEFORE the first sweep

Build them first, at minute 15, not between runs. Curve-building is exactly the desktop activity
that contaminates a run, and building first reveals at once whether the edits can be applied.
**Snapshot the profile store before the first edit** (`SESSION-D-COMMANDS.md` §2).

| slot | curve | how |
|---|---|---|
| **P1** | **STOCK** | Save untouched, before any edit |
| **P2** | **Edit 1: the manipulation** | **CAP every point at or below 0.825 V at 1200 MHz.** 0.831 V and above stay at stock. Drag **down** only; a far-left point already below 1200 stays where it is |
| **P3** | **Edit 2: the negative control** | **Flatten every point at 0.831 V and above to 1500 MHz.** 0.825 V and below stay at stock |

✅ **Both are safe by construction.** After either edit, every clock costs at least the voltage it
cost at stock. Instability is not reachable.

### 🛑 OPEN: Edit 1 would not apply, and the cause is not known

**Reported by Raymond:** *"I can't set 825 mV directly to 1200 MHz, Afterburner won't let me apply
it."* The failure mode was never pinned down, and it decides the fix. **At the machine, note which
one it is:**

| what happens | likely cause | try |
|---|---|---|
| the point snaps back when released | a single point cannot sit below the points to its left | **Cap from the left edge rightward**, so the curve never decreases mid-edit. Or select the whole range ≤0.825 V and drag it down as one |
| Apply is refused, or the curve resets on Apply | a downward step somewhere in the curve | look for any point left of 0.825 V still above 1200 |
| other points move with it | Afterburner's range-drag behaviour | confirm the result by reading the points back, not by eye |

⚠️ **These are candidate explanations, none tested on this card.** The earlier correction, capping
everything instead of leaving the points below 0.812 V at stock, is in `SESSION-D-COMMANDS.md` §5.
⛔ **The report above came AFTER that correction, so capping alone did not fix it.** **Build P2 first, precisely because this is the risk.** If Edit 1 cannot be applied,
runs 2 and 3 are impossible and the session becomes a stock replicate. Learn that before the
first sweep, not seventy minutes in.

🔧 **Last resort, not yet tried:** this project has decoded Afterburner's curve format (127 points ×
offset, voltage, base clock). The curve can be written straight into the profile `.cfg` with
Afterburner closed, then applied with `-profile2 -q`. **Untested on any card**; only if the GUI route
fails and the card is about to leave.

---

## Session D — the order, ~5 h 40

| # | what | time | cut? |
|---|---|---|---|
| 0 | Confirm the **SILENT BIOS** position (290 W) and a quiet machine | 5 min | never |
| 1 | Re-sync the kit; install Afterburner; **snapshot the profile store** | 15 min | never |
| 2 | **Build P1, P2, P3** — see above | 15 min | never |
| 3 | Apply P1, **verify stock three ways**. ⛔ **Do NOT calibrate**: reuse the 09-04 iteration counts in `SESSION-D-COMMANDS.md` §4 | 5 min | never |
| 4 | **Run 1: stock suite** | 62 min | never |
| 5 | **Run 2: Edit 1 suite**, the manipulation. Predicted: median optimum **1485 → 1170 or 1275 MHz** | 62 min | never |
| 6 | **Run 3: Edit 2 suite**, the negative control. Predicted: stays at **~1485–1500 achieved**; the six clipped rows count as one bin | 62 min | 🛑 **never** |
| 7 | **Run 4: stock again**, closes the drift bracket; must return to run 1 within ~1.5% | 62 min | 🥈 second cut |
| 8 | Descending stock fine sweep, §4d on a third architecture | 12 min | 🥇 first cut |
| 9 | Revert, **verify stock three ways**, uninstall Afterburner and its profile store | 15 min | never |

### Go / no-go: count the hours at the machine BEFORE installing anything

| hours available | do |
|---|---|
| **5½+** | everything |
| **~4½** | cut step 8, then step 7 |
| **under ~4¼** | ⛔ **do not start.** Keep Session D whole for a day that has the hours |

⚠️ **The one exception:** if the card is leaving for good, a stock + Edit 1 pair still replicates
the *treatment* on a second chip. Write it up as that, **never as the controlled design**.

**Cutting run 4 does not invalidate the result.** The prediction is a shift of two or three grid
points (1485 → 1275 or 1170 on a 105 MHz grid), and cross-session drift (~1.47% on `gemm`) does not move a grid point. It weakens the write-up;
it does not void it.

---

## Also possible on this card, only after Session D

| item | time | why |
|---|---|---|
| Put `tools/hwinfo-logging/` on the kit | desk work | would remove the per-run log clicks here. Not a one-line sync: the wrapper uses the Python on `PATH`, not the kit's bundled interpreter, and writes to a fixed `C:` folder |

## Before the card ships — every time

**Revert to stock and verify three ways:** power limit, memory clock under load, and peak core
reaching **~1763 MHz**. Then **remove Afterburner and its profile store.** A driver reset silently
clears Afterburner offsets, so a settings string proves nothing.
