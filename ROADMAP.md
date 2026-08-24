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
- ✅ **[CORE] Deliberately trigger a failure and check it gets caught.** Done 2026-08-20 —
  `tools/stability-logger/Test-LoggerCatchesFailure.ps1`. Three 45-second cases including a
  positive control, without which a classifier stuck on `INCONCLUSIVE` would have passed both
  failure cases: sustained load → `CLEAN` (95% of samples loaded), idle device → `INCONCLUSIVE`
  (0%), load stopping a third of the way through → `INCONCLUSIVE` (28%). The load-fraction
  detector is accurate to the sample.
  **The driver-reset path also fired for the first time**, on an `nvlddmkm` Error 153 context
  reset induced by force-terminating a CUDA process — caused by the test harness itself, which
  contaminated the following case until the harness was reordered and given a settle delay.
  **Two real defects found and fixed:** the crash flag reported a count with no event id, level or
  timestamp, making a false alarm impossible to identify without going to the Windows event log by
  hand; and `session.json` carried a UTF-8 BOM that broke every standard JSON parser, so a
  machine-readable artifact was unreadable by machines.
  **Still open:** an actual hard lock. All three cases exercise the load-fraction and event-log
  detectors, not survival of a real crash, which by construction can only be inferred from a
  truncated log.
- 🟡 **[CORE] Stability-test the applied curves.** Started 2026-08-23. **The split-region curve -
  the configuration section 5.7.6 reports as best - passed a thirty-minute run under protocol
  v1.0.0**: 33 iterations, zero aborted, zero driver resets, zero throttled samples, 96.9% loaded.
  Post-soak throughput did not fall - `gemm` **-0.11%**, `membw` **+0.16%** - which is the check
  that addresses the GDDR7 trap, since silent error correction shows up as lost throughput rather
  than as a crash. Power averaged 140.2 W, peaked 196.1 W of 200 W; temperature peaked 79 C.

  Read it as "no failure observed in thirty minutes", never as "stable".

  **Still open, and most of the work remains:**
  - The **original tune** and the **repaired curve** have not been tested at all. A single
    configuration passing says nothing comparative.
  - No run longer than thirty minutes. Undervolt failures routinely take hours.
  - The degradation threshold is uncalibrated. It was set at 2% before anyone knew what healthy
    drift looks like; this run's 0.11-0.16% suggests it is loose by roughly an order of magnitude,
    but one run does not calibrate a threshold.
  - **A configuration declaration was wrong three times on the day this was built**, twice caught
    only because Raymond contradicted it. Probe before declaring: core clock at a locked 3090
    target reads ~2610 stock / ~2947 tuned / ~2977 split, and memory under load reads 13801 stock
    against 16301 at +2500. Both take under two minutes.

  **Now has evidence behind it, which it did not when this item was written.** The split-region
  curve produced a ~2.5% low outlier on `gemm` in roughly one run in three, against a 0.06% spread
  across three runs on the tuned curve and ~0.5% on the repaired one. An intermittent 2.5% loss is
  exactly what a marginal curve looks like before it becomes a crash, and it sits on the
  configuration currently producing the project's best numbers. This is no longer just good
  practice.
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
- ✅ **[CORE] Build a genuinely bandwidth-saturated kernel and re-run the fine sweep.** Answered
  2026-08-20, and the answer is **it cannot be built on this part**. Three independent approaches
  converge:
  six torch access patterns at 1395 and 2760 MHz all issue-limited (elasticity 0.45–0.96, and the
  read-only reduction is the *worst* at 0.957 rather than the best);
  four concurrent streams reaching 281.2 GB/s where one reaches 218.3, then plateauing;
  and a hand-written `float4` CUDA kernel through CuPy sweeping 1 to 16 outstanding loads per
  thread, which delivers 268.3 GB/s at unroll 1 and 281.9 at unroll 16 — a 5% spread across a
  16× change in memory-level parallelism.
  Methods 2 and 3 agree to within **0.25%** from entirely different mechanisms for raising
  parallelism, at roughly 54% of available bandwidth. That is a hardware ceiling, not a kernel
  defect. **A `membw` sweep below ~2000 MHz is not measuring a memory-bound workload whatever
  kernel is used**, which is a domain limitation to state rather than a bug to fix.
  A conclusion drawn mid-investigation — that concurrency's 1.29× meant a better kernel could
  break the wall — was withdrawn when the better kernel did not.
  **Still open:** what the 281 GB/s ceiling actually is. Neither per-thread parallelism nor
  concurrency, and well below both the DRAM peak and any plausible issue bound. Naming it needs
  hardware counters this project does not read (Nsight Compute).
  Also unresolved: two probes disagree on single-stream copy at 1395 MHz, 299.9 against 218.3
  GB/s, differing in array size and resident array count. Ratios within a probe are unaffected;
  absolute figures across probes are provisional.
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

