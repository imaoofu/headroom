"""
Tests for the guards inside the 3070 Ti cross-chip claims.

WHY THIS FILE EXISTS, AND WHAT IT IS FOR
    Four of the claims in claims_crosschip.py carry a check that raises when the DATA stops
    supporting the sentence around it, rather than merely changing a number: the OC BIOS drawing
    more power at every matched point, the silent run being the hotter one, neither BIOS reaching
    its clock ceiling, and the two membw sweeps sharing all thirteen targets.

    A mutation run showed all four surviving deletion, because against today's data the guard
    condition is false and removing it changes nothing observable. That is the same trap recorded
    three times in test_audit_claims.py: a check that cannot be observed to fail is not a check.

    So each test below feeds one guard the data it exists to reject, and then feeds it data it
    should accept - because a guard that raises unconditionally is no better than one that never
    raises.

RUN
    python analysis/test_claims_crosschip.py
"""

import csv
import io
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import audit_claims                                     # noqa: E402
import claims_crosschip as cc                           # noqa: E402

failures = []


def check(name, ok, detail=""):
    if ok:
        print(f"[PASS] {name}")
    else:
        print(f"[FAIL] {name}" + (f"\n       {detail}" if detail else ""))
        failures.append(name)


# --------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------

COLUMNS = [
    "target_frequency_mhz", "achieved_frequency_avg", "achieved_frequency_min",
    "achieved_frequency_max", "memory_clock_avg_mhz", "memory_clock_min_mhz",
    "memory_clock_max_mhz", "lock_held", "lock_miss_mhz", "lock_miss_direction",
    "power_avg_w", "power_min_w", "power_max_w", "temperature_avg_c", "temperature_max_c",
    "utilization_avg_pct", "power_avg_process_w", "power_window_applied", "workload_seconds",
    "bench_seconds", "bench_wall_seconds", "bench_monitoring_s", "bench_throughput",
    "bench_throughput_unit", "bench_ok", "samples", "samples_process", "throttle_masks_seen",
]


