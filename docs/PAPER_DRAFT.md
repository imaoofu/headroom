# Headroom — paper draft

> **Status: Related Work and Methods are drafted. Results are a skeleton — no original data has
> been collected yet.** Every number below that is not marked `[PENDING]` traces to something
> actually run or actually read. Placeholders are marked rather than filled with plausible values.
>
> Citation reliability is flagged per entry in [References](#references). Anything marked
> ⚠️ needs the primary source opened before it appears in a submitted version.

---

## 1. Introduction

*(Draft after Results exist — the framing depends on what the data shows. Skeleton only.)*

The argument, in order:

1. GPUs ship with conservative default voltage-frequency behaviour, because vendor defaults must
   be stable across millions of unknown units, in unknown thermal environments, for years.
2. That conservatism leaves measurable efficiency on the table. Prior work quantifies it as a
   voltage guardband of roughly 20% ⚠️.
3. This is well studied on **datacenter** hardware. It is poorly studied on **consumer** hardware,
   and — as this work shows in §3.3 — the public consumer datasets that do exist sweep a frequency
   range that structurally cannot locate an efficiency optimum.
4. This work measures the frequency-efficiency relationship on consumer GPUs across a range that
   includes the optimum, releases the data openly, and asks whether the optimum is chip-specific
   enough to justify per-chip measurement.

**Contribution claim, stated narrowly and defensibly:**

- An open, reproducible dataset of consumer-GPU frequency-power-performance measurements across a
  range that includes the efficiency optimum.
- A demonstration that existing public consumer DVFS datasets sweep at or above stock and therefore
  cannot answer efficiency-optimum questions.
- An evaluation of whether per-unit prediction beats a fixed-frequency policy, reported honestly
  including when it does not.

**Explicitly NOT claimed:** that this outperforms vendor boost algorithms, which already account
for per-chip factory binning; or that the existence of a guardband is a new discovery.

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

Vendors set operating points with margin for worst-case silicon, temperature, and ageing. Studies
that characterise this margin report a voltage guardband on the order of 20% of nominal, with
elimination yielding up to roughly 25% energy savings ⚠️. Related work on minimum-operating-voltage
(Vmin) characterisation quantifies core-to-core and chip-to-chip variation and shows guardband is
partly *program-dependent* rather than a single per-chip constant ⚠️.

Chip-to-chip variation is itself measurable at the system level: one characterisation of a GPU
cluster reported an overall frequency variation of about 140 MHz (~11%) between nominally identical
units, and up to a 10% performance difference at matched temperature ⚠️. Consumer-facing exposure of
this variation has been limited and short-lived — GPU-Z's "ASIC quality" reading surfaced
leakage-based binning for a period before being deprecated as unreliable.

**Positioning.** The existence and approximate size of the guardband is therefore *established*, not
novel. What this work adds is open measurement on current consumer parts, across a range that
includes the optimum, with released data.

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
  iteration). Bandwidth-bound; comparatively insensitive to core clock.

Both perform identical arithmetic on every invocation, so wall-clock duration is a valid performance
metric and efficiency follows as work ÷ (duration × power).

Iteration counts are fixed per workload (120 for `gemm`, 600 for `membw`), sized for approximately
15 s at full boost, and **held constant across every frequency in a sweep**. Preliminary runs at 30
iterations completed in 0.7–4.1 s, which proved too short for the device to reach steady clock and
thermal state and left kernel-launch overhead visible in throughput.

### 3.4 Measurement protocol

For each target frequency:

1. Lock the core clock (`nvidia-smi -lgc`) and verify the lock held; readings drifting more than
   30 MHz from target are flagged.
2. Wait 8 s for the device to settle.
3. Launch the benchmark as a separate process and **sample telemetry concurrently at 1 Hz while it
   runs**, recording SM clock, memory clock, power, temperature, utilisation, and the decoded
   throttle-reason bitmask.
4. On completion, record the benchmark's internally-timed duration, which excludes process startup
   and CUDA initialisation.
5. Reset clocks (`nvidia-smi -rgc`) in a `finally` block that executes on every exit path, including
   interrupt, and verify the reset took effect.

Concurrent sampling is essential rather than incidental: an earlier implementation sampled after the
workload completed and therefore recorded **idle** power at every frequency — a defect that produces
a plausible-looking but meaningless dataset.

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

`[PENDING — no original data collected]`

### 5.5 Cross-chip variation

`[PENDING — requires multiple units]`

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

**Verified** — opened and confirmed:

- [3] Maliakel, Ilager, Brandic. *Characterizing LLM Inference Energy-Performance Tradeoffs across
  Workloads and GPU Scaling.* arXiv:2501.08219.
- [5] Yang et al. *Accurate and Convenient Energy Measurements for GPUs: A Detailed Study of NVIDIA
  GPU's Built-in Power Sensor.* 2024. Code: `github.com/JimZeyuYang/GPU_Power_Benchmark`
- [6] GPU-DVFS-Dataset. `github.com/zyjopensource/GPU-DVFS-Dataset`
- [7] HKBU-HPML DVFS datasets. `github.com/HKBU-HPML/GPU-DVFS-Job-Schedule`,
  `github.com/HKBU-HPML/NV-DVFS-Benchmark`

**⚠️ Located but not yet read in full** — open the primary source before submission:

- [1] Guerreiro et al. *Predictable GPUs Frequency Scaling for Energy and Performance.* ICPP 2019.
  DOI 10.1145/3337821.3337833
- [2] *Accurate Energy and Performance Prediction for Frequency-Scaled GPU Kernels.* MDPI
  Computation 8(2):37.
- [4] Measurement studies of GPU DVFS energy conservation (multiple; consolidate to one citation).
- Voltage guardband characterisation (~20% guardband, ~25% savings) — **specific citation still
  needed.** Currently second-hand; do not cite until the primary paper is read.
- *Not All GPUs Are Created Equal: Characterizing Variability* — 140 MHz / ~11% figure needs
  first-hand confirmation.
- Rodinia benchmark suite. IISWC 2009.
