TASK: write three missing README.md files, one for each of three data directories

Write Markdown only. These are three NEW files. Do not modify any existing file.

## Why this task exists

CLAUDE.md states a rule: **"Every data directory carries its own README explaining what is
dataset-grade and what is not."** Seven data directories exist; four comply and three do not.
The three below are the gap. Every other data directory in this repository already follows the
convention, so match their tone: direct, factual, and leading with whatever a reader is most
likely to get wrong.

The single most important thing each of these READMEs must do is say plainly **whether the
contents are dataset-grade** — that is, whether they are original measurements this project
stands behind — because for all three the answer is NO, for three different reasons.

## Output format

Return all three files in one reply, each preceded by a marker line on its own, exactly:

    === FILE: data/raw/README.md ===
    === FILE: data/external/README.md ===
    === FILE: data/HWiNFO-Data/README.md ===

After each marker put that file's complete Markdown content. Do NOT wrap the content in code
fences. Do not write any commentary before the first marker or after the last file.

Each file should open with an HTML comment on its own line recording dataset-grade status,
matching the convention already used elsewhere in this repository:

    <!-- dataset-grade: no -->

Aim for roughly 40-70 lines per file. Use a `#` title, then short sections with `##` headings.
Prefer a table where the content is a list of files with descriptions.

## FACTS — use only these. Do not invent, extrapolate, or add plausible-sounding detail.

If a fact you want is not listed here, leave it out. An invented file size, licence, row count or
URL is worse than an omission, because a reader cannot tell the two apart.

### 1. data/raw/ — the public V100 dataset

- Three files: `dataset_efficiency.csv`, `dataset_performance.csv`, `dataset_power.csv`.
  About 16 KB total.
- **Gitignored** via `data/raw/*.csv`, so it is NOT committed and NOT redistributed by this
  repository. The reason is that **the licence has not been checked.** Say this plainly.
- Fetch it with `scripts/Get-Dataset.ps1`.
- Shape: **33 workloads x 13 core frequencies, one Tesla V100.** Core clock only.
- ⚠️ It has **no workload feature columns and no voltage column.** Because of that, "predict the
  optimum from workload characteristics" is *structurally impossible* on this dataset — not
  merely difficult. This is the single most important thing to say about it.
- It is the basis of the project's reference results: mean **44.4%** efficiency given up by
  running at stock (1530 MHz) instead of each workload's own optimum; median 45.7%; range
  15.1-62.8%; costs 13.7% performance and saves 40.1% power.
- **THE NULL that this dataset produced:** a probe-based Ridge model scores **0.883%** mean
  regret against a best-fixed-frequency baseline's **0.837%**. The model LOSES. Leave-one-
  workload-out, 33 folds. 952 MHz is optimal for **24 of 33 workloads (73%)**, so a single
  constant recovers 43.56 of the 44.4 available points.
- ⚠️ CI does not see this directory. `analysis/claims_reference.py` registers its claims only in
  the job that fetches the dataset, which is why the repository has two different green claim
  totals depending on whether `data/raw/` is present.

### 2. data/external/ — downloaded third-party data

- Eight files, about 6.6 MB total. **Gitignored** via `data/external/*.csv` and
  `data/external/*.json`. Fetch with `scripts/Get-Dataset.ps1`.
- Files and what they are:
  - `gtx1080ti-dvfs-real-Performance-Power.csv` and `gtx1080ti.csv` — GTX 1080 Ti, **600 rows,
    30 applications**, a **2D sweep**: core 1600-2000 MHz crossed with memory 4000-5500 MHz.
    The memory axis is one the V100 set lacks entirely.
  - `gtx2070s-dvfs-real-Performance-Power.csv` and `gtx2070s.csv` — RTX 2070 Super, 400 rows.
  - `all-gpus.json` and `gpuspecs.json` — **2,824 GPUs** with numeric specs (sms, tdp,
    memoryBandwidth, memoryBus, processSize, clocks). **Apache-2.0.** Contains the RTX 5060 Ti.
  - `benchmarks.csv` and `mining.csv` — roughly 500 consumer cards, 422 with wattage, from
    mining hashrate-per-watt. An external sanity check on perf-per-watt *ordering* only.
    **NOT training data.**
