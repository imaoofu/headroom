TASK: write analysis/compare_fine_pair.py, which compares two frequency sweeps point by point

Return the COMPLETE contents of one Python file and nothing else: no explanation before or after.

## YOU HAVE NO TOOLS AND CANNOT READ ANY FILE

Everything you need is in this message. Do not claim to have run anything. Your output will be run
afterwards against two real sweep files, and every number will be checked.

## Why it exists

The project sweeps a GPU through a list of locked core clocks and records throughput and power at
each. It needs to compare two sweeps of the same grid, for example one run ascending and one run
descending, and say how much each point differs. It must **report differences, never explain them**:
it cannot know whether a difference comes from sweep order, temperature or the day it ran.

## Input format

Each sweep is a CSV written with a UTF-8 byte-order mark, so read it with `encoding="utf-8-sig"`.
Every value is double-quoted. The header row, exactly as written:

```
"target_frequency_mhz","achieved_frequency_avg","achieved_frequency_min","achieved_frequency_max","memory_clock_avg_mhz","memory_clock_min_mhz","memory_clock_max_mhz","lock_held","lock_miss_mhz","lock_miss_direction","power_avg_w","power_min_w","power_max_w","temperature_avg_c","temperature_max_c","utilization_avg_pct","power_avg_process_w","power_window_applied","window_start_unix","window_end_unix","workload_seconds","bench_seconds","bench_wall_seconds","bench_monitoring_s","bench_throughput","bench_throughput_unit","bench_ok","samples","samples_process","throttle_masks_seen"
```

Two real rows:

```
"1590","1590","1590","1590","9251","9251","9251","True","0","none","210.08","85.91","222.3","60.4","62","97.6","155.56","True","1790226602.2067","1790226611.145","13.032","8.7646","8.9344","0.1697","15053854994107.9","FLOP/s","True","16","24","0x0000000000000001;0x0000000000000000"
"1545","1545","1545","1545","9251","9251","9251","True","0","none","201.02","124.27","211.04","59","61","100","151.99","True","1790226623.4695","1790226632.6609","13.555","9.0105","9.1924","0.1819","14642990848540.303","FLOP/s","True","17","25","0x0000000000000001;0x0000000000000000"
```

`lock_held` and `bench_ok` are the strings `True` or `False`. Rows may be in any order. Do not
assume ascending order.

## The API: the checker imports these names

```python
def load_sweep(path) -> dict[int, dict]:
```
Returns a dict keyed by `int(target_frequency_mhz)`. Each value is a dict with exactly these keys:
- `achieved` (float, from `achieved_frequency_avg`);
- `throughput` (float, `bench_throughput`);
- `power` (float, `power_avg_w`);
- `temp` (float, `temperature_avg_c`);
- `lock_held` (bool);
- `bench_ok` (bool).

Raise `ValueError` with a message naming the file:
- if any of those six source columns is missing;
- if a target appears twice;
- if `bench_throughput` is empty on any row.

```python
def compare(a: dict, b: dict) -> dict:
```
Takes two `load_sweep` results. Sweep `a` is the reference; every delta is `b` relative to `a`.
Returns a dict with:
- `points`: a list, one entry per target present in BOTH, sorted by target ascending. Each entry is
  a dict with:
  - `target`;
  - `throughput_a`, `throughput_b`, and `delta_pct` = `100 * (throughput_b / throughput_a - 1)`;
  - `power_a`, `power_b`;
  - `eff_a` = `throughput_a / power_a` and `eff_b` likewise;
  - `temp_a`, `temp_b`;
  - `clean`: True only if `lock_held` and `bench_ok` are True in BOTH sweeps.
- `only_a` and `only_b`: sorted lists of targets present in one sweep but not the other.
- `mean_delta_pct`, `min_delta_pct`, `max_delta_pct`: over clean points only, or `None` if there
  are none.
- `argmax_eff_a`: the target with the highest `eff_a` among clean points, else `None`.
  `argmax_eff_b` is the same for `eff_b`.

Do not round anything inside `compare`. Rounding is for printing only.

## The command line

`python analysis/compare_fine_pair.py A.csv B.csv [--json]`

- Without `--json`, print:
  1. a table with one row per shared target: target, throughput a and b in TFLOP/s (divide by
     1e12, 3 decimals), delta % (2 decimals, with sign), power a and b (1 decimal), efficiency a
     and b in GFLOP/s per W (divide throughput by power and by 1e9, 2 decimals), temperature a
     and b (1 decimal), and a clean mark;
  2. complete sentences: how many targets were shared, how many were clean, the mean, minimum
     and maximum delta over clean points, and each sweep's efficiency argmax;
  3. the sentence: "A difference between two sweeps is not attributed to anything by this tool:
     sweep order, temperature, time of day and session all differ together."
- With `--json`, print `compare()`'s result as JSON instead.
- Exit 2 with a one-line message on a `ValueError`.

## Style

Python 3.10+, standard library only (`csv`, `json`, `argparse`). Descriptive names. A short module
docstring saying what the tool does and what it does not do.
