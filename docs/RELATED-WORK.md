# Related work — the index

**One place for every source this project has found, with a link, what it actually says, and what
it bears on.** Built 2026-09-13 after the ridge-point retraction, by consolidating the paper's
reference list with the prior-art sweep in [`PRIOR-ART-20260912.md`](PRIOR-ART-20260912.md).

🛑 **Read status is part of the citation.** Every entry says whether the primary source was opened.
This project has twice written a figure from a second-hand summary that turned out wrong — see the
corrections at the bottom — so an unread source is marked unread and is not cited for a number.

📄 **Local PDFs go in [`papers/`](papers/), which is gitignored.** Copies are not redistributed
here; the links below are how you get them back.

---

## 1. The sources that bound this project's novelty

These four decide what can and cannot be claimed. Read these before writing any contribution
statement.

### ⛔ van Werkhoven et al. — the ridge point. **THE retraction source.**
*Going green: optimizing GPUs for energy efficiency through model-steered auto-tuning* (Kernel
Tuner). arXiv **[2211.07260](https://arxiv.org/abs/2211.07260)**, 2022. **Read in full.**

Defines the **ridge point**: the frequency at which core voltage stops being constant and begins
rising. States the consequence this project had believed was its own finding:

> "Reducing the clock frequency beyond the ridge point does not make the GPU more energy efficient,
> as performance drops with f while v is constant below the ridge point."

A100 ridge 1025 MHz (70% of peak), RTX A4000 1290 MHz (72%); predicted energy-optimal clocks 985
and 1298 MHz. **Datacenter and workstation only — no consumer parts.**

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

### 🔑 Zamani, Tripathy, Chen, Bhuyan — SAOU. **Re-read this against the causal claim.**
*Safe Adaptive Overclocking and Undervolting for Energy-Efficient GPU Computing.* ISLPED 2020.
[cs.ucr.edu/~hzama001/publications/SAOU.pdf](https://www.cs.ucr.edu/~hzama001/publications/SAOU.pdf)
· doi:10.1145/3370748.3406553. **Read in full 2026-09-07.**

GTX 980, cuBLAS 10K matmul, **MSI Afterburner used to apply the offsets**, checkpoint-recovery for
faults, up to 22% energy reduction.

⛔ **This was read on 09-07, before the causal claim existed, and has NOT been re-examined against
it.** It is a consumer GPU, adaptively overclocked *and* undervolted through the same tool this
project uses. **Whether it moves an efficiency optimum or only chases a safe operating point is the
open question, and it is the highest-value re-read on this list.**

### ⚠️ Guerreiro et al. — flagged as closest prior art, **STILL NOT READ**
*Predictable GPUs Frequency Scaling for Energy and Performance.* ICPP 2019.
[doi:10.1145/3337821.3337833](https://doi.org/10.1145/3337821.3337833)

⛔ The paper's own reference list has carried the note *"the closest prior art; read this before
finalising any novelty claim"* since well before the ridge-point retraction. **It is still unread.**
Given that two novelty claims have now fallen to sources exactly like this one, this is the single
most overdue item in the bibliography.

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
| **Mei, Wang, Chu**, *A survey and measurement study of GPU DVFS on energy conservation*, Digital Communications and Networks 2017. [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2352864816300736) | — | ⛔ **NOT READ — HTTP 403.** The standard survey of this area; very likely contains a swept-range comparison bearing directly on the wrong-range argument. Try an institutional login |
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
| [HKBU-HPML/GPU-DVFS-Job-Schedule](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule), [NV-DVFS-Benchmark](https://github.com/HKBU-HPML/NV-DVFS-Benchmark) | ⚠️ **`master` branch, not `main`** — raw URLs 404 silently otherwise |
| [zyjopensource/GPU-DVFS-Dataset](https://github.com/zyjopensource/GPU-DVFS-Dataset) | **No license stated.** Not redistributed here; fetched by `scripts/Get-Dataset.ps1` |
| V100 reference set (33 workloads × 13 frequencies) | The project's original basis. Core clock only, **no voltage column** |
| GTX 1080 Ti / RTX 2070 Super consumer sweeps | The two datasets the wrong-range argument is about. ⚠️ Their originating paper was **never located** — see the prior-art log |

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
