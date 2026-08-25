"""
Claims about the RTX 5060 Ti consumer measurements, checked against their source CSVs.

READ audit_claims.py FIRST. The short version: each function below returns the exact string
its document must contain, computed from the data. The engine asserts that string appears
verbatim and exactly once. Nothing here stores an expected number.

WHICH RUNS THESE REFER TO
    Eight sweeps, in the order they were taken, all on the same card:

      1  stock         gemm    2026-08-19 14:28   no memory OC, stock V/F curve
      2  tuned         gemm    2026-08-19 16:20   memory OC + flattened core curve
      3  tuned         membw   2026-08-19 20:42   the run that found the plateau
      4  memory-only   membw   2026-08-20 18:13   memory OC, core curve reverted
      5  memory-only   gemm    2026-08-20 18:32
      6  curve-fixed   membw   2026-08-20 21:53   stock slope restored below ~925 mV
      7  curve-fixed   gemm    2026-08-20 22:02   DISCARDED at 1852 MHz, see below
      8  curve-fixed2  gemm    2026-08-20 22:14   the clean gemm run under the repair

    Run 7's 1852 MHz row overshot its lock by +1002.6 MHz - the cap was never applied and the
    card ran at full boost. analyze_sweep.loadSweep drops rows that miss ABOVE, so sweep()
    excludes it automatically and every analytical claim below uses run 8. The one claim that
    quotes the failure itself reads it through sweepRaw().

    This matters more than it looks. An earlier version of the ROADMAP computed the tuned-vs-
    repaired efficiency gap from run 7 and reported "5-18% across 2317-2782 MHz". Including
    that one bad row understated both the band and the effect: the real answer from run 8 is
    up to 33.1% across 1545-2782 MHz.

WHY SOME CLAIMS PIN A SENTENCE FRAGMENT
    The documents are hard-wrapped at ~100 characters, so a sentence usually spans a line
    break and its exact text depends on where the wrap happens to fall. Claims therefore pin
    the longest fragment that stays on ONE line. Re-wrapping a paragraph will not break a
    claim; changing a number will.
"""

from statistics import fmean as mean, stdev
from audit_claims import (POST_SOAK, SOAK, WHOLE_RUN, claim, deltaPct, iterationsIn,
                          loadedSamples, signedPct, stabilityRun, sweep, sweepRaw,
                          voltageJoin)

PAPER = "docs/PAPER_DRAFT.md"
ANOMALY_README = "data/frequency-sweeps/membw-anomaly-20260819/README.md"

STOCK_GEMM = "oc-comparison-20260819/20260819-142844_5060ti-kittest-stock-gemm-stock_sweep.csv"
TUNED_GEMM = "oc-comparison-20260819/20260819-162025_5060ti-oc-gemm-stock_sweep.csv"
MEMONLY_GEMM = "membw-anomaly-20260819/20260820-183206_5060ti-memonly-gemm_sweep.csv"
FIXED1_GEMM = "membw-anomaly-20260819/20260820-220226_5060ti-curvefixed-gemm_sweep.csv"
FIXED2_GEMM = "membw-anomaly-20260819/20260820-221451_5060ti-curvefixed2-gemm_sweep.csv"

FIXED1_MEMBW_VOLTS = "membw-anomaly-20260819/20260820-215336_5060ti-curvefixed-membw_sweep_voltage.csv"
FIXED2_GEMM_VOLTS = "membw-anomaly-20260819/20260820-221451_5060ti-curvefixed2-gemm_sweep_voltage.csv"

# The four targets at which stock, tuned and the repaired curve all held their lock at the same
# achieved clock. 5.7.1 and 5.7.5 both tabulate these, which is the point - the repair is
# measured against the same rows the original saving was measured against.
MATCHED_TARGETS = [1852, 2010, 2167, 2317]

GRID = [1237, 1395, 1545, 1702, 1852, 2010, 2167, 2317, 2475, 2625, 2782, 2932, 3090]


def efficiency(row):
    return row["throughput"] / row["power"]


def peak(sweepRows):
    """Highest-throughput row. Not the highest TARGET row - the card does not reach its top
    targets, so the fastest point and the last point are different rows."""
    return max(sweepRows.values(), key=lambda r: r["throughput"])


# --------------------------------------------------------------------------------------
# 5.7.1 - the matched-frequency power reduction is entirely the core curve
# --------------------------------------------------------------------------------------

# Section 5.7.1 uses the 2026-08-22 clean-protocol runs, two per configuration, averaged.
#
# NEW CONSTANTS RATHER THAN REPOINTING STOCK_GEMM AND TUNED_GEMM IN PLACE. Those two are read by
# nine claims, including 5.7.5's voltage-shortfall refutation, which compares the tuned card
# against the curvefixed925 run of 2026-08-21. That is a dirty-vs-dirty comparison and valid on
# its own terms; repointing the shared constant would silently make it clean-vs-dirty, corrupting
# a sound refutation while breaking no test and looking like a tidy refactor.
#
# Averaged over two runs because a single sweep is what this project spent 2026-08-22 learning not
# to trust. Stock run-to-run spread on power at these four targets is 1.54% mean, 3.05% worst.
STOCK_GEMM_CLEAN = ["20260822-201101_5060ti-stock-gemm-clean-r1_sweep.csv", "20260822-201554_5060ti-stock-gemm-clean-r2_sweep.csv"]
TUNED_GEMM_CLEAN = ["20260822-182129_5060ti-tuned-gemm-clean-r1_sweep.csv", "20260822-182619_5060ti-tuned-gemm-clean-r2_sweep.csv"]
MEMONLY_GEMM_CLEAN = ["20260822-211705_5060ti-memonly-gemm-clean-r1_sweep.csv", "20260822-212156_5060ti-memonly-gemm-clean-r2_sweep.csv"]


def _meanPower(paths, target):
    return mean(sweep(p)[target]["power"] for p in paths)


def _powerRow171(target):
    stockW = _meanPower(STOCK_GEMM_CLEAN, target)
    tunedW = _meanPower(TUNED_GEMM_CLEAN, target)
    memonlyW = _meanPower(MEMONLY_GEMM_CLEAN, target)
    # No ** around the tuned column even though the document bolds it: audit_claims.normalise
    # strips emphasis from both sides, so rendering it here would be decoration only.
    return (f"| {target} MHz | {deltaPct(tunedW, stockW)} "
            f"| {deltaPct(memonlyW, stockW)} |")


for _target in MATCHED_TARGETS:
    claim(f"5.7.1-power-{_target}", PAPER, "5.7.1")(
        lambda target=_target: _powerRow171(target))


