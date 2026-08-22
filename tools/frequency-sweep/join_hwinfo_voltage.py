"""
Join HWiNFO core-voltage and crossbar-clock telemetry to a locked-frequency sweep.

WHY THIS EXISTS
    NVML does not expose GPU core voltage - an exhaustive scan of field IDs 1-259 through
    nvmlDeviceGetFieldValues returns 44 readable fields and none is a voltage at any scale (see
    tools/frequency-sweep/probe_nvml_fields.py). HWiNFO does read it, so every voltage statement
    in this project has to come through an HWiNFO log rather than the sweep tool itself.

WHY IT BINS BY CLOCK RATHER THAN JOINING ON TIMESTAMP
    The sweep CSV records durations per point, not absolute timestamps, so a time join would
    have to reconstruct point boundaries from the session start plus accumulated settle and
    measure intervals - fragile, and wrong the moment a point runs long. Binning HWiNFO samples
    by the core clock they were taken at avoids the problem entirely: the sweep locks each
    frequency to a distinct value and holds it for ~28 s, so samples group unambiguously.

    Samples taken while the card was idle between points are discarded by a power threshold.
    Without that filter the ramp-up and ramp-down samples - which sit at boost voltage - pull
    the per-point medians upward and manufacture a voltage-frequency slope that is not there.

WHICH COLUMNS
    HWiNFO on this machine reports TWO GPU sensor blocks. The first (around indices 277-281)
    carries AMD-style names - VDDCR_GFX, SoC Clock, VCN Clock - and does not describe the
    NVIDIA card. Columns are resolved by name within the block that also contains a plausible
    NVIDIA core clock, not by fixed index, so a different machine layout does not silently read
    the wrong sensor.

Usage:
    python join_hwinfo_voltage.py <sweep.csv> <hwinfo.csv> [--min-power W]
"""

import argparse
import csv
import statistics
import sys
from pathlib import Path

IDLE_POWER_WATTS = 30.0
CLOCK_TOLERANCE_MHZ = 25.0


def loadHwinfo(path):
    rows = list(csv.reader(open(path, encoding="latin-1")))
    header = [h.strip() for h in rows[0]]

    def findAll(name):
        return [i for i, h in enumerate(header) if h == name]

    voltageCandidates = findAll("GPU Core Voltage [V]")
    clockCandidates = findAll("GPU Clock [MHz]")
    crossbarCandidates = findAll("GPU Crossbar Clock [MHz]")
    powerCandidates = findAll("GPU Power [W]")

    if not voltageCandidates or not clockCandidates:
        raise SystemExit("Could not find 'GPU Core Voltage [V]' and 'GPU Clock [MHz]' columns.")

    # Pick the block whose clock column actually moves and reaches NVIDIA-like values. The
    # AMD-style phantom block sits at a fixed low clock and would otherwise be chosen by index.
    def spread(index):
        values = []
        for r in rows[1:]:
            if index < len(r):
                try:
                    values.append(float(r[index]))
                except ValueError:
                    pass
        return (max(values) - min(values)) if values else 0.0

    clockIndex = max(clockCandidates, key=spread)
    voltageIndex = min(voltageCandidates, key=lambda i: abs(i - clockIndex))
    crossbarIndex = min(crossbarCandidates, key=lambda i: abs(i - clockIndex)) if crossbarCandidates else None
    powerIndex = min(powerCandidates, key=lambda i: abs(i - clockIndex)) if powerCandidates else None

    samples = []
    for r in rows[1:]:
        needed = [clockIndex, voltageIndex]
        if max(needed) >= len(r):
            continue
        try:
            clock = float(r[clockIndex])
            voltage = float(r[voltageIndex])
            crossbar = float(r[crossbarIndex]) if crossbarIndex is not None and crossbarIndex < len(r) else None
            power = float(r[powerIndex]) if powerIndex is not None and powerIndex < len(r) else None
        except ValueError:
            continue
        samples.append({"clock": clock, "voltage": voltage, "crossbar": crossbar, "power": power})

    return samples, {"clock": clockIndex, "voltage": voltageIndex,
                     "crossbar": crossbarIndex, "power": powerIndex}


def loadSweep(path):
    rows = list(csv.reader(open(path, encoding="utf-8-sig")))
    header = rows[0]
    out = []
    for r in rows[1:]:
        if not r:
            continue
        d = dict(zip(header, r))
        out.append({
            "target": int(float(d["target_frequency_mhz"])),
            "achieved": float(d["achieved_frequency_avg"]),
            "throughputGbs": float(d["bench_throughput"]) / 1e9,
            "powerW": float(d["power_avg_w"]),
            "memoryMhz": float(d.get("memory_clock_avg_mhz", "nan")),
        })
    return out


