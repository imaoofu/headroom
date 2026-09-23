"""Synthetic precollection checks for the offset-ladder scorer (registered section 7)."""

import csv
import json
import tempfile
from pathlib import Path

from score_offset_ladder import ITERATIONS, PREDICTED, RUNG_MHZ, TARGETS, WORKLOADS, score


def check(condition, message):
    if not condition:
        raise AssertionError(message)
    print(f"[PASS] {message}")


def fixture(root, achieved_shift=7.3, split_rung=None, bad_target=False,
            missing_voltage=False, missed_lock=False, wrong_iterations=False, peaks=None):
    for rung in RUNG_MHZ:
        for index, workload in enumerate(WORKLOADS):
            label = f"5060ti-4o-{rung}-{workload}"
            path = root / f"synthetic_{label}_sweep.csv"
            iterations = ITERATIONS[index] + (1 if wrong_iterations and rung == "offset0"
                                              and workload == "copy" else 0)
            metadata = {
                "session_label": label,
                "gpu_name": "NVIDIA GeForce RTX 5060 Ti",
                "driver_version": "synthetic-driver",
                "power_limit_w": "200.00",
                "power_limit_enforced_w": "180.00",
                "power_limit_default_w": "180.00",
                "workload_command": (f"python gpu_workload.py --workload {workload} --json "
                                     f"--iterations {iterations}"),
            }
            path.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
            peak = (peaks or {}).get(rung, PREDICTED.get(rung, PREDICTED["offset0"]))
            if split_rung == rung and index >= 6:
                peak = 1545
            with path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=(
                    "target_frequency_mhz", "achieved_frequency_avg", "bench_throughput",
                    "power_avg_w", "bench_ok", "lock_held", "lock_miss_direction",
                    "power_window_applied", "memory_clock_avg_mhz",
                ))
                writer.writeheader()
                for target in TARGETS:
                    grid_target = (1402 if bad_target and rung == "offset0" and
                                   workload == "copy" and target == 1395 else target)
                    writer.writerow({
                        "target_frequency_mhz": grid_target,
                        "achieved_frequency_avg": grid_target - achieved_shift,
                        "bench_throughput": 200 if target == peak else 100,
                        "power_avg_w": 100,
                        "bench_ok": "True",
                        "lock_held": ("False" if missed_lock and rung == "offsetm300"
                                      and workload == "gemm" and target == 1237 else "True"),
                        "lock_miss_direction": "none",
                        "power_window_applied": "True",
                        "memory_clock_avg_mhz": 13801,
                    })
            if missing_voltage and rung == "offset0close" and workload == "gemm":
                continue
            voltage_path = path.with_name(path.stem + "_voltage.csv")
            with voltage_path.open("w", newline="", encoding="utf-8") as handle:
                writer = csv.DictWriter(handle, fieldnames=(
                    "target", "achieved", "voltage", "sampleCount",
                ))
                writer.writeheader()
                for target in TARGETS:
                    writer.writerow({"target": target, "achieved": target - achieved_shift,
                                     "voltage": 0.720 if target <= peak else 0.730,
                                     "sampleCount": 25})


def evaluate(**kwargs):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        fixture(root, **kwargs)
        return score(root)


def expect_invalid(message, **kwargs):
    try:
        evaluate(**kwargs)
    except ValueError:
        print(f"[PASS] {message}")
        return
    raise AssertionError(f"accepted invalid fixture: {kwargs}")


def main():
    passing = evaluate(achieved_shift=7.3)
    check({rung: passing["medians"][rung] for rung in PREDICTED} == PREDICTED,
          "score target grid, not achieved clocks")
    check(set(passing["per_rung"]) == {"offset0", "offsetm150", "offsetm300"},
          "the closing stock suite carries no prediction of its own")
    check(passing["drift_ok"] and set(passing["per_rung"].values()) == {"PASS"},
          "all three predicted rungs pass inside an agreeing drift bracket")
    check(passing["nonincreasing"] and passing["strict_drops"],
          "registered trend components pass")

    drifted = evaluate(peaks={"offset0close": 1702})
    check(not drifted["drift_ok"]
          and set(drifted["per_rung"].values()) == {"UNINTERPRETABLE"},
          "a drifted bracket scores no rung, even when every rung matches")

    upward = evaluate(peaks={"offsetm300": 1545})
    check(upward["per_rung"]["offsetm300"] == "FAIL" and not upward["nonincreasing"],
          "an upward step at -300 refutes both its rung and the trend")

    split = evaluate(split_rung="offsetm150", achieved_shift=0.6)
    check(split["medians"]["offsetm150"] == 1470, "six/six median falls between grid points")
    check(split["per_rung"]["offsetm150"] == "FAIL", "do not round split to a passing grid point")
    check(split["nonincreasing"], "weak monotonicity differs from exact rung prediction")

    expect_invalid("wrong target grid rejected", bad_target=True)
    expect_invalid("missing voltage extract rejected", missing_voltage=True)
    expect_invalid("missed lock rejected", missed_lock=True)
    expect_invalid("wrong iteration count rejected", wrong_iterations=True)


if __name__ == "__main__":
    main()
