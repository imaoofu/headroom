=== FILE: data/raw/README.md ===
<!-- dataset-grade: no -->

# data/raw/

This directory holds the public Tesla V100 dataset. It is **not dataset-grade**: the licence
has not been checked, so the files are gitignored (`data/raw/*.csv`) and are not committed or
redistributed by this repository. Fetch them with `scripts/Get-Dataset.ps1`.

## Files

| File | Description |
|------|-------------|
| `dataset_efficiency.csv` | Efficiency measurements |
| `dataset_performance.csv` | Performance measurements |
| `dataset_power.csv` | Power measurements |

About 16 KB total.

## Shape

33 workloads x 13 core frequencies, one Tesla V100. Core clock only.

⚠️ There are no workload feature columns and no voltage column. Because of that, "predict the
optimum from workload characteristics" is structurally impossible on this dataset, not merely
difficult.

## Reference results

This dataset is the basis of the project's reference results. Running at stock (1530 MHz)
instead of each workload's own optimum gives up:

- Mean 44.4% efficiency
- Median 45.7%
- Range 15.1-62.8%
- Costs 13.7% performance and saves 40.1% power

## The null this dataset produced

A probe-based Ridge model scores 0.883% mean regret against a best-fixed-frequency baseline's
0.837%. The model loses. Leave-one-workload-out, 33 folds. 952 MHz is optimal for 24 of 33
workloads (73%), so a single constant recovers 43.56 of the 44.4 available points.

## CI

⚠️ CI does not see this directory. `analysis/claims_reference.py` registers its claims only in
the job that fetches the dataset. This is why the repository has two different green claim
totals depending on whether `data/raw/` is present.
=== FILE: data/external/README.md ===
<!-- dataset-grade: no -->

# data/external/

This directory holds downloaded third-party data. It is **not dataset-grade**: the files are
external, gitignored (`data/external/*.csv` and `data/external/*.json`), and not redistributed
by this repository. Fetch them with `scripts/Get-Dataset.ps1`. Eight files, about 6.6 MB total.

## Files

| File | Description |
|------|-------------|
| `gtx1080ti-dvfs-real-Performance-Power.csv` | GTX 1080 Ti DVFS sweep |
| `gtx1080ti.csv` | GTX 1080 Ti DVFS sweep |
| `gtx2070s-dvfs-real-Performance-Power.csv` | RTX 2070 Super DVFS sweep |
| `gtx2070s.csv` | RTX 2070 Super DVFS sweep |
| `all-gpus.json` | 2,824 GPUs with numeric specs |
| `gpuspecs.json` | 2,824 GPUs with numeric specs |
| `benchmarks.csv` | Consumer cards, mining hashrate-per-watt |
| `mining.csv` | Consumer cards, mining hashrate-per-watt |

## DVFS sweeps

The GTX 1080 Ti set is 600 rows, 30 applications, a 2D sweep: core 1600-2000 MHz crossed with
memory 4000-5500 MHz. The memory axis is one the V100 set lacks entirely. The RTX 2070 Super
set is 400 rows.

⚠️ The two published consumer DVFS datasets sweep the wrong range. As a percentage of each
card's rated boost clock, the GTX 1080 Ti set covers 101-126% and the RTX 2070 Super 95-118%,
against the V100's 55-111%. Both consumer sets start at or above stock and go up; they are
overclocking sweeps. They structurally cannot locate an efficiency optimum, because the optimum
lives below stock; the V100's sat at 62% of its maximum.

🛑 Their small measured gaps (1.00% and 3.34% mean, against the V100's 44.40%) are not evidence
that consumer GPUs lack headroom. They are evidence that nobody swept the range where headroom
lives. Never cite the 1.0% figure as a null result. Reproduce this with
`python analysis/compare_consumer.py`.

## GPU specs

`all-gpus.json` and `gpuspecs.json` cover 2,824 GPUs with numeric specs (sms, tdp,
memoryBandwidth, memoryBus, processSize, clocks). Apache-2.0. Contains the RTX 5060 Ti.

⚠️ The spec sheets describe reference cards. The table lists the 5060 Ti 16GB at boost 2572 MHz
/ TDP 180 W; the card measured in this project reports a 3090 MHz maximum lock target and a 200
W limit against a 180 W default. Never treat a spec-sheet clock as a measured clock.

## Mining data

`benchmarks.csv` and `mining.csv` cover roughly 500 consumer cards, 422 with wattage, from
mining hashrate-per-watt. This is an external sanity check on perf-per-watt ordering only.
Not training data.

## Upstream

⚠️ The upstream HKBU-HPML repositories use the `master` branch, not `main`. Raw URLs 404
silently otherwise.
=== FILE: data/HWiNFO-Data/README.md ===
<!-- dataset-grade: no -->

# data/HWiNFO-Data/

This directory holds raw HWiNFO sensor dumps. It is **not dataset-grade**: the files are
unprocessed input, and the whole directory is gitignored (`data/HWiNFO-Data/`), not just a file
pattern. Seven CSV files, about 9.6 MB.

🔑 The distilled extracts are what the project actually uses, and they live beside their sweep,
committed, as `*_sweep_voltage.csv`. This directory is the unprocessed input to that step, kept
only so an extract can be regenerated or audited. A reader wanting the voltage data should use
the extracts, not these files.

## Files

| File | Description |
|------|-------------|
| `hwinfo-20260908-p4-fullcurve-gemm.csv` | Raw HWiNFO log |
| `hwinfo-20260908-p5-splitcurve-gemm.csv` | Raw HWiNFO log |
| `hwinfo-silent-membw-matched2130.csv` | Raw HWiNFO log |
| `hwinfo-volt-OC-20260820-2108.csv` | Raw HWiNFO log |
| `hwinfo-volt-OCv2.CSV` | Raw HWiNFO log |
| `hwinfo-volt-ocsweep.CSV` | Raw HWiNFO log |
| `hwinfo-voltnonoc.CSV` | Raw HWiNFO log |

Three of these carry an uppercase `.CSV` extension. This is how HWiNFO wrote them and the
inconsistency is real, so it is not silently normalised.

## What the logs contain

These are raw HWiNFO logs carrying 300+ columns, covering every CPU, motherboard, drive and fan
sensor on the machine. Almost none of it is relevant.

Produced by `tools/frequency-sweep/join_hwinfo_voltage.py`. Polling is at 2 s. Voltage
resolution is 5 mV.

## Join behaviour

🔑 The join bins samples by core clock, not by timestamp, because a sweep CSV records durations
rather than absolute times.

⚠️ A single log must never span a profile change. Because the join bins by core clock, two
configurations measured at the same frequency would be silently merged into one median.

⚠️ A 30 W idle filter is load-bearing, not hygiene. HWiNFO polls continuously through the settle
gaps between sweep points, and an idle card sits at boost voltage, so keeping idle samples
manufactures a voltage-frequency slope out of nothing.

## Logging

⚠️ HWiNFO logging is started by hand from its GUI. It cannot be started remotely, which is why
several runs in this project have no voltage telemetry at all.