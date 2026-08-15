# Frequency Sweep

Builds a frequency-power-performance curve on real consumer hardware — the equivalent of the
public V100 dataset, measured on a card you actually own.

Two pieces:

| File | Role |
|---|---|
| `Invoke-FrequencySweep.ps1` | Locks the core clock to each of N frequencies and measures power, temperature, and achieved clock. |
| `gpu_workload.py` | Fixed-work GPU benchmark. Supplies the *performance* half of the measurement. |

---

## Why a separate benchmark exists

The sweep needs a performance number at every frequency. A fixed-**time** stress test (OCCT,
FurMark, Afterburner's bundled `gpu_stressor.exe`) cannot give one — it runs for N seconds no
matter how fast the card is. A fixed-**work** benchmark does identical arithmetic every run, so
duration *is* the performance metric and efficiency falls out as `work / (duration × power)`.

Without `-WorkloadCommand`, the sweep still produces a valid power-vs-frequency curve. It just
cannot compute efficiency, and it says so in its own output.

### Two workloads, deliberately

The V100 analysis found the efficiency-optimal frequency depends on whether a workload is
compute-bound or memory-bound — correlation **−0.666** between frequency sensitivity and optimal
clock. Reproducing that contrast on consumer hardware needs both:

- **`gemm`** — large matrix multiply via cuBLAS. Compute-bound, scales nearly linearly with core
  clock. Chosen over a homemade kernel because `GeMM` is one of the 33 workloads in the published
  V100 dataset, making the two directly comparable.
- **`membw`** — large elementwise stream over VRAM. Bandwidth-bound and largely *insensitive* to
  core clock. That insensitivity is the point.

---

## Usage

**Always dry-run first.** It changes no GPU state and prints the planned grid:

```powershell
.\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-first" -DryRun
```

Then, from an **elevated** PowerShell (clock locking requires administrator rights — the script
refuses to start otherwise rather than failing halfway through with the clock pinned):

```powershell
.\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-gemm" -WorkloadCommand "python tools\frequency-sweep\gpu_workload.py --workload gemm --json"
```

Run the benchmark standalone to sanity-check it first:

```powershell
python gpu_workload.py --workload gemm
```

### Key parameters

| Parameter | Default | Notes |
|---|---|---|
| `-FrequencyCount` | 13 | Matches the V100 dataset's grid size. |
| `-MinFrequencyPercent` | 40 | Floor as a % of max clock. See below. |
| `-SettleSeconds` | 8 | Wait after locking before measuring. |
| `-MeasureSeconds` | 20 | Telemetry sampling window per point. |
| `-DryRun` | off | Plan only, touch nothing. |

**On `-MinFrequencyPercent`:** consumer cards report absurdly low clocks as supported — an
RTX 5060 Ti offers 180 MHz against a 3090 MHz max, under 6%. Sweeping evenly from there wastes a
third of the run on frequencies that will never be efficiency-optimal and makes a fixed-work
benchmark crawl. The V100 dataset only swept 49–100% of its max and found its optimum at 62%. The
default of 40% keeps the grid where the answer lives.

---

## Safety

This is the first tool in the repo that **changes GPU state** rather than only observing it, so
the reset path matters more than the measurement.

- The sweep body is wrapped in `try/finally`; the finally **always** issues `nvidia-smi -rgc`,
  then reads the clock back and reports loudly if the reset did not take.
- **Ctrl+C is intercepted** rather than allowed to terminate the process, so stopping early
  unwinds through that same reset path instead of leaving the card pinned.
- **Clock locks do not survive a reboot.** If anything ever looks wrong, restarting returns the
  card to stock. That is the backstop.
- It refuses to run un-elevated, and warns when utilisation is low with no workload supplied —
  an idle sweep measures nothing.

`gpu_workload.py` is ordinary arithmetic, the same work any game or training run does. A compute
workload has no path to permanent hardware damage, and the card enforces its own thermal and power
limits underneath anything software requests. Additional rails regardless:

- Temperature ceiling checked between iterations (`--max-temp`, default 88 °C), aborts cleanly.
- Finite, bounded iteration count. No infinite loops.
- VRAM freed on exit including on error, so repeated sweep points don't accumulate allocations.
- It never touches clocks, voltage, or power limits — only the sweep script does, and only through
  documented `nvidia-smi` calls.

If a run crashes the display driver, that is a **finding about stability at the applied settings**,
not damage. It is also exactly what the stability logger's verdict logic is built to catch.

---

## What the control APIs actually allow

Verified directly against an RTX 5060 Ti on driver 610.88 by dumping `nvml.dll`'s export table and
calling the API through P/Invoke — not assumed from documentation.

| Capability | Status |
|---|---|
| Lock core clock (`nvidia-smi -lgc`) | **Works.** Volta+; Blackwell qualifies. Needs admin. 389 discrete clocks supported, 180–3090 MHz. |
| Set power limit | **Works.** Adjustable 150–200 W on this card (default 180 W). Needs admin. |
| Per-P-state clock offsets (`nvmlDeviceSetClockOffsets`) | **Available.** Reads SUCCESS; graphics ±1000 MHz, memory −2000/+6000 MHz. Writes return `NO_PERMISSION` un-elevated — meaning the API works and wants elevation, not that it is unsupported. |
| Global V/F offset (`nvmlDeviceGetGpcClkVfOffset`) | **NOT_SUPPORTED** on this card. Closed on consumer Blackwell. |
| Read or write **voltage** | **Impossible via NVML.** Zero voltage exports across all 260 device functions. |
| Per-point V/F curve reshaping | Undocumented NVAPI only (`ClockClientClkVfPointsSetControl`). Out of scope — can break on any driver update. |

The voltage limitation is the honest constraint on this whole project: **the sweep measures
frequency versus power, not voltage.** Any write-up must say so plainly rather than describing
this as undervolting research.
