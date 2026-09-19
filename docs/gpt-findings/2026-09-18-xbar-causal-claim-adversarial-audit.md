# Adversarial audit: flattened V/F curve, XBAR clock, and the 300 GB/s plateau

**Date:** 2026-09-18  
**Task:** Make the strongest evidence-based case that the proposed causal chain is wrong or
overinterpreted. Identify alternatives, the best discriminating measurement, and the limits imposed
by one chip and one curve edit.  
**Scope:** Repository data and code were inspected after reading the project instructions. This was
an internal evidence audit, not an independent hardware reproduction.

## Verdict

The existing evidence supports a narrower statement than the one under attack:

> On this GB206 board, driver, monitoring stack, and set of profiles, the flattened low-voltage
> curve was associated with a low reported XBAR clock and an approximately 300 GB/s
> effective-throughput plateau. Restoring the low-voltage curve slope restored both. The runs do not
> isolate XBAR as the causal bottleneck.

The strong chain

```text
flattened curve -> measured voltage held low -> XBAR held low -> global-memory bandwidth capped
```

is not established. It is assembled from three comparisons that do not share all controls:

1. **Curve to plateau:** full tune against memory-only. Memory clock is matched at the +2500
   setting, but the runs are 21.5 hours apart and have no XBAR telemetry in the memory-only run.
2. **Curve to reported XBAR:** full tune against full stock. These runs are eight minutes apart and
   include voltage/XBAR telemetry, but their memory clocks differ by 2500 MHz.
3. **Reported XBAR to throughput:** covariance within the full-tune sweep. XBAR was not intervened
   on, and several hidden domains can co-vary with it.

That design shows a repeatable configuration-level effect on this unit. It does not demonstrate
causal mediation by XBAR.

## The strongest ordinary-saturation objection

The strongest defensible objection is broader than “the GDDR7 channels are saturated at
300 GB/s.” Pure DRAM-channel saturation is a poor fit: this card exceeds 300 GB/s in other runs,
and fixed MCLK does not imply that DRAM is delivering its maximum transaction rate.

The stronger objection is:

> `membw` hits an end-to-end throughput ceiling upstream of the DRAM devices: SM request issue,
> load/store or L1TEX pipelines, L2, an internal SYS/HUB/fabric link, a memory-controller clock, or
> another low-voltage clock domain. Firmware selects that ceiling and the reported XBAR clock from
> the same V/F policy, so XBAR is a correlated indicator rather than the demonstrated mediator.

This objection fits the repository's later evidence. Section 3.3.1 reports that at 1395 MHz four
independent copies increase aggregate throughput from 218.3 to 281.2 GB/s, and unrolling a
hand-written kernel reaches 281.9 GB/s. The two methods agree within 0.24%, but only at roughly 54%
of the tuned theoretical bus rate. The paper therefore states that a DRAM-saturated workload at
1400 MHz was not constructible and that hardware counters are required to identify the ceiling.
The flattened run begins at 280.6 GB/s, almost exactly this unexplained approximately 281 GB/s
ceiling.

NVIDIA's documentation also distinguishes the benchmark's effective or requested bandwidth from
actual global and DRAM throughput. Nsight Compute separately distinguishes full utilization of
memory units (“Mem Busy”), exhaustion of links between them (“Max Bandwidth”), and the maximum rate
of issuing memory instructions (“Mem Pipes Busy”). A timed PyTorch kernel alone does not say which
of these is limiting.

## Findings that directly weaken the stated chain

### 1. The voltage/XBAR control is not memory-clock matched

The committed sweep telemetry is unambiguous:

| Run | Core curve | Maximum logged MCLK | Voltage/XBAR telemetry | Relevant limitation |
|---|---:|---:|---:|---|
| `20260820-210822_5060ti-oc-volt-membw` | flattened | 16,301 MHz | yes | profile label was corrected after collection |
| `20260820-211630_5060ti-stock-volt-membw` | stock | 13,801 MHz | yes | not memory matched to the flattened run |
| `20260820-181307_5060ti-memonly-membw-anomaly` | stock | 16,301 MHz | no | 21.5 hours after the earlier tuned plateau run |

