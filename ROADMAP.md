# Roadmap

What this prototype is missing, in the order it should probably be fixed. Written down so the
project has a plan that survives between sessions rather than being re-derived each time.

🔑 **The phases below are a WORK LOG, not a plan.** They are written forwards and corrected
in place, and most of what they hold is closed. **For what is actually open, read "Open right now"
near the bottom** — that section exists because finding the live items inside the phases had
become the hard part.

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
  v1.0.0**: 33 iterations, zero aborted, zero driver resets, zero thermal or hardware-slowdown
  samples (15 of 1765 at the software power cap, which is normal), 96.9% loaded.
  Post-soak throughput did not fall - `gemm` **-0.11%**, `membw` **+0.16%** - which is the check
  that addresses the GDDR7 trap, since silent error correction shows up as lost throughput rather
  than as a crash. Power averaged 140.2 W, peaked 196.1 W of 200 W; temperature peaked 79 C.

  Read it as "no failure observed in thirty minutes", never as "stable".

  **The original tune passed the same test forty minutes later** - 33 iterations, zero aborted,
  zero resets, zero thermal or hardware-slowdown samples, drift `gemm` +0.10% and `membw` -0.28%.
  Two results follow: the split curve's `gemm` advantage reproduces at **+1.41%** under sustained
  unlocked load against the **+1.53%** measured from locked sweep peaks, two protocols sharing no
  methodology agreeing to 0.12 points; and the split curve's `membw` advantage **does not appear
  at all** at free boost (-0.44%), because the plateau lives at 1402-1867 MHz and a boosting card
  sits at 2968-2993 MHz, above it. 5.7.2's -29.6% is a locked-frequency cost, not one paid in
  ordinary use.

  Both of those figures were +1.45% and -0.35% until 2026-08-24, when re-deriving them found the
  paragraph had drawn three numbers from three different aggregation windows while declaring one.
  Corrected, pinned, and the reader now requires the window to be named - see 5.7.6.

  **Still open, and most of the work remains:**
  - The **repaired curve** has not been tested at all.
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
- 🟡 **[CORE] Decide the sampling strategy, and be honest about which question it can answer.**
  **Largely settled by circumstance, 2026-08-23.** Machines reached through the PC-building
  business are **customer** machines, so their curves cannot be touched - the 3070 Ti build will
  very likely be **stock only**. That forecloses the same-SKU tuning arm and commits the
  cross-machine work to *many models, one unit each*.

  **This costs the project less than it sounds, because stock is what that arm needs anyway.**
  The cross-machine question is "does the efficiency curve shape generalise across
  architectures?", and it is answered by stock sweeps; the tuning work in 5.7 is a separate
  single-chip investigation that was never going to scale to customer hardware. What is
  permanently out of reach on this route is chip-to-chip variance in *tuned* headroom, which
  needs repeat units of one SKU that the project controls.

  **Watch for factory OC.** A customer card with a vendor-OC BIOS is not stock in the reference
  sense, and nothing in `nvidia-smi` reports it. The kit already handles this correctly: it
  records the measured peak SM clock and `machine-info.txt` tells the reader to classify from
  that number rather than from the operator's claim.

- **[CORE] The original framing of the sampling decision, kept for the reasoning:**
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

- ✅ **[CORE] Test whether the V100's efficiency curve shape holds on consumer hardware.** Done,
  and it is the largest result in the project. **It holds, on four chips across three
  architectures** — 44.40% mean gap on the V100 against 42.21% on an RTX 3060, 41.57% on an
  RTX 2060 Super, and the 5060 Ti's own figures. §5.4 and §5.5 of the paper.

  🔑 **The answer arrived with a mechanism nobody was looking for.** The efficiency optimum
  is the highest frequency the applied V/F curve reaches at the card's **load-floor voltage** —
  tested three ways, each prediction registered in `docs/REGISTERED-PREDICTIONS.md` *before* the
  measurement: a manipulation that moved the floor and moved the optimum, a negative control that
  changed the curve 570 MHz *above* the floor and moved nothing, and two further chips.

  ⛔ **The floor voltage is per card and does not transfer** — 0.631 / 0.720 / 0.756 /
  0.812 V across the four. Borrowing one card's value predicts another's optimum 270 MHz wrong.

  ⚠️ **The fourth chip found the rule's boundary.** The RTX 2060 Super leaves its floor
  6 mV at a time, so the floor's top edge is known only to ±60 MHz and the verdict turns on a
  single sensor step. Neither confirmed nor refuted — **undecidable**, a third outcome this
  project had not met.
