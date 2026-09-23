"""Score the registered RTX 3070 Ti Session D before its measurements exist.

Usage: python analysis/score_session_d.py PATH_TO_SESSION_D_RESULTS

The directory may contain the four Collect.ps1 run directories or their files
directly. Each run needs twelve sweep CSVs, matching sweep JSONs, and separate
HWiNFO _sweep_voltage.csv extracts. This script only reads them.

Per-row efficiency and filtering come from analyze_sweep.loadSweep. Only Edit 2's
six clipped targets are combined afterward, as the runsheet requires.
"""

import argparse
import csv
import json
import math
import statistics
import sys
from dataclasses import dataclass
from pathlib import Path

from analyze_sweep import efficiencyPeak, loadSweep


@dataclass(frozen=True)
class SessionDRegistration:
    # "1 stock ... 2 Edit 1 ... 3 Edit 2 ... 4 stock" (A/B/B/A table).
    runs: tuple[str, ...] = ("stock-1", "edit1-2", "edit2-3", "stock-4")
    # SESSION-D-RUNSHEET.md, "The suite is copy, reduce, ... conv, gemm".
    workloads: tuple[str, ...] = (
        "copy", "reduce", "softmax", "layernorm", "bgemm32", "bgemm64",
        "bgemm128", "bgemm256", "bgemm1024", "attention", "conv", "gemm",
    )
    # "Grid: hold the suite grid constant ... 855 to 2115 MHz in 105 MHz steps."
    targets: tuple[int, ...] = tuple(range(855, 2116, 105))
    # "Floor band is three codes wide ... 0.825 V ... inside the flat region."
    floor_max_v: float = 0.825
    # Edit 1: "at or below 0.825 V ... 1200 MHz"; "0.831 V and above ... stock".
    edit1_curve_boundary_v: float = 0.825
    edit1_curve_cap_mhz: int = 1200
    first_above_floor_v: float = 0.831
    # 4a: "median suite optimum moves down from 1485 MHz ... 1170 or 1275 MHz".
    stock_optimum_mhz: int = 1485
    edit1_optima_mhz: tuple[int, ...] = (1170, 1275)
    # 4b restated: "top of the floor, ~1485-1500 MHz achieved".
    control_min_mhz: int = 1485
    control_max_mhz: int = 1500
    # 4b: "1590, 1695, 1800, 1905, 2010, 2115" clip to "~1500 each".
    clipped_targets: tuple[int, ...] = (1590, 1695, 1800, 1905, 2010, 2115)
    clipped_achieved_mhz: int = 1500
    # Operational acceptance for "~1500", fixed before collection at < 1/4 grid step.
    clip_tolerance_mhz: int = 25
    # "If run 4 does not come back to run 1 within ~1.5%, ... drift-contaminated."
    stock_return_tolerance_pct: float = 1.5
    # "290 / 290 / 320 W" identifies SILENT BIOS.
    silent_power_default_w: int = 290
    silent_power_max_w: int = 320


REGISTRATION = SessionDRegistration()
RUNS = REGISTRATION.runs


def median(values):
    return statistics.median(values)


def read_voltage(path, expected_targets):
    by_target = {}
    with path.open(encoding="utf-8-sig", newline="") as handle:
        for raw in csv.DictReader(handle):
            try:
                target = int(float(raw["target"]))
                achieved = float(raw["achieved"])
                voltage = float(raw["voltage"])
                sample_count = int(float(raw["sampleCount"]))
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"{path}: invalid voltage extract row: {exc}") from exc
            if target in by_target or sample_count < 1 or not all(
                math.isfinite(value) and value > 0 for value in (achieved, voltage)
            ):
                raise ValueError(f"{path}: duplicate, empty, or invalid reading at {target}")
            by_target[target] = {"mhz": achieved, "voltage": voltage}
    if set(by_target) != set(expected_targets):
        raise ValueError(f"{path}: voltage targets differ from registered grid")
    return by_target