def filterIdle(samples, minPower):
    """Drop samples taken while the card was idle between sweep points.

    This is the single most consequential line in the file. HWiNFO polls straight through the
    settle gaps, and an idle card sits at BOOST voltage, not at the voltage the locked point was
    running at. Keeping those samples pulls the per-point medians upward by an amount that grows
    with how long the gaps are - which manufactures a voltage-frequency slope out of nothing.
    Since "stock has a voltage slope and the tuned curve does not" IS the project's mechanism
    result, a defect here does not perturb a number, it invents the finding.

    A sample with no power reading at all is KEPT rather than dropped. An absent power column
    means the log never carried one, so there is nothing to filter on, and discarding every
    sample would silently produce an empty join instead of an obvious error.
    """
    return [s for s in samples if s["power"] is None or s["power"] >= minPower]


def matchSamples(samples, achievedMhz, toleranceMhz=CLOCK_TOLERANCE_MHZ):
    """Bin samples to a sweep point by the core clock they were taken at.

    The sweep CSV has no absolute timestamps, so the clock itself is the join key - see the
    module docstring. The tolerance has to be wide enough to absorb the reported clock jitter
    within one held point and narrow enough not to reach the neighbouring point; the grid steps
    are ~75 MHz apart at the low end, so 25 MHz leaves margin on both sides.
    """
    return [s for s in samples if abs(s["clock"] - achievedMhz) <= toleranceMhz]


def summarisePoint(matched, achievedMhz):
    """Median voltage and crossbar clock for one point, plus the crossbar-to-core ratio.

    Median rather than mean because a single sample landing in a ramp is a large outlier and
    there are only 5-7 samples per point. Crossbar is nan rather than 0.0 when the column is
    absent: the ratio is quoted in the paper, and a fabricated 0.0 would read as a stalled
    interconnect - which is exactly the effect being argued about.
    """
    voltage = statistics.median(s["voltage"] for s in matched)
    crossbars = [s["crossbar"] for s in matched if s["crossbar"] is not None]
    crossbar = statistics.median(crossbars) if crossbars else float("nan")
    ratio = crossbar / achievedMhz if crossbars else float("nan")
    return voltage, crossbar, ratio


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("sweep")
    parser.add_argument("hwinfo")
    parser.add_argument("--min-power", type=float, default=IDLE_POWER_WATTS,
                        help="Discard HWiNFO samples below this GPU power; they are the idle "
                             "gaps between sweep points and sit at boost voltage.")
    args = parser.parse_args()

    samples, indices = loadHwinfo(args.hwinfo)
    sweep = loadSweep(args.sweep)
    print(f"HWiNFO columns used: {indices}")
    print(f"{len(samples)} samples, {len(sweep)} sweep points\n")

    loaded = filterIdle(samples, args.min_power)
    print(f"{len(loaded)} of {len(samples)} samples are above {args.min_power} W and kept\n")

    print(f"{'target':>7} {'achieved':>9} {'GB/s':>8} {'W':>6} {'n':>4} "
          f"{'volts':>7} {'crossbar':>9} {'xbar/core':>10}")
    merged = []
    for point in sweep:
        matched = matchSamples(loaded, point["achieved"])
        if not matched:
            print(f"{point['target']:>7} {point['achieved']:>9.1f} "
                  f"{point['throughputGbs']:>8.1f} {point['powerW']:>6.1f} {0:>4}  (no samples)")
            continue
        voltage, crossbar, ratio = summarisePoint(matched, point["achieved"])
        print(f"{point['target']:>7} {point['achieved']:>9.1f} {point['throughputGbs']:>8.1f} "
              f"{point['powerW']:>6.1f} {len(matched):>4} {voltage:>7.3f} {crossbar:>9.1f} {ratio:>10.3f}")
        merged.append({**point, "voltage": voltage, "crossbar": crossbar,
                       "sampleCount": len(matched)})

    if len(merged) >= 2:
        voltages = [m["voltage"] for m in merged]
        crossbars = [m["crossbar"] for m in merged]
        print(f"\nvoltage across the swept range : {min(voltages):.3f} - {max(voltages):.3f} V "
              f"(spread {max(voltages) - min(voltages):.3f} V)")
        print(f"crossbar across the swept range: {min(crossbars):.0f} - {max(crossbars):.0f} MHz "
              f"(spread {max(crossbars) - min(crossbars):.0f} MHz)")
        coreSpread = merged[-1]["achieved"] - merged[0]["achieved"]
        print(f"core clock rose {coreSpread:.0f} MHz "
              f"({coreSpread / merged[0]['achieved']:.1%}) over the same range")

    outPath = Path(args.sweep).with_suffix("").as_posix() + "_voltage.csv"
    with open(outPath, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(merged[0].keys()) if merged else ["target"])
        writer.writeheader()
        writer.writerows(merged)
    print(f"\nwrote {outPath}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
