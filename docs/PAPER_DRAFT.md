# Headroom — paper draft

> **Status: Related Work and Methods are drafted. Results are partly written and rest on original
> data.** Sections 5.4 and 5.7 are backed by 21 committed sweeps on one RTX 5060 Ti, including
> core-voltage and crossbar telemetry; earlier sections still carry `[PENDING]` placeholders.
> Every number not marked `[PENDING]` traces to something actually run or actually read, and 50 of
> them are pinned by `analysis/audit_claims.py`, which recomputes each from the CSVs and fails if
> the text and the data disagree. Placeholders are marked rather than filled with plausible
> values.
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
- **`membw`** - a scaled elementwise add over a 256 M-element buffer (~3 GB of traffic per
  iteration). Intended as the bandwidth-bound counterpart; substantially less sensitive to core
  clock than `gemm` - measured elasticity of throughput to core clock is ~0.36 against ~1.12 for
  `gemm` (section 5.4) - but **it is not bandwidth-saturated over most of the swept range**, and
  that is a material limitation rather than a detail. See 3.3.1.

Both perform identical arithmetic on every invocation, so wall-clock duration is a valid performance
metric and efficiency follows as work ÷ (duration × power).

Iteration counts are fixed per workload (120 for `gemm`, 1200 for `membw`), sized for approximately
8–9 s of device work at full boost, and **held constant across every frequency in a sweep**.
Preliminary runs at 30 iterations completed in 0.7–4.1 s, which proved too short for the device to
reach steady clock and thermal state and left kernel-launch overhead visible in throughput.

`membw`'s count was originally 600, which appeared to yield a 9.4 s run. Once instrumentation
overhead was excluded from the timer (§3.4) only 4.7 s of that proved to be memory traffic, and the
count was doubled to restore the intended duration.

#### 3.3.1 `membw` is issue-limited, not bandwidth-limited, below roughly 2000 MHz - DRAFT

An earlier version of this section placed the issue-limited regime below ~1200 MHz. Direct
measurement puts it far higher, and the correction matters: it means the frequency-prediction
results of section 5.2 were tested against a workload whose memory-bound premise does not hold
where the test was run.

A DRAM-limited kernel is flat against core clock. `membw` is not: on stock it rises 264.9 to 352.2
GB/s from 1237 to 2932 MHz, i.e. 59% to 79% of the card's 448 GB/s rating, flattening only at the
very top.

Three independent attempts to construct a genuinely saturated kernel all fail, and converge:

1. **Six access patterns** - triad, copy, a width-doubled copy, scale, read-only reduction, and
   in-place add - measured at 1395 and 2760 MHz. Elasticity to core clock ranges 0.45 to 0.96. None
   is DRAM-limited. The read-only reduction is the *worst* (0.957): it carries dependency chains and
   performs one add per 4 bytes, making it more issue-hungry per byte moved than the triad. The
   width-doubled copy is indistinguishable from the plain one, indicating the library kernels already
   emit vectorised accesses.
2. **Concurrency** - four independent copies on separate streams at 1395 MHz reach 281.2 GB/s
   aggregate, against 218.3 for one, then plateau; eight streams add nothing.
3. **A hand-written CUDA kernel** issuing 1 to 16 independent `float4` loads into registers before
   storing any, so a single thread holds up to 16 memory requests in flight. At 1395 MHz it delivers
   268.3 GB/s at unroll 1 and 281.9 at unroll 16 - a 5% spread across a 16x change in memory-level
   parallelism.

Methods 2 and 3 agree to within 0.25% (281.2 against 281.9 GB/s) from entirely different mechanisms
for raising memory-level parallelism. That is a hardware ceiling at roughly 54% of the bandwidth
available, not a defect in any one kernel.

**A DRAM-saturated workload at 1400 MHz is therefore not constructible on this part.** What sets the
281 GB/s ceiling is not identified: it is neither per-thread parallelism nor concurrency, and it sits
well below both the DRAM peak and any plausible instruction-issue bound. Naming it would require
hardware performance counters this study does not read.

#### 3.3.2 What limits `membw` is not one thing, and it moves with frequency - DRAFT

Section 5.7.3 identifies a third limiter, and taken together the three make a more honest picture
than "the memory-bound workload":

| regime | binding constraint |
|---|---|
| low core clock | SM instruction issue rate, and a ceiling near 281 GB/s that neither concurrency nor per-thread unrolling lifts (3.3.1) |
| mid core clock, flattened V/F curve | **the crossbar clock**, pinned because core voltage is pinned (5.7.3) |
| high core clock | DRAM bandwidth, at roughly 78% of the rated peak |

Only the last of these is what "bandwidth-bound" is normally taken to mean. A workload's identity as
memory-bound is therefore **frequency-dependent on this hardware**, and a study that assumes it holds
across a swept range is assuming something measurably false.

This matters for how the crossbar result should be read. It is not that a core-domain setting
mysteriously reaches into memory. The path from a streaming multiprocessor to a DRAM device is
mostly on-die logic - crossbar, L2 slices, memory controllers - and only its final stage, the PHY
and the GDDR devices themselves, sits in the memory clock domain. A "core" V/F curve governs the
rest of it. The measurements are consistent with the crossbar clock being derived from core voltage
rather than from the locked graphics clock: locking the graphics clock 32.8% higher while voltage is
held constant moves the crossbar 2.3%, whereas at stock the crossbar holds a near-constant 0.95
ratio to the graphics clock across the same range. The rail topology itself was not probed; what was
measured is the behaviour.

#### 3.3.3 The governing clock is invisible to standard telemetry - DRAFT

`nvidia-smi` exposes four clock domains - graphics, SM, memory and video - and on this device
graphics and SM report identical values. **There is no crossbar or fabric clock among them**, and
NVML's field-value interface does not supply one either (see 6, item 1). The clock that best predicts
`membw` throughput on a tuned card - elasticity 1.31, against 0.51 for the graphics clock - cannot be
read by the tooling that essentially every published GPU DVFS study relies on.