- ✅ **[CORE] The wrong-range argument was tested on the architecture it criticises**,
  2026-09-12. `compare_consumer.py` argues both published consumer DVFS datasets sweep at or above
  stock and so cannot locate an optimum. One is an RTX 2070 Super reporting **3.34%**. The same
  architecture swept from 40% gives **41.57%** — a factor of 12.4, with the threshold
  registered beforehand. Until then the argument compared *different* architectures and asserted
  the range was the difference.
- **[BLOCKER] Never pool the two datasets into one training set.** Different architecture, different
  workload type, different feature space, wildly different sample sizes. Combining them is not more
  data, it is noise wearing a lab coat. Two separate models, compared — never one merged fit.
- **[CORE] Get a methods opinion on the datacenter-vs-consumer comparison** from someone qualified to
  judge it. If it is too apples-to-oranges to carry a paper, that is much cheaper to learn now than
  in the write-up. **Still open, and the question has sharpened rather than gone away:** it is no
  longer datacenter-against-consumer asserting the range is the difference, it is
  same-architecture-against-same-architecture at two swept ranges. That is the stronger claim, and
  the one worth putting in front of someone.
- ⛔ **[CORE] Decide honestly what the collected data can support.** **The premise expired.**
  This assumed **N=6–10 heterogeneous machines** with "no valid train/test split", and planned
  around a breadth dataset that was never built. What exists is **four chips with deep per-chip
  replication** — 300 dataset-grade sweeps on the 5060 Ti against 25, 17 and 14 on the others.

  🔑 **That is a different dataset supporting a different argument.** Breadth would have
  supported a population claim; depth supports a **mechanism** claim, which is what the load-floor
  result is. The original judgement survives where it matters — this is not a second prediction
  model, and there is still no same-SKU repeat — but "it only becomes a real prediction model
  with enough same-SKU repeats" is no longer the interesting sentence about it.

  ⚠️ **n is still 1 chip per architecture**, and that is the weakness any reader names
  first.

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
- ✅ **[CORE] Re-run the probe model under the performance constraint. The null was measured on
  the version of the problem with nothing in it.** Done 2026-08-27,
  `analysis/models/predict_constrained_frequency.py`, with known-answer tests and an 11-mutation gate in
  `analysis/models/test_predict_constrained_frequency.py`. It landed as **two results with opposite
  signs**, and they must be reported together.

  🔑 **Probing wins under a constraint.** At a 95% floor, leave-one-workload-out, a probe-based
  strategy reaches **25.4% mean efficiency gain against the fixed policy's 4.9%** - **87% of the
  23.6-point gap** 5.6.1 identified - **with zero floor violations**. It holds at a 90% floor
  (94% of the gap) and an 85% floor (91%). 5.2's null is therefore a statement about the
  *unconstrained* problem and does not survive the constraint. The module cross-checks itself
  against `analyze_constrained.py` at run time, reproducing 28.5% and 4.9% at 1462 MHz before
  reporting anything.

  🔑 **The FITTING still earns nothing, and this is the stronger half.** The strategy that wins is
  **straight-line interpolation between the four probes** - no model, no training workloads,
  nothing fitted. Ridge *appears* to beat it, 28.1% and 98% of the gap, but does so by **breaking
  the floor on 8 of 33 workloads**, worst by 3.81 points. Efficiency collected below the floor is
  not efficiency the constraint permits, so that number is disqualified rather than ranked; the
  giveaway is negative regret, which at a 90% floor is exactly what it produces. Calibrated with
  a safety margin fitted by inner leave-one-out on the training workloads only, ridge respects the
  floor and drops to **19.6%** - worse than four line segments. **A model that ties a lookup table
  had not earned a slide; one that loses to linear interpolation has earned less.**

  **The mechanism is measured, not asserted**, because "interpolate the probes" would otherwise
  be carried away as a recommendation when it is a consequence of curve shape. Performance is
  predominantly **concave** - 64.1% of second differences curve downward - so a straight line
  between probes sits below the true curve; interpolated performance is an under-estimate **88% of
  the time** by a mean 0.90 points, which biases every choice upward. Under a floor that bias is
  free safety. **On a convex performance curve the sign flips and interpolation would violate the
  floor more often than the fitted model, not less** - asserted against a convex fixture in the
  tests rather than left in prose. The diagnostic prints on every run.

  ⚠️ **The fixed policy is not automatically safe either.** At a 90% floor, chosen leave-one-out,
  it broke the floor on 1 of 33 workloads by 1.37 points - the cost of picking a frequency without
  measuring the workload it will meet. A guarantee learned from 32 workloads is not a guarantee.

  **A hardcoded V100 constant was caught by the mutation gate**, not by review: the infeasible-set
  fallback returned `REFERENCE_FREQUENCY_MHZ` (1530), which is this grid's maximum only by
  coincidence. On a consumer sweep it would have returned a frequency the card never ran. Now the
  grid's own maximum everywhere, so the module carries no V100 number at all.

  **Still to do:** none of this is in the paper. 5.2 currently reports the unconstrained null with
  no indication that it inverts under a constraint, and the README repeats it. Both need the
  second half or they overstate a null.