def writeSweep(path, points, unit="FLOP/s"):
    """Write a sweep CSV the real loader will accept.

    `points` is a list of (target, achievedMhz, watts, throughput, tempAvg).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        for target, mhz, watts, throughput, temp in points:
            writer.writerow([
                target, mhz, mhz, mhz, 9251, 9251, 9251, "True", 0, "",
                watts, watts, watts, temp, temp + 2,
                98.0, watts, "True", 20, 20, 20, 20, throughput, unit, "True", 20, 20, "0x0",
            ])


def withFixture(build, call):
    """Run `call` against a throwaway repository laid out the way the claims expect."""
    saved = audit_claims.REPO_ROOT
    with tempfile.TemporaryDirectory() as raw:
        root = Path(raw)
        build(root / "data" / "frequency-sweeps")
        try:
            audit_claims.REPO_ROOT = root
            audit_claims._sweepCache.clear()
            return call()
        finally:
            audit_claims.REPO_ROOT = saved
            audit_claims._sweepCache.clear()


GRID = [855, 960, 1065, 1170, 1275, 1380, 1485]


def buildPair(silentWatts, ocWatts, silentTemp, ocTemp, ocThroughput=None):
    """A silent and a matched-grid OC sweep that differ only in the ways a test cares about."""
    def build(root):
        writeSweep(root / cc.SILENT_GEMM,
                   [(t, float(t), silentWatts(t), 1e10 * t, silentTemp(t)) for t in GRID])
        writeSweep(root / cc.OC_GEMM_MATCHED,
                   [(t, float(t), ocWatts(t),
                     (ocThroughput(t) if ocThroughput else 1e10 * t), ocTemp(t)) for t in GRID])
    return build


# --------------------------------------------------------------------------------------
# The four guards
# --------------------------------------------------------------------------------------

def testMatchedPowerGuardRejectsALostDirection():
    """The paragraph calls this the clearest evidence that shipped voltage is not required voltage.

    That reading needs the OC BIOS to draw more power at EVERY matched point. If one point ever
    inverts, a mean is still computable and would render happily under prose that has stopped
    being true.
    """
    # One point where the OC BIOS draws less: the claim must refuse the whole comparison.
    inverted = buildPair(lambda t: 100.0, lambda t: 130.0 if t != 1275 else 90.0,
                         lambda t: 50.0, lambda t: 50.0)
    raised = False
    try:
        withFixture(inverted, cc.matchedPower)
    except ValueError:
        raised = True
    check("an inverted power point is refused", raised, "it rendered a mean anyway")

    higher = buildPair(lambda t: 100.0, lambda t: 130.0, lambda t: 50.0, lambda t: 50.0)
    text = withFixture(higher, cc.matchedPower)
    check("a uniformly higher OC power still renders", "+30.00%" in text, f"got {text!r}")


def testThermalGuardRejectsAReversedTemperature():
    """The thermal argument only works while the SILENT run is the hotter one.

    Reverse the temperatures and the paragraph's reasoning is gone - but the numbers would still
    format. The guard is what makes the argument, not the formatting.
    """
    # TWO hotter points, not zero. A fixture with none makes `hotter` empty, and min() over an
    # empty sequence raises ValueError all by itself - so the test passed whether the guard was
    # there or not, and a mutation run caught it doing exactly that. Two points leaves the
    # rendering path working, so the only thing that can raise is the guard.
    reversed_ = buildPair(lambda t: 100.0, lambda t: 130.0,
                          silentTemp=lambda t: 60.0 if t in (855, 960) else 45.0,
                          ocTemp=lambda t: 52.0)
    message = ""
    try:
        withFixture(reversed_, cc.thermalRunsBackwards)
    except ValueError as error:
        message = str(error)
    check("too few hotter points is refused", "no longer the hotter one" in message,
          f"got {message!r}" if message else "it rendered a range anyway")

    asMeasured = buildPair(lambda t: 100.0, lambda t: 130.0,
                           silentTemp=lambda t: 58.0, ocTemp=lambda t: 52.0)
    text = withFixture(asMeasured, cc.thermalRunsBackwards)
    check("the measured ordering still renders", "C against" in text, f"got {text!r}")


def testPeakClockGuardRejectsABiosThatReachesItsCeiling():
    """5.5 says the card is power-limited rather than clock-limited. That is a claim about the
    data, not a description of it, and it has to be able to fail."""
    def build(root):
        # Throughput rising all the way to the top target: the card reaches its ceiling.
        writeSweep(root / cc.SILENT_GEMM,
                   [(t, float(t), 100.0 + t / 20, 1e10 * t, 50.0) for t in GRID])
        writeSweep(root / cc.OC_GEMM,
                   [(t, float(t), 100.0 + t / 20, 1e10 * t, 50.0) for t in GRID])
    raised = False
    try:
        withFixture(build, cc.peakClocksAgainstCeilings)
    except ValueError:
        raised = True
    check("a BIOS that reaches its ceiling is refused", raised, "it rendered a comparison anyway")

    def buildShort(root):
        # Peak in the middle, top targets undershooting - the measured behaviour.
        points = [(t, float(t) if t < 1380 else 1300.0, 100.0, 1e10 * min(t, 1380), 50.0)
                  for t in GRID]
        writeSweep(root / cc.SILENT_GEMM, points)
        writeSweep(root / cc.OC_GEMM, points)
    text = withFixture(buildShort, cc.peakClocksAgainstCeilings)
    check("a card short of its ceiling still renders", "against ceilings of" in text, f"got {text!r}")


def testReplicateGuardRejectsAChangedTargetCount():
    """"all thirteen shared targets" is a sentence, and thirteen is checkable."""
    def build(root):
        for path in cc.OC_MEMBW_RUNS:
            writeSweep(root / path,
                       [(t, float(t), 100.0, 1e11 * t, 50.0) for t in GRID], unit="B/s")
    raised = False
    try:
        withFixture(build, cc.membwReplicates)
    except ValueError:
        raised = True
    check("a grid that is not thirteen targets is refused", raised, "it rendered a mean anyway")


testMatchedPowerGuardRejectsALostDirection()
testThermalGuardRejectsAReversedTemperature()
testPeakClockGuardRejectsABiosThatReachesItsCeiling()
testReplicateGuardRejectsAChangedTargetCount()


if failures:
    print(f"{len(failures)} check(s) failed.")
    raise SystemExit(1)
print("ALL CHECKS PASSED")
