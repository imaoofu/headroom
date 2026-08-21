# Separating the two tuning knobs — 2026-08-19 / 2026-08-20

> **Folder name is narrower than its contents.** It began as a `membw` investigation and now
> also holds the `gemm` separation run. Kept as-is so existing links stay valid.

The tuned profile changes two independent things: a **memory overclock** (+2500) and a **core
V/F curve** pinned flat near 3000 MHz above ~925 mV. Every earlier result treated them as one
setting. These runs separate them, and the two knobs turn out to do opposite things to the two
workloads.

| | memory overclock | core V/F curve |
|---|---|---|
| `gemm` (compute-bound) | nothing, ±1% | **the whole win**: −18% to −26% power at matched clock, +12% clock ceiling |
| `membw` (bandwidth-bound) | **the whole win**: +3.6% to +16.1% over stock | **actively harmful**: up to −29.6% throughput in the 1560–1867 MHz band |

Neither knob is good for both. That is the result.

---

# Part 1 — The membw plateau: reproduced, then explained

Two focused `membw` sweeps over the same band on the same card, to find out what caused the
1545–1852 MHz plateau recorded in `../oc-comparison-20260819/`.

**These two runs are 21.5 hours apart, not the same session.** Run 1 was 2026-08-19 20:42; run 2
was 2026-08-20 18:13. The gap is unavoidable — it takes a manual Afterburner change to switch
configurations — but it means ambient temperature, driver state and background load were not
held constant between them. See the caveats.

**Answer: the core V/F curve, not the memory overclock.** Reverting the core curve to stock
while keeping memory at +2500 removes the plateau entirely.

## Conditions common to both runs

- RTX 5060 Ti, 1400–2100 MHz, 10 points, 8 s settle, 20 s measure. Identical tool, identical
  targets, identical workload invocation.
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

---

# Part 2 — gemm: the power finding survives, and belongs to the curve

`../oc-comparison-20260819/` reports that the tuned profile draws **18–26% less power than
stock at identical core clock** on `gemm`, and attributes the efficiency gain to that rather
than to the higher peak clock. That was measured with both knobs applied at once and had never
been separated.

Run 3 (`*-memonly-gemm`, 2026-08-20 18:32) uses the **full default 13-point grid**, the exact
target list both existing `gemm` sweeps used, so all three configurations compare at identical
targets rather than nearest neighbours.

## The matched-frequency comparison, re-tested

| MHz | tuned vs stock: thru / power / effic | mem-only vs stock: thru / power / effic |
|---|---|---|
| 1852 | −2.0% / **−18.1%** / +19.8% | +0.3% / **−0.6%** / +1.0% |
| 2010 | −2.3% / **−26.4%** / +32.7% | −0.7% / **−2.9%** / +2.2% |
| 2167 | +0.8% / **−19.9%** / +25.8% | −0.6% / **+0.9%** / −1.5% |
| 2317 | −1.2% / **−18.1%** / +20.7% | +0.0% / **−2.5%** / +2.6% |

**Memory-only reproduces stock power to within ±3%. The full tuned profile cuts it by 18–26%.**
The power reduction is therefore entirely the core V/F curve. The original finding survives
intact and its attribution was correct — the curve really is functioning as an undervolt.

Temperatures at these four points matched to within 0.6 °C between the mem-only and stock runs,
so this is not thermal.

Memory overclocking does nothing measurable for `gemm`, which is what a compute-bound workload
should do when only memory speed changes. That is a sanity check the experiment passes.

## The curve also raises the ceiling

At stock and at memory-only, `gemm` cannot hold the top three grid points — all of 2782, 2932
and 3090 MHz collapse to ~2590 MHz achieved and ~15.7 TFLOP/s. With the curve applied the card
holds 2775 / 2916 / 2948 MHz and reaches **17.61 TFLOP/s, +12.3%**.

So for `gemm` the curve is a pure win on both axes: less power at matched clock, and a higher
clock it can actually sustain.

## Why this matters beyond one card

The project's central claim is that the efficiency-optimal *frequency* is workload-dependent.
This is the same claim one level up: the efficiency-optimal *hardware configuration* is
workload-dependent too, and by a large margin. A single "tuned" profile chosen on `gemm` costs
a bandwidth-bound workload up to 29.6% of its throughput; a profile chosen on `membw` gives up
a 18–26% power reduction on compute-bound work.

## Caveats

- **The `memory_clock_min_mhz` column reads 7001 at four points in run 2** (1560, 1635, 1710,
  1867) against an average near 15850. That is the idle memory P-state caught by a telemetry
  sample landing between benchmark iterations — the same class of artifact as the `GpuIdle`
  throttle bit, which also appears at frequencies performing perfectly well. The evidence that
  it is an artifact and not a real mid-work downclock: the four points with clean
  `min = max = 16301` (1792, 1942, 2025, 2100) sit exactly on the same smooth trend as the four
  with 7001 minima. A genuine downclock during timed work would show as a throughput dip, and
  there is none.
- **Neither leg is contemporaneous, and this is the weakest point of the study.** Run 1 was
  2026-08-19 20:42, run 2 was 2026-08-20 18:13, and the stock leg was 2026-08-19 14:33. All
  three are separated by hours to a full day. Idle temperature was 40–42 °C at the start of
  each, which is the only cross-run control available, and no driver or system change is known
  to have occurred — but "not known to have occurred" is not the same as verified. The size of
  the effect (up to +29.6%) is far outside any plausible day-to-day drift, so the direction of
  the result is safe; the precise percentages are not. Proper interleaving would need the
  profile switched between every point, which Afterburner cannot be scripted to do here.
- **The gemm run has its own timing gap.** It ran 2026-08-20 18:32 against a stock leg from
  2026-08-19 14:28. Temperatures at the four matched-frequency comparison points agree to within
  0.6 °C, which is the relevant control, but the runs are a day apart.
- **Two gemm points outside the comparison band disagree by ~6%.** At 2475 and 2625 MHz the
  mem-only run drew 5.8% and 6.6% more power than stock, with only +1.2 and +2.1 °C to explain
  it. Neither point is part of the matched-frequency finding, but the gap is unexplained and is
  recorded rather than trimmed.
- **At the low end the mem-only gemm run started 4–6 °C warmer** than the stock run (46 °C
  against 41 °C at 1237 MHz), which accounts for its 1.4–3.6% higher power there. The four
  comparison points are unaffected.
- **n = 1 chip**, and one profile. Nothing here generalises to other cards or other curves.
- **Sequential, not interleaved.** Temperature rose 42 → 52 °C within each run. The drift is
  similar in both so it does not obviously bias the comparison, but it is not controlled.