- **[SUPERSEDED - see above] Original filing:** §5.2 reports the probe model tying a fixed frequency
  at 0.883% against 0.837% mean regret, and that result is honest — but it is the *unconstrained*
  problem, where 952 MHz is optimal for 24 of 33 workloads and there is almost no per-workload
  variation left to exploit. The model tied because the answer is nearly constant, not because
  probing carries no information.

  §5.6.1 then measured the same comparison under a 95% floor and got **28.5% against 4.9%** — a
  **23.6-point gap, 83% of all available gain** — because a fixed policy is pinned by its most
  sensitive workload (`BiCG` needs 1462 MHz; `ViT_t` would be fine at 757). That gap is the
  headroom a predictor could compete for, and **nothing has competed for it.** Neither
  `predict_optimal_frequency.py` nor `curve_model.py` contains any notion of a performance floor;
  both optimise unconstrained efficiency. Confirmed 2026-08-27 by grep, not by memory.

  So the honest current statement is narrower than §5.2's headline: *probing does not beat a
  constant when the objective is unconstrained efficiency.* Whether it beats one under a
  constraint is **unmeasured**, and it is the version of the question the project's own premise
  cares about.

  What the run needs: predict each held-out workload's constrained optimum from the same 4 probes,
  score against `analyze_constrained.py`'s oracle, and compare to the best fixed frequency **that
  also holds the floor on every workload** — not to the unconstrained 952 MHz, which would be a
  baseline that fails the constraint and therefore an easy one to beat. Report it whichever way it
  lands; a second null here is a stronger result than the first, because it would mean probing
  fails even where the signal demonstrably exists.

  ⚠️ **This does not license re-framing §5.2.** The unconstrained null stands as measured and stays
  in the paper. This adds a second measurement beside it; it does not retire the first.
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
  91 claims over §5.4, §5.4.1, §5.4.3, §5.4.4, §5.7.1, §5.7.2, §5.7.4, §5.7.5 and §5.7.6, all green. `--coverage` lists
  every number in an audited section that no claim pins, and every numbered section with no claims
  at all, so the gap is visible instead of assumed: 26 of the paper's numbered sections have none.
  **It found a real error on its first run**, in a section written days earlier: §5.7.1's
  "+12.3% sustainable ceiling" is measured against stock's LAST grid point (15.68 TFLOP/s at
  2588 MHz) rather than its peak (15.71 at 2598), and the sentence did not say which. Corrected
  to +12.1% with the denominator stated.
  **2026-08-23 gave it provenance tracking**, which classifies each run by what its session JSON
  recorded about measurement conditions and flags any claim whose numbers were computed across
  runs of different tiers. **2026-08-24 gave it stability-run readers**, whose `iterationsIn()`
  takes the aggregation window as a REQUIRED argument - §5.7.6 had quoted three different windows
  in one sentence while declaring one, and no default is the structural fix.

  🔑 **The provenance flag then predicted a result before it was measured.** On the morning of
  2026-08-24 it marked §5.7.6's split-curve bandwidth comparison as mixed, with the note that the
  risk ran AGAINST the finding and that the -3.18% deficit was an upper bound rather than a
  measurement. The clean re-measurement that afternoon returned -0.11%. A flag that says which
  DIRECTION an unverified comparison is likely wrong in is worth more than one that only says it
  is unverified.

  Engine tests in `analysis/test_audit_claims.py`, mutation-gated 11/11, then 5/5 and 9/9 on
  later behaviour. Two
  mutations survived the first pass — both because the check asserted an outcome the mutation
  also produced — and both are written up in that file rather than quietly fixed.
  **Still open:** claims cover six subsections. Everything else in the paper is unaudited, and
  a green run says nothing about it.

