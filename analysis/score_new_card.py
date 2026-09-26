"""Score a new card collected with the generic stock protocol (REGISTERED-PREDICTIONS 11).

Usage: python analysis/score_new_card.py PATH_TO_THE_CARD'S_RESULTS

Written 2026-09-25, before any card is known. The directory holds one card's Headroom Bench output:
the two dense floor sweeps (newcard-dense-asc, newcard-dense-desc) and the twelve suite sweeps
(newcard-suite-<workload>), each with its JSON and a separate HWiNFO _sweep_voltage.csv extract.
This script only reads them.
"""

import argparse
import csv
import json
import statistics
import sys
from pathlib import Path

from analyze_sweep import efficiencyPeak, loadSweep
from score_session_d import read_voltage

WORKLOADS = ("copy", "reduce", "softmax", "layernorm", "bgemm32", "bgemm64", "bgemm128",
             "bgemm256", "bgemm1024", "attention", "conv", "gemm")
TIE_V = 0.003  # under half of one 6.25 mV code
# 11c: this project's 16 GB RTX 5060 Ti. Floor 0.720 V, end 1567-1575 MHz (5060ti-finefloor-20260922).
REFERENCE_5060TI = {"floor_v": 0.720, "floor_end_mhz": 1571}


def median(values):
    return statistics.median(values)


def classify_floor(volts):
    """volts: {target: voltage}. Returns (classification, floor end or None, floor voltage)."""
    targets = sorted(volts)
    lowest = min(volts.values())
    floor = [t for t in targets if volts[t] <= lowest + TIE_V]
    positions = [targets.index(t) for t in floor]
    contiguous = positions == list(range(positions[0], positions[-1] + 1))
    if not contiguous or floor[0] != targets[0]:
        return "NON_MONOTONIC", None, lowest
    if len(floor) < 2 or floor[-1] == targets[-1]:
        return "NOT_LOCATED", None, lowest
    return "FLAT_FLOOR", floor[-1], lowest


def median_spacing(targets):
    ordered = sorted(targets)
    return median(b - a for a, b in zip(ordered, ordered[1:]))


def read_metadata(json_path):
    if not json_path.is_file():
        raise ValueError(f"missing companion file: {json_path}")
    with json_path.open(encoding="utf-8-sig") as handle:
        return json.load(handle)


def check_stock(metadata, path):
    if "power_limit_enforced_w" not in metadata or "power_limit_default_w" not in metadata:
        raise ValueError(f"{path}: power limits not recorded")
    if float(metadata["power_limit_enforced_w"]) != float(metadata["power_limit_default_w"]):
        raise ValueError(f"{path}: power limit is not the card default, so this is not stock")


def find_one(directory, label):
    found = [p for p in directory.rglob("*_sweep.csv") if p.stem.endswith(label + "_sweep")]
    if len(found) != 1:
        raise ValueError(f"expected one {label} sweep, found {len(found)}")
    return found[0]


def read_dense(csv_path, expected_order):
    metadata = read_metadata(csv_path.with_suffix(".json"))
    check_stock(metadata, csv_path)
    if metadata.get("sweep_order", "ascending") != expected_order:
        raise ValueError(f"{csv_path}: sweep_order is {metadata.get('sweep_order')!r}, "
                         f"not {expected_order!r}")
    with csv_path.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    targets = [int(float(row["target_frequency_mhz"])) for row in rows]
    temps = {int(float(row["target_frequency_mhz"])): float(row["temperature_avg_c"]) for row in rows}
    volts = read_voltage(csv_path.with_name(csv_path.stem + "_voltage.csv"), targets)
    return metadata, {t: volts[t]["voltage"] for t in targets}, temps


def read_suite(directory):
    suite = {}
    for path in directory.rglob("*_sweep.csv"):
        if "newcard-suite-" not in path.stem:
            continue
        workload = path.stem.split("newcard-suite-", 1)[1].removesuffix("_sweep")
        if workload not in WORKLOADS or workload in suite:
            raise ValueError(f"{path}: unknown or duplicate suite workload {workload!r}")
        metadata = read_metadata(path.with_suffix(".json"))
        check_stock(metadata, path)
        rows = loadSweep(path)
        if len(rows) != 13 or not all(row["windowed"] for row in rows):
            raise ValueError(f"{path}: expected 13 windowed points")
        suite[workload] = {"metadata": metadata, "rows": rows, "best": efficiencyPeak(rows)}
    missing = set(WORKLOADS) - set(suite)
    if missing:
        raise ValueError(f"suite is missing: {', '.join(sorted(missing))}")
    grids = {tuple(sorted(row["target"] for row in item["rows"])) for item in suite.values()}
    if len(grids) != 1:
        raise ValueError("suite workloads were swept on different grids")
    return suite, list(next(iter(grids)))


def regret_at(suite, grid_point):
    """Per workload, the efficiency given up by running at grid_point instead of its own best."""
    regrets = {}
    for name, item in suite.items():
        at = {row["target"]: row["efficiency"] for row in item["rows"]}[grid_point]
        regrets[name] = 100 * (1 - at / item["best"]["efficiency"])
    return regrets


