"""Synthetic Session D decisions; no measurement files are written or edited."""

import csv
import json
import tempfile
from pathlib import Path

from score_session_d import REGISTRATION, collapse_control, score


def check(condition, message):
    if not condition:
        print(f"[FAIL] {message}")
        raise AssertionError(message)
    print(f"[PASS] {message}")


def fixture(root, edit1_peak=1170, control_peak=1485, stock4_factor=1.0,
            edit1_floor_end=1170, missing_voltage=False, missed_edit_workload=None,
            achieved_offset=0.0, edit1_peak_by_workload=None):
    # achieved_offset: real sweeps rarely land exactly on target. The first fixtures always did,
    # which is how an exact-equality comparison on achieved clocks passed every test.
    cfg = REGISTRATION
    for run in ("stock-1", "edit1-2", "edit2-3", "stock-4"):
        for workload in cfg.workloads:
            stem = f"synthetic_rtx3070ti-sessiond-{run}-{workload}_sweep"
            csv_path = root / f"{stem}.csv"
            metadata = {
                "session_label": f"rtx3070ti-sessiond-{run}-{workload}",
                "gpu_name": "NVIDIA GeForce RTX 3070 Ti",
                "driver_version": "synthetic-driver",
                "power_limit_default_w": "290.00",
                "power_limit_enforced_w": "290.00",
                "power_limit_w": "320.00",
            }
            csv_path.with_suffix(".json").write_text(json.dumps(metadata), encoding="utf-8")
            with csv_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=(
                    "target_frequency_mhz", "achieved_frequency_avg", "bench_throughput",
                    "power_avg_w", "bench_ok", "lock_miss_direction", "power_window_applied",
                ))
                writer.writeheader()
                for target in cfg.targets:
                    achieved = 1500 if run == "edit2-3" and target in cfg.clipped_targets else target
                    achieved -= achieved_offset
                    run_edit1_peak = (edit1_peak_by_workload or {}).get(workload, edit1_peak)
                    peak = (run_edit1_peak if run == "edit1-2" else
                            control_peak if run == "edit2-3" else 1485)
                    efficiency = 2.0 if target == peak else 1.0
                    factor = stock4_factor if run == "stock-4" else 1.0
                    writer.writerow({
                        "target_frequency_mhz": target,
                        "achieved_frequency_avg": achieved,
                        "bench_throughput": efficiency * 100 * factor,
                        "power_avg_w": 100,
                        "bench_ok": "True",
                        "lock_miss_direction": "none",
                        "power_window_applied": "True",
                    })
            if missing_voltage and run == "edit1-2" and workload == "gemm":
                continue
            voltage_path = csv_path.with_name(csv_path.stem + "_voltage.csv")
            with voltage_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=(
                    "target", "achieved", "voltage", "sampleCount",
                ))
                writer.writeheader()
                for target in cfg.targets:
                    achieved = 1500 if run == "edit2-3" and target in cfg.clipped_targets else target
                    achieved -= achieved_offset
                    floor_end =(1485 if run == "edit1-2" and workload == missed_edit_workload
                                 else edit1_floor_end if run == "edit1-2" else
                                 cfg.clipped_targets[-1] if run == "edit2-3" else 1485)
                    writer.writerow({
                        "target": target,
                        "achieved": achieved,
                        "voltage": 0.812 if target <= floor_end else 0.831,
                        "sampleCount": 25,
                    })


def evaluate(**kwargs):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        fixture(root, **kwargs)
        return score(root)