@claim("5.7.1-memonly-within-3pct", PAPER, "5.7.1")
def memonlyReproducesStockPower():
    """The claim is a bound, so the rendering has to be a bound too: the sentence says "within
    3%" and what is checked is that 3 is the smallest whole percent that still contains every
    matched point."""
    worst = max(abs(_meanPower(MEMONLY_GEMM_CLEAN, t) / _meanPower(STOCK_GEMM_CLEAN, t) - 1.0) * 100.0
                for t in MATCHED_TARGETS)
    import math
    return f"Memory-only reproduces stock power to within {math.ceil(worst)}%."


# --------------------------------------------------------------------------------------
# 5.7.5 - the repair is a trade, not a win
# --------------------------------------------------------------------------------------

def _powerRow175(target):
    stock, tuned, fixed = sweep(STOCK_GEMM), sweep(TUNED_GEMM), sweep(FIXED2_GEMM)
    return (f"| {target} MHz | {deltaPct(tuned[target]['power'], stock[target]['power'])} "
            f"| {deltaPct(fixed[target]['power'], stock[target]['power'])} |")


for _target in MATCHED_TARGETS:
    claim(f"5.7.5-power-{_target}", PAPER, "5.7.5")(
        lambda target=_target: _powerRow175(target))


def _efficiencyRow(target):
    tuned, fixed = sweep(TUNED_GEMM), sweep(FIXED2_GEMM)
    tunedEff, fixedEff = efficiency(tuned[target]), efficiency(fixed[target])
    # Throughput is in FLOP/s in the CSV; the table is in TFLOP/W, so scale before rounding.
    # Rounding a ratio of unscaled numbers would agree to four decimals by accident.
    return (f"| {target} MHz | {tunedEff / 1e12:.4f} | {fixedEff / 1e12:.4f} "
            f"| {signedPct(tunedEff / fixedEff)} |")


for _target in GRID:
    claim(f"5.7.5-efficiency-{_target}", PAPER, "5.7.5")(
        lambda target=_target: _efficiencyRow(target))


@claim("5.7.5-peak-repaired", PAPER, "5.7.5")
def peakOfRepairedCurve():
    best = peak(sweep(FIXED2_GEMM))
    return (f"repaired curve reaches {best['throughput'] / 1e12:.2f} TFLOP/s "
            f"at {best['mhz']:.0f} MHz drawing {best['power']:.1f} W")


@claim("5.7.5-peak-tuned", PAPER, "5.7.5")
def peakOfTunedCurve():
    best = peak(sweep(TUNED_GEMM))
    return (f"{best['mhz']:.0f} MHz drawing {best['power']:.1f} W - "
            f"{deltaPct(peak(sweep(FIXED2_GEMM))['throughput'], best['throughput'])[1:]} "
            f"less throughput for "
            f"{deltaPct(peak(sweep(FIXED2_GEMM))['power'], best['power'])[1:]} less power")


@claim("5.7.5-peak-efficiency-inversion", PAPER, "5.7.5")
def repairedIsMoreEfficientAtItsPeak():
    """The one point where the repaired curve wins on gemm. Pinned deliberately: reporting it
    without the thirteen-row table above was the cherry-pick this section exists to avoid."""
    fixedBest, tunedBest = peak(sweep(FIXED2_GEMM)), peak(sweep(TUNED_GEMM))
    gain = signedPct(efficiency(fixedBest) / efficiency(tunedBest))
    return f"so {gain[1:]} better efficiency"


@claim("5.7.5-stock-peak", PAPER, "5.7.5")
def stockPeak():
    return f"peaks at {peak(sweep(STOCK_GEMM))['throughput'] / 1e12:.2f}."


@claim("5.7.5-run7-overshoot", PAPER, "5.7.5")
def run7Overshoot():
    """Read through sweepRaw because sweep() exists to remove exactly this row."""
    bad = sweepRaw(FIXED1_GEMM)[1852]
    if bad["missDirection"] != "above":
        raise ValueError("run 7's 1852 MHz row no longer misses ABOVE; the claim is stale")
    return (f"{bad['mhz']:.1f} MHz and {bad['power']:.1f} W, "
            f"an overshoot of +{bad['missMhz']:.1f} MHz")


@claim("5.7.5-top-voltage-identical", PAPER, "5.7.5")
def bothCurveVariantsTopOutAtTheSameVoltage():
    """Two different runs on two different workloads, hence the odd pairing: run 7 was not
    voltage-logged, so variant 1's top voltage is only available from its membw sweep."""
    tops = []
    for path in (FIXED1_MEMBW_VOLTS, FIXED2_GEMM_VOLTS):
        rows = voltageJoin(path)
        volts = {rows[t]["voltage"] for t in rows if t >= 2625}
        if len(volts) != 1:
            raise ValueError(f"{path} is not flat above 2625 MHz: {sorted(volts)}")
        tops.append(volts.pop())
    if tops[0] != tops[1]:
        raise ValueError(f"the two variants differ at the top: {tops}")
    return f"Both curve variants measure {tops[0]:.3f} V at every target"


@claim("5.7.1-ceiling", PAPER, "5.7.1")
def theCurveRaisesTheSustainableCeiling():
    """The +12.3% here needs a stated denominator, and the sentence around it does not give
    one. Stock's PEAK is 15.71 TFLOP/s at 2598 MHz; stock's LAST GRID POINT is 15.68 at
    2588 MHz. Against the peak the gain is +12.1%, against the last point +12.3%. This claim
    renders the peak comparison, because "the highest throughput this configuration reached"
    is the only denominator the surrounding sentence can be read as meaning once it has
    already said stock collapses to ~2590 MHz."""
    tunedBest, stockBest = peak(sweep(TUNED_GEMM)), peak(sweep(STOCK_GEMM))
    return (f"holds {tunedBest['mhz']:.0f} MHz and reaches "
            f"{tunedBest['throughput'] / 1e12:.2f} TFLOP/s "
            f"({deltaPct(tunedBest['throughput'], stockBest['throughput'])}).")


@claim("5.7.5-widest-gap", PAPER, "5.7.5")
def theWidestEfficiencyGap():
    """The prose bound. Rendering it from the data is what stops it drifting out of step with
    the table above it, which is precisely how the ROADMAP came to say 5-18%."""
    tuned, fixed = sweep(TUNED_GEMM), sweep(FIXED2_GEMM)
    band = [t for t in GRID if efficiency(tuned[t]) > efficiency(fixed[t])]
    widest = max(efficiency(tuned[t]) / efficiency(fixed[t]) for t in band)
    return (f"ahead at every point from {min(band)} through {max(band)} MHz, "
            f"by up to {signedPct(widest)[1:]}")