- ✅ **[BLOCKER] Fix one stress-test protocol and never vary it.** Done 2026-08-23,
  `tools/stability-logger/Invoke-StabilityProtocol.ps1`, protocol v1.0.0, documented in that
  directory's README.

  **A protocol was already written on 2026-08-14 and had never been executed once.** It specified
  OCCT GPU:3D Adaptive and required four manual steps in a fixed order - install, start OCCT,
  start the logger at the right moment, then a separate three-run benchmark comparison to cover a
  gap it named itself. Nine days, zero runs. The diagnosis is that it asked too much, not that
  anyone was negligent, and the fix is that the new one is a single command.

  It also closes that fourth step rather than deferring it, which is the substantive change:
  GDDR7 corrects errors silently, so a memory overclock can pass hours of OCCT with no crash,
  artifact or event-log entry while being **net slower** than stock. Only continuous throughput
  measurement catches that, so the protocol loops this project's own fixed-work benchmark and
  watches post-soak drift.

  **The harness had, three separate times, the exact bug the stability logger exists to catch** -
  an inability to tell "the telemetry says fine" from "there is no telemetry". Held closed now by
  `Test-ProtocolCatchesDeadLogger.ps1`, which reintroduces the original defect and asserts the
  harness refuses without running any load.
- **[CORE] Log a stock baseline for every machine before touching anything.** A tuned result with
  no stock comparison from the same chip measures nothing. This is the "gap" in
  gap-measurement — without it there is no gap, just a number.
- **[CORE] Start with machines already accessible.** Own rig first, then anything nearby. Do not
  wait on new shop builds to begin; shop cadence limits how fast the sample *grows*, not when it
  starts.
- ✅ **[CORE] Build a collection kit that runs on a machine with nothing installed.** Done —
  `tools/collection-kit/`, proven end-to-end on the 5060 Ti on 2026-08-19: UAC elevation, portable
  Python finding CUDA from a non-system drive, clock locking, both sweeps completing, self-check
  reporting success. 13/13 points with performance data on each sweep.
  **The timing assumption that made collection look expensive was wrong.** The execution plan
  budgeted ~5 hours per machine. Measured from the session JSONs: `gemm` 6 min 42 s, `membw`
  5 min 11 s — **about 15 minutes for both sweeps including setup.** Collection is a coffee break,
  not a build-day sacrifice, which removes the main reason it had not started.
  Nothing is installed on the target: Python and PyTorch run from the kit folder and leave no
  trace when it is deleted. A plain copy of a working Python install is relocatable — verified on
  a different drive letter, 412 GB/s against 415 GB/s from the installed copy.

  **The kit is a snapshot and it rots — checked 2026-08-23, three days before a build, and it had.**
  The 4.65 GB Python copy keeps the kit out of version control, so nothing links the tooling on the
  USB drive to the tooling in the repository. Four of its eight files were stale: the sweep at
  schema 0.1.0 against 0.3.0, so it carried **neither `-AppliedSettings` nor the video-engine
  guard** — the two things built specifically to stop the contamination that cost this project two
  days; a `Collect.ps1` predating the 08-19 label fix, which wrote `<label>-oc-gemm-stock_sweep.csv`
  on an overclocked run; a stability logger without the BOM fix, whose `session.json` no standard
  JSON parser can read; and a checklist that never mentions Instant Replay.
  **None of them announce themselves.** Each produces a run that prints `COLLECTION SUCCEEDED` and
  is quietly worth less than it should be. Fixed by `tools/collection-kit/Sync-Kit.ps1`, which
  copies tooling only, re-hashes every file to prove the copy landed, and prints the sweep schema
  version. Run it before every build.