def collapse_control(rows):
    """Six repeated achieved ~1500 MHz rows become one median-efficiency bin.

    Each row's efficiency is still computed by analyze_sweep.loadSweep. Taking the
    median of six, rather than their maximum, removes the six-draw selection
    advantage identified in the runsheet before the result was collected.
    """
    cfg = REGISTRATION
    by_target = {row["target"]: row for row in rows}
    selected = [by_target[target] for target in cfg.clipped_targets]
    if any(abs(row["mhz"] - cfg.clipped_achieved_mhz) > cfg.clip_tolerance_mhz
           for row in selected):
        raise ValueError("Edit 2's six high targets did not clip to about 1500 MHz")
    bin_row = {
        "target": "clipped high targets",
        "mhz": median(row["mhz"] for row in selected),
        "efficiency": median(row["efficiency"] for row in selected),
        "count": len(selected),
    }
    others = [row for row in rows if row["target"] not in cfg.clipped_targets]
    return others + [bin_row], bin_row


def read_run_file(csv_path, run, workload):
    cfg = REGISTRATION
    json_path = csv_path.with_suffix(".json")
    voltage_path = csv_path.with_name(csv_path.stem + "_voltage.csv")
    for path in (json_path, voltage_path):
        if not path.is_file():
            raise ValueError(f"missing companion file: {path}")
    with json_path.open(encoding="utf-8-sig") as handle:
        metadata = json.load(handle)
    if metadata.get("session_label") != f"rtx3070ti-sessiond-{run}-{workload}":
        raise ValueError(f"{json_path}: session_label does not match filename/run")
    if "RTX 3070 Ti" not in metadata.get("gpu_name", ""):
        raise ValueError(f"{json_path}: wrong GPU")
    for field, expected in (("power_limit_default_w", cfg.silent_power_default_w),
                            ("power_limit_enforced_w", cfg.silent_power_default_w),
                            ("power_limit_w", cfg.silent_power_max_w)):
        if field not in metadata or float(metadata[field]) != expected:
            raise ValueError(f"{json_path}: {field} does not match SILENT BIOS")
    try:
        rows = loadSweep(csv_path)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{csv_path}: invalid sweep row: {exc}") from exc
    if len(rows) != len(cfg.targets) or {row["target"] for row in rows} != set(cfg.targets):
        raise ValueError(f"{csv_path}: usable sweep rows do not match the "
                         f"{len(cfg.targets)}-point grid")
    if not all(math.isfinite(row[field]) and row[field] > 0
               for row in rows for field in ("mhz", "throughput", "power", "efficiency")):
        raise ValueError(f"{csv_path}: nonpositive or nonfinite sweep measurement")
    if not all(row["windowed"] for row in rows):
        raise ValueError(f"{csv_path}: power was not windowed for every point")
    volts = read_voltage(voltage_path, cfg.targets)
    for row in rows:
        if abs(row["mhz"] - volts[row["target"]]["mhz"]) > cfg.clip_tolerance_mhz:
            raise ValueError(f"{voltage_path}: achieved clock disagrees with sweep at "
                             f"{row['target']} MHz")
    if run == "edit2-3":
        options, clipped_bin = collapse_control(rows)
    else:
        options, clipped_bin = rows, None
    best = efficiencyPeak(options)
    # The registered numbers (1485, 1170, 1275) are TARGET grid points, so the optimum is scored
    # as one. Corrected at review 2026-09-22: the first version used the ACHIEVED clock and then
    # tested it for exact equality with those grid numbers, which any sub-MHz offset breaks.
    # With a 0.6 MHz offset a passing fixture came back NOT_SCOREABLE. Edit 2's clipped bin
    # has no single target, so it counts as its registered achieved value, ~1500.
    grid = cfg.clipped_achieved_mhz if best is clipped_bin else best["target"]
    return {"rows": rows, "volts": volts, "best": best, "grid": grid, "clipped_bin": clipped_bin,
            "driver": metadata.get("driver_version", "")}


def find_files(directory):
    grouped = {run: {} for run in RUNS}
    for path in directory.rglob("*_sweep.csv"):
        name = path.stem
        for run in RUNS:
            prefix = f"rtx3070ti-sessiond-{run}-"
            if prefix in name:
                workload = name.split(prefix, 1)[1].removesuffix("_sweep")
                if workload not in REGISTRATION.workloads:
                    raise ValueError(f"{path}: unknown workload {workload!r}")
                if workload in grouped[run]:
                    raise ValueError(f"duplicate {run}/{workload} sweeps")
                grouped[run][workload] = path
                break
    for run in RUNS:
        missing = set(REGISTRATION.workloads) - set(grouped[run])
        if missing:
            raise ValueError(f"{run}: missing workload sweeps: {', '.join(sorted(missing))}")
    return grouped