- ✅ **[SUPPORT] Move the local-model delegation onto llama.cpp.** Done 2026-08-25. The 27B model
  ships a multi-token-prediction head (`nextn_predict_layers = 1`, tensors at `blk.64.nextn.*`)
  that Ollama cannot use on this machine at all — its MTP implementation is in the MLX runner and
  runs only on Apple Silicon, while the CUDA runner has no speculative path. On llama.cpp with
  `--spec-type draft-mtp` the same model gives **40.0 tok/s against 28.9**, n=5 each, spreads 3.1%
  and 0.9%, draft acceptance 0.978 at mean length 1.96, and **byte-identical greedy output** —
  which is the check that matters, because speculative decoding is only free if it is lossless.

  🔑 **The measurement nearly went the other way, and the reason is worth keeping.** The first A/B
  showed MTP *slower*: 15.0 tok/s against 28.1. Acceptance was 0.957, so the draft head was working
  — the card had run out of memory. `llama-server` defaults to four slots and allocates compute
  buffers per slot; at 64K context that pushed past 16 GB and the driver **spilled to system RAM
  without failing**. `nvidia-smi` reported ~400 MiB free throughout, because spilled memory is not
  counted. The honest tell was prefill collapsing 190 → 29 tok/s, on a stage speculative decoding
  does not touch. `-np 1` recovered it. **VRAM-used is not a fit check near the limit** — watch a
  throughput number that should not have moved.

  Quantisation was chosen the same way: `UD-IQ4_XS` is not a preference, it is the largest quant
  that fits at 64K on 16 GB. Graded on `specs/paper-5.7.4-claims.md`, it beats the smaller
  `UD-Q3_K_XL` 87/91 against 71/91, p = 0.0057 — **but only at n=13 per model.** At n=3 it read
  20/21 against 17/21 with overlapping ranges and did not support a ranking. Note the standard
  changes with the measurement: worst-of-A-beats-best-of-B is right for tight repeated readings
  like the tok/s above, and wrong for a coarse discrete score, where it would have discarded a
  real effect. `test_ask_local.py` is mutation-gated over the new two-backend normalisation.

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

- ✅ **[CORE] The sweep did not check that its benchmark produced anything.** **Closed
  2026-09-12, the day after it cost a run.** A sweep locked clocks, sampled telemetry at every
  frequency, wrote a CSV, printed a normal summary and exited **0** — having never launched its
  workload, because `-WorkloadCommand` named an interpreter on one drive and a script on another.
  The card sat at ~18 W throughout.

  🔑 **Nothing downstream would have caught it either, and that is the part worth keeping.**
  The power column is real — it is the genuine idle draw of a locked card — so the file
  parses, plots and joins like any other sweep. Only the empty `bench_throughput` column says
  otherwise. Same shape as the 2026-08-16 defect that sampled telemetry *after* the workload
  finished.

  `WorkloadResultVerdict.ps1` now stops at the FIRST resultless point rather than spending the
  remaining hour on an idle card, classifies the finished run into the session JSON, and exits
  **7** when nothing was measured. It is a separate file so it can be tested without a GPU:
  18 checks, mutation-gated six for six.

  ⚠️ **Sweeps taken before this carry no `workload_result_verdict` and cannot be audited
  for it** — the same unfixable cost as the VRAM guard below shipping late. And it answers one
  question only: *did a measurement come back*. A workload that ran badly and returned a
  wrong-but-positive number still passes.