def score(directory):
    asc_meta, asc_volts, asc_temps = read_dense(find_one(directory, "newcard-dense-asc"), "ascending")
    desc_meta, desc_volts, desc_temps = read_dense(find_one(directory, "newcard-dense-desc"), "descending")
    suite, grid = read_suite(directory)
    metas = [asc_meta, desc_meta] + [item["metadata"] for item in suite.values()]
    names = {m.get("gpu_name", "") for m in metas}
    drivers = {m.get("driver_version", "") for m in metas}
    if len(names) != 1 or len(drivers) != 1 or not next(iter(names)) or not next(iter(drivers)):
        raise ValueError(f"files come from more than one card or driver: {names} {drivers}")

    asc = classify_floor(asc_volts)
    desc = classify_floor(desc_volts)
    step = max(median_spacing(asc_volts), median_spacing(desc_volts))
    if asc[0] == "FLAT_FLOOR" and desc[0] == "FLAT_FLOOR":
        direction = "AGREE" if abs(asc[1] - desc[1]) <= step else "DIFFER"
    else:
        direction = "NOT_SCORED"

    optima = {name: item["best"]["target"] for name, item in suite.items()}
    m = median(optima.values())
    g = median_spacing(grid)
    floor_end = None
    regrets = None
    reasons = []
    if "NON_MONOTONIC" in (asc[0], desc[0]):
        rule = "UNDECIDABLE"
    elif "NOT_LOCATED" in (asc[0], desc[0]):
        rule = "NOT_SCOREABLE"
        reasons.append("the floor end lies outside the dense sweep's 40-80% range")
    elif direction != "AGREE":
        rule = "NOT_SCOREABLE"
        reasons.append(f"ascending and descending floor ends differ ({asc[1]} and {desc[1]} MHz)")
    else:
        floor_end = (asc[1] + desc[1]) / 2
        if abs(m - floor_end) <= g / 2:
            rule = "PASS"
        elif m < floor_end:
            rule = "FAIL_BELOW"
        else:
            rule = "FAIL_ABOVE"
    if floor_end is not None:
        nearest = min(grid, key=lambda t: abs(t - floor_end))
        regrets = regret_at(suite, nearest)

    gpu = next(iter(names))
    comparison = None
    if "5060 Ti" in gpu:
        borrowed = min(grid, key=lambda t: abs(t - REFERENCE_5060TI["floor_end_mhz"]))
        comparison = {"floor_v": (asc[2], desc[2]), "floor_end": (asc[1], desc[1]),
                      "borrowed_grid_point": borrowed, "borrowed_error_mhz": m - borrowed}
    return {"gpu": gpu, "driver": next(iter(drivers)), "asc": asc, "desc": desc,
            "asc_volts": asc_volts, "desc_volts": desc_volts, "asc_temps": asc_temps,
            "desc_temps": desc_temps, "dense_step": step, "direction": direction,
            "optima": optima, "median": m, "grid_step": g, "floor_end": floor_end,
            "regrets": regrets, "not_scoreable_reasons": reasons, "rule": rule,
            "comparison": comparison}


def report(result):
    print(f"New-card scorer (REGISTERED-PREDICTIONS 11) | {result['gpu']} | driver {result['driver']}")
    for label, key in (("ascending", "asc"), ("descending", "desc")):
        kind, end, volts = result[key]
        print(f"Dense {label}: {kind}; floor {volts:.3f} V; floor end {end if end else '-'} MHz")
    print(f"11b direction (floor ends within one dense step, {result['dense_step']:g} MHz): "
          f"{result['direction']}")
    print("Suite optima: " + ", ".join(f"{n}={result['optima'][n]:g}" for n in WORKLOADS))
    print(f"Median suite optimum {result['median']:g} MHz; suite grid step {result['grid_step']:g} MHz.")
    if result["floor_end"] is not None:
        print(f"Floor end F = {result['floor_end']:g} MHz; pass window +/- {result['grid_step'] / 2:g} MHz.")
    for reason in result["not_scoreable_reasons"]:
        print(f"Not scoreable: {reason}")
    print(f"11a rule (median optimum within half a grid step of the floor end): {result['rule']}")
    if result["regrets"] is not None:
        values = list(result["regrets"].values())
        print(f"Regret at the suite grid point nearest F: mean {statistics.mean(values):.3f}%, "
              f"worst {max(values):.3f}% ({max(result['regrets'], key=result['regrets'].get)}).")
    if result["comparison"]:
        c = result["comparison"]
        print(f"11c (descriptive): floor {c['floor_v'][0]:.3f}/{c['floor_v'][1]:.3f} V against the "
              f"16 GB unit's {REFERENCE_5060TI['floor_v']:.3f} V; floor end {c['floor_end']} against "
              f"1567-1575 MHz; borrowing 1571 MHz predicts {c['borrowed_grid_point']} MHz, "
              f"{c['borrowed_error_mhz']:+g} MHz from this card's median optimum.")
    print("n = 1 card; twelve workloads are repeated outcomes on it. Stock rests on the default "
          "power limit and a fresh shop build.")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    if not args.directory.is_dir():
        parser.error(f"not a directory: {args.directory}")
    try:
        result = score(args.directory)
    except (ValueError, TypeError, KeyError, OSError, csv.Error, json.JSONDecodeError) as exc:
        print(f"The new card cannot be scored: {exc}", file=sys.stderr)
        return 2
    report(result)
    return 0 if result["rule"] != "NOT_SCOREABLE" else 2


if __name__ == "__main__":
    raise SystemExit(main())