Every measurement of it here comes from HWiNFO, joined to the sweep by binning samples on the
graphics clock they were taken at. That is a workable method and it is also a reason this effect
could persist unnoticed in the literature: a study logging `nvidia-smi` telemetry on a card with a
modified V/F curve would record a clean frequency sweep and a well-behaved power curve, and would
have no column in which the actual limiter appears.

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

**The classifier has been tested against induced failures - DRAFT.** Until 2026-08-20 the logger
had only ever run on sessions that went well, so a tool that unconditionally reported `CLEAN` would
have been indistinguishable from a working one. Three 45-second cases were run: sustained load
throughout (reported `CLEAN`, 95% of samples loaded), an idle device (`INCONCLUSIVE`, 0% loaded),
and a load that stops a third of the way through (`INCONCLUSIVE`, 28% loaded). The positive control
is load-bearing: without it a classifier stuck on `INCONCLUSIVE` would have passed both failure
cases. The driver-reset detector also fired correctly for the first time, on an `nvlddmkm`
context-reset event induced by force-terminating a CUDA process. An actual hard lock remains
untested, and by construction can only be inferred from a truncated log.

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
| — as % of sustained max | 59% (of 2609 MHz) | 56% (of 2753 MHz) |
| Efficiency gain vs sustained max | **+63.1%** | **+50.1%** |
| Performance cost at optimum | −40.6% | **−9.8%** |
| Power saved at optimum | −63.6% | −39.9% |

**The V100 headroom result reproduces on consumer silicon.** The reference dataset gives a 44.4%
mean efficiency gain for a 13.7% performance cost and 40.1% power saving, with its optimum at 62%
of maximum (§5.1). The `membw` figures here — 41.6%, 11.3%, 37.4%, at 56% of sustained maximum —
are more favourable than that on two of four axes, on a 2025 consumer part measured
independently seven years and four
architectural generations later. This is the central empirical claim of the work: the efficiency
headroom identified on datacentre hardware is not an artefact of datacentre hardware.

**The compute/memory distinction appears in what the optimum costs, not where it sits.** Both
optima land on the same grid point, so at this resolution they are *indistinguishable* — which is
not the same as equal, and separating them requires a finer sweep around 1300–1800 MHz rather than
a wider one. What does separate cleanly is the price of operating there: `gemm` surrenders 40.6% of
its throughput to reach its optimum, `membw` only 9.8%. For bandwidth-bound work, running at 56%
of maximum clock is close to free — 37.4% less power for an 11.3% slowdown. For compute-bound work
it is a genuine trade. Any recommender built on this must therefore be workload-aware in its
*advice*, even where the optimal frequency itself is common.

Both curves are single-peaked with the optimum well inside the swept range, so these are interior
optima rather than artefacts of where the sweep stopped. One minor irregularity: `gemm` efficiency
at 1987 MHz (119.58 GFLOP/J) sits marginally below 2205 MHz (124.03), breaking monotonicity by 3.7%
— larger than the 0.6% the contaminated dataset showed for the same irregularity, and no
longer comfortably inside run-to-run variation. It is recorded as an open irregularity rather
than dismissed; a third pass over this region would settle whether it is structure or noise.

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

**This subsection uses the 2026-08-22 clean-protocol repeat**, matching §5.4. The 2026-08-16
originals are superseded and remain in the repository; `python analysis/compare_protocol.py`
reports what moved. Reproduce these fits with
`python analysis/analyze_fine_sweep.py --pattern "*fine-p*-rerun_sweep.csv" --bootstrap 5000`.

The coarse sweep placed both workloads' optima in the same 217 MHz bin, which is a statement about
grid resolution rather than about the hardware. Separating them required a design change, because
the obvious approach does not work.

**An efficiency curve is flat near its optimum by construction, so its argmax is largely noise.**
In the 13-point coarse run `gemm`'s peak stood only 3.4% above its nearer neighbour ±218 MHz away, while
the same run contained an unexplained 3.7% non-monotonicity between 1987 and 2205 MHz. On synthetic
curves with a known peak, this grid and realistic noise, the raw argmax moved **53–60 MHz between
identical passes**. Comparing two argmaxes would have compared two coin flips. The measured
repeatability under the clean protocol is median 1.25% for `gemm` (worst 2.65%) and 2.25% for
`membw` (worst 4.81%), driven by power rather than by throughput. Note the asymmetry: against the
contaminated 2026-08-16 passes `gemm` improved from 2.4% and `membw` got worse, from 1.7%. Removing
a background SM competitor helps the compute-bound workload and does little for the bandwidth-bound
one, which is consistent with §5.4.4 but is reported here as measured rather than as expected.

The design therefore: **13 points over 1200–1900 MHz, two passes per workload, run in the order
`gemm`, `membw`, `membw`, `gemm`**, with the optimum located by fitting the curve rather than by
selecting a point. Three choices carry weight.

*The band is wider than the peak.* A fit needs curvature to constrain a vertex; across 1300–1800 MHz
the curve falls only ~2% from peak, against 8–9% across 1200–1900 MHz. Tightening a fine sweep
around the peak buys frequency resolution and pays for it in signal.

*The order is counterbalanced.* Sweeps run ascending and the card warms over a ~30 minute session,
so run position is confounded with temperature. The ABBA order put each workload in one early and
one late slot. It worked: `gemm` ran at 47.5–53.5 °C then 44.0–50.8 °C, `membw` at 39.0–49.0 °C
then 45.9–52.0 °C,
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
| `gemm` pass 1 | 1467 MHz | 1446–1491 |
| `gemm` pass 2 | 1513 MHz | 1492–1536 |
| `membw` pass 1 | 1598 MHz | 1552–1636 |
| `membw` pass 2 | 1611 MHz | 1582–1633 |

The two `gemm` fits agree within 46 MHz and the two `membw` fits within 13 MHz, while the gap
between workloads is ~112 MHz — so the effect remains larger than the disagreement between
repeats of the same measurement, though by a narrower margin than the contaminated dataset
suggested. No footnote is needed here: unlike the 2026-08-16 passes, no point in either pass
was excluded.

Pooled: `gemm` **1492 MHz**, `membw` **1604 MHz**, difference **−112 MHz (95% CI −146 to −70)**. The interval excludes zero, so the optima do differ, and the bandwidth-bound workload prefers the higher clock.
All 52 points held their locked clock exactly, none overshot, and all 52 had power windowed to the
benchmark's timed region.