- **[CORE] Decide the sampling strategy, and be honest about which question it can answer:**
  - *Many different GPU models, one unit each* → answers "does the efficiency curve shape
    generalise across architectures?" Cannot say anything about chip-to-chip variance.
  - *Repeated units of one popular GPU model* → answers "how much does headroom vary between
    supposedly identical chips?" This is the silicon-lottery question and it needs same-SKU repeats.
  - These need different builds tested. **Pick one before collecting, not after.**
- ✅ **[CORE] Separate the two tuning knobs, and explain the `membw` plateau.** Done 2026-08-19/20,
  six sweeps. "Tuned" was always two settings — a memory overclock and a core V/F curve — and they
  do **opposite** things to the two workloads. `gemm` gets nothing from the memory overclock
  (±1%) and everything from the curve (−18 to −26% power at matched clock). `membw` gets
  everything from the memory overclock (+3.6 to +16.1%) and is **harmed** by the curve, up to
  −29.6% across 1560–1867 MHz.
  **The mechanism is measured, not inferred.** NVML exposes no voltage (verified by scanning field
  IDs 1–259; 44 readable fields, none a voltage) but HWiNFO does, along with the crossbar clock.
  The flattened curve pins core voltage at 0.720 V across a 49% rise in core clock; the crossbar
  clock — the SM-to-memory-controller interconnect — is pinned with it. Crossbar-to-core ratio
  holds 0.928–0.976 at stock and collapses to 0.726 under the curve. Throughput follows the
  crossbar (elasticity 1.31) not the core (0.51). The two configurations agree exactly where their
  voltages agree, at 1402 MHz, and diverge from 1635 MHz, the first point where stock raises
  voltage and the tuned card does not.
  This unifies the two findings above: `gemm` at ~1365 FLOP/byte never loads the crossbar, so the
  pinned low voltage is pure benefit; `membw` at 0.167 FLOP/byte lives on it, so the same pinned
  voltage is pure cost. **The undervolt's benefit and its harm are one mechanism.**
