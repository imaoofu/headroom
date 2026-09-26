"""Score the registered RTX 2060 Super Session E (4c and 4d) before its measurements exist.

Usage:
    python analysis/score_session_e.py PATH_TO_SESSION_E_RESULTS          # 4c, the three suites
    python analysis/score_session_e.py PATH_TO_SESSION_E_RESULTS --4d     # 4d, the descending sweep

The criteria are REGISTERED-PREDICTIONS §4d's amendment of 2026-09-25, "how Session E scores 4c
and 4d", written before collection. The directory may hold the Headroom Bench run folders or
their files directly. Every sweep needs its JSON and a separate HWiNFO _sweep_voltage.csv extract.
This script only reads them.
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
from score_session_d import read_voltage

REPO = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class SessionERegistration:
    # build_sessione.py: E2 is stock-1 -> edit-2 -> stock-3.
    runs: tuple[str, ...] = ("stock-1", "edit-2", "stock-3")
    workloads: tuple[str, ...] = (
        "copy", "reduce", "softmax", "layernorm", "bgemm32", "bgemm64",
        "bgemm128", "bgemm256", "bgemm1024", "attention", "conv", "gemm",
    )
    # Run sheet Part 2: "Grid 855-2115 MHz, 13 points, the same as that suite."
    targets: tuple[int, ...] = tuple(range(855, 2116, 105))
    # "the median suite optimum moves from 1065 MHz down toward 855 MHz".
    stock_optimum_mhz: int = 1065
    pass_min_mhz: int = 855
    pass_max_mhz: int = 960
    stock_return_tolerance_pct: float = 1.5
    # build_sessione.py witness ranges. Every clock above 810 MHz needs 0.669 V under the edit.
    edit_min_v: float = 0.668
    stock_check_mhz: int = 1065
    stock_at_check_v: tuple[float, float] = (0.630, 0.657)
    # POWER in build_sessione.py, and every committed sweep on this card.
    power_default_w: int = 175
    power_max_w: int = 185
    # 4d: the ascending reference and its registered minimum.
    ascending_reference: str = ("data/frequency-sweeps/rtx2060s-finefloor-20260915/"
                                "20260915-160921_rtx2060s-finefloor-gemm_sweep.csv")
    minimum_band_mhz: tuple[int, int] = (975, 1005)
    # Under half of one 6.25 mV code, so a median between two codes ties with the lower one.
    minimum_tie_v: float = 0.003
    e1_label: str = "rtx2060s-sessione-e1-desc"


REGISTRATION = SessionERegistration()


def median(values):
    return statistics.median(values)


def read_metadata(json_path, expected_label):
    if not json_path.is_file():
        raise ValueError(f"missing companion file: {json_path}")
    with json_path.open(encoding="utf-8-sig") as handle:
        metadata = json.load(handle)
    if metadata.get("session_label") != expected_label:
        raise ValueError(f"{json_path}: session_label does not match {expected_label}")
    if "RTX 2060 SUPER" not in metadata.get("gpu_name", "").upper():
        raise ValueError(f"{json_path}: wrong GPU")
    cfg = REGISTRATION
    for field, expected in (("power_limit_default_w", cfg.power_default_w),
                            ("power_limit_enforced_w", cfg.power_default_w),
                            ("power_limit_w", cfg.power_max_w)):
        if field not in metadata or float(metadata[field]) != expected:
            raise ValueError(f"{json_path}: {field} is not {expected} W")
    return metadata


def read_temperatures(csv_path):
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        return {int(float(row["target_frequency_mhz"])): float(row["temperature_avg_c"])
                for row in csv.DictReader(handle)}


def read_suite_file(csv_path, run, workload):
    cfg = REGISTRATION
    metadata = read_metadata(csv_path.with_suffix(".json"), f"rtx2060s-sessione-{run}-{workload}")
    voltage_path = csv_path.with_name(csv_path.stem + "_voltage.csv")
    if not voltage_path.is_file():
        raise ValueError(f"missing companion file: {voltage_path}")
    try:
        rows = loadSweep(csv_path)
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"{csv_path}: invalid sweep row: {exc}") from exc
    if len(rows) != len(cfg.targets) or {row["target"] for row in rows} != set(cfg.targets):
        raise ValueError(f"{csv_path}: usable sweep rows do not match the 13-point grid")
    if not all(math.isfinite(row[field]) and row[field] > 0
               for row in rows for field in ("mhz", "throughput", "power", "efficiency")):
        raise ValueError(f"{csv_path}: nonpositive or nonfinite sweep measurement")
    if not all(row["windowed"] for row in rows):
        raise ValueError(f"{csv_path}: power was not windowed for every point")
    volts = read_voltage(voltage_path, cfg.targets)
    best = efficiencyPeak(rows)
    # Scored on the TARGET grid point, as Session D is: the registered 1065 / 855 are grid points.
    return {"rows": rows, "volts": volts, "best": best, "grid": best["target"],
            "driver": metadata.get("driver_version", "")}


def find_suites(directory):
    cfg = REGISTRATION
    grouped = {run: {} for run in cfg.runs}
    for path in directory.rglob("*_sweep.csv"):
        for run in cfg.runs:
            prefix = f"rtx2060s-sessione-{run}-"
            if prefix in path.stem:
                workload = path.stem.split(prefix, 1)[1].removesuffix("_sweep")
                if workload not in cfg.workloads:
                    raise ValueError(f"{path}: unknown workload {workload!r}")
                if workload in grouped[run]:
                    raise ValueError(f"duplicate {run}/{workload} sweeps")
                grouped[run][workload] = path
                break
    for run in cfg.runs:
        missing = set(cfg.workloads) - set(grouped[run])
        if missing:
            raise ValueError(f"{run}: missing workload sweeps: {', '.join(sorted(missing))}")
    return grouped


def stock_return(first, last):
    cfg = REGISTRATION
    per_workload = {}
    for name in cfg.workloads:
        a = {row["target"]: row for row in first[name]["rows"]}
        b = {row["target"]: row for row in last[name]["rows"]}
        per_workload[name] = median(abs(100 * (b[t]["throughput"] / a[t]["throughput"] - 1))
                                    for t in cfg.targets)
    return per_workload


def stock_verified(suite):
    cfg = REGISTRATION
    low, high = cfg.stock_at_check_v
    return all(low <= item["volts"][cfg.stock_check_mhz]["voltage"] <= high
               for item in suite.values())


def edit_verified(suite):
    cfg = REGISTRATION
    return all(item["volts"][target]["voltage"] >= cfg.edit_min_v
               for item in suite.values() for target in cfg.targets)


def score_4c(directory):
    cfg = REGISTRATION
    paths = find_suites(directory)
    runs = {run: {name: read_suite_file(paths[run][name], run, name) for name in cfg.workloads}
            for run in cfg.runs}
    drivers = {item["driver"] for suite in runs.values() for item in suite.values()}
    if len(drivers) != 1 or not next(iter(drivers)):
        raise ValueError(f"driver version is missing or changed during Session E: {drivers}")
    optima = {run: {name: runs[run][name]["grid"] for name in cfg.workloads} for run in cfg.runs}
    medians = {run: median(optima[run].values()) for run in cfg.runs}
    drift = stock_return(runs["stock-1"], runs["stock-3"])
    checks = {"stock-1 verified at 1065 MHz": stock_verified(runs["stock-1"]),
              "edit-2 at or above 0.668 V everywhere": edit_verified(runs["edit-2"]),
              "stock-3 verified at 1065 MHz": stock_verified(runs["stock-3"])}
    reasons = []
    if medians["stock-3"] != medians["stock-1"]:
        reasons.append(f"stock-3 median {medians['stock-3']:g} differs from stock-1's "
                       f"{medians['stock-1']:g}")
    over = sorted(name for name, value in drift.items() if value > cfg.stock_return_tolerance_pct)
    if over:
        reasons.append(f"stock-1 to stock-3 change above {cfg.stock_return_tolerance_pct:.1f}%: "
                       + ", ".join(over))
    reasons += [f"check failed: {name}" for name, passed in checks.items() if not passed]
    edit, stock = medians["edit-2"], medians["stock-1"]
    if reasons:
        verdict = "NOT_SCOREABLE"
    elif edit >= stock:
        verdict = "FAIL_NO_MOVEMENT"
    elif cfg.pass_min_mhz <= edit <= cfg.pass_max_mhz:
        verdict = "PASS"
    else:
        verdict = "FAIL_PARTIAL"
    return {"driver": next(iter(drivers)), "optima": optima, "medians": medians,
            "drift_per_workload_pct": drift, "checks": checks, "not_scoreable_reasons": reasons,
            "baseline_matches_registration": stock == cfg.stock_optimum_mhz,
            "moved_count": sum(optima["edit-2"][n] != optima["stock-1"][n] for n in cfg.workloads),
            "moved_down_count": sum(optima["edit-2"][n] < optima["stock-1"][n]
                                    for n in cfg.workloads),
            "4c": verdict}


def read_fine_sweep(csv_path):
    if not csv_path.is_file():
        raise ValueError(f"missing sweep: {csv_path}")
    voltage_path = csv_path.with_name(csv_path.stem + "_voltage.csv")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        targets = [int(float(row["target_frequency_mhz"])) for row in csv.DictReader(handle)]
    volts = read_voltage(voltage_path, targets)
    return targets, volts, read_temperatures(csv_path)


def minimum_set(volts):
    lowest = min(reading["voltage"] for reading in volts.values())
    return sorted(t for t, reading in volts.items()
                  if reading["voltage"] <= lowest + REGISTRATION.minimum_tie_v)


def classify_minimum(targets, minimum):
    cfg = REGISTRATION
    bottom, top = min(targets), max(targets)
    if all(cfg.minimum_band_mhz[0] <= t <= cfg.minimum_band_mhz[1] for t in minimum):
        return "HOLDS"
    if bottom in minimum and top in minimum:
        return "FLAT"
    if bottom in minimum:
        return "MINIMUM_REACHES_BOTTOM"
    if top in minimum:
        return "MINIMUM_AT_TOP"
    return "PARTIAL"


def score_4d(directory, reference=None):
    cfg = REGISTRATION
    reference = reference or REPO / cfg.ascending_reference
    found = [p for p in directory.rglob("*_sweep.csv") if p.stem.endswith(cfg.e1_label + "_sweep")]
    if len(found) != 1:
        raise ValueError(f"expected one {cfg.e1_label} sweep, found {len(found)}")
    metadata = read_metadata(found[0].with_suffix(".json"), cfg.e1_label)
    asc_targets, asc_volts, asc_temps = read_fine_sweep(reference)
    targets, volts, temps = read_fine_sweep(found[0])
    reasons = []
    if metadata.get("sweep_order") != "descending":
        reasons.append(f"sweep_order is {metadata.get('sweep_order')!r}, not 'descending'")
    if sorted(targets) != sorted(asc_targets):
        reasons.append("targets differ from the ascending reference's 13")
    low, high = cfg.stock_at_check_v
    at_check = volts.get(cfg.stock_check_mhz, {}).get("voltage")
    if at_check is None or not low <= at_check <= high:
        reasons.append(f"reads {at_check} V at {cfg.stock_check_mhz} MHz, outside the stock "
                       f"range {low}-{high}")
    minimum = minimum_set(volts)
    with open(reference.with_suffix(".json"), encoding="utf-8-sig") as handle:
        reference_driver = json.load(handle).get("driver_version", "")
    return {"driver": metadata.get("driver_version", ""), "reference_driver": reference_driver,
            "targets": sorted(targets), "volts": volts, "temps": temps,
            "reference_volts": asc_volts, "reference_temps": asc_temps,
            "minimum": minimum, "reference_minimum": minimum_set(asc_volts),
            "not_scoreable_reasons": reasons,
            "4d": "NOT_SCOREABLE" if reasons else classify_minimum(targets, minimum)}


def report_4c(result):
    cfg = REGISTRATION
    print(f"Session E 4c scorer | RTX 2060 Super | driver {result['driver']}")
    print("Efficiency = bench_throughput / power_avg_w via analyze_sweep.loadSweep; optima are "
          "scored on the target grid.")
    for run in cfg.runs:
        print(f"{run}: median optimum {result['medians'][run]:g} MHz")
        print("  " + ", ".join(f"{name}={result['optima'][run][name]:g}" for name in cfg.workloads))
    if not result["baseline_matches_registration"]:
        print(f"stock-1's median is {result['medians']['stock-1']:g}, NOT the registered "
              f"{cfg.stock_optimum_mhz} MHz. 4c is scored against the same-session stock suite.")
    print("Stock return stock-1 -> stock-3: worst workload median absolute matched-target "
          f"throughput change {max(result['drift_per_workload_pct'].values()):.3f}% "
          f"(limit {cfg.stock_return_tolerance_pct:.1f}%).")
    for name, passed in result["checks"].items():
        print(f"Check, {name}: {'yes' if passed else 'NO'}")
    for reason in result["not_scoreable_reasons"]:
        print(f"Not scoreable: {reason}")
    print(f"Workloads whose optimum moved: {result['moved_count']} of 12, "
          f"{result['moved_down_count']} of them down.")
    print(f"4c (edit-2 median in {cfg.pass_min_mhz}-{cfg.pass_max_mhz} MHz and below stock-1's): "
          f"{result['4c']}")
    print("Session E does not sample the edited floor end (810 MHz is below the 855 grid start), "
          "so a PASS does not show the edited floor end is sharp. n = 1 chip, one session.")


def report_4d(result):
    print(f"Session E 4d scorer | RTX 2060 Super | driver {result['driver']} "
          f"(ascending reference: {result['reference_driver']})")
    print("target  asc V  asc C | desc V  desc C")
    for target in result["targets"]:
        print(f"{target:6d}  {result['reference_volts'][target]['voltage']:.3f}  "
              f"{result['reference_temps'].get(target, float('nan')):5.1f} | "
              f"{result['volts'][target]['voltage']:.3f}  "
              f"{result['temps'].get(target, float('nan')):5.1f}")
    print(f"Minimum set, ascending: {result['reference_minimum']}; descending: {result['minimum']}")
    for reason in result["not_scoreable_reasons"]:
        print(f"Not scoreable: {reason}")
    print(f"4d (minimum stays within 975-1005 MHz): {result['4d']}")
    print("MINIMUM_REACHES_BOTTOM is the thermal outcome under the registered mechanism; "
          "MINIMUM_AT_TOP is what the registered words literally named (see the amendment). "
          "One sweep each way, one chip.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="Directory holding the Session E results")
    parser.add_argument("--4d", dest="four_d", action="store_true",
                        help="score 4d from the descending sweep instead of 4c from the suites")
    args = parser.parse_args(argv)
    if not args.directory.is_dir():
        parser.error(f"not a directory: {args.directory}")
    scorer, reporter, key = ((score_4d, report_4d, "4d") if args.four_d
                             else (score_4c, report_4c, "4c"))
    try:
        result = scorer(args.directory)
    except (ValueError, TypeError, KeyError, OSError, csv.Error, json.JSONDecodeError) as exc:
        print(f"{key} cannot be scored: {exc}", file=sys.stderr)
        return 2
    reporter(result)
    return 0 if result[key] != "NOT_SCOREABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