**There is no contamination in this dataset to be robust to, and that is checkable.** The
2026-08-16 measurement had one: a console-selection freeze (§5.4.2) interrupted `gemm` pass 1 at
its 1725 and 1785 MHz points, which read 7.0% and 4.5% below their pass-2 counterparts and
produced throughput *falling* as clock *rose* — physically impossible, and identifiable without
reference to the conclusion. That section reported a four-way sensitivity analysis showing the
effect surviving every way of handling those points.

The repeat was run headless, with no console attached, so the freeze could not occur. The data
confirms it did not:

| | 2026-08-16 | 2026-08-22 |
|---|---|---|
| worst pass-1 deficit against pass 2 | −7.0% at 1725 MHz | −2.2% at 1320 MHz |
| points where throughput falls as clock rises | 1 (pass 1, 1665→1725 MHz) | **none, either pass** |

The sensitivity table is therefore retired rather than recomputed: with no contaminated points
there is nothing to be sensitive to, and transcribing four variants of an analysis whose premise
no longer holds would be worse than dropping it. The check above replaces it.

For reference, on the 2026-08-16 data the contamination accounted for ~20 MHz of a ~150 MHz
effect, so it was never the source of the finding there either. The coarse sweep — a separate
run on a different grid — independently gives the same sign.

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
opposite order. At 1897 MHz the two passes recorded utilisation of **91.8% and 94.0%** — and
throughput of **350.2 and 350.3 GB/s**. At 1605 MHz, 91.6% and 91.7% utilisation gave 328.8 and
328.4 GB/s, the *lower*-utilisation pass being marginally faster. A two-point utilisation
difference with throughput identical to within 0.03% means the two are decoupled: whatever
`utilization.gpu` is varying over, it is not work.

**This leg of the argument is weaker than it was, and the reason is instructive.** Measured on
the contaminated 2026-08-16 dataset the same two passes read 99.0% and 92.7%, a six-point
spread, against 2.2 points here. The clean dataset shows both a lower absolute utilisation and
far less variation in it, which is consistent with §5.4.4: a background consumer inflates the
run-to-run scatter in this reading as well as depressing throughput. A smaller gap is less
striking evidence for decoupling, so the case now rests mainly on the launch-count experiment
below, which is a direct manipulation rather than an observation.

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

#### 5.4.4 Default-enabled capture software shifts the measured optimum

This subsection reports a contaminant that biased this study's own measurements, was not detected
for several weeks, and is not caught by the quiet-GPU check the sweep tool performs. It is reported
as a result rather than as a caveat because it moved a quantity this paper reports, not merely the
confidence in one.

**How it surfaced.** Two `gemm` sweeps run minutes apart on identical hardware settings disagreed by
5.5% at 1545 MHz and 5.5% at 1852 MHz while agreeing to 0.08% at the peak. Repeating a sweep that
had previously only ever been run once is what exposed it; no single run looked wrong.

**The controlled comparison.** NVIDIA Instant Replay is a continuous capture feature, enabled by
default with the NVIDIA app, which keeps a rolling buffer of recent gameplay. It has no window. Five
sweeps were run on one configuration in one session, three with it enabled and two with it disabled,
with nothing else changed:

| condition | peak `gemm` | spread |
|---|---|---|
| Instant Replay enabled | 17.97 / 17.98 / 17.99 TFLOP/s | 0.09% |
| Instant Replay disabled | 18.24 / 18.24 TFLOP/s | 0.04% |

The disabled condition is faster at all thirteen grid points. **The penalty is frequency-dependent:
4.22% mean across 1237-2010 MHz against 1.71% across 2167-3090 MHz.** The achieved clock is
unchanged - 2975.9, 2976.5 and 2977.1 MHz enabled against 2977.0 MHz disabled - so the card runs at
the same speed and only the share of it available to the measured workload differs. Power rises
along with throughput rather than falling, which is what removing a competitor looks like and not
what a faster card looks like. Temperature is excluded: the fastest run was also the warmest at the
affected points.

**It is a variance source as well as a bias, and that is the more damaging half.** Mean run-to-run
spread is 1.82% with the feature enabled against 0.35% with it disabled. At 1545 MHz the spread is
6.95% enabled against 0.13% disabled.

**It moves the reported optimum.** Because the penalty is larger at low frequency than at high, it
tilts the efficiency curve rather than shifting it uniformly, and curve shape is what this study
measures:

| | efficiency optimum | gain over the top grid point |
|---|---|---|
| Instant Replay enabled | 1395 MHz | +26.4% |
| Instant Replay disabled | 1545 MHz | +32.6% |

One full grid step of movement in the optimum, and 6.2 percentage points of the efficiency gain.

**Why a quiet-GPU check does not catch it.** Encode and decode execute on NVENC and NVDEC, engines
separate from the streaming multiprocessors, and `nvidia-smi`'s `utilization.gpu` reports neither.
On the machine used here the feature raised idle SM utilisation from 4.3% to 10.8%, which does cross
this study's 10% refusal threshold - but only incidentally, and a capture tool that sat quieter on
the SMs would pass unnoticed. The discriminating signal is `utilization.encoder`, which reads 0%
with the feature disabled and 21% with it enabled and nothing being recorded to screen. The sweep
tool now refuses to start on any encoder or decoder activity and records both in the session
metadata.

**The category, not the instance.** Always-on clip capture is common on the consumer hardware that
consumer DVFS measurements are made on: NVIDIA Instant Replay and ShadowPlay, the OBS replay buffer,
Discord and Steam recording, Xbox Game Bar, AMD ReLive. Any of these occupies the video engines
continuously while remaining invisible to a utilisation check and, in most cases, to the operator.

**What this does and does not support.** It is one feature, one card, one workload, one session. The
claim is that on this hardware a default-enabled capture feature shifted a measured efficiency
optimum by a grid step and its gain figure by 6.2 points, and that idle SM utilisation is an
insufficient precondition check. It is **not** a claim that any published dataset is affected: the
measurement conditions of those datasets are not documented, which is itself the point, and
asserting contamination without evidence would repeat the error corrected in section 2.
`gemm` renders nothing to the screen, so the capture feature has little new frame content to encode
during these measurements; the cost measured here is plausibly a floor rather than a typical case,
and a graphics workload was not tested.