def floor_summary(workloads):
    cfg = REGISTRATION
    points = []
    for target in cfg.targets:
        readings = [workloads[name]["volts"][target] for name in cfg.workloads]
        points.append((target, median(r["mhz"] for r in readings),
                       median(r["voltage"] for r in readings)))
    floor = [point for point in points if point[2] <= cfg.floor_max_v]
    above = [point for point in points if point[2] >= cfg.first_above_floor_v]
    return {
        "top_mhz": max((point[1] for point in floor), default=None),
        "first_above_mhz": min((point[1] for point in above), default=None),
        "by_target": {target: voltage for target, _, voltage in points},
    }


def stock_return(first, last):
    cfg = REGISTRATION
    per_workload = {}
    for name in cfg.workloads:
        a = {row["target"]: row for row in first[name]["rows"]}
        b = {row["target"]: row for row in last[name]["rows"]}
        per_workload[name] = median(
            abs(100 * (b[target]["throughput"] / a[target]["throughput"] - 1))
            for target in cfg.targets
        )
    return per_workload


def score(directory):
    cfg = REGISTRATION
    paths = find_files(directory)
    runs = {run: {name: read_run_file(paths[run][name], run, name)
                  for name in cfg.workloads} for run in RUNS}
    drivers = {item["driver"] for suite in runs.values() for item in suite.values()}
    if len(drivers) != 1 or not next(iter(drivers)):
        raise ValueError(f"driver version is missing or changed during Session D: {drivers}")

    optima = {run: {name: runs[run][name]["grid"] for name in cfg.workloads}
              for run in RUNS}
    medians = {run: median(optima[run].values()) for run in RUNS}
    # Achieved clocks at each optimum, reported beside the verdict but never used to score it.
    achieved = {run: {name: runs[run][name]["best"]["mhz"] for name in cfg.workloads}
                for run in RUNS}
    floors = {run: floor_summary(runs[run]) for run in RUNS}
    drift = stock_return(runs["stock-1"], runs["stock-4"])
    drifted = any(value > cfg.stock_return_tolerance_pct for value in drift.values())
    baseline_ok = medians["stock-1"] == cfg.stock_optimum_mhz
    stock_return_ok = medians["stock-4"] == medians["stock-1"] and not drifted

    def stock_floor(run):
        return all(
            suite["volts"][cfg.stock_optimum_mhz]["voltage"] <= cfg.floor_max_v
            and suite["volts"][cfg.clipped_targets[0]]["voltage"]
            >= cfg.first_above_floor_v
            for suite in runs[run].values()
        )

    stock1_floor_ok = stock_floor("stock-1")
    stock4_floor_ok = stock_floor("stock-4")
    edit1_floor_ok = all(
        suite["volts"][cfg.edit1_optima_mhz[0]]["voltage"] <= cfg.floor_max_v
        and all(suite["volts"][target]["voltage"] >= cfg.first_above_floor_v
                for target in cfg.targets if target > cfg.edit1_curve_cap_mhz)
        and max((suite["volts"][target]["mhz"] for target in cfg.targets
                 if suite["volts"][target]["voltage"] <= cfg.floor_max_v),
                default=float("inf")) <= cfg.edit1_curve_cap_mhz + cfg.clip_tolerance_mhz
        for suite in runs["edit1-2"].values()
    )
    control_floor_ok = all(
        suite["volts"][cfg.stock_optimum_mhz]["voltage"] <= cfg.floor_max_v
        and all(suite["volts"][target]["voltage"] <= cfg.floor_max_v
                for target in cfg.clipped_targets)
        for suite in runs["edit2-3"].values()
    )

    if not baseline_ok or not stock_return_ok:
        eligibility = "DRIFT_OR_BASELINE_MISMATCH"
    elif not (stock1_floor_ok and stock4_floor_ok and edit1_floor_ok
              and control_floor_ok):
        eligibility = "CURVE_EDIT_NOT_VERIFIED"
    else:
        eligibility = "VALID"
    if eligibility == "VALID":
        # "moves down to 1170 or 1275": with twelve workloads the median can fall BETWEEN the
        # two, e.g. six at each gives 1222.5, and that is inside the registered range, not
        # outside it. The first version tested set membership and scored that case a failure.
        if min(cfg.edit1_optima_mhz) <= medians["edit1-2"] <= max(cfg.edit1_optima_mhz):
            result_4a = "PASS"
        elif medians["edit1-2"] >= medians["stock-1"]:
            result_4a = "FAIL_NO_DOWNWARD_MOVEMENT"
        else:
            result_4a = "FAIL_OTHER_DOWNWARD_BIN"
        result_4b = ("PASS" if cfg.control_min_mhz <= medians["edit2-3"]
                     <= cfg.control_max_mhz else "FAIL")
        if result_4a == "PASS" and result_4b == "PASS":
            joint = "CAUSAL_CLAIM_REPLICATES_ON_SECOND_CHIP"
        elif result_4a == "PASS":
            joint = "CONTROL_ALSO_MOVES_ATTRIBUTION_FAILS"
        elif result_4b == "FAIL":
            joint = "BOTH_PREDICTIONS_FAIL"
        elif result_4a == "FAIL_NO_DOWNWARD_MOVEMENT":
            joint = "CAUSAL_CLAIM_REFUTED_ON_SECOND_CHIP"
        else:
            joint = "EDIT1_MOVED_DOWN_OUTSIDE_REGISTERED_BINS"
    else:
        result_4a = result_4b = "NOT_SCOREABLE"
        joint = eligibility
    return {
        "driver": next(iter(drivers)),
        "optima": optima,
        "achieved_at_optima": achieved,
        "medians": medians,
        "floors": floors,
        "drift_per_workload_pct": drift,
        "floor_checks": {"stock-1": stock1_floor_ok, "edit1-2": edit1_floor_ok,
                         "edit2-3": control_floor_ok, "stock-4": stock4_floor_ok},
        "eligibility": eligibility,
        "4a": result_4a,
        "4b": result_4b,
        "joint": joint,
        "clipped_bins": {name: runs["edit2-3"][name]["clipped_bin"]
                         for name in cfg.workloads},
    }