TUNED_MEMBW = "membw-anomaly-20260819/20260819-204233_5060ti-oc-membw-anomaly_sweep.csv"
MEMONLY_MEMBW = "membw-anomaly-20260819/20260820-181307_5060ti-memonly-membw-anomaly_sweep.csv"
STOCK_MEMBW_13PT = "oc-comparison-20260819/20260819-143337_5060ti-kittest-stock-membw-stock_sweep.csv"

# --------------------------------------------------------------------------------------
# 5.7.2 - the core curve costs a bandwidth-bound workload up to 29.6%
# --------------------------------------------------------------------------------------

PLATEAU_TARGETS = [1560, 1710, 1867, 2025]


def _plateauRow(target):
    memonly, tuned = sweep(MEMONLY_MEMBW), sweep(TUNED_MEMBW)
    m, t = memonly[target], tuned[target]
    return (f"| ~{target} MHz | {m['throughput'] / 1e9:.1f} | {t['throughput'] / 1e9:.1f} "
            f"| {deltaPct(m['throughput'], t['throughput'])} "
            f"| {deltaPct(efficiency(m), efficiency(t))} |")


for _target in PLATEAU_TARGETS:
    claim(f"5.7.2-plateau-{_target}", PAPER, "5.7.2")(
        lambda target=_target: _plateauRow(target))


@claim("5.7.2-monotone-range", PAPER, "5.7.2")
def monotoneRange():
    rows = sweep(MEMONLY_MEMBW)
    targets = sorted(rows)
    lo, hi = targets[0], targets[-1]
    return f"at {lo} MHz to {rows[hi]['throughput'] / 1e9:.1f} at {hi}:"


@claim("5.7.2-plateau-band", PAPER, "5.7.2")
def plateauBand():
    rows = sweep(TUNED_MEMBW)
    bandTargets = [1560, 1635, 1710, 1792, 1867]
    throughputs = [rows[t]["throughput"] for t in bandTargets]
    smallest = min(throughputs)
    band = (max(throughputs) - smallest) / smallest * 100
    # rise is over achieved clock, not commanded target
    rise = (rows[bandTargets[-1]]["mhz"] / rows[bandTargets[0]]["mhz"] - 1) * 100
    return f"Five consecutive points sit inside a {band:.1f}% band while core clock rises {rise:.0f}%."


@claim("5.7.2-stock-rises", PAPER, "5.7.2")
def stockRises():
    rows = sweep(STOCK_MEMBW_13PT)
    vals = [rows[t]["throughput"] / 1e9 for t in (1545, 1702, 1852)]
    return f"{vals[0]:.0f} to {vals[1]:.0f} to {vals[2]:.0f}."


# --------------------------------------------------------------------------------------
# 5.4 - consumer hardware measurements
# --------------------------------------------------------------------------------------

GEMM_FLOOR15 = "20260822-173451_5060ti-gemm-floor15-rerun_sweep.csv"
MEMBW_FLOOR15 = "20260822-174118_5060ti-membw-floor15-rerun_sweep.csv"


def _optimum(rows):
    return max(rows.values(), key=efficiency)


def _sustainedMax(rows):
    return max(rows.values(), key=lambda r: r["mhz"])


def _gemmMembw():
    g, m = sweep(GEMM_FLOOR15), sweep(MEMBW_FLOOR15)
    return (_optimum(g), _sustainedMax(g), _optimum(m), _sustainedMax(m))


@claim("5.4-optimum", PAPER, "5.4")
def optimumRow():
    gOpt, _, mOpt, _ = _gemmMembw()
    return (f"| Efficiency optimum | {gOpt['mhz']:.0f} MHz "
            f"| {mOpt['mhz']:.0f} MHz |")


@claim("5.4-pct-of-max", PAPER, "5.4")
def pctOfMaxRow():
    gOpt, gMax, mOpt, mMax = _gemmMembw()
    gPct = gOpt["mhz"] / gMax["mhz"] * 100
    mPct = mOpt["mhz"] / mMax["mhz"] * 100
    return (f"| {chr(0x2014)} as % of sustained max "
            f"| {gPct:.0f}% (of {gMax['mhz']:.0f} MHz) "
            f"| {mPct:.0f}% (of {mMax['mhz']:.0f} MHz) |")


@claim("5.4-efficiency-gain", PAPER, "5.4")
def efficiencyGainRow():
    gOpt, gMax, mOpt, mMax = _gemmMembw()
    g = signedPct(efficiency(gOpt) / efficiency(gMax))
    m = signedPct(efficiency(mOpt) / efficiency(mMax))
    return f"| Efficiency gain vs sustained max | {g} | {m} |"


@claim("5.4-performance-cost", PAPER, "5.4")
def performanceCostRow():
    gOpt, gMax, mOpt, mMax = _gemmMembw()
    g = deltaPct(gOpt["throughput"], gMax["throughput"], minus=chr(0x2212))
    m = deltaPct(mOpt["throughput"], mMax["throughput"], minus=chr(0x2212))
    return f"| Performance cost at optimum | {g} | {m} |"


@claim("5.4-power-saved", PAPER, "5.4")
def powerSavedRow():
    gOpt, gMax, mOpt, mMax = _gemmMembw()
    g = deltaPct(gOpt["power"], gMax["power"], minus=chr(0x2212))
    m = deltaPct(mOpt["power"], mMax["power"], minus=chr(0x2212))
    return f"| Power saved at optimum | {g} | {m} |"


@claim("5.4-monotonicity-break", PAPER, "5.4")
def monotonicityBreak():
    rows = sweep(GEMM_FLOOR15)
    lower = min(rows.values(), key=lambda r: abs(r["mhz"] - 1987))
    higher = min(rows.values(), key=lambda r: abs(r["mhz"] - 2205))
    if lower["mhz"] >= higher["mhz"]:
        lower, higher = higher, lower
    lowerEff = efficiency(lower) / 1e9
    higherEff = efficiency(higher) / 1e9
    gap = (higherEff / lowerEff - 1) * 100
    # The unit is on the FIRST figure only, which is how the paper writes it.
    return (f"at {lower['mhz']:.0f} MHz ({lowerEff:.2f} GFLOP/J) sits marginally below "
            f"{higher['mhz']:.0f} MHz ({higherEff:.2f}), "
            f"breaking monotonicity by {gap:.1f}%")