**Consequence for this study.** The feature was enabled during every sweep in this paper predating
2026-08-22. Because it was enabled uniformly, comparisons between configurations retain their
direction and their large effects - the 29.6% bandwidth plateau of section 5.7.2 is six times the
contaminant. Absolute throughput figures from those runs are understated, and the optimum locations
and efficiency gains in sections 5.4 and 5.4.1 are subject to the shift demonstrated above. Those
sweeps are being repeated under the corrected protocol.

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

### 5.7 Separating the two tuning knobs - DRAFT, 2026-08-20

> **Draft.** Written the day the measurements were taken. Numbers are checked against the
> committed CSVs; prose and framing are not settled.

Every earlier consumer result treats "tuned" as one setting. It is two: a **memory overclock**
(+2500 MHz offset, 16301 against a 14001 rating) and a **core V/F curve** pinned flat near
3000 MHz at every voltage at and above ~925 mV. Three sweeps separate them - full tuned, memory
overclock only with the core curve reverted to stock, and stock - on the same card at identical
locked targets.

**The two knobs have opposite effects on the two workloads.**

| | memory overclock | core V/F curve |
|---|---|---|
| `gemm` (compute-bound) | nothing measurable, plus or minus 1% | the entire benefit: -17% to -28% power at matched clock, +12.1% sustainable ceiling |
| `membw` (bandwidth-bound) | the entire benefit: +3.6% to +16.1% over stock | actively harmful: up to -29.6% throughput across 1560-1867 MHz |

#### 5.7.1 The matched-frequency power reduction is entirely the core curve

Section 5.4 reports the tuned configuration drawing 17-28% less power than stock at identical core
clock on `gemm`, and attributes the efficiency gain to that rather than to the higher peak clock.
That was measured with both knobs applied and had not been separated. It survives separation:

**All three legs below are the 2026-08-22 clean-protocol runs, two sweeps per configuration,
averaged.** The originals were measured before the capture-software contamination of 5.4.4 was
known. Each configuration was confirmed applied before measuring rather than assumed: stock and
memory-only by the core clock collapsing to ~2610 MHz at a 3090 MHz target, tuned by it holding
2947.6 MHz, and memory-only additionally by memory reading 16301 MHz under load against stock's
13801 MHz - a memory overclock is invisible to a core-clock check. Measured cleanly the reduction
is 17-28% where the contaminated pair gave 18-26%, so the finding is slightly stronger than
published, not weaker.

| locked clock | tuned vs stock (power) | memory-only vs stock (power) |
|---|---|---|
| 1852 MHz | **-22.3%** | -0.2% |
| 2010 MHz | **-28.3%** | +1.1% |
| 2167 MHz | **-21.4%** | -0.1% |
| 2317 MHz | **-17.2%** | +1.6% |

Memory-only reproduces stock power to within 2%. That is tighter than the 3% the contaminated
pair showed, so cleaning the measurement sharpened this result rather than softening it.
Temperatures at these four points matched to within 0.6 C. Memory speed does nothing measurable for a compute-bound workload, which is the
sanity check this design should pass and does.

The curve additionally raises the sustainable ceiling: at stock and at memory-only the card cannot
hold the top three grid points, collapsing to ~2590 MHz and ~15.7 TFLOP/s, while with the curve it
holds 2948 MHz and reaches 17.61 TFLOP/s (+12.1%). The denominator is stock's own peak,
15.71 TFLOP/s at 2598 MHz. An earlier version of this sentence said +12.3%, which is the
comparison against stock's LAST grid point (15.68 at 2588 MHz) rather than its best, and
did not say so.

#### 5.7.2 The same curve costs a bandwidth-bound workload up to 29.6%

Across 1560-1867 MHz the fully tuned configuration runs `membw` flat at ~295 GB/s while stock rises
312 to 332 to 342. Five consecutive points sit inside a 1.3% band while core clock rises 20%.

Three mechanisms were eliminated before the curve was implicated. It is **not** contention from
concurrent monitoring - a repeat run with nothing else touching the device reproduces the plateau to
within 1%. It is **not** a memory downclock - memory-clock telemetry was added to the sweep tool for
this question and reads exactly 16301 MHz at every point, `min` equal to `max`. It is **not**
throttling - `clocks_throttle_reasons.active` was decoded across all runs and shows no power cap, no
thermal slowdown and no hardware slowdown, at 42-52 C.

Reverting only the core curve removes the plateau entirely; throughput becomes monotone, 291.8 GB/s
at 1402 MHz to 400.4 at 2100:

| locked clock | memory-only | full tuned | throughput delta | efficiency delta |
|---|---|---|---|---|
| ~1560 MHz | 323.0 | 294.1 | +9.8% | +8.8% |
| ~1710 MHz | 360.1 | 297.8 | +20.9% | +9.3% |
| ~1867 MHz | 385.7 | 297.5 | **+29.6%** | **+12.1%** |
| ~2025 MHz | 399.9 | 326.7 | +22.4% | +1.7% |

In this band the flattened curve costs more throughput than it saves power.

#### 5.7.3 Interpretation

At identical core clock and identical memory clock, the tuned configuration draws ~10% less power
and delivers ~20% less bandwidth. The remaining free variable is voltage. The working hypothesis is
that forcing the core clock into 1560-1867 MHz selects a voltage point *below* the curve's flattened
region, where the applied and stock curves diverge most, and that the memory controllers and
interconnect - which share the core voltage domain, unlike the DRAM devices themselves - become the
limiter. `gemm` is unaffected because at ~1365 FLOP per byte it is nowhere near saturating that path.

**This mechanism is now established by direct measurement - DRAFT.** NVML exposes neither core
voltage nor interconnect clock, but HWiNFO exposes both, and two further sweeps were run with it
logging alongside: one fully tuned, one at full stock.

