# Headroom

**Quantifying the gap between conservative stock GPU behaviour and the empirically-found safe optimum.**

> ## ⚠️ Scope and status — read before citing anything here
>
> Original data now exists and the central mechanism has been measured. What follows is what that
> does and does not license.
>
> - **Two chips, one unit each — which is not a sample.** Most consumer results come from one
>   RTX 5060 Ti (Blackwell). A Gigabyte RTX 3070 Ti GAMING OC (Ampere) was measured on 2026-08-25
>   on a third party's machine and returned; the central result reproduces there — running the
>   compute workload at its efficiency optimum rather than its peak-throughput point costs **21.7%**
>   throughput and saves **37.3%** power. The magnitude differs from the 5060 Ti's; the shape does
>   not. That is one unit of each of two architectures, so it says the *effect* is not an artifact
>   of one board and says nothing about either model line. Chip-to-chip variation on this class of
>   part is published at roughly 11% and remains unmeasured here, because it needs repeat units of
>   one SKU that the project controls.
> - **Everything about *tuning* is still one chip.** §5.7's two-knob decomposition, the split-region
>   curve, and every overclocked measurement are 5060 Ti only. The 3070 Ti was a customer machine:
>   its curves were never touched, only its two vendor BIOS positions compared.
> - **The V100 analysis is a separate dataset** — 33 workloads, one chip, published by others.
>   It is never pooled with the consumer data, and the two are reported side by side rather than
>   merged.
> - **The prediction model lost.** Leave-one-workload-out, it gives 0.883% mean regret against
>   0.837% for a best-fixed-frequency lookup table. That null is the result and is reported as one.
> - **Configuration runs are not contemporaneous.** Switching profiles needs a manual Afterburner
>   change, so comparisons are separated by hours. Effect sizes are far outside plausible drift;
>   the precise percentages are not defended to the last decimal.
> - **Nothing here has been stability-tested yet**, including the configurations producing the best
>   numbers. See the roadmap.
> - Interfaces, file layout, and metrics still move.
>
> Two results discussed in working notes — the split-region curve's `gemm` peak and a tuned
> control re-run — were taken as ad-hoc single points and never written to disk. They are
> excluded from this README and must be re-measured before being cited anywhere.
>
> See [ROADMAP.md](ROADMAP.md) for what needs to happen next and in what order.

---

## What this project actually claims

Vendor boost algorithms are not naive. NVIDIA and AMD already account for individual chip quality —
factory ASIC binning is why two "identical" cards clock differently out of the box. **This project
does not try to beat that engineering, and any version of it that claims to should be rejected.**

What vendors deliberately do not publish is an open, reproducible account of *how much* headroom
their conservative, warranty-safe defaults leave on the table, or what predicts it. Stock behaviour
has to be safe across millions of unknown units, in unknown cases, for years. That forces real
margin, and the overclocking community's consistent ability to beat stock is the everyday evidence
of it.

So the claim is narrow and checkable:

> Measure the gap between stock behaviour and the efficiency optimum, explain what drives it, and
> show the work — on hardware whose results nobody has published.

Not "we built a better GPU Boost."

---

## Repository layout

```
headroom/
├── analysis/                     Python — modelling, and the audit that checks the paper
│   ├── load_data.py              loading + a validation check against the published files
│   ├── characterize.py           measures the stock-vs-optimum gap directly, before any model
│   ├── analyze_constrained.py    best efficiency subject to a performance floor — the useful form
│   ├── predict_optimal_frequency.py   the model, and the baselines built to embarrass it
│   ├── predict_constrained_frequency.py  the same question under a performance floor
│   ├── analyze_sweep.py          frequency sweeps; analyze_fine_sweep.py for the dense grids
│   ├── curve_model.py            the fitted curve the sweeps are read against
│   ├── audit_claims.py           asserts every pinned number in the paper against the CSVs
│   ├── claims_consumer.py        the 5060 Ti claims
│   └── claims_crosschip.py       the 3070 Ti claims, kept SEPARATE on purpose — see below
├── tools/
│   ├── stability-logger/         PowerShell — original data collection
│   ├── frequency-sweep/          PowerShell — the sweep harness
│   ├── collection-kit/           what goes on the USB stick for a machine that is not this one
│   └── local-model/              delegating mechanical work to a local LLM, and grading it
├── docs/
│   └── PAPER_DRAFT.md            the write-up — every consumer measurement lives here, not below
├── scripts/
│   └── Get-Dataset.ps1           downloads the public dataset (not redistributed here)
└── data/
    ├── raw/                      the downloaded public CSVs (gitignored)
    ├── frequency-sweeps/         sweep output, one directory per collection session
    └── stability-runs/           output from the logger — this becomes the original dataset
```

