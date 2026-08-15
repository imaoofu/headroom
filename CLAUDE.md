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
- ❌ *"This is undervolting research."* **Voltage cannot be read or written through any documented
  API.** This measures frequency versus power. Say that plainly.

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
| **Read or write voltage** | ❌ **Impossible.** Zero voltage exports across all 260 NVML device functions. |
| `nvidia-smi -svfd` | ❌ Rubin+ only. Not Blackwell. |
| Per-point V/F curve reshaping | ⚠️ Undocumented NVAPI only (`ClockClientClkVfPointsSetControl`, `0x0733E009`). Out of scope — breaks on driver updates. |

**Bonus, decoded but unused:** Afterburner stores the curve at
`Profiles\VEN_10DE&DEV_2D04&…cfg` as hex — 3224 bytes, header, then 127 points × 3 float32.
His Profile 4 shows `+478` mid-band and `−2500` at top. `MSIAfterburner.exe -profile4 -q` applies
and exits. Scriptable curve control **as a stretch goal only.**

---

## Ruled out — do not revisit without new information

- **CPU and RAM extension.** Mostly BIOS/UEFI-level, so it needs a reboot per data point, which
  destroys the automated-sweep economics. Many Intel parts had undervolting locked in microcode
  post-Plundervolt. And unstable CPU/RAM causes **silent data corruption and filesystem damage** —
  categorically worse than a GPU driver crash. Scoped out, not deferred.
- **Simultaneous OC+UV recommendations.** Needs Tier-3 curve control *and* voltage readback. The
  latter does not exist. Ship "recommended frequency cap + power limit" instead.
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

## Repo layout

```
analysis/          Python modelling on the public V100 dataset
tools/
  stability-logger/   observes only — telemetry + crash verdict
  frequency-sweep/    CHANGES GPU STATE — locks clocks, must always reset
    gpu_workload.py   fixed-work benchmark (gemm = compute, membw = bandwidth)
scripts/           dataset download
data/
  raw/                public CSVs (gitignored, not redistributed — license unchecked)
  stability-runs/     logger output — becomes the original dataset
  frequency-sweeps/   sweep output — becomes the original dataset
```

`ROADMAP.md` holds the ordered plan. `README.md` holds results and related work.

---

## Open right now

- **Zero real data collected.** The logger has only run at idle; the sweep has only dry-run. First
  real sweep is the immediate next step, at stock, on a quiet GPU.
- **The failure detector has never seen a failure.** Deliberately crashing something and confirming
  the logger catches it is the highest-value single hour available.
- **Inspirit deliverable format unknown** — asked repeatedly, still unanswered.
- **Push directly with `git push`.** `gh` is installed but auth never completed; Windows Credential
  Manager already works. Do not route through `gh`.
