# Project Proposal — Inspirit AI

**Project Title:** Headroom — Locating the Energy-Efficiency Optimum on Consumer GPUs
**Domain / Category:** Systems / Hardware Energy Efficiency (applied ML)
**Author Name:** Raymond
**Email:** alesten213@gmail.com
**Repository:** `github.com/imaoofu/headroom` (private)

---

## 1. What is the problem that you would be researching?

GPUs ship with conservative default clocks, because a vendor's voltage-frequency behaviour must hold
across millions of varying dies for years. The energy-efficiency optimum — the clock giving the most
work per watt — therefore sits below the default. On a public Tesla V100 dataset, running at stock
instead of each workload's own optimum gives up a mean of **44.4%** efficiency.

That much has been measured before, so my question is narrower: **what sets where the optimum lands
on current consumer hardware, and can it be predicted without measuring the whole curve?**

I chose it because I build and sell PCs, so I have physical access to multiple GPUs — the scarce
resource in this field. It interests me because published GPU DVFS work is almost entirely
datacenter, while consumer cards are where much of the electricity actually goes.

## 2. What are some challenges you foresee while doing the project?

Four, and three have already happened.

**Prior art.** I have retracted seven novelty claims after searching and finding the result already
published. None were measurement errors — every one was a claim about what was *new*.

**Control surface.** Voltage cannot be *written* through any documented API on current consumer
cards, only read, so curve changes are made by hand — which limits exact reproducibility.

**Sample size.** Cards pass through my bench and are then sold, so most results are n=1 per chip.

**Contamination.** Ordinary desktop software silently cost up to 10.3% of measured throughput before
I found it.

## 3. Describe the dataset you will be using.

**Public, for comparison:** a Tesla V100 DVFS dataset (33 workloads × 13 core frequencies) from
`zyjopensource/GPU-DVFS-Dataset`, consumer GTX 1080 Ti and RTX 2070 Super sweeps from
`HKBU-HPML/GPU-DVFS-Job-Schedule`, and a 2,824-GPU specifications database.

**My own, which is the contribution:** **359 dataset-grade sweeps across four consumer GPUs and
three architectures** (Blackwell, Ampere ×2, Turing). A PowerShell harness locks each clock, runs a
fixed-work benchmark and always resets; HWiNFO supplies core voltage and interconnect clock, joined
onto each sweep by core clock. Released under CC BY 4.0 with the collection tooling.

## 4. What algorithms/techniques/models would you be using?

Three predictors against one baseline, so that "does prediction earn its cost?" is answerable rather
than assumed: **Ridge regression over probe points** (leave-one-workload-out); **a curve-derived
rule** that reads the optimum off the decoded voltage-frequency curve and needs no measurement; and
**a workload-feature model** using arithmetic intensity, occupancy and memory traffic. **Baseline:
the single best fixed frequency.**

**Pre-existing implementations adopted:** scikit-learn, pandas/NumPy, PyTorch, NVIDIA's NVML via
P/Invoke, MSI Afterburner, HWiNFO.

**Modifications:** I decoded Afterburner's binary profile format so curves apply from the command
line unattended, and built a mechanical auditor that recomputes every number in the write-up from
the raw CSVs and fails if text and data disagree.

## 5. How will you evaluate your results?

**Metric: regret** — efficiency given up against the best achievable choice, in percentage points.
Not megahertz error, because being 100 MHz wrong costs different amounts at different points on the
curve. Validation is leave-one-workload-out.

**The headline result so far is a null, and is reported as one:** the probe-based model scores
**0.883%** mean regret against the fixed-frequency baseline's **0.837%**. It loses, and the script
prints that verdict about its own output.

**Plots:** efficiency against core frequency per workload; voltage and interconnect clock against
core clock; regret by strategy; and swept range as a percentage of each card's default.

**Qualitative:** predictions registered in writing *before* collection, a negative control arm, and
a stated boundary condition — a card on which the rule cannot be applied at all, reported rather
than dropped.

## 6. (Optional) Post completing the project, do you have any specific goals?

To publish the dataset with a citable DOI, and a written paper. The dataset is the part that cannot
be pre-empted by another paper appearing.

> ⚠️ **Raymond — fill in before submitting:** the program's actual deadlines and required
> submissions. No part of this plan should read as if time were unlimited.

## 7. References

1. Schoonhoven, R., Veenboer, B., van Werkhoven, B., Batenburg, K.J. *Going green: optimizing GPUs
   for energy efficiency through model-steered auto-tuning.* arXiv:2211.07260, 2022.
2. Mei, X., Wang, Q., Chu, X. *A Survey and Measurement Study of GPU DVFS on Energy Conservation.*
   Digital Communications and Networks, 2017. arXiv:1610.01784.
3. Mei, X., Yung, L.S., Zhao, K., Chu, X. *A Measurement Study of GPU DVFS on Energy Conservation.*
   HotPower '13.
4. Fan, K., Cosenza, B., Juurlink, B. *Predictable GPUs Frequency Scaling for Energy and
   Performance.* ICPP 2019. doi:10.1145/3337821.3337833.
5. Leng, J., Buyuktosunoglu, A., Bertran, R., Bose, P., Reddi, V.J. *Safe Limits on Voltage
   Reduction Efficiency in GPUs.* MICRO-48, 2015.
6. Wang, Q., Mei, X., Liu, H., Leung, Y.-W., Li, Z., Chu, X. *Energy-aware Non-Preemptive Task
   Scheduling with Deadline Constraint in DVFS-enabled Heterogeneous Clusters.* IEEE TPDS.
   arXiv:2104.00486.
7. Wang, Q., Chu, X. *GPGPU Performance Estimation with Core and Memory Frequency Scaling.* ICPADS
   2018, pp. 417–424.
8. Tang, Z., Wang, Y., Wang, Q., Chu, X. *The Impact of GPU DVFS on the Energy and Performance of
   Deep Learning.* e-Energy 2019. arXiv:1905.11012.
9. Zhang, Z., Wang, Q., Lin, Z., Xu, N., Wang, X. *Improving GPU Energy Efficiency through an
   Application-transparent Frequency Scaling Policy with Performance Assurance.* EuroSys '24.