| core MHz | stock volts | stock crossbar | crossbar/core | tuned volts | tuned crossbar | crossbar/core |
|---|---|---|---|---|---|---|
| 1402 | 0.720 | 1335 | 0.953 | 0.720 | 1320 | 0.942 |
| 1560 | 0.720 | 1470 | 0.947 | 0.720 | 1342 | 0.863 |
| 1710 | 0.760 | 1642 | 0.965 | 0.720 | 1342 | 0.788 |
| 1867 | 0.805 | 1815 | 0.976 | 0.720 | 1350 | 0.726 |
| 2025 | 0.840 | 1942 | 0.963 | 0.720 | 1470 | 0.729 |

Across the swept range stock core voltage rises 0.120 V while the tuned card's rises 0.020 V: the
flattened curve holds one voltage, as configured. The consequence is the crossbar clock - the
SM-to-memory-controller interconnect. At stock its ratio to core clock holds between 0.928 and
0.976. Under the flattened curve that ratio collapses from 0.942 to 0.726: the interconnect
decouples from the core and stops scaling.

Throughput follows the crossbar, not the core. On the tuned card, elasticity of `membw` throughput
to core clock is 0.51; to crossbar clock it is 1.31. Above the plateau a 14.4% crossbar increase
buys 14.1% more throughput.

The two configurations agree precisely where their voltages agree - at 1402 MHz both sit at 0.720 V
and both deliver ~282 GB/s - and diverge from 1635 MHz, the first point at which stock raises
voltage and the tuned card does not.

The chain is therefore: flattened curve, so pinned voltage, so pinned crossbar clock, so a
non-scaling path to memory, so a bandwidth plateau while DRAM itself is untouched at 16301 MHz.

**This also unifies 5.7.1 and 5.7.2, which had read as two unrelated findings.** They are one
intervention with one mechanism. `gemm`, at ~1365 FLOP per byte, never loads the crossbar hard
enough to care, so the pinned low voltage is pure benefit - the 18 to 26% power reduction at
matched clock. `membw`, at 0.167 FLOP per byte, lives on that path, so the same pinned voltage is
pure cost. The undervolt's benefit and its harm are the same mechanism observed through two
workloads.

The practical consequence is that a profile tuned at the top of the V/F curve - the region a card
actually occupies in normal use - can be badly wrong in the mid-range, which is precisely where a
DVFS efficiency optimum is looked for. **There is no single tuned configuration that is right for
both workloads.** This is the section 5.6 result one level up: not only is the efficiency-optimal
frequency workload-dependent, so is the efficiency-optimal hardware configuration, and by a
considerably larger margin.

#### 5.7.4 A repair derived from the mechanism, and confirmed - DRAFT

> ⚠️ **Every measurement in this subsection and in 5.7.5 predates the capture-software finding of
> 5.4.4 and has no clean counterpart.** All four curve-fixed sweeps were taken on 2026-08-20/21
> with NVIDIA Instant Replay almost certainly running, while 5.4, 5.4.1, 5.7.1 and 5.7.6 were all
> re-measured clean on 2026-08-22. The magnitudes below are therefore expected to understate the
> repair, in the same direction and by roughly the same amount as everywhere else. **The
> qualitative findings were re-tested on 2026-08-23 and hold - see the confirmation at the end of
> this subsection.** The specific curve could not be re-measured: it was drawn by hand and never
> saved to a profile.

If the account in 5.7.3 is correct, the repair follows from it: leave the flattened region above
~925 mV intact and restore the stock voltage slope below it. A sixth sweep tested exactly that, on
the full 13-point grid with the memory overclock retained, with four outcomes stated in advance.

Voltage now rises where it had been pinned - 0.720 V at 1545 MHz through 0.840 V at 2010, against a
flat 0.720 V on the tuned card - and the crossbar-to-core ratio returns to 0.939-0.967 from 0.726.
The plateau disappears, and throughput lands on the memory-only curve: 383.2 GB/s at 1852 MHz
against the tuned profile's 294.5, **+30.1%**. The top end is unaffected: 411.8 GB/s peak against
the tuned 414.3, a 0.6% difference, with HWiNFO polling during this run and not the tuned one, so
the gap is if anything overstated.

For `membw` the repaired curve therefore dominates the fully tuned one at every point on the grid,
while remaining more efficient than either alternative across most of the range and drawing less
power at peak (79.4 W against 82.4 W at 2932 MHz).

This is the strongest evidence in this study that the mechanism is understood rather than merely
described. The intervention was derived from the diagnosis, its outcome was predicted before the
measurement, and it behaved as predicted at both ends of a range where the two configurations were
expected to differ in opposite directions.

**The predicted cost was then measured, and it is real.** Restoring stock voltage below the
flattened region should restore roughly stock power on `gemm`, giving up the 17-28%
matched-frequency saving of 5.7.1. That prediction was stated before the run and is confirmed in
5.7.5, which is why this section is titled a repair rather than an improvement.

**Confirmed on a second, independently drawn curve, 2026-08-23.** The original profile was never
saved, so it was rebuilt by hand from the design rather than restored - stock voltage slope below
~925 mV, flattened region above it intact, memory +2500 - and deliberately altered slightly. It is
a different curve: probed at a locked 3090 target it reads 2906.1 MHz on `gemm` against the
2026-08-20 runs' 2887.1 and 2898.5, and 2947.0 on `membw` against 2909.9.

**That makes it a better test than a replay would have been.** A bit-identical re-measurement
would only have shown the numbers were reproducible; an independently redrawn curve of the same
design tests whether the effect belongs to the mechanism or to one particular hand-drawn shape.

Measured on the same 10-point 1400-2100 MHz grid as the clean tuned and split-curve runs, so all
three are clean-protocol and directly comparable, with achieved clocks matched to **6.6 MHz in the
worst case and under 3 MHz at most points**:

| | vs full tuned | worst point |
|---|---|---|
| `membw` throughput | **+2.3% to +31.4%** | +31.4% at 1867 MHz |
| `membw` efficiency, 1402-1867 MHz | **+4.0% to +10.4%** | |

