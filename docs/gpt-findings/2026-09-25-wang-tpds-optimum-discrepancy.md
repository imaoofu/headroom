# Job 21: Wang et al. TPDS optimum against the released GTX 1080 Ti grid

**Later audit:** [Job 22](2026-09-26-wang-figure4-review-audit.md) verifies the
historical model results and clarifies that model/grid agreement requires
snapping to the sampled clock grid, uses the model's training measurements,
and does not establish how the authors obtained their meter-based 4.3%.
The 4.351999% diagnostic rounds to **4.4%**, not 4.3%, at one decimal.
It also separates the notebook's `gamma` reduction from static power.

**Checked 2026-09-25.** The task was to identify the 20 applications behind Figure 4 of
[Wang et al., arXiv:2104.00486](https://arxiv.org/pdf/2104.00486), compare their optima
with the released 30-application GTX 1080 Ti CSV, and decide how §2.7 should use the
paper. **The Figure 4 name-to-index mapping is recoverable from publication-era
repository history.** For those 20 named applications, 14 raw GPU-power grid
optima lie at the highest sampled core clock, whereas Figure 4 places most
modeled optima near the lowest allowed clock. The historical plotting code
also reveals a stateful parameter change behind its savings. No paper or
data file was edited.

## What the primary paper actually says

- §5.1.1, printed page 10 (PDF page index 9), distinguishes a **real GTX 1080 Ti**
  interval with normalized core-frequency lower bound **0.89** from a continuously
  adjustable **simulated** interval with lower bound **0.5**. It says a commercial
  power meter supplied real measurements before simulation.
- §5.1.2, the same page, gives `P_idle = 37 W`: 24 W CPU and 13 W GPU. This is
  the modeled idle power of a CPU–GPU pair. Equation (4), printed page 4, also
  says average **active** CPU runtime power is incorporated into the fitted
  `P_G0` term. The 37 W is not a documented per-row correction to the released CSV.
- §5.1.3, printed page 10, says 20 benchmark applications with good model fits
  were used as an application library. The PDF gives parameter ranges but
  does not name them or explain how the 20 were selected. Publication-era
  source history supplies the index key below; it does not document a
  goodness-of-fit threshold.
- §5.2 and Figure 4, printed page 11 (PDF page index 10), report a 4.3% mean
  energy conservation in realistic GTX 1080 Ti experiments and 36.4% in the
  widened simulation. The exact sentence is: **“For both intervals, the optimal
  core voltage/frequency is relatively low, close to the allowed lowest
  setting.”** Thus the statement applies to **both** intervals, but Figure 4
  shows **model-derived settings**, with unnamed indices 1–20. It is not a
  table of raw per-application CSV argmins.

## Dataset and reproducible raw-grid comparison

I cloned [`GPU-DVFS-Job-Schedule`, branch `master`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/tree/master)
to a directory under `%TEMP%`, outside this repository, at commit
`7ae3c9c8ebe766909cc7e3ee6fa0c752c62154c5`. The raw
[`gtx1080ti-dvfs-real-Performance-Power.csv`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/master/csvs/gtx1080ti-dvfs-real-Performance-Power.csv)
has SHA-256 `e5d3a6804ba09704dac0cf8687255c9ad18302ba066ff4102d85401dd61fe468`
for the **git-clone bytes**. It contains 600 rows: 30 application names × five
core clocks (1600–2000 MHz) × four memory clocks (4000–5500 MHz). There were
no tied minima at the recorded precision.

For each application, I minimized `time/ms × power/W` over all 20 measured
core/memory combinations and classified the winning core clock as low (1600),
interior (1700/1800/1900), or high (2000). The CSV's `power/W` comes from the
original repository's [NVML sampler launch](https://github.com/HKBU-HPML/NV-DVFS-Benchmark/blob/master/dvfs_benchmark.py)
and [power extractor](https://github.com/HKBU-HPML/NV-DVFS-Benchmark/blob/master/gpuPowerExtracter.py),
which averages sampled device power into that column. It is a **GPU power
telemetry** comparison, not the paper's commercial-meter CPU–GPU energy.

| Measured-grid energy rule | Applications | Low core | Interior core | High core |
|---|---:|---:|---:|---:|
| CSV `time × power`, all released GTX 1080 Ti names | 30 | 8 | 4 | **18** |
| Same rule, Figure 4's mapped 20 names | 20 | 3 | 3 | **14** |
| `time × (power + 37 W)`, all names: hypothetical uniform-addition sensitivity | 30 | 8 | 3 | **19** |
| Same +37 W sensitivity, Figure 4's mapped 20 | 20 | 3 | 3 | **14** |

The +37 W row is **not** a reconstruction of the paper's system scope. The paper
does not publish the active CPU power trace or its commercial-meter readings
per configuration. The fitted parameter table was recovered from repository
history but does not substitute for either missing measurement.
Its 37 W value is an idle model term, while active CPU power enters `P_G0`.
Adding 37 W uniformly is useful only to test whether such an offset reverses
the raw-grid direction; it does not.

The mapped 20 give the direct raw-grid comparison. The all-30 table also gives
a selection-free bound: **any** 20 of these 30 include at least 8 high-edge
winners under CSV GPU power, because only 12 are low or interior. Under the
uniform +37 W sensitivity, at least 9 of any 20 are high-edge winners. This
is a persistent **raw-grid versus modeled-result mismatch**, not a matched
system-power experiment.

## Figure 4's application names recovered from repository history

The current `master` branch omits `apps.pkl` and has since changed its
[`plot.ipynb`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/master/plot.ipynb).
I inspected [commit `8a0a2e0` (26 April 2021, “finalize the TPDS version”)](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/tree/8a0a2e0ef402b84c428496ce037c6753f19f0873),
which contains the saved [`apps.pkl`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/8a0a2e0ef402b84c428496ce037c6753f19f0873/apps.pkl),
[`plot.ipynb`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/8a0a2e0ef402b84c428496ce037c6753f19f0873/plot.ipynb),
and [`figures/single_exp.pdf`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/8a0a2e0ef402b84c428496ce037c6753f19f0873/figures/single_exp.pdf).
The saved pickle contains 30 ordered GTX application names. The notebook
loads that object, iterates `list(tmp_dict.values())`, and plots the first
20. Its committed figure has the same bar pattern and index order as the
paper's Figure 4. This source and figure match supports the following
mapping; the PDF alone does not supply it. The code simply truncates the
ordered list and does not show how the paper's “good fitting results”
criterion was applied.

| Figure 4 index | Recovered application | Raw CSV winning core |
|---:|---|---|
| 1 | BlackScholes | low |
| 2 | SobolQRNG | low |
| 3 | backpropBackward | interior |
| 4 | backpropForward | high |
| 5 | binomialOptions | high |
| 6 | cfd | high |
| 7 | conjugateGradient | high |
| 8 | convolutionSeparable | high |
| 9 | convolutionTexture | high |
| 10 | dxtc | high |
| 11 | eigenvalues | high |
| 12 | fastWalshTransform | interior |
| 13 | gaussian | interior |
| 14 | histogram | high |
| 15 | hotspot | high |
| 16 | matrixMulGlobal | high |
| 17 | matrixMulShared | high |
| 18 | mergeSort | high |
| 19 | nn | low |
| 20 | pathfinder | high |

The other ten released GTX names are `quasirandomGenerator`, `reduction`,
`scalarProd`, `scanScanExclusiveShared`, `scanUniformUpdate`,
`sortingNetworks`, `srad`, `stereoDisparity`, `transpose`, and `vectorAdd`.

## Reproducing the publication-era modeled savings

I inspected the saved parameters with a restricted pickle reader and
reproduced the historical notebook's `solve_dvfs()` calls in their plotted
order, **narrow then wide on the same mutable application dictionaries**.
Within `solve_dvfs()`, both calls divide `app["p0"]` by 4.75 and
`app["gamma"]` by 4.65. The wide call therefore uses values divided
**twice**. The committed notebook output itself prints 7.2503 and 36.4834,
and its plotted bars match the paper's Figure 4.

| Calculation on the 20 saved applications | Mean modeled saving |
|---|---:|
| Historical plot, narrow call after one division | **7.250%** |
| Historical plot, wide call after a second division on the same objects | **36.483%** |
| Diagnostic: narrow on original parameters, undoing the notebook division | **4.352%** |
| Diagnostic: wide on a fresh copy with only one division | **10.957%** |

The published **36.4%** is reproduced by the historical plotted wide path.
The published **4.3%** is reproduced numerically by the diagnostic narrow
path on original parameters, **not** by the saved plotted narrow path
(7.250%). That numerical match does not establish how the authors obtained
their stated 4.3%; the required independent system-power measurements are
unpublished. The 36.4% calculation changes **both** the frequency interval
and the fitted power terms, with a second reduction inherited from the
narrow call. These four numbers represent distinct parameter conditions,
not four repeated measurements. Current `master` modifies this code and
yields different numbers, so it is unsuitable for reproducing the
publication-era figure.

## Verdict and proposed wording, not a paper edit

**The discrepancy is real for the 20 applications mapped to Figure 4:** 14
of 20 raw `time × GPU power` winners sit at the high core edge, while the
historical model's narrow Figure 4 solutions sit at the lowest allowed core
setting for 17 of 20. The measured-grid and fitted-model results use
different power inputs and scopes; the paper's unpublished
active CPU–GPU meter readings prevent a matched energy recalculation. Its
37 W idle term cannot reconstruct them. The historical notebook adds a
separate caution: the published 36.4% follows a second reduction of two
fitted power parameters, and the narrow plotted mean does not reproduce
the paper's 4.3% statement. The real-window limit is firmly documented;
Figure 4 does not validate raw CSV optima or directly diagnose their high
edge results.

**Proposed replacement for the Wang passage in `docs/PAPER_DRAFT.md` §2.7:**

> Wang et al. [22] document a real GTX 1080 Ti core interval starting at
> 0.89 times their declared 1800 MHz default and attribute their reported
> 4.3% mean energy saving partly to its narrow range. Their simulated
> wider interval reaches 36.4% in Figure 4, with modeled core optima near
> the lower allowed bound in both intervals. Their publication-era artifact
> identifies Figure 4's 20 applications. For those same applications,
> however, direct minimization of `time × GPU telemetry power` on the
> released core/memory grid puts 14 of 20 at the *highest* sampled core
> clock (3 lowest, 3 interior). This does not reproduce the fitted figure:
> the paper uses a different power scope and model, and it does not release
> the meter readings needed for a matched comparison. The historical
> plotting notebook reproduces 36.4% after two sequential reductions of
> fitted power parameters; its narrow plotted mean is 7.25%, not the
> paper's stated 4.3%. We therefore use [22] as prior art for the narrow
> real interval and a wider simulated scenario, not as direct validation
> that the released raw grid hides a lower-frequency optimum.

This wording replaces the “authors against their own artifact” and direct
4.3%→36.4% analogy as evidence for the CSV's optimum. It keeps the authors'
credit for the real-interval limit and wider simulation, and it distinguishes
their modeled energy from this project's board-power efficiency.

**Proposed replacement for the unresolved-discrepancy paragraph in `CLAUDE.md`:**

> ⛔ **Wang Figure 4 versus the released CSV, checked 2026-09-25.** The
> 2026-09-19 paragraph counted raw GPU-power grid optima correctly at
> 8 low / 4 interior / 18 high for all 30 GTX 1080 Ti applications, but
> left the selected 20 and measurement scope unresolved. The 2021
> publication-era commit `8a0a2e0` preserves `apps.pkl`, `plot.ipynb`,
> and the plotted figure, mapping Figure 4 indices to the first 20 named
> applications. Their raw grid has **3 low / 3 interior / 14 high** core
> winners; adding 37 W uniformly leaves those counts unchanged, but that
> idle term does **not** reconstruct the authors' active system-energy
> measurements. The paper's “near lowest” wording describes a fitted
> optimum in both modeled intervals, not a raw table. The historical
> notebook divides fitted `p0` and `gamma` once for narrow and **again**
> for wide on the same objects: its plotted means are **7.250%** and
> **36.483%**, whereas the paper states **4.3%** and **36.4%**. A diagnostic
> unmodified-parameter narrow call yields 4.352%; that numerical match
> does not verify the missing meter trace. The real interval and wider
> simulated scenario remain prior art, but Figure 4 cannot be treated
> as validation of raw CSV optima or as a matched system-power comparison.

## Access and check log

Accessed 2026-09-25: the [paper PDF](https://arxiv.org/pdf/2104.00486)
(§5.1.1–§5.2, equations, and rendered Figure 4); both source repositories
on `master`; `GPU-DVFS-Job-Schedule`'s CSV, README, `model.py` and `plot.ipynb`;
and `NV-DVFS-Benchmark`'s sampling and extraction code. The latter clone
resolved to commit `bc70c555d590be38900eff55300d61dc18e56aea`.
I fetched the schedule repository's full Git history and read
`8a0a2e0:apps.pkl`, `:plot.ipynb`, and `:figures/single_exp.pdf`; the pickle
was opened with a restricted class allowlist. I compared the rendered 2021
figure with the paper's Figure 4 and ran the historical solver in the
notebook's narrow-then-wide order. Both clones, downloaded PDF, rendered
pages, and calculation scripts were kept under
`%TEMP%/headroom-job21-20260925`, outside this repository. No file under
`data/` was written.

Exact web search queries in this pass: `"GPGPU Performance Estimation with
Core and Memory Frequency Scaling" Wang Chu 2020 pdf benchmark 20
applications`; `"GPGPU Performance Estimation with Core and Memory
Frequency Scaling" 20 benchmarks 1080 Ti application list`. I opened the
primary [earlier Wang–Chu preprint](https://arxiv.org/pdf/1701.05308)
as a mapping lead; it reports an older 12-kernel experiment, not this
paper's 20-name key. Direct URL openings and local repository searches
were identifier checks, not additional keyword web searches.

Before writing, `python run_tests.py --quiet` passed **1,059 checks across
34 suites**; `python analysis/audit_claims.py`,
`python analysis/build_data_manifest.py --check`, and
`python analysis/verify_citations.py --check` all exited successfully.
These gates check repository consistency, not Wang's unreleased system-power
trace. The historical application mapping and model outputs were checked
separately against the publication-era source.

---

## Claude review, 2026-09-25: accepted, and one step further

**Reproduced independently, from a fresh clone of the same repository:**
- Commit `8a0a2e0` exists, is dated 2021-04-26 and is titled "finalize the TPDS version."; its
  `apps.pkl` holds 30 ordered names, and the notebook plots the first 20. The pickle uses only
  `numpy` scalar and dtype globals, and was loaded with an allowlist.
- The 20-name mapping is right. The 2021 `figures/single_exp.pdf`, rendered here, matches the
  paper's Figure 4 feature for feature: narrow core at 1.0 for index 11 and raised at 6 and 18, and
  wide core at 0.5 for indices 1, 2, 12 and 19. A re-run of the solver gives those same indices.
- The raw-grid counts are 8/4/18 for all 30 and **3/3/14** for the mapped 20, with the same result
  under +37 W. They were computed on this repository's own copy of the CSV, which is content-identical
  to the clone (LF here, CRLF in the clone, so the hashes differ as CLAUDE.md records).
- The four modelled means **7.250 / 36.483 / 4.352 / 10.957%** reproduce, as do 17 of 20 narrow
  optima at the lowest setting and every quotation, checked against the arXiv PDF text.

**What the review adds, and why it changes the verdict.** GPT computed the undivided narrow mean
(4.352%) but did not ask where that condition puts the optima. Under it, **only 3 of 20 narrow
optima sit at the lowest setting**. Fourteen are at 1886 MHz or above, and every one of the 20 lands
within one 100 MHz grid step of the raw CSV argmin, 10 exactly. The wide case on unmodified
parameters is **7.174%**. So:
- the condition that reproduces the paper's 4.3% **agrees with the raw grid**;
- Figure 4's "close to the allowed lowest setting" narrow optima exist only after the static-power
  division;
- widening the interval alone moves 4.35% → 7.17%, and the remaining rise to 36.4% is the division.

The discrepancy is therefore **between their Figure 4 and their own fitted parameters, not between
their paper and their CSV**. That removes the "structurally the same as 1.00% → 44.40%" analogy
outright, which GPT's wording had only softened. GPT also missed the §5.2 sentence *"The derived
optimal voltage/frequency settings coincide with our measurements"*. It is quotable, but not
checkable without their meter data. The same limit applies to everything above: it shows which
condition reproduces 4.3%, not how the authors obtained it.

**Applied:** `analysis/wang_tpds_figure4.py` reproduces every number above from a local clone and
writes nothing. The following were corrected by the retraction protocol:
- `PAPER_DRAFT.md` §2.7;
- CLAUDE.md, where the open discrepancy is now resolved and the analogy struck;
- `RELATED-WORK.md` §7;
- a pointer in `PRIOR-ART-20260913.md`;
- `GPT-QUEUE.md`.

GPT's proposed wording was not used verbatim. It kept 7.25% as a comparison against 4.3%, which
compares a plotted figure with a stated one, and it left the direction of the released-parameter
optima unstated.
