"""
Tests for predict_from_curve.py.

WHAT THESE ARE FOR
    The module makes a claim that is easy to state and easy to get quietly wrong: the efficiency
    optimum is the grid point nearest where the V/F curve leaves the 0.720 V load floor. Every
    step between "curve" and "grid point" is arithmetic that would produce a plausible answer if
    it were broken - an interpolation that reads the wrong side of a bracket, a nearest-target
    search that rounds the wrong way, a regret formula that divides by the wrong number.

    So these assert VALUES, not shapes. `isinstance(x, float)` catches nothing here.

    Most cases are synthetic and run in milliseconds. A handful at the end touch the real
    committed data, because the constants that make the module mean anything - the four floor
    extents - live in a snapshot file and would go stale silently if nothing read them.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from predict_from_curve import (  # noqa: E402
    CONFIGURATION_PROFILE,
    FLOOR_VOLTAGE_MV,
    chooseByBestFixedFrequency,
    chooseByBestPerConfiguration,
    chooseByMechanism,
    chooseByOracle,
    clockAtVoltage,
    decodeCurve,
    evaluateStrategy,
    floorExtentMhz,
    nearestTarget,
    regretByWorkload,
    regretFor,
    sweepPath,
)

failures = []


def check(description, condition, detail=""):
    # The [PASS] / [FAIL] markers are load-bearing, not decoration: run_tests.py counts literal
    # occurrences of them to get a suite's assertion count, and treats a suite reporting ZERO
    # assertions as a failure even when it exits 0. A prettier format here reads as "exited
    # cleanly but asserted nothing", which is how a gutted suite is meant to be caught.
    if condition:
        print(f"[PASS] {description}")
    else:
        print(f"[FAIL] {description}")
        if detail:
            print(f"  Detail: {detail}")
        failures.append(description)


print("clockAtVoltage")
# A deliberately non-uniform curve, so a linear-interpolation bug cannot hide behind even spacing.
CURVE = [(700.0, 1400.0), (800.0, 1900.0), (1000.0, 2100.0)]
check("exact point returns its own clock", clockAtVoltage(CURVE, 800.0) == 1900.0,
      f"got {clockAtVoltage(CURVE, 800.0)}")
check("midpoint interpolates linearly", clockAtVoltage(CURVE, 750.0) == 1650.0,
      f"got {clockAtVoltage(CURVE, 750.0)}")
check("interpolates on the second, differently-sloped segment",
      clockAtVoltage(CURVE, 900.0) == 2000.0, f"got {clockAtVoltage(CURVE, 900.0)}")
check("20% along the first segment", abs(clockAtVoltage(CURVE, 720.0) - 1500.0) < 1e-9,
      f"got {clockAtVoltage(CURVE, 720.0)}")
check("below the curve clamps to the lowest point", clockAtVoltage(CURVE, 500.0) == 1400.0,
      f"got {clockAtVoltage(CURVE, 500.0)}")
check("above the curve clamps to the highest point", clockAtVoltage(CURVE, 1200.0) == 2100.0,
      f"got {clockAtVoltage(CURVE, 1200.0)}")
# A flat segment is exactly what a plateau is, and a naive slope calculation divides by zero here.
FLAT = [(900.0, 3000.0), (900.0, 3000.0), (1000.0, 3000.0)]
check("a flat/duplicated segment does not divide by zero", clockAtVoltage(FLAT, 900.0) == 3000.0)

print("\nnearestTarget")
GRID = [1237, 1395, 1545, 1702, 1852, 2010]
check("picks the closest target below", nearestTarget(GRID, 1530) == 1545,
      f"got {nearestTarget(GRID, 1530)}")
check("picks the closest target above", nearestTarget(GRID, 2002) == 2010,
      f"got {nearestTarget(GRID, 2002)}")
check("exact grid value returns itself", nearestTarget(GRID, 1702) == 1702)
check("a tie resolves to the LOWER target", nearestTarget([1000, 2000], 1500) == 1000,
      f"got {nearestTarget([1000, 2000], 1500)}")
check("unsorted input still works", nearestTarget([2010, 1237, 1545], 1500) == 1545,
      f"got {nearestTarget([2010, 1237, 1545], 1545)}")

print("\nregretFor")
# Peak 100 at 1545. Regret is RELATIVE to the sweep's own peak, so these are exact percentages.
SWEEP = {1237: 90.0, 1395: 95.0, 1545: 100.0, 1702: 80.0}
check("regret at the optimum is exactly zero", regretFor(SWEEP, 1545) == 0.0,
      f"got {regretFor(SWEEP, 1545)}")
check("regret is relative to the peak, not absolute", abs(regretFor(SWEEP, 1395) - 5.0) < 1e-9,
      f"got {regretFor(SWEEP, 1395)}")
check("regret at the worst point", abs(regretFor(SWEEP, 1702) - 20.0) < 1e-9,
      f"got {regretFor(SWEEP, 1702)}")
# The scale-invariance is the point of dividing by the peak: two sweeps at wildly different
# absolute efficiency must contribute comparably. Multiply every value by 7 and nothing moves.
SCALED = {k: v * 7.0 for k, v in SWEEP.items()}
check("regret is invariant to overall scale",
      abs(regretFor(SCALED, 1395) - regretFor(SWEEP, 1395)) < 1e-9)

print("\nevaluateStrategy and the baselines")
# Two configurations whose optima genuinely differ, so a per-config strategy can beat a single
# constant and the test can tell them apart.
CURVES = [
    ("low", "w1", {1237: 90.0, 1545: 100.0, 2010: 70.0}),
    ("low", "w2", {1237: 95.0, 1545: 100.0, 2010: 60.0}),
    ("high", "w3", {1237: 60.0, 1545: 80.0, 2010: 100.0}),
    ("high", "w4", {1237: 50.0, 1545: 70.0, 2010: 100.0}),
]
oracleScore = evaluateStrategy(CURVES, chooseByOracle())
check("oracle scores zero mean regret", oracleScore["mean_regret_pct"] == 0.0,
      f"got {oracleScore['mean_regret_pct']}")
check("oracle matches exactly every time", oracleScore["exact_match_rate"] == 1.0)
check("evaluateStrategy counts every sweep", oracleScore["n"] == 4, f"got {oracleScore['n']}")

fixedChooser, fixedPick = chooseByBestFixedFrequency(CURVES)
check("best single constant picks 1545 here", fixedPick == 1545, f"got {fixedPick}")
fixedScore = evaluateStrategy(CURVES, fixedChooser)
# 1545 costs 0 + 0 + 20 + 30 over the four sweeps -> mean 12.5
check("best single constant scores its true mean regret",
      abs(fixedScore["mean_regret_pct"] - 12.5) < 1e-9, f"got {fixedScore['mean_regret_pct']}")

perConfigChooser, perConfigPicks = chooseByBestPerConfiguration(CURVES)
check("per-config picks 1545 for the low group", perConfigPicks["low"] == 1545,
      f"got {perConfigPicks['low']}")
check("per-config picks 2010 for the high group", perConfigPicks["high"] == 2010,
      f"got {perConfigPicks['high']}")
perConfigScore = evaluateStrategy(CURVES, perConfigChooser)
check("per-config reaches zero regret on this synthetic set",
      perConfigScore["mean_regret_pct"] == 0.0, f"got {perConfigScore['mean_regret_pct']}")
check("per-config beats the single constant here",
      perConfigScore["mean_regret_pct"] < fixedScore["mean_regret_pct"])

print("\nregretByWorkload")
rows = regretByWorkload(CURVES, fixedChooser)
check("returns one row per workload", len(rows) == 4, f"got {len(rows)}")
check("worst workload is listed first", rows[0][0] == "w4", f"got {rows[0][0]}")
check("worst workload's mean regret is its true value", abs(rows[0][1] - 30.0) < 1e-9,
      f"got {rows[0][1]}")

print("\ndecodeCurve against the committed snapshot")
stockCurve = decodeCurve(CONFIGURATION_PROFILE["stock"])
check("stock decodes to a non-empty curve", len(stockCurve) > 50, f"got {len(stockCurve)}")
check("the >3090 MHz decoder artifact is filtered out",
      max(clock for _, clock in stockCurve) <= 3090.0,
      f"max {max(clock for _, clock in stockCurve)}")
check("curve is returned sorted by voltage",
      all(stockCurve[i][0] <= stockCurve[i + 1][0] for i in range(len(stockCurve) - 1)))

print("\nfloorExtentMhz - the four configurations")
# These are the numbers the whole module rests on. If a snapshot is replaced or the decode
# changes, these fail loudly rather than the predictor quietly picking a different frequency.
extents = {name: floorExtentMhz(name) for name in CONFIGURATION_PROFILE}
check("the load floor constant is 720 mV", FLOOR_VOLTAGE_MV == 720.0)
check("stock leaves the floor near 1530 MHz", abs(extents["stock"] - 1530.0) < 15.0,
      f"got {extents['stock']:.1f}")
check("the split curve leaves the floor near 1530 MHz", abs(extents["split"] - 1530.0) < 15.0,
      f"got {extents['split']:.1f}")
check("the repair curve leaves the floor near 1530 MHz", abs(extents["repair"] - 1530.0) < 15.0,
      f"got {extents['repair']:.1f}")
check("the full tune leaves the floor near 2002 MHz", abs(extents["fulltune"] - 2002.0) < 15.0,
      f"got {extents['fulltune']:.1f}")
check("stock, split and repair share a floor extent to within a megahertz",
      max(extents["stock"], extents["split"], extents["repair"])
      - min(extents["stock"], extents["split"], extents["repair"]) < 1.0)
check("the full tune's extent is ~465 MHz above the others",
      440.0 < extents["fulltune"] - extents["stock"] < 490.0,
      f"got {extents['fulltune'] - extents['stock']:.1f}")

print("\nsweepPath refuses ambiguity rather than guessing")
try:
    sweepPath("stock-bracket-20260909", "gemm", "r9")
    resolved = True
except ValueError:
    resolved = False
check("resolves a real sweep", resolved)
try:
    sweepPath("stock-bracket-20260909", "gemm", "no-such-tag")
    raised = False
except ValueError:
    raised = True
check("raises when nothing matches, rather than returning None", raised)
# The r2 directory holds bgemm64 sweeps tagged -r3 and -r4 from a separate early set. A glob for
# tag "r" would match several; the module must refuse rather than silently take the first.
try:
    sweepPath("suite-replicate-r2-20260830", "bgemm64", "r*")
    raisedOnMultiple = False
except ValueError:
    raisedOnMultiple = True
check("raises when several sweeps match, rather than taking the first", raisedOnMultiple)

print("\nchooseByMechanism reads the curve rather than a hardcoded table")
# Real configuration names with synthetic efficiency curves. The predictor only needs the name to
# look up the applied profile; the curves supply the grid it snaps to. This is what proves the
# picks are DERIVED - swap the snapshot and they move.
REAL = [(name, "w1", {1237: 1.0, 1545: 2.0, 2010: 1.5}) for name in CONFIGURATION_PROFILE]
mechChooser, mechPicks = chooseByMechanism(REAL)
check("returns a pick for every configuration present",
      set(mechPicks) == set(CONFIGURATION_PROFILE), f"got {set(mechPicks)}")
check("stock snaps to the 1545 grid point", mechPicks["stock"] == 1545,
      f"got {mechPicks['stock']}")
check("the full tune snaps to the 2010 grid point", mechPicks["fulltune"] == 2010,
      f"got {mechPicks['fulltune']}")
check("the pick ignores the workload it is given",
      mechChooser("stock", "anything", REAL[0][2]) == mechPicks["stock"])
# The predictor's input is the applied curve. Asked about a configuration whose curve is unknown
# it must say so, not raise a bare KeyError from three frames down.
try:
    floorExtentMhz("not-a-configuration")
    explained = False
except ValueError as error:
    explained = "not-a-configuration" in str(error)
except KeyError:
    explained = False
check("an unknown configuration raises a ValueError naming it", explained)

if failures:
    print(f"\n{len(failures)} CHECK(S) FAILED")
    raise SystemExit(1)
print("\nALL CHECKS PASSED")
