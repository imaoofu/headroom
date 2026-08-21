# Is `membw` actually bandwidth-bound? — 2026-08-20

`ROADMAP.md` asks for "a genuinely bandwidth-saturated kernel" because `membw` is issue-limited
over most of the swept range, which means the V100 frequency-prediction result was tested
outside the domain where its premise holds. Three probes were run to find out whether such a
kernel is constructible on this card.

## Probe 1 — six access patterns at two locked clocks

`tools/frequency-sweep/probe_saturating_kernel.py`. Elasticity is
`ln(T_high/T_low) / ln(f_high/f_low)`: 1.0 means throughput scales with core clock (purely
issue-limited), 0.0 means independent of it (purely DRAM-limited).

| kernel | @1395 MHz | @2760 MHz | elasticity |
|---|---|---|---|
| `copy` | 299.9 | 408.0 | 0.451 |
| `copy_wide` (fp64 view) | 296.8 | 408.5 | 0.468 |
| `scale` | 291.3 | 405.4 | 0.485 |
| `inplace_add` | 282.6 | 406.0 | 0.531 |
| `triad_current` (**today's membw**) | 287.2 | 416.6 | 0.545 |
| `read_only_sum` | 230.5 | 443.0 | 0.957 |

**Not one is DRAM-limited.** Two expectations were wrong and both are informative:

- **`read_only_sum` was the WORST**, not the best. A reduction carries dependency chains and
  performs one add per 4 bytes, so per byte moved it is more issue-hungry than the triad, not
  less. It does reach the highest absolute throughput at boost (443 GB/s) precisely because it
  moves the fewest bytes per element.
- **`copy_wide` gave no benefit at all** (296.8 against 299.9). Viewing fp32 storage as fp64
  halves the element count without changing bytes moved, which should double the payload per
  thread. It changed nothing, which means torch's copy kernel was *already* emitting vectorised
  accesses. Hand-vectorisation is not the missing ingredient.

## Probe 2 — does concurrency help? (at boost: uninformative)

Eight concurrent copies on eight streams at free boost: 406.2 / 404.0 / 407.7 / 405.5 GB/s for
1 / 2 / 4 / 8 streams. Flat.

**This probe was badly designed and is recorded as a lesson rather than a result.** At boost the
kernel is already near the achievable DRAM ceiling — roughly 406 GB/s against a ~521 GB/s
theoretical peak at this memory clock, about 78%, which is normal efficiency for GDDR under a
real access pattern. Concurrency cannot raise a workload that is already saturated. The test
only discriminates at a clock where the workload is known *not* to be saturated.

## Probe 3 — concurrency at a LOW locked clock (the deciding test)

`tools/frequency-sweep/probe_issue_ceiling.py`, locked to 1395 MHz:

| streams | aggregate GB/s | vs 1 stream |
|---|---|---|
| 1 | 218.3 | 1.00x |
| 2 | 276.5 | **1.27x** |
| 4 | 281.2 | **1.29x** |
| 8 | 279.7 | 1.28x |

**Concurrency buys 29%.** So at low clock the binding constraint is memory-level parallelism —
not enough requests in flight — and *not* the SM instruction issue rate. Issue rate is shared
hardware that no kernel could escape; MLP is something a better kernel can attack.

**But it plateaus immediately.** All the gain arrives by 2 streams and nothing after that helps.
The plateau sits at ~281 GB/s, still only about 54% of the ~521 GB/s available. So MLP is a real
lever and a limited one: a deeply unrolled kernel could plausibly move `membw` from ~218 toward
~280 GB/s at this clock, but there is a second ceiling well short of saturation that more
parallelism does not lift.

## Answer to the roadmap question

The roadmap asks whether the contradiction is "about consumer silicon or about this particular
kernel." The evidence says **mostly the silicon, partly the kernel**:

- Six different access patterns, including a pre-vectorised one and a read-only one, all land in
  the same issue/MLP-limited regime. That is not a property of one badly written kernel.
- Concurrency lifts low-clock bandwidth by only 29% and then stops, well short of saturation.
- **A fully DRAM-saturated workload at 1400 MHz appears not to be constructible on this part.**
  The crossover into genuine bandwidth-limited behaviour happens somewhere above 2000 MHz.

The practical consequence for the project is that a `membw` sweep below ~2000 MHz is not
measuring a memory-bound workload, whatever the kernel. That is a domain limitation to state in
the paper, not a bug to fix.

## Not established

- **No hand-tuned CUDA kernel was tested.** This machine has no `nvcc`, no CuPy and no Triton, so
  a custom kernel with deep unrolling could not be compiled. Everything above is torch-level
  access patterns. CuPy's `RawKernel` bundles NVRTC and would not need a separate CUDA toolkit;
  that is the cheapest path if this is worth pursuing.
- **The two probes disagree on single-stream `copy` at 1395 MHz: 299.9 GB/s in probe 1 against
  218.3 in probe 3.** They differ in array size (1 GiB against 256 MiB) and in how many arrays
  are resident (2 against 16). The 37% gap is not explained, and it means absolute numbers across
  probes are not comparable. The 1.29x concurrency ratio is measured *within* probe 3 and is
  unaffected, but the absolute figures should be treated as provisional until this is chased down.
- **n = 1 card**, one memory configuration (the +2500 memory overclock was applied throughout).