The claim that both voltage/XBAR configurations held 16,301 MHz is false for the committed pair.
The reported 312 to 342 GB/s stock rise also comes from an earlier stock sweep over approximately
1545 to 1852 MHz, not from the voltage-logged stock run over 1402 to 1867 MHz. The latter records
283.8 to 338.8 GB/s. The prompt combines values from different comparisons.

The direction matters: the flattened run has the higher MCLK and lower throughput, so the MCLK
mismatch does not trivially explain away its plateau and may make the stock/flat gap conservative
on that axis. It still prevents the table from being a single controlled test of the complete
mechanism, especially because memory-clock limits can participate in cross-domain clock policy.

“Maximum logged MCLK” is deliberate wording. Several committed sweep rows have a 7001 MHz minimum
and an average below the stated maximum, including rows in the flattened and memory-only runs.
Those can be boundary or idle samples rather than loaded downclocks, but the literal claim that
MCLK was 16,301 MHz in every sample cannot be recovered from the committed aggregates. The raw
logs needed to window it again are not present.

All three session JSON files record a 200 W configured power limit, rather than the board's 180 W
default. Actual power remained far below either value, so this does not rescue a power-cap
explanation; it is another place where the experimental condition in the prompt differs from the
record.

### 2. XBAR and throughput diverge before the reported voltages diverge

The repository says the configurations “separate at 1635 MHz,” the first point where stock voltage
rises. The committed joined files show otherwise:

| Target | Stock V | Flat V | Stock XBAR | Flat XBAR | Stock GB/s | Flat GB/s |
|---:|---:|---:|---:|---:|---:|---:|
| 1402 | 0.720 | 0.720 | 1335 | 1320 | 283.83 | 280.64 |
| 1477 | 0.720 | 0.720 | 1402 | 1320 | 298.45 | 284.16 |
| 1560 | 0.720 | 0.720 | 1470 | 1342 | 309.73 | 292.76 |
| 1635 | 0.740 | 0.720 | 1545 | 1342 | 320.96 | 298.97 |

At 1477 MHz the throughput gap is already 4.8%; at 1560 MHz it is 5.5%. Both XBAR and throughput
separate while HWiNFO still reports the same 0.720 V for both configurations. That falsifies the
literal claim that divergence begins with the observed voltage divergence.

Possible interpretations remain open: HWiNFO voltage may be a coarse request rather than rail
voltage; the V/F table or profile identity may affect clock policy independently of the displayed
voltage; or another hidden state may differ. None restores the asserted measured chain without an
additional measurement.

### 3. The ratio collapse adds no independent causal evidence

If core clock rises while XBAR changes little, XBAR/core must fall. The ratio spread is a compact
description of the raw clocks, but it is not another measurement. It cannot distinguish a causal
XBAR bottleneck from a shared firmware policy that holds XBAR and some unobserved limiting domain
low together.

The “49%” wording also merges ranges. From 1400.6 to 1859.7 MHz, where XBAR stays around 1320 to
1350 MHz, core rises 32.8%. Across the full 49.4% core-clock rise to 2092 MHz, XBAR rises to
1545 MHz, throughput rises to 345.0 GB/s, and reported voltage ends at 0.740 V. The mid-band
plateau is real, but XBAR is not fixed over the entire 49% range.

### 4. Profile provenance is partly circular

The flattened telemetry run was launched with the wrong label. Its session JSON says the profile
was identified from the plateau signature in the collected throughput data. The plateau was thus
used to classify the run, after which the classified profile was used to explain the plateau.
There is no independently recorded `applied_settings` field in this schema version.

The classification is plausible and supported by other fields, but it is not independent profile
readback. A wrong or partially applied Afterburner state cannot be excluded as cleanly as the
narrative implies.

### 5. The benchmark does not measure physical DRAM bytes

`gpu_workload.py` times

```python
torch.add(source, other, alpha=2.0, out=destination)
```