- ⚠️ **The two published consumer DVFS datasets sweep the WRONG RANGE**, and this is the most
  important fact about this directory. Expressed as a percentage of each card's rated boost
  clock: the GTX 1080 Ti set covers **101-126%** and the RTX 2070 Super **95-118%**, against the
  V100's **55-111%**. Both consumer sets **start at or above stock and go up** — they are
  overclocking sweeps. They structurally cannot locate an efficiency optimum, because the
  optimum lives *below* stock; the V100's sat at 62% of its maximum.
- 🛑 Their small measured gaps (1.00% and 3.34% mean, against the V100's 44.40%) are therefore
  **NOT evidence that consumer GPUs lack headroom.** They are evidence that nobody swept the
  range where headroom lives. Never cite the 1.0% figure as a null result. Reproduce this with
  `python analysis/compare_consumer.py`.
- ⚠️ Spec sheets in this data describe **reference** cards. The table lists the 5060 Ti 16GB at
  boost 2572 MHz / TDP 180 W; the card measured in this project reports a 3090 MHz maximum lock
  target and a 200 W limit against a 180 W default. Never treat a spec-sheet clock as a measured
  clock.
- ⚠️ The upstream HKBU-HPML repositories use the **`master`** branch, not `main`. Raw URLs 404
  silently otherwise.

### 3. data/HWiNFO-Data/ — raw sensor dumps

- Seven CSV files, about 9.6 MB. **The whole directory is gitignored** (`data/HWiNFO-Data/`),
  not just a file pattern.
- These are raw HWiNFO logs carrying **300+ columns** covering every CPU, motherboard, drive and
  fan sensor on the machine. Almost none of it is relevant.
- 🔑 **The distilled extracts are what the project actually uses, and they live beside their
  sweep**, committed, as `*_sweep_voltage.csv`. This directory is the unprocessed input to that
  step, kept only so an extract can be regenerated or audited. **A reader wanting the voltage
  data should use the extracts, not these files.**
- Produced by `tools/frequency-sweep/join_hwinfo_voltage.py`.
- 🔑 **The join bins samples by CORE CLOCK, not by timestamp**, because a sweep CSV records
  durations rather than absolute times.
- ⚠️ **A single log must never span a profile change.** Because the join bins by core clock, two
  configurations measured at the same frequency would be silently merged into one median.
- ⚠️ **A 30 W idle filter is load-bearing, not hygiene.** HWiNFO polls continuously through the
  settle gaps between sweep points, and an idle card sits at *boost* voltage — so keeping idle
  samples manufactures a voltage-frequency slope out of nothing.
- Polling is at 2 s. Voltage resolution is 5 mV.
- Files present: `hwinfo-20260908-p4-fullcurve-gemm.csv`,
  `hwinfo-20260908-p5-splitcurve-gemm.csv`, `hwinfo-silent-membw-matched2130.csv`,
  `hwinfo-volt-OC-20260820-2108.csv`, `hwinfo-volt-OCv2.CSV`, `hwinfo-volt-ocsweep.CSV`,
  `hwinfo-voltnonoc.CSV`. Note that three of them carry an uppercase `.CSV` extension — this is
  how HWiNFO wrote them and the inconsistency is real, so do not silently normalise it.
- ⚠️ HWiNFO logging is started by hand from its GUI. It **cannot be started remotely**, which is
  why several runs in this project have no voltage telemetry at all.

## Tone

Follow the repository's house style, which is unusually blunt about its own limitations:

- State what is NOT trustworthy before what is.
- Where a number could be misread, say how it will be misread and why that reading is wrong.
- Never claim something is verified unless the facts above say it was.
- Complete sentences. No marketing language. Warning emoji (⚠️, 🛑, 🔑) are used in this
  repository to mark the sentences a reader must not skip — use them for exactly that, sparingly.

## Output

Three files, each after its `=== FILE: ... ===` marker, no code fences, no commentary.
