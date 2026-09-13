The 26 root-level CSVs in this directory are frequency sweep runs that predate the convention of placing each investigation in its own subdirectory. They remain in the directory root alongside the 32 subdirectories because they were generated before that structural rule was adopted. Each file is a standalone sweep output; none of them is described in the existing README sections.

### Fine-grained baseline sweeps

These runs are the earliest sweeps in the set, named `fine-p1` and `fine-p2` with no rerun or tuning suffix. They measure the `membw` and `gemm` workloads on a 13-point grid.

| stem | points | workload | schema |
|---|---|---|---|
| `20260816-125959_5060ti-membw-fine-p1` | 13 | `membw` | 0.1.0 |
| `20260816-130549_5060ti-membw-fine-p2` | 13 | `membw` | 0.1.0 |
| `20260816-131140_5060ti-gemm-fine-p2` | 13 | `gemm` | 0.1.0 |

### Split-curve sweeps

These runs carry the `splitcurve` name and cover the `gemm` and `membw` workloads. They include round markers (`r1` through `r5`), a `quiet` variant, and explicit `instantreplay` on/off pairs.

| stem | points | workload | schema |
|---|---|---|---|
| `20260822-160740_5060ti-splitcurve-gemm-r1` | 13 | `gemm` | 0.2.0 |
| `20260822-161322_5060ti-splitcurve-gemm-r2` | 13 | `gemm` | 0.2.0 |
| `20260822-161921_5060ti-splitcurve-membw-r2` | 10 | `membw` | 0.2.0 |
| `20260822-163705_5060ti-splitcurve-gemm-r3-quiet` | 13 | `gemm` | 0.2.0 |
| `20260822-165213_5060ti-splitcurve-gemm-r4-instantreplay-on` | 13 | `gemm` | 0.2.0 |
| `20260822-165944_5060ti-splitcurve-gemm-r5-instantreplay-off` | 13 | `gemm` | 0.2.0 |
| `20260822-220443_5060ti-splitcurve-gemm-clean-r3` | 13 | `gemm` | 0.3.0 |

### Floor-15 reruns

These runs are named `floor15-rerun` and re-measure the `gemm` and `membw` workloads on a 13-point grid.

| stem | points | workload | schema |
|---|---|---|---|
| `20260822-173451_5060ti-gemm-floor15-rerun` | 13 | `gemm` | 0.3.0 |
| `20260822-174118_5060ti-membw-floor15-rerun` | 13 | `membw` | 0.3.0 |

### Fine-p1/p2 reruns

These runs are re-measurements of the earlier fine-grained baseline sweeps, named `fine-p1-rerun` and `fine-p2-rerun` for both `gemm` and `membw`.

| stem | points | workload | schema |
|---|---|---|---|
| `20260822-174624_5060ti-gemm-fine-p1-rerun` | 13 | `gemm` | 0.3.0 |
| `20260822-175205_5060ti-membw-fine-p1-rerun` | 13 | `membw` | 0.3.0 |
| `20260822-175706_5060ti-membw-fine-p2-rerun` | 13 | `membw` | 0.3.0 |
| `20260822-180206_5060ti-gemm-fine-p2-rerun` | 13 | `gemm` | 0.3.0 |

### Tuned clean sweeps

These runs are named `tuned` and `clean`, with round markers `r1` through `r5` for `gemm` and a single `membw` run. They measure the `gemm` and `membw` workloads.

| stem | points | workload | schema |
|---|---|---|---|
| `20260822-182129_5060ti-tuned-gemm-clean-r1` | 13 | `gemm` | 0.3.0 |
| `20260822-182619_5060ti-tuned-gemm-clean-r2` | 13 | `gemm` | 0.3.0 |
| `20260822-183112_5060ti-tuned-membw-clean` | 10 | `membw` | 0.3.0 |
| `20260822-213750_5060ti-tuned-gemm-clean-r3` | 13 | `gemm` | 0.3.0 |
| `20260822-215317_5060ti-tuned-gemm-clean-r4` | 13 | `gemm` | 0.3.0 |
| `20260822-215811_5060ti-tuned-gemm-clean-r5` | 13 | `gemm` | 0.3.0 |

### Stock clean sweeps

These runs are named `stock` and `clean`, with round markers `r1` and `r2` for the `gemm` workload.

| stem | points | workload | schema |
|---|---|---|---|
| `20260822-201101_5060ti-stock-gemm-clean-r1` | 13 | `gemm` | 0.3.0 |
| `20260822-201554_5060ti-stock-gemm-clean-r2` | 13 | `gemm` | 0.3.0 |

### Mem-only clean sweeps

These runs are named `memonly` and `clean`, with round markers `r1` and `r2` for the `gemm` workload.

| stem | points | workload | schema |
|---|---|---|---|
| `20260822-211705_5060ti-memonly-gemm-clean-r1` | 13 | `gemm` | 0.3.0 |
| `20260822-212156_5060ti-memonly-gemm-clean-r2` | 13 | `gemm` | 0.3.0 |

### Data quality limitations

- **3 of the 26 runs carry schema `0.1.0`** and therefore **cannot be checked for capture-software contamination retrospectively**, because schema `0.1.0` has no video-engine telemetry. A reader using these files cannot rule out that the measured frequencies were affected by unrelated GPU activity.
- **3 of the 26 runs carry a null `applied_settings` field**, which means **the configuration was not recorded**. Null does not mean stock: it means nothing reconstructs what the card was set to. A reader cannot determine the clock, power, or other settings under which these sweeps ran.