def main():
    passed = evaluate()
    check(passed["eligibility"] == "VALID", "synthetic pass is scoreable")
    check(passed["medians"]["edit1-2"] == 1170, "Edit 1 median uses target-grid optima")

    # Added at review 2026-09-22. Both cases scored wrongly in the first version.
    offset = evaluate(achieved_offset=0.6)
    check(offset["eligibility"] == "VALID" and offset["joint"] == "CAUSAL_CLAIM_REPLICATES_ON_SECOND_CHIP",
          "a 0.6 MHz achieved-clock offset does not change the verdict")
    split = evaluate(edit1_peak_by_workload={name: (1170 if i < 6 else 1275)
                                             for i, name in enumerate(REGISTRATION.workloads)})
    check(split["medians"]["edit1-2"] == 1222.5 and split["4a"] == "PASS",
          "an even 1170/1275 split has median 1222.5, inside the registered range, and passes")
    check(passed["4a"] == "PASS" and passed["4b"] == "PASS",
          "both registered predictions pass")
    check(passed["joint"] == "CAUSAL_CLAIM_REPLICATES_ON_SECOND_CHIP",
          "pass verdict requires manipulation and control")
    check(all(bin_row["count"] == 6 for bin_row in passed["clipped_bins"].values()),
          "six clipped targets collapse to one bin per workload")
    check(passed["floors"]["stock-1"]["top_mhz"] == 1485
          and passed["floors"]["edit1-2"]["top_mhz"] == 1170
          and passed["floors"]["edit2-3"]["top_mhz"] == 1500,
          "voltage extracts determine each floor top")
    check(passed["floors"]["edit1-2"]["first_above_mhz"] == 1275,
          "voltage extracts locate the first rise after Edit 1")

    rows = [{"target": target, "mhz": 1500 if target in REGISTRATION.clipped_targets
             else target, "efficiency": 1.0} for target in REGISTRATION.targets]
    rows[-1]["efficiency"] = 9.0
    collapsed, bin_row = collapse_control(rows)
    check(len(collapsed) == 8 and bin_row["efficiency"] == 1.0,
          "one noisy clipped row cannot win by maximum-of-six selection")

    failed = evaluate(edit1_peak=1485)
    check(failed["4a"] == "FAIL_NO_DOWNWARD_MOVEMENT" and failed["4b"] == "PASS",
          "unchanged Edit 1 optimum fails registered prediction")
    check(failed["joint"] == "CAUSAL_CLAIM_REFUTED_ON_SECOND_CHIP",
          "unchanged Edit 1 gets refutation verdict")

    moved_control = evaluate(control_peak=1170)
    check(moved_control["4a"] == "PASS" and moved_control["4b"] == "FAIL",
          "moved control fails negative control")
    check(moved_control["joint"] == "CONTROL_ALSO_MOVES_ATTRIBUTION_FAILS",
          "moved control changes the attribution verdict")

    both_fail = evaluate(edit1_peak=1485, control_peak=1170)
    check(both_fail["joint"] == "BOTH_PREDICTIONS_FAIL",
          "both failures are distinguished from the control-also-moves case")

    partial_move = evaluate(edit1_peak=1380)
    check(partial_move["4a"] == "FAIL_OTHER_DOWNWARD_BIN"
          and partial_move["joint"] == "EDIT1_MOVED_DOWN_OUTSIDE_REGISTERED_BINS",
          "unpredicted downward movement is reported without a no-movement claim")

    drift = evaluate(stock4_factor=1.03)
    check(drift["eligibility"] == "DRIFT_OR_BASELINE_MISMATCH"
          and drift["4a"] == "NOT_SCOREABLE", "stock return failure blocks effect verdict")

    no_edit = evaluate(edit1_floor_end=1485)
    check(no_edit["eligibility"] == "CURVE_EDIT_NOT_VERIFIED",
          "unchanged load floor cannot support a causal verdict")
    one_missed_edit = evaluate(missed_edit_workload="gemm")
    check(one_missed_edit["eligibility"] == "CURVE_EDIT_NOT_VERIFIED",
          "one unmodified workload is not hidden by a suite median")

    try:
        evaluate(missing_voltage=True)
    except ValueError as exc:
        check("missing companion file" in str(exc), "missing voltage extract is rejected")
    else:
        check(False, "missing voltage extract is rejected")


if __name__ == "__main__":
    main()