over 256 million FP32 elements and calculates 12 bytes per element from two reads plus one write.
That is effective/requested bandwidth. No counter confirms DRAM read/write bytes, L2 sectors,
cache hit rate, compression, write behavior, or transaction efficiency. The declared
0.167 FLOP/byte intensity is useful for describing the source operation but does not identify the
hardware bottleneck.

The approximately 3 GB working set makes full-array L2 residency implausible. It does not remove
L1/L2 sector behavior, compression, coalescing, TLB effects, store policy, or a cache/fabric link
from consideration.

The workload also records successful completion rather than validating the destination values.
Silent numerical errors, replay, or retry behavior under undervolting are not demonstrated, but
they were not tested.

## Alternative explanations, ordered by present plausibility

### Serious and unresolved

- **A shared low-voltage policy controls several domains.** XBAR, SYS/HUB/fabric, L2, memory
  controller, and request-generation clocks may move together. Observing one does not identify the
  limiting one.
- **Kernel request-generation or pipeline saturation.** The later concurrency/unroll tests already
  show an unexplained approximately 281 GB/s ceiling at low core clock. The flattened curve may
  extend that ceiling by holding an upstream domain low.
- **Curve metadata or P-state policy, rather than physical voltage.** The pre-voltage-divergence
  separation is direct evidence that the displayed voltage is not a sufficient state variable.
- **Configuration and run-composition confounding.** No one run pair is simultaneously matched for
  MCLK, instrumented for XBAR, independently profile-verified, and temporally replicated.

### Plausible measurement and software effects

- **Telemetry semantics.** HWiNFO does not publicly document whether these NVIDIA fields are
  physical measurements, firmware targets, or API-reported state. Six to eight samples per point
  were reduced to medians after a power filter.
- **Join and polling effects.** HWiNFO polled every two seconds during these runs. The join bins by
  achieved core clock, selects the moving sensor block, and the raw 300-column HWiNFO logs are not
  committed, so the distilled extraction cannot be independently re-run from this repository.
- **Background capture or driver state.** These schema-0.1.0 runs record no video-engine telemetry.
  Later work found a roughly 4.2% mean mid-band Instant Replay penalty, smaller than the largest
  plateau gap but comparable with the early 1477/1560 gaps.
- **Clock gating, residency, or duty cycling.** Average reported frequencies can hide different
  active-cycle residency. Throttle masks do not enumerate every firmware policy or retry mode.

### Poor fits to the observed runs

- **Gross software power capping:** configured limit was 200 W and measured power was about
  50–67 W; software-power-cap and hardware-slowdown flags were absent.
- **Thermal throttling:** temperatures were approximately 41–53 C, and the lower-throughput tuned
  run was cooler.
- **Whole-working-set cache residency:** the workload uses approximately 3 GB, far beyond L2.
- **A global core-lock failure:** achieved clocks held, and the compute-heavy GEMM did not show the
  same throughput failure.

These observations weaken those specific alternatives; sample size alone does not rule them out.

## What the unaffected GEMM result does and does not show

An unaffected high-intensity GEMM is consistent with an internal memory-path limitation, because
GEMM reuses data and spends most time in arithmetic pipelines. It helps rule out a gross
whole-GPU failure, a failed clock lock, or a universal timing penalty.

It does not distinguish XBAR from SM memory-instruction issue, L1TEX, L2, SYS/HUB/fabric, the
memory controller, cache policy, or actual DRAM saturation. Most of those can hurt a streaming
kernel while leaving GEMM almost unchanged.

## The repair is predictive but not mechanistically unique

Restoring the low-voltage slope and observing the plateau disappear is strong evidence that the
profile matters, especially because the direction was stated in advance. It is not a selective
XBAR intervention. The repair simultaneously changes requested voltage, reported XBAR, power,
possibly several hidden clocks, and firmware state. Every alternative based on a shared V/F policy
predicts the same repair.

The repair therefore supports **curve/profile causality on this unit**. It does not by itself prove
**XBAR mediation**.

