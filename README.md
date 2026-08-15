# Headroom

**Quantifying the gap between conservative stock GPU behaviour and the empirically-found safe optimum.**

> ## ⚠️ This is a very early prototype
>
> Day-one scaffolding, not a result. Nothing here has produced a finding worth citing yet.
> Specifically:
>
> - The analysis runs on **one published dataset covering a single NVIDIA V100**. Thirty-three
>   workloads on one chip. Nothing in it transfers to a consumer GPU without being retested there.
> - **No original data has been collected yet.** The stability logger works, but it has only been
>   smoke-tested at idle. Zero real stress-test runs exist.
> - The prediction model is a first pass whose main job right now is to **find out whether it beats
>   a fixed-frequency lookup table at all**. It may not. If it doesn't, that is the result and it
>   gets reported, not buried.
> - Interfaces, file layout, and metrics will move. Do not build anything on this yet.
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
├── analysis/                     Python — modelling on the public dataset
│   ├── load_data.py              loading + a validation check against the published files
│   ├── characterize.py           measures the stock-vs-optimum gap directly, before any model
│   └── predict_optimal_frequency.py   the model, and the baselines built to embarrass it
├── tools/
│   └── stability-logger/         PowerShell — original data collection
│       └── Log-GpuStability.ps1  records GPU telemetry during a stress test, reports a verdict
├── scripts/
│   └── Get-Dataset.ps1           downloads the public dataset (not redistributed here)
└── data/
    ├── raw/                      the downloaded public CSVs (gitignored)
    └── stability-runs/           output from the logger — this becomes the original dataset
```

Two languages on purpose. The modelling is Python because that is the ecosystem for it. The logger
is PowerShell because it has to run on a shop machine with **no setup at all** — no interpreter, no
package install, no virtualenv. It calls `nvidia-smi`, which ships with the driver.

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

### Getting the data

The public CSVs are **not redistributed in this repo** — their license has not been checked, and
re-hosting someone else's dataset without that check is not a thing to do casually. Download them:

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

### 2. Per-workload prediction does not beat a fixed frequency — reporting this as a null

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

## License and attribution

The GPU-DVFS-Dataset belongs to its authors and is not redistributed here. Check its license before
using its data in any published write-up.
