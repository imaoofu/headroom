# Figures

Screenshots of **MSI Afterburner's own Voltage/Frequency curve editor** on the Zotac RTX 5060 Ti
Twin Edge OC, captured 2026-09-11, one per profile slot.

⚠️ **These are photographs of a third-party GUI, not measurements.** Nothing is derived from them —
every number in the repository comes from the decoded profile store
(`data/afterburner-profiles/`) or from a sweep CSV. Their value is as an **independent visual check
on the decoder** and as a figure a reader can understand in one glance.

## Reading them

The editor draws **two traces**:

| trace | what it is | decoded field |
|---|---|---|
| square handles | the **applied** curve — what the card runs | `applied_mhz` |
| thin line beneath | the **base** curve — the factory V/F curve | `base_mhz` |

The vertical gap between them is the per-point offset. Where a profile applies no offset the two
traces **coincide**, which is why stock, P2 and the low-voltage half of P5 show only one line.

## The five slots

| file | slot | offset at the 0.720 V load floor | floor extent | plateau | mem | PL |
|---|---|---|---|---|---|---|
| `5060ti-vfcurve-p3-stock.png` | P3 **stock** | +0 | **1530** | none — climbs to 3135 | +0 | 100% |
| `5060ti-vfcurve-p1-mild-tune.png` | P1 | **+478** | **1972** | 2962 | +2000 | **100%** |
| `5060ti-vfcurve-p2-repair.png` | P2 repair | +0 | **1530** | 3022 | +2500 | 111% |
| `5060ti-vfcurve-p4-fulltune.png` | P4 full tune | **+478** | **2002** | 3030 | +2500 | 111% |
| `5060ti-vfcurve-p5-split.png` | P5 split | +0 | **1530** | 3030 | +2500 | 111% |

🔑 **P4 against P5 is the mechanism result as a picture.** Both plateau at 3030 and both are
aggressive above ~850 mV. The only difference in the region that decides the optimum is that **P5's
handles sit exactly on the base trace at the load floor while P4's sit 478 MHz above it** — and
`abba-20260908` measured the optimum move **+465 MHz in 12 of 12 workloads** between them. The
efficiency optimum is set by a part of the curve most tuning guides never mention.

✅ **P3 (stock) is the control and also settles a decoding question.** It has no plateau at all: the
factory curve climbs smoothly past 3000 MHz and reaches **3135 MHz at 1240 mV**, above the card's
3090 MHz lock-target ceiling. So the five points stock loses to the `≤3090` read filter are
**real**, not artifacts — which is what makes stock decode to 122 points rather than 127.

⚠️ **P1 is not the memory-only profile it is easy to mistake it for.** It carries the **same +478
floor offset as P4**, so it is a second high-floor configuration; it differs from P4 in power limit
(100% / 180 W against 111% / 200 W), memory (+2000 against +2500) and plateau (2962 against 3030).
**It has never been swept** — see `docs/AFTERBURNER-PROFILES.md` for why that makes it the cheapest
available control on whether power limit moves the optimum.

## The sentinel, visible

In P1, P4 and P5 the thin base trace **exits the top of the chart near 930 mV**. That is not a
rendering fault: the store writes the flat top as a constant out-of-range base (5462 / 5530 / 5453
MHz) plus a constant large negative offset, and Afterburner plots the base it was given. P2 does the
same thing 230 mV higher — its faint vertical line sits at **1165 mV**. Stock, which has no plateau,
has no such line anywhere.

Full decode and the arithmetic identity behind the one impossible record: `docs/AFTERBURNER-PROFILES.md`.

## Provenance

Captured from Afterburner 4.6.6 on 2026-09-11 by the repository owner, on the machine described in
`CLAUDE.md`. Originals are unmodified PNGs — no cropping, annotation or rescaling — so they can be
re-read against the profile store at any time. The profile store they correspond to is
`data/afterburner-profiles/5060ti-profiles-20260908b-p4-plateau-3030.json`.
