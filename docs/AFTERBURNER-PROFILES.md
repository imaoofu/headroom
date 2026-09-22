# The five Afterburner profiles on the 5060 Ti — decoded from disk

**Decoded 2026-09-08 from `Profiles\VEN_10DE&DEV_2D04&SUBSYS_177219DA&REV_A1&BUS_1&DEV_0&FN_0.cfg`.**

This file exists because **a profile identified by slot number is not identified.** On 2026-08-30 a
run was labelled "memory untouched — verified 14001 MHz stock" while a +2500 offset was live, and
the fix at the time was to probe the memory clock under load. That catches stock-versus-tuned. It
does **not** catch tuned-versus-a-different-tune, because four of these five profiles carry the same
+2500 memory offset. This table is the part that does.

✅ **CORRECTED 2026-09-09 — Profile 3 IS NOW STOCK, and the sentence this replaced was already
stale when it was written.** It said: *"None of these is stock. Every slot carries a memory offset and
127 non-zero V/F curve points. There is no stock profile to apply."* The operator wiped Profile 3 to
stock in the **same** edit that raised Profile 4's plateau on 2026-09-08, and the `…20260908b…`
snapshot captured it — the snapshot data was complete; the write-up beside it described only the
Profile 4 half. **When two things change in one edit, diff every slot, not the one you were
expecting.**

**How "stock" was verified, on disk:** a stock slot is not one with *no* curve — Afterburner stores
the factory curve as 122 points whose per-point **offsets are all zero**, so `applied = base`.

| profile | curve points | with a non-zero offset | mem boost | core boost | PL |
|---|---|---|---|---|---|
| P1 | 126 | 86 | +2000 | −502 | 100 |
| P2 | 125 | 12 | +2500 | −502 | 111 |
| **P3** | **122** | **0** | **+0** | **+0** | **100** |
| P4 | 126 | 86 | +2500 | −502 | 111 |
| P5 | 126 | 61 | +2500 | −502 | 111 |

Zero curve offsets, zero memory offset, zero core offset, and PL 100 — which is **180 W, this card's
factory default**. That is stock in every respect the profile store can express.

⛔ **STALE APPLICATION WARNING, CORRECTED 2026-09-21.** This paragraph said *"Verified on disk,
NOT yet verified in application"* and *"the check ... has not been run."* It was left in place
after the **2026-09-09 11:38** application probe, which was recorded in
`data/frequency-sweeps/stock-bracket-20260909/README.md` and the stock leg's session JSON. The
guide was updated for the disk decode but its pending application check was not revisited.

✅ **Profile 3 was verified in application on 2026-09-09:** after `-profile3 -q`, the enforced power
limit fell **200 → 180 W**, memory under load read **13801 MHz** rather than 16301, and peak core
clock read **2640 MHz** against Profile 4's ~2976. The stock sweep's CSV and JSON preserve the
180 W enforced limit and stock memory readings. This verifies that historical application; a new
session must still check the live card after applying the profile.

⚠️ **The operator states that none of the five has been stability tested.** The repository records
30-minute protocol runs on 2026-08-23 for "the split curve" and "the original tune", but those were
hand-set curves and nothing verifies they are identical to what is now saved in these slots. Treat
the profiles as untested. The operator reports P4 and P5 as game-stable, which is weak evidence and
is recorded as such.

---

## The table

Effective core clock (MHz) at each voltage — base plus offset, as applied:

| profile | PL% | mem boost | 700 mV | 800 mV | 875 mV | 925 mV | plateau | knee |
|---|---|---|---|---|---|---|---|---|
| **P1** | 100 | **+2000** | 1897 | 2317 | 2752 | 2934 | 2962 | 940 mV |
| **P2** | 111 | +2500 | 1447 | 1852 | 2280 | 2455 | 3022 | 940 mV |
| **P3 — STOCK** | 100 | **+0** | 1447 | 1852 | 2280 | 2460 | **3090** | 940 mV |
| **P4** | 111 | +2500 | **1912** | 2317 | 2752 | 2932 | **3030** | 940 mV |
| **P5** | 111 | +2500 | 1447 | 1852 | **2850** | **3030** | 3030 | **925 mV** |

PL 100 = 180 W, PL 111 = 200 W. "Knee" is the lowest voltage at which the curve reaches within 0.5%
of its own plateau. **P3's row is the factory curve** and P4's plateau is the post-2026-09-08 value.

