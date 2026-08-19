# Roadmap

What this prototype is missing, in the order it should probably be fixed. Written down so the
project has a plan that survives between sessions rather than being re-derived each time.

Status key: **[BLOCKER]** must happen before anything downstream is trustworthy ·
**[CORE]** on the critical path · **[STRETCH]** worth doing if time allows.

---

## Phase 0 — make the prototype real

Nothing here is research. It is the difference between "code exists" and "code is known to work."

- ✅ **[BLOCKER] Install Python and actually run the analysis scripts.** Done — Python 3.12.10
  installed, both scripts executed (pandas 3.0.5, numpy, sklearn 1.9.0). Commit `bf17aa1`.
- ✅ **[BLOCKER] Check what `predict_optimal_frequency.py` actually reports.** Done — outcome (c):
  it loses. The leave-one-workload-out probe model (Ridge) gives 0.883% mean regret vs. 0.837% for
  the best-fixed-frequency baseline. Reported as the null it is, not hidden. Separately, the
  headroom gap itself was measured: stock vs. each workload's own optimum gives up a mean 44.4%
  efficiency (range 15.1–62.8%).
- 🟡 **[CORE] Run the stability logger under real load.** Partly done — one hour under sustained CUDA
  inference on the overclocked card: 1760 samples, **zero telemetry failures**, clean exit. The OC
  held (2962–3000 MHz, 64 °C peak, no throttling, no crash).
  **It found a defect in the logger, which was the real value.** The run's workload finished after
  13 minutes and the card idled for 47; the verdict came back `CLEAN` with whole-run averages that
  described neither period. Nothing distinguished "survived an hour" from "the load died early" —
  the exact event the tool exists to catch, since a crashing stress test leaves the GPU idle.
  Fixed: `loaded_fraction` plus loaded-only statistics are now recorded, and an under-loaded run
  returns a new `INCONCLUSIVE` verdict (exit 3) instead of `CLEAN`. Both paths verified directly.
  Also established that the `GpuIdle` throttle bit reads `0x1` at 98% utilisation under compute
  load, so it cannot be used to detect idleness.
  **Still open:** the throttling path has never fired (the card never neared its limits — 139 W of
  a 200 W budget) and no run has used the locked OCCT protocol.
- **[CORE] Deliberately trigger a failure and check it gets caught.** Push an undervolt until
  something actually crashes, and confirm the logger records it. A detector that has never seen a
  positive case is not known to work. This is the single highest-value hour in Phase 0.
- ✅ **[BLOCKER] Verify the fixed-work benchmark actually measures anything.** Done — and it did not,
  at first. Two instrumentation bugs made every number wrong (`nvidia-smi` inside the timed region
  cost `membw` 50.5% of its duration; power was averaged over a wider window than performance,
  understating load power 16%). Both fixed and verified against rated hardware limits: `gemm` 74% of
  peak FP32, `membw` 92% of peak bandwidth. Frequency response confirmed end-to-end — 2.38× the
  clock gave 2.57× the throughput. Commit `33ffe56`.
- ✅ **[CORE] Sweep `membw`.** Done. The contrast holds and is 3.1× — elasticity of throughput to
  core clock 0.35 for `membw` against 1.09 for `gemm`. But the previous wording, "clock-insensitive",
  was too strong and is corrected: `membw` gained 35% throughput over a 123% clock increase, so it is
  sub-linear, not flat. Below ~1200 MHz it is issue-limited rather than bandwidth-limited.
- ✅ **[CORE] Find the actual efficiency optimum.** Done — 13 points × 2 workloads, 464–3090 MHz.
  **Optimum at 1552 MHz for both**, 60% / 56% of each workload's sustained maximum. `gemm` gains
  46.5% efficiency there; `membw` gains 41.6% for a performance cost of only 11.3%. **The V100 result
  reproduces on consumer silicon** — `membw`'s 41.6% / 11.3% / 37.4% against the V100's
  44.4% / 13.7% / 40.1% at 62% of maximum. Run `python analysis/analyze_sweep.py`.
  **Correction:** the previous version of this entry claimed the 40% floor was too high to contain
  the optimum. It was not — 1552 MHz sits inside the old range, and the fault was three points, not
  the floor. "Optimum lands on the lowest frequency tested" implies a truncated range only for a
  *dense* sweep; on a sparse one it is equally consistent with the optimum lying between points one
  and two. Lowering the floor still helped, for the different reason that it proved the optimum
  interior rather than an edge.
- ✅ **[CORE] Fine sweep to separate the two workloads' optima.** Done — 13 points × 1200–1900 MHz ×
  2 workloads × 2 passes, counterbalanced. **The optima do differ: `gemm` 1488 MHz, `membw`
  1634 MHz, −146 MHz (95% CI −187 to −93)** — and `membw` prefers the *higher* clock, opposite the
  V100's −0.666 prediction. Two caveats carried forward, not buried: `membw` retains 78% at the
  equivalent relative floor so it belongs to neither of the V100's sensitivity classes, and the
  penalty for using one workload's optimum for the other is under 2%. Run
  `python analysis/analyze_fine_sweep.py`. Swept 1200–1900 rather than 1300–1800 because a band
  tight around the peak has no curvature for a fit to use.
