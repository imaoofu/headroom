# Headroom — paper draft

> **Status: Related Work and Methods are drafted. Results are a skeleton — no original data has
> been collected yet.** Every number below that is not marked `[PENDING]` traces to something
> actually run or actually read. Placeholders are marked rather than filled with plausible values.
>
> Citation reliability is flagged per entry in [References](#references). Anything marked
> ⚠️ needs the primary source opened before it appears in a submitted version.

---

## 1. Introduction

Graphics processors ship with conservative default operating points. A vendor's default
voltage-frequency behaviour must hold across millions of individually varying dies, in unknown
thermal environments and unknown chassis, for a warranty period measured in years. That requirement
necessarily produces margin, and the margin is not small: Leng et al. [8] measured approximately a
20% voltage guardband on commercial GPUs, and showed that eliminating it entirely would yield up to
25% energy savings.

That result is a decade old, and it was obtained on cards — the GTX 480 and GTX 680 — released in
2010 and 2012. In the intervening period consumer GPU power management has changed considerably:
successive generations of automatic boost, finer-grained factory binning, and per-chip
characterisation now shipped as standard. Whether comparable margin remains, and where it sits, is
not established for current consumer parts.

Answering that question from published data turns out not to be possible, for a reason that is
itself worth reporting. Two public DVFS datasets covering consumer GPUs exist, and both sweep core
frequency only **at and above** the card's rated boost clock — 101–126% for a GTX 1080 Ti, 95–118%
for an RTX 2070 Super. An efficiency optimum lies *below* stock: in the one public dataset that
sweeps low enough, it sits at 62% of maximum frequency. The existing consumer datasets therefore
cannot locate an optimum, and their correspondingly small measured efficiency gaps (1.00% and 3.34%)
invite precisely the wrong conclusion — that consumer GPUs have little headroom — when what they
actually show is a truncated measurement range (§2.7).

A second constraint shapes what can be measured rather than what has been. On the hardware studied
here, GPU voltage is neither readable nor writable through any documented interface: enumeration of
the driver's full management API surface returns no voltage-related function among 260 device
operations (§3.2). Direct guardband measurement in the manner of [8], which requires undervolting
until failure, is therefore unavailable. What remains accessible — and what this work measures — is
the relationship between core frequency, power draw, and delivered performance.

This paper makes three contributions:

1. **An open dataset** of consumer-GPU frequency–power–performance measurements swept across
   40–100% of maximum core clock, a range that contains the efficiency optimum, released with the
   collection tooling and protocol.
2. **A characterisation of why existing public consumer DVFS data cannot answer efficiency
   questions**, placing each dataset on a common axis of swept range relative to rated boost clock,
   and reproducible in a single script.
3. **An evaluation of whether per-unit measurement is worth its cost** against a fixed-frequency
   policy — reported including the case where it is not. On the reference dataset, a probe-based
   model ties a single constant frequency, while the same probes reconstruct the full efficiency
   curve accurately enough to reduce measurement effort by 77%. Those are distinct results and are
   reported as such.

Two claims are explicitly **not** made. This work does not outperform vendor boost algorithms, which
already incorporate per-chip factory binning and against which a small independent study has no
plausible advantage. And it does not claim the discovery of guardband or of inter-chip variation;
both are established [8, 9]. The contribution is open, current-generation, reproducible measurement
of a relationship whose public data is either datacenter-only or swept over the wrong range.

---

## 2. Related Work

### 2.1 GPU DVFS and energy efficiency

Dynamic voltage and frequency scaling is a mature technique for trading performance against power,
and its application to GPUs has been studied for over a decade. Measurement studies established
early that substantial energy savings are available at modest performance cost — one such study
reported an average 19.28% energy reduction for under 4% performance loss across 37 benchmark
applications ⚠️. The general shape of the result is consistent across the literature: reducing core
frequency below stock improves performance-per-watt up to a point, after which fixed power costs
dominate and efficiency falls again.

Workload character strongly mediates this effect. Compute-bound kernels scale close to linearly
with core clock, while memory-bandwidth-bound kernels are limited elsewhere and are comparatively
insensitive to it [4]. This work reproduces that distinction directly (§3.2) and uses it to select
benchmark workloads.

### 2.2 Voltage guardbands and manufacturing variation

Vendors set operating points with margin for worst-case silicon, temperature, and ageing. Leng et
al. [8] measured this margin directly on commercial off-the-shelf cards by progressively undervolting
until program output became incorrect, and report:

> "there exists about **20% voltage guardband** on those GPUs spanning two architectural
> generations, which, if 'eliminated' completely, can result in **up to 25% energy savings** on one
> of the studied GPU cards."

Per-card figures are finer-grained: a 9–18% guardband between nominal voltage and Vmin on a GTX 680,
geometric-mean energy savings of 21% (GTX 680) and 15.8% (GTX 480), with savings ranging 14–25% and
8–22% respectively. They further establish that Vmin is **program-dependent** rather than a single
per-chip constant, and that voltage noise affects it more than process or temperature variation.

**Two points about [8] matter for positioning this work, and neither is a criticism of it.**

*First, it studied consumer cards — GTX 480 (Fermi, 2010) and GTX 680 (Kepler, 2012).* The
guardband question has therefore already been answered on consumer silicon; it has simply not been
revisited on parts more than a decade newer, whose power management (successive GPU Boost
generations, finer factory binning) differs substantially.

*Second, and more fundamentally, [8] measures a quantity this work cannot access.* They undervolt
directly and detect the Vmin failure point. On the hardware studied here, voltage is neither
readable nor writable through any documented interface (§3.2). This work therefore measures the
**frequency–power–efficiency** relationship, not the voltage guardband. These are related but
distinct quantities and are not presented as interchangeable.

Chip-to-chip variation has been characterised at cluster scale by Sinha et al. [9], who collected
over 18,800 hours of data across more than 90% of the GPUs in five HPC systems (Summit, Vortex,
Frontera, Longhorn, Corona) and report **8% average performance variation (max 22%) between
nominally identical GPUs of the same SKU**, with outliers up to **1.5× slower than the median GPU**.
Consumer-facing exposure of such variation has been limited and short-lived — GPU-Z's "ASIC quality"
reading surfaced leakage-based binning for a period before being deprecated as unreliable.

**Positioning.** The existence and approximate size of both the guardband and inter-chip variation
is therefore *established*, not novel. What this work adds is open, released measurement of the
frequency–efficiency relationship on current consumer parts, across a range that includes the
optimum.

### 2.3 Prediction models for frequency scaling

The closest prior work predicts optimal core *and* memory frequency configurations for an unseen
kernel from static code features, evaluated across three NVIDIA architectures (Kepler, Maxwell,
Volta) using a suite of micro-benchmarks [1]. A follow-up compares six model families and reports
XGBoost achieving R² ≈ 0.9646 on Volta [2]. Related approaches predict execution time and power
across frequency settings for deadline-aware scheduling ⚠️.

**Positioning.** This work does not claim a better predictor than [1]. It asks a different question:
whether per-*unit* prediction is worth its measurement cost at all, against a fixed-frequency
baseline — and reports a null where it is not (§5.2).

### 2.4 Energy-performance tradeoffs in modern workloads

Recent work characterises LLM inference under DVFS across five decoder-only models and four NLP
benchmarks, sweeping 180–2842 MHz, and reports approximately 42% energy savings for a 1–6% latency
increase, noting that the decode phase is largely frequency-insensitive [3]. That figure is a useful
independent corroboration: it is the same order of magnitude as the 44.4% efficiency gap measured
here on a different architecture and a different workload class (§5.1).

### 2.5 Measurement methodology

GPU power figures reported by `nvidia-smi` are not raw instrument readings. A detailed study of
NVIDIA's built-in power sensor documents its update frequency, transient response, and a boxcar
averaging window applied to reported values [5]. Any work sampling power through `nvidia-smi` — this
work included — inherits those characteristics, and §3.4 states the consequences explicitly rather
than treating the sensor as ground truth.

### 2.6 Vendor auto-tuning

NVIDIA ships automated overclock scanning (exposed through the NVIDIA App and bundled with
third-party tools such as MSI Afterburner). Inspection of the bundled scanner confirms it is
NVIDIA's own implementation, driving the voltage-frequency curve through NVAPI and reporting a
confidence level for a discovered curve.

**Positioning.** These tools optimise for *maximum stable clock*, not for *efficiency*, and they are
closed — they return a curve, not an explanation. This work targets the efficiency objective and
publishes its method.

### 2.7 Existing public datasets, and why they are insufficient

| Dataset | Hardware | Core sweep (% of rated boost) | Suitable for efficiency-optimum questions? |
|---|---|---|---|
| GPU-DVFS-Dataset [6] | 1× Tesla V100 | 55–111% | **Yes** — spans below stock |
| HKBU-HPML [7] | GTX 1080 Ti | 101–126% | **No** — at/above stock only |
| HKBU-HPML [7] | RTX 2070 Super | 95–118% | **No** — at/above stock only |

This is a contribution in its own right and is reproducible via `analysis/compare_consumer.py`.
Both public *consumer* DVFS datasets are effectively overclocking sweeps: they begin at or above the
rated boost clock and increase from there. Because the efficiency optimum lies *below* stock — at
62% of maximum in the V100 data — these datasets cannot locate it.

The consequence is a trap for anyone reading them naively. The GTX 1080 Ti data yields a mean
efficiency gap of 1.00% and the RTX 2070 Super 3.34%, against 44.40% for the V100. Read without
reference to stock clock, that pattern invites the conclusion that consumer GPUs lack headroom.
The correct reading is that the measurements stop short of where headroom appears — evidenced by
60% of 1080 Ti applications having their measured optimum at the lowest frequency tested, the
signature of a truncated range.

---

## 3. Methods

### 3.1 Hardware and software

| Component | Detail |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Ti 16 GB (Blackwell, GB206, compute capability 12.0) |
| Driver | 610.88 |
| Rated clocks | Base 2407 MHz, boost 2572 MHz (reference); **3090 MHz observed max** (factory-OC board) |
| Power limit | 180 W default, 200 W configured, adjustable range 150–200 W |
| Memory | 16 GB GDDR7, 128-bit bus, 448 GB/s |
| OS | Windows 11 |
| Framework | PyTorch 2.11.0+cu128 |

The distinction between reference and observed clocks is deliberate: the specification database
lists this model at 2572 MHz boost, while the physical card reports a 3090 MHz maximum. Spec-sheet
clocks are not measured clocks, and analyses use the measured values.

Additional units are drawn opportunistically from a small PC-building operation, giving on the order
of one new machine every 2–3 weeks. Sample size is therefore small and heterogeneous by
construction, and is reported explicitly wherever results are stated.

### 3.2 Frequency control

Control capability was established empirically rather than from documentation, by enumerating the
NVML export table on the target driver and invoking functions through P/Invoke:

| Mechanism | Result on target hardware |
|---|---|
| `nvidia-smi -lgc` (lock core clock) | **Supported.** Volta+. Requires administrator. 389 discrete clocks, 180–3090 MHz. |
| `nvidia-smi -pl` (power limit) | **Supported**, 150–200 W. Requires administrator. |
| `nvmlDeviceSetClockOffsets` | **Available.** Graphics ±1000 MHz, memory −2000/+6000 MHz per P-state. Returns `NO_PERMISSION` un-elevated (not `NOT_SUPPORTED`). |
| `nvmlDeviceGetGpcClkVfOffset` | **`NOT_SUPPORTED`** on this device. |
| Voltage read or write | **Unavailable.** No voltage-related exports across 260 NVML device functions. |

**This is the central methodological constraint of the work: voltage is neither observable nor
controllable through any documented interface.** Consequently this study measures *frequency versus
power*, not voltage versus frequency. It is not an undervolting study, and results are not presented
as such. Per-point voltage-frequency curve manipulation is possible only through undocumented NVAPI
entry points, which were deliberately excluded as unstable across driver revisions.

Measurements therefore fix the core clock and observe the power the card draws to sustain it.

**Third-party V/F curve overrides silently defeat clock locking.** `nvidia-smi -lgc` is not
authoritative when another utility owns the voltage-frequency curve. On the target device with an
MSI Afterburner profile applied — the curve flattened to ≈3010 MHz for every voltage above 925 mV —
a request for 2167 MHz produced a sustained **2942 MHz**, overshooting the cap by 775 MHz, while
1237 MHz locked normally. Repeating the identical sweep with the curve reset to stock, 2167 MHz
produced 2143.8 MHz and held. The flattened curve is therefore the cause rather than merely
consistent with the observation.

The failure is not benign, because it is not a random error. Requests falling inside the overridden
region collapse onto the **same** achieved clock, so a grid reports more distinct frequencies than
it measured and silently overweights one, while every row still looks well-formed. In the affected
sweep, 2 of 3 targets landed on one clock. Sweeps therefore record the direction of any lock miss:
*below* target indicates the device could not sustain the request (power or thermal limits, expected
at the top of the range where maximum boost is a bin no device holds — 3090 MHz sustains 2617.6 MHz
here), whereas *above* target indicates the cap was never applied, which `nvidia-smi` cannot do
unaided. Distinct achieved clocks are counted against planned points and reported per session.

This generalises beyond the present setup: any measurement or auto-tuning tool that assumes
`-lgc` is authoritative will silently mis-sample on the many consumer systems that run a persistent
overclocking profile.

### 3.3 Workload design

Performance measurement requires **fixed work**, not fixed time. Standard stress tools (OCCT,
FurMark, and NVIDIA's bundled `gpu_stressor`) run for a specified duration regardless of device
speed and so yield no throughput measure. Two fixed-work benchmarks are used, chosen to span the
compute/memory-bound axis identified in §2.1:

- **`gemm`** — dense matrix multiplication (8192², FP32) through cuBLAS. Compute-bound; scales
  approximately linearly with core clock. Matrix multiplication was chosen over a bespoke kernel
  specifically because `GeMM` appears in the reference V100 dataset [6], making the two directly
  comparable.
- **`membw`** — a scaled elementwise add over a 256 M-element buffer (≈3 GB of traffic per
  iteration). Bandwidth-bound; substantially less sensitive to core clock, though **not
  insensitive** — measured elasticity of throughput to core clock is ≈0.35 against ≈1.09 for
  `gemm` (§5.4). Below roughly 1200 MHz the streaming multiprocessors cannot issue memory requests
  fast enough to saturate DRAM, so the workload becomes issue-limited rather than bandwidth-limited
  and does retain clock sensitivity there.

Both perform identical arithmetic on every invocation, so wall-clock duration is a valid performance
metric and efficiency follows as work ÷ (duration × power).

Iteration counts are fixed per workload (120 for `gemm`, 1200 for `membw`), sized for approximately
8–9 s of device work at full boost, and **held constant across every frequency in a sweep**.
Preliminary runs at 30 iterations completed in 0.7–4.1 s, which proved too short for the device to
reach steady clock and thermal state and left kernel-launch overhead visible in throughput.

`membw`'s count was originally 600, which appeared to yield a 9.4 s run. Once instrumentation
overhead was excluded from the timer (§3.4) only 4.7 s of that proved to be memory traffic, and the
count was doubled to restore the intended duration.

### 3.4 Measurement protocol

For each target frequency:

1. Lock the core clock (`nvidia-smi -lgc`) and verify the lock held; readings deviating more than
   30 MHz from target are flagged, **with the direction recorded** (§3.2).
2. Wait 8 s for the device to settle.
3. Launch the benchmark as a separate process and **sample telemetry concurrently at 2 Hz while it
   runs**, recording SM clock, memory clock, power, temperature, utilisation, the decoded
   throttle-reason bitmask, and a timestamp per sample.
4. On completion, record the benchmark's internally-timed duration and **restrict the power average
   to the samples falling inside that same timed interval**, which the benchmark reports in epoch
   time.
5. Reset clocks (`nvidia-smi -rgc`) in a `finally` block that executes on every exit path, including
   interrupt, and verify the reset took effect.

**Measurement-instrumentation defects.** Three separate defects in this protocol produced
plausible-looking but wrong data, and are recorded because each was invisible on inspection and
detectable only by checking measurements against known device limits.

*Post-hoc sampling.* An early implementation sampled after the workload completed and therefore
recorded **idle** power at every frequency. Concurrent sampling is essential rather than incidental.

*Instrumentation inside the timed region.* The benchmark's temperature check invoked `nvidia-smi`
every 5 iterations between the start and stop of its performance timer. Each invocation is a process
spawn costing ≈42 ms, so `membw` at 600 iterations spent **50.5%** of its measured duration waiting
on a subprocess, and `gemm` 10.0%. Corrected throughput moved from 204.83 to 414.23 GB/s and from
15.60 to 17.62 TFLOP/s, both halves measured back-to-back under identical device state. (These
particular runs were taken with a memory overclock applied; the corrected `membw` figure should
therefore not be compared against the 448 GB/s stock rating, an error made in an earlier draft.
Measured later at stock memory the same benchmark reaches 343.7 GB/s, or 77% of rating — an
unremarkable stream efficiency, and the uncorrected 46% was the signal something was wrong.)
Polling is now time-based (an iteration-based cadence samples a fast device more often
than a slow one) and its cost is measured and subtracted; `duration_seconds` is work-only, with
`wall_seconds` and `monitoring_overhead_seconds` reported alongside for audit.

*Mismatched averaging windows.* Power was averaged over the workload **process** while performance
was taken from the benchmark's internal timer, so the power average included ≈2.3 s of interpreter
startup and CUDA initialisation at idle: 124.77 W recorded against 148.52 W actually drawn. Since
efficiency is throughput ÷ power, this divided a load measurement by a partly-idle one.

Neither of the latter two was a constant offset. Both were fixed wall-clock costs, so each shrank as
a proportion of the run as the clock was locked lower, and they biased the efficiency curve in
**opposite** directions — instrumentation-in-timer penalising high frequencies, power dilution
flattering them. A frequency-dependent bias in either duration or power is a bias in the *location*
of the efficiency optimum, which is the quantity of interest. Measured on a validation sweep, the
power correction alone recovered 8.6% at 1236 MHz against 22.8% at 2942 MHz, and changed the
apparent efficiency gap between those points from 7.9% to 21.1%.

The sweep grid spans **40–100% of the device maximum** (1237–3090 MHz here, 13 points). The floor is
deliberate: consumer devices report supported clocks as low as 180 MHz, which are never
efficiency-optimal for real work and make fixed-work benchmarks impractically slow. The V100
reference swept 55–111% of rated boost and located its optimum at 62% of maximum.

**Contention control.** Baseline utilisation is measured before each sweep and the run is aborted
above 10%. This is not a formality: a validation run conducted during an active gaming session
recorded 79% baseline utilisation, with benchmark throughput falling from 8.03 to 4.84 TFLOP/s from
contention alone. Competing load cannot be separated from the measurement after the fact.

**Instrument limitations.** Power is read through `nvidia-smi`, which applies boxcar averaging and
has finite update frequency and transient response [5]. Reported power is therefore a smoothed
device-side estimate, not a shunt measurement, and short transients are not resolvable. All
comparisons are made between measurements taken through the same instrument.

### 3.5 Stability testing

Stability is assessed separately from efficiency, using OCCT's GPU:3D test in Adaptive mode with
error detection enabled, for 10 minutes per configuration. Adaptive mode was chosen over FurMark
because contemporary drivers detect FurMark's constant synthetic load pattern specifically.

Telemetry is logged throughout and the Windows System event log is checked for display-driver reset
events (ID 4101) within the run window. Runs are classified `CLEAN`, `FLAGGED` (thermal or hardware
throttling observed), or `UNSTABLE` (driver reset or telemetry failure).

**A `CLEAN` result is reported as "no failure observed in 10 minutes," never as "stable."**
Undervolt-induced instability commonly requires hours to manifest. Separately, GDDR7 employs error
correction that silently retries on failure, so a memory overclock may be free of crashes while
being net *slower* — stability testing and performance testing are therefore treated as distinct
checks and both are required.

### 3.6 Analysis

**Efficiency** is defined as performance per watt, normalised per unit to its value at the highest
measured frequency — the convention used by the reference dataset [6], preserving comparability.

**Validation** uses leave-one-unit-out cross-validation, where a unit is a workload (V100 data) or a
physical chip (collected data). Splitting on individual measurements rather than units would allow a
model to observe the same unit at a neighbouring frequency and inflate its apparent skill.

**Metric.** Strategies are scored by *regret*: the efficiency given up relative to that unit's own
optimum, in percentage points. Regret is preferred to exact-match accuracy because selecting a
neighbouring frequency on a flat curve costs almost nothing, while exact-match scores it identically
to selecting the worst available frequency.

**Baselines**, chosen to be difficult rather than flattering:

1. **Stock** — always run at maximum frequency. What the device does by default.
2. **Best fixed frequency** — a single frequency selected from training units only, applied to all
   held-out units. Requires no per-unit measurement, and is the baseline any per-unit method must
   justify its cost against.

**Datasets are never pooled.** The V100 and consumer measurements differ in architecture, workload
type, and feature space. Models are fitted separately and compared.

---

## 4. Data availability

All code, protocols, and collected data are released at
`https://github.com/imaoofu/headroom`. Third-party datasets are fetched by script rather than
redistributed. Collected sweeps are published as CSV with an accompanying schema.

---

## 5. Results

### 5.1 Efficiency headroom in the reference dataset

Running each of 33 workloads at stock (1530 MHz) rather than at its own efficiency optimum gives up
a mean of **44.4%** efficiency (median 45.7%, range 15.1–62.8%), costing a mean 13.7% performance
and saving a mean 40.1% power. Measured directly; no model involved.

### 5.2 Per-unit prediction does not beat a fixed frequency

| Strategy | Mean regret | Median | Worst | Exact match |
|---|---|---|---|---|
| Stock (do nothing) | 44.396% | 45.68% | 62.81% | 0.0% |
| **Best fixed frequency (952 MHz)** | **0.837%** | 0.00% | 6.89% | **72.7%** |
| Probe model (Ridge, 4 probes) | 0.883% | 0.00% | 6.89% | 69.7% |

The probe model does not improve on a single fixed frequency. The mechanism is visible in the data:
952 MHz is optimal for 24 of 33 workloads (73%), so a constant already captures 43.56 of the 44.4
available percentage points and little per-unit variation remains to exploit. Workload sensitivity
is present and directionally consistent with §2.1 — correlation −0.666 between performance retained
at the lowest frequency and optimal frequency — but insufficient to beat the constant.

**This null is reported as the result.** The analysis script emits this verdict about its own output.

### 5.3 Probe-based curve reconstruction

While probe measurements do not improve frequency *selection*, they do reconstruct the full curve
accurately, which reduces measurement cost:

| Probes | Frequencies selected (MHz) | Curve MAE | Measurement reduction |
|---|---|---|---|
| 3 | 757, 825, 1530 | 0.0290 | 77% |
| 4 | 757, 825, 885, 1530 | 0.0261 | 69% |
| 5 | + 952 | 0.0243 | 62% |

These are distinct claims and are not conflated: reconstruction succeeds while selection ties,
because when one frequency is optimal for most units a constant is already near-optimal.

### 5.4 Consumer hardware measurements

`[n = 1 unit, 2 workloads, 13 frequencies each. Single-chip result; no cross-unit claim.]`

Thirteen-point sweeps on an RTX 5060 Ti, stock V/F curve, 464–3090 MHz requested
(`20260816-001048_5060ti-gemm-floor15`, `20260816-001734_5060ti-membw-floor15`). Reproduce with
`python analysis/analyze_sweep.py`.

| | `gemm` (compute-bound) | `membw` (bandwidth-bound) |
|---|---|---|
| Efficiency optimum | **1552 MHz** | **1552 MHz** |
| — as % of sustained max | 60% (of 2597 MHz) | 56% (of 2755 MHz) |
| Efficiency gain vs sustained max | **+46.5%** | **+41.6%** |
| Performance cost at optimum | −43.2% | **−11.3%** |
| Power saved at optimum | −61.2% | −37.4% |

**The V100 headroom result reproduces on consumer silicon.** The reference dataset gives a 44.4%
mean efficiency gain for a 13.7% performance cost and 40.1% power saving, with its optimum at 62%
of maximum (§5.1). The `membw` figures here — 41.6%, 11.3%, 37.4%, at 56% of sustained maximum —
match that on every axis, on a 2025 consumer part measured independently seven years and four
architectural generations later. This is the central empirical claim of the work: the efficiency
headroom identified on datacentre hardware is not an artefact of datacentre hardware.

**The compute/memory distinction appears in what the optimum costs, not where it sits.** Both
optima land on the same grid point, so at this resolution they are *indistinguishable* — which is
not the same as equal, and separating them requires a finer sweep around 1300–1800 MHz rather than
a wider one. What does separate cleanly is the price of operating there: `gemm` surrenders 43.2% of
its throughput to reach its optimum, `membw` only 11.3%. For bandwidth-bound work, running at 56%
of maximum clock is close to free — 37.4% less power for an 11.3% slowdown. For compute-bound work
it is a genuine trade. Any recommender built on this must therefore be workload-aware in its
*advice*, even where the optimal frequency itself is common.

Both curves are single-peaked with the optimum well inside the swept range, so these are interior
optima rather than artefacts of where the sweep stopped. One minor irregularity: `gemm` efficiency
at 1987 MHz (119.40 GFLOP/J) sits marginally below 2205 MHz (120.12), breaking monotonicity by 0.6%
— within run-to-run variation and not treated as structure.

#### Correction: the earlier 3-point diagnosis was wrong

A preceding 3-point sweep (1237 / 2167 / 3090 MHz) found efficiency highest at its lowest point and
concluded **the sweep floor was too high to contain the optimum.** That was a misdiagnosis, recorded
here rather than removed because the reasoning error is instructive.

The optimum is at 1552 MHz — comfortably *inside* the original 40%-floor range (1237–3090 MHz). The
floor was never the problem. Three points were. The error was over-applying this work's own
criterion from §2.7, where an optimum landing on the lowest frequency tested signals a range that
stops short: **that inference holds only for a dense sweep.** On a sparse one, an optimum at the
lowest sampled point is equally consistent with the true optimum lying between the first and second
points, which is precisely what occurred. A criterion for detecting truncated *ranges* was applied
to what was actually insufficient *resolution*.

Lowering the floor to 15% nevertheless earned its place, for a reason other than the one given at
the time: efficiency falls monotonically from 1552 MHz down to 464 MHz, which establishes the
optimum as interior. Had the sweep begun at 1237 MHz, the peak would have been found but could not
have been shown to be a peak rather than an edge.

The superseded 3-point measurements are retained in `data/frequency-sweeps/` as validation runs.

**The compute-bound / memory-bound contrast is confirmed, and is smaller than assumed.** Across the
full 464–2750 MHz range the elasticity of throughput to core clock is **1.18** for `gemm` and
**0.32** for `membw` — a 3.7× difference in clock sensitivity, which is the effect the two-workload
design exists to produce. But `membw` still gained 75% throughput over a 5.9× clock increase, so it
is strongly sub-linear rather than insensitive, and §3.3's original "comparatively insensitive"
framing is corrected accordingly. The residual sensitivity is expected and its cause is visible in
the curve: the device sustains 200.3 GB/s at 464 MHz against 351.4 GB/s at 2754 MHz, i.e. it cannot
issue memory requests fast enough to saturate DRAM at low core clock, and is issue-limited rather
than bandwidth-limited there. Bandwidth saturates only above roughly 1990 MHz, beyond which a
further 39% of clock buys 2.5% of throughput while costing 34% more power.

**Sustained maximum boost is workload-dependent**, so "stock" is not a single frequency. Requesting
3090 MHz yielded 2597 MHz under `gemm` (171.9 W) but 2754 MHz under `membw` (86.2 W): the
more power-intensive workload sustains a *lower* clock. Consequently the top of any grid built from
`clocks.max.sm` is unreachable, and grid points above roughly 2800 MHz will collapse onto one
achieved clock — a second, benign mechanism for the collapse described in §3.2, and one that must be
distinguished from it. Any stock-versus-tuned gap must define stock as the clock the device selects
*for that workload*, not as a nameplate figure.

**Workload type does shift the optimal frequency — in the direction opposite to the prediction.**
§2.1's compute/memory-bound distinction and the V100's −0.666 correlation between performance
retained at the lowest frequency and optimal clock both predict that the *less* frequency-sensitive
workload should prefer a *lower* optimum. A fine sweep resolves the two optima and finds the
reverse: `gemm` optimises at **1488 MHz** and `membw` at **1634 MHz**, a difference of
**146 MHz (95% CI 93–187 MHz)**, with the bandwidth-oriented workload preferring the *higher*
clock. Method, evidence and the reasons for caution are in §5.4.1.

**Incidental comparison: a manual tune beat stock at the top of the range.** The earlier validation
sweep ran with an Afterburner profile applied (flattened V/F curve, ≈3010 MHz above 925 mV). At the
maximum-boost request, that configuration sustained 2942 MHz at 162.91 W and 17.42 TFLOP/s, against
stock's 2617.6 MHz at 167.03 W and 15.40 TFLOP/s — **+13.1% throughput for −2.5% power, ≈15.9%
better efficiency.** This is the paper's central thesis in miniature: conservative stock behaviour
leaves measurable headroom that an empirically-found configuration recovers. It is reported as an
observation, not a result. The two sweeps were run separately rather than interleaved, background
utilisation differed (6.2% against 3.6%), thermal state was not matched, and n = 1 chip, 1 workload,
1 configuration. A controlled stock-versus-tuned comparison on the same unit is required before this
is more than suggestive, and is the obvious next measurement.

#### 5.4.1 Resolving the two optima

The coarse sweep placed both workloads' optima in the same 217 MHz bin, which is a statement about
grid resolution rather than about the hardware. Separating them required a design change, because
the obvious approach does not work.

**An efficiency curve is flat near its optimum by construction, so its argmax is largely noise.**
In the 13-point coarse run `gemm`'s peak stood 1.8% above the points ±218 MHz on either side, while
the same run contained an unexplained 0.6% non-monotonicity between 1987 and 2205 MHz. On synthetic
curves with a known peak, this grid and realistic noise, the raw argmax moved **53–60 MHz between
identical passes**. Comparing two argmaxes would have compared two coin flips. The measured
repeatability here was worse than assumed at design time — median 2.4% for `gemm` and 1.7% for
`membw` between passes, driven by power rather than by throughput, whose pass-to-pass agreement was
0.2–1%.

The design therefore: **13 points over 1200–1900 MHz, two passes per workload, run in the order
`gemm`, `membw`, `membw`, `gemm`**, with the optimum located by fitting the curve rather than by
selecting a point. Three choices carry weight.

*The band is wider than the peak.* A fit needs curvature to constrain a vertex; across 1300–1800 MHz
the curve falls only ~2% from peak, against 8–9% across 1200–1900 MHz. Tightening a fine sweep
around the peak buys frequency resolution and pays for it in signal.

*The order is counterbalanced.* Sweeps run ascending and the card warms over a ~30 minute session,
so run position is confounded with temperature. The ABBA order put each workload in one early and
one late slot. It worked: `gemm` ran at 47–53 °C then 44–51 °C, `membw` at 39–49 °C then 45–52 °C,
so drift landed on both workloads rather than on the difference between them.

*The estimator is a cubic, not a parabola.* Efficiency curves are asymmetric — steep rise, gentle
fall — and a symmetric parabola fitted to a skewed curve places its vertex on the shallow side.
Measured on synthetic curves peaking at 1550 MHz: the parabola returned 1550/1564/1578/1587 MHz at
skews of 0.0/0.3/0.6/0.8 with ±2 MHz scatter, while the cubic returned 1550 MHz at every skew with
±5 MHz scatter. **The parabola is precise and wrong.** This is not a cosmetic difference: the two
workloads have differently-shaped curves, so the bias does not cancel in the difference. Given two
synthetic curves with an *identical* optimum at 1550 MHz and skews of 0.8 and 0.0, the parabola
reported "+37 MHz, 95% CI +29 to +45, the optima do differ" — a false positive of the same size and
direction as the effect being sought. The cubic reported no difference, correctly. That failure was
caught by `analysis/test_analyze_fine_sweep.py`, which checks the estimator against curves whose
answers are known by construction, and not by inspection of the code.

**Result.** Each of the four sweeps locates a vertex independently, and they agree:

| | vertex | 95% CI |
|---|---|---|
| `gemm` pass 1 † | 1508 MHz | 1452–1580 |
| `gemm` pass 2 | 1480 MHz | 1446–1524 |
| `membw` pass 1 | 1636 MHz | 1590–1668 |
| `membw` pass 2 | 1632 MHz | 1576–1667 |

† excluding the two contaminated points identified below. The two `gemm` fits agree within 28 MHz
and the two `membw` fits within 4 MHz, while the gap between workloads is ~150 MHz — so the effect
is larger than the disagreement between repeats of the same measurement.

Pooled: `gemm` **1488 MHz**, `membw` **1634 MHz**, difference **−146 MHz (95% CI −187 to −93)**.
All 52 points held their locked clock exactly, none overshot, and all 52 had power windowed to the
benchmark's timed region.

**The finding is robust to the one known contamination.** A console-selection freeze (§5.4.2)
interrupted `gemm` pass 1 at its 1725 and 1785 MHz points, which read 7.3% and 4.6% below their
pass-2 counterparts and produced throughput *falling* as clock *rose* — physically impossible, and
identifiable without reference to the conclusion. Because those points depress `gemm`'s
high-frequency flank, they bias its vertex downward, i.e. *toward* the reported effect. Removing
them does not remove it:

| Handling of the contaminated points | `gemm` | `membw` | difference |
|---|---|---|---|
| Retained | 1467 | 1634 | −167 (−204, −118) |
| Dropped from `gemm` pass 1 | 1488 | 1634 | −146 (−187, −93) |
| `gemm` pass 1 dropped entirely | 1480 | 1634 | −154 (−196, −103) |
| Dropped from both `gemm` passes | 1489 | 1634 | −146 (−191, −88) |

The contamination accounts for ~20 MHz of a ~150 MHz effect. The coarse sweep from the previous
session — a separate run on a different grid — independently gives the same sign (`gemm` 1571 MHz,
`membw` 1601 MHz by parabola over its four in-band points).

**Why this is not yet a refutation of the V100 correlation.** Two reasons, and both should survive
into any write-up.

First, **`membw` is not memory-bound by the V100's own criterion.** That correlation classifies
workloads by performance retained at the lowest frequency swept, with memory-bound meaning ≥90%
retained. Evaluated at the same *relative* floor the V100's 757 MHz represented (49% of sustained
maximum), `gemm` retains 46% — properly compute-bound — but `membw` retains **78%**, which falls in
neither the ≥90% memory-bound class nor the <70% compute-bound class. §5.4 already established that
this kernel is issue-limited rather than bandwidth-limited below ~1990 MHz. The prediction is
therefore being tested outside the domain where its premise holds, and the mechanism is visible in
the data: across 1200–1890 MHz `gemm` gains 66.9% throughput for 67.1% more power, while `membw`
gains 26.8% for 25.8% more power. `membw`'s power grows more slowly with core clock because its
consumption is dominated by a memory subsystem running at fixed clock, so it can afford more core
clock before power overtakes throughput — which is exactly a *higher* optimum. A genuinely
bandwidth-saturated kernel would not behave this way, and building one is the correct next test.

Second, **the effect is statistically clear and practically small.** Running `gemm` at `membw`'s
optimum costs 1.6% efficiency; running `membw` at `gemm`'s costs 1.8%. The optima differ, but the
penalty for using one frequency for both is under 2% — which is itself a useful result for a
recommender, and a caution against over-reading the 150 MHz gap.

#### 5.4.2 An instrumentation hazard worth recording

`gemm` pass 1 froze for six minutes mid-sweep with the GPU clock-locked and idle. The cause was not
the benchmark, the sweep script, or the driver: Windows consoles enable QuickEdit by default, so a
single click inside the window enters selection mode, and **selection mode blocks all output to that
console**, suspending any process that writes progress. There is no error, the process stays alive,
and the only visible trace is the word `Select` prepended to the window title.

This is recorded because it is a silent failure mode for exactly the kind of long, unattended,
elevated run this project depends on, and because its damage was *not* obvious: the interrupted
point itself looked normal (it reheated during the settle interval), while the two neighbouring
points were measurably corrupted. Both sweep tooling and the stability logger now disable QuickEdit
at startup.

#### 5.4.3 The sub-100% utilisation is a telemetry artifact, not lost work

Sweep points recorded GPU utilisation below 100% even after subtracting the measured `nvidia-smi`
monitoring cost, and the residual appeared to grow with clock: 0.9% at 1200 MHz, 5.5% at 1897 MHz,
7.5% at 2754 MHz. Read naively this is the signature of a CPU that cannot launch kernels fast enough
as they shorten — which would suppress high-clock throughput, understate high-clock efficiency, and
bias `membw`'s optimum downward. That would undermine §5.4.1, so it was tested.

**The counterbalanced passes already answer it.** Each target frequency was measured twice in
opposite order. At 1897 MHz the two passes recorded utilisation of **99.0% and 92.7%** — and
throughput of **342.3 and 342.3 GB/s**. At 1605 MHz, 99.0% and 93.0% utilisation gave 320.1 and
321.4 GB/s, the *lower*-utilisation pass being marginally faster. A six-point utilisation difference
with no throughput difference means the two are decoupled: whatever `utilization.gpu` is varying
over, it is not work.

**A direct test confirms it.** Holding total bytes moved constant while varying bytes-per-kernel
over a 32× range changes the launch count from 320 to 10240. Throughput across that range spans
415.3–417.6 GB/s — a **0.5% spread**, running the wrong way for the hypothesis, with the smallest
kernels marginally fastest. Replaying the identical sequence from a CUDA graph, which removes nearly
all per-launch CPU work, moved throughput **−0.1%**. Clock was steady at 2992 MHz across every
condition (measured spread 0 MHz).

The instructive detail is that the CPU cost is genuinely large and still not binding. At 16 M
elements per kernel the CPU spent **90% of wall time** submitting launches; at 512 M it spent 0.0%.
Throughput was the same. **A high CPU cost is not a CPU bottleneck** — the submission thread stays
ahead of the GPU until it doesn't, and 90% occupancy is not 100%. The sweep's own configuration sits
at 0.1% submit, three orders of magnitude clear of the edge.

The conclusion for methodology is narrow but worth stating: `utilization.gpu` averaged over ~25
samples is too coarse to support an argument about lost work, and should not be used as one.
Throughput is the measurement; utilisation is a diagnostic hint. Data in `data/probes/`.

### 5.5 Cross-chip variation

`[PENDING — requires multiple units]`

### 5.6 The performance-constrained optimum

§5.1's 44.4% is the *unconstrained* optimum: best efficiency at any cost, and the cost is a mean
13.7% performance. Almost nobody wants that trade. The question users actually ask is constrained —
maximise efficiency subject to keeping at least some fraction of stock performance — and the same
data answers it. Run `python analysis/analyze_constrained.py`.

**Reference dataset, 33 workloads.** Realised loss is below the floor because the optimum must land
on one of 13 grid points, so the constraint is usually overshot; every saving here is therefore a
lower bound on what a continuous knob would reach.

| floor | workloads that downclock | efficiency gain (mean / median) | realised perf lost (mean / worst) | power saved | median freq |
|---|---|---|---|---|---|
| 95% | 33/33 | **28.5% / 22.3%** | 3.3% / 4.9% | 23.4% | 1275 MHz |
| 90% | 33/33 | 35.8% / 36.6% | 6.5% / 9.9% | 30.5% | 1080 MHz |
| 85% | 33/33 | 41.1% / 43.3% | 9.4% / 15.0% | 35.5% | 952 MHz |

**Every workload benefits at a 5% budget** — the worst case is still +3.3% efficiency, and the mean
28.5% gain costs only 3.3% realised performance. Two-thirds of the unconstrained 44.4% survives a
constraint that removes three-quarters of its performance cost, which is the practically useful form
of the result.

**Against GEEPAFS [6], on the same chip.** Their online policy achieves 26.7% mean efficiency gain
for 5.8% performance loss. At a 95% floor this analysis reaches 28.5% for 3.3% — better on both
axes. **That comparison must not be presented as a win.** GEEPAFS chooses frequencies live with no
prior knowledge of the application; this is an offline oracle that has already measured the entire
curve for every workload. An oracle is *supposed* to beat an online policy, and a margin this
narrow — 1.8 points of efficiency — is the more notable observation: it bounds how much a perfect
predictor could add over an existing deployed method, and the answer is *not much*.

That bound applies to *adaptive* methods only, and reading it as a general statement about
frequency selection would be a mistake — §5.6.1 shows the comparison against a non-adaptive baseline
runs the other way entirely.

#### 5.6.1 The constraint is what makes workload identity valuable

§5.2 found that a probe-based model does not beat a single fixed frequency, and that null stands.
It was measured *without* a performance constraint. Applying the same baseline under one reverses
it.

A fixed-frequency policy must honour its guarantee on **every** workload it might meet, so it cannot
choose a frequency that is merely good on average — it is pinned by the most frequency-sensitive
workload in the set. On the V100 at a 95% floor, `BiCG` and `GeMM` need at least 1462 MHz, while
`CNN_1.5M`, `ViT_t` and `RL-PPO` would be fine at 757 MHz. One frequency has to serve both ends.

| floor | per-workload optimum | best single fixed frequency | pinned at | gap | share of available gain |
|---|---|---|---|---|---|
| 95% | 28.5% | **4.9%** | 1462 MHz | **23.6 pp** | **83%** |
| 90% | 35.8% | 10.2% | 1402 MHz | 25.6 pp | 72% |
| 85% | 41.1% | 22.2% | 1275 MHz | 18.9 pp | 46% |
| 80% | 43.1% | 27.5% | 1207 MHz | 15.6 pp | 36% |

**At a 95% floor, 83% of all available efficiency gain requires knowing which workload is running.**
The fixed policy can descend only one grid step below stock and captures 4.9% of an available 28.5%.

Robustness: excluding the four flat-top workloads of §5.6 whose curves may be noise, the gap is
still **20.7 pp of 25.8 pp** — 80%. The effect does not depend on the questionable points.

The consumer sweeps reproduce the mechanism at smaller scale, and one detail is worth stating
plainly: **at a 95% floor no single frequency is feasible for both workloads at all**, because
`gemm` needs 2592 MHz to hold 95% and no shared grid point that high exists in `membw`'s sweep. The
tool reports that rather than substituting a number. At a 90% floor the gap is 7.4 pp of 26.2 pp
(28%), smaller than the V100's — expected, since two workloads of similar clock sensitivity span
much less of the space than 33.

**This is the reconciliation between §5.2 and the project's premise.** Unconstrained, the efficiency
curve is flat near its peak and one frequency serves nearly everything — hence the null, which is
real and stays reported. Constrained, the flat region is cut off from below by whichever workload
loses performance fastest, and workload identity becomes worth most of the available gain. The
defensible claim is therefore not *"per-workload tuning is worth its cost"* nor *"it is not"*, but
that **the answer inverts depending on whether a performance guarantee is required, and the
unconstrained measurement is the misleading one** — because a performance guarantee is what
essentially every real deployment has.

It also explains why GEEPAFS is a substantial result rather than an over-engineered one: adaptation
is doing real work under a constraint, which is precisely the regime it targets.

**Consumer hardware, and this is where the constraint bites unevenly.** The two workloads diverge
sharply once a performance floor is imposed, in a way the unconstrained optima did not reveal:

| floor | `gemm` (compute-bound) | `membw` (memory-bound) |
|---|---|---|
| 99% | 0% gain — cannot move | 21.6% gain, 0.9% lost, 18.5% power saved |
| 95% | **0% gain — cannot move** | **36.4% gain, 4.9% lost, 30.2% power saved** |
| 90% | 16.1% gain, 7.1% lost | 36.4% gain, 4.9% lost |

At a 5% performance budget `gemm` can do nothing at all, while `membw` gains 36.4% efficiency and
saves 30.2% power. The unconstrained optima differ by only 146 MHz (§5.4.1) with under 2% penalty
for using one for the other; **the constrained optima differ qualitatively.** Workload-aware
frequency selection matters far more under a performance constraint than without one — which is an
argument for the project's premise that the §5.4.1 result on its own does not make.

**Caveats, all reported by the tool rather than left to the reader.** Floors of 100% and 99% sit
inside a 1% noise band and are flagged as unquotable: 4 of the 33 V100 workloads (CNN_1.8M, FDTD,
CNN_1.5M, RL-PPO) record performance *above* their own 1530 MHz value at some lower frequency, by
+0.62 to +1.44 percentage points. Either those curves are genuinely flat across the top — which
would mean real downclocking at literally zero cost, and they are the memory-bound workloads where
that is most plausible — or a 1% excess is noise in a dataset averaging 5 repeats. The data cannot
separate the two and neither is asserted. Separately, the consumer reference is the card's
*sustained maximum* on an overclocked card whose offsets were never recorded, so the consumer half
is shape, not magnitude, until §5.4's interleaved stock-versus-tuned run exists.

The optimiser brute-forces the feasible set rather than using the closed form
`max(unconstrained optimum, lowest feasible frequency)`, and reports whether the two agree. They
agree on all 33 V100 workloads. They disagree on the consumer sweeps, but only by 1–5 MHz, and the
tool identifies why: the card clamped several high targets onto one achieved clock, so those are
repeat measurements of one condition rather than distinct grid points.

---

## 6. Limitations

1. **Voltage is unmeasured.** No documented API exposes it. This is a frequency-power study.
2. **Small, heterogeneous sample.** Access is limited to roughly one machine every 2–3 weeks, mostly
   different models rather than repeats, which bounds any claim about chip-to-chip variation.
3. **Single vendor, recent architecture.** NVIDIA only; no AMD or Intel measurements.
4. **Power is a device-side estimate**, boxcar-averaged, not an external measurement [5].
5. **Stability windows are short.** Ten minutes is not proof of stability.
6. **Reference-dataset results are single-device.** The 44.4% figure is one V100; it is not a
   population estimate.

---

## References

**Verified** — primary source opened, quoted figures confirmed against it:

- [3] Maliakel, Ilager, Brandic. *Characterizing LLM Inference Energy-Performance Tradeoffs across
  Workloads and GPU Scaling.* arXiv:2501.08219.
- [5] Yang et al. *Accurate and Convenient Energy Measurements for GPUs: A Detailed Study of NVIDIA
  GPU's Built-in Power Sensor.* 2024. Code: `github.com/JimZeyuYang/GPU_Power_Benchmark`
- [6] Zhang, Wang, Lin, Xu, Wang. *Improving GPU Energy Efficiency through an
  Application-transparent Frequency Scaling Policy with Performance Assurance.* EuroSys '24,
  pp. 769–785. ACM. doi:10.1145/3627703.3629584.
  Dataset: `github.com/zyjopensource/GPU-DVFS-Dataset` — **no license stated**; not redistributed
  here, fetched locally by `scripts/Get-Dataset.ps1`. Their reported result is **26.7% mean V100
  efficiency gain for 5.8% performance loss**, which is performance-constrained and therefore not
  the same quantity as this project's unconstrained 44.4% (§5.1). The two must not be compared
  directly as if one beats the other.
- [7] HKBU-HPML DVFS datasets. `github.com/HKBU-HPML/GPU-DVFS-Job-Schedule`,
  `github.com/HKBU-HPML/NV-DVFS-Benchmark`
- [8] Leng, Buyuktosunoglu, Bertran, Bose, Janapa Reddi. *Safe Limits on Voltage Reduction
  Efficiency in GPUs: a Direct Measurement Approach.* MICRO-48, December 2015. IBM T.J. Watson
  Research Center / University of Texas at Austin.
  PDF: `cs.sjtu.edu.cn/~leng-jw/resources/Files/leng15micro-gpuvminexp.pdf`
  *Figures confirmed by reading the paper: ~20% guardband across two generations; up to 25% energy
  savings on one card; 9–18% guardband on GTX 680 specifically; geomean savings 21% (GTX 680) and
  15.8% (GTX 480); ranges 14–25% and 8–22%.*
- [9] Sinha, Guliani, Jain, Tran, Sinclair, Venkataraman. *Not All GPUs Are Created Equal:
  Characterizing Variability in Large-Scale, Accelerator-Rich Systems.* SC '22. arXiv:2208.11035.
  *Figures confirmed: 8% average (max 22%) performance variation within identical SKUs; outliers up
  to 1.5× slower than median; >18,800 hours across five clusters.*

**⚠️ Located but not yet read in full** — open the primary source before submission:

- [1] Guerreiro et al. *Predictable GPUs Frequency Scaling for Energy and Performance.* ICPP 2019.
  DOI 10.1145/3337821.3337833 — **the closest prior art; read this before finalising any novelty
  claim.**
- [2] *Accurate Energy and Performance Prediction for Frequency-Scaled GPU Kernels.* MDPI
  Computation 8(2):37.
- [4] Measurement studies of GPU DVFS energy conservation (multiple; consolidate to one citation).
- Rodinia benchmark suite. IISWC 2009.

### Corrections made during citation verification

Recorded because both errors would have reached a submitted draft:

- **"~140 MHz / ~11% frequency variation"** attributed to [9] was **wrong** — a garbled second-hand
  summary. The paper reports 8% average and 22% maximum *performance* variation, and 1.5× outliers.
- **"9–18% guardband"** as the headline figure for [8] was **wrong** — that is the GTX 680-specific
  range. The headline is ~20% across two architectural generations. This error came from a local
  model's extraction of the PDF and was caught by checking the raw text.