# --------------------------------------------------------------------------------------
# 5.4.1 - Resolving the two optima
# 5.4.3 - The sub-100% utilisation is a telemetry artifact, not lost work
# --------------------------------------------------------------------------------------

GEMM_FINE_P1 = "20260822-174624_5060ti-gemm-fine-p1-rerun_sweep.csv"
MEMBW_FINE_P1 = "20260822-175205_5060ti-membw-fine-p1-rerun_sweep.csv"
MEMBW_FINE_P2 = "20260822-175706_5060ti-membw-fine-p2-rerun_sweep.csv"
GEMM_FINE_P2 = "20260822-180206_5060ti-gemm-fine-p2-rerun_sweep.csv"


@claim("5.4.1-point-count", PAPER, "5.4.1")
def pointCount():
    # sweepRaw keeps every row (so the total is right even if a lock overshot); sweep() has
    # the windowed flag, which sweepRaw rows do not carry.
    paths = (GEMM_FINE_P1, MEMBW_FINE_P1, MEMBW_FINE_P2, GEMM_FINE_P2)
    rawRows = [r for p in paths for r in sweepRaw(p).values()]
    total = len(rawRows)
    held = sum(1 for r in rawRows if r["lockHeld"])
    windowed = sum(1 for p in paths for r in sweep(p).values() if r["windowed"])
    if not (total == held == windowed):
        raise ValueError(
            f"point counts disagree: total={total}, lockHeld={held}, windowed={windowed}")
    return (f"All {total} points held their locked clock exactly, none overshot, "
            f"and all {total} had power windowed to the benchmark's timed region.")


def _membwDecoupled(target):
    p1, p2 = sweep(MEMBW_FINE_P1)[target], sweep(MEMBW_FINE_P2)[target]
    return p1, p2


@claim("5.4.3-decoupled-1897", PAPER, "5.4.3")
def decoupled1897():
    p1, p2 = _membwDecoupled(1897)
    return (f"At 1897 MHz the two passes recorded utilisation of {p1['utilisation']:.1f}% "
            f"and {p2['utilisation']:.1f}% {chr(0x2014)} and throughput of "
            f"{p1['throughput'] / 1e9:.1f} and {p2['throughput'] / 1e9:.1f} GB/s.")


@claim("5.4.3-decoupled-1605", PAPER, "5.4.3")
def decoupled1605():
    p1, p2 = _membwDecoupled(1605)
    return (f"At 1605 MHz, {p1['utilisation']:.1f}% and {p2['utilisation']:.1f}% "
            f"utilisation gave {p1['throughput'] / 1e9:.1f} and "
            f"{p2['throughput'] / 1e9:.1f} GB/s")


# ---------------------------------------------------------------------------------------------
# 5.7.5 The voltage-shortfall hypothesis, refuted
#
# These pin a REFUTATION. The paragraph they cover previously proposed the test as future work,
# and disagreed with every other project document for a day after the test was run. Pinning the
# numbers is what stops that paragraph drifting back out of step with the sweeps.
# ---------------------------------------------------------------------------------------------

CURVEFIXED2_GEMM = "membw-anomaly-20260819/20260820-221451_5060ti-curvefixed2-gemm_sweep.csv"
CURVEFIXED925_GEMM = "membw-anomaly-20260819/20260821-215215_5060ti-curvefixed925-gemm_sweep.csv"


def _peakPoint(path):
    return max(sweep(path).values(), key=lambda r: r["throughput"])


@claim("5.7.5-ceiling-fell", PAPER, "5.7.5")
def ceilingFell():
    before, after = _peakPoint(CURVEFIXED2_GEMM), _peakPoint(CURVEFIXED925_GEMM)
    drop = before["mhz"] - after["mhz"]
    if drop <= 0:
        raise ValueError(
            f"the ceiling did not fall: {before['mhz']:.1f} -> {after['mhz']:.1f} MHz. "
            "The paragraph this pins argues the prediction failed; if the data now says "
            "otherwise the prose is wrong, not this claim.")
    return (f"it fell, from {before['mhz']:.1f} MHz to {after['mhz']:.1f} MHz, "
            f"{drop:.1f} MHz in the wrong direction")


@claim("5.7.5-peak-improved", PAPER, "5.7.5")
def peakImproved():
    before, after = _peakPoint(CURVEFIXED2_GEMM), _peakPoint(CURVEFIXED925_GEMM)
    return (f"to {after['throughput'] / 1e12:.2f} TFLOP/s from "
            f"{before['throughput'] / 1e12:.2f}")


@claim("5.7.5-deficit-narrowed", PAPER, "5.7.5")
def deficitNarrowed():
    tuned = _peakPoint(TUNED_GEMM)
    before, after = _peakPoint(CURVEFIXED2_GEMM), _peakPoint(CURVEFIXED925_GEMM)
    return (f"against the tuned card's {tuned['throughput'] / 1e12:.2f} TFLOP/s from "
            f"{100 * (before['throughput'] / tuned['throughput'] - 1):.1f}% to "
            f"{100 * (after['throughput'] / tuned['throughput'] - 1):.1f}%")


@claim("5.7.5-frequency-gap", PAPER, "5.7.5")
def frequencyGap():
    tuned, after = _peakPoint(TUNED_GEMM), _peakPoint(CURVEFIXED925_GEMM)
    return (f"{after['mhz']:.1f} MHz against {tuned['mhz']:.1f} MHz, a shortfall of "
            f"{tuned['mhz'] - after['mhz']:.1f} MHz")


# ---------------------------------------------------------------------------------------------
# 5.4.4 Default-enabled capture software shifts the measured optimum
#
# Five sweeps on one configuration in one session: three with NVIDIA Instant Replay enabled, two
# with it disabled. These pin the section that reports a contaminant which biased this project's
# own measurements, so they matter more than most - a drifted number here would undermine the
# section's whole argument about measurement discipline.
# ---------------------------------------------------------------------------------------------

IR_ON = ["20260822-160740_5060ti-splitcurve-gemm-r1_sweep.csv",
         "20260822-161322_5060ti-splitcurve-gemm-r2_sweep.csv",
         "20260822-165213_5060ti-splitcurve-gemm-r4-instantreplay-on_sweep.csv"]
IR_OFF = ["20260822-163705_5060ti-splitcurve-gemm-r3-quiet_sweep.csv",
          "20260822-165944_5060ti-splitcurve-gemm-r5-instantreplay-off_sweep.csv"]


