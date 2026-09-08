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

### The hardware (Zotac RTX 5060 Ti Twin Edge OC) — verified by direct probing

⚠️ **Driver: 616.56 as of 2026-09-02.** This heading said 610.88 until then, which had been stale
since 2026-08-30 - the update landed between suite replicates r1 and r2, not before r3, and was
found only by reading `driver_version` out of the sweep JSONs. r1 is the odd one out. It does not
explain the between-replicate variance and appears to run the wrong way (mean absolute gain
difference 1.99 points for the driver-differing pair against 3.07 for the driver-matched one), so
attribute nothing to it. Read the driver off a sweep JSON, never off this file.

| Fact | Value |
|---|---|
| Board | **Zotac Twin Edge OC**, dual fan. ⚠️ The 3090 MHz below is the driver's LOCK-TARGET CEILING, not a boost clock and NOT evidence of a factory overclock - it reads 3090 at stock and with a curve applied alike. Measured stock boost is ~2584 MHz against a 2572 MHz reference rating. |
| Max lock target | 3090 MHz (top of the supported-clock table) |
| Measured stock boost | ~2584 MHz under gemm, 2026-08-29 |
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

### 📌 Coverage — the canonical block, and the ONLY place in this file a registry count lives

**These four numbers are themselves audited**, by `analysis/claims_repo.py` against this file. They
cannot go stale without CI failing, so unlike every earlier version of this paragraph they can be
quoted. Nothing else in CLAUDE.md restates them; if you find a second copy, delete it rather than
update it.

| quantity | value |
|---|---|
| claims green, 0 failures, with `data/raw/` | **225 of 225** |
| ...and where `data/raw/` is absent, as CI's "checks" leg runs | **197 of 197** |
| sections with no claim at all | **20 numbered sections are still unaudited** |
| §5.7 and its subsections carry | **84 claims between them and §5.5 carries 40** |

⚠️ **THE TOTAL WENT STALE FOUR TIMES BEFORE IT WAS PINNED: 87 -> 119 -> 185 -> 204**, and on
2026-08-30 this file carried two contradictory values for it at once. That history is the reason the
claims exist and is kept deliberately - a reader who sees the sequence knows the total is not the
interesting part.

**Green means every claim that EXISTS passes, not that the paper is covered.**

🔑 **The totals hide how uneven the coverage is, and the unevenness is the useful number.** A high
claim count is not a covered paper. Snapshot from `--coverage` on 2026-09-05, **not pinned** — these
need a full audit pass to compute, so read them off the tool: **§5.5 at 15 of 352, §5.4 at 24 of 350,
§5.6.1 at 20 of 147.** §5.5 is now the least-covered section in the paper.

✅ **§5.4.1 was the worst at 2 of 122 and is now 32 of 122**, done 2026-09-05. The blocker this file
recorded for it — `analyze_fine_sweep.py` needing its summary exposed — had already been removed
some time before, so the section sat at the bottom of the coverage table for weeks with nothing
actually stopping it. **Check whether a recorded blocker still exists before treating it as one.**

⚠️ **Two figures that stood here did not reproduce and have been replaced.** This paragraph said §5.7
carried 80 claims and §5.5 carried 53; by registry attribution they are 84 and 30, and by
pinned-numbers far larger. The derivation was never written down, so it could never be checked. **A
figure nobody can reproduce is worse than one that is merely out of date** — the counting method now
travels with the number, in `claims_repo.sectionFamilyCounts`.

**Check counts are NOT pinned and must be read off `python run_tests.py`.** They come from a
different runner counting a different thing, and a second implementation inside the auditor would be
two methods that can disagree - the exact failure this project keeps finding elsewhere.

Claims live in **THREE** modules, split by which hardware the data came from - `claims_consumer.py`
for the 5060 Ti, `claims_crosschip.py` for the 3070 Ti, and `claims_reference.py` for the public
V100 set. Keep them apart; a shared constant is how a claim would silently read the wrong hardware.

---

## Repo layout

