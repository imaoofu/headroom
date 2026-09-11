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

print("\nhow the store encodes the plateau - and where the artifact actually is")
# ADDED 2026-09-11, after screenshots of the Profile 4 and Profile 5 curve editors were checked
# against this decode. The >3090 filter above is correct, but the reason recorded for it in three
# documents was NOT: they said a "naive stride-3 read mispairs at the zero-offset boundary".
#
# The flat top is encoded with a SENTINEL - one constant out-of-range base repeated across every
# point of the plateau, plus one constant large negative offset that lands the sum exactly on the
# plateau clock. Fifty identical records is a design, not a pairing slip: a stride error corrupts a
# boundary, not fifty consecutive triples. Pinned here so the old explanation cannot drift back.
import json  # noqa: E402

from predict_from_curve import PROFILE_SNAPSHOT  # noqa: E402

snapshot = json.loads(Path(PROFILE_SNAPSHOT).read_text(encoding="utf-8"))["profiles"]

for profileName in ("Profile1", "Profile4", "Profile5"):
    points = snapshot[profileName]["curve_points"]
    sentinel = [q for q in points if q["base_mhz"] > 3090.0]
    bases = {q["base_mhz"] for q in sentinel}
    offsets = {q["offset_mhz"] for q in sentinel}
    impossible = [q for q in points if q["applied_mhz"] > 3090.0]
    zeroOffset = [q["voltage_mv"] for q in points if q["offset_mhz"] == 0.0]

    check(profileName + ": the plateau is a block of sentinel records, not one bad point",
          len(sentinel) == 50, "got %d" % len(sentinel))
    check(profileName + ": every sentinel record carries the SAME out-of-range base",
          len(bases) == 1, "got %s" % sorted(bases))
    check(profileName + ": all but one sentinel record shares one negative offset",
          len(offsets) == 2 and sum(1 for q in sentinel if q["offset_mhz"] < 0) == 49,
          "got %s" % sorted(offsets))
    check(profileName + ": exactly one point decodes above the 3090 MHz ceiling",
          len(impossible) == 1, "got %s" % [q["applied_mhz"] for q in impossible])
    check(profileName + ": that point is at 935 mV, the FIRST record of the sentinel block",
          impossible[0]["voltage_mv"] == 935.0 == min(q["voltage_mv"] for q in sentinel),
          "got %s" % impossible[0]["voltage_mv"])
    # The refutation, asserted rather than left in prose: Profile 4 carries no zero-offset point
    # anywhere above 695 mV, so its 935 mV artifact cannot sit on a zero-offset boundary.
    check(profileName + ": the artifact is nowhere near a zero-offset boundary",
          max(zeroOffset) < 900.0 and impossible[0]["voltage_mv"] - max(zeroOffset) > 80.0,
          "zero-offset region ends at %s mV" % max(zeroOffset))

# Stock is the control: no sentinel, no artifact, and the five points it loses to the filter are
# REAL - its curve genuinely exceeds the 3090 lock-target ceiling above 1215 mV. CLAUDE.md quotes
# "122 curve points" for stock; this is what makes that 122 rather than 127.
stockPoints = snapshot[CONFIGURATION_PROFILE["stock"]]["curve_points"]
stockDecoded = decodeCurve(CONFIGURATION_PROFILE["stock"])
check("stock carries no sentinel encoding at all",
      all(q["base_mhz"] <= 3135.0 for q in stockPoints))
check("every stock per-point offset is zero",
      {q["offset_mhz"] for q in stockPoints} == {0.0},
      "got %s" % sorted({q["offset_mhz"] for q in stockPoints}))
check("stock loses exactly five REAL points to the >3090 filter, not an artifact",
      len(stockPoints) - len(stockDecoded) == 5,
      "got %d" % (len(stockPoints) - len(stockDecoded)))
check("stock's decoded point count is the 122 CLAUDE.md quotes",
      len(stockDecoded) == 122, "got %d" % len(stockDecoded))

# What the two curve-editor screenshots show directly: Profile 5 leaves the floor region untouched
# and Profile 4 lifts the whole of it. This is the manipulation arm of the mechanism test, readable
# off the store with no benchmark at all.
p4Points = {q["voltage_mv"]: q for q in snapshot["Profile4"]["curve_points"]}
p5Points = {q["voltage_mv"]: q for q in snapshot["Profile5"]["curve_points"]}
check("Profile 5 applies NO offset at the load floor",
      p5Points[720.0]["offset_mhz"] == 0.0, "got %s" % p5Points[720.0]["offset_mhz"])
check("Profile 4 applies a large positive offset at the load floor",
      470.0 < p4Points[720.0]["offset_mhz"] < 490.0,
      "got %s" % p4Points[720.0]["offset_mhz"])
check("the two profiles' underlying BASE curves agree at the floor to within one clock bin",
      abs(p4Points[720.0]["base_mhz"] - p5Points[720.0]["base_mhz"]) <= 15.0,
      "got %s vs %s" % (p4Points[720.0]["base_mhz"], p5Points[720.0]["base_mhz"]))

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