- ✅ **[CORE] Check whether the fine sweep was CPU-launch-limited.** Done — **it was not**, so the
  §5.4.1 optima stand. Sweep utilisation ran below 100% even after subtracting monitoring cost, and
  the residual looked clock-dependent (0.9% at 1200 MHz → 7.5% at 2754 MHz), which would have meant
  suppressed high-clock throughput and a downward-biased `membw` optimum. Two independent checks say
  no. The counterbalanced passes already contained the answer: at 1897 MHz they recorded 99.0% and
  92.7% utilisation with throughput of 342.3 and 342.3 GB/s — utilisation and work are decoupled.
  A direct probe then held total work constant while varying kernel size 32×, moving the launch
  count from 320 to 10240: throughput spread **0.5%**, and CUDA graph replay changed it **−0.1%**.
  Notably the CPU spent **90% of wall time** submitting at the smallest kernel size and still did not
  limit anything — high CPU cost is not a CPU bottleneck. Run
  `python tools/frequency-sweep/probe_launch_bound.py --rounds 3`; data in `data/probes/`.
  **Methodological lesson:** `utilization.gpu` over ~25 samples is too coarse to carry an argument
  about lost work. It is a hint, not a measurement.
- **[CORE] Build a genuinely bandwidth-saturated kernel and re-run the fine sweep.** This is now the
  sharpest open question. `membw` is issue-limited below ~1990 MHz, so the V100 prediction was
  tested outside the domain where its premise holds. A kernel that saturates DRAM across the whole
  swept range would test it properly, and would say whether the contradiction above is about
  consumer silicon or about this particular kernel.
- ✅ **[CORE] Add a `LICENSE` file** and check the GPU-DVFS-Dataset's license. Done — MIT for the
  software (`LICENSE`), CC BY 4.0 for the collected data (`LICENSE-DATA`), split because the dataset
  is the contribution that warrants attribution and the tooling is not.
  **Both DVFS datasets turned out to have no license file at all** — GPU-DVFS-Dataset and
  HKBU-HPML/GPU-DVFS-Job-Schedule. Both repos exist and are public; neither states terms, which
  under default copyright means all rights reserved and no redistribution. Verified that
  `data/raw/` and `data/external/` are gitignored, so nothing has ever been redistributed and the
  README's claim was accurate. That arrangement is now load-bearing and must stay. The other two
  sources are Apache-2.0 and MIT. Full table in `README.md`.
  Also resolved a citation gap: the dataset's README asks that its paper be cited, and it was
  referenced only by GitHub URL. It is Zhang et al., EuroSys '24, doi:10.1145/3627703.3629584 —
  **and that paper reports 26.7% mean V100 efficiency gain for 5.8% performance loss**, a
  performance-constrained figure that is not the same quantity as this project's unconstrained
  44.4%. Recorded in reference [6] so the write-up cannot accidentally imply it beats them.

---

## Phase 1 — collect original data

The part nobody else can replicate, and the reason the project is worth doing at all.

- **[BLOCKER] Fix one stress-test protocol and never vary it.** Same test, same duration, same
  ambient conditions, every run. Consistency matters more than which test gets picked. Write the
  chosen protocol into `tools/stability-logger/README.md` so it survives being forgotten.
- **[CORE] Log a stock baseline for every machine before touching anything.** A tuned result with
  no stock comparison from the same chip measures nothing. This is the "gap" in
  gap-measurement — without it there is no gap, just a number.
- **[CORE] Start with machines already accessible.** Own rig first, then anything nearby. Do not
  wait on new shop builds to begin; shop cadence limits how fast the sample *grows*, not when it
  starts.
- **[CORE] Decide the sampling strategy, and be honest about which question it can answer:**
  - *Many different GPU models, one unit each* → answers "does the efficiency curve shape
    generalise across architectures?" Cannot say anything about chip-to-chip variance.
  - *Repeated units of one popular GPU model* → answers "how much does headroom vary between
    supposedly identical chips?" This is the silicon-lottery question and it needs same-SKU repeats.
  - These need different builds tested. **Pick one before collecting, not after.**
- **[CORE] Run a controlled stock-versus-tuned sweep on the same unit.** Two validation sweeps
  incidentally straddled this: the tuned configuration sustained 2942 MHz at 162.91 W / 17.42 TFLOP/s
  against stock's 2617.6 MHz at 167.03 W / 15.40 TFLOP/s — **+13.1% throughput for −2.5% power**.
  That is the project's whole thesis in one comparison, and it is currently worth nothing, because
  the runs were separate, background load differed (6.2% vs 3.6%), and thermal state was not matched.
  Interleaved on one chip under matched conditions, it becomes the headline result. This is now the
  highest-value single measurement available.