## The best discriminating measurement

For the narrow question “ordinary DRAM saturation or an upstream limit?”, collect Nsight Compute
`SpeedOfLight` and `MemoryWorkloadAnalysis` at a plateau point under stock and flattened profiles,
with MCLK matched. The decisive passive quantity is **actual DRAM read/write throughput as a
percentage of sustained peak**, read alongside L2 throughput and the tool's Mem Busy, Max
Bandwidth, and Mem Pipes Busy classification.

- If actual DRAM throughput is at its sustained limit in both states, ordinary DRAM saturation is
  viable and the effective-GB/s interpretation needs revision.
- If actual DRAM traffic is well below peak while an L2/link/issue metric is at peak, the ceiling is
  upstream. That would reject pure GDDR saturation but would still not identify XBAR uniquely.

The single experiment that most reduces the **causal** ambiguity is stronger: at one plateau point,
hold core clock, curve/voltage request, MCLK, power limit, and temperature fixed; randomize or use
an ABBA sequence of direct XBAR offsets; verify physical XBAR with `CLK_MEASURE_FREQ`; and measure
the same kernel. A monotonic throughput response to XBAR while the other controls remain fixed is
the missing intervention. No response would refute or materially narrow the current mechanism.

Direct runtime XBAR control and physical clock measurement have been demonstrated publicly on one
GB202 RTX 5090 with Linux driver R610.57.04. That private interface is driver-specific and has not
been verified here on GB206, Windows, or this driver, so portability must not be assumed.

## What n = 1 chip and one curve edit alone rule out

They rule out any defensible population claim. The data cannot establish that the behavior is
typical of RTX 5060 Ti, GB206, Blackwell, or NVIDIA consumer GPUs; estimate prevalence or unit
variance; or separate chip, board, VBIOS, driver, and tool-specific behavior.

One edited curve also provides no dose-response, threshold, or independent repeatability. It does
not separate the effects of voltage level, curve slope, table metadata, or P-state selection. The
ten frequency points are repeated observations on one intervention, not ten independent samples.

On sample size alone, no physical alternative is ruled out. The measurements provide narrower
within-run exclusions such as no gross power cap, no thermal throttle, and no obvious core-lock
failure. Those exclusions come from telemetry and controls, not from n = 1.

At most, if configuration identity and telemetry are accepted, this is a proof-of-existence result:
this one unit exhibited the association under this software and profile state.

## Sources and verification status

### Repository evidence opened

- [`data/frequency-sweeps/membw-anomaly-20260819/README.md`](../../data/frequency-sweeps/membw-anomaly-20260819/README.md)
- [`20260820-210822_5060ti-oc-volt-membw_sweep.csv`](../../data/frequency-sweeps/membw-anomaly-20260819/20260820-210822_5060ti-oc-volt-membw_sweep.csv)
- [`20260820-210822_5060ti-oc-volt-membw_sweep_voltage.csv`](../../data/frequency-sweeps/membw-anomaly-20260819/20260820-210822_5060ti-oc-volt-membw_sweep_voltage.csv)
- [`20260820-210822_5060ti-oc-volt-membw_sweep.json`](../../data/frequency-sweeps/membw-anomaly-20260819/20260820-210822_5060ti-oc-volt-membw_sweep.json)
- [`20260820-211630_5060ti-stock-volt-membw_sweep.csv`](../../data/frequency-sweeps/membw-anomaly-20260819/20260820-211630_5060ti-stock-volt-membw_sweep.csv)
- [`20260820-211630_5060ti-stock-volt-membw_sweep_voltage.csv`](../../data/frequency-sweeps/membw-anomaly-20260819/20260820-211630_5060ti-stock-volt-membw_sweep_voltage.csv)
- [`20260820-181307_5060ti-memonly-membw-anomaly_sweep.csv`](../../data/frequency-sweeps/membw-anomaly-20260819/20260820-181307_5060ti-memonly-membw-anomaly_sweep.csv)
- [`tools/frequency-sweep/gpu_workload.py`](../../tools/frequency-sweep/gpu_workload.py)
- [`tools/frequency-sweep/join_hwinfo_voltage.py`](../../tools/frequency-sweep/join_hwinfo_voltage.py)
- [`docs/PAPER_DRAFT.md`](../PAPER_DRAFT.md), especially sections 3.3.1–3.3.3 and 5.7.2–5.7.4