The plateau removal reproduces. The contaminated 2026-08-20 measurement gave +30.1% at 1852 MHz;
the clean, independently drawn curve gives **+31.4% at 1867 MHz** against a clean tuned reference.
Power behaves as 5.7.3 predicts: at matched clock the repaired curve draws **more** power than the
tuned one - 66.1 W against 52.4 W at 1867 MHz - because the restored voltage slope is what
un-starves the crossbar. The trade of 5.7.5 also reproduces: above 2010 MHz the tuned curve is
back ahead on efficiency, by 4.4% at 2025 and 6.0% at 2100 MHz.

**Against the split curve of 5.7.6, on `membw`, the repair wins throughput at all ten points** by
+1.6% to +7.7%. On efficiency it is closer and mixed - the repair leads at seven of ten points, the
split curve at 1867 and 1942 MHz. This does not change 5.7.6's conclusion about `gemm`, where the
split curve remains ahead and the repair gives up the compute advantage entirely.

#### 5.7.5 The repair is a trade, not a win

The repaired curve was swept on `gemm` twice, on the same 13-point grid, with HWiNFO logging
throughout. The first run is discarded at one point: under an 1852 MHz target the card ran at
2854.6 MHz and 151.6 W, an overshoot of +1002.6 MHz, which is the failure mode the sweep tool's own
comments describe - something outside `nvidia-smi` owning the V/F curve and the cap never being
applied. The tool flagged it. All numbers below are from the second run, where every point below
2782 MHz held its lock.

**The predicted loss is confirmed.** Matched-clock power returns to stock:

| locked clock | tuned vs stock | repaired vs stock |
|---|---|---|
| 1852 MHz | **-18.1%** | +1.7% |
| 2010 MHz | **-26.4%** | +0.2% |
| 2167 MHz | **-19.9%** | +1.8% |
| 2317 MHz | **-18.1%** | +1.2% |

Within 2% of stock at every point, against the tuned card's 18-26% saving. This is the same
signature the memory-only configuration produced in 5.7.1, and for the same reason: with the
sub-925 mV slope restored, the card sits at approximately stock voltage in this band.

**The loss extends well beyond those four points.** On efficiency the tuned curve beats the
repaired one across the entire mid-range, not just where power was matched:

| locked clock | tuned TFLOP/W | repaired TFLOP/W | tuned advantage |
|---|---|---|---|
| 1237 MHz | 0.1266 | 0.1284 | -1.4% |
| 1395 MHz | 0.1354 | 0.1365 | -0.8% |
| 1545 MHz | 0.1415 | 0.1375 | +2.9% |
| 1702 MHz | 0.1476 | 0.1344 | +9.8% |
| 1852 MHz | 0.1513 | 0.1242 | **+21.8%** |
| 2010 MHz | 0.1533 | 0.1152 | **+33.1%** |
| 2167 MHz | 0.1442 | 0.1123 | **+28.4%** |
| 2317 MHz | 0.1361 | 0.1114 | +22.2% |
| 2475 MHz | 0.1219 | 0.1079 | +13.0% |
| 2625 MHz | 0.1193 | 0.1085 | +9.9% |
| 2782 MHz | 0.1147 | 0.1089 | +5.4% |
| 2932 MHz | 0.1057 | 0.1078 | -1.9% |
| 3090 MHz | 0.1059 | 0.1075 | -1.4% |

The tuned curve is ahead at every point from 1545 through 2782 MHz, by up to 33.1%, and behind only
at the two lowest targets and the two highest. **The band it wins is the band that matters**: the
`gemm` efficiency optimum sits at 2010 MHz under the tuned curve, which is exactly where the gap is
widest.

At peak throughput the ranking inverts, and reporting only that would misrepresent the result. The
repaired curve reaches 16.82 TFLOP/s at 2898 MHz drawing 156.5 W, against the tuned card's 17.61 at
2948 MHz drawing 166.3 W - 4.5% less throughput for 5.9% less power, so 1.5% better efficiency at
that one point. Both beat stock, which cannot hold anything above ~2590 MHz and peaks at 15.71.

**Neither configuration dominates the other.** For `membw` the repaired curve wins at every point on
the grid (5.7.4); for `gemm` the tuned curve wins across the whole mid-range. The undervolt's
benefit and its harm are one mechanism (5.7.3), so removing the harm removes the benefit. This is
the 5.6 result one level up, and the stronger form of it: not only is the efficiency-optimal
*frequency* workload-dependent, so is the efficiency-optimal *hardware configuration*, and no
setting of this knob is right for both workloads at once.

##### The 2898 MHz ceiling is probably a voltage shortfall, not a cost of the repair

The repaired curve tops out 50 MHz below the tuned card, and this was recorded as unexplained. The
voltage telemetry gives a mundane candidate. **Both curve variants measure 0.895 V at every target
from 2625 MHz upward** - the first on its `membw` sweep, the second on this `gemm` sweep, since the
first `gemm` run was not voltage-logged. The two readings are identical to the millivolt, despite
the second curve having been redrawn specifically to raise the top point by roughly 10 mV. That
raise does not appear in the telemetry at all, on either workload.

The tuned card's top voltage was never measured. HWiNFO was not running during its `gemm` sweep, and
the two voltage-logged runs on that configuration cover only 1402-2100 MHz. The Afterburner curve
editor showed 0.925 V, which is a setting that was read off a screen, not a measurement. If it is
right, the repaired curve is running 30 mV short at the top, which is sufficient on its own to
explain a 50 MHz deficit and requires no inherent cost of the repair.

Two observations support that reading over an inherent-cost one. `membw` under the same repaired
curve lost only 0.6% at its peak, which does not fit a story where the repair caps the top of the
range. And no run of either configuration reports a hardware-slowdown, thermal or power-brake
throttle bit at any point; `SwPowerCap` appears intermittently on both and stock reports no reason
at all while still collapsing to ~2590 MHz. The ceiling is set by the curve, not by the card
protecting itself.

**That prediction was tested on 2026-08-21, and it is wrong.** The repaired curve's top point was
raised to 0.925 V and `gemm` re-run on the same grid. The ceiling did not rise: it fell, from
2898.5 MHz to 2876.6 MHz, 21.9 MHz in the wrong direction. Locking the curve flat at 925 mV
changed nothing further. HWiNFO shows 0.925 V requested delivering 0.920 V under roughly 170 W of
load, so the raise did reach the card - the 5 mV shortfall is ordinary vdroop, not a missing
voltage bin - and the card simply does not clock higher for it.