- **[CORE] Reset any overclocking utility to stock before collecting.** Not hygiene — an active V/F
  curve override silently defeats `nvidia-smi -lgc`, collapsing grid points onto one achieved clock
  while every CSV row still looks well-formed. Verified both ways; see `data/frequency-sweeps/`.
- **[CORE] Record what was applied, every single time.** `-AppliedSettings` is the one field nothing
  can reconstruct later. A run without it is close to worthless.
- **[STRETCH] Commit real runs to the repo as they accumulate.** The dataset is the contribution.
  An open, consistently-collected set of consumer stability results does not currently exist —
  [gpu-undervolt-db](https://github.com/iBlessi/gpu-undervolt-db) has the right schema and, as of
  this writing, 8 rows.

---

## Phase 2 — connect the two halves

Turning two separate models into one project with a single research question.

- **[CORE] Test whether the V100's efficiency curve shape holds on consumer hardware.** This is the
  unifying question. The public dataset is datacenter silicon running compute workloads; the
  collected data is consumer silicon running gaming workloads. Whether the shape transfers is
  genuinely unknown and worth asking.
- **[BLOCKER] Never pool the two datasets into one training set.** Different architecture, different
  workload type, different feature space, wildly different sample sizes. Combining them is not more
  data, it is noise wearing a lab coat. Two separate models, compared — never one merged fit.
- **[CORE] Get a methods opinion on the datacenter-vs-consumer comparison** from someone qualified to
  judge it. If it is too apples-to-oranges to carry a paper, that is much cheaper to learn now than
  in the write-up.
- **[CORE] Decide honestly what the collected data can support.** At N=6–10 heterogeneous machines
  there is no valid train/test split — it is a validation and case-study set, not a second
  prediction model. It only becomes a real prediction model with enough same-SKU repeats.

---

## Phase 3 — analysis the prototype doesn't do yet

- **[CORE] Add a performance-constrained optimum.** "Best efficiency" is the wrong objective for
  most real users. "Lowest power subject to keeping ≥95% of stock performance" is the question
  people actually have, and the dataset can already answer it.
  **There is now a published number to compare against:** GEEPAFS [6], the paper the V100 dataset
  comes from, reports **26.7% mean efficiency gain for 5.8% performance loss** on the same chip.
  That is the right benchmark for a constrained result, and it is a much harder bar than the
  unconstrained 44.4%. Landing near or below it is a perfectly good outcome — they had an online
  policy with hardware feedback; this would be an offline oracle on the same data, so the two are
  not measuring the same difficulty either. Say which is which.
- **[CORE] Report uncertainty, not just point estimates.** Leave-one-workload-out gives 33 regret
  values — report the distribution, not only the mean. The worst case matters more than the average
  when the failure mode is an unstable machine.
- **[STRETCH] Try a non-linear model** (small tree ensemble, or a shape-constrained fit) and compare
  honestly against the Ridge baseline. Only after the linear version's result is known — a fancier
  model that beats an unrun baseline proves nothing.
- **[STRETCH] Model the curve shape parametrically** rather than predicting 13 independent points.
  Efficiency curves are smooth and single-peaked; a model that knows that should need fewer probes.
- **[STRETCH] Add temperature as a variable.** The public dataset has none. Collected data will, and
  thermal state plausibly moves the optimum — an angle the public dataset structurally cannot reach.

---

## Phase 4 — write-up

- **[CORE] State plainly which results are validated and which are exploratory.** Public-dataset
  results have a real train/test split. Collected-data results, at small N, do not. Say which is
  which in the same breath as the number.
- **[BLOCKER] Never frame this as beating vendor engineering.** The claim is "measured and explained
  a gap that is not published," and that claim is defensible. The other one is not.
- **[CORE] Include the negative results.** If the probe model ties a lookup table, that goes in. A
  paper reporting one honest null is worth more than one reporting three unverified wins.
- **[STRETCH] Contribute findings back to `gpu-undervolt-db`.** Costs almost nothing and makes the
  work useful to people outside the project.

---

## Known limitations to keep stating

Not a to-do list — things that stay true and should never quietly disappear from the write-up.

- One V100 is one chip. Nothing about chip-to-chip variance can come from the public dataset.
- The public dataset tops out at stock. **No overclocking claim can be sourced from it, ever.**
- The stability logger cannot observe a crash that takes the machine down instantly. It infers one
  from a truncated log, which is weaker evidence, and the verdict should keep saying so.
- A clean 10-minute run is not stability. Undervolt failures routinely take hours to appear.
- Consumer GPU telemetry is driver-mediated and not a lab instrument. `nvidia-smi` power figures are
  the card's own estimate, not a measurement from a shunt.