🔑 **Having stock decoded settles a claim this project had only asserted.** §5.7 describes P2 and P5
as "restoring the stock voltage slope below the knee". That is now literally checkable, and it is
exact: **P2 and P5 read 1447 / 1852 / 2280 at 700 / 800 / 875 mV — the same numbers as stock** — and
the reason is visible in the offsets. P2 carries only 12 non-zero curve points and P5 carries 61, all
of them high on the curve; their low ends are stock because the offsets there are *zero*. The
description was right, and it is no longer an assertion.

⚠️ **An undecoded field: `CoreClkBoost` reads −502 MHz on P1, P2, P4 and P5, and +0 on stock.** It is
**not** applied on top of the curve, on two pieces of evidence: NVML reports a **0 MHz** P0 graphics
offset with Profile 4 and Profile 5 live, and the 2026-09-08 optimum predictions — computed from the
curve *without* subtracting 502 — hit 2002 and 1537 exactly, which a missing 502 MHz shift would have
destroyed. **That is an empirical inference, not a decoded fact.** Do not add it to a curve reading,
and do not claim to know what the field means.

## Three curve shapes, not five

- **P1 / P4 — the aggressive-low-end family.** ~1900 MHz at 700 mV. These pin voltage low across
  a wide frequency range, which is the mechanism behind both the `gemm` power advantage and the
  `membw` crossbar plateau. **P1 is the milder of the two: +2000 memory and PL 100**, an earlier
  attempt. ⛔ **This bullet used to read "P1 / P3 / P4" and to say "P3 and P4 differ only in power
  limit — same curve, 180 W versus 200 W". P3 is stock and that pair no longer exists.** It had been
  the only single-variable pair in the whole profile set, and losing it is a real cost — but what
  replaced it is worth more, because a stock control is what every cross-configuration comparison in
  this repository has lacked.

  🔑 **P1 AND P4 CARRY THE IDENTICAL +478 MHz FLOOR OFFSET, AND P1 HAS NEVER BEEN SWEPT
  (2026-09-11).** Reading the floor extent for all five slots rather than the four that have data:

  | slot | offset at 0.720 V | **floor extent** | nearest grid target | plateau | mem | PL |
  |---|---|---|---|---|---|---|
  | P3 stock | +0 | 1530 | 1545 | none | +0 | 100% |
  | P2 repair | +0 | 1530 | 1545 | 3022 | +2500 | 111% |
  | P5 split | +0 | 1530 | 1545 | 3030 | +2500 | 111% |
  | **P1** | **+478** | **1972** | **2010** | 2962 | +2000 | **100%** |
  | P4 full tune | +478 | 2002 | 2010 | 3030 | +2500 | 111% |

  ⚠️ **P1 is easy to mis-remember as "the memory-only profile" and it is not one** — its core curve
  is P4's in the region that decides the optimum. It is a **fifth configuration**, and the mechanism
  makes a falsifiable prediction about it that costs one suite to check: **its optimum should land on
  the same 2010 MHz grid point as P4**, because 1972 and 2002 are 30 MHz apart against a ~155 MHz
  grid step.

  🔑 **That would be a THIRD control, on the one variable the other two do not touch: power limit.**
  The manipulation arm (`abba-20260908`) moved the floor and the optimum moved with it; the negative
  control (`repair-suite-p2-20260909`) moved the curve *above* the floor and the optimum did not
  move. P1 against P4 changes **power limit (180 W against 200 W) and memory (+2000 against +2500)
  while holding the floor region fixed** — so the mechanism predicts no movement. ⚠️ **It is a
  two-variable contrast, not a clean single-variable one**, which weakens it as a *cause* test but
  not as a *prediction* test: the mechanism says the optimum is set by the floor extent alone, so any
  movement at all refutes it regardless of which of the two did it.

  ⚠️ **The floor extents differ by 30 MHz for a reason nobody has checked**: P1's base curve reads
  1494 MHz at 720 mV where P4's reads 1524, though their offsets are identical. Two clock bins. Do
  not assume the base curve is a constant of the card until that is looked at.
- **P2 — the repaired shape.** Gentle low end (1447 at 700 mV) *and* a low mid-band (2280 at 875 mV).
  This is the curve-fixed / repair geometry: stock voltage slope restored across the whole lower
  range. **Its low end is not merely stock-like — it is stock**, offsets zero, and only 12 of its 125
  points are touched at all.
- **P3 — stock.** The factory curve, no offsets anywhere, 180 W. See the correction above.
- **P5 — the split-region curve.** Gentle low end like P2, then climbs steeply above 850 mV to reach
  the 3030 plateau by 925 mV. Stock slope below the knee, flattened region above it, which is the
  design the paper describes in §5.7.

