# Headroom — working instructions

**Read this before touching anything in this repo.** It carries what has already been established,
what has already been ruled out, and the standards this project is held to. Re-deriving things
listed here wastes time; re-litigating decisions listed here wastes more.

Owner: Raymond ([imaoofu](https://github.com/imaoofu)). Solo research project for the Inspirit AI
mentorship program, ~3 month window, targeting a written paper. He also runs a small PC-building
business, which is the only reason multiple physical chips are reachable at all.

---

# 🛑 THE HONESTY RULE — this project's entire value rests on it

**Do not state anything you have not verified. Do not soften a null. Do not claim novelty you
have not checked for.**

This is carried over from his previous research project, where it was learned expensively. It is
not decoration:

| Instead of | Do this |
|---|---|
| "this API should work on consumer cards" | Call it. The 5060 Ti returned `NOT_SUPPORTED` for an API the docs implied was fine |
| "the model probably beats the baseline" | Run it. It **lost**, and that loss is now the headline result |
| "nobody has published this" | Search first. The guardband literature already had it |
| "the script works" | Run it. Five separate defects were invisible on inspection and only appeared under test |
| "the GPU was idle" | Measure it. It was 79% busy — he was gaming |

**A null result is a result and gets reported as one.** `predict_optimal_frequency.py` prints a
verdict against *itself* when it ties or loses. Do not "fix" that by tuning until it wins.

**Say the sample size out loud every single time.** N=1 chip is N=1 chip.

---

## What this project claims — and what it must never claim

**The claim:** measure the gap between stock GPU behaviour and the efficiency optimum, on current
consumer hardware, openly and reproducibly, and release the dataset.

**Never claim:**
- ❌ *"We beat NVIDIA's boost algorithm."* Vendor boost already accounts for per-chip factory ASIC
  binning. This project cannot and does not out-engineer it.
- ❌ *"Nobody has quantified this gap."* **Retracted 2026-08-14.** The ~20% voltage guardband and up
  to 25% energy savings are already published, as is chip-to-chip frequency variation (140 MHz /
  ~11%, "Not All GPUs Are Created Equal"). What is genuinely unpublished is narrower: **open,
  reproducible, downloadable data for current consumer hardware.**
- ❌ *"This is undervolting research."* **Voltage cannot be *written* through any documented API**,
  so nothing here controls voltage programmatically — curve changes are made by hand in Afterburner.
  It can now be *read*: HWiNFO exposes core voltage and the crossbar clock, and that telemetry is
  what the plateau mechanism below rests on. This measures frequency versus power, with voltage as
  observed telemetry rather than an independent variable. Say that plainly.

---

## Established facts — do NOT re-derive these

### Results from the public V100 dataset (commit `bf17aa1`, reproducible via `analysis/`)

- **Headroom gap: mean 44.4% efficiency** given up by running at stock (1530 MHz) instead of each
  workload's own optimum. Median 45.7%, range 15.1–62.8%. Costs 13.7% performance, saves 40.1% power.
- **THE NULL:** probe-based Ridge model = **0.883%** mean regret vs. best-fixed-frequency baseline
  = **0.837%**. The model *loses*. Leave-one-workload-out, 33 folds.
- **Why:** 952 MHz is optimal for **24 of 33 workloads (73%)**. A single constant recovers 43.56 of
  the 44.4 available points. There is almost no per-workload variance left to exploit.
- Workload sensitivity is real but too weak to beat the constant: correlation **−0.666** between
  performance-retained-at-lowest-frequency and optimal frequency (memory-bound workloads prefer
  lower clocks, matching the DVFS literature).
- The dataset is a **33×13 matrix with no workload feature columns** and **no voltage column**.
  "Predict from workload characteristics" is structurally impossible on it.

### External datasets — verified downloadable 2026-08-15, fetch with `scripts/Get-Dataset.ps1`

| Dataset | What it is | Why it matters |
|---|---|---|
| `data/raw/` V100 set | 33 workloads × 13 core frequencies, one V100 | The original basis. Core clock only, no voltage. |
| `data/external/gtx1080ti-*.csv` | **Consumer** GTX 1080 Ti, 600 rows, 30 apps, **core 1600–2000 × mem 4000–5500 MHz** | A **2D sweep** — core crossed with memory clock, an axis the V100 set lacks entirely. Plus GTX 2070 Super, 400 rows. |
| `data/external/all-gpus.json` | 2,824 GPUs, numeric specs (sms, tdp, memoryBandwidth, memoryBus, processSize, clocks). Apache-2.0 | Activates the specs-conditioning extension point in `curve_model.py`. **Contains the RTX 5060 Ti.** |
| `data/external/benchmarks.csv` | ~500 consumer cards, 422 with wattage (mining hashrate/W) | External sanity check on perf-per-watt *ordering* across cards. Not training data. |

⚠️ **HKBU-HPML repos use the `master` branch, not `main`.** Raw URLs 404 silently otherwise.

⚠️ **Spec sheets describe REFERENCE cards, not his.** The table lists the 5060 Ti 16GB at boost
2572 MHz / TDP 180 W; his card reports max SM 3090 MHz and a 200 W limit (180 W default). TDP
matches the default limit exactly, which validates the source — but his is a factory-OC board
running above reference. Never treat a spec-sheet clock as the measured clock.

### 🔑 The published consumer DVFS datasets sweep the WRONG RANGE (2026-08-15)

Reproduce with `python analysis/compare_consumer.py`. Every dataset placed on a common axis —
swept range as a percentage of the card's **rated boost clock**, taken from the specs database:

| Dataset | Swept range | Mean gap | At ceiling |
|---|---|---|---|
| GTX 1080 Ti (consumer) | **101–126%** of boost | 1.00% | 60% of apps |
| RTX 2070 Super (consumer) | **95–118%** of boost | 3.34% | 20% of apps |
| Tesla V100 (datacenter) | **55–111%** of boost | **44.40%** | 0% |

**Both published consumer datasets are OVERCLOCKING sweeps.** They start at or above stock and go
up. They structurally cannot locate an efficiency optimum, because the optimum lives *below* stock
(the V100's sat at 62% of its max).

🛑 **Their small measured gaps are NOT evidence that consumer GPUs lack headroom.** They are
evidence that nobody swept the range where headroom lives. Never cite the 1.0% figure as a null,
and never conclude "the V100 finding does not transfer to consumer silicon" from it — that
conclusion is unsupported and backwards.

✅ **This validates this project's own sweep design.** `-MinFrequencyPercent 40` covers the region
every published consumer dataset misses entirely. The justification is therefore stronger than
"no open consumer data exists" — it is **"the consumer data that exists sweeps the wrong range."**
That is a sharper, more defensible contribution claim, and it is checkable by anyone.

### The hardware (RTX 5060 Ti, driver 610.88) — verified by direct probing

| Fact | Value |
|---|---|
| Max SM clock | 3090 MHz |
| Power limit | 200 W current, 180 W default, **range 150–200 W** |
| Supported graphics clocks | **389 discrete**, 180–3090 MHz |
| Compute capability | 12.0 (Blackwell, GB206) |
| PyTorch | 2.11.0+cu128, CUDA available ✅ |

### Control API reality — verified by dumping `nvml.dll` exports and calling via P/Invoke

| Capability | Status |
|---|---|
| `nvidia-smi -lgc` (lock core clock) | ✅ Works. Volta+. **Requires admin.** |
| `nvidia-smi -pl` (power limit) | ✅ Works, 150–200 W. Requires admin. |
| `nvmlDeviceSetClockOffsets` (per-P-state) | ✅ Available. Graphics ±1000 MHz, memory −2000/+6000. Writes return `NO_PERMISSION` un-elevated — **not** `NOT_SUPPORTED`, so it works with elevation. |
| `nvmlDeviceGetGpcClkVfOffset` (global V/F) | ❌ **NOT_SUPPORTED** on this card. Closed on consumer Blackwell. |
| **Read or write voltage via NVML** | ❌ **Impossible.** Zero voltage exports across all 260 NVML device functions; a scan of field IDs 1–259 returns 44 readable fields and no voltage at any scale. |
| **Read voltage via HWiNFO** | ✅ **Works, and is load-bearing.** Core voltage and crossbar clock at 2 s polling, joined to sweeps by timestamp. Five runs carry it. This is the project's central mechanism result — see below. |
| `nvidia-smi -svfd` | ❌ Rubin+ only. Not Blackwell. |
| Per-point V/F curve reshaping | ⚠️ Undocumented NVAPI only (`ClockClientClkVfPointsSetControl`, `0x0733E009`). Out of scope — breaks on driver updates. |

**Bonus, decoded but unused:** Afterburner stores the curve at
`Profiles\VEN_10DE&DEV_2D04&…cfg` as hex — 3224 bytes, header, then 127 points × 3 float32.
His Profile 4 shows `+478` mid-band and `−2500` at top. `MSIAfterburner.exe -profile4 -q` applies
and exits. Scriptable curve control **as a stretch goal only.**

### 🔑 The `membw` plateau: mechanism measured, repair built (2026-08-19 → 08-21)

The largest body of original work in the project. Every table is in
`data/frequency-sweeps/membw-anomaly-20260819/README.md`. Do not re-derive any of it.

**The tuned profile changes two independent things** — memory +2500 and a core V/F curve pinned flat
near 3000 MHz above ~925 mV. Every earlier result treated them as one setting. Separated, they do
opposite things to the two workloads:

| | memory overclock | core V/F curve |
|---|---|---|
| `gemm` (compute-bound) | nothing, ±1% | **the whole win**: −18% to −26% power at matched clock |
| `membw` (bandwidth-bound) | **the whole win**: +3.6% to +16.1% over stock | **actively harmful**: up to −29.6% throughput at 1560–1867 MHz |

**The mechanism, every link measured, with a stock control run:**

    flattened V/F curve
      -> core voltage pinned at 0.720 V across a 49% rise in core clock
      -> crossbar clock pinned near 1340 MHz instead of tracking the core
      -> the SM-to-memory-controller path stops scaling
      -> membw plateaus at ~300 GB/s while DRAM sits at 16301 MHz throughout

The crossbar-to-core ratio is the cleanest single statistic in the study: **0.928–0.976 at stock**
(spread 0.048 — the interconnect tracks the core) against **0.942 collapsing to 0.726 under the
flattened curve** (spread 0.218). The two configurations agree exactly where their voltages agree
— at 1402 MHz both sit at 0.720 V and both deliver ~282 GB/s — and diverge from the first point
where stock raises voltage and tuned does not.

**This unified two findings that had looked unrelated.** `gemm` at ~1365 FLOP/byte never stresses
the crossbar, so the pinned low voltage is pure benefit; `membw` at 0.167 FLOP/byte lives on that
path, so the same pinned voltage is pure cost. **The undervolt's benefit and its harm are one
mechanism seen from two workloads.**

**The repair was derived from the diagnosis, stated in advance, and behaved as predicted.** Restore
the stock voltage slope *below* ~925 mV, leave the flattened region above it alone: plateau gone
(+8.0% / +20.4% / +30.1% at 1545 / 1702 / 1852 MHz over tuned), top end intact (−0.6% at peak).
The predicted *cost* arrived too — `gemm`'s matched-frequency power advantage returned to within 2%
of stock, and tuned beats curve-fixed on `gemm` efficiency across 1545–2782 MHz by up to 33.1%.

**`gemm` peaks of record, all from committed sweeps:**

| configuration | peak | at |
|---|---|---|
| stock | 15.71 TFLOP/s | 2597.8 MHz |
| memory-only | 15.67 | 2583.7 |
| curve-fixed v1 | 16.81 | 2887.1 |
| curve-fixed v2 | 16.82 | 2898.5 |
| curve-fixed + 0.925 V top | 16.90 | 2876.6 |
| **full tuned** | **17.61** | **2948.1** |

**❌ REFUTED 2026-08-21 — the voltage-shortfall hypothesis.** Curve-fixed's `gemm` ceiling sat ~71 MHz
below tuned, and the candidate explanation was a 30 mV shortfall at the top of the curve. Raising
the top point to 0.925 V *lowered* the ceiling by 21.9 MHz (2898.5 → 2876.6); locking it there
changed nothing. 0.925 V requested delivers 0.920 V under ~170 W load — vdroop, not a missing
voltage bin. **The deficit is real and reproduces, and is still unexplained.** Voltage, thermals,
power and throttling are all eliminated. Do not re-run this test.

---

## Ruled out — do not revisit without new information

- **CPU and RAM extension.** Mostly BIOS/UEFI-level, so it needs a reboot per data point, which
  destroys the automated-sweep economics. Many Intel parts had undervolting locked in microcode
  post-Plundervolt. And unstable CPU/RAM causes **silent data corruption and filesystem damage** —
  categorically worse than a GPU driver crash. Scoped out, not deferred.
- ~~**Simultaneous OC+UV recommendations.**~~ **Reopened 2026-08-20 — the premise expired.** Ruled
  out because it "needs Tier-3 curve control *and* voltage readback, and the latter does not
  exist." Both now exist: Afterburner supplies curve control by hand, HWiNFO supplies the readback.
  The split-region curve *is* simultaneous OC+UV. Struck rather than deleted — the reasoning was
  correct when written; what changed was the tooling, not the argument.
- **HWBOT / UL-3DMark as data sources.** No API; paid-enterprise aggregate-only respectively.
- **Pooling the V100 and consumer datasets into one training set.** Different architecture, workload
  type, feature space, and sample size. Two separate models, compared. Never one merged fit.

---

## Bugs found by testing, all invisible on inspection

Recorded because the pattern matters more than the individual bugs: **this codebase's defects do
not look like defects.** Every one of these would have produced plausible, wrong data.

1. `[ordered]` dictionary indexed by integer does **positional** lookup in PowerShell, not key
   lookup — every throttle reason was shifted by one (`0x1` → `ApplicationsClocksSetting` instead
   of `GpuIdle`).
2. `| Select-Object -First 1` stopped the pipeline early, killing `nvidia-smi` mid-write and
   producing spurious exit 255 on successful runs.
3. `[Console]::TreatControlCAsInput` throws "handle is invalid" with no console attached — fatal
   under `$ErrorActionPreference = "Stop"`.
4. **The sweep sampled telemetry *after* the workload finished — recording idle power at every
   frequency.** Would have made the entire dataset worthless while looking completely normal.
5. Default iteration counts too low (0.7–4 s runs) — card never reached steady clocks, launch
   overhead visible in throughput.
6. No check for competing GPU load. Caught only because a test ran mid-gaming session: 79% baseline
   utilisation, throughput down from 8.03 to 4.84 TFLOP/s from contention alone.

**Corrected claim:** the 79% load was initially attributed to Wallpaper Engine. It was a game.
Diagnose before naming a culprit.

---

## Safety invariants — do not weaken these

- **The sweep must always reset clocks.** `try/finally` → `-rgc`, then read back and report if the
  reset did not take. Ctrl+C is intercepted rather than allowed to terminate, so it unwinds through
  that same path. Clock locks do not survive reboot — that is the backstop.
- **`Log-GpuStability.ps1` observes only.** It never applies settings. Deliberate: an unattended
  voltage sweep can hard-lock a machine, and on a customer's build that is not acceptable.
- **`gpu_workload.py` never touches clocks, voltage, or power limits.** Temperature ceiling with
  clean abort, bounded iterations, VRAM freed on error.
- **Never automate tuning on machines Raymond does not own.** Business reputation risk, not just
  technical risk.
- Measured during testing: peak 60 °C / 132 W against an 88 °C ceiling and 200 W limit. Nowhere near
  hardware protection thresholds.

---

## Protocols — locked, do not drift

**Stability testing:** OCCT GPU:3D **Adaptive** mode, **error detection on**, **10 minutes**.
Chosen over FurMark because modern drivers detect and throttle FurMark's constant synthetic load
specifically. Error detection catches outright faults but **cannot** see GDDR7's silent
error-correction retries — a memory OC can be "stable" and net *slower*. Stability testing and
performance testing are separate checks; both are needed.

**Frequency sweeps:** `-MinFrequencyPercent 40` (consumer cards report absurdly low clocks — 180 MHz
on a 3090 MHz card — which are never efficiency-optimal and make fixed-work benchmarks crawl).
Iteration counts must be **held constant across every frequency in a sweep**, or the fixed-work
property that makes duration a valid performance metric is broken.

**Always log a stock baseline per machine before testing tuned settings.** A tuned result with no
same-chip stock comparison measures nothing.

**Change one variable at a time.** Core curve, memory, and power limit are three separate variables.

---

## Code conventions

- **Python:** pandas / numpy / sklearn. `analysis/` holds modelling. Descriptive names, not `df2`.
- **PowerShell:** tools that must run on a shop machine with **zero setup** — no interpreter, no
  packages. They call `nvidia-smi`, which ships with the driver. PowerShell **5.1**: no ternary,
  no `??`, no `&&`. Use `git commit -F <file>` for multi-line messages — here-strings break on
  embedded quotes.
- **Print in complete sentences.** Output gets read by a human deciding whether a run is valid.
- Every tool states its own limitations in its own output. `CLEAN` verdicts say they are not proof
  of stability; sweeps without a workload say they have no performance metric.

---

## The claims auditor — how it works, and the trap in it

`analysis/audit_claims.py` mechanically checks `docs/PAPER_DRAFT.md` against the CSVs. It has
already caught four wrong numbers in the paper, so it earns its keep, but its design is
counter-intuitive and easy to break by "improving".

**A claim stores no expected number.** It stores a function that *renders the exact string the
document must contain*, computed from the CSVs at audit time. The engine then asserts that string
appears in the paper verbatim and **exactly once**. This is what closes drift in both directions:
edit the paper and the claim fails; change the data and the claim fails. A stored expected value
would only catch the first.

- **Matching twice is `AMBIGUOUS`, not a pass.** A claim that matches two lines is not pinning the
  line anyone thinks it is.
- **Bold markers and whitespace runs are normalised away on both sides**, so a claim may span a
  line break and does not need to know where the paper wraps. Line wrapping is presentation.
- **A claim's job is to state what the data says, not to make the audit green.** If a correctly
  written claim does not match the paper, that is a *finding*. Fix the paper, never the formula.

**⚠️ The double-import trap.** Running `audit_claims.py` directly binds it as `__main__`. A claims
module then does `from audit_claims import claim`, which imports a *second copy* of the module with
its own empty registry — claims register into one copy and the runner reads the other, reporting
"0 registered". The `__main__` block re-imports itself by name to avoid this. Do not simplify it.

Coverage as of 2026-08-22: **61 claims green, 27 sections unaudited.**

---

## Repo layout

```
run_tests.py       runs every suite, one verdict - `python run_tests.py`
analysis/          Python modelling on the public V100 dataset
  audit_claims.py     mechanical paper auditor — see "The claims auditor" above
  claims_consumer.py  the claims themselves, one function per sentence of the paper
  test_*.py           11 suites, 276 checks total (plus tools/frequency-sweep)
tools/
  stability-logger/   observes only — telemetry + crash verdict
  frequency-sweep/    CHANGES GPU STATE — locks clocks, must always reset
    gpu_workload.py   fixed-work benchmark (gemm = compute, membw = bandwidth)
  local-model/        delegate spec'd work to Ollama; specs/ holds reusable task specs
scripts/           dataset download
docs/
  PAPER_DRAFT.md      the write-up the auditor checks
data/
  raw/                public CSVs (gitignored, not redistributed — license unchecked)
  external/           downloaded GPU specs (gitignored)
  probes/             kernel-probe results as JSON
  HWiNFO-Data/        gitignored raw dumps; distilled extracts live beside their sweep
  stability-runs/     logger output — becomes the original dataset
  frequency-sweeps/   sweep output — becomes the original dataset
```

**Every data directory carries its own README** explaining what is dataset-grade and what is not.
Keep that true for anything added.

`ROADMAP.md` holds the ordered plan. `README.md` holds results and related work.

---

## Open right now

*Status as of 2026-08-22. The bullet this replaced — "zero real data collected... first real sweep
is the immediate next step" — was true on 08-15 and badly false a week later, while this file was
still being loaded into every session as the authority on project state. If this section ever
disagrees with the data directory, the data directory is right.*

- ✅ **The transcript-only results were re-measured 2026-08-22 and are now committed.** The
  split-region curve peaks at **17.97 and 17.98 TFLOP/s at ~2976 MHz** across two back-to-back
  sweeps — 0.08% apart, and above the 17.84–17.88 the unsaved run had shown. A third sweep on a
  quiet machine reached **18.24 TFLOP/s at 2977.0 MHz**, which is the figure of record and the
  fastest result on this card.

  **The comparison against the original tune was settled later the same day and the earlier
  numbers here are superseded.** The 3.6% first quoted was clean-vs-dirty and is withdrawn; the
  tuned card was then re-measured clean. Final figures, §5.7.6 of the paper: **tuned n=5 gives
  17.96 TFLOP/s mean with 0.76% spread, split n=3 gives 18.23 with 0.13%, a gap of +1.53% with
  ranges that do not overlap** — lowest split 18.22 above highest tuned 18.02.
- ✅ **The 1867 MHz `membw` dip did not reproduce — and the dip MOVED.** The repeat gives 386.7 GB/s
  at 1867, matching memory-only's 385.7. But 1792 came back at 354.5, below its own 1710 neighbour,
  where it had been fine the night before. A defect that lands on a different frequency each time
  is transient, not a property of the curve. Do not attribute either dip to the hardware.
- 🔑 **THE MOST CONSEQUENTIAL FINDING OF 2026-08-22: ordinary desktop GPU load systematically
  depresses measured throughput, and it hits the low and mid band four times harder than the top.**
  Three `gemm` sweeps on identical hardware settings. Runs 1 and 2 ran at ~7% idle baseline
  wandering between 6 and 17%; run 3 ran at 4.3% stable. **Run 3 is faster at all thirteen points.**

  ⚠️ **TWO variables changed before run 3, not one: Wallpaper Engine was closed AND NVIDIA Instant
  Replay was switched off.** The first version of this entry credited the wallpaper alone, which
  was not supported. **The A/B below settled it: Instant Replay is the cause.** The wallpaper state
  varied inside the Instant-Replay-on group and moved the peak by nothing at all. Left here as the
  record of an attribution made too early on two co-varying changes.

  **Measured 2026-08-22, and it is NOT subtle at idle:**

  | Instant Replay | idle SM utilisation | encoder |
  |---|---|---|
  | off | 4.3% mean | 0% |
  | on | **10.8% mean, 15% max** | **21%** |

  It more than doubles idle GPU utilisation and runs NVENC at 21% with nothing being recorded to
  screen. An earlier version of this entry said it "costs nothing measurable at idle" — that was
  wrong, and it was wrong because both numbers behind it (4.5% and 4.3%) had been taken with the
  feature already off. It does trip the sweep tool's 10% baseline guard, so the preflight check
  does catch it, which is better news than the earlier text implied.

  | band | mean uplift from a quiet machine |
  |---|---|
  | 1237-2010 MHz | **+6.0%** (worst point +10.3% at 1545 MHz) |
  | 2167-3090 MHz | +1.5% |

  **This is contention, not noise, and not the hardware.** The evidence: the achieved clock is
  identical across all three runs (2975.9 / 2976.5 / 2977.0 MHz at the top) while throughput moves,
  so the card runs at the same speed and only the share we get changes. Power RISES with throughput
  rather than falling, which is what removing a competitor looks like. Efficiency improves too, so
  it is not a power-for-performance trade. Temperature is eliminated: run 3 was the WARMEST at the
  mid-band points and still the fastest, which is the opposite of throttling. Utilisation does not
  explain it either - run 2 read 99% at the affected points and was still slower than run 3 - which
  is §5.4.3's warning holding up.

  **What this costs the project.** Every cross-configuration comparison in the repo was measured
  under uncontrolled desktop load, so all of them carry an unknown bias of this size. Large effects
  are safe: the 29.6% `membw` plateau is far outside it. These are not:
  - **§5.4's efficiency optimum at 1552 MHz sits exactly where contention bites hardest.** Its
    location and its efficiency-gain figure are less certain than stated.
  - **The matched-frequency power claims of "within 2%" and "within ±3%"** are the same magnitude
    as the power shift seen here (up to 5.0% at 1852 MHz).
  - The −4.5% / −4.0% peak deficits sit in the band where contention is smallest (~1.5%), so they
    are the least affected, but not unaffected.

  **Protocol from now on: close Wallpaper Engine, browsers and media players, switch off NVIDIA
  Instant Replay / ShadowPlay, verify the baseline is stable and under ~5%, and record all of it in
  `-AppliedSettings`.** A passing 10% guard is not enough; run 1 passed at 6% and still lost 10.3%
  at 1545 MHz. **Idle baseline is not a sufficient check either** — Instant Replay is invisible at
  idle. Note that Instant Replay was almost certainly running during every earlier sweep in this
  project, including the stock, tuned, memory-only and curve-fixed legs.

  **The discriminating experiment was run, and Instant Replay is the culprit.** Run 4 re-enabled it
  with the wallpaper still closed. It is slower than run 3 at **all thirteen points** — mean −2.9%
  across 1237–2010 MHz and −1.7% above it.

  **At the peak the attribution is clean, because the wallpaper varied inside the Instant-Replay-on
  group and changed nothing:**

  | run | Instant Replay | wallpaper | peak `gemm` |
  |---|---|---|---|
  | r1 | on | on | 17.97 TFLOP/s @ 2975.9 MHz |
  | r2 | on | on | 17.98 @ 2976.5 |
  | r4 | on | **off** | 17.99 @ 2977.1 |
  | **r3** | **off** | off | **18.24 @ 2977.0** |

  Spread within the three Instant-Replay-on runs: **0.09%**. Gap to the one with it off: **1.48%**,
  at an achieved clock identical to within 1.2 MHz. Closing the wallpaper moved the peak by nothing
  at all; switching off Instant Replay moved it by sixteen times the measurement spread.

  In the mid-band the split is roughly even — Instant Replay accounts for about 2.9 of the ~6.0
  points, with the remainder from the wallpaper and from the baseline wander in run 1.

  **Repeated: n=3 on, n=2 off. 18.24 reproduced exactly.**

  | condition | peak `gemm` | spread |
  |---|---|---|
  | Instant Replay on | 17.97 / 17.98 / 17.99 | 0.09% |
  | Instant Replay off | **18.24 / 18.24** | **0.04%** |

  The gap is **+1.46% at peak, +4.22% mean across 1237–2010 MHz, +1.71% above it**, positive at all
  thirteen points, and roughly 16–36× the within-condition measurement spread.

  🔑 **IT IS ALSO A VARIANCE SOURCE, WHICH IS THE MORE USEFUL HALF.** Mean run-to-run spread is
  **1.82% with it on against 0.35% with it off**. At the two worst points:

  | target | spread, IR on | spread, IR off |
  |---|---|---|
  | 1545 MHz | **6.95%** | **0.13%** |
  | 1852 MHz | **5.97%** | **0.95%** |

  Fifty-three times tighter at 1545 MHz. **This retires the "mid-band is not reproducible" entry
  that this section previously carried as an open problem** — the mid-band is reproducible to
  better than 1% once Instant Replay is off. It also explains the earlier "~2.5% outlier in roughly
  1 of 3 runs" and very likely the wandering `membw` dip, neither of which needs another
  explanation.

  **Limits.** `gemm` renders nothing to screen, so Instant Replay has little new frame content to
  encode here; its cost during a graphics workload could be larger and this does not bound that.
  Two conditions on one chip on one evening. The wandering `membw` dip is very likely the
  same phenomenon and needs no other explanation.
- ✅ **"Neither configuration dominates" was tested and SURVIVES.** This entry previously said it
  "may now be false"; the measurement says otherwise. The split curve beats tuned on `membw` at
  every point (+3.2% to +30.0%) and on `gemm` peak throughput (+2.0%), but **tuned still wins
  `gemm` efficiency from 1545 through 2625 MHz, by up to 30.5% at 2010 MHz** — which is where
  `gemm`'s efficiency optimum sits. The trade is unchanged in character. Do not rewrite §5.7.5.
- 🟡 **The split curve passed its first stability run, 2026-08-23. The other two configurations
  have never been tested.** Thirty minutes under protocol v1.0.0
  (`tools/stability-logger/Invoke-StabilityProtocol.ps1`): 33 iterations, zero aborted, zero
  driver resets, zero throttled samples, 96.9% loaded, post-soak drift `gemm` **-0.11%** and
  `membw` **+0.16%**. Peak 196.1 W of a 200 W limit, peak 79 C.

  Say **"no failure observed in thirty minutes"**, never "stable". The original tune and the
  repaired curve remain untested, so nothing comparative can be said yet, and the 2% degradation
  threshold this was judged against was set before anyone knew what healthy drift looks like.
  What was once called a "~2.5% outlier in 1 of 3 runs" is better described by the mid-band
  reproducibility entry above.
- **27 paper sections are unaudited.** 61 claims are green; `analyze_fine_sweep.py` needs its
  summary exposed before §5.4.1's vertices and confidence intervals can be pinned.
- **The failure detector has never seen a failure.** Deliberately crashing something and confirming
  the logger catches it is still the highest-value single hour available.
- **Instant Replay went 0% -> 14% inside one session on 2026-08-23, and the cause is now known:
  the operator switched it back on** after a deliberate guard test, and confirmed so when asked.
  **It did NOT re-enable itself.** An earlier version of this entry, and the `applied_settings`
  field of `20260823-144349_5060ti-kitverify-idle`, both asserted that it had. That was an
  attribution written without evidence, into the one field whose entire purpose is accuracy, and
  about forty minutes after this file gained a warning against doing exactly that. There is no
  software-hygiene finding here and none should be written into the paper.

  The operational point survives in weakened form: it was off, then it was on, and only the
  preflight check would have caught it. Re-check every run rather than trusting a check from
  earlier in the session - not because the software is untrustworthy, but because a person in
  the loop is enough to change the state.
- **The collection kit rots between builds, and `Sync-Kit.ps1` is the answer.** It is a snapshot
  that version control cannot reach, because of the 4.65 GB Python copy. Checked 2026-08-23 it was
  four files stale, including a sweep with no video-engine guard. Run
  `.	ools\collection-kit\Sync-Kit.ps1 -KitPath F:\headroom-kit` before every build. A synced kit
  is still not a tested kit — run `RUN-ME.bat` once on a machine you understand first.
- **Inspirit deliverable format unknown** — asked repeatedly, still unanswered.
- **Push directly with `git push`.** `gh` is installed but auth never completed; Windows Credential
  Manager already works. Do not route through `gh`.
