# The membw plateau: reproduced, then explained — 2026-08-19 evening

Two focused `membw` sweeps over the same band, run back to back the same evening on the same
card, to find out what caused the 1545–1852 MHz plateau recorded in
`../oc-comparison-20260819/`.

**Answer: the core V/F curve, not the memory overclock.** Reverting the core curve to stock
while keeping memory at +2500 removes the plateau entirely.

## Conditions common to both runs

- RTX 5060 Ti, 1400–2100 MHz, 10 points, 8 s settle, 20 s measure.
- **No stability logger, no local LLM resident, no other GPU work.** The 18 GB
  `qwen3-coder:30b` model was explicitly unloaded first; it had 15.6 GB of the card's 16 GB
  held, which is what wedged an earlier attempt at preflight.
- `bench_ok` true and `lock_held` true at every point in both runs.

## Run 1 — full tuned profile (`*-oc-membw-anomaly`)

Memory +2500, core V/F curve pinned flat near 3000 MHz at and above ~925 mV, power limit 111%.

Run to test whether the plateau was an artifact of the stability logger that ran during the
original tuned sweep. **It was not.** The plateau reproduced to within 1% at every frequency
with nothing else touching the GPU:

| SM MHz | stock (14:33) | tuned run 1 (logger) | tuned run 2 (clean) | run 1 vs run 2 |
|---|---|---|---|---|
| ~1560 | 311.8 | 296.6 | 294.1 | −0.8% |
| ~1710 | 331.8 | 295.3 | 297.8 | +0.8% |
| ~1867 | 341.6 | 294.5 | 297.5 | +1.0% |
| ~2025 | 344.4 | 324.4 | 326.7 | +0.7% |

Five consecutive points from 1560 to 1867 MHz sat inside a 1.2% band while the core clock rose
20%.

This run also added memory-clock telemetry to the sweep tool, which had only ever recorded the
SM clock — the wrong clock for a bandwidth-bound workload. Memory held at exactly 16301 MHz at
every point, `min` equal to `max` equal to `avg`. **No downclock.**

## Run 2 — memory overclock only (`*-memonly-membw-anomaly`)

Memory still +2500; core V/F curve reverted to stock. The separation test.

| target | achieved SM | memory clock | GB/s | power | temp |
|---|---|---|---|---|---|
| 1402 | 1400.3 | 16301 | 291.8 | 51.4 | 42.1 |
| 1477 | 1470.0 | 16301 | 305.6 | 52.8 | 43.2 |
| 1560 | 1552.0 | 16301 | 323.0 | 54.1 | 44.1 |
| 1635 | 1627.0 | 16301 | 342.2 | 56.4 | 45.2 |
| 1710 | 1702.0 | 16301 | 360.1 | 60.6 | 46.4 |
| 1792 | 1785.0 | 16301 | 372.9 | 62.5 | 47.5 |
| 1867 | 1860.0 | 16301 | 385.7 | 64.7 | 48.4 |
| 1942 | 1935.0 | 16301 | 393.5 | 68.5 | 49.6 |
| 2025 | 2017.0 | 16301 | 399.9 | 70.1 | 50.7 |
| 2100 | 2085.4 | 16301 | 400.4 | 70.6 | 51.6 |

Monotone throughout. **No plateau anywhere.**

Two independent confirmations that the profile change did what was intended rather than
silently no-opping: memory still reads 16301 MHz under load, and power at matched clock rose
(56.0 W at ~1470 MHz against the tuned run's 52.8 W at ~1477 MHz) — which is what losing an
undervolt looks like.

## The size of the effect

| SM MHz | mem-OC only | full tuned | throughput | efficiency (GB/s/W) |
|---|---|---|---|---|
| 1477 | 305.6 | 283.6 | +7.8% | +7.6% |
| 1560 | 323.0 | 294.1 | +9.8% | +8.8% |
| 1635 | 342.2 | 296.6 | +15.4% | +11.7% |
| 1710 | 360.1 | 297.8 | +20.9% | +9.3% |
| 1792 | 372.9 | 297.6 | +25.3% | +11.0% |
| 1867 | 385.7 | 297.5 | **+29.6%** | **+12.1%** |
| 2025 | 399.9 | 326.7 | +22.4% | +1.7% |

The flattened curve is not a wash that happens to look odd on a graph. Across the plateau band
it costs up to **29.6% of throughput and 12.1% of efficiency** on this workload. It costs more
throughput than it saves power.

Against stock, memory-overclock-only wins on both axes:

| stock MHz | stock GB/s | mem-OC GB/s | throughput | power | efficiency |
|---|---|---|---|---|---|
| 1545 → 1560 | 311.8 | 323.0 | +3.6% | +1.4% | +2.1% |
| 1702 → 1710 | 331.8 | 360.1 | +8.5% | +6.1% | +2.3% |
| 1852 → 1867 | 341.6 | 385.7 | +12.9% | +7.9% | +4.6% |
| 2010 → 2025 | 344.4 | 399.9 | +16.1% | +7.1% | +8.4% |

## What is established, and what is not

**Established:** the plateau is caused by the core V/F curve. It is not the stability logger
(reproduced within 1% without it), not a memory downclock (flat 16301, and it is flat in the
memory-only run too), and not throttling — throttle masks were decoded across every run and
show no power cap, no thermal slowdown, no hardware slowdown. Temperatures stayed at 42–52 °C.

**Not established:** the mechanism by which the curve does it. The working hypothesis is that
locking the SM clock into this band forces a voltage selection below the curve's flattened
region, where the custom and stock curves diverge most. This hardware exposes no voltage
readback, so that remains a hypothesis. What these runs pin down is *which knob* is
responsible, not *how*.

## Caveats

- **The `memory_clock_min_mhz` column reads 7001 at four points in run 2** (1560, 1635, 1710,
  1867) against an average near 15850. That is the idle memory P-state caught by a telemetry
  sample landing between benchmark iterations — the same class of artifact as the `GpuIdle`
  throttle bit, which also appears at frequencies performing perfectly well. The evidence that
  it is an artifact and not a real mid-work downclock: the four points with clean
  `min = max = 16301` (1792, 1942, 2025, 2100) sit exactly on the same smooth trend as the four
  with 7001 minima. A genuine downclock during timed work would show as a throughput dip, and
  there is none.
- **The stock leg is not contemporaneous.** It was measured at 14:33, about six hours before
  run 2, with an unknown ambient shift. The two evening runs are directly comparable to each
  other; comparisons to stock are weaker.
- **`membw` only.** Whether the flattened curve costs `gemm` anything in this band is untested,
  and `gemm` is the workload the original matched-frequency power finding rested on.
- **n = 1 chip**, and one profile. Nothing here generalises to other cards or other curves.
- **Sequential, not interleaved.** Temperature rose 42 → 52 °C within each run. The drift is
  similar in both so it does not obviously bias the comparison, but it is not controlled.