- ✅ **[CORE] Test a repair derived from the mechanism.** Done 2026-08-20. Restoring the stock
  voltage slope below the flattened region, with four outcomes stated before the run, removes the
  plateau entirely: crossbar ratio returns to 0.939–0.967 and `membw` at 1852 MHz goes 294.5 →
  383.2 GB/s, **+30.1%**, with peak within 0.6% of the tuned card.
  **But it is a trade, not a win, and the trade reverses by workload.** `gemm` under the repaired
  curve returns to stock power at matched frequency (+0.2% to +1.8% across four points, against
  the tuned card's −18 to −26%) and loses 4.5% peak throughput. The original curve beats the
  repaired one on `gemm` efficiency at **every point from 1545 through 2782 MHz, by up to 33.1%**,
  and the widest point of the gap is 2010 MHz, which is exactly where `gemm`'s efficiency optimum
  sits. (An earlier version of this entry said "2317 to 2782 MHz, by 5–18%". That was computed
  from run 7, whose 1852 MHz row is invalid — the lock overshot by +1002.6 MHz — and it
  understated both the band and the magnitude. Corrected against run 8, 2026-08-21.)
  Curve-fixed wins only at the two lowest and two highest targets, including peak throughput, where
  it is 1.5% more efficient at one point out of thirteen.
  **Neither configuration dominates.** That is this project's thesis one level up: not only is the
  efficiency-optimal *frequency* workload-dependent, so is the efficiency-optimal *hardware
  configuration*.
- ❌ **[CORE] Test whether the ~2898 MHz `gemm` ceiling is just a voltage shortfall.** Done
  2026-08-21, and the hypothesis is **refuted**. Do not re-run this test.

  The prediction was that the repaired curve was running ~30 mV short at the top, which would
  explain the deficit without invoking any inherent cost of the repair. Raising the top point to
  0.925 V **lowered** the ceiling, from 2898.5 MHz to 2876.6 MHz — 21.9 MHz the wrong way.
  Locking the curve flat at 925 mV changed nothing further. HWiNFO shows 0.925 V requested
  delivering 0.920 V under ~170 W of load, which is vdroop rather than a missing voltage bin, so
  the raise did reach the card and the card simply does not clock higher for it.

  **The deficit is real, reproduces, and is now unexplained.** Against full tuned's 17.61 TFLOP/s
  at 2948.1 MHz, the best repaired result is 16.90 at 2876.6 — a 71.5 MHz gap. Voltage, thermals,
  power and throttling are all eliminated. Recorded as an open question rather than closed with a
  guess.

  The reasoning above was sound and is left in the history rather than deleted: 0.895 V really was
  identical to the millivolt across both curve variants, and that really did look like a raise
  that never reached the card. It was a good hypothesis that the measurement killed.
- ✅ **[CORE] Run a controlled stock-versus-tuned sweep on the same unit.** Done 2026-08-19,
  `data/frequency-sweeps/oc-comparison-20260819/`. Same chip, same tool, same 13 targets, ~90
  minutes apart in one session, with the applied settings recorded for the first time. At each
  configuration's own sustained maximum: `gemm` **+12.1% throughput / −2.9% power / +15.4%
  efficiency**, `membw` **+17.6% / −3.7% / +22.1%**. That corroborates the earlier uncontrolled
  +13.1% / −2.5% rather than overturning it.
  The more interesting half is at **matched** clock, where `gemm` does the same work for
  −18% to −26% power across four frequencies with clocks matched to 0 MHz and temperatures to
  1 °C — the efficiency gain is mostly power reduction, not the higher peak clock.
  **Still open:** interleaving. All of stock then all of tuned, so thermal drift remains confounded
  with condition. Proper interleaving alternates them.
- **[CORE] Reset any overclocking utility to stock before collecting.** Not hygiene — an active V/F
  curve override silently defeats `nvidia-smi -lgc`, collapsing grid points onto one achieved clock
  while every CSV row still looks well-formed. Verified both ways; see `data/frequency-sweeps/`.
- ✅ **[CORE] Record what was applied, every single time.** `-AppliedSettings` is the one field
  nothing can reconstruct later. A run without it is close to worthless.

  **This item asserted a safeguard that did not exist.** The parameter was described here for
  weeks and was never implemented, so every sweep in the repo predating 2026-08-22 lacks it — which
  is why the curve behind the best `gemm` result on this card could not be recovered the morning
  after it was measured. Voltage telemetry reconstructed the region below 2100 MHz and nothing
  above it. Built 2026-08-22: free text, warned about at preflight *before* the dry-run exit so the
  rehearsal catches a forgotten one, echoed in the result banner, and stored in the session JSON
  alongside `applied_settings_declared` so an absent value cannot later be misread as "stock".
  Schema 0.1.0 → 0.2.0.

  **Wired through the collection kit 2026-08-23**, which had been calling the sweep without it and
  would therefore have recorded `applied_settings_declared = false` on every build-day run.
  `Collect.ps1` now prompts for it and refuses a blank answer, and `machine-info.txt` reports what
  was declared instead of the hardcoded `tuning_state_claimed : STOCK` it asserted before — a line
  that was simply false on the second, overclocked run the checklist itself asks for.
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

- ✅ **[CORE] Add a performance-constrained optimum.** Done — `analysis/analyze_constrained.py`,
  with known-answer tests in `analysis/test_analyze_constrained.py`. See §5.6.
  **At a 95% floor all 33 V100 workloads benefit**: mean 28.5% efficiency gain (median 22.3%, worst
  case still +3.3%) for 3.3% realised performance loss and 23.4% power saved. Two-thirds of the
  unconstrained 44.4% survives a constraint that removes three-quarters of its performance cost.
  **The consumer contrast is the more interesting finding.** Unconstrained, the two workloads'
  optima differ by 146 MHz with under 2% penalty for swapping them. Constrained to 95%, `gemm` can
  do **nothing at all** while `membw` gains **36.4% efficiency for 4.9% loss and 30.2% power saved**.
  Workload-aware selection matters far more under a performance constraint than without one — an
  argument for the project's premise that §5.4.1 alone does not make.
  **The result that matters most is §5.6.1**, added after the above: against a single FIXED
  frequency — the baseline §5.2's null actually used — per-workload selection at a 95% floor gives
  28.5% against **4.9%**, a gap of **23.6 pp, i.e. 83% of all available gain**. A fixed policy must
  hold its guarantee on every workload so it is pinned by the most sensitive one (`BiCG` needs
  1462 MHz; `ViT_t` would be fine at 757). **This reconciles §5.2's null with the project's
  premise:** unconstrained the curve is flat and one frequency serves everything; constrained, the
  flat region is cut off from below and workload identity becomes worth most of the gain. Claim
  neither "tuning is worth it" nor "it isn't" — claim that the answer inverts with the constraint,
  and that the unconstrained measurement is the misleading one. Robust to dropping the four
  flat-top workloads (20.7 pp of 25.8 pp).
  **Against GEEPAFS [6]:** 28.5% for 3.3% loss versus their 26.7% for 5.8%, better on both axes —
  and this must never be written as a win. They are an online policy with no prior knowledge; this
  is an offline oracle holding the whole measured curve. An oracle is supposed to win. The narrow
  1.8-point margin is the real observation: it bounds what a perfect predictor could add over a
  deployed method, and the answer is *not much* — pointing the same way the §5.2 null already did.
  Grid overshoot means every saving is a lower bound; the 100% and 99% floors are flagged
  unquotable because 4 workloads record performance above their own 1530 MHz value.
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

- ✅ **[CORE] Make the paper's numbers mechanically checkable.** Done 2026-08-21,
  `analysis/audit_claims.py` with claims in `analysis/claims_consumer.py`. A claim stores no
  expected value: it stores a function that RENDERS the string the document should contain,
  computed from the CSVs at audit time, and the engine asserts that string appears verbatim
  and exactly once. That one mechanism catches drift in both directions — change the data and
  the rendering stops matching the prose; edit the prose and it stops matching the rendering.
  Matching twice is reported AMBIGUOUS rather than passing, because a claim that appears in two
  places is not pinning the line anyone thinks it is.
  61 claims over §5.4, §5.4.1, §5.4.3, §5.4.4, §5.7.1, §5.7.2, §5.7.5 and §5.7.6, all green. `--coverage` lists
  every number in an audited section that no claim pins, and every numbered section with no claims
  at all, so the gap is visible instead of assumed: 27 of the paper's numbered sections have none.
  **It found a real error on its first run**, in a section written days earlier: §5.7.1's
  "+12.3% sustainable ceiling" is measured against stock's LAST grid point (15.68 TFLOP/s at
  2588 MHz) rather than its peak (15.71 at 2598), and the sentence did not say which. Corrected
  to +12.1% with the denominator stated.
  Engine tests in `analysis/test_audit_claims.py`, 42 checks, mutation-gated 11/11 then 5/5 on
  later behaviour. Two
  mutations survived the first pass — both because the check asserted an outcome the mutation
  also produced — and both are written up in that file rather than quietly fixed.
  **Still open:** claims cover six subsections. Everything else in the paper is unaudited, and
  a green run says nothing about it.

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