def report(result):
    cfg = REGISTRATION
    print(f"Session D scorer | RTX 3070 Ti | driver {result['driver']}")
    print("Efficiency = bench_throughput / power_avg_w via analyze_sweep.loadSweep.")
    print("Efficiency argmax uses loadSweep's achieved-clock-sorted rows. "
          "Edit 2's six clipped targets are one median-efficiency bin per workload.")
    for run in RUNS:
        floor = result["floors"][run]
        print(f"{run}: median optimum {result['medians'][run]:g} MHz (target grid; clipped bin = "
              f"{cfg.clipped_achieved_mhz}); "
              f"highest sampled floor clock {floor['top_mhz']!s} MHz, "
              f"lowest sampled above-floor clock {floor['first_above_mhz']!s} MHz")
        print("  " + ", ".join(f"{name}={result['optima'][run][name]:g}"
                            for name in cfg.workloads))
    print("Edit 2 clipped targets "
          + ", ".join(str(target) for target in cfg.clipped_targets)
          + f": one bin for each of {len(cfg.workloads)} workloads.")
    print("Stock return: worst workload median absolute matched-target throughput change "
          f"{max(result['drift_per_workload_pct'].values()):.3f}% "
          f"(limit {cfg.stock_return_tolerance_pct:.1f}%).")
    print("Floor verification: " + ", ".join(
        f"{name}={'yes' if passed else 'NO'}"
        for name, passed in result["floor_checks"].items()))
    print(f"Eligibility: {result['eligibility']}")
    print(f"4a Edit 1 prediction: {result['4a']}")
    print(f"4b Edit 2 negative control: {result['4b']}")
    print(f"Joint registered outcome: {result['joint']}")
    print("Per-workload counts are descriptive only: identical stock suites agreed on "
          "9 of 12 argmaxes in one prior pair.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="Directory holding all four Session D runs")
    args = parser.parse_args(argv)
    if not args.directory.is_dir():
        parser.error(f"not a directory: {args.directory}")
    try:
        result = score(args.directory)
    except (ValueError, TypeError, OSError, csv.Error, json.JSONDecodeError) as exc:
        print(f"Session D cannot be scored: {exc}", file=sys.stderr)
        return 2
    report(result)
    return 0 if result["eligibility"] == "VALID" else 2


if __name__ == "__main__":
    raise SystemExit(main())
