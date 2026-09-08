# The five Afterburner profiles on the 5060 Ti — decoded from disk

**Decoded 2026-09-08 from `Profiles\VEN_10DE&DEV_2D04&SUBSYS_177219DA&REV_A1&BUS_1&DEV_0&FN_0.cfg`.**

This file exists because **a profile identified by slot number is not identified.** On 2026-08-30 a
run was labelled "memory untouched — verified 14001 MHz stock" while a +2500 offset was live, and
the fix at the time was to probe the memory clock under load. That catches stock-versus-tuned. It
does **not** catch tuned-versus-a-different-tune, because four of these five profiles carry the same
+2500 memory offset. This table is the part that does.

⚠️ **None of these is stock.** Every slot carries a memory offset and 127 non-zero V/F curve points.
There is no stock profile to apply, which is why a configuration change to stock cannot currently be
made programmatically — it needs the offsets cleared by hand, or a stock profile written.

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
| **P3** | 100 | +2500 | 1897 | 2317 | 2752 | 2932 | 3015 | 940 mV |
| **P4** | 111 | +2500 | **1912** | 2317 | 2752 | 2932 | 3015 | 940 mV |
| **P5** | 111 | +2500 | 1447 | 1852 | **2850** | **3030** | 3030 | **925 mV** |

PL 100 = 180 W, PL 111 = 200 W. "Knee" is the lowest voltage at which the curve reaches within 0.5%
of its own plateau.

## Three curve shapes, not five

- **P1 / P3 / P4 — the aggressive-low-end family.** ~1900 MHz at 700 mV. These pin voltage low across
  a wide frequency range, which is the mechanism behind both the `gemm` power advantage and the
  `membw` crossbar plateau. **P1 is the outlier of the three: +2000 memory and PL 100**, so it is an
  earlier, milder attempt. **P3 and P4 differ only in power limit** — same curve, 180 W versus 200 W.
- **P2 — the repaired shape.** Gentle low end (1447 at 700 mV) *and* a low mid-band (2280 at 875 mV).
  This is the curve-fixed / repair geometry: stock voltage slope restored across the whole lower
  range.
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

⚠️ **A naive stride-3 read mispairs at one record** — the boundary between the zero-offset and
non-zero-offset regions — and renders a nonsensical ~6000 MHz point around 937 mV. Filter to the
card's supported range (≤3090 MHz, the top of its supported-clock table) rather than trusting every
decoded triple.

`MSIAfterburner.exe -profileN -q` applies profile N and exits. Verified working 2026-09-08; it was
used to apply Profile 5 and Profile 4 programmatically with the operator away from the machine, a
first for this project. **No CLI flag to reset to stock was found**, and the `[Startup]` section —
which holds empty values, i.e. no settings — does not appear to be reachable from the command line.