def _irCondition(paths):
    """Per-target mean throughput and mean power across the runs in one condition."""
    runs = [sweep(p) for p in paths]
    shared = set(runs[0])
    for r in runs[1:]:
        shared &= set(r)
    return {t: (mean(r[t]["throughput"] for r in runs),
                mean(r[t]["power"] for r in runs)) for t in shared}


def _irPeaks(paths):
    return [max(sweep(p).values(), key=lambda r: r["throughput"])["throughput"] / 1e12
            for p in paths]


def _irBandMeanGap(low, high):
    on, off = _irCondition(IR_ON), _irCondition(IR_OFF)
    targets = [t for t in sorted(on) if low <= t <= high]
    return mean(100 * (off[t][0] / on[t][0] - 1) for t in targets)


@claim("5.4.4-peaks-on", PAPER, "5.4.4")
def peaksOn():
    return "| Instant Replay enabled | " + " / ".join(f"{v:.2f}" for v in _irPeaks(IR_ON)) + " TFLOP/s |"


@claim("5.4.4-peaks-off", PAPER, "5.4.4")
def peaksOff():
    return "| Instant Replay disabled | " + " / ".join(f"{v:.2f}" for v in _irPeaks(IR_OFF)) + " TFLOP/s |"


@claim("5.4.4-band-penalty", PAPER, "5.4.4")
def bandPenalty():
    return (f"{_irBandMeanGap(1237, 2010):.2f}% mean across 1237-2010 MHz against "
            f"{_irBandMeanGap(2167, 3090):.2f}% across 2167-3090 MHz")


@claim("5.4.4-clock-unchanged", PAPER, "5.4.4")
def clockUnchanged():
    def peakMhz(p):
        return max(sweep(p).values(), key=lambda r: r["throughput"])["mhz"]
    on = [peakMhz(p) for p in IR_ON]
    off = [peakMhz(p) for p in IR_OFF]
    # The sentence gives ONE figure for the disabled condition, which is only honest if both of
    # its runs peaked at the same clock. Raise rather than quietly picking one of two.
    if len(set(round(v, 1) for v in off)) != 1:
        raise ValueError(f"disabled runs peaked at different clocks: {off}; the prose states a "
                         "single value and would be misdescribing the data")
    listed = ", ".join(f"{v:.1f}" for v in on[:-1]) + f" and {on[-1]:.1f}"
    return f"{listed} MHz enabled against {off[0]:.1f} MHz disabled"


def _irSpread(paths, target):
    values = [sweep(p)[target]["throughput"] for p in paths]
    return 100 * (max(values) - min(values)) / mean(values)


@claim("5.4.4-spread-1545", PAPER, "5.4.4")
def spread1545():
    return (f"At 1545 MHz the spread is\n{_irSpread(IR_ON, 1545):.2f}% enabled against "
            f"{_irSpread(IR_OFF, 1545):.2f}% disabled.")


def _irOptimum(paths):
    cond = _irCondition(paths)
    best = max(cond, key=lambda t: cond[t][0] / cond[t][1])
    top = max(cond)
    gain = 100 * ((cond[best][0] / cond[best][1]) / (cond[top][0] / cond[top][1]) - 1)
    return best, gain


@claim("5.4.4-optimum-on", PAPER, "5.4.4")
def optimumOn():
    best, gain = _irOptimum(IR_ON)
    return f"| Instant Replay enabled | {best} MHz | +{gain:.1f}% |"


@claim("5.4.4-optimum-off", PAPER, "5.4.4")
def optimumOff():
    best, gain = _irOptimum(IR_OFF)
    return f"| Instant Replay disabled | {best} MHz | +{gain:.1f}% |"


# ---------------------------------------------------------------------------------------------
# 5.7.6 A split-region curve, derived from the mechanism, recovers both
#
# Eight clean-protocol sweeps, five tuned and three split. The non-overlap claim is the load-
# bearing one here because it does not depend on averaging, so it is pinned separately from the
# means and RAISES rather than rendering if the ranges ever start to overlap.
# ---------------------------------------------------------------------------------------------

# The three split-curve gemm runs are not all verified-quiet, and four claims below
# compare them against five runs that are. Written once here rather than repeated at
# each call site, because a reason pasted four times is a reason nobody re-reads.
SPLIT_GEMM_MIX = ("two of the three split-curve runs (r3-quiet, r5-instantreplay-off) predate the encoder guard: their settings declare Instant Replay off but nothing verified it. The five tuned runs are all verified-quiet. The risk runs TOWARD the finding, not against it - undetected contamination would depress the split runs and understate the gap - and the one verified-quiet split run agrees at 18.22. Stated rather than silently mixed.")

TUNED_CLEAN_5 = [f"20260822-{s}_5060ti-tuned-gemm-clean-r{i}_sweep.csv" for i, s in
                 zip((1, 2, 3, 4, 5), ("182129", "182619", "213750", "215317", "215811"))]
SPLIT_CLEAN_3 = ["20260822-163705_5060ti-splitcurve-gemm-r3-quiet_sweep.csv",
                 "20260822-165944_5060ti-splitcurve-gemm-r5-instantreplay-off_sweep.csv",
                 "20260822-220443_5060ti-splitcurve-gemm-clean-r3_sweep.csv"]


def _peakTf(path):
    return max(sweep(path).values(), key=lambda r: r["throughput"])["throughput"] / 1e12


@claim("5.7.6-tuned-runs", PAPER, "5.7.6")
def tunedRuns():
    v = [_peakTf(p) for p in TUNED_CLEAN_5]
    return ("| original tune, n=5 | " + " / ".join(f"{x:.2f}" for x in v)
            + f" | {mean(v):.2f} TFLOP/s |")


@claim("5.7.6-split-runs", PAPER, "5.7.6",
       mixedProvenance=SPLIT_GEMM_MIX)
def splitRuns():
    v = [_peakTf(p) for p in SPLIT_CLEAN_3]
    return ("| split curve, n=3 | " + " / ".join(f"{x:.2f}" for x in v)
            + f" | {mean(v):.2f} TFLOP/s |")


@claim("5.7.6-no-overlap", PAPER, "5.7.6",
       mixedProvenance=SPLIT_GEMM_MIX)
def noOverlap():
    """The section's central claim, and the one that survives a small sample. If the ranges ever
    overlap the sentence is false, so this raises rather than quietly rendering numbers that no
    longer support the surrounding prose."""
    t = [_peakTf(p) for p in TUNED_CLEAN_5]
    s = [_peakTf(p) for p in SPLIT_CLEAN_3]
    if min(s) <= max(t):
        raise ValueError(f"the ranges now OVERLAP: lowest split {min(s):.2f} is not above highest "
                         f"tuned {max(t):.2f}. The prose claims they do not overlap.")
    return f"{min(s):.2f} against\n{max(t):.2f}"


