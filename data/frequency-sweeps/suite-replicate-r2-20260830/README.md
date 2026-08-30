# Suite replicate r2 — 2026-08-30

The second complete collection of the twelve-workload suite at stock. All twelve reached **13 of
13** planned frequencies, locks held, clocks reset. Collected in one sitting in 56 minutes by
`tools/frequency-sweep/Invoke-SuiteReplicate.ps1`.

r1 is `../stock-suite-20260829/` plus `../suite-pilot-20260829/`.

## Why

Everything the consumer half of the paper rests on was measured once. §5.5's table, §5.6.1.1's
fixed-versus-per-workload comparison and §5.6.2.1's constrained-model retest all read from twelve
curves collected a single time each, so none of them carried an interval.

**It also collapses a provenance split.** r1's "twelve-workload suite" is really eight plus four:
`copy`, `bgemm128`, `bgemm1024` and `conv` came from the pilot batch under looser conditions, and
`../stock-suite-20260829/README.md` forbids leaning on sub-percent differences between the two
batches. r2 has no such split.

## Configuration, verified rather than declared

| | |
|---|---|
| Card | Zotac RTX 5060 Ti Twin Edge OC, driver 610.88 |
| Configuration | **STOCK** — **13801 MHz memory measured under load** by the script's own preflight |
| Power limit | 180 W default |
| Precision | fp32, TF32 **off** |
| Baseline | encoder 0%, decoder 0%, GPU 4% |
| Grid | 13 points, `-MinFrequencyPercent 40`, targets 1237–3090 MHz |
| Iteration counts | `../../../tools/frequency-sweep/SUITE-ITERATIONS.md`, unchanged from r1 |

The configuration check is the memory clock **under load**, because `clocks.max.memory` reads
14001 MHz whether or not an Afterburner offset is applied and cannot distinguish the two. Earlier
the same day a run was labelled "memory untouched, verified 14001 stock" while a +2500 offset was
live. The script now measures it and refuses on a mismatch.

⚠️ **r2 was collected after a driver crash and a reboot** (see `../../stability-runs/`). That is a
genuine provenance difference from r1 and is stated rather than glossed. It runs in the honest
direction: agreement between r1 and r2 is evidence the reset left nothing behind.

## Result 1 — the optima wander, exactly as the dense grid predicted

| workload | r1 optimum | r2 optimum | moved |
|---|---|---|---|
| `copy` | 1537 | **1695** | +158 |
| `softmax` | 1537 | **1387** | −150 |
| `bgemm128` | 1695 | **1537** | −158 |
| the other nine | — | — | **0** |

Three of twelve moved, each by **exactly one grid step**. Nine did not move at all.

This independently reproduces `../dense-grid-20260829/`'s finding by a different route. That run
concluded the argmax positions were a resolution artifact — the efficiency curves are flat near
their peaks, so the reported optimum wanders with grid spacing. If that is true, it should also
wander **between repeats at the same spacing**, and it does. One-step movement in a quarter of the
workloads is what a flat peak looks like when sampled twice.

**Nothing here should be read as three workloads changing their preferred frequency.**

## Result 2 — the efficiency gains reproduce, with one exception

| workload | r1 gain | r2 gain | Δ |
|---|---|---|---|
| `copy` | 51.3% | 51.3% | +0.0 |
| `reduce` | 37.2% | 37.3% | +0.2 |
| `bgemm128` | 34.9% | 34.8% | −0.1 |
| `bgemm256` | 39.5% | 39.6% | +0.1 |
| `bgemm32` | 74.0% | 73.4% | −0.6 |
| `bgemm1024` | 61.0% | 60.3% | −0.7 |
| `gemm` | 55.6% | 54.8% | −0.8 |
| `softmax` | 61.5% | 63.6% | +2.1 |
| `attention` | 53.7% | 56.2% | +2.5 |
| `layernorm` | 51.0% | 53.8% | +2.9 |
| `conv` | 75.6% | 72.1% | −3.4 |
| **`bgemm64`** | **77.0%** | **70.0%** | **−7.0** |

Seven of twelve agree within ±1 point. The gains are 34–77%, so even the ±3 point cases leave the
headline effect untouched — a 51% efficiency gain measured as 54% is the same finding.

🔑 **`bgemm64` is not in that category.** A 7.0-point move is roughly nine times the ~0.76%
between-run spread this project has recorded for `gemm`, and it is the largest disagreement in the
table by a factor of two. It is **not explained** here. Until it is, `bgemm64`'s r1 figure should
not be quoted without this replicate beside it.

## What this does NOT establish

- **n = 2 gives a difference, not an interval.** Two measurements bound nothing. A third set is
  needed before any error bar is quoted, and it should be taken on a **different day**: the
  retraction in `../memonly-gemm-20260829/` established +1.47% cross-session drift on an identical
  configuration against −0.05% same-session, so same-sitting repeats measure the smaller of the
  two variance components and would give intervals that are too tight.
- **The performance-cost and power-saved columns were not compared here**, only the optimum and
  the gain.
- **The `bgemm64` disagreement is unexplained**, and it is the one result in this directory that
  should not be built on.

## What it caught

Recomputing r1's figures for this comparison found that the `attention` row of
`../stock-suite-20260829/README.md` disagreed with its own CSV — 55.6% written against 53.7%
computed. The other eleven rows agreed to within rounding, so it was a transcription error. It has
been corrected there with a note, and the whole column is now pinned by `5.5-suite-row-*` in
`analysis/claims_consumer.py`, so the same error fails the audit from here.

That error had stood since 2026-08-29 and was found by collecting a replicate, not by reading.
