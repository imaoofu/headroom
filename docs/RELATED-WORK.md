# Related work — the index

**One place for every source this project has found, with a link, what it actually says, and what
it bears on.** Built 2026-09-13 after the ridge-point retraction, by consolidating the paper's
reference list with the prior-art sweep in [`PRIOR-ART-20260912.md`](PRIOR-ART-20260912.md).

🛑 **Read status is part of the citation.** Every entry says whether the primary source was opened.
This project has written **four** wrong figures from second-hand summaries — see the corrections at
the bottom — so an unread source is marked unread and is never cited for a number.

✅ **As of 2026-09-13 every source that bounds a novelty claim has been read in full.** The two that
blocked automated fetching, HotPower 2013 and the 2017 survey, were the two that mattered most: one
partially pre-empted the causal claim, the other closed the consumer claim outright. ⚠️ **A 403 is
not a dead end — HotPower needed a browser and the survey was on arXiv all along.**

📄 **Local PDFs go in [`papers/`](papers/), which is gitignored.** Copies are not redistributed
here; the links below are how you get them back.

---

## 1. The sources that bound this project's novelty

These four decide what can and cannot be claimed. Read these before writing any contribution
statement.

### ⛔ Schoonhoven et al. — the ridge point. **THE retraction source.**
*Going green: optimizing GPUs for energy efficiency through model-steered auto-tuning* (Kernel
Tuner). arXiv **[2211.07260](https://arxiv.org/abs/2211.07260)**, 2022. **Read in full.**

Defines the **ridge point**: the frequency at which core voltage stops being constant and begins
rising. States the consequence this project had believed was its own finding:

> "Reducing the clock frequency beyond the ridge point does not make the GPU more energy efficient,
> as performance drops with f while v is constant below the ridge point."

A100 ridge 1025 MHz (70% of peak), RTX A4000 1290 MHz (72%); predicted energy-optimal clocks 985
and 1298 MHz. **Datacenter and workstation only — no consumer parts.**

### ⛔ Mei, Wang, Chu — the 2017 survey. **Closes the last narrow form of the consumer claim.**
*A Survey and Measurement Study of GPU DVFS on Energy Conservation.* Digital Communications and
Networks, 2017. ScienceDirect returns 403 — **the arXiv version is open:
[arXiv:1610.01784](https://arxiv.org/abs/1610.01784)**. **Read in full 2026-09-13**, local copy
`papers/mei-2017-survey-gpu-dvfs.pdf`.

**This was the last unread source on the list and the one flagged as the biggest remaining risk.
It was the right thing to worry about.**

| | |
|---|---|
| Hardware | **ASUS Strix GeForce GTX 980 (Maxwell, consumer)** and the GTX 560 Ti (Fermi) |
| Maxwell sweep | core **480 → 1080 MHz against a 950 MHz default**, i.e. down to **51% of default** |
| Maxwell voltage | **held FIXED at the 0.987 V lower bound** of P2 while frequency is swept — DFS, not DVFS |
| 🔑 Power scope | **GPU-level, from the on-chip power sensors** — *"the R̂ and Rmax for the Maxwell refer to the GPU energy savings only"*. The Fermi numbers are whole-system, and the paper says so explicitly |
| Benchmarks | the same 37 applications, CUDA SDK 6.5 + Rodinia, ≥20 min per kernel, 95% CI |

🛑 **The finding that matters:**

> *"Among all the kernels, **12 benefit from scaling up the core frequency** (f_Gc > 950 MHz) while
> **the other 30 benefit from scaling down** the core frequency (f_Gc < 950 MHz). In particular,
> half of the kernels achieve their minimum energy at core frequencies **between 680 MHz and
> 880 MHz**, where 11 of them at 780 MHz."*

and

> *"for modern GPUs, **scaling down the core frequency to some extent is an effective approach to
> conserving energy**, even if it is difficult to scale down the core voltage."*

⛔ **That is a board-level, below-default, per-kernel efficiency optimum on a GeForce card, in
2017.** The narrow survivor this project was still claiming — *"no study locates a ridge-point-style
optimum via a full sweep on GeForce silicon at board level"* — **is gone.** Average R̂ 5.24%, average
Rmax 10.87%, best case (nn) 34% of GPU energy.

⚠️ **Do NOT compare 5.24% to this project's 44.4%.** Their R̂ is energy saved against the **default
clock**; the headroom gap here is efficiency gain against the **sustained maximum**. Different
baseline and different quantity.

✅ **What it does NOT do, and this is all that is left:** voltage is **held constant** throughout the
Maxwell experiment. They never reshape a V/F curve, never move a floor, and never show an optimum
relocate as a consequence. Claim A stands.

🔑 **It also corroborates two things this project measured independently.** Figure 6 reports the
maximum-stable-frequency-versus-voltage relationship as **sublinear** on both Fermi and Maxwell —
the same frontier shape as HotPower's Figure 3. And their memory result matches the shape of §5.7:
24 kernels lose >30% energy when memory frequency drops 30%, and **34 of 42 kernels have their
minimum energy at the vendor's default memory setting**.

### ⛔ Mei, Yung, Zhao, Chu — HotPower 2013. **Partially pre-empts the causal claim.**
*A Measurement Study of GPU DVFS on Energy Conservation.* HotPower '13, HKBU.
[comp.hkbu.edu.hk/~chxw/papers/hotpower_2013.pdf](https://www.comp.hkbu.edu.hk/~chxw/papers/hotpower_2013.pdf)
— **read in full 2026-09-13** (fetch returns 403; PDF supplied by the operator, scanned, no text
layer).

One **GTX 560 Ti**, 37 benchmarks, fcore 480–880 MHz at fixed 1.049 V and 0.849 V, **whole-system
energy at the wall** against an 85 W idle floor of which 29 W is the card. Tools: NVIDIA Inspector
1.9.7.1 + **MSI Afterburner 2.3.0**. Headline 18.91% energy for 3.45% performance at 0.849 V /
880 MHz.

🔑 **The sentence that matters:** *"for Kmeans, scaling down f_core can save energy when
V_core = 1.049 V, but this situation does not hold anymore when V_core = 0.849 V."* Change the
voltage and the energy-optimal frequency changes with it — 2013, consumer GPU, Afterburner.

⚠️ **Its frequency result runs opposite to ours** (only 5 of 37 apps benefit from lower fcore)
**because it measures system energy, not board power.** Never cite it against low-frequency
headroom.

### ✅ Zamani, Tripathy, Bhuyan, Chen — SAOU. **Re-read 2026-09-13. Does NOT pre-empt the causal claim.**
*Safe Adaptive Overclocking and Undervolting for Energy-Efficient GPU Computing.* ISLPED 2020.
[cs.ucr.edu/~hzama001/publications/SAOU.pdf](https://www.cs.ucr.edu/~hzama001/publications/SAOU.pdf)
· doi:10.1145/3370748.3406553. **Read in full**, local copy `papers/saou-islped-2020.pdf`.

One **GTX 980**, cuBLAS matrix multiply. Pushes **beyond** `V_safeMin` and **beyond** `f_safeMax` —
deliberately into the faulting region — and catches the resulting errors with in-kernel
checkpoint-recovery. Up to 22% energy reduction. Built on the authors' earlier GreenMM (ABFT).

🔑 **The sentence that settles it:** *"Since the GPU is undervolted at a **fixed frequency**, it does
not incur any performance degradation."* They hold frequency and lower voltage. **They never sweep
frequency for an optimum, never reshape a V/F curve, and the "optimum" they chase is the
RELIABILITY EDGE, not an efficiency one.** Afterburner appears only as reference [22], the tool.

**Same family as Leng et al.:** exploit the guardband at fixed frequency, handle the faults. The
open question raised on 09-12 is closed — it bears on the guardband literature, not on claim A.

### ⛔ Fan, Cosenza, Juurlink — ICPP 2019. **Read 2026-09-13, and it was MISATTRIBUTED for months.**
*Predictable GPUs Frequency Scaling for Energy and Performance.* ICPP 2019.
[doi:10.1145/3337821.3337833](https://doi.org/10.1145/3337821.3337833) · open-access postprint:
[TU Berlin DepositOnce](https://depositonce.tu-berlin.de/items/06109ac7-40f7-42e7-bd14-442a273b360a)
· local copy `papers/fan-icpp-2019-predictable-gpu-freq-scaling.pdf`.

⛔ **The paper's reference list attributed this to "Guerreiro et al." It is by Kaijie Fan, Biagio
Cosenza and Ben Juurlink, TU Berlin.** Guerreiro is a real author in this field — RNN-based
DVFS-aware power models — but wrote different papers. **A wrong author name sat in the bibliography
under a note telling everyone to read it, which is presumably part of why nobody did.**

| | |
|---|---|
| Hardware | **NVIDIA GTX Titan X** (Maxwell, consumer) as the main target, plus Tesla P100 |
| Space | 85 core frequencies **135–1392 MHz** × 4 memory frequencies = 219 configurations |
| Control | **NVML only** — `nvmlDeviceSetApplicationsClocks`, `nvmlDeviceGetPowerUsage`. **No voltage control, no curve reshaping** |
| Method | ML on **static code features**, trained on 106 synthetic micro-benchmarks; predicts speedup and normalised energy, combined into a **Pareto set** |
| Claim | *"can predict the best frequency settings of a new kernel **without executing it**"* — accurate on extrema and Pareto set for 10 of 12 test benchmarks |

🔑 **The "closest prior art" note was pointing at the wrong risk.** This is frequency-only and
voltage-free, so it does not touch the causal claim at all. **What it is closest to is this
project's NULL** — the probe-based Ridge model that loses to a fixed constant. Fan et al. report
*success* at predicting per-kernel optimal configurations, from richer inputs: static code features
rather than probe points, a 2D core×memory space rather than 1D, and purpose-built micro-benchmark
training rather than a 33×13 matrix with no feature columns. ⚠️ **That difference has to be stated
whenever the null is presented, or a reader will take the null as contradicting a published
success.**

✅ **It also independently corroborates a measurement hazard this project found on its own:**
*"some of the configurations marked as supported by NVML are not available, because the setting
function does not actually change the frequencies"* — and on Titan X, requesting above 1202 MHz
silently gives 1202. That is the same class as this project's lock-overshoot detection.

**And it is another consumer card swept far below default** — more prior art for the consumer
claim, on a third card (Titan X), from a third group.

---

## 2. Voltage limits, guardbands and per-chip variation

**Bears on:** the claim that the floor voltage is per-card (**prior art** — these are why).

| source | hardware | what it establishes |
|---|---|---|
| **Leng et al.**, *Safe Limits on Voltage Reduction Efficiency in GPUs*, MICRO-48 2015. [PDF](https://cs.sjtu.edu.cn/~leng-jw/resources/Files/leng15micro-gpuvminexp.pdf) — **read in full** | GTX 480 / 580 / 680 / 780 — **consumer** | ~20% guardband across two generations; up to 25% energy saved; geomean 21% (680) and 15.8% (480). **Vmin measured across five physical GTX 780 cards, differing by a roughly constant offset.** ⚠️ Vmin is a fixed-frequency correctness limit, NOT the load floor |
| **Trakosa et al.**, *NAVIgator*, IOLTS 2025. [PDF](https://www.ceid.upatras.gr/webpages/faculty/gpapad/assets/papers/iolts2025_trakosa.pdf) — **read in full** | RX 7600 / 7700 / 7800 XT — **consumer AMD** | Voltage reduced at fixed frequency, up to −300 mV, 14% average power saving, chip-to-chip variation across three models |
| **Sinha et al.**, *Not All GPUs Are Created Equal*, SC '22. [arXiv:2208.11035](https://arxiv.org/abs/2208.11035) — **read in full** | five clusters, >18,800 GPU-hours | 8% average, 22% max **performance** variation within identical SKUs; 1.5× outliers |

---

## 3. DVFS energy measurement and the efficiency optimum

**Bears on:** whether locating an optimum on consumer silicon is new (**it is not**).

| source | hardware | what it establishes |
|---|---|---|
| **Tang, Wang, Wang, Chu**, e-Energy '19. [arXiv:1905.11012](https://arxiv.org/abs/1905.11012) — **read in full** | P100, V100, **GTX 2080 Ti** | Energy curves show a valley with a sweet spot; 8.7–23.1% training / 19.6–26.4% inference against DEFAULT clock. The consumer card is scaled **up** from 1350 MHz while datacenter defaults are already the ceiling |
| **Afzal et al.**, *Modeling and Chasing the Energy-Efficiency Sweet Spots in Modern GPUs*. [arXiv:2607.00819](https://arxiv.org/abs/2607.00819) — abstract + HTML read | A40 / A100 / H100 / H200 | Piecewise power model with a transition frequency f_t; optimum "clusters near f_t but does not necessarily coincide". **Datacenter only**, open dataset |
| **Zhang et al.**, EuroSys '24. [doi:10.1145/3627703.3629584](https://doi.org/10.1145/3627703.3629584) — **read in full** | V100 | 26.7% mean efficiency gain for 5.8% performance loss. ⚠️ **Performance-constrained** — not the same quantity as this project's unconstrained 44.4% |
| **Mei, Wang, Chu** 2017 survey | GTX 980 + GTX 560 Ti | ✅ **READ 2026-09-13 via [arXiv:1610.01784](https://arxiv.org/abs/1610.01784)** — see section 1. ScienceDirect still 403s; the arXiv version is the way in |
| **Maliakel, Ilager, Brandic**, *Characterizing LLM Inference Energy-Performance Tradeoffs*. [arXiv:2501.08219](https://arxiv.org/abs/2501.08219) — **read** | — | LLM-inference framing of the same tradeoff |
| *Accurate Energy and Performance Prediction for Frequency-Scaled GPU Kernels*, MDPI Computation 8(2):37 | — | ⚠️ Not read |

---

## 4. The interconnect / crossbar domain

**Bears on:** the crossbar-starvation mechanism (**partially novel** — the domain is documented,
the bandwidth chain is not).

| source | what it establishes |
|---|---|
| **loong0x00**, *XBAR in NVIDIA Blackwell GPUs: A Physical Clock Domain Ignored by Public Tooling*, 2026-08-13. [link](https://loong0x00.com/notes/blackwell-xbar-physical-clock-domain/) — **read in full** | GB202. XBARCLK's own PMU object, clock source, 127-point V/F table and control path; 0.8999:1 GPC-to-XBAR topology constraint. ⛔ **Cited as the source that establishes the domain, which this work therefore does not claim.** No bandwidth figures, no swept ratio |
| **LACT issue #1147**, 2026-08-10. [github.com/ilya-zlobintsev/LACT/issues/1147](https://github.com/ilya-zlobintsev/LACT/issues/1147) — **verified by API 2026-09-12** | RTX 5090. *"Runtime XBAR clock and per-domain MSVDD control on NVIDIA Blackwell."* +60 to +450 MHz XBAR offsets for up to +10.6% FPS. ⚠️ A throughput-limit figure appears in the thread with no benchmark trace and is deliberately not cited |
| **WO2013137862A1**, *Dynamically controlling interconnect frequency in a processor* | Prior art that a slow interconnect stalls a faster core. **CPU/uncore, closed-loop controller, no voltage-pinning, no GPU crossbar.** Cited to pre-empt the objection, not as a source |
| Intel uncore frequency scaling (UFS) literature | The long-established CPU analogue. Not GPU, not voltage-driven in the same sense |

---

## 5. Measurement methodology

| source | what it establishes |
|---|---|
| **Yang et al.**, *Accurate and Convenient Energy Measurements for GPUs: A Detailed Study of NVIDIA GPU's Built-in Power Sensor*, 2024. [code](https://github.com/JimZeyuYang/GPU_Power_Benchmark) — **read** | What the built-in sensor actually reports. Directly relevant: this project's power figures are the card's own estimate, not a shunt measurement |
| **Rodinia**, IISWC 2009 | Benchmark suite. ⚠️ Not read; cited for the suite only |

---

## 6. Datasets

| dataset | what it is |
|---|---|
| [HKBU-HPML/NV-DVFS-Benchmark](https://github.com/HKBU-HPML/NV-DVFS-Benchmark) | ⚠️ **`master` branch, not `main`.** 🔑 **This is the origin of the GTX 1080 Ti dataset this project uses** — `csvs/gtx1080ti-dvfs-real-features.csv` — which the prior-art log had recorded as never located. It belongs to **Wang & Chu, ICPADS 2018**, *GPGPU Performance Estimation with Core and Memory Frequency Scaling*, NOT to Mei's papers. Also holds GTX 980, Titan X, P100 and V100 files |
| [HKBU-HPML/GPU-DVFS-Job-Schedule](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule) | 🔑 **The repo `Get-Dataset.ps1` actually downloads BOTH consumer files from**, and the artifact of **Wang, Mei, Liu, Leung, Li & Chu, TPDS** ([arXiv:2104.00486](https://arxiv.org/abs/2104.00486)). ⛔ Listed as merely "later scheduling work" until 2026-09-13. **Its README states the cards' default operating clocks — GTX 1080 Ti 1800 MHz core / 5000 memory, RTX 2070 Super 1880 / 6300 — which overturned the overclocking-sweep claim.** |
| [zyjopensource/GPU-DVFS-Dataset](https://github.com/zyjopensource/GPU-DVFS-Dataset) | **No license stated.** Not redistributed here; fetched by `scripts/Get-Dataset.ps1` |
| V100 reference set (33 workloads × 13 frequencies) | The project's original basis. Core clock only, **no voltage column** |
| GTX 1080 Ti / RTX 2070 Super consumer sweeps | The two datasets the range argument is about. ✅ **Originating paper LOCATED 2026-09-13** — Wang *et al.*, TPDS, arXiv:2104.00486 for the 2070 Super; the 1080 Ti file is byte-identical in Wang & Chu's ICPADS 2018 repo (checksum-verified) |

---

## ✅ Did Mei release raw data? Checked 2026-09-13. **No — and that matters.**

The open question left after the survey read. Answered three ways:

1. **Mei's own papers release nothing.** The 2017 survey's full text contains **no data-availability
   statement and no dataset URL** — every link in it is a vendor or tool page. HotPower 2013 has no
   such statement either.
2. **The same group DID release consumer DVFS data**, but under different papers: Wang & Chu's
   ICPADS 2018 work, via `HKBU-HPML/NV-DVFS-Benchmark`. That repo holds GTX 980, GTX 1080 Ti,
   Titan X, P100 and V100 CSVs.
3. ⛔ **A claim stood here saying those released files sweep the wrong way. It was FALSE and is
   retracted.** See the box below.

⛔ **RETRACTED 2026-09-13, hours after it was written, by the person who wrote it.** The claim
was: *"the open, reusable consumer DVFS data that exists sweeps at or above stock"*, on the evidence
that `coreF`/`memF` in the HKBU release are normalised multipliers 1.0 to 2.0. **That was read off a
`*-features.csv`. The `*-Performance-Power.csv` files — the ones this project actually analyses —
carry absolute megahertz, and the GTX 980 files sweep 500-1000 and 700-1500 MHz (plus two more at
400-1000) against that card's 1127 MHz base clock.** Below-stock consumer data is released and
downloadable.

🔑 **A conclusion drawn from one file of the wrong kind. The fifth retraction in two days and the
only one that was self-inflicted rather than inherited** - and it reached CLAUDE.md, the roadmap,
the paper's abstract and conclusion, a to-do list and four commit messages before `compare_consumer`
was opened and found to read a different file than the one that had been sampled.

⛔ **AND THE REPLACEMENT CLAIM WAS ALSO WRONG, FOUND THE SAME DAY.** It read: *"every consumer part
in that release later than Maxwell sweeps at or above stock"*, on percentages computed against the
**rated boost clock from a specs database**. That describes a REFERENCE card. The dataset authors
publish the default operating clock of the cards they used — **GTX 1080 Ti 1800 MHz, RTX 2070 Super
1880 MHz** — and against those each sweep **brackets** its default, **two of five core points below
it**, down to 89%. Both declared values land exactly on a swept grid point in both axes, which is
what settles that they are the sweep's centre.

✅ **What survives is a claim about WIDTH.** Each modern consumer window is ~22 points wide and
bottoms out at 89% of default, so none can contain an optimum that sat at **62% of maximum** on the
V100. That is checkable via `analysis/compare_consumer.py`, which now prints both axes, and the
GTX 980 counter-example by opening
`csvs/raw/gtx980-low-dvfs-real-small-workload-Performance-Power.csv` in that same repository.

| released consumer file | coreF range | vs its default |
|---|---|---|
| `gtx980-low-...-Performance-Power` | **500–1000 MHz** | **entirely below** (1127 MHz base) |
| `gtx980-high-...-Performance-Power` | **700–1500 MHz** | spans it |
| `csvs/v0/gtx980-dvfs-real`, `csvs/backup/gtx980-DVFS` | **400–1000 MHz** | **entirely below** |
| `gtx1080ti-dvfs-real-Performance-Power` | 1600–2000 MHz | **brackets** 1800 MHz declared default |
| Titan X (Pascal-generation) | 1600–2000 MHz | above (1531 MHz boost) |
| RTX 2070 Super | 1680–2080 MHz | **brackets** 1880 MHz declared default |

---

## 7. Found 2026-09-13, in the post-rewrite search pass

### ⛔ Wang, Mei, Liu, Leung, Li, Chu — TPDS. **The narrow-window criticism is THEIRS.**

[arXiv:2104.00486](https://arxiv.org/abs/2104.00486) — **read in full; every quotation below
verified against the PDF, not a summary.** Artifact: `HKBU-HPML/GPU-DVFS-Job-Schedule`, the repo
`scripts/Get-Dataset.ps1` downloads both consumer CSVs from.

§5.1.1 publishes the platform interval `V^Gc ∈ [0.8, 1.24], f^Gc ∈ [0.89, g1(V^Gc)], f^Gm ∈
[0.8, 1.1]` and the default `(1.05 V, 1800 MHz, 5000 MHz)`. **The 0.89 and the 1800 MHz are their
figures.** §5.2 attributes their low measured saving to the window — *"the average energy
conservation of 20 benchmarks is 4.3% for GTX 1080Ti... The reason for this low effect is (1) The
static power P_G0 takes a big portion...; (2) The scaling intervals of f^Gc and f^Gm are narrow"* —
then simulates a widened interval reaching **36.4%**, with the optimum *"close to the allowed lowest
setting"* in both cases.

🔑 **Cite them FOR the argument, never claim it.** Their 4.3% → 36.4% is structurally this
project's 1.00% → 44.40%. ⚠️ **System-scope energy** at the wall against a 37 W idle floor (24 W
CPU, 13 W GPU), and the wide case is a **simulation with static power shrunk** — not comparable to
board-power figures, and not a measurement. That last point is the opening: they could only simulate
the wide window; this project measures it.

### 🟡 Price, Clark, Barsdell, Babich, Greenhill — K20 firmware voltage tables, 2014

[arXiv:1407.8116](https://arxiv.org/abs/1407.8116) — **read in full.** ⛔ `PRIOR-ART-20260912.md`
calls this "Mei et al.'s K20 firmware study". **It is not a Mei paper** — Harvard-Smithsonian CfA,
with two NVIDIA co-authors. Verified against arXiv metadata.

They reprogrammed a K20's firmware with **GPU-Z + Kepler BIOS Tweaker** so core voltages V1–V5 were
**fixed to 900 / 912.5 / 925 / 950 / 987.5 mV**. That is a **per-point voltage-table edit**, closer
to this project's method than HotPower 2013's global voltage setting. Headline: **37–48% perf/W**
over default by combining undervolt, overclock and cooling.

✅ **The causal claim survives, narrowly.** Under the *modified* table they hold frequency
**constant at 800 MHz** and sweep temperature; they never sweep frequency under an edited table, and
report no interior optimum (efficiency rises monotonically to their stability edge). So the optimum
is never shown to MOVE. ⚠️ **But "nobody edits a voltage table per point" was never true** — do
not write it. 🔑 Their Figure 4a also reports **unexplained repeatable power drops** under a
modified voltage table, attributed to regulator efficiency — worth reading against this project's
still-unexplained ~71 MHz curve-fixed `gemm` ceiling deficit.

### ⚠️ The XBAR domain was public EARLIER than §4 of this file records

§4 dates the XBAR prior art to LACT #1147 (2026-08-10). **A GIGAZINE news report dated 2026-06-08**
— `gigazine.net/gsc_news/en/20260608-rtx-5090-external-clock/` — describes RTX 5090 vBIOS work in
which *"the crossbar clock, which affects the connection speed inside the GPU, can only be partially
adjusted by swapping the vBIOS"*, treats it as a binning indicator (~2700 MHz a good bin), and
reports a modified card reaching ~2920 MHz. **Two months earlier than the date currently recorded.**

⚠️ **READ AS A NEWS REPORT ONLY.** The primary source is work by "PickleRick" on the XtremeSystems
forum, which was **not reached** — that forum thread is the highest-priority follow-up, because the
GIGAZINE summary contains no bandwidth measurement, no crossbar/core ratio, and no coupling to
voltage. **The causal chain is untouched; only the date on the domain fact moves.** A third
independent source (`kovasky.me`, Blackwell XBAR via direct ioctl) also exists, snippet only.

### ⚠️ mVolt+ — an undocumented voltage WRITE path now exists publicly on RTX 50-series

`github.com/b00nz/mVolt`, covered by igor'sLAB / VideoCardz / KitGuru — **snippet only, not
tested.** Exposes Core, XBAR, SYS and Video domain voltage controls plus curve editing on Blackwell.
🔑 **Operationally relevant, not prior art.** CLAUDE.md's "voltage cannot be written through any
*documented* API" stays true as written, but an undocumented public write path on this exact
architecture changes what is feasible. Coverage notes its wattage figures are community results,
"not repeatable lab validation". Related: **LACT issue #936** (2026-03-07, full text) —
reverse-engineered 128-point V/F curve read and per-point offsets via `ClockClientClkVfPointsSetControl`,
the same undocumented entry point CLAUDE.md lists as out of scope. **No efficiency measurements in
either.**

🔑 **And the technique is not novel even in the enthusiast world.** Region-by-region curve
reshaping — raise a chosen mV point, flatten everything above it — is the standard undervolting
recipe since GPU Boost 3.0, documented by igor'sLAB among others. **The contribution sentence's
"we reshape the curve region by region" describes a Tuesday to anyone who undervolts.** The
load-bearing half is what follows it: that the optimum tracks the floor region and not the region
above, measured, with a control. Nothing found measures where the optimum LANDS under different
reshapes; enthusiast sources measure "same FPS, less power" at one operating point.

---

## Corrections made while verifying citations

**Kept because the pattern is the point: every one came from a second-hand summary.**

- ⛔ **"~140 MHz / ~11% frequency variation"** attributed to Sinha et al. — **wrong.** The paper
  reports 8% average / 22% maximum *performance* variation and 1.5× outliers. Garbled second-hand.
- ⛔ **"9–18% guardband"** as the headline for Leng et al. — **wrong.** That is the GTX 680-specific
  range; the headline is ~20% across two generations. Came from a local model's PDF extraction and
  was caught by checking the raw text.
- ⛔ **"GTX 480, 480–1080 MHz sweep"** for HotPower 2013 — **wrong on both counts.** One GTX 560 Ti,
  480–880 MHz. Came from a search snippet, was explicitly marked `search snippet only`, and was
  still wrong. 🔑 **A confidence label tells you how much to trust a citation; it does not make the
  content less wrong.**
- ⛔ **"They had more control than this project does ... which is why this project uses
  Afterburner"** — **wrong.** HotPower 2013 used Afterburner too. Written before anyone read it.
- ⛔ **arXiv 2211.07260 attributed to "van Werkhoven et al."**, and its reference entry listed
  **"van Werkhoven, Willemsen, Schoonhoven, Nieuwpoort"** — **wrong twice.** Two of those names are
  not on the paper, and van Werkhoven is the THIRD author. It is **Schoonhoven, Veenboer, van
  Werkhoven, Batenburg**. 🔑 **This is the source of the project's largest retraction, and its
  author list was invented** - written from memory of a summary, in the same hours the search rule
  was being celebrated for catching things.
- ⛔ **arXiv 1407.8116 attributed to "Mei et al."** in `PRIOR-ART-20260912.md` — **wrong.** It is
  Price, Clark, Barsdell, Babich & Greenhill. Caught only because a later pass opened it, and the
  paper turned out to matter more than the log had judged.
- ⛔ **Reference [10] carried NO author at all** (Afzal et al.) while this index recorded one the
  whole time. 🔑 **The index and the bibliography were never reconciled**, which is the same gap
  the Guerreiro error lived in.
- ⛔ **ICPP 2019 attributed to "Guerreiro et al."** — **wrong.** It is Fan, Cosenza and Juurlink.
  🔑 **The wrong name sat under a note saying "read this before finalising any novelty claim",
  for months, while two novelty claims fell.** A citation nobody can look up is a citation nobody
  opens.

---

## 8. Found 2026-09-18 by the first outside reader, and READ IN FULL

### ✅ Mendes, Tomás, Roma — *Decoupling GPGPU voltage-frequency scaling for deep-learning applications*

JPDC **165**:32–51, 2022. `10.1016/j.jpdc.2022.03.004`. Author PDF:
`hpcas.inesc-id.pt/~handle/papers/Journal_JPDC_2022.pdf`. **Read in full 2026-09-18**, 20 pages,
every statement below taken from the text rather than from a summary.

**GPT surfaced this as the closest pre-emption of the manipulation claim. Reading it narrows that
considerably — and hands this project a quotable justification it did not have.**

🔑 **THEY EXCLUDED NVIDIA, AND SAID WHY, IN THEIR OWN WORDS:**

> "The sole inclusion of AMD devices comes from the reduced availability of drivers and convenient
> software APIs from other manufacturers (e.g., NVIDIA) for an independent and decoupled control
> over the GPU frequency and voltage."

✅ **That is a peer-reviewed statement that the thing this project does cannot be done the way they
did it on NVIDIA.** They set voltage and frequency independently through `rocm-smi`; on consumer
NVIDIA parts voltage cannot be written through any documented API at all, which is why this project
reshapes the V/F *curve* instead. **Cite them for the constraint, not merely against the claim.**

**What they actually measure is Vmin — a CORRECTNESS limit, not an efficiency optimum.** Their
central quantity is *"the frequency-dependent minimum operating voltage that (still) leads to a
correct GPU operation"*, found by undervolting at fixed frequency in 50 mV steps (10 mV near the
edge) through three stages: working → computation errors → crash.

⛔ **The words "optimum", "optimal frequency", "ridge" and "constant voltage" do not appear in the
paper.** The nearest thing is a *"plateau of minimum energy consumption"* in the 2-D F–V space for
CNN training (Fig. 21). **They never locate the frequency that maximises throughput per watt**,
which is the quantity this project's rule is about.

🔑 **This is the same distinction `CLAUDE.md` already draws for Leng et al.**: Vmin at a fixed
frequency is a correctness limit, *not* the bottom of the dynamic V/F curve, and neither connects
per-chip voltage to *where the efficiency optimum sits*.

| | Mendes et al. 2022 | this project |
|---|---|---|
| hardware | AMD Vega 10 FE, Radeon 5700 XT | 4 consumer NVIDIA chips, 3 architectures |
| control | voltage set **directly**, decoupled, via `rocm-smi` | curve **reshaped** per point; voltage unwritable |
| quantity | **Vmin**, correctness limit | **efficiency optimum** over frequency |
| granularity | global V at fixed f, 50 mV steps | region-targeted edit on a 127-point curve |
| power cap | **raised to TDP max** (220→300 W, 190→285 W) | **stock throughout** |
| failure | deliberately driven to **crash** | safe direction only; instability unreachable |
| control arm | none | negative control + registered predictions |

**Results, for the record:** 15–25% safe undervolt on both GPUs, >20% guardband at all frequencies,
up to **38% energy** and **41% EDP** reduction on CNN training, average **36.7%** EDP improvement
across complete CNN training, with no significant accuracy loss.

### ⚠️ What GPT got slightly wrong, and it matters

GPT wrote that this *"pre-empts a general claim such as 'first experiment to modify a GPU V/F
relationship and re-find its energy optimum'."* ✅ **The broad form is genuinely pre-empted.**
⛔ **But "energy optimum" overstates the overlap**: they map a 2-D F–V space and report a
minimum-energy *plateau*, and they do not locate an energy-optimal *frequency*. Reading the paper
was the only way to see that, which is the standing rule here — **an AI-supplied summary is a lead,
not a source.**

### 🟡 A lead for the open §4d thermal question — do NOT over-read it

§3.4 reports that undervolt capability is roughly flat to **70–75 °C**, is **greatest at 55 °C**,
and degrades above 75 °C as carrier mobility falls. They extend Leng et al. [10], who found only
small Vmin variation with temperature but tested only to 70 °C.

⚠️ **This is about Vmin, not about the requested voltage a driver programs**, and the two are
different quantities — the driver does not know Vmin. The RTX 2060 Super's voltage minimum happening
to fall at **55.5 °C** is a coincidence worth noticing and **not** an explanation. Record it as a
lead; §4d's descending sweep is still the test.

### ⛔ Guerreiro, Ilic, Roma, Tomás — *GPGPU Power Modeling for Multi-Domain Voltage-Frequency Scaling*

HPCA 2018, pp. 789–800. `10.1109/HPCA.2018.00072`. Author PDF:
`web.tecnico.ulisboa.pt/~ist14359/wordpress/nfvr_pubs/hpca18.pdf`. **Read in full 2026-09-18**,
12 pages.

🔑 **THIS IS THE EARLIEST DIRECT MEASUREMENT OF THE CONSTANT-VOLTAGE REGION ON CONSUMER NVIDIA
HARDWARE THAT THIS PROJECT KNOWS OF — 2018, four years before Schoonhoven et al.** Verbatim:

> "The results clearly show that there are two distinct regions for the core voltage when scaling
> the core frequency: i) **a constant voltage region, for lower frequencies**; and ii) after a
> specific frequency, **the voltage starts increasing linearly with the frequency.**"

⚠️ **And they measured it with the same tool lineage this project uses:**

> "The real measured voltages were obtained using the **NVIDIA Inspector and MSI Afterburner**
> (third party Windows tools)."

**Hardware: GTX Titan X (Maxwell), Titan Xp (Pascal), Tesla K40c (Kepler).** Figure 6 plots
measured against predicted core voltage over roughly **500–1200 MHz** on the Titan X and
**500–1900 MHz** on the Titan Xp — i.e. well below default, on consumer-class parts.

✅ **The measurement is INDEPENDENT of their model.** Voltage enters their power model as an
unknown estimated from power (Eq. 4–7); Figure 6 then validates that estimate against
Afterburner/Inspector readings. So unlike Schoonhoven et al.'s Equation 3 — a flat floor plus a
rise *by construction*, fitted from power — this paper has an actual voltage measurement that
could have come out any shape.

**Their own stated limits:** *"it was not possible to sweep through all core and memory frequency
ranges, due to limitations of these tools, nor was it possible to verify the voltage levels on the
Tesla K40c GPU."*

### ⛔ What this changes, and what it does not

| | status |
|---|---|
| "the constant-voltage region exists on consumer NVIDIA" | ⛔ **measured and published 2018.** Older than this project credited. |
| "it was measured with Afterburner-class tools" | ⛔ also 2018, same lineage |
| the region ↔ **efficiency optimum** link | ✅ **NOT in this paper.** "efficiency" appears **0 times**; "optimum" **0 times**; "ridge" only as a false match inside a reference. It is a **power model**, and it never computes energy efficiency or locates an optimal frequency. |
| Turing | ✅ untouched — Kepler, Maxwell, Pascal only |
| the region-targeted causal manipulation | ✅ untouched |

🔑 **So the correlation's ownership does NOT move to Guerreiro — but the measurement's does.**
`CLAUDE.md` says the ridge-point literature *"assumed rather than observed"* the floor on parts it
could not read; that remains true of Schoonhoven et al. on Turing, but it must no longer be implied
about consumer NVIDIA generally. **Guerreiro et al. observed it directly in 2018.**

✅ **This is now the THIRD independent measurement of the structure on NVIDIA** — Guerreiro 2018
(Maxwell, Pascal), Schoonhoven 2022 (Ampere), and this project (Turing, Ampere, Blackwell). That
makes the mechanism look general, which strengthens the thing this project actually claims — the
*causal* result — while removing any residual novelty in having measured the region at all.

⚠️ **Nothing here was ever claimed as novel by this project**, whose contribution sentence says what
was DONE. But `PRIOR-ART-20260913.md`'s framing — that the ridge-point literature had not measured
consumer V/F curves — was too strong, and this is the source that corrects it.