```
run_tests.py       runs every suite, one verdict - `python run_tests.py`
analysis/          Python measurement + audit on the public V100 dataset
  audit_claims.py     mechanical paper auditor — see "The claims auditor" above
  claims_*.py         the claims themselves, one function per sentence of the paper - THREE
                      modules, split by hardware: _consumer (5060 Ti), _crosschip (3070 Ti),
                      _reference (public V100)
  models/             everything that PREDICTS rather than measures — has its own README
  test_*.py           16 suites, 541 checks (539 without data/raw) - NOT pinned, see above
tools/
  stability-logger/   observes only — telemetry + crash verdict
  frequency-sweep/    CHANGES GPU STATE — locks clocks, must always reset
    gpu_workload.py   fixed-work benchmark (gemm = compute, membw = bandwidth)
  local-model/        delegate spec'd work to a local LLM - llama.cpp by default, Ollama
                      via --backend ollama; specs/ holds reusable task specs
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
Keep that true for anything added. ⚠️ **Two sweep directories had drifted out of that rule until
2026-09-05** - `curve-rebuild-20260823` and `memonly-clean-20260823`, both of them read by live
claims and both central to the §5.7.6 paragraph that has been wrong twice. The convention holds
again; check it with a loop over `data/frequency-sweeps/*/` rather than assuming.

**Every tool directory carries one too**, for the same reason. `tools/local-model/README.md` leads
with the VRAM hazard rather than with usage, because that is the part that costs data.

## The five root documents, and which answers what

Ask the right file and none of them need re-deriving. This list exists because the layout above
named only two of them.

| file | answers |
|---|---|
| `CLAUDE.md` | **what is technically established** and must not be re-derived, plus the standards |
| `ROADMAP.md` | the ordered plan - what is open, in what order, and what is closed with why |
| `README.md` | results and related work - the outward-facing summary |
| `CONTEXT.md` | **why this project exists** and how to work on it; portable copy of context that otherwise lives only in local memory on one machine |
| `HANDOFF.md` | **how to get running** on another machine or in a new chat, and the current state |

🛑 **None of them is the authority on a COUNT.** `python analysis/audit_claims.py --coverage` and
`python run_tests.py` are. Every one of these files has carried a stale claim total at some point,
and CLAUDE.md has carried two contradictory ones simultaneously.

---

## Open right now

*Status as of 2026-08-30. The bullet this replaced — "zero real data collected... first real sweep
is the immediate next step" — was true on 08-15 and badly false a week later, while this file was
still being loaded into every session as the authority on project state. If this section ever
disagrees with the data directory, the data directory is right.*

*⚠️ **It rotted again, and the second time it contradicted itself.** On 2026-08-30 this section still
said "26 paper sections are unaudited, 87 claims are green" and "the failure detector has never seen
a failure", while the auditor section above said 119 claims and the data directory held a real
driver crash caught earlier the same day. Two stale numbers for the same quantity, in one file, is
worse than one: neither can be trusted and nothing flags which is which. **Read counts off
`python analysis/audit_claims.py --coverage` and `python run_tests.py`, never off this file.***

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
  1 of 3 runs".

  ⛔ **IT DOES NOT EXPLAIN THE WANDERING `membw` DIP. That attribution is retired, 2026-08-24.**
  Every verified-quiet `membw` sweep on the 10-point grid has a worst point, and across the seven
  of them the deepest single-point departure runs **-0.36%, -0.59%, -1.00%, -1.15%, -2.17%,
  -5.93%, -6.91%**. All seven had encoder and decoder verified at 0%. **The variation survives the encoder guard, so
  it is something else, and its cause is unidentified.**

  ⚠️ **AN EARLIER VERSION OF THIS ENTRY SAID "TWO OF FIVE RUNS CARRY A 6-7% DIP".** That was a 3%
  threshold laid across a continuous distribution of five samples; the sixth sweep landed at
  -2.17%, between the two groups it had invented. **Report the spread, not a count** - and be
  suspicious of any bimodal split drawn from single-digit n.

  **Limits.** `gemm` renders nothing to screen, so Instant Replay has little new frame content to
  encode here; its cost during a graphics workload could be larger and this does not bound that.
  Two conditions on one chip on one evening. The wandering `membw` dip is NOT the same phenomenon
  - see the retraction above - and still needs an explanation.
- 🔑 **THE MEMORY-ONLY "CEILING" WAS READING LOW, AND 5.7.6's `membw` CLAIM WAS WRONG BECAUSE OF
  IT (2026-08-23).** That section said the split curve "holds the repair", landing within 0.4% of
  memory-only at seven of ten points. The reference was contaminated 08-20 data compared against
  a clean 08-22 split-curve run. Re-measured clean, memory-only rose **+3.30% mean (+1.86% to
  +6.25%)**, matching 5.4.4's +4.22% mid-band figure.

  **How it was caught matters more than the number.** The tell was that the rebuilt repaired curve
  EXCEEDED the supposed ceiling at all ten points. Nothing beats a ceiling, so the reference was
  suspect - not the measurement.

  ⛔ **AND THEN THAT CORRECTION WAS ITSELF WRONG. 2026-08-24 WITHDREW IT.** The 08-23 fix cleaned
  the ceiling and left the split curve on contaminated 08-22 data, producing an apparent -3.18%
  deficit and a rewritten "three-way trade". Re-measured verified-quiet with replicates,
  **the three configurations that keep the memory overclock cannot be told apart, and this
  measurement is not capable of telling them apart.** Band-mean throughput, GB/s:

  | configuration | sweeps | per sweep | mean | within-config spread |
  |---|---|---|---|---|
  | memory-only (ceiling) | 1 | 368.8 | 368.8 | - |
  | repaired curve | 2 | 367.5 / 371.1 | 369.3 | 0.98% |
  | split curve | 3 | 368.5 / 366.2 / 367.0 | 367.2 | 0.61% |

  ⛔ **BETWEEN configurations: 0.56%. WITHIN one configuration: up to 0.98%. Across all six
  sweeps: 1.32%.** The curves are closer together than one curve is to itself. **No ranking among
  memory-only, repair and split on `membw` is supported** - do not write one, and treat any
  ordering of them as noise until n is much larger.

  ⚠️ **EVERY POINT ESTIMATE THIS ENTRY HAS EVER CARRIED WAS FROM TOO FEW SWEEPS.** Individually the
  split sweeps give **-0.11%, -0.73%, -0.57%** against the memory-only reference and the repair
  sweeps give **-0.39%, +0.58%**. Successive versions of this entry quoted -0.11%, then -0.42%,
  then -0.47%, then "agrees to 0.03 points", then 0.08. **The number kept moving because n kept
  being 1 or 2, not because the card changed.**

  🔑 **THE REPAIR EXCEEDS THE "CEILING" IN ONE OF ITS TWO SWEEPS (+0.58%).** The memory-only card
  is still the right reference in principle, and on 2026-08-23 "nothing beats a ceiling" correctly
  caught a contaminated reference. But at this precision it is not a hard limit - it is n=1 and
  carries the same fragility as everything measured against it.

  ✅ **WHAT SURVIVES AT THIS n:** against the FULLY TUNED profile the plateau is removed outright,
  **+18.7% mean across the band**, which is thirty times the noise. And the repair is dominated -
  but that rests entirely on `gemm`, where eight sweeps give non-overlapping ranges. On `membw`
  the honest statement is "gives up nothing measurable", not "matches the repair".

  **Of the three reasons given for calling the 08-22 run contaminated, only one survives.**
  MAGNITUDE stands: +2.88% (n=2), or +2.77% excluding the one known dip in each run, against the
  +3.30% the ceiling itself moved and 5.4.4's +4.22% for this band. FREQUENCY SIGNATURE is
  withdrawn as never applicable - with the dips removed it is flat (+2.89% vs +2.58%), and 5.4.4's
  boundary is near 2010 MHz while nine of these ten points sit below it, so a uniform offset is
  what 5.4.4 actually predicts here. The internal split quoted earlier read structure into noise.
  THE ISOLATED-POINT ARGUMENT is withdrawn outright: clean runs make those holes too.

  **A different applied profile is not excluded.** The withdrawal of -3.18% rests on the two new
  measurements, not on the diagnosis of the old one - keep those two things apart.

  🔑 **THE PARAGRAPH HAS NOW BEEN WRONG TWICE AND THE SHAPE IS THE SAME BOTH TIMES.** Version one
  compared contaminated against contaminated and was **right by accident**. Version two cleaned
  ONE side and was wrong on evidence that already existed - the provenance audit had flagged it
  that morning and recorded that -3.18% was an upper bound, not a measurement. **Correcting one
  half of a pair is not a partial fix; it converts a symmetric error into an asymmetric one while
  looking like diligence.** Before "correcting" any comparison, check the provenance of BOTH sides.

  **The current statement: the repaired curve is dominated.** The split curve matches its
  bandwidth and keeps the compute advantage the repair gives away, so there is no operating point
  where the repair is the right choice. The live trade is tuned versus split, unchanged: tuned
  still wins `gemm` efficiency 1545-2625 MHz by up to 30.5%. Against the fully tuned profile the
  split curve removes the plateau outright, +19.2% mean across the band (+2.4% to +31.7%).

  **Every `membw` figure here is n=1 per configuration.** A second split-curve sweep is the
  cheapest thing that would strengthen any of it.

  🔑 **THE SAME SESSION INDEPENDENTLY REPLICATED 5.4.4's CONTAMINATION MAGNITUDE.** The clean
  memory-only `gemm` sweep against its contaminated 08-20 counterpart, 13 shared targets, gives
  **+1.73% above 2010 MHz against the +1.71% 5.4.4 measured** - agreement to 0.02 points, on a
  DIFFERENT configuration, three days apart, by a different route. Mid-band gives +3.05% against
  5.4.4's +4.22%: same sign and order, lower. This turns the capture-software finding from a
  single-session result into a replicated one, which is worth more than the correction that
  prompted the run.

  ✅ **RESOLVED 2026-08-29, and the claim STANDS.** Measured same-session, stock against
  memory-only on the 1237-3090 grid, `gemm` differs by **-0.05%** - comfortably inside the plus or
  minus 1%. A first attempt the same morning compared today's stock against 2026-08-22's
  memory-only and got -1.50%, which was written up as the claim failing and retracted hours later:
  the identical configuration measured today against 2026-08-22 differs by **+1.47%**, so that was
  cross-session drift and not an effect. 🔑 **THAT DRIFT FIGURE IS THE THING TO REMEMBER - ~1.47%
  on `gemm` across sessions on one unchanged configuration, against the ~0.76% this project cites
  for within-session spread.** Any comparison here drawn from different days carries an offset of
  that order. See `data/frequency-sweeps/memonly-gemm-20260829/README.md`.

  The original statement of the problem, kept because the reasoning was right: "`gemm` gets nothing
  measurable from the memory overclock, plus or minus 1%" could not be checked clean. The clean memory-only `gemm` run is on the 1237-3090 grid and the
  clean stock `gemm` run is on the 465-3090 floor15 grid, which share only their top point. One
  clean stock `gemm` sweep on the 1237-3090 grid would close it.
- ✅ **"Neither configuration dominates" was tested and SURVIVES.** This entry previously said it
  "may now be false"; the measurement says otherwise. The split curve beats tuned on `membw` at
  every point (+3.2% to +30.0%) and on `gemm` peak throughput (+2.0%), but **tuned still wins
  `gemm` efficiency from 1545 through 2625 MHz, by up to 30.5% at 2010 MHz** — which is where
  `gemm`'s efficiency optimum sits. The trade is unchanged in character. Do not rewrite §5.7.5.
- 🟡 **The split curve passed its first stability run, 2026-08-23. The other two configurations
  have never been tested.** Thirty minutes under protocol v1.0.0
  (`tools/stability-logger/Invoke-StabilityProtocol.ps1`): 33 iterations, zero aborted, zero
  driver resets, zero thermal or hardware-slowdown samples, 96.9% loaded, post-soak drift `gemm`
  **-0.11%** and `membw` **+0.16%**. Peak 196.1 W of a 200 W limit, peak 79 C.

  **Not "zero throttled samples" without qualification** - 15 of 1765 hit the software power cap,
  which the logger classes as normal rather than as throttling. The paper said the unqualified
  version until 2026-08-24.

  **The original tune passed the same test forty minutes later**, drift `gemm` +0.10% / `membw`
  -0.28%. 🔑 **Two things fall out of having both.** First, the `gemm` gap reproduces: +1.41%
  under sustained unlocked load against +1.53% from locked sweep peaks - different protocols,
  agreeing to 0.12 points. Second, **the split curve's `membw` advantage vanishes at free boost**
  (-0.44%), because the plateau is a property of 1402-1867 MHz and a boosting card sits at
  2968-2993 MHz, above it. Do not quote §5.7.2's -29.6% as a cost paid in normal use; it is a
  locked-frequency result.

  Say **"no failure observed in thirty minutes"**, never "stable". The repaired curve remains
  untested, the 2% degradation threshold was set before anyone knew what healthy drift looks like,
  and all four drift figures land between -0.28% and +0.16% - so these runs do NOT distinguish the
  two configurations on steadiness, and the 4.5x reproducibility advantage (a between-sweep
  spread, not within-run drift) is neither confirmed nor overturned by them.
  What was once called a "~2.5% outlier in 1 of 3 runs" is better described by the mid-band
  reproducibility entry above.

  ⚠️ **THE +1.41% AND -0.44% ABOVE WERE +1.45% AND -0.35% UNTIL 2026-08-24, AND BOTH WERE WRONG
  FOR THE SAME REASON.** The paragraph declared "post-soak means over eleven unlocked iterations
  each" and then drew its three numbers from three different windows: the split curve's `gemm`
  mean over all sixteen iterations, its `membw` mean over the five SOAK iterations alone, and the
  original tune's over its eleven post-soak ones. Every figure was a real measurement of
  something. The pairing was not, and it read as three tidy numbers.

  No conclusion changed - the gap still corroborates, the `membw` difference is still noise in the
  wrong direction - but the defect was structural, not arithmetic. `iterationsIn()` in
  `analysis/audit_claims.py` now REQUIRES the window at the call site, and §5.7.6 went from 4
  pinned numbers to 23. **The lesson is the one this project keeps relearning: an aggregate whose
  window is implicit is a claim nobody can check.**
- **Which sections are unaudited, and which of them matter.** *The count itself lives in the
  canonical coverage block above and is not repeated here - that duplication is what produced two
  contradictory totals in one file on 2026-08-30.* Most are prose - 2.1-2.5, 3.1-3.4 - with little
  to pin. The ones carrying real numbers are **3.3.2, 3.3.3, 5.4.2, 5.5.5, 5.6.3, 5.7 and 5.7.7**.

  **5.5.4 and 5.7.3 have left this list** - 5.5.4 gained four claims when the cross-architecture
  result entered the paper, and 5.7.3 is now 23 of 70 pinned. **5.5.5 and 5.6.3 have joined it**,
  and both joined by being WRITTEN, not by being neglected: a new section starts unaudited, so this
  count going up is not automatically a regression.

  ✅ **The blocker this bullet used to name is gone.** It said `analyze_fine_sweep.py` "needs its
  summary exposed" before §5.4.1's vertices and confidence intervals could be pinned.
  `analyseWorkload()` is importable, returns the summary dict, and takes an `rng` whose seed already
  defaults to 20260816 - so the intervals are deterministic and pinnable today. Nothing is stopping
  §5.4.1, which the canonical block above records as the least-covered section in the paper.
- ✅ **The failure detector HAS now seen a real failure, 2026-08-30.** This bullet called it "the
  highest-value single hour available" for weeks; it was spent, and it paid. An undervolt
  deliberately set past the edge - **875 mV pinned at 3000 MHz** - crashed the display driver, and
  `Get-DisplayDriverCrashEvents` returned 11 events over the run window. Full record in
  `data/stability-runs/README-uv-875mv-3ghz-20260830.md`. Three things fell out that no synthetic
  test would have produced:
  - **The failure signature is a power collapse under sustained reported utilisation** - 92.21 W to
    24.05 W in one second while the card still reported 2970 MHz and 100% util. That is §5.4.3's
    decoupling of `utilization.gpu` from real throughput, appearing inside a crash instead of a
    measurement.
  - **The driver reset silently cleared the Afterburner offsets.** Memory came back at 13801, stock.
    Any run continued past that point would have measured stock silicon under a settings string
    still claiming an undervolt.
  - **It crashed fourteen seconds BEFORE the benchmark process launched.** Ordinary desktop
    compositing was enough to boost the card to ~2970 MHz at 875 mV and kill the driver. A protocol
    that only inspects its own load window would have missed the event outright.

  ⚠️ **The UNSTABLE verdict was reconstructed, not emitted.** The operator stopped the run on seeing
  the crash, so no `_session.json` and no `_stability_protocol.json` were written. The detector
  function was re-run unmodified over the same event-log window, which is sound - but it is not the
  same as the tool having produced the verdict itself, and the difference is worth keeping. What
  makes the record exist at all is `AutoFlush = $true` in the logger: `_samples.csv` covers the
  whole event.

  **n = 1, and the crash was spontaneous rather than provoked at a known load.** It establishes that
  875 mV at 3000 MHz is unstable on this card and nothing about where the edge sits. **Quote no
  threshold from it.** One of the eleven events, at 12:37:21, post-dates the kill and is not
  attributable to the card.

  ⚠️ **§3.5 of the paper has NOT been updated for this and still carries a DRAFT marker.** It
  describes the reset detector as having fired only on an induced context-reset from force-killing a
  CUDA process. Its sentence "an actual hard lock remains untested" needs care rather than deletion:
  the card recovered on its own here, so what is now tested is genuine instability, not a hard lock.
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
- ✅ **The Inspirit "deliverable format" question is retired, 2026-08-23.** It was carried as an
  open risk for weeks and the premise was wrong. There is no presentation and no required format:
  the program's role is to **support Raymond in publishing this research**. Stop asking, and treat
  publication - not a submission - as the target the work is aimed at.

  **That raises the bar on two things rather than lowering it.** Provenance has to survive a
  reviewer, which is what makes the clean/contaminated split below the project's main technical
  problem. And n=1 chip is the weakness any reader will name first, which is what makes stock
  sweeps on other machines valuable even when nothing can be tuned on them.
- **Push directly with `git push`** - Windows Credential Manager handles it and there is no reason
  to change that. This line used to end "do not route through `gh`" because auth had never
  completed; **`gh` was authenticated 2026-09-02** (account `imaoofu`, keyring, scopes `gist`,
  `read:org`, `repo`, `workflow`), so the instruction is now about pushes ONLY.

  ✅ **Use `gh` to read CI, because nothing else can.** The repo is PRIVATE, so an unauthenticated
  `api.github.com` request returns `Not Found` rather than a useful error, and a session without
  `gh` is reduced to guessing at build results:

  ```
  gh run list --limit 10
  gh run view <run-id>                 # per-job breakdown
  gh run view <run-id> --log-failed    # just the failing step
  ```

  ⚠️ **A `cancelled` run is usually not a failure.** `ci.yml` sets `cancel-in-progress: true`, so a
  push that supersedes one still running cancels the older one. Three of the last forty runs are
  cancelled for that reason and none of them indicate a problem.

  🔑 **CI does NOT see `data/raw/`, and that changes the claim count.** The dataset is gitignored
  and fetched, so `claims_reference.py` registers its 24 claims only in the "V100 reference
  claims" job. Both legs are green, and **their two totals are in the canonical coverage block
  above rather than here.** The gap between them is 25 rather than 24 because `header-pinned-count`
  is guarded on the same condition and so registers only alongside the reference set - and
  `claims_repo.py` splits the same way, registering the with-reference total in one leg and the
  without-reference total in the other, because `len(CLAIMS)` can only honestly report the
  environment it is running in. Any claim whose value depends on the SIZE of the registry is therefore
  environment-dependent; `header-pinned-count` is guarded for exactly that reason, after an
  unguarded version broke both checks legs on 2026-09-02. A local run can be made to match CI by
  temporarily moving `data/raw` aside, which is how that break was reproduced before it was fixed.