@claim("5.7.6-gap", PAPER, "5.7.6",
       mixedProvenance=SPLIT_GEMM_MIX)
def splitGap():
    t = mean(_peakTf(p) for p in TUNED_CLEAN_5)
    s = mean(_peakTf(p) for p in SPLIT_CLEAN_3)
    return f"The gap is **+{100 * (s / t - 1):.2f}%**"


# ---------------------------------------------------------------------------------------------
# 5.7.4 - the repair REMOVES the membw plateau, and the cost lands on gemm in 5.7.5.
# Three source files, two grids, and one of them is an overclocked run with the word
# "stock" in its filename. See specs/paper-5.7.4-claims.md before editing any of this.
# ---------------------------------------------------------------------------------------------

FIXED_MEMBW = "membw-anomaly-20260819/20260820-215336_5060ti-curvefixed-membw_sweep.csv"
FIXED_MEMBW_VOLTS = "membw-anomaly-20260819/20260820-215336_5060ti-curvefixed-membw_sweep_voltage.csv"
TUNED_MEMBW_13PT = "oc-comparison-20260819/20260819-162516_5060ti-oc-membw-stock_sweep.csv"
TUNED_MEMBW_VOLTS = "membw-anomaly-20260819/20260820-210822_5060ti-oc-volt-membw_sweep_voltage.csv"


def _r574ratioRange(path, targets):
    rows = voltageJoin(path)
    vals = [rows[t]["crossbar"] / rows[t]["mhz"] for t in targets]
    return min(vals), max(vals)


@claim("5.7.4-voltage-rises", PAPER, "5.7.4")
def voltageRises():
    rows = voltageJoin(FIXED_MEMBW_VOLTS)
    return (f"{rows[1545]['voltage']:.3f} V at 1545 MHz through "
            f"{rows[2010]['voltage']:.3f} V at 2010, against a")


@claim("5.7.4-crossbar-restored", PAPER, "5.7.4")
def crossbarRestored():
    tunedRows = voltageJoin(TUNED_MEMBW_VOLTS)
    tunedVolt = tunedRows[1867]["voltage"]
    tunedRatio = tunedRows[1867]["crossbar"] / tunedRows[1867]["mhz"]
    lo, hi = _r574ratioRange(FIXED_MEMBW_VOLTS, [1545, 1852, 2010])
    return (f"flat {tunedVolt:.3f} V on the tuned card - and the crossbar-to-core ratio "
            f"returns to {lo:.3f}-{hi:.3f} from {tunedRatio:.3f}.")


@claim("5.7.4-plateau-gone", PAPER, "5.7.4")
def plateauGone():
    return f"{sweep(FIXED_MEMBW)[1852]['throughput'] / 1e9:.1f} GB/s at 1852 MHz"


@claim("5.7.4-plateau-comparison", PAPER, "5.7.4")
def plateauComparison():
    fixed = sweep(FIXED_MEMBW)[1852]["throughput"]
    tuned = sweep(TUNED_MEMBW_13PT)[1852]["throughput"]
    return (f"against the tuned profile's {tuned / 1e9:.1f}, "
            f"{deltaPct(fixed, tuned)}.")


@claim("5.7.4-peak-throughput", PAPER, "5.7.4")
def peakThroughput():
    best = max(sweep(FIXED_MEMBW).values(), key=lambda r: r["throughput"])
    return f"{best['throughput'] / 1e9:.1f} GB/s peak against"


@claim("5.7.4-peak-comparison", PAPER, "5.7.4")
def peakComparison():
    fixedPeak = max(sweep(FIXED_MEMBW).values(), key=lambda r: r["throughput"])["throughput"]
    tunedPeak = max(sweep(TUNED_MEMBW_13PT).values(), key=lambda r: r["throughput"])["throughput"]
    gap = abs(1 - fixedPeak / tunedPeak) * 100
    return f"the tuned {tunedPeak / 1e9:.1f}, a {gap:.1f}% difference"


@claim("5.7.4-peak-power", PAPER, "5.7.4")
def peakPower():
    fixedW = sweep(FIXED_MEMBW)[2932]["power"]
    tunedW = sweep(TUNED_MEMBW_13PT)[2932]["power"]
    return f"{fixedW:.1f} W against {tunedW:.1f} W at 2932 MHz"


# ---------------------------------------------------------------------------------------------
# 5.7.6 continued - the clean bandwidth ceiling, and the two sustained-load runs
#
# This block exists because of what 2026-08-24 found in the prose above it. Section 5.7.6 was
# rewritten twice on 2026-08-23 and both rewrites landed as UNPINNED prose, which the audit
# cannot see. Re-deriving every number in it by hand turned up two sentences that quoted three
# different aggregation windows as though they were one, and one unqualified "no throttled
# sample" that was true only of the logger's narrower definition.
#
# Nothing here was wrong arithmetic. Every figure was a real measurement of something. What was
# missing was a machine that would have noticed the pairing, which is what these claims are.
# ---------------------------------------------------------------------------------------------

# The three membw sweeps that share the 10-point 1402-2100 fine grid, all measured under the
# clean protocol of 5.4.4. Do not substitute the 2026-08-21 split-curve membw sweep or the
# 2026-08-20 memory-only one: both predate the encoder guard, and the second of them is the
# contaminated reference this section was rewritten to remove.
CLEAN_CEILING_MEMBW = "memonly-clean-20260823/20260823-205231_5060ti-memonly-clean-membw-fine_sweep.csv"
DIRTY_CEILING_MEMBW = "membw-anomaly-20260819/20260820-181307_5060ti-memonly-membw-anomaly_sweep.csv"
REPAIR_MEMBW_FINE = "curve-rebuild-20260823/20260823-202324_5060ti-curverebuilt-membw-fine_sweep.csv"
SPLIT_MEMBW_FINE = "20260822-161921_5060ti-splitcurve-membw-r2_sweep.csv"

# UNLIKE the gemm case above, the risk here runs AGAINST the finding rather than toward it.
# The split curve's membw sweep is 2026-08-22 data that predates the encoder guard, so if it
# was contaminated its throughput reads low and the -3.18% deficit below is an UPPER BOUND on
# what the split curve actually gives up. A six-minute clean re-measurement would settle it,
# and until then the section should not be read as having pinned that figure exactly.
SPLIT_MEMBW_MIX = ("the split curve's membw sweep predates the encoder guard and declares "
                   "rather than verifies its conditions, while both references are "
                   "verified-quiet. The risk runs AGAINST the finding: undetected "
                   "contamination would depress the split curve and overstate its deficit, "
                   "so -3.18% is an upper bound on the loss, not a measurement of it. "
                   "A clean re-measurement is outstanding.")