Peak throughput did improve slightly, to 16.90 TFLOP/s from 16.82, which narrows the deficit
against the tuned card's 17.61 TFLOP/s from -4.5% to -4.0%. The frequency gap is unchanged in
character: 2876.6 MHz against 2948.1 MHz, a shortfall of 71.5 MHz.

**The deficit is therefore real, reproducible, and unexplained.** Voltage is eliminated by this
sweep; thermals, power limit and throttle state were eliminated earlier. It is recorded here as an
open question rather than closed with a second guess, and it is still not used to argue anything
about the repair. What the failed prediction does establish is that the 0.895 V reading was not a
setting that failed to apply, which had been the reason for doubting the telemetry at the top of
the range.

#### 5.7.6 A split-region curve, derived from the mechanism, recovers both

Sections 5.7.4 and 5.7.5 describe a repair that removed the bandwidth penalty and gave up the
compute advantage with it, because the two share a mechanism. That framing suggests a third option
the earlier sections did not test: if the harm comes from pinned voltage *below* the flattened
region and the benefit comes from the flattened region *itself*, the two can be separated by
frequency rather than traded against each other.

**The design follows directly from 5.7.3.** Restore the stock voltage slope below ~845 mV, so the
crossbar clock scales with the core and the bandwidth-bound workload is not starved. Keep the
tuned flat shape from 850 to 920 mV, where `gemm` lives at its ceiling and the pinned low voltage
is pure benefit. Set the top point to 920 mV at 3000 MHz. Memory remains at +2500.

**On `gemm` the split curve wins, and the two configurations do not overlap.** Eight sweeps under
the clean protocol of 5.4.4, five on the tuned configuration and three on the split curve, each
with both axes of the configuration confirmed before measuring:

| configuration | peak `gemm` runs | mean | spread |
|---|---|---|---|
| original tune, n=5 | 17.98 / 17.88 / 18.02 / 17.98 / 17.93 | 17.96 TFLOP/s | 0.76% |
| **split curve, n=3** | **18.24 / 18.24 / 18.22** | **18.23 TFLOP/s** | **0.13%** |

The gap is **+1.53%**, and the lowest split-curve run exceeds the highest tuned run — 18.22 against
18.02 — so the split curve wins on every pairwise comparison the data admits. That statement does
not depend on averaging, which matters at these sample sizes. All three split runs peaked at 2977.0
MHz achieved, against the tuned card's 2946-2948 MHz.

**The split curve is also the steadier of the two**, 0.13% spread against 0.76%, a factor of 4.5 on
standard deviation. This reverses a concern carried through the earlier sections: the split curve
had been suspected of instability on the strength of a ~2.5% low outlier appearing in roughly one
`gemm` run in three. That outlier was the capture software of 5.4.4. With the contaminant removed
the configuration producing the best throughput is also the more reproducible one, and the
remaining run-to-run variation belongs to the original tune.

**On `membw` the split curve holds the repair.** Against the memory-overclock-only configuration,
which is the ceiling for this workload because it carries no core curve at all, the split curve
lands within 0.4% at seven of ten grid points and beats the fully tuned profile everywhere, by
+3.2% at 1402 MHz rising to +30.0% at 1867 MHz. The plateau of 5.7.2 does not appear.

> ⚠️ **The "ceiling" in that sentence is a contaminated reference, and the agreement with it is
> probably an artefact.** The memory-only sweep is from 2026-08-20, before the capture-software
> finding of 5.4.4; the split-curve sweep is clean 2026-08-22 data. Comparing the two flatters the
> split curve by roughly the size of the contamination. The seven-of-ten figure reproduces exactly
> as written and is not a transcription error - but on 2026-08-23 the independently rebuilt
> repaired curve, measured clean on the same grid, **exceeded the same memory-only reference at
> all ten points, by +1.80% to +5.15%, mean +2.89%.** Nothing should beat a ceiling. That margin
> sits inside the +4.22% mid-band cost 5.4.4 measured for Instant Replay, so the most economical
> explanation is that the memory-only reference reads low rather than that two configurations
> both exceed it.
>
> **What this costs the claim:** the split curve is probably somewhat BELOW the true clean ceiling
> rather than at it, and by an unknown amount. Settling it needs one clean memory-only sweep on
> the 1400-2100 grid, which is about five minutes plus an Afterburner change. Until then, read
> "holds the repair" as directional and do not quote the 0.4%.

**What it does not recover.** The tuned curve still wins `gemm` efficiency across 1545-2625 MHz, by
up to 30.5% at 2010 MHz, which is where that workload's efficiency optimum sits. The split curve
buys peak throughput and bandwidth scaling; it does not buy back the matched-frequency power
advantage, and 5.7.5's conclusion that no single configuration dominates survives this section
rather than being overturned by it. What the split curve changes is the *shape* of the trade, not
its existence.

**It survived thirty minutes of sustained load, which is the first such test in this work.** Under
the protocol of the appendix - fifteen minutes of `gemm` then fifteen of `membw`, unlocked clocks,
96.9% of one-second samples above 50% utilisation - the configuration recorded no driver reset, no
throttled sample and no aborted iteration. Post-soak throughput did not fall: `gemm` drifted
**-0.11%** and `membw` **+0.16%** between the first and last quarter of their post-soak iterations,
both of which are improvements or noise rather than degradation. Power averaged 140.2 W and peaked
at 196.1 W against a 200 W limit; temperature peaked at 79 C.

That drift figure is the part that matters, and it is not a crash test. GDDR7 corrects errors
silently, so a memory overclock can run for hours without a crash, an artifact or an event-log
entry while being net slower than stock. Measuring throughput continuously is the only way to see
that, and over thirty minutes there is no sign of it here.

**The original tune was then put through the same test, forty minutes later on the same card, and
also passed** - 33 iterations, zero aborted, zero driver resets, zero throttled samples, 96.8%
loaded, drift `gemm` +0.10% and `membw` -0.28%. Two results follow from having both.