- ✅ **[CORE] The preflight guard cannot see VRAM, and an idle model walks straight past it.**
  **Closed 2026-09-05.** `Invoke-FrequencySweep.ps1` now reads `memory.free` and refuses below
  `-MinFreeVramMb`, default 4000 - the SAME constant `preflight.py` already used, deliberately, so
  that two guards on one quantity cannot disagree. `free_vram_mb_at_start` goes into every session
  JSON at schema `0.3.2`.

  ⚠️ **THIS ITEM WAS WRONG ABOUT ITS OWN SCOPE, AND THE ERROR RAN THE SAFE WAY.** It said VRAM was
  unchecked; the collection kit's `preflight.py` had checked it since 2026-08-27, before torch is
  imported, with the failure written into its docstring - "with an unrelated 19 GB model resident
  and ~765 MB free, the preflight hung indefinitely". The gap was only ever in the sweep script.
  Written from a grep of one file and generalised to the toolchain.

  🔑 **AND THE PROCESS-NAME HINT HAD BEEN BLIND TO THIS PROJECT'S OWN MODEL FOR ELEVEN DAYS.** The
  offender list named `ollama` and `ollama_llama_server`. The delegation moved to llama.cpp on
  2026-08-25 (commit `c80b569`) and the list did not follow, so `llama-server` - the single most
  likely offender on this machine - was not on it. Added, with `llama-cli`, `koboldcpp`, `lm-studio`.

  ⛔ **THE FIRST VERSION OF THE FIX WAS DEAD CODE ON THE TARGET PLATFORM, AND ONLY RUNNING IT SAID
  SO.** `Get-VramHolders` parsed `--query-compute-apps=used_memory` to name the heaviest holder.
  Under WDDM - the consumer Windows driver model - that field returns the string `[N/A]` for every
  process, because NVML cannot account memory per process when the OS owns the allocator. Tested
  with a python process demonstrably holding 6 GB: its NAME was listed, its memory read `[N/A]`. The
  code parsed the figure, skipped anything under 200 MB, and would therefore have printed an EMPTY
  list under exactly the conditions it was written for. It now reports the figure where the platform
  supplies it (Linux, TCC-mode datacenter cards) and names alone where it does not, saying which.

  Verified on hardware with a 6 GB resident allocation at 3% utilisation and 0% encoder - the exact
  shape both older guards miss: refusal below threshold (exit 6), the holder named, a pass at the
  default on a clean card, `free_vram_mb_at_start=15243` in the JSON, clocks released after.

  **Found while verifying: `-FrequencyCount 1` divides by zero** in grid construction. Pre-existing,
  unrelated, not fixed here, and nothing in the repo has ever passed 1.

  *Original statement of the problem, kept because the reasoning was right:*

- **[SUPERSEDED] The preflight guard cannot see VRAM, and an idle model walks straight past it.**
  `Get-BaselineUtilization` reads `utilization.gpu`, and the separate encoder check reads
  `utilization.encoder` / `utilization.decoder`. **Neither reports memory, and `memory.used` is
  queried nowhere in the script** - the only `memory` fields anywhere in it are memory *clock*.
  Confirmed 2026-08-27 by grep, while correcting CONTEXT.md.

  The guard was built to catch a BUSY GPU and it does that well: a run during a gaming session
  showed 79% baseline utilisation and 8.03 -> 4.84 TFLOP/s. But a **loaded and idle** model is the
  opposite shape - ~0% utilisation, ~14 GiB held. On this machine that is the normal state, since
  `llama-server` serves a 27B on the same card the research measures, so the failure is not
  hypothetical.

  What it would do to a run: ~2.3 GiB remains on a 16.3 GiB card. `gpu_workload.py`'s `gemm`
  allocates ~768 MB and **would run to completion** under memory pressure, producing a number that
  looks like every other number. `membw` allocates ~3 GB and would not fit - failing outright, or
  falling back to system memory the way this driver already demonstrably does, where throughput
  collapses and nothing errors. **A `membw` sweep measuring spilled memory is plausible and wrong**,
  which is the exact failure class this project keeps finding.

  The fix is one field: add `memory.used` to the preflight and refuse above a threshold, naming the
  process the way the encoder check already names its offender. Cheap, and it closes the last
  contamination route the guard does not cover. **Runs already collected cannot be re-checked** -
  no session JSON records VRAM occupancy either, so there is no way to audit past sweeps for this.