`claims_crosschip.py` is a separate module rather than a section of `claims_consumer.py` so that a
cross-chip claim **cannot** reach a 5060 Ti sweep through a shared constant. Same-file would have
made that a one-character mistake.

Two languages on purpose. The modelling is Python because that is the ecosystem for it. The logger
is PowerShell because it has to run on a shop machine with **no setup at all** — no interpreter, no
package install, no virtualenv. It calls `nvidia-smi`, which ships with the driver.

### Delegating to a local model

`tools/local-model/ask_local.py` sends a specification to a local LLM and saves what comes back.
Nothing it returns is ever committed without being run — for claims work that means `audit_claims.py`,
for a test file it means the mutation gate. Two of the specifications written for it turned out to
contain errors of their own, so the checking catches both sides.

It talks to **llama.cpp** by default and Ollama with `--backend ollama`. llama.cpp is the default
because it is the only one of the two that can use the multi-token-prediction head the model ships
with: **40.0 tok/s against 28.9** on one RTX 5060 Ti, n=5 each, spreads 3.1% and 0.9%, and
byte-identical greedy output, so the speedup is free. Sampling is sent explicitly to both backends
from one constant — a bare GGUF has no baked-in Modelfile, so leaving it to the backend's default
would have quietly changed the sampler and nothing in the output would have shown it.

The same delegation is what the 27B model is graded by, and the grading needed **n=13 per model**
before it separated: two quantisations of one model read as 20/21 against 17/21 with overlapping
ranges at n=3, and only at n=13 did it resolve to 87/91 against 71/91, p = 0.0057 by permutation
test. That is the same lesson as §5.7.6 in a different domain, and it is why the harness runs
repeats by default.

---

## The dataset, and what it cannot do