SPLIT_RUN = "20260823-183256_splitcurve"
OGTUNE_RUN = "20260823-192719_ogtune"


def _r576vsCeiling(path):
    """Per-point throughput of one configuration against the clean memory-only ceiling."""
    ceiling = sweep(CLEAN_CEILING_MEMBW)
    other = sweep(path)
    return [(other[t]["throughput"] / ceiling[t]["throughput"] - 1) * 100 for t in sorted(ceiling)]


def _r576ceilingRow(label, path):
    d = _r576vsCeiling(path)
    within = sum(1 for v in d if abs(v) <= 0.4)
    return (f"| {label} | {mean(d):.2f}% mean, {min(d):.2f}% to {max(d):+.2f}% | "
            f"{within} of {len(d)} points |")


@claim("5.7.6-tuned-spread", PAPER, "5.7.6")
def tunedSpread():
    """The table's spread column is the RANGE over the mean, not a standard deviation. The
    sentence below the table quotes a standard deviation ratio instead, and the two are pinned
    separately because they are different statistics that happen to sit two lines apart."""
    v = [_peakTf(p) for p in TUNED_CLEAN_5]
    return f"| {mean(v):.2f} TFLOP/s | {100 * (max(v) - min(v)) / mean(v):.2f}% |"


@claim("5.7.6-split-spread", PAPER, "5.7.6", mixedProvenance=SPLIT_GEMM_MIX)
def splitSpread():
    v = [_peakTf(p) for p in SPLIT_CLEAN_3]
    return f"| {mean(v):.2f} TFLOP/s | {100 * (max(v) - min(v)) / mean(v):.2f}% |"


@claim("5.7.6-spread-factor", PAPER, "5.7.6", mixedProvenance=SPLIT_GEMM_MIX)
def spreadFactor():
    """Raw standard deviations, not coefficients of variation. The two differ here - 4.5 against
    4.6 - and the sentence says "on standard deviation", so the raw ratio is what it means."""
    t = [_peakTf(p) for p in TUNED_CLEAN_5]
    s = [_peakTf(p) for p in SPLIT_CLEAN_3]
    tSpread = 100 * (max(t) - min(t)) / mean(t)
    sSpread = 100 * (max(s) - min(s)) / mean(s)
    return (f"{sSpread:.2f}% spread against {tSpread:.2f}%, "
            f"a factor of {stdev(t) / stdev(s):.1f} on")


@claim("5.7.6-peak-clocks", PAPER, "5.7.6",
       mixedProvenance="the split runs are mixed provenance, but this claim is about achieved CLOCK, and 5.4.4 measured that capture software does not move it - 2975.9 / 2976.5 / 2977.1 MHz with it enabled against 2977.0 disabled. The contaminant depresses throughput at a given clock; it does not change the clock reached.")
def peakClocks():
    def clockAtPeak(path):
        return max(sweep(path).values(), key=lambda r: r["throughput"])["mhz"]
    s = [clockAtPeak(p) for p in SPLIT_CLEAN_3]
    t = [clockAtPeak(p) for p in TUNED_CLEAN_5]
    if len({round(x, 1) for x in s}) != 1:
        raise ValueError(f"the three split runs no longer share one peak clock: {s}")
    return (f"All three split runs peaked at {s[0]:.1f} MHz achieved, against the tuned card's "
            f"{min(t):.1f}-{max(t):.1f} MHz.")


@claim("5.7.6-ceiling-rose", PAPER, "5.7.6",
       mixedProvenance="deliberately clean against contaminated - that difference is the quantity being measured. The 2026-08-20 memory-only sweep is schema 0.1.0 and recorded no video-engine telemetry at all, which is why it reads as unknown rather than merely unverified.")
def ceilingRose():
    """The correction that prompted the rewrite: the memory-only reference was contaminated, and
    re-measuring it clean moved it by roughly the amount 5.4.4 attributes to capture software."""
    clean = sweep(CLEAN_CEILING_MEMBW)
    dirty = sweep(DIRTY_CEILING_MEMBW)
    shared = sorted(set(clean) & set(dirty))
    if len(shared) != len(clean):
        raise ValueError(f"grids no longer match: {len(shared)} shared of {len(clean)}")
    d = [(clean[t]["throughput"] / dirty[t]["throughput"] - 1) * 100 for t in shared]
    return f"+{mean(d):.2f}%\non average, from +{min(d):.2f}% to +{max(d):.2f}%"


@claim("5.7.6-ceiling-holds", PAPER, "5.7.6", mixedProvenance=SPLIT_MEMBW_MIX)
def ceilingHolds():
    """A ceiling nothing exceeds by more than this much is still a ceiling. If either
    configuration ever clears it by more than the prose allows, the reference is suspect again -
    which is exactly how the contaminated one was caught."""
    best = max(max(_r576vsCeiling(REPAIR_MEMBW_FINE)), max(_r576vsCeiling(SPLIT_MEMBW_FINE)))
    return f"nothing now exceeds it by more than {best:.2f}% at"


@claim("5.7.6-clock-match", PAPER, "5.7.6", mixedProvenance=SPLIT_MEMBW_MIX)
def clockMatch():
    """The comparison is only meaningful if the three configurations reached the same clocks."""
    ceiling = sweep(CLEAN_CEILING_MEMBW)
    worst = 0.0
    for path in (REPAIR_MEMBW_FINE, SPLIT_MEMBW_FINE):
        rows = sweep(path)
        worst = max(worst, max(abs(rows[t]["mhz"] - ceiling[t]["mhz"]) for t in ceiling))
    return f"achieved clocks matched to {worst:.1f} MHz in"


@claim("5.7.6-repair-vs-ceiling", PAPER, "5.7.6")
def repairVsCeiling():
    return _r576ceilingRow("repaired curve", REPAIR_MEMBW_FINE)


@claim("5.7.6-split-vs-ceiling", PAPER, "5.7.6", mixedProvenance=SPLIT_MEMBW_MIX)
def splitVsCeiling():
    return _r576ceilingRow("split curve", SPLIT_MEMBW_FINE)


# --- the two thirty-minute protocol runs ------------------------------------------------------
#
# EVERY AGGREGATE BELOW NAMES ITS WINDOW. See iterationsIn() in audit_claims.py for why that is
# a required argument rather than a defaulted one.

