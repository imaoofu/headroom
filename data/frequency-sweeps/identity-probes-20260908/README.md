# `identity-probes-20260908` — determining which configuration Afterburner Profile 4 holds

<!-- dataset-grade: no -->

⛔ **NOT DATASET-GRADE. Do not pool these with any suite or replicate.** They exist to answer a
single yes/no question about the machine's state, not to measure the card.

Two `gemm` sweeps, 2026-09-08, RTX 5060 Ti on **Afterburner Profile 4**, applied programmatically.

---

## Why they exist

The ABBA dose-response run needed to know which configuration Profile 4 actually holds. The
repository names configurations by their `gemm` peak achieved clock — stock ~2593, memory-only
~2584, curve-fixed ~2887–2899, full tune ~2948, split ~2977 — so the obvious probe is to apply the
profile and read the top of the grid.

## 🔑 The first probe was AMBIGUOUS, and that is the finding

`5060ti-p4-identity-probe` — 3 points, 90–100% of the grid — peaked at **2965.6 MHz**. That sits
**between** the full tune (~2948) and the split curve (~2977): 17.5 MHz above one, 11.4 below the
other.

⚠️ **The signature table implies more resolution than it has.** Two of the configurations it lists
are ~29 MHz apart at the top of the grid, which is comparable to thermal and run-to-run variation on
this card. Identifying a configuration from its peak clock alone is not reliable, and any past or
future claim that does so should be treated with suspicion.

## What worked: power at matched locked frequency

`5060ti-p4-identity-full` — the full 13-point 1237–3090 grid — compared point-for-point against the
`splitcurve-suite-s2-20260908` `gemm` sweep, which is a known split curve:

| target | P4 achieved | P5 achieved | P4 power | P5 power | difference |
|---|---|---|---|---|---|
| 1852 MHz | 1847.8 | 1845.0 | 74.56 W | 93.36 W | **−20.1%** |
| **2010 MHz** | 2002.0 | 2002.0 | **79.54 W** | **108.80 W** | **−26.9%** |
| 2167 MHz | 2160.0 | 2160.0 | 94.07 W | 118.29 W | −20.5% |

Mean **−11.4%** across 1237–2010 MHz, at achieved clocks matching to within 3 MHz.

**This identifies Profile 4 as the full tune**, because it reproduces the "−18% to −26% power at
matched clock" that `CLAUDE.md` records for that configuration on `gemm`. The mechanism is
`P = C·V²·f`: at a matched clock the two curves sit at different voltages, and the square makes the
difference large. Clock cannot separate them; power separates them by 27%.

This probe is also the origin of the **power fingerprint** now used to verify every leg of the ABBA
run — a single locked point at 2010 MHz, about a minute, refusing the leg if the wrong family is
live. See `docs/AFTERBURNER-PROFILES.md`.

## Why not dataset-grade

- The 3-point probe uses a 90% floor, not the standard 40%, so it shares no grid with anything.
- The 13-point sweep is on the standard grid and is internally sound, but it was collected as a
  diagnostic between other work, with no replicate and no cooldown protocol. It is a **reference for
  the power fingerprint**, not a measurement of Profile 4's efficiency — the ABBA legs `a1` and `a2`
  are that.
- Both ran while the operator was away and the display asleep, so their baselines are not comparable
  to the attended replicates.

Anything needing Profile 4 numbers should read `a1` and `a2` instead.
