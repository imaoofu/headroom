# membw plateau, clean re-run — 2026-08-19 20:42

One focused `membw` sweep to test whether the 1545–1852 MHz plateau seen in
`../oc-comparison-20260819/` was an artifact of the stability logger that ran concurrently
during that session's tuned sweep.

**It was not.** The plateau reproduced with nothing else touching the GPU.

## Conditions

- Same RTX 5060 Ti, same tuned profile (memory +2500, core V/F curve pinned flat near
  3000 MHz at and above ~925 mV, power limit 111%) — see `../oc-comparison-20260819/`.
- **No stability logger, no local LLM resident, no other GPU work.** The 18 GB
  `qwen3-coder:30b` model was explicitly unloaded first; it had 15.6 GB of the card's 16 GB
  held, which is what wedged an earlier attempt at preflight.
- 1400–2100 MHz, 10 points, 8 s settle, 20 s measure. `bench_ok` true and `lock_held` true at
  every point.

## The result

| target | achieved SM | memory clock | GB/s | power | temp |
|---|---|---|---|---|---|
| 1402 | 1400.3 | 16301 | 283.8 | 51.0 | 42.5 |
| 1477 | 1475.3 | 16301 | 283.6 | 52.8 | 43.6 |
| 1560 | 1555.0 | 16301 | **294.1** | 53.6 | 44.5 |
| 1635 | 1627.3 | 16301 | **296.6** | 54.6 | 45.5 |
| 1710 | 1702.7 | 16301 | **297.8** | 54.8 | 46.2 |
| 1792 | 1785.0 | 16301 | **297.6** | 55.4 | 47.0 |
| 1867 | 1860.0 | 16301 | **297.5** | 56.0 | 47.8 |
| 1942 | 1935.0 | 16301 | 310.7 | 55.6 | 48.3 |
| 2025 | 2017.0 | 16301 | 326.7 | 58.2 | 49.1 |
| 2100 | 2092.0 | 16301 | 342.0 | 62.0 | 50.0 |

Five consecutive points from 1560 to 1867 MHz sit inside a 3.7 GB/s band — 1.2% spread across
a 307 MHz range — while the core clock rises 20%. Above and below it, throughput moves
normally.

## What this run added to the tool

The sweep script recorded `clocks.current.sm` and never the memory clock. For a
bandwidth-bound workload that is the wrong clock, so the original data could not test the most
obvious hypothesis. `clocks.current.memory` is now sampled and written as
`memory_clock_avg_mhz` / `_min_` / `_max_`.

The answer is unambiguous: **16301 MHz at every point, with min equal to max equal to avg.**
There is no memory downclock. The hypothesis is dead.

## What is eliminated

- **The logger confound** — reproduced within 1% without it.
- **Memory downclocking** — flat 16301, zero variance.
- **Throttling** — throttle masks decoded across all three runs show no power cap, no thermal
  slowdown, no hardware slowdown. The `GpuIdle` bit appears at every frequency including those
  performing at +17.6%, so it marks a sample between iterations, not a stall.
- **Heat** — 44–48 °C in the band.

## What is not

A mechanism. See the leading untested hypothesis in `../oc-comparison-20260819/README.md`:
the flattened V/F curve forces a voltage selection below its flattened region at exactly these
locked clocks, and the plateau may belong to the curve rather than to bandwidth. Testing that
needs one more sweep with the **memory overclock only** and the core curve at stock.

## Caveat

This is a tuned-versus-tuned reproduction. No fresh stock sweep was run alongside it, so the
size of the gap against stock still rests on the original same-session pair in
`../oc-comparison-20260819/`, measured about six hours earlier.