## 🔑 Which profile is live: identify by POWER, not by clock

**The top-of-grid achieved clock cannot distinguish these profiles.** Tried 2026-09-08: the full tune
peaks near 2948 MHz and the split curve near 2977, ~29 MHz apart, which is inside thermal and
run-to-run variation. A probe on Profile 4 returned 2965.6 MHz — between the two signatures,
17.5 above one and 11.4 below the other. **Ambiguous, and the signature table in `CLAUDE.md` implies
more resolution than it has.**

**Power at a matched locked frequency separates them by 27%.** At 2010 MHz on `gemm`:

| target | P4 achieved | P5 achieved | P4 power | P5 power | difference |
|---|---|---|---|---|---|
| 1852 MHz | 1847.8 | 1845.0 | 74.56 W | 93.36 W | **−20.1%** |
| **2010 MHz** | 2002.0 | 2002.0 | **79.54 W** | **108.80 W** | **−26.9%** |
| 2167 MHz | 2160.0 | 2160.0 | 94.07 W | 118.29 W | −20.5% |

Mean **−11.4%** across 1237–2010 MHz. This is a direct consequence of `P = C·V²·f`: at a matched
clock the two curves sit at different voltages, and the square makes that difference large and
unmissable. It is also how **Profile 4 was confirmed to be the full tune** — the figures reproduce
the "−18% to −26% power at matched clock" that `CLAUDE.md` records for that configuration on `gemm`.

**Use this as the per-run fingerprint.** `tools/frequency-sweep` locks a clock and reports mean
power, so a single locked point at 2010 MHz identifies which family is live in about a minute.

---

## The file format

INI text. Each `[ProfileN]` section carries `PowerLimit` (percent), `CoreClkBoost` and `MemClkBoost`
(both in kHz, so `2500000` is +2500 MHz), and `VFCurve` as a hex blob.

The blob is **3224 bytes: an 8-byte header (`000002007f000000`) followed by 268 float32 triples**, of
which the first 127 are real curve points and the remainder are zero padding. Each triple is
**(offset, voltage_mV, base_clock_MHz)** and the applied clock is `base + offset`. Voltages run
450–1240 mV.

### How the plateau is encoded, and the one record that decodes impossibly

⚠️ **Filter to the card's supported range (≤3090 MHz, the top of its supported-clock table) rather
than trusting every decoded triple.** That instruction has always been right. ⛔ **The explanation
that stood here until 2026-09-11 was not, and is struck:** it said "a naive stride-3 read mispairs at
one record — the boundary between the zero-offset and non-zero-offset regions — and renders a
nonsensical ~6000 MHz point around 937 mV."

**What the store actually does.** The flat top is written as a block of identical records — a
constant base plus a constant offset that sum to the plateau clock. Three of the four tuned profiles
use a **sentinel**: a deliberately out-of-range base with a large negative offset correcting it.

| profile | plateau encoding | block | applied |
|---|---|---|---|
| Profile 1 | sentinel base 5462 MHz, offset −2500 | 50 points, 935–1240 mV | 2962 |
| Profile 4 | sentinel base 5530 MHz, offset −2500 | 50 points, 935–1240 mV | **3030** |
| Profile 5 | sentinel base 5453 MHz, offset −2423 | 50 points, 935–1240 mV | **3030** |
| **Profile 2** | **real base 3022 MHz, offset 0** from 935 mV… | 226 points, 935–1160 mV | 3022 |
| Profile 2 | …then sentinel base 5608 MHz, offset −2586 | 13 points, 1165–1240 mV | 3022 |
| **Profile 3 (stock)** | **no plateau at all** — every offset 0 | — | base only, to 3135 |

⚠️ **Profile 2 is why "the plateau is a sentinel" is not a format-wide rule.** It writes its flat top
as a genuine repeated base for 226 records and only switches to a sentinel for its last 13. Whatever
the sentinel is for, it is not *how a plateau is stored*.

### The one impossible record, and the identity it obeys

**Exactly one record per tuned profile decodes above the ceiling, and it is always at 935 mV.** It
obeys an exact arithmetic identity, in all four:

    offset(935 mV)  ==  plateau_clock  −  base(925 mV)

| profile | plateau | base at 925 mV | difference | stored offset at 935 mV |
|---|---|---|---|---|
| Profile 1 | 2962 | 2456 | **+506** | **+506** |
| Profile 2 | 3022 | 2455 | **+567** | **+567** |
| Profile 4 | 3030 | 2454 | **+576** | **+576** |
| Profile 5 | 3030 | 2458 | **+572** | **+572** |