- ✅ **[CORE] Record the ENFORCED power limit, not just the maximum settable one.** Done
  2026-08-27. The identity query now asks for `power.limit` and `power.default_limit` alongside
  `power.max_limit`, written as `power_limit_enforced_w` and `power_limit_default_w`.
  `power_limit_w` keeps its old meaning - it has always been `power.max_limit` and redefining the
  key would make every historical session JSON silently wrong. A driver returning `[N/A]` is
  stored as `[N/A]` rather than coerced to 0, because a silent zero reads as a real measurement of
  zero watts. Verified by a two-point sweep, not by inspection: `-DryRun` exits before the JSON is
  written, so it could not have caught a missing key.

  Found 2026-08-26 writing 5.5.3, which wanted to say a `SwPowerCap` engaged at its limit and
  could not source that limit from any committed file - the 3070 Ti OC BIOS reports 350 W max
  against a 310 W enforced figure that exists only in a hand-read note. **Runs already collected
  cannot be repaired.** The updated tool is on the collection USB so a Silent-BIOS session would
  record what the OC session could not.

  🔑 **Verifying it turned up a third tuning knob.** The 5060 Ti enforces **200 W against a 180 W
  default** - the "power limit 111%" this repository's own sweep-tool docstring names as part of
  the standard tune. Paper 5.7 decomposes "tuned" into two knobs, a memory overclock and a core
  V/F curve, and separates them with three sweeps. The power limit is a third, it is part of the
  documented tune, and **no sweep in the repository records it**, so it cannot be ruled in or out
  as a confound in any existing comparison. Whether 5.7's decomposition needs re-stating is a
  paper question and is not answered here.

---

## 🔄 The direction changed on 2026-09-12/13, and this section says how

**Four novelty claims fell in two days, all to searching.** Full account in
`docs/RELATED-WORK.md` (the index, with read status) and `docs/PRIOR-ART-20260912.md` (the log).

| claim | verdict |
|---|---|
| The load-floor rule | ⛔ **prior art** — it is the published RIDGE POINT, van Werkhoven et al. 2022 |
| Per-card floor voltage | ⛔ **prior art** — Leng et al. 2015 (five GTX 780s), Trakosa et al. 2025 |
| Efficiency optimum on consumer silicon | ⛔ **prior art** — Mei/Wang/Chu 2017, GTX 980, board-level, 30 of 42 kernels below default |
| "Nobody swept below stock" | ⛔ **false since 2013** |
| **Causal manipulation + negative control** | ✅ **survives** four full reads and two adversarial passes |
| **The 2060 Super boundary condition** | ✅ **survives** |

### What the project is now about

⛔ **Stop looking for a version of the consumer-optimum claim that survives.** Four reformulations
have failed. Cite Mei and move on.

**The spine is the DATASET, and it got sharper rather than weaker on 2026-09-13.** The claim is no
longer "nobody measured below stock" but:

> 🔑 **For consumer silicon later than Maxwell, no released sweep descends far enough below the
> default clock to contain the efficiency optimum.**

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

⛔ **AND ITS REPLACEMENT FELL THE SAME DAY, TO THE SAME KIND OF ERROR.** The replacement read
*"every consumer part in that release later than Maxwell sweeps at or above stock"* - computed
against a **rated boost clock from a specs database**, i.e. a REFERENCE card, which is the mistake
CLAUDE.md's own hardware section warns about. The dataset authors publish their cards' default
operating clocks - **GTX 1080 Ti 1800 MHz, RTX 2070 Super 1880 MHz** - and against those, each
sweep **brackets** its default with **two of five core points below it**, bottoming out at 89%.

✅ **What survives is a claim about WIDTH, and only that.** Each modern consumer window is ~22
points wide and reaches no lower than 89% of default, so none of them can contain an optimum that
sat at **62% of maximum** on the V100. That is what this project's four chips across Turing, Ampere
and Blackwell provide, and it is a weaker claim than either version it replaces.

🔑 **Two retractions of the same sentence in one day, both from reading a convenient file instead
of the authoritative one.** The first took a normalised features CSV for the measurement data; the
second took a specs database for the cards actually used. **Both were reproducible, and being
reproducible is what made them feel checked.**

That claim is about artifacts rather than priority, so it cannot be lost to a paper turning up —
but as the retraction above shows, it can still be lost to reading the wrong file.

**Three goals, in order:**

1. **Publish the dataset properly** — 359 dataset-grade sweeps, four chips, three architectures
   including Blackwell, below stock, with provenance and a mechanical auditor.
2. **Finish the causal arm** — the floor-ladder rungs turn the one surviving novel claim from
   *directional* into *quantitative*.
3. **Reframe the write-up** from discovery to method-and-data.

### 🧪 The ML thread, reopened with a different question

**It is worth continuing, and the reason changed.** Fan, Cosenza & Juurlink (ICPP 2019) report
SUCCESS predicting per-kernel optima from static code features; this project reports a NULL. Left
unexplained that reads as a contradiction.

⚠️ **Their inputs are far richer**: code features rather than probe points, a 2D core×memory space
rather than 1D, and 106 purpose-built micro-benchmarks rather than a 33×13 matrix *with no feature
columns*. So the interesting question is not "can we beat a constant" but **"what does each class of
input actually buy?"**

