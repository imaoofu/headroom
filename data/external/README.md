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