[GPU-DVFS-Dataset](https://github.com/zyjopensource/GPU-DVFS-Dataset) — a single NVIDIA V100,
33 workloads, 13 core frequencies from 757 to 1530 MHz.

**1530 MHz is the V100's stock boost clock.** Every measurement is at or below stock, so this
dataset says nothing whatsoever about overclocking headroom. It supports underclocking and
efficiency questions only. It also contains no voltage column and no workload feature columns —
just workload name, frequency, performance, and power.

That last point shaped the modelling task. With no workload descriptors available, "predict the
optimum from workload characteristics" is not possible. What *is* possible, and is what
`predict_optimal_frequency.py` does, is: **measure a workload at a few cheap probe frequencies,
then predict where its efficiency peaks** — so you don't have to sweep all thirteen.

Run it and see:

```bash
python analysis/characterize.py
```

```bash
python analysis/predict_optimal_frequency.py
```

"Best efficiency at any cost" is rarely the objective anyone actually has. This asks the constrained
version — most efficiency subject to keeping ≥95% (or 90%, 85%) of stock performance — across both
datasets, and reports the assumption checks alongside the answer:

```bash
python analysis/analyze_constrained.py
```

The paper cites eight frequency sweeps, and prose drifts away from data quietly. Each claim below
is a function that *renders* the string the document should contain, computed from the CSVs at run
time; the audit asserts that string is present verbatim and exactly once, so changing either side
breaks it. `--coverage` also lists every number in an audited section that nothing pins:

```bash
python analysis/audit_claims.py --coverage
```

### Getting the data

The public CSVs are **not redistributed in this repo**, and now cannot be: the license check found
that the two DVFS datasets state no terms at all, which under default copyright means all rights
reserved. See [Third-party data](#third-party-data). Download them yourself:

```powershell
.\scripts\Get-Dataset.ps1
```

---

## The stability logger

Records what the GPU actually did during a stress test, and writes a verdict plus a machine-readable
session record.

```powershell
.\tools\stability-logger\Log-GpuStability.ps1 -SessionLabel "build07-uv900" -AppliedSettings "900mV @ 2700MHz, mem +500" -TestMethod "OCCT 3D Adaptive" -DurationSeconds 900
```

**It observes. It does not apply settings.** You set the clocks and voltage by hand in MSI
Afterburner first, then tell the logger what you set. That is deliberate — a script that sweeps
voltage unattended can hard-lock a machine, and on a customer's build that is not an acceptable
failure mode. Automating the sweep is a decision to make on purpose later, not one to inherit by
accident from a logging tool.

Full detail: [tools/stability-logger/README.md](tools/stability-logger/README.md).

---

## What has actually been verified

Being explicit, because "it's written" and "it's known to work" are different things.

| Component | Status |
|---|---|
| Stability logger | **Tested** on an RTX 5060 Ti (driver 610.88). Two 8–12 s idle runs, CSV + JSON output confirmed well-formed. Two bugs found and fixed this way: an `[ordered]`-dictionary positional-lookup bug that mislabelled every throttle reason, and a `Select-Object` pipeline-stop that killed `nvidia-smi` and produced spurious exit 255. |
| Logger under real load | **Not tested.** Only idle. Verdict logic for thermal throttling and driver crashes has never fired against a real event. |
| Frequency-sweep harness | **Tested on two machines and two architectures** — 64 committed sweeps across an RTX 5060 Ti and an RTX 3070 Ti. It refuses to start when another process is using the GPU, and that guard has fired on a real run (an idle browser at 11%). Its session JSON records the enforced power limit as of 2026-08-27; runs collected before that date record only the maximum settable one and cannot be repaired. |
| Dataset loading + validation | **Schema verified** against the real downloaded files. The efficiency identity (`performance / power`, normalised to 1530 MHz) was confirmed by hand on one row before the check was written into code. |
| Python analysis scripts | **Run** on Python 3.12.10 / pandas 3.0.5 / numpy 2.5.2 / scikit-learn 1.9.0. Both scripts execute clean. Results below. |

---

## First results (public dataset only)

Two findings, one of which is a null. Both are from `analysis/`, on the V100 dataset — one chip, so
neither transfers to consumer hardware without being retested there.

### 1. The gap is large — 44.4% mean efficiency

Running each of the 33 workloads at stock (1530 MHz) rather than at its own efficiency optimum gives
up a mean of **44.4% efficiency** (median 45.7%, range 15.1%–62.8%). Those optima cost a mean of
**13.7% performance** and save a mean of **40.1% power**.

Measured directly from the published data. No model involved.

### 2. Unconstrained, per-workload prediction does not beat a fixed frequency — a null

| Strategy | Mean regret | Exact-match rate |
|---|---|---|
| Stock — do nothing | 44.396% | 0.0% |
| **Best fixed frequency (952 MHz)** | **0.837%** | **72.7%** |
| Probe model (Ridge, 4 probes) | 0.883% | 69.7% |

*Regret = efficiency given up versus that workload's true optimum. Leave-one-workload-out.*

Simply running everything at **952 MHz** recovers 43.56 of the 44.4 available percentage points. The
probe model does not improve on that — it is marginally worse, and its deviations from 952 MHz hurt
more often than they help.

The mechanism is visible in the data: 952 MHz is optimal for **24 of 33 workloads (73%)**, so there
is very little per-workload variation left for a model to exploit. Workload sensitivity is real and
behaves as the literature predicts — the correlation between performance retained at the lowest
frequency and the optimal frequency is **−0.666**, meaning memory-bound workloads prefer lower
clocks — but that signal is not strong enough to beat the constant.

### 3. Under a performance floor it inverts — and the model still loses

The null above is about the *unconstrained* problem, where the curve is flat and one frequency
serves almost everything. Add a floor and the picture reverses, because a fixed policy must hold
its guarantee on **every** workload it might meet and is therefore pinned by the most sensitive one
(`BiCG` needs 1462 MHz; `ViT_t` would be fine at 757).

Leave-one-workload-out, at a **95% performance floor** (`analysis/predict_constrained_frequency.py`):

| Strategy | Mean efficiency gain | Floor violations |
|---|---|---|
| stock — do nothing | 0.0% | 0 |
| best fixed frequency | 4.9% | 0 |
| **interpolation between 4 probes (no model)** | **25.4%** | **0** |
| probe model (Ridge) | 28.1% | **8 of 33** — disqualified |
| probe model (Ridge, calibrated to respect the floor) | 19.6% | 0 |
| oracle (upper bound) | 28.5% | 0 |

So **probing is worth its cost under a constraint** — 25.4% against 4.9% is 87% of the gap between
the fixed policy and the oracle, and it holds at 90% and 85% floors too. But **the fitting is not
what earns it.** Straight lines between the same four probes beat every fitted variant. Ridge only
appears to win by breaking the floor it was supposed to respect; made to respect it, it does worse
than the interpolation.

Efficiency collected below the floor is not efficiency the constraint permits, so those rows are
disqualified rather than ranked — the giveaway is *negative* regret against the oracle, which at a
90% floor is exactly what Ridge produces.

**Why interpolation is the safe one is measured, not assumed.** Performance is predominantly
concave (64.1% of second differences curve downward), so a straight line between probes sits below
the true curve and under-estimates performance 88% of the time. That biases every choice upward,
and under a floor an upward bias is free safety. **On a convex performance curve the sign flips and
interpolation would violate the floor more often than the fitted model** — so "interpolate the
probes" is a consequence of curve shape here, not a general recommendation. The diagnostic prints
on every run.

Taken together: the project's premise survives — knowing the workload is worth most of the
available gain once anyone attaches a performance guarantee to it — while its *modelling* result
gets stronger rather than weaker. A model that ties a lookup table has not earned a slide; one that
loses to linear interpolation has earned less.

**This makes the collected consumer-GPU data more important, not less.** The open question becomes
whether one frequency is similarly dominant on consumer silicon, or whether chip-to-chip variance
makes per-chip tuning worth it there. That is the silicon-lottery question, and this dataset — one
V100 — structurally cannot answer it.

---

## Standards this project is held to

Carried over from a previous research project, because they were learned the expensive way:

1. **Baselines first, and pick ones that could embarrass you.** A model that ties a lookup table has
   not earned a slide. `predict_optimal_frequency.py` prints that verdict about itself.
2. **Never claim a number without running the thing that produces it.** The table above exists
   because of this rule.
3. **Say the sample size out loud, every time.** N=1 chip is N=1 chip.
4. **A null result is a result.** If probing doesn't beat a fixed frequency, report it.
5. **Separate measured from inferred in the same breath.** The gap in `characterize.py` is measured.
   Anything a model outputs is inferred.

---

## Related work

Checked directly, not just found by search title, before being trusted enough to list here.

**Prior art — read this one first.** ["Predictable GPUs Frequency Scaling for Energy and
Performance"](https://dl.acm.org/doi/10.1145/3337821.3337833) (ICPP 2019) predicts optimal core
*and* memory frequency from static code features across three architectures (Kepler, Maxwell,
Volta), trained on 106 micro-benchmarks. The [follow-up](https://www.mdpi.com/2079-3197/8/2/37)
reports XGBoost at R²=0.9646 on Volta. This is the closest existing work to what this project does
— read it before claiming anything here is new, and cite it regardless.

**Independent corroboration of the headroom-gap magnitude.**
[arXiv:2501.08219](https://arxiv.org/abs/2501.08219), LLM inference under DVFS, frequency swept
180–2842 MHz on modern hardware, found **42% energy savings for a 1–6% latency increase**. Different
hardware, different workload class, same order of magnitude as this repo's measured 44.4% figure.
Worth a line in the results section as a cross-check, not as data to build on.

**Methods citation this project actually needs.**
[JimZeyuYang/GPU_Power_Benchmark](https://github.com/JimZeyuYang/GPU_Power_Benchmark) — companion
to *"Accurate and Convenient Energy Measurements for GPUs: A Detailed Study of NVIDIA GPU's
Built-in Power Sensor"* (2024). Documents that `nvidia-smi` power readings carry a boxcar averaging
window, a specific update rate, and transient response lag. `Log-GpuStability.ps1` samples power
from `nvidia-smi` at 1 Hz — this paper is the honest account of what those numbers do and don't
mean, and belongs in the methods section of any write-up.

**Independent sanity-check numbers for this exact card.**
[hholtmann/llm-consumer-gpu-benchmark](https://github.com/hholtmann/llm-consumer-gpu-benchmark)
covers RTX 5060 Ti/5070 Ti/5090 with committed power, temperature, and throttle results. It is
**fixed-clock, no DVFS** — not usable as training data — but its published power draw and thermal
numbers for the 5060 Ti are worth comparing collected data against.

**Broader context, not per-chip data.**
[MLPerf Power](https://mlcommons.org/2025/03/ml-commons-power-hpca/) has 1,841 public submissions
with measured energy, but it's system wall-plug energy — MLCommons explicitly says a per-chip
figure isn't a metric they define. Useful for framing, not for training.

**Checked and ruled out.** `shashikantilager/gpu-ddvfs` — code only, no dataset committed.

---

## License

Split, because the code and the data are different contributions with different reuse needs.

| | License | Covers |
|---|---|---|
| Software | [MIT](LICENSE) | `tools/`, `analysis/`, `scripts/` |
| Data | [CC BY 4.0](LICENSE-DATA) | `data/frequency-sweeps/`, `data/stability-runs/`, `data/probes/` |

The dataset is the part of this project nobody else can replicate, so it carries an attribution
requirement; the tooling does not.

**Before using any run, read the README in its data directory.** Several are explicitly marked not
dataset-grade, and one carries a verdict later shown to be wrong. Those notes are part of the data.

## Third-party data

No third-party data is redistributed in this repository. `data/raw/` and `data/external/` are
gitignored and populated locally by `scripts/Get-Dataset.ps1`, which downloads from each upstream
project. Licenses were checked on 2026-08-18:

| Source | License | Status |
|---|---|---|
| [GPU-DVFS-Dataset](https://github.com/zyjopensource/GPU-DVFS-Dataset) | **None stated** | Redistribution not permitted |
| [HKBU-HPML/GPU-DVFS-Job-Schedule](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule) | **None stated** | Redistribution not permitted |
| [RightNow-AI/RightNow-GPU-Database](https://github.com/RightNow-AI/RightNow-GPU-Database) | Apache-2.0 | Redistribution permitted with notice |
| [kylemcdonald/ethereum-emissions](https://github.com/kylemcdonald/ethereum-emissions) | MIT | Redistribution permitted with notice |

**The two DVFS datasets have no license file at all.** Both repositories exist and are public, and
neither states terms — which under default copyright means all rights reserved, so the CSVs must not
be redistributed. The fetch-don't-vendor arrangement already in place is what makes this fine, and it
needs to stay that way. Citing them and reporting findings derived from them is ordinary academic
use and is unaffected.

The GPU-DVFS-Dataset's README asks that its paper be cited, which costs nothing and is done:

> Zhang, Wang, Lin, Xu, Wang. *Improving GPU Energy Efficiency through an Application-transparent
> Frequency Scaling Policy with Performance Assurance.* EuroSys '24, pp. 769–785. ACM.
> [doi:10.1145/3627703.3629584](https://doi.org/10.1145/3627703.3629584)

Worth knowing what that paper reports, because it is the closest published comparison to this
project's own numbers: their GEEPAFS policy improves V100 energy efficiency by **26.7% on average
for 5.8% performance loss**. That is a *performance-constrained* result. This project's 44.4% figure
is the unconstrained per-workload optimum and is not the same quantity — any write-up must not
present the two as if one beats the other.