🔑 **That is the offset which would carry the PREVIOUS record's base to the plateau.** The offset
field lags the base field by one record at that boundary — and such a lag is **invisible everywhere
else**, because shifting the offsets inside a constant-offset block changes nothing. That is exactly
why the defect surfaces at one record and only at one record.

⛔ **So this IS a pairing problem, and the section's ORIGINAL wording was right in kind.** What it
got wrong was the place: it named "the boundary between the zero-offset and non-zero-offset
regions", and Profile 1 and Profile 4 have no zero-offset point anywhere above **695 mV** while
Profile 5's ends at **850 mV** — yet all three put the artifact at 935.

⛔ **And the replacement written hours later on 2026-09-11 was wrong too, which is the part worth
keeping.** It said the record "still carries the offset from the region below". That is **false for
Profile 1, Profile 2 and Profile 4** — +506, +567 and +576 against preceding offsets of +478, 0 and
+478. It was generalised from Profile 5, the single profile where the value happens to coincide
(+572 is also its high-voltage block offset). 🔑 **A correction drawn from one example replaced a
vague right answer with a specific wrong one, and looked more rigorous for it.** Check a regularity
on every profile before writing it down as the mechanism.

⚠️ **The filter therefore does two different jobs, and only one of them is removing an artifact.**
On a tuned profile it drops the single 935 mV record. On **stock it drops five entirely legitimate
points** — 1215–1240 mV at 3105–3135 MHz, where the factory curve genuinely runs past the 3090 MHz
lock-target ceiling. **This is why stock decodes to 122 points and not 127**, and the 122 quoted at
the top of this file is a post-filter count rather than what the profile contains.

**Curve-editor screenshots for all five slots are committed in `docs/figures/`**, with a README
explaining how to read the two traces. They are an independent visual check on this decode, not a
source of any number.

**How this was caught.** Screenshots of Afterburner's own Voltage/Frequency curve editor for
Profiles 4 and 5 were checked against the decode on 2026-09-11. The editor draws two traces — the
square handles are the applied curve and the thin line beneath is the base — and the thin line exits
the top of the chart near 930 mV in both, which is the sentinel base being plotted by Afterburner
itself. The numbers are pinned by 82 checks in `analysis/models/test_predict_from_curve.py`.

**The same screenshots confirm the mechanism result visually.** At the 0.720 V load floor Profile 5's
handles sit exactly on the base trace (per-point offset **+0**) while Profile 4's sit **+478 MHz**
above it, and the two base traces agree to within one clock bin. That is the manipulation arm of the
load-floor experiment — `abba-20260908` moved the optimum **+465 MHz** — readable off the profile
store with no benchmark run at all.

`MSIAfterburner.exe -profileN -q` applies profile N and exits. Verified working 2026-09-08; it was
used to apply Profile 5 and Profile 4 programmatically with the operator away from the machine, a
first for this project. No CLI flag resets to stock, and the `[Startup]` section — which holds empty
values, i.e. no settings — does not appear to be reachable from the command line. **Since 2026-09-09
that no longer matters: Profile 3 holds stock, so `-profile3 -q` is the stock control**. The
2026-09-09 application check is recorded above; verify the live limit and memory clock each time.

## A second control knob, independent of Afterburner: the NVML P0 clock offset

`nvmlDeviceSetClockOffsets` is available on this card with elevation — `CLAUDE.md` records the write
returning `NO_PERMISSION` rather than `NOT_SUPPORTED`. **Reading it back is confirmed working
2026-09-09** (range −1000 to +1000 MHz), and it reports **0 MHz while Profile 4 or Profile 5 is
live**, which establishes something the project did not know: **Afterburner writes its curve through
NVAPI curve points, so the NVML offset is a separate knob that stacks on top of a profile rather than
being the mechanism a profile uses.**

That matters because a global offset slides the whole V/F curve, and therefore slides **the frequency
at which the 0.720 V load floor ends** — the one quantity `voltage-curve-20260908` records as set by
the profile rather than by the experimenter. Negative offsets are the safe direction: they lower the
clock at every voltage, so holding a given clock takes *more* voltage, not less.

⚠️ **The write has not been exercised.** A read-back succeeds; no offset has ever been applied to
this card through NVML, and a validation pair — power at a locked *f* with a −300 offset should match
power at *f*+300 without one — was designed on 2026-09-09 and **not run**. Claim nothing about the
offset's effect until it has been.