The project already holds three predictors of different input classes, all measured:

| predictor | input required | result |
|---|---|---|
| best fixed constant | nothing | **0.837%** mean regret |
| curve-reading rule | the V/F curve, no benchmarking | **0.675%** over 192 sweeps |
| probe-based Ridge | k measured points | **0.883%** — it LOSES |

**The missing fourth row is a workload-feature model on this project's OWN data** — 12 workloads
with computable arithmetic intensity (`gemm` ~1365 FLOP/byte against `membw` 0.167), across four
chips, which the V100 matrix structurally could not support.

🛑 **The deliverable is the BOUNDARY, not a win.** When does per-workload prediction earn its
measurement cost? `predict_optimal_frequency.py` prints a verdict against itself when it ties or
loses, and that must not be "fixed". ⚠️ **n is 12 workloads per chip — leave-one-out on 12 is weak,
and say so every time.**

---

## Open right now — 2026-09-23

**Collected 2026-09-22/23 on the 5060 Ti, all registered in `docs/REGISTERED-PREDICTIONS.md` first:**
- ✅ **§1 rung B of the floor ladder, HOLDS.** Median optimum 1702 as registered, 9 of 12 on it.
  **Rung C is not built**, so the four-rung monotone test is 3 of 4 and unscored.
- ✅ **§6 the load floor survives an NVML offset**, 2026-09-22.
- 🟡 **§7 the offset ladder: registered verdict ⛔ INVALID, revised ✅ all hold.** The registration
  demanded locks stock cannot reach, so it could never pass. Revised scoring is post hoc and is
  reported beside the registered verdict, never instead of it.
- ⛔ **§5 the activity A/B: INCOMPLETE, no registered verdict.** In 3 of 6 active runs the load
  generator started 0.1–0.2 s after the first measured window opened. Fixing the trigger and
  re-running is open.

**The 3070 Ti causal replication (§4a/§4b) is under way. The PC is sold in about two days, so this
is the last chance on this chip.**
- ✅ Curves built and decoded (Amendment 2, before collection), and the profile store is hash-pinned
  (`data/afterburner-profiles/3070ti-profiles-20260923/`).
- ✅ **Shakedown 2026-09-23 passed, 23 of 23 steps**, on the shop PC. Edit 1 at a locked 1395 MHz
  read 0.850 V; Edit 2 peaked at 1515 MHz. **C8, the descending fine sweep, was collected there as
  real Session D data**; it is not scored yet.
- ⏳ **Session D (C4–C7, four 12-workload suites, ~4.5 h) runs unattended 2026-09-24.** Nothing about
  its outcome is known yet. Scoring is `analysis/score_session_d.py`, against §4a/§4b as registered.

**New tooling: Headroom Bench** (`tools/bench-app/`). A click-to-run window on the USB kit that runs
a checked run list, manages HWiNFO logging, reverts to stock and verifies its own end state. It had
four live runs on 2026-09-23, all ending PASS, and ten defects were found and fixed that night.
`tools/bench-app/README.md` lists what has and has not been tested live.

**Open, in order:**
1. **Score Session D** after it lands: join, score, write up, hash gate.
2. 🟡 **Does HWiNFO log automation work with the screen OFF or the PC LOCKED?** Unverified. The
   offset ladder's 48 of 48 log starts and stops ran 13:08–16:58 with a 2 h screen timeout and
   logged input at 14:28, so at most the last ~30 min could have been screen-off, and nothing
   records whether it was. Test it on the 5060 Ti with a short screen timeout before any run
   depends on it. Until then an unattended run sets Screen: Never.
3. **Build rung C** and run it, to complete §1's four-rung test.
4. **Re-run the activity A/B** with a load trigger that starts before the first measured window.
5. **The afterburner decoder cannot read a 3-slot store** or pair offsets with the next record's
   base; the 3070 Ti table was decoded by hand. Teach it both.
6. GPT jobs 12, 14 and 13 (`docs/agents/GPT-PROMPT-NEXT.md`).

---

## Open right now — 2026-09-13

⛔ **SUPERSEDED by the 2026-09-23 section above.** Kept as the record of what was open then.

⚠️ **This header read 2026-09-12 and the list below it is now PARTLY SUPERSEDED.** The live,
priority-ordered list is `docs/TODO-20260918.md` (GPU work: `docs/GPU-WORKLIST-*.md`, one per card); this section is the roadmap-level view and defers
to it on ordering. Three things changed on 09-13 and all three change what is open:

