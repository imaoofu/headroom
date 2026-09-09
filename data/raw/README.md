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