def _r576loadedFraction(label):
    run = stabilityRun(label)
    return 100 * run["session"]["loaded_fraction"]


def _r576powerCapped(label):
    run = stabilityRun(label)
    return sum(1 for s in run["samples"] if "SwPowerCap" in s["throttleReasons"])


@claim("5.7.6-split-loaded", PAPER, "5.7.6")
def splitLoaded():
    run = stabilityRun(SPLIT_RUN)
    return (f"{_r576loadedFraction(SPLIT_RUN):.1f}% of one-second samples above "
            f"{run['session']['loaded_threshold_pct']:.0f}% utilisation")


@claim("5.7.6-split-powercap", PAPER, "5.7.6")
def splitPowerCap():
    """The logger reports zero throttled samples because it counts only hardware slowdown and
    thermal events - the software power cap is normal operation and it says so at length. The
    paper used to repeat the zero without the qualification, which reads as a stronger claim
    than the telemetry supports."""
    run = stabilityRun(SPLIT_RUN)
    return f"{_r576powerCapped(SPLIT_RUN)} of\n{len(run['samples'])} samples reported the software power cap"


@claim("5.7.6-split-power-temp", PAPER, "5.7.6")
def splitPowerTemp():
    run = stabilityRun(SPLIT_RUN)
    loaded = loadedSamples(run)
    return (f"Power averaged {mean(s['power'] for s in loaded):.1f} W and peaked\n"
            f"at {max(s['power'] for s in run['samples']):.1f} W against a "
            f"{float(run['session']['power_limit_w']):.0f} W limit; temperature peaked at "
            f"{max(s['temperature'] for s in run['samples']):.0f} C.")


def _r576drift(label, workload):
    """The harness's own post-soak degradation figure, positive meaning a fall."""
    for entry in stabilityRun(label)["protocol"]["degradation"]:
        if entry["Workload"] == workload:
            return entry["DropPct"]
    raise ValueError(f"{label} has no {workload} degradation entry")


@claim("5.7.6-split-drift", PAPER, "5.7.6")
def splitDrift():
    return (f"`gemm` drifted\n{_r576drift(SPLIT_RUN, 'gemm'):.2f}% and `membw` "
            f"+{_r576drift(SPLIT_RUN, 'membw'):.2f}%")


@claim("5.7.6-ogtune-summary", PAPER, "5.7.6")
def ogtuneSummary():
    run = stabilityRun(OGTUNE_RUN)
    return (f"{run['protocol']['iterations']} iterations, zero aborted, zero driver resets, zero "
            f"thermal or hardware-slowdown\nsamples, {_r576powerCapped(OGTUNE_RUN)} of "
            f"{len(run['samples'])} at the software power cap, "
            f"{_r576loadedFraction(OGTUNE_RUN):.1f}%\nloaded, drift `gemm` "
            f"+{_r576drift(OGTUNE_RUN, 'gemm'):.2f}% and `membw`\n"
            f"{_r576drift(OGTUNE_RUN, 'membw'):.2f}%.")


@claim("5.7.6-sustained-gemm", PAPER, "5.7.6")
def sustainedGemm():
    """POST-SOAK, on both sides. The earlier version of this sentence took the split curve's
    figure from all sixteen iterations and the original tune's from its eleven post-soak ones,
    under prose declaring both post-soak."""
    s = iterationsIn(stabilityRun(SPLIT_RUN), "gemm", POST_SOAK)
    o = iterationsIn(stabilityRun(OGTUNE_RUN), "gemm", POST_SOAK)
    if len(s) != len(o):
        raise ValueError(f"the two runs no longer have matching post-soak counts: {len(s)}, {len(o)}")
    return (f"`gemm` {mean(s) / 1e12:.2f} TFLOP/s on the split curve against {mean(o) / 1e12:.2f} on the\n"
            f"original tune, a gap of +{100 * (mean(s) / mean(o) - 1):.2f}%.")


@claim("5.7.6-sustained-corroboration", PAPER, "5.7.6", mixedProvenance=SPLIT_GEMM_MIX)
def sustainedCorroboration():
    """The whole point of the paragraph: two designs sharing no methodology land in the same
    place. Both halves are computed, so neither can drift away from the other unnoticed."""
    lockedGap = 100 * (mean(_peakTf(p) for p in SPLIT_CLEAN_3)
                       / mean(_peakTf(p) for p in TUNED_CLEAN_5) - 1)
    sustainedGap = 100 * (mean(iterationsIn(stabilityRun(SPLIT_RUN), "gemm", POST_SOAK))
                          / mean(iterationsIn(stabilityRun(OGTUNE_RUN), "gemm", POST_SOAK)) - 1)
    return f"agree to within {abs(lockedGap - sustainedGap):.2f}\npercentage points"


def _r576membwGap(window):
    s = iterationsIn(stabilityRun(SPLIT_RUN), "membw", window)
    o = iterationsIn(stabilityRun(OGTUNE_RUN), "membw", window)
    return mean(s), mean(o), 100 * (mean(s) / mean(o) - 1)


@claim("5.7.6-sustained-membw", PAPER, "5.7.6")
def sustainedMembw():
    s, o, gap = _r576membwGap(POST_SOAK)
    return f"{s / 1e9:.1f} GB/s against {o / 1e9:.1f}, a difference of {gap:.2f}%"


@claim("5.7.6-membw-windows", PAPER, "5.7.6")
def membwWindows():
    """Reading the same comparison on all three windows is what makes "indistinguishable"
    a measurement rather than a hope: it is small and negative on each of them."""
    soakGap = _r576membwGap(SOAK)[2]
    wholeGap = _r576membwGap(WHOLE_RUN)[2]
    whole = iterationsIn(stabilityRun(SPLIT_RUN), "membw", WHOLE_RUN)
    if len(whole) != 17:
        raise ValueError(f"the whole-run window is no longer seventeen iterations: {len(whole)}")
    return f"{soakGap:.2f}% across the soak\niterations, {wholeGap:.2f}% across all seventeen"


@claim("5.7.6-boost-band", PAPER, "5.7.6")
def boostBand():
    """Where an unlocked card actually sits, which is what makes 5.7.2's locked-frequency
    plateau a laboratory result rather than a cost paid in ordinary use. Mean loaded clock of
    each run, so the range is across configurations rather than within one."""
    means = sorted(mean(s["smClock"] for s in loadedSamples(stabilityRun(label)))
                   for label in (SPLIT_RUN, OGTUNE_RUN))
    return f"at {means[0]:.0f}-{means[1]:.0f} MHz, above the flattened region entirely"