1. ✅ **The framing rewrite is DONE** (`5452004`, `995cdf9`, `0b2f5d8`, `854bd96`). §2.1–2.5 and
   §2.7 now introduce the ridge point as prior art, and §2.7 cites the dataset's own authors *for*
   the narrow-window argument rather than claiming it — the seventh retraction, and the one that
   made the section stronger.
2. 🔓 **The cross-chip causal replication is UNBLOCKED and was never actually blocked.** Two sweep
   READMEs classified the 3070 Ti and 3060 as machines Raymond does not own; they are builds
   assembled to sell, owned outright on the bench. The safety invariant was never engaged. **An RTX
   3070 Ti and an RTX 2060 Super are both available now and both leave soon.** Predictions are
   registered (`docs/REGISTERED-PREDICTIONS.md` §4) and run sheets are written
   (`SESSION-D-RUNSHEET.md`, `SESSION-E-RUNSHEET.md`).
3. ⚠️ **The causal claim's SCOPE is overstated in the paper and must be narrowed** to *strong
   within-chip causal evidence, generalisation uncertain*. Only the 5060 Ti has a causal arm; the
   other three chips are stock observations. A council session flagged this as the first thing a
   reviewer would name.

📝 **And there is now a program deliverable with an external deadline** — the Inspirit project
proposal, drafted at `docs/INSPIRIT-PROPOSAL.md`. It is the only item here whose timing is not set
by this project, which makes it the only one that can make everything else late.

Its own section, because the phases above are a work log and finding the live items inside them had
become the hard part. ⚠️ **Read counts off `python run_tests.py` and
`python analysis/audit_claims.py --coverage`, never off this file.**

**Needs the hardware:**

- 🟡 **[CORE] Build the two floor-ladder rungs on the 5060 Ti.** Registered in
  `docs/REGISTERED-PREDICTIONS.md` before collection, and not yet built. The mechanism says
  shifting the floor region moves the optimum by the same amount; the ladder tests whether it does
  so **proportionally** rather than merely in the right direction. ⚠️ None of the profiles
  is stability tested, and none may resemble the 875 mV at 3 GHz that crashed the driver.
- 🟡 **[CORE] Fine floor sweep on the RTX 2060 Super**, 900–1150 MHz, ~10 minutes. It
  decides the undecidable case in Phase 2 by finding where voltage first leaves 0.631 V, narrowing
  the floor extent from ±60 MHz to about ±10. **It settles this card, not the general
  case** — a card whose voltage moves 13 mV across its whole low range will always make the
  rule hard to apply, and that limit is itself the finding.

**Needs nothing but time:**

- 🟡 **[CORE] Three data-inventory gaps**, all found 2026-09-11, none closed.
  `data/stability-runs/README.md` lists **one run of six**; `data/frequency-sweeps/README.md` does
  not list the **32 sweeps in its own root**; `membw-anomaly-20260819/README.md` skips one sweep.
  Every data directory is supposed to carry a README saying what is dataset-grade. These do not.
- 🟡 **[CORE] §5.4.2 is the last paper section with real numbers and no claims.**
  Everything else carrying numbers is pinned. Its content is mostly the QuickEdit incident, so
  there may be little to pin — but that should be a finding, not an assumption.
- 🟡 **[STRETCH] Coverage is uneven, and the unevenness is the useful number**, not the
  total. §5.5 and §5.4 sit near the bottom. A high claim count is not a covered paper.

**Designed and never run:**

- ✅ **[CORE] The NVML clock-offset question — ANSWERED 2026-09-22.** The write was exercised
  (−300 MHz, registered in advance as REGISTERED-PREDICTIONS §6). It **shifts the V/F curve**:
  locks hold, and voltage at f equals stock voltage at f+300. The planned validation pair's
  criterion, "power at *f* with −300 should match *f*+300 without", is not a valid prediction,
  because the two arms differ by 300 MHz at the same reported voltage: retire it. ⚠️ The VID pairing
  shows the lookup shifted, **not** that the machine state matches; that wider question stays open.
  Next: an **offset ladder**, runnable unattended. ⛔ The mechanism is prior art (170tune,
  RELATED-WORK §10), so it is a capability, not a finding.
  `data/frequency-sweeps/5060ti-nvml-offset-20260922/`.

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