The repository's required pre-write checks passed on 2026-09-18: 792 checks, 284/284 audited
claims, manifest reconciliation, and citation coverage check.

### External documentation opened

- NVIDIA, [CUDA C++ Best Practices Guide, §9.2](https://docs.nvidia.com/cuda/cuda-c-best-practices-guide/index.html#bandwidth): defines effective bandwidth from requested bytes and distinguishes requested/global/DRAM throughput.
- NVIDIA, [Nsight Compute Profiling Guide](https://docs.nvidia.com/nsight-compute/ProfilingGuide/index.html): documents `SpeedOfLight`, `MemoryWorkloadAnalysis`, L2/DRAM metrics, and the Mem Busy/Max Bandwidth/Mem Pipes Busy distinction.
- LACT issue 1147, [Runtime XBAR clock and per-domain MSVDD control on NVIDIA Blackwell](https://github.com/ilya-zlobintsev/LACT/issues/1147): public identifier and code path for direct XBAR control and `CLK_MEASURE_FREQ`; tested on one RTX 5090, GB202 A1, R610.57.04.
- Loong0x00, [XBAR in NVIDIA Blackwell GPUs: A Physical Clock Domain Ignored by Public Tooling](https://loong0x00.com/notes/blackwell-xbar-physical-clock-domain/): documents the same GB202 control and explicitly limits claims about topology and portability.

The external GB202 work establishes that XBAR can be a physical and independently controllable
clock domain on that tested system. It does not prove that XBAR caused the GB206 plateau reviewed
here.

## Unresolved access and evidence limits

- The raw HWiNFO logs are gitignored, so the sensor-block selection, every original sample, and
  exact timestamps cannot be reprocessed from the repository.
- HWiNFO's implementation and NVIDIA field semantics are not public, so the physical meaning of
  the displayed voltage and XBAR values remains unverified.
- No Nsight Compute counter capture for these exact runs was present.
- No direct XBAR intervention on this GB206/Windows configuration was present.
- The hardware experiment was not independently reproduced for this audit.

---

# ✅ Verification pass — Claude, 2026-09-18

**Three central claims checked against the committed data. All three hold.** This is the most
consequential external finding this project has received.

⚠️ **Scope note first:** this audit states it read the repository and `CLAUDE.md` before writing.
**It is therefore NOT a cold outside-reader check** — unlike the prompt-B search, which recorded
that its boundary closed only afterwards. For an adversarial audit that is the right call (it needs
the data), but the two must not be counted as the same kind of evidence.

## Claim 1 ✅ — the voltage-logged pair is not memory-clock matched

| run | MCLK max | MCLK avg | MCLK min |
|---|---|---|---|
| `…oc-volt-membw` (flattened) | **16301** | 16140 | 7001 |
| `…stock-volt-membw` (stock) | **13801** | 13592 | 7001 |
| `…memonly-membw-anomaly` | 16301 | 16121 | 7001 |

⛔ **`CLAUDE.md` says "membw plateaus at ~300 GB/s while DRAM sits at 16301 MHz throughout."** The
only pair carrying voltage and XBAR telemetry differs by **2500 MHz of memory clock**, and every
run records a 7001 MHz minimum, so "16301 throughout" is not literally true of any of them.

✅ The direction is conservative — the flattened run has the *higher* MCLK and the *lower*
throughput — so this does not explain the plateau away. But it means no single committed run pair
is simultaneously memory-matched, XBAR-instrumented, and profile-verified.

## Claim 2 ✅ — divergence begins BEFORE the voltages diverge. This is the damaging one.

| MHz | V stock | V flat | XBAR st | XBAR fl | GB/s st | GB/s fl | gap |
|---|---|---|---|---|---|---|---|
| 1402 | 0.720 | 0.720 | 1335 | 1320 | 283.83 | 280.64 | −1.12% |
| **1477** | **0.720** | **0.720** | **1402** | **1320** | 298.45 | 284.16 | **−4.79%** |
| **1560** | **0.720** | **0.720** | **1470** | **1342** | 309.73 | 292.76 | **−5.48%** |
| 1635 | 0.740 | 0.720 | 1545 | 1342 | 320.96 | 298.97 | −6.85% |

⛔ **`CLAUDE.md` says: *"The two configurations agree exactly where their voltages agree… and
diverge from the first point where stock raises voltage and tuned does not."* THAT IS FALSE.**
At 1477 and 1560 the reported voltages are identical at 0.720 V, XBAR is already 82–128 MHz apart,
and throughput has diverged 4.8% and 5.5%.

🔑 **The stated chain requires the voltage to be the state variable, and it demonstrably is not.**

✅ **A reconciliation exists and it comes from today's other work**, so it is not special pleading:
the reported voltage is a **coarse VID lookup quantised at 5 mV on this card**, not a rail
measurement — established independently by the fixed-frequency load test (47–71 W moving it 0.0 mV)
and corroborated by HWiNFO's own author. **Two configurations can request the same 0.720 V and
differ in what is actually applied.** ⚠️ That rescues the physics and **not** the evidence: it means
the reported voltage cannot carry the mechanism, and the honest statement is that XBAR and
throughput track **the curve configuration**, not the observed voltage.

## Claim 3 ✅ — the plateau starts at a ceiling the paper already documents

§3.3.1 of this project's own paper: four independent copies at 1395 MHz reach **281.2 GB/s**,
an unrolled kernel reaches **281.9 GB/s** — *"Methods 2 and 3 agree to within 0.24%… from entirely
different mechanisms"* — and §3.3.1's summary names *"a ceiling near **281 GB/s** that neither
concurrency nor per-thread unrolling lifts."*

**The flattened run's plateau begins at 280.64 GB/s.**

⛔ **So the plateau's floor coincides with an unexplained ceiling this project measured separately,
with no curve manipulation involved.** GPT's reading is the better fit: the flattened curve may not
*create* the plateau so much as **prevent the card from escaping a pre-existing ceiling**. That is a
different causal story and the data does not currently distinguish them.

## What survives, and what does not

| | |
|---|---|
| ✅ The plateau is real and reproduces | unchanged |
| ✅ The repair was predicted in advance and worked | unchanged |
| ✅ Configuration-level effect on this unit | unchanged |
| ⛔ "Divergence begins where voltage diverges" | **false — retract** |
| ⛔ "DRAM at 16301 throughout" for the telemetry pair | **false — retract** |
| ⛔ XBAR demonstrated as the *mediator* | **not established** — it may be a correlated indicator of a shared low-voltage policy |
| ⚠️ The ratio collapse as independent evidence | it is arithmetic on the same two clocks, not a second measurement |

**The defensible sentence is the audit's own:** on this board, driver, monitoring stack and profile
set, the flattened low-voltage curve was **associated with** a low reported XBAR clock and a
~300 GB/s plateau, and restoring the low-voltage slope restored both. **The runs do not isolate
XBAR as the causal bottleneck.**

## What would settle it

The audit's discriminating proposal is the right one and it needs hardware this project has:
**intervene on XBAR directly at a fixed core curve and fixed MCLK**, and measure GB/s. Loong0x00's
NVIDIA issue #1266 did exactly that shape of experiment on a 5090 (capping XBAR dropped FurMark
32.4% at higher core clock and unchanged DRAM). ⚠️ Doing it here needs runtime XBAR control, which
LACT #1147 requests and which is not available on this card today.

**Cheaper and available now:** re-run the flattened-vs-stock pair **memory-matched** — both at
stock 13801 or both at +2500 — with voltage and XBAR logged in one session. That removes the single
largest confound and costs about 25 minutes.
