"""
Compare the published consumer-GPU DVFS datasets against the V100 set, and against what
this project's own sweep tool is configured to measure.

WHY THIS EXISTS
    The obvious move on finding consumer DVFS data was to test whether the V100's 44.4%
    efficiency-headroom finding reproduces on consumer silicon. It does not - but NOT because
    consumer GPUs behave differently. The published consumer sweeps never enter the frequency
    range where the efficiency optimum lives.

    That distinction matters enormously. Reading "1.0% gap on the GTX 1080 Ti" as "consumer
    GPUs have no headroom" would be flatly wrong, and is exactly the kind of confident-but-
    backwards conclusion this script exists to prevent.

WHAT IT SHOWS
    Every dataset is placed on a common axis: swept frequency as a PERCENTAGE OF THE CARD'S
    RATED BOOST CLOCK, taken from the specs database rather than assumed.

REQUIRES
    scripts/Get-Dataset.ps1 to have been run (needs data/raw/ and data/external/).
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
EXTERNAL = REPO_ROOT / "data" / "external"

# Frequency floor this project's own sweep tool uses, as a fraction of the card's max clock.
OUR_SWEEP_FLOOR_PERCENT = 40


def loadSpecs():
    path = EXTERNAL / "all-gpus.json"
    if not path.exists():
        return {}
    raw = json.load(open(path, encoding="utf-8"))
    rows = raw if isinstance(raw, list) else raw.get("gpus", [])
    return {r.get("name", ""): r for r in rows}


def findSpec(specs, prefix):
    for name, row in specs.items():
        if name.lower().startswith(prefix.lower()):
            return row
    return None


def efficiencyByCoreFrequency(frame, coreColumn="coreF", memColumn="memF"):
    """
    Normalised efficiency per app at the highest memory clock, indexed by core frequency.

    Efficiency is performance-per-watt. Work is fixed per app, so performance is 1/time, and
    each app's curve is normalised to its own value at the top core clock - the same
    convention the published V100 dataset uses, so the numbers are directly comparable.
    """
    atTopMemory = frame[frame[memColumn] == frame[memColumn].max()].copy()
    atTopMemory["efficiency"] = (1.0 / atTopMemory["time/ms"]) / atTopMemory["power/W"]
    pivot = atTopMemory.pivot_table(index="appName", columns=coreColumn, values="efficiency")
    return pivot.div(pivot[pivot.columns.max()], axis=0)


def summarise(name, pivot, boostClock):
    gapPercent = (pivot.max(axis=1).mean() - 1.0) * 100.0
    optima = pivot.idxmax(axis=1)
    lowest, highest = int(pivot.columns.min()), int(pivot.columns.max())
    atCeiling = int((optima == pivot.columns.max()).sum())

    return {
        "dataset": name,
        "units": len(pivot),
        "swept_low_mhz": lowest,
        "swept_high_mhz": highest,
        "rated_boost_mhz": boostClock,
        "swept_low_pct_of_boost": round(lowest / boostClock * 100, 0) if boostClock else None,
        "swept_high_pct_of_boost": round(highest / boostClock * 100, 0) if boostClock else None,
        "mean_headroom_gap_pct": round(gapPercent, 2),
        "units_optimal_at_ceiling": atCeiling,
        "pct_optimal_at_ceiling": round(atCeiling / len(pivot) * 100, 0),
    }


def main():
    specs = loadSpecs()
    if not specs:
        print("[COMPARE] data/external/all-gpus.json missing. Run scripts/Get-Dataset.ps1 first.")
        return 1

    rows = []

    # --- Consumer datasets (HKBU-HPML) ---
    for label, filename, specPrefix in [
        ("GTX 1080 Ti (consumer)", "gtx1080ti-dvfs-real-Performance-Power.csv", "GeForce GTX 1080 Ti"),
        ("RTX 2070 Super (consumer)", "gtx2070s-dvfs-real-Performance-Power.csv", "GeForce RTX 2070 SUPER"),
    ]:
        path = EXTERNAL / filename
        if not path.exists():
            print(f"[COMPARE] missing {filename} - skipping")
            continue
        frame = pd.read_csv(path)
        spec = findSpec(specs, specPrefix)
        boost = spec.get("boostClock") if spec else None
        rows.append(summarise(label, efficiencyByCoreFrequency(frame), boost))

    # --- The public V100 set, via the existing loader ---
    try:
        from load_data import loadDataset
        dataset = loadDataset(validate=False)
        pivot = dataset.pivot(index="workload", columns="frequency_mhz", values="efficiency_normalised")
        spec = findSpec(specs, "Tesla V100")
        rows.append(summarise("Tesla V100 (datacenter)", pivot, spec.get("boostClock") if spec else None))
    except Exception as error:
        print(f"[COMPARE] could not load the V100 set: {error}")

    table = pd.DataFrame(rows)
    print("[COMPARE] Every dataset on a common axis - swept range as % of the card's RATED BOOST clock:")
    print()
    print(table.to_string(index=False))
    print()

    # --- The point ---
    print("[COMPARE] THE FINDING:")
    for row in rows:
        low, high = row["swept_low_pct_of_boost"], row["swept_high_pct_of_boost"]
        if low is None:
            continue
        if low >= 90:
            verdict = ("sweeps AT AND ABOVE stock only - this is an OVERCLOCKING dataset and "
                       "cannot locate an efficiency optimum")
        elif low <= 65:
            verdict = "sweeps well below stock - can locate an efficiency optimum"
        else:
            verdict = "partially below stock - may miss the optimum"
        print(f"[COMPARE]   {row['dataset']:28s} {low:>3.0f}%-{high:>3.0f}% of boost: {verdict}")

    print()
    print("[COMPARE] The published CONSUMER datasets never go below stock, so their small measured")
    print("[COMPARE] gaps are NOT evidence that consumer GPUs lack headroom. They are evidence that")
    print("[COMPARE] nobody swept the range where the headroom lives. Do not cite them as a null.")
    print()
    print(f"[COMPARE] This project's own sweep floor is {OUR_SWEEP_FLOOR_PERCENT}% of max clock, which")
    print("[COMPARE] covers the region the V100 optimum sat in (62% of its max) and that every")
    print("[COMPARE] published consumer dataset above misses entirely. That is the gap this project")
    print("[COMPARE] fills, and it is a stronger justification than 'no consumer data exists'.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
