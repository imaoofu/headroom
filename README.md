# Headroom

**Quantifying the gap between conservative stock GPU behaviour and the empirically-found safe
optimum — and explaining what sets it.**

> ## ⚠️ Scope and status — read before citing anything here
>
> Updated 2026-09-10. Original data exists on three GPUs, and the central mechanism has been
> measured on two architectures. What follows is what that does and does not license.
>
> - **Three chips, one unit each — which is not a sample.** Most results come from one **Zotac
>   RTX 5060 Ti Twin Edge OC 16 GB** (Blackwell, 5 nm). A **Gigabyte RTX 3070 Ti GAMING OC**
>   (Ampere, 8 nm) was measured 2026-08-25 on a third party's machine, and an **ASUS Phoenix
>   RTX 3060** (Ampere, 8 nm) on 2026-09-10. One unit of each says the *effect* is not an artifact
>   of one board; it says nothing about any model line. **Chip-to-chip variation is published at
>   roughly 11% and remains unmeasured here**, because it needs repeat units of one SKU the project
>   controls — which the customer-machine route structurally cannot provide.
> - **Everything about *tuning* is still one chip.** The two-knob decomposition, the split-region
>   curve, the ABBA manipulation and the negative control are 5060 Ti only. The other two were
>   customer machines: stock, nothing applied.
> - **The V100 analysis is a separate dataset** — 33 workloads, one chip, published by others. It is
>   never pooled with the consumer data.
> - **The prediction model lost**, and that null is a headline result rather than a footnote. See
>   [The prediction result](#the-prediction-result-a-null-that-now-has-a-mechanism).
> - ⚠️ **Nothing in the tuned profile set has been stability tested**, including the configurations
>   producing the best numbers.
> - ⚠️ **The efficiency figures carry an uncontrolled-load history.** Ordinary desktop capture
>   software was found to depress measured throughput by up to 10% in the mid-band; every
>   measurement before 2026-08-22 predates that discovery. Provenance is recorded per directory.
> - Interfaces, file layout and metrics still move.
>
> See [ROADMAP.md](ROADMAP.md) for what is open, and [HANDOFF.md](HANDOFF.md) for current state.

---

## What this project actually claims

Vendor boost algorithms are not naive. NVIDIA and AMD already account for individual chip quality —
factory ASIC binning is why two "identical" cards clock differently out of the box. **This project
does not try to beat that engineering, and any version of it that claims to should be rejected.**

What vendors do not publish is an open, reproducible account of *how much* headroom their
conservative, warranty-safe defaults leave on the table, or what predicts it. Stock behaviour has to
be safe across millions of unknown units, in unknown cases, for years. That forces real margin.

> Measure the gap between stock behaviour and the efficiency optimum, explain what drives it, and
> show the work — on hardware whose results nobody has published.

Not "we built a better GPU Boost."

### 🔑 Why this is not already answered by the published data

Two consumer GPU DVFS datasets exist publicly. **Both sweep the wrong range.** Placed on a common
axis — swept range as a percentage of each card's rated boost clock:

| dataset | swept range | mean gap found |
|---|---|---|
| GTX 1080 Ti | **101–126%** of boost | 1.00% |
| RTX 2070 Super | **95–118%** of boost | 3.34% |
| Tesla V100 (datacenter) | **55–111%** of boost | **44.40%** |

Both consumer sets start at or above stock and go **up**. They are overclocking sweeps, and they
structurally cannot locate an efficiency optimum, because the optimum lives *below* stock — the
V100's sat at 62% of its maximum.

🛑 **Their small measured gaps are NOT evidence that consumer GPUs lack headroom.** They are evidence
that nobody swept the range where headroom lives. Reproduce with `python analysis/compare_consumer.py`.

That is the contribution, stated checkably: **the consumer data that exists sweeps the wrong range.**

---

## 🔑 The central result: the optimum sits at the end of the voltage floor

> **The efficiency optimum is the highest frequency the applied V/F curve reaches at the card's
> load-floor voltage.**

A GPU will not run an active SM below a floor voltage. Across the span where the curve is still at
that floor, frequency rises while voltage does not — so power rises roughly linearly and efficiency
improves. The moment the curve leaves the floor, voltage starts climbing, `P = C·V²·f` turns
quadratic, and efficiency falls. **The optimum is the last point before that happens.**

| configuration | chip | arch | floor | floor ends | measured optimum | |
|---|---|---|---|---|---|---|
| stock | 5060 Ti | Blackwell | 0.720 V | 1537 MHz | 1537 | ✅ |
| split curve | 5060 Ti | Blackwell | 0.720 V | 1530 | 1537 | ✅ |
| repaired curve | 5060 Ti | Blackwell | 0.720 V | 1530 | 1537 | ✅ |
| full tune | 5060 Ti | Blackwell | 0.720 V | 2002 | 2002 | ✅ |
| **stock** | **RTX 3060** | **Ampere** | **0.756 V** | **1260** | **1260** | ✅ |

**Tested three ways, with each prediction registered in the run's own metadata before the
measurement existed:**

- **Manipulation** — change the *floor region* of the curve and the optimum moved **+465 MHz in 12
  of 12 workloads** (`data/frequency-sweeps/abba-20260908/`).
- **Negative control** — change the curve *above* the floor by up to 570 MHz and the optimum moved
  **by nothing** (`repair-suite-p2-20260909/`).
- **Cross-architecture** — a different chip, node and vendor board, hit exactly
  (`rtx3060-20260910/`).

⛔ **The floor voltage is per card and does not transfer.** 0.720 V on the 5060 Ti, **0.756 V on the
3060**. Borrowing the wrong one costs a 270 MHz error. 🔑 **That is the stronger outcome** — a shared
constant would most likely have meant a driver policy, where a differing one means the floor is a
property of the silicon **and the relationship survives it anyway**.

⚠️ The frequency grid is ~155 MHz wide (105 on the 3060), so a prediction need only land within half
a step. Genuine, and coarse. And the floor's *extent* is still read from a decoded curve rather than
set by the experimenter.

### The mechanism's other half: crossbar starvation

Pinning voltage low across a wide frequency range does not only save power. The **crossbar clock**
— the SM-to-memory-controller path, invisible to `nvidia-smi` and readable only via HWiNFO — tracks
the core *while voltage is rising*. Where voltage plateaus and the core keeps climbing, the crossbar
stops, and bandwidth-bound work plateaus with it.

That unified two findings that had looked unrelated: the same flattened curve is **pure benefit** to
compute-bound work (−18% to −26% power at matched clock on `gemm`, 1365 FLOP/byte) and **pure cost**
to bandwidth-bound work (up to −29.6% throughput on `membw`, 0.167 FLOP/byte). One mechanism, seen
from two workloads.

---

## Results

### The headroom gap, three chips

| card | arch | node | TDP | mean efficiency gain at the optimum |
|---|---|---|---|---|
| RTX 5060 Ti | Blackwell | 5 nm | 180 W | **55.9%** |
| RTX 3060 | Ampere | 8 nm | 170 W | **42.2%** |
| RTX 3070 Ti | Ampere | 8 nm | 290 W | **38.9%** |

⚠️ **n=1 per chip. Do not read an architecture trend from three points** — this data cannot separate
node, power budget and architecture. What it supports is that a large gap is present on all three
and is not a peculiarity of one board.

### Stock versus tuned, measured in one session

The first same-session comparison in the project, with the stock leg centred between two tuned legs
so linear drift cancels (`stock-bracket-20260909/`):

| | mean efficiency gain |
|---|---|
| stock | 56.99% |
| full tune | 34.16% |
| **gap** | **~23 points, ±1.3** |

Stock has more headroom in **12 of 12 workloads**. Every earlier stock-versus-tuned figure here was
assembled across days and carries the ~1.47% cross-session drift the project measures on a single
*unchanged* configuration; this one does not.

### The prediction result: a null that now has a mechanism

On the public V100 set, a probe-based Ridge model scores **0.883%** mean regret against a
best-fixed-frequency baseline's **0.837%**. **The model loses**, and 952 MHz is optimal for 24 of 33
workloads.

🔑 **The consumer data explains why.** Across 192 sweeps under four applied curves, a variance
decomposition puts **61.9%** of the optimum's variance on the **configuration** and **19.0%** on the
workload. The V100 set contains exactly **one** configuration — so 62% of the signal is invisible in
it by construction. **"The model loses" is a property of that dataset, not a failure of modelling.**

What follows is a predictor that reads the V/F curve instead of measuring the workload
(`analysis/models/predict_from_curve.py`):

| strategy | mean regret | exactly optimal |
|---|---|---|
| oracle | 0.000% | 100% |
| **read the curve at the load floor** | **0.675%** | **74.0%** |
| best constant per configuration, fitted with hindsight | **0.675%** | 74.0% |
| best single constant, fitted with hindsight | 1.961% | 60.9% |

It beats the best single constant **2.90×** — and **ties a hindsight-fitted per-configuration
constant exactly**, because it picks the identical frequency every time. **It extracts everything the
configuration axis holds and nothing beyond it; its value is needing no measurement.**

🛑 **And the whole axis is worth 1.29 points of regret against a 30–57 point headroom.** Predictor
choice barely matters. Anyone quoting the 2.90× without that sentence is overselling it.

---

## Repository layout

```
headroom/
├── CLAUDE.md                     what is established and must not be re-derived, plus the standards
├── ROADMAP.md                    what is open, in what order, and what is closed with why
├── CONTEXT.md                    why this project exists and how to work on it
├── HANDOFF.md                    how to get running, and the current state
├── run_tests.py                  every suite, one verdict
├── analysis/
│   ├── characterize.py           measures the stock-vs-optimum gap directly, before any model
│   ├── compare_consumer.py       the wrong-range comparison above
│   ├── analyze_constrained.py    best efficiency subject to a performance floor
│   ├── audit_claims.py           asserts every pinned number in the paper against the CSVs
│   ├── claims_consumer.py        5060 Ti  ─┐ three modules, split by HARDWARE, so a claim
│   ├── claims_crosschip.py       3070 Ti   ├─ cannot reach the wrong card through a
│   ├── claims_reference.py       V100     ─┘ shared constant
│   └── models/                   everything that PREDICTS rather than measures — has its own README
│       └── predict_from_curve.py the curve-reading predictor above
├── tools/
│   ├── frequency-sweep/          the sweep harness — CHANGES GPU STATE, always resets
│   ├── stability-logger/         observes only, never applies settings
│   ├── collection-kit/           what goes on the USB stick for a machine that is not this one
│   └── local-model/              delegating mechanical work to a local LLM, and grading it
├── docs/
│   ├── PAPER_DRAFT.md            the write-up the auditor checks
│   └── AFTERBURNER-PROFILES.md   the five V/F curves, decoded from the profile store
└── data/
    ├── frequency-sweeps/         349 sweeps, one directory per session, each with its own README
    ├── afterburner-profiles/     verbatim curve snapshots, so a configuration stays reconstructible
    ├── stability-runs/           logger output
    └── raw/, external/           third-party data, gitignored and fetched, never redistributed
```

**Every data directory carries its own README** explaining what is dataset-grade and what is not.
Several are explicitly marked *not* dataset-grade, and one records a verdict later shown to be wrong.
**Those notes are part of the data.**

Two languages on purpose. Modelling is Python. The collection tools are PowerShell because they must
run on a shop machine with **no setup at all** — no interpreter, no packages. They call `nvidia-smi`,
which ships with the driver.

---

## The auditor, and why the paper cannot drift

`analysis/audit_claims.py` mechanically checks `docs/PAPER_DRAFT.md` against the CSVs.

**A claim stores no expected number.** It stores a function that *renders the exact string the
document must contain*, computed from the data at audit time. The engine asserts that string appears
verbatim and **exactly once**. Edit the paper and the claim fails; change the data and the claim
fails. A stored expected value would only catch the first.

```bash
python analysis/audit_claims.py --coverage
```

It has caught wrong numbers in the paper repeatedly, including the sweep count drifting four times
in one day as data landed. **Matching twice is `AMBIGUOUS`, not a pass.**

| | |
|---|---|
| claims green, with `data/raw/` | **231 of 231** |
| without it, as CI's checks leg runs | **203 of 203** |
| test checks across 17 suites | **587** |

**Green means every claim that exists passes, not that the paper is covered.** 20 numbered sections
still carry no claim at all.

---

## What has actually been verified

| Component | Status |
|---|---|
| Frequency-sweep harness | **Tested across three machines and three architectures** — 346 committed sweeps. Refuses to start when another process is using the GPU, and that guard has fired on real runs, including one at 22.6% from background webviews on 2026-09-10. |
| Stability logger | **Tested, and it has now seen a real failure.** An undervolt deliberately set past the edge (875 mV at 3000 MHz) crashed the display driver on 2026-08-30; 11 events were caught. ⚠️ The UNSTABLE verdict was **reconstructed** from the event log, not emitted by the tool — the operator stopped the run first. |
| Voltage telemetry | **Load-bearing and confirmed on two architectures.** HWiNFO supplies core voltage and the crossbar clock; NVML exposes neither. |
| Tuned configurations | ⚠️ **Not stability tested.** Two 30-minute protocol runs exist from 2026-08-23 on hand-set curves, and nothing verifies those are identical to what is now saved in the profile slots. |
| Python analysis | **Run** on Python 3.12.10 / pandas 3.0.5 / numpy 2.5.2 / scikit-learn 1.9.0. |

---

## Standards this project is held to

Carried over from a previous research project, because they were learned the expensive way:

1. **Baselines first, and pick ones that could embarrass you.** A model that ties a lookup table has
   not earned a slide. `predict_optimal_frequency.py` prints that verdict about itself.
2. **Never claim a number without running the thing that produces it.**
3. **Say the sample size out loud, every time.** N=1 chip is N=1 chip.
4. **A null result is a result.**
5. **Separate measured from inferred in the same breath.**
6. **Record the corrections, not just the conclusions.** Several directory READMEs exist mainly to
   document a result that was wrong and how it was caught. The retraction history is deliberate —
   a reader who can see what changed knows which numbers to trust.

---

## Related work

Checked directly, not just found by search title.

**Prior art — read this one first.** ["Predictable GPUs Frequency Scaling for Energy and
Performance"](https://dl.acm.org/doi/10.1145/3337821.3337833) (ICPP 2019) predicts optimal core *and*
memory frequency from static code features across three architectures, trained on 106
micro-benchmarks. The [follow-up](https://www.mdpi.com/2079-3197/8/2/37) reports XGBoost at R²=0.9646
on Volta. **Read it before claiming anything here is new, and cite it regardless.**

**Independent corroboration of the gap's magnitude.**
[arXiv:2501.08219](https://arxiv.org/abs/2501.08219) — LLM inference under DVFS, 180–2842 MHz on
modern hardware, **42% energy savings for a 1–6% latency increase.** Different hardware, different
workload class, same order of magnitude.

**Methods citation this project needs.**
[JimZeyuYang/GPU_Power_Benchmark](https://github.com/JimZeyuYang/GPU_Power_Benchmark) — documents
that `nvidia-smi` power readings carry a boxcar averaging window and transient response lag. This is
the honest account of what those numbers mean.

**Independent sanity-check numbers for this exact card.**
[hholtmann/llm-consumer-gpu-benchmark](https://github.com/hholtmann/llm-consumer-gpu-benchmark) —
fixed-clock, no DVFS, so not training data, but its 5060 Ti power and thermal figures are worth
comparing against.

**Broader context, not per-chip data.** [MLPerf Power](https://mlcommons.org/2025/03/ml-commons-power-hpca/)
— 1,841 submissions with measured energy, but system wall-plug. Useful for framing.

**Checked and ruled out.** `shashikantilager/gpu-ddvfs` — code only, no dataset committed.

---

## License

| | License | Covers |
|---|---|---|
| Software | [MIT](LICENSE) | `tools/`, `analysis/`, `scripts/` |
| Data | [CC BY 4.0](LICENSE-DATA) | `data/frequency-sweeps/`, `data/stability-runs/`, `data/probes/` |

The dataset is the part nobody else can replicate, so it carries an attribution requirement; the
tooling does not.

## Third-party data

No third-party data is redistributed here. `data/raw/` and `data/external/` are gitignored and
populated by `scripts/Get-Dataset.ps1`. Licenses checked 2026-08-18:

| Source | License | Status |
|---|---|---|
| [GPU-DVFS-Dataset](https://github.com/zyjopensource/GPU-DVFS-Dataset) | **None stated** | Redistribution not permitted |
| [HKBU-HPML/GPU-DVFS-Job-Schedule](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule) | **None stated** | Redistribution not permitted |
| [RightNow-AI/RightNow-GPU-Database](https://github.com/RightNow-AI/RightNow-GPU-Database) | Apache-2.0 | Permitted with notice |
| [kylemcdonald/ethereum-emissions](https://github.com/kylemcdonald/ethereum-emissions) | MIT | Permitted with notice |

**The two DVFS datasets have no license file at all**, which under default copyright means all
rights reserved. The fetch-don't-vendor arrangement is what makes use of them fine, and it needs to
stay that way. Citing them and reporting derived findings is ordinary academic use.

The GPU-DVFS-Dataset's README asks that its paper be cited:

> Zhang, Wang, Lin, Xu, Wang. *Improving GPU Energy Efficiency through an Application-transparent
> Frequency Scaling Policy with Performance Assurance.* EuroSys '24, pp. 769–785.
> [doi:10.1145/3627703.3629584](https://doi.org/10.1145/3627703.3629584)

⚠️ Their GEEPAFS policy improves V100 energy efficiency by **26.7% for 5.8% performance loss** — a
*performance-constrained* result. This project's 44.4% is the unconstrained per-workload optimum.
**They are not the same quantity and must not be presented as if one beats the other.**
