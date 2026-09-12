# Suite pilot — RTX 5060 Ti at stock, 2026-08-29

⚠️ **This directory carries NO `dataset-grade: no` marker, and that is a live contradiction rather than an oversight.**
The prose below says these four sweeps are validation and not dataset-grade. The claims registry uses
them anyway: `REPLICATES_5060[0]` in `analysis/claims_consumer.py` is this run, and roughly eight
live claims average over all six stock replicates including it. Adding the marker would change the
published sweep count and several pinned numbers at once. **Resolve deliberately** - either the
prose below is too strong, or those claims should move to `REPLICATES_5060[1:]`, which the drift
and optimum claims already do.

**VALIDATION, NOT DATASET-GRADE.** Read this before using any number here.

Four sweeps run to check that the extended workload suite works end to end in the sweep harness —
that the kernels run under a locked clock, that the units come out right, and that the throughputs
are physically possible. That is what these are for. They are **not** a designed collection and the
directory README convention requires saying so.

## Why they are not dataset-grade

- **n = 1 per workload.** No replicates, so nothing here has an error bar and no comparison between
  configurations is possible.
- **Iteration counts were calibrated at a 7% baseline**, above the protocol's ~5%, and on a
  different day from these sweeps. Counts are a setup constant so this is tolerable for a
  validation run and would not be for a collection.
- **Only four of the eleven suite workloads**, chosen to span the axis rather than to cover it.
- **The machine was being remote-controlled during the run.** Encoder and decoder were verified at
  0% across repeated samples and no NVENC-using remote tool was present, so the video-engine class
  of contamination is excluded — but it was not the undisturbed machine a collection wants.

## Conditions

| | |
|---|---|
| Card | RTX 5060 Ti 16 GB, driver 610.88 |
| Configuration | **STOCK** — verified at 13801 MHz memory under load, power limit 180 W default |
| Precision | fp32, TF32 **off** (the suite default since the conv finding) |
| Baseline | 4% GPU, encoder 0%, decoder 0%, Wallpaper Engine closed, no llama-server or ollama |
| Grid | 13 points, `-MinFrequencyPercent 40`, defaults otherwise |

Clocks reset cleanly after all four sweeps. Every sweep completed 13/13 points with locks held
within ~7 MHz and utilisation 96–99%.

## What it showed

All four ran, produced sane units, and landed inside the card's physical limits. Nothing exceeded
the memory bus or the fp32 ceiling.

| workload | declared FLOP/byte | peak | efficiency optimum | efficiency gain | performance cost | power saved |
|---|---|---|---|---|---|---|
| `copy` | 0 | 354.29 GB/s | 1537 MHz | 51.3% | **9.2%** | 40.0% |
| `bgemm128` | 21.3 | 7.69 TFLOP/s | 1695 MHz | 34.9% | 31.3% | 49.1% |
| `bgemm1024` | 170.7 | 9.20 TFLOP/s | 1537 MHz | 61.0% | 44.0% | 65.2% |
| `conv` | 288 | 5.75 TFLOP/s | 1537 MHz | 75.6% | **44.9%** | 68.6% |

**The performance cost of the unconstrained optimum ranges from 9.2% to 44.9% across the axis.**
That is §5.6.1's mechanism — a fixed policy is pinned by the most frequency-sensitive workload it
might meet — appearing on consumer hardware rather than on the V100. It is the reason the suite was
built, and it is the first sign the design does what it was meant to.

⚠️ **Do not quote any of it.** n = 1, and see the caveats above.

## Two things to check before a real collection

1. **Three of four optima land on the same grid point, 1537 MHz.** That is either genuinely flat
   curves near the optimum — which is what the V100 showed and would be a finding — or 13 points
   across 40–100% being too coarse to separate them. A denser grid around 1400–1800 MHz would tell
   the two apart, and the answer changes how much §5.6.1's argument can lean on this data.
2. **`bgemm128` is the odd one out** at 1695 MHz with the smallest gain and it is also the workload
   the earlier characterisation put closest to the roofline knee. Whether that is real or noise
   needs the replicate this run does not have.