**The throughput gap reproduces under a completely different protocol.** Post-soak means over
eleven unlocked iterations each give `gemm` 18.24 TFLOP/s on the split curve against 17.98 on the
original tune, a gap of **+1.45%**. The +1.53% of the table above came from peak values in locked
thirteen-point sweeps. Two measurement designs that share no methodology - locked against unlocked,
peak-of-sweep against sustained mean, minutes apart against days apart - agree to within 0.08
percentage points. That is a stronger corroboration of the gap than either measurement alone.

**The `membw` advantage does not appear at all**, and this is the more practically important of
the two. Under sustained unlocked load the two configurations are indistinguishable on `membw`:
423.1 GB/s against 424.6, a difference of -0.35% and in the wrong direction to matter. This does
not contradict 5.7.2, it locates it. The plateau is a property of the **1402-1867 MHz band**,
where the flattened curve pins voltage and starves the crossbar; a card left to boost freely sits
at 2968-2993 MHz, above the flattened region entirely, where both curves carry the same voltage.
The harm is real and reproducible when frequency is locked into that band, and absent when it is
not. Anyone reading 5.7.2's "-29.6%" as a cost they would pay in ordinary use would be wrong.

**Neither run distinguishes the two configurations on steadiness.** All four drift figures fall
between -0.28% and +0.16%, in both directions, which is noise. The 4.5x reproducibility advantage
reported above is a spread across *separate sweeps*, not drift *within* a run, and these are
different quantities - so this does not overturn it. What it does say is that whatever produces
the original tune's wider run-to-run spread is not visible as degradation inside a single
half-hour of sustained load, which narrows where to look for it.

**Limits.** n=1 chip, one curve shape, and **one thirty-minute run**. The correct reading is "no
failure observed in thirty minutes", not "stable": undervolt failures routinely take hours to
appear, and a single session says nothing about thermal cycling, cold boots, or the driver updates
this configuration will meet in normal use. The degradation threshold the run was judged against is
uncalibrated - it was set at 2% before anybody knew what healthy drift looks like, and this run
suggests that is loose by an order of magnitude. The sub-845 mV region was also reshaped by hand
rather than by any principled optimisation. How much of the stock slope can be given back before
the crossbar starves is unmapped; only the two endpoints have been measured.

#### 5.7.7 Caveats

The three configurations were **not** measured contemporaneously: stock at 14:33 on 2026-08-19, full
tuned at 20:42 the same day, memory-only at 18:13 the next - switching configurations requires a
manual Afterburner change that cannot be scripted here. Idle temperature was 40-42 C at the start of
each, the only cross-run control available. Effect sizes up to 29.6% are far outside plausible
day-to-day drift so the direction is safe, but the precise percentages are softer than they look.
n = 1 chip, one profile. Two `gemm` points outside the comparison band (2475 and 2625 MHz) show
memory-only drawing 5.8% and 6.6% more power than stock with only 1.2 and 2.1 C to account for it;
this is unexplained and recorded rather than trimmed.

---

---

## 6. Limitations

1. **Voltage is measured, but thinly, and not through the vendor API.** NVML does not expose it:
   `nvidia-smi` has no voltage field, and an exhaustive scan of NVML field IDs 1-259 via
   `nvmlDeviceGetFieldValues` returns 44 readable fields, none of them a core voltage at any scale.
   That scan also confirms the fields it *does* return are correct - IDs 185/186 give instantaneous
   and average power in milliwatts, and 187-192 give the power limits (150/180/200 W), matching both
   `nvidia-smi` and third-party tools. Earlier drafts asserted "no documented API exposes it" without
   testing; this is verified for NVML specifically.

   HWiNFO64 does read core voltage and the crossbar clock on this device, and an earlier version of
   this limitation named joining that log to a sweep as the highest-value outstanding experiment in
   the study. **That join was built and run, and the mechanism in 5.7.3 is a measurement rather
   than an inference.** The joining tool is `tools/frequency-sweep/join_hwinfo_voltage.py`; it bins
   samples by the core clock they were taken at rather than by timestamp, because the sweep CSV
   records durations per point and not absolute times.

   What remains limited is the coverage and the conditions, and those bound the voltage claims:

   - **The voltage-logged runs cover 1402-2100 MHz.** The tuned card's voltage at the top of its
     range was never measured, so statements about the top point rest on the Afterburner editor
     rather than on telemetry.
   - **HWiNFO polls throughout**, which is the class of contention this study has already been
     burned by, so throughput from a voltage-logged run is not quoted as a clean measurement.
   - **Idle samples must be excluded or the result inverts.** HWiNFO samples through the settle
     gaps and an idle card sits at boost voltage, so the join discards samples below 30 W. That
     threshold is a judgment call; it is the parameter this result is most sensitive to, and it is
     covered by tests for exactly that reason.
   - **One source log no longer exists.** HWiNFO reuses a single log filename, and the log for the
     `curvefixed-membw` run was overwritten by a later capture, so its committed distilled extract
     is now the only record and cannot be regenerated.
   - **N = 1 chip**, one set of curves.
2. **Small, heterogeneous sample.** Access is limited to roughly one machine every 2–3 weeks, mostly
   different models rather than repeats, which bounds any claim about chip-to-chip variation.
3. **Single vendor, recent architecture.** NVIDIA only; no AMD or Intel measurements.
4. **Power is a device-side estimate**, boxcar-averaged, not an external measurement [5].
5. **Stability windows are short.** Ten minutes is not proof of stability.
6. **Reference-dataset results are single-device.** The 44.4% figure is one V100; it is not a
   population estimate.
7. **The memory-bound workload is not memory-bound over most of the swept range.** `membw` is
   issue-limited below roughly 2000 MHz on this device, and no constructible kernel saturates DRAM
   there (3.3.1). Consumer results that depend on a workload being bandwidth-limited hold only near
   the top of the range.
8. **Tuning configurations were not measured contemporaneously.** The stock, fully tuned and
   memory-only sweeps of 5.7 are separated by hours to a day, because switching between them
   requires a manual change that cannot be scripted (5.7.7).

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
