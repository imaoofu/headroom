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

from statistics import fmean as mean, median, stdev
from audit_claims import (CLAIMS, POST_SOAK, SOAK, WHOLE_RUN, claim, deltaPct, iterationsIn,
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
# The only stock membw sweep on the 10-point grid the memory-only runs use. The 13-point
# file above shares NO targets with them, so it cannot serve a matched comparison.
STOCK_MEMBW_VOLT = "membw-anomaly-20260819/20260820-211630_5060ti-stock-volt-membw_sweep.csv"

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
# Two sweeps, for the same reason the split curve has three: read individually they give
# -0.39% and +0.58% against the memory-only reference, so a single one of them is not a
# measurement of anything. REPAIR_MEMBW_FINE is kept as a name for the first because the
# 2026-08-23 write-up quotes it specifically as the run that caught the contaminated
# reference; analytical claims use the list.
REPAIR_MEMBW_FINE = "curve-rebuild-20260823/20260823-202324_5060ti-curverebuilt-membw-fine_sweep.csv"
REPAIR_MEMBW_RUNS = [
    REPAIR_MEMBW_FINE,
    "repair-clean-20260824/20260824-214928_5060ti-repair-clean-membw-fine-r2_sweep.csv",
]
TUNED_MEMBW_CLEAN = "20260822-183112_5060ti-tuned-membw-clean_sweep.csv"
# TWO sweeps, averaged. n=1 was not enough: the two runs land at -0.11% and -0.73% against
# the ceiling, because one of them carries a 6.91% single-point dip and the other does not.
# Every claim that reads the split curve reads the mean of both, and none of them reports
# a per-point statistic any more - see 5.7.6-within-instability for why.
SPLIT_MEMBW_RUNS = [
    "splitcurve-clean-20260824/20260824-203810_5060ti-splitcurve-clean-membw-fine_sweep.csv",
    "splitcurve-clean-20260824/20260824-210054_5060ti-splitcurve-clean-membw-fine-r2_sweep.csv",
    "splitcurve-clean-20260824/20260824-211535_5060ti-splitcurve-clean-membw-fine-r3_sweep.csv",
]

# RESOLVED 2026-08-24. This constant used to carry a mixed-provenance caveat saying that the
# split curve's -3.18% deficit was an upper bound rather than a measurement, because its membw
# sweep predated the encoder guard while both references were verified-quiet. The clean
# re-measurement below settled it: the split curve rose 3.19% and the deficit was almost entirely
# the contaminant. The caveat is gone because the run it described is no longer used.
#
# Keep the old sweep in the repository and do NOT delete it - it is the evidence for the
# withdrawal, and two claims below quote the difference between the two runs.
SPLIT_MEMBW_OLD = "20260822-161921_5060ti-splitcurve-membw-r2_sweep.csv"

SPLIT_RUN = "20260823-183256_splitcurve"
OGTUNE_RUN = "20260823-192719_ogtune"


def _r576throughput(paths, target):
    """Mean throughput at one target across however many sweeps a configuration has."""
    return mean(sweep(p)[target]["throughput"] for p in paths)


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


def _r576join(items):
    """"a, b and c" - the prose reads as English, so the rendering has to as well."""
    items = list(items)
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


def _r576word(n):
    small = {0: "zero", 1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six",
             7: "seven", 8: "eight", 9: "nine", 10: "ten", 20: "twenty", 30: "thirty",
             40: "forty", 50: "fifty", 60: "sixty", 70: "seventy", 80: "eighty", 90: "ninety"}
    if n in small:
        return small[n]
    if 20 < n < 100:
        return small[n // 10 * 10] + "-" + small[n % 10]
    raise ValueError(f"no spelling for {n}; the prose that needs it should be rewritten")


@claim("5.7.6-clock-match", PAPER, "5.7.6")
def clockMatch():
    """The comparison is only meaningful if the three configurations reached the same clocks.

    Both halves are computed: the worst mismatch, and the tolerance that covers all but the two
    top-of-band points. Pinning only the worst case would let the typical case drift silently,
    and the typical case is what makes the -0.11% and -0.39% readable as real."""
    ceiling = sweep(CLEAN_CEILING_MEMBW)
    deltas = []
    for path in REPAIR_MEMBW_RUNS + SPLIT_MEMBW_RUNS:
        rows = sweep(path)
        deltas.extend(abs(rows[t]["mhz"] - ceiling[t]["mhz"]) for t in ceiling)
    deltas.sort(reverse=True)
    # One point per sweep misses by the same amount at the top of the band, so "above the
    # third largest" counts zero. Split on the worst VALUE, not on a rank.
    outliers = sum(1 for d in deltas if d >= deltas[0])
    sweeps = len(REPAIR_MEMBW_RUNS) + len(SPLIT_MEMBW_RUNS)
    if len(deltas) != 10 * sweeps:
        raise ValueError(f"expected ten points across {sweeps} sweeps, got {len(deltas)}")
    return (f"achieved clocks matched to {deltas[0]:.1f} MHz in the worst case\n"
            f"and to {deltas[outliers]:.1f} MHz at the other {_r576word(len(deltas) - outliers)}")


def _r576bandMean(path):
    """Mean throughput across the whole 10-point band, in GB/s.

    The band mean rather than a per-point comparison, because 2026-08-24 established that
    per-point statistics on this measurement move by up to a full percentage point between
    replicates of one untouched profile. Six sweeps of three configurations span 1.32%; the
    configurations themselves span 0.56%. Nothing finer than a band mean is supportable.
    """
    return mean(r["throughput"] for r in sweep(path).values()) / 1e9


def _r576configRow(label, paths):
    # A bare path is iterable, so without this a single sweep would be read one character at a
    # time and the "sweeps" column would print its filename length. The count is a number the
    # reader relies on, so it has to be a real count.
    if isinstance(paths, str):
        raise TypeError("pass a list of sweeps; a configuration measured once must say so")
    values = [_r576bandMean(p) for p in paths]
    spread = ("-" if len(values) == 1
              else f"**{100 * (max(values) - min(values)) / mean(values):.2f}%**")
    each = " / ".join(f"{v:.1f}" for v in values)
    bold = "" if len(values) == 1 else "**"
    return f"| {label} | {len(values)} | {each} | {bold}{mean(values):.1f}{bold} | {spread} |"


@claim("5.7.6-ceiling-row", PAPER, "5.7.6")
def ceilingRow():
    return _r576configRow("memory-only (stock curve)", [CLEAN_CEILING_MEMBW])


@claim("5.7.6-repair-row", PAPER, "5.7.6")
def repairRow():
    return _r576configRow("repaired curve", REPAIR_MEMBW_RUNS)


@claim("5.7.6-split-row", PAPER, "5.7.6")
def splitRow():
    return _r576configRow("split curve", SPLIT_MEMBW_RUNS)


@claim("5.7.6-resolution", PAPER, "5.7.6")
def resolution():
    """The load-bearing claim of the subsection: the configurations are closer than the noise.

    RAISES if that ever stops being true, because the sentence around it says no ranking is
    supported. A future measurement that separates them would need different prose, not a
    different number."""
    groups = [[CLEAN_CEILING_MEMBW], REPAIR_MEMBW_RUNS, SPLIT_MEMBW_RUNS]
    configMeans = [mean(_r576bandMean(p) for p in g) for g in groups]
    between = 100 * (max(configMeans) - min(configMeans)) / mean(configMeans)
    withinEach = [100 * (max(v) - min(v)) / mean(v) for v in
                  ([_r576bandMean(p) for p in g] for g in groups) if len(v) > 1]
    everySweep = [_r576bandMean(p) for g in groups for p in g]
    across = 100 * (max(everySweep) - min(everySweep)) / mean(everySweep)
    if between >= max(withinEach):
        raise ValueError(f"the configurations now separate: between {between:.2f}% against a "
                         f"within-configuration maximum of {max(withinEach):.2f}%. The prose says "
                         "no ranking is supported and would no longer be true.")
    return (f"span {between:.2f}%. A single configuration re-measured spans up to "
            f"{max(withinEach):.2f}%, and the six\nsweeps together span {across:.2f}%")


@claim("5.7.6-repair-above-ceiling", PAPER, "5.7.6")
def repairAboveCeiling():
    """The reference is exceeded, and the paragraph says why that is noise and not a finding."""
    ceiling = sweep(CLEAN_CEILING_MEMBW)
    rows = sweep(REPAIR_MEMBW_RUNS[1])
    d = [(rows[t]["throughput"] / ceiling[t]["throughput"] - 1) * 100 for t in sorted(ceiling)]
    return f"also sits **{mean(d):.2f}%** above it"


@claim("5.7.6-per-sweep-readings", PAPER, "5.7.6")
def perSweepReadings():
    """Every individual reading, on one line, so no future edit can quote one of them alone."""
    # Counts checked before any file is read, so a changed run list fails saying so rather than
    # surfacing as a missing CSV. Third time this pattern has been needed in one file - a guard
    # placed after the I/O reports the wrong problem.
    if len(SPLIT_MEMBW_RUNS) != 3 or len(REPAIR_MEMBW_RUNS) != 2:
        raise ValueError("the prose names three split and two repair sweeps; there are "
                         f"{len(SPLIT_MEMBW_RUNS)} and {len(REPAIR_MEMBW_RUNS)}")
    ceiling = sweep(CLEAN_CEILING_MEMBW)

    def against(path):
        rows = sweep(path)
        return mean((rows[t]["throughput"] / ceiling[t]["throughput"] - 1) * 100
                    for t in sorted(ceiling))

    split = [against(p) for p in SPLIT_MEMBW_RUNS]
    repair = [against(p) for p in REPAIR_MEMBW_RUNS]
    return ("give " + _r576join(f"**{v:.2f}%**" for v in split)
            + " against the memory-only reference, and the two repair\nsweeps give "
            + _r576join(f"**{v:+.2f}%**" for v in repair))


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


# --- the withdrawal, and the evidence that identifies it as contamination ---------------------
#
# These pin the numbers that make the second correction of this paragraph auditable. Without them
# the withdrawal is an assertion, which is precisely the shape the two withdrawn versions had.

# The two grid points known to carry a single-point dip: 1792 MHz in the withdrawn 2026-08-22
# sweep, 1867 MHz in the second 2026-08-24 sweep. Excluding both is what "the one known dip in
# each run excluded" means in the prose, and it is stated rather than trimmed silently.
DIP_POINTS = (1792, 1867)


def _r576oldVsNew(excludeDips=False):
    old = sweep(SPLIT_MEMBW_OLD)
    targets = [t for t in sorted(old) if not (excludeDips and t in DIP_POINTS)]
    return {t: (_r576throughput(SPLIT_MEMBW_RUNS, t) / old[t]["throughput"] - 1) * 100
            for t in targets}


@claim("5.7.6-split-rose", PAPER, "5.7.6",
       mixedProvenance="deliberately verified-quiet against declared-unverified - that difference "
                       "is the quantity being measured, and it is what withdrew the -3.18%.")
def splitRose():
    """Both figures, because the second is what makes the first not depend on the dips."""
    return (f"reads **+{mean(_r576oldVsNew().values()):.2f}%** above\n"
            f"its 2026-08-22 predecessor, or **+{mean(_r576oldVsNew(True).values()):.2f}%** "
            f"with the one known dip in each run excluded")


@claim("5.7.6-contamination-signature", PAPER, "5.7.6",
       mixedProvenance="deliberately verified-quiet against declared-unverified, for the same "
                       "reason as 5.7.6-split-rose.")
def contaminationSignature():
    """WITHDRAWN AS EVIDENCE, and pinned anyway so the withdrawal itself stays honest.

    This used to render a within-band decline as confirmation that the rise carried 5.4.4's
    frequency signature, and it asserted the direction so it would fail if that inverted. Two
    things were wrong with it. With both known dips removed the difference is 0.31 points, which
    is flat. And the test was never available on this grid: 5.4.4's boundary is near 2010 MHz and
    nine of these ten points sit below it, where 5.4.4 predicts a UNIFORM offset. The paragraph
    now cites these numbers as the reason the argument does not hold, so the guard is gone with
    it - there is no direction left to assert."""
    d = _r576oldVsNew(excludeDips=True)
    low = [v for t, v in d.items() if t <= 1710]
    high = [v for t, v in d.items() if t >= 1942]
    return f"flat: **+{mean(low):.2f}%** against **+{mean(high):.2f}%**"


@claim("5.7.6-dip-replicate", PAPER, "5.7.6")
def dipInReplicate():
    """The verified-quiet dip that withdrew the isolated-point argument."""
    return f"**{_r576dip(SPLIT_MEMBW_RUNS[1])[1]:.2f}%** hole of its own at {_r576dip(SPLIT_MEMBW_RUNS[1])[0]} MHz"


@claim("5.7.6-vs-tuned-band", PAPER, "5.7.6")
def splitVsTunedBand():
    """The claim that survived every rewrite: against the fully tuned profile the plateau is gone.

    Both sweeps are verified-quiet, so unlike the ceiling comparison this one has never rested on
    mixed evidence."""
    tuned = sweep(TUNED_MEMBW_CLEAN)
    d = [(_r576throughput(SPLIT_MEMBW_RUNS, t) / tuned[t]["throughput"] - 1) * 100
         for t in sorted(tuned)]
    return f"+{mean(d):.1f}% on average across the\nband, +{min(d):.1f}% to +{max(d):.1f}%"


# --- single-point membw dips in verified-quiet runs -------------------------------------------
#
# Added 2026-08-24, and it retires an explanation rather than adding one. The "wandering membw
# dip" had been attributed to the capture software of 5.4.4 since 2026-08-22 on the strength of
# both being transient and both moving between runs. Two of the five verified-quiet sweeps on this
# grid carry one, so whatever produces it, that is not what it is.

CLEAN_MEMBW_FINE = ([CLEAN_CEILING_MEMBW, TUNED_MEMBW_CLEAN]
                    + REPAIR_MEMBW_RUNS + SPLIT_MEMBW_RUNS)


def _r576dip(path):
    """The deepest single-point departure from the local trend, as (target, percent).

    Measured against the mean of a point's two neighbours rather than against another sweep,
    because the question is whether a run is internally consistent - a dip that appears in one
    sweep of a pair is not a property of the configuration and must not be read as one.
    """
    rows = sweep(path)
    targets = sorted(rows)
    residuals = []
    for i in range(1, len(targets) - 1):
        neighbours = (rows[targets[i - 1]]["throughput"] + rows[targets[i + 1]]["throughput"]) / 2
        residuals.append((targets[i], (rows[targets[i]]["throughput"] / neighbours - 1) * 100))
    return min(residuals, key=lambda entry: entry[1])


@claim("5.7.6-dip-spread", PAPER, "5.7.6")
def dipSpread():
    """The worst-point departure of every verified-quiet sweep, as a CONTINUUM.

    This replaces a claim that counted "two of five runs with a 6-7% dip". That count was a 3%
    threshold laid across a continuous distribution of five samples, and the sixth sweep landed
    at -2.17%, between the two groups it had invented. A spread cannot be discretised into a
    finding the way a count invites."""
    worst = sorted((_r576dip(p)[1] for p in CLEAN_MEMBW_FINE), reverse=True)
    return (f"runs from **{worst[0]:.2f}%** to **{worst[-1]:.2f}%**, with the others at "
            + _r576join(f"{v:.2f}%" for v in worst[1:-1]))


@claim("5.7.6-dip-pair", PAPER, "5.7.6")
def dipPair():
    """The same point in two sweeps of one untouched profile, twenty minutes apart.

    This is the claim that makes the dip a measurement property rather than a configuration
    property, so it is pinned separately from the depth figures."""
    target = _r576dip(SPLIT_MEMBW_RUNS[1])[0]
    # The pair the prose names: the run WITHOUT the bad point and the run with it. Indexing two
    # specific runs rather than unpacking the list, which silently broke when a third was added.
    a = sweep(SPLIT_MEMBW_RUNS[0])[target]["throughput"] / 1e9
    b = sweep(SPLIT_MEMBW_RUNS[1])[target]["throughput"] / 1e9
    return f"reads {a:.1f} GB/s in one sweep\nand {b:.1f} in another"


# --------------------------------------------------------------------------------------
# 5.5.3 - the 5060 Ti half of the cross-chip bus-saturation comparison
# --------------------------------------------------------------------------------------
# This claim renders into 5.5.3, which is otherwise served by claims_crosschip.py. It lives here
# because it reads 5060 Ti sweeps and that module is forbidden from doing so. Splitting on data
# ownership rather than section number is what keeps a cross-chip claim from quietly reaching a
# 5060 Ti file through a shared constant.

# 128-bit bus, double-pumped, at the memory clock each configuration actually ran. Computed per
# configuration rather than from one nominal figure: the memory overclock changes the denominator,
# and dividing an overclocked throughput by the stock bus is how "173% of theoretical peak" got
# into a README once already.
def _r553bus(memoryClockMhz):
    return memoryClockMhz * 2 * 16 / 1000


@claim("5.5.3-5060ti-bus", PAPER, "5.5.3",
       mixedProvenance="two of the three runs are schema 0.1.0 and record no video-engine telemetry. Capture contamination DEPRESSES throughput, so a contaminated run understates bus efficiency and would exaggerate the shortfall this claim reports. The direction therefore runs toward the finding - and the single verified-quiet run gives 78.3%, the HIGHEST of the three, so the best-provenance number is still 12 points below the 3070 Ti's 90.4%.")
def bus5060ti():
    stock = max(r["throughput"] for r in sweep(STOCK_MEMBW_VOLT).values()) / 1e9
    ocPeaks = [max(r["throughput"] for r in sweep(p).values()) / 1e9
               for p in (MEMONLY_MEMBW, CLEAN_CEILING_MEMBW)]
    fractions = ([100 * stock / _r553bus(13801)]
                 + [100 * p / _r553bus(16301) for p in ocPeaks])
    return f"**{min(fractions):.1f}-{max(fractions):.1f}%** of its own bus"


# ---------------------------------------------------------------------------------------------
# 5.6.1.1, added 2026-08-29: the twelve-workload consumer constrained result, computed on the
# COMMANDED frequency basis. Keyed by achieved clock these sweeps share only five frequencies and
# the comparison cannot run at all - see analyze_constrained.py's loadSweepCurves docstring.
#
# These claims RUN THE ANALYSIS rather than reading a stored table, so the audit fails if the
# analyser's behaviour changes under them. That costs about a second per run.

SUITE_PATTERNS = ("stock-suite-20260829/*_sweep.csv", "suite-pilot-20260829/*_sweep.csv")


def _suiteCurves():
    """The twelve stock suite workloads, keyed by commanded target."""
    import contextlib
    import io
    import sys
    from audit_claims import REPO_ROOT
    analysisDir = str(REPO_ROOT / "analysis")
    if analysisDir not in sys.path:
        sys.path.insert(0, analysisDir)
    import analyze_constrained as constrained
    curves = {}
    with contextlib.redirect_stdout(io.StringIO()):
        for pattern in SUITE_PATTERNS:
            curves.update(constrained.loadSweepCurves(pattern, basis="commanded"))
    if len(curves) != 12:
        raise ValueError(f"expected 12 suite workloads, loaded {len(curves)}")
    return curves


def _fixedRow(floor):
    import contextlib
    import io
    import sys
    from audit_claims import REPO_ROOT
    analysisDir = str(REPO_ROOT / "analysis")
    if analysisDir not in sys.path:
        sys.path.insert(0, analysisDir)
    import analyze_constrained as constrained
    with contextlib.redirect_stdout(io.StringIO()):
        rows = constrained.reportFixedVersusPerWorkload(_suiteCurves(), [floor])
    if not rows:
        raise ValueError(f"no fixed frequency is feasible at a {floor:.0%} floor on the "
                         f"commanded basis - 5.6.1.1's table cannot be rendered")
    return rows[0]


@claim("5.6.1.1-shared-frequencies", PAPER, "5.6.1.1")
def suiteSharedFrequencies():
    """RAISES if the achieved basis ever stops being the smaller number.

    The whole argument for the commanded basis is that clamping collapses the shared grid. If the
    two counts ever match, the section's premise is gone and the prose needs rewriting rather than
    the number updating.
    """
    import contextlib
    import io
    import sys
    from audit_claims import REPO_ROOT
    analysisDir = str(REPO_ROOT / "analysis")
    if analysisDir not in sys.path:
        sys.path.insert(0, analysisDir)
    import analyze_constrained as constrained
    counts = {}
    with contextlib.redirect_stdout(io.StringIO()):
        for basis in ("achieved", "commanded"):
            curves = {}
            for pattern in SUITE_PATTERNS:
                curves.update(constrained.loadSweepCurves(pattern, basis=basis))
            counts[basis] = len(set.intersection(
                *[{round(p["mhz"]) for p in v} for v in curves.values()]))
    if counts["achieved"] >= counts["commanded"]:
        raise ValueError(f"the achieved basis no longer shares fewer frequencies "
                         f"({counts['achieved']}) than the commanded one ({counts['commanded']})")
    return f"share only **{counts['achieved']}** achieved clocks"


@claim("5.6.1.1-floor-row-95", PAPER, "5.6.1.1")
def suiteFloorRow95():
    row = _fixedRow(0.95)
    return (f"| **{row['floor']:.0%}** | **{row['per_workload_pct']:.1f}%** | "
            f"**{row['fixed_pct']:.1f}%** | **{row['fixed_mhz']:.0f} MHz** | "
            f"**{row['gap_pp']:.1f} pp** | **{row['share_pct']:.0f}%** |")


@claim("5.6.1.1-share-beats-v100", PAPER, "5.6.1.1")
def suiteShareBeatsV100():
    """RAISES if the consumer share ever falls below the V100's 83%.

    The sentence says the consumer case is the stronger one. If it stops being so, that is a
    finding about the suite and not a number to quietly update.
    """
    share = _fixedRow(0.95)["share_pct"]
    if share <= 83:
        raise ValueError(f"consumer share {share:.0f}% no longer exceeds the V100's 83%")
    return f"**{share:.0f}% of the available efficiency gain requires knowing which workload is\nrunning** — against 83% on the V100"


@claim("5.6.1.1-achieved-spread", PAPER, "5.6.1.1")
def suiteAchievedSpread():
    """What the twelve workloads actually held at the fixed policy's chosen target.

    The point of the commanded basis is that this spread exists and an achieved-keyed analysis
    cannot see it, so it is pinned rather than described.
    """
    row = _fixedRow(0.95)
    target = round(row["fixed_mhz"])
    held = []
    for points in _suiteCurves().values():
        held += [p["achieved_mhz"] for p in points if round(p["mhz"]) == target]
    return (f"**{min(held):.0f} to {max(held):.0f} MHz, a spread of "
            f"{max(held) - min(held):.0f} MHz**")


# ---------------------------------------------------------------------------------------------
# 5.6.2.1: the constrained MODEL comparison retested on consumer silicon. These run the
# leave-one-workload-out evaluation, which is why the audit costs a few seconds - the alternative
# is a stored table that cannot notice the model changing underneath it.

def _consumerLoo(floor=0.95):
    import contextlib
    import io
    import sys
    from audit_claims import REPO_ROOT
    for directory in (REPO_ROOT / "analysis", REPO_ROOT / "analysis" / "models"):
        if str(directory) not in sys.path:
            sys.path.insert(0, str(directory))
    import predict_constrained_frequency as predictor
    with contextlib.redirect_stdout(io.StringIO()):
        dataset = predictor.loadConsumerDataset()
        result = predictor.runLeaveOneWorkloadOut(
            dataset, floor, probeFrequencies=predictor.CONSUMER_PROBE_FREQUENCIES_MHZ)
    return result["scores"]


@claim("5.6.2.1-interpolation-row", PAPER, "5.6.2.1")
def consumerInterpolationRow():
    s = _consumerLoo()
    return (f"| **interpolation between the four probes, no fit** | "
            f"**{s.loc['interpolation (no fit)', 'mean_gain_pct']:.1f}%** | "
            f"**{s.loc['interpolation (no fit)', 'floor_violations']:.0f}** |")


@claim("5.6.2.1-fitting-earns-nothing", PAPER, "5.6.2.1")
def consumerFittingEarnsNothing():
    """RAISES if a fitted variant ever beats plain interpolation on the consumer suite.

    This is the half of the result that says the FITTING earns nothing. If a calibrated fit
    overtakes interpolation, 5.6.2.1's conclusion is inverted and the prose must be rewritten
    rather than the numbers refreshed.
    """
    s = _consumerLoo()
    calibrated = s.loc["probe model (calibrated)", "mean_gain_pct"]
    interpolation = s.loc["interpolation (no fit)", "mean_gain_pct"]
    if calibrated >= interpolation:
        raise ValueError(f"the calibrated fit now beats interpolation on the consumer suite, "
                         f"{calibrated:.1f}% against {interpolation:.1f}%")
    return f"falls to {calibrated:.1f}%, below the {interpolation:.1f}%"


@claim("5.6.2.1-ridge-breaks-floor", PAPER, "5.6.2.1")
def consumerRidgeBreaksFloor():
    """RAISES if Ridge ever keeps the floor here - the sentence says it only leads by breaking it."""
    violations = _consumerLoo().loc["probe model (ridge)", "floor_violations"]
    if violations <= 0:
        raise ValueError("Ridge no longer breaks the floor on the consumer suite")
    return f"breaking the floor on {violations:.0f} of 12"


@claim("5.6.2.1-fixed-breaks-floor", PAPER, "5.6.2.1")
def consumerFixedBreaksFloor():
    """The fixed baseline breaking the floor is the consumer-specific part of this result.

    RAISES if it stops, because the paragraph's claim is that a single frequency is infeasible at
    a 95% floor across this spread of workloads - not that it merely scores badly.
    """
    violations = _consumerLoo().loc["best fixed frequency", "floor_violations"]
    if violations <= 0:
        raise ValueError("the fixed baseline no longer breaks the floor on the consumer suite - "
                         "5.6.2.1 says it does, and that is the consumer-specific finding")
    return f"**One workload of twelve.**" if violations == 1 else f"{violations:.0f} of twelve"


# --------------------------------------------------------------------------------------
# 3.3 / 5.5 - the declared arithmetic intensity column
#
# WHY THIS IS PINNED, AND WHY A TEST WAS NOT ENOUGH
#     The FLOP/byte column is the axis 5.5's central result is plotted against: the performance
#     cost of the optimum tracks arithmetic intensity, with the transition between bgemm64 and
#     bgemm128 landing where the roofline knee was measured independently. Nothing checked it.
#
#     test_gpu_workload.py appears to. It compares suiteDeclaredIntensity() against a longhand
#     builderIntensity() written out in the test file, deliberately not importing from the
#     builder so the two derivations stay independent. But buildSuiteWorkload() - the code that
#     actually runs on the card - is in NEITHER side of that comparison. Mutation testing on
#     2026-08-30 changed six of its coefficients one at a time (softmax 5.0 to 4.0, layernorm
#     8.0 to 6.0, conv's 2.0 to 1.0, attention's 4.0 to 2.0, and two byte counts) and all six
#     survived the full suite. The check compares two copies of the formula; the third copy is
#     the one that ships.
#
#     Fixing that properly means extracting the builder's arithmetic so the runtime path is the
#     tested path. That is a change to the collection tool, and the 3070 Ti runs are still to be
#     taken with it, so it waits until after collection. THIS claim is the interim guard: it is
#     additive, touches no collection code, and if a coefficient ever drifts the README table
#     stops matching the formula and the audit fails.
#
#     It pins suiteDeclaredIntensity, not the builder, so it does not close the gap above - it
#     bounds the damage. A drift in the builder alone still goes unnoticed.
# --------------------------------------------------------------------------------------

import sys as _sys
from audit_claims import REPO_ROOT as _REPO_ROOT

# gpu_workload defers `import torch` into the function that needs it, so importing the module
# here costs nothing and works on a machine with no CUDA - which is what lets CI run this.
_sys.path.insert(0, str(_REPO_ROOT / "tools" / "frequency-sweep"))
from gpu_workload import LADDER_SIZES, suiteDeclaredIntensity  # noqa: E402

SUITE_README = "data/frequency-sweeps/stock-suite-20260829/README.md"

# `gemm` appears in the same table at 1365 but is the legacy workload, not a suite one -
# suiteDeclaredIntensity raises on it - so it is not pinned here.
SUITE_INTENSITY_NAMES = (["copy", "reduce", "softmax", "layernorm"]
                         + [f"bgemm{n}" for n in LADDER_SIZES]
                         + ["attention", "conv"])


def formatIntensity(value):
    """Render one cell exactly as the table writes it.

    Three shapes, and they are the table's, not a preference: an exact zero is written `0`
    rather than `0.00`; a whole number at or above 100 drops its decimals (`256`, `288`);
    everything else takes two places. Changing this changes what the document must say.
    """
    if value == 0:
        return "0"
    if float(value).is_integer() and value >= 100:
        return str(int(value))
    return f"{value:.2f}"


def _registerIntensityClaim(name):
    def render():
        return f"| `{name}` | {formatIntensity(suiteDeclaredIntensity(name))} |"
    render.__name__ = f"intensity_{name}"
    render.__doc__ = (f"{name}'s FLOP/byte cell, computed from operation counts rather than "
                      f"read back from the table it is checking.")
    claim(f"5.5-intensity-{name}", SUITE_README)(render)


for _name in SUITE_INTENSITY_NAMES:
    _registerIntensityClaim(_name)


# --------------------------------------------------------------------------------------
# 5.5 - the suite table's measured columns
#
# WHY THESE EXIST, AND WHAT THEY COST BY NOT EXISTING SOONER
#     The FLOP/byte column was pinned earlier on 2026-08-30. The three MEASURED columns beside
#     it - efficiency gain, performance cost, power saved - were not, and one of them was wrong.
#     `attention` read 55.6% / 46.3% / 65.5% against its own CSV's 53.7% / 45.9% / 64.8%. The
#     other eleven rows agreed to within rounding, so it was a transcription error rather than a
#     computation one, and it survived from 2026-08-29 until a replicate was collected and the
#     recomputed r1 value disagreed with the table.
#
#     That is the failure audit_claims.py was built for, appearing in the one part of the table
#     nothing rendered. Each claim below pins a row through its gain column, computed from the
#     CSV, so the same error fails the audit rather than waiting for someone to recompute it.
# --------------------------------------------------------------------------------------

SUITE_R1_SWEEPS = {
    "copy": "suite-pilot-20260829/20260829-142703_5060ti-stock-suitepilot-copy_sweep.csv",
    "reduce": "stock-suite-20260829/20260829-151627_5060ti-stock-suite-reduce_sweep.csv",
    "softmax": "stock-suite-20260829/20260829-152055_5060ti-stock-suite-softmax_sweep.csv",
    "layernorm": "stock-suite-20260829/20260829-152513_5060ti-stock-suite-layernorm_sweep.csv",
    "bgemm32": "stock-suite-20260829/20260829-150242_5060ti-stock-suite-bgemm32_sweep.csv",
    "bgemm64": "stock-suite-20260829/20260829-150701_5060ti-stock-suite-bgemm64_sweep.csv",
    "bgemm128": "suite-pilot-20260829/20260829-143124_5060ti-stock-suitepilot-bgemm128_sweep.csv",
    "bgemm256": "stock-suite-20260829/20260829-151122_5060ti-stock-suite-bgemm256_sweep.csv",
    "bgemm1024": "suite-pilot-20260829/20260829-143601_5060ti-stock-suitepilot-bgemm1024_sweep.csv",
    "attention": "stock-suite-20260829/20260829-152936_5060ti-stock-suite-attention_sweep.csv",
    "conv": "suite-pilot-20260829/20260829-144105_5060ti-stock-suitepilot-conv_sweep.csv",
    "gemm": "stock-suite-20260829/20260829-145752_5060ti-stock-gemm-1237grid_sweep.csv",
}


def suiteRowFigures(relativePath):
    """(optimum MHz, efficiency gain %, performance cost %) for one sweep.

    The reference point is the highest ACHIEVED clock in the sweep, not the highest commanded
    one: above ~2310 MHz each workload clamps to a different sustained clock, so the top target
    is not a frequency any of them actually ran at. This mirrors analyze_sweep.describe().
    """
    rows = list(sweep(relativePath).values())
    peak = max(rows, key=lambda row: row["efficiency"])
    fastest = max(rows, key=lambda row: row["mhz"])
    return (peak["mhz"],
            100.0 * (peak["efficiency"] / fastest["efficiency"] - 1.0),
            100.0 * (1.0 - peak["throughput"] / fastest["throughput"]))


def _registerSuiteRowClaim(name):
    def render():
        optimum, gain, _ = suiteRowFigures(SUITE_R1_SWEEPS[name])
        return (f"| `{name}` | {formatIntensity(suiteDeclaredIntensity(name)) if name != 'gemm' else '1365'} "
                f"| {optimum:.0f} MHz | {gain:.1f}% |")
    render.__name__ = f"suiteRow_{name}"
    render.__doc__ = (f"{name}'s row through the efficiency-gain column, recomputed from its "
                      f"sweep CSV rather than read back from the table it checks.")
    claim(f"5.5-suite-row-{name}", SUITE_README)(render)


for _name in SUITE_R1_SWEEPS:
    _registerSuiteRowClaim(_name)


# --------------------------------------------------------------------------------------
# 3.3.1 - the saturation probes
#
# These sat unpinned while 3.3.1 carried a DRAFT marker, and the marker was doing the work a
# claim should: signalling "not checked" rather than making checking unnecessary. The section's
# argument rests on two independent methods landing at the same ceiling, so the two numbers that
# have to agree are exactly the two worth rendering from the data.
#
# The 2800 MHz band of the unrolled-kernel probe is deliberately NOT pinned: it sampled the
# memory clock at an idle P-state and its derived peak is wrong by a factor of two, which shows
# up as unroll-1 reading 173% of "peak". See data/probes/README-saturation.md. Pinning a number
# from it would give a wrong figure the appearance of an audited one.
# --------------------------------------------------------------------------------------

import json as _json

PROBE_ISSUE_CEILING = "data/probes/probe_issue_ceiling_result.json"
PROBE_UNROLLED = "data/probes/probe_unrolled_kernel_result.json"


def _probe(relativePath):
    with open(_REPO_ROOT / relativePath, encoding="utf-8-sig") as handle:
        return _json.load(handle)


@claim("3.3.1-concurrency-ceiling", PAPER, "3.3.1")
def concurrencyCeiling():
    """Four streams against one, at 1395 MHz. The sentence pins both numbers because the CLAIM is
    that concurrency lifts throughput and then stops, which one number cannot express."""
    data = _probe(PROBE_ISSUE_CEILING)["aggregate_gbs"]
    return (f"four independent copies on separate streams at 1395 MHz reach "
            f"{data['4']:.1f} GB/s\naggregate, against {data['1']:.1f} for one")


@claim("3.3.1-unroll-spread", PAPER, "3.3.1")
def unrollSpread():
    """Unroll 1 against unroll 16 at 1395 MHz - a 16x change in memory-level parallelism."""
    unrolled = _probe(PROBE_UNROLLED)["results"]["1400"]["unrolled"]
    return (f"At 1395 MHz it delivers {unrolled['1']:.1f} GB/s at unroll 1 and "
            f"{unrolled['16']:.1f} at unroll 16")


@claim("3.3.1-methods-agree", PAPER, "3.3.1")
def methodsAgree():
    """The load-bearing sentence of 3.3.1: two unrelated mechanisms for raising memory-level
    parallelism land on the same ceiling. Rendered as a BOUND, because the sentence states one -
    and the bound is what makes the agreement an argument rather than a coincidence."""
    concurrency = _probe(PROBE_ISSUE_CEILING)["aggregate_gbs"]["4"]
    unrolled = _probe(PROBE_UNROLLED)["results"]["1400"]["unrolled"]["16"]
    spread = abs(unrolled / concurrency - 1.0) * 100.0
    import math
    bound = math.ceil(spread * 100) / 100
    return f"agree to within {bound:.2f}% ({concurrency:.1f} against {unrolled:.1f} GB/s)"


# --------------------------------------------------------------------------------------
# 5.4.5 - what reproduces between sessions
#
# Three complete stock collections of the twelve-workload suite: r1 (2026-08-29), r2 (08-30),
# r3 (09-02). These claims recompute the spread from all 36 CSVs rather than storing it, so a
# re-measured replicate or an edited paper both fail the audit.
#
# THE FILES CANNOT BE GLOBBED, which is why all three maps are written out. r1's gemm sweep is
# named `stock-gemm-1237grid` rather than `stock-suite-gemm`, so a `*gemm*` pattern matches
# `bgemm1024` instead and yields a plausible wrong number - that happened once during analysis.
# And `bgemm64-r3` exists in TWO directories: this replicate, and the third of four bgemm64
# repeats collected during the r2 session. Resolve by directory, never by tag.
# --------------------------------------------------------------------------------------

SUITE_R2_DIR = "suite-replicate-r2-20260830"
SUITE_R3_DIR = "suite-replicate-r3-20260902"

SUITE_R2_SWEEPS = {
    "copy": f"{SUITE_R2_DIR}/20260830-131414_5060ti-stock-suite-copy-r2_sweep.csv",
    "reduce": f"{SUITE_R2_DIR}/20260830-131835_5060ti-stock-suite-reduce-r2_sweep.csv",
    "softmax": f"{SUITE_R2_DIR}/20260830-132304_5060ti-stock-suite-softmax-r2_sweep.csv",
    "layernorm": f"{SUITE_R2_DIR}/20260830-132723_5060ti-stock-suite-layernorm-r2_sweep.csv",
    "bgemm32": f"{SUITE_R2_DIR}/20260830-133147_5060ti-stock-suite-bgemm32-r2_sweep.csv",
    "bgemm64": f"{SUITE_R2_DIR}/20260830-133608_5060ti-stock-suite-bgemm64-r2_sweep.csv",
    "bgemm128": f"{SUITE_R2_DIR}/20260830-134028_5060ti-stock-suite-bgemm128-r2_sweep.csv",
    "bgemm256": f"{SUITE_R2_DIR}/20260830-134503_5060ti-stock-suite-bgemm256-r2_sweep.csv",
    "bgemm1024": f"{SUITE_R2_DIR}/20260830-135007_5060ti-stock-suite-bgemm1024-r2_sweep.csv",
    "attention": f"{SUITE_R2_DIR}/20260830-135511_5060ti-stock-suite-attention-r2_sweep.csv",
    "conv": f"{SUITE_R2_DIR}/20260830-140020_5060ti-stock-suite-conv-r2_sweep.csv",
    "gemm": f"{SUITE_R2_DIR}/20260830-140529_5060ti-stock-suite-gemm-r2_sweep.csv",
}

SUITE_R3_SWEEPS = {
    "copy": f"{SUITE_R3_DIR}/20260902-190250_5060ti-stock-suite-copy-r3_sweep.csv",
    "reduce": f"{SUITE_R3_DIR}/20260902-190713_5060ti-stock-suite-reduce-r3_sweep.csv",
    "softmax": f"{SUITE_R3_DIR}/20260902-191142_5060ti-stock-suite-softmax-r3_sweep.csv",
    "layernorm": f"{SUITE_R3_DIR}/20260902-191602_5060ti-stock-suite-layernorm-r3_sweep.csv",
    "bgemm32": f"{SUITE_R3_DIR}/20260902-192026_5060ti-stock-suite-bgemm32-r3_sweep.csv",
    "bgemm64": f"{SUITE_R3_DIR}/20260902-192446_5060ti-stock-suite-bgemm64-r3_sweep.csv",
    "bgemm128": f"{SUITE_R3_DIR}/20260902-192906_5060ti-stock-suite-bgemm128-r3_sweep.csv",
    "bgemm256": f"{SUITE_R3_DIR}/20260902-193343_5060ti-stock-suite-bgemm256-r3_sweep.csv",
    "bgemm1024": f"{SUITE_R3_DIR}/20260902-193847_5060ti-stock-suite-bgemm1024-r3_sweep.csv",
    "attention": f"{SUITE_R3_DIR}/20260902-194351_5060ti-stock-suite-attention-r3_sweep.csv",
    "conv": f"{SUITE_R3_DIR}/20260902-194901_5060ti-stock-suite-conv-r3_sweep.csv",
    "gemm": f"{SUITE_R3_DIR}/20260902-195410_5060ti-stock-suite-gemm-r3_sweep.csv",
}

REPLICATES = (SUITE_R1_SWEEPS, SUITE_R2_SWEEPS, SUITE_R3_SWEEPS)


def _relativeSpread(values):
    """Range as a percentage of the mean - the statistic 5.4.5's table reports."""
    return 100.0 * (max(values) - min(values)) / mean(values)


def _sharedTargets(name):
    """Commanded frequencies present in all three replicates of one workload."""
    keyed = [sweep(table[name]) for table in REPLICATES]
    shared = set(keyed[0])
    for one in keyed[1:]:
        shared &= set(one)
    return keyed, sorted(shared)


def _spreadsFor(field):
    """Mean per-point spread of one measured field, averaged over the twelve workloads."""
    perWorkload = []
    for name in SUITE_R1_SWEEPS:
        keyed, targets = _sharedTargets(name)
        perWorkload.append(mean(_relativeSpread([k[t][field] for k in keyed]) for t in targets))
    return mean(perWorkload)


def _gainSpreads():
    """Per-workload range of the reported efficiency gain, in percentage POINTS not percent."""
    out = {}
    for name, relativePath in SUITE_R1_SWEEPS.items():
        gains = [suiteRowFigures(table[name])[1] for table in REPLICATES]
        out[name] = max(gains) - min(gains)
    return out


@claim("5.4.5-throughput-spread", PAPER, "5.4.5")
def replicateThroughputSpread():
    """Throughput is the quantity the project's existing ~0.76% figure describes."""
    return f"| throughput | **{_spreadsFor('throughput'):.2f}%** |"


@claim("5.4.5-power-spread", PAPER, "5.4.5")
def replicatePowerSpread():
    """Power, the term every efficiency figure divides by, and the dominant noise source."""
    return f"| power | **{_spreadsFor('power'):.2f}%** |"


@claim("5.4.5-efficiency-spread", PAPER, "5.4.5")
def replicateEfficiencySpread():
    """Efficiency tracks power rather than throughput - that is the section's whole point."""
    return f"| efficiency (throughput per watt) | **{_spreadsFor('efficiency'):.2f}%** |"


@claim("5.4.5-gain-spread", PAPER, "5.4.5")
def replicateGainSpread():
    """The derived gain, in percentage POINTS. Rendered to match the table's own wording."""
    return (f"| reported efficiency gain | **{mean(_gainSpreads().values()):.2f} percentage "
            f"points** |")


@claim("5.4.5-power-versus-throughput", PAPER, "5.4.5")
def powerIsTheDominantTerm():
    """The ratio the section leads with. Rendered as a bound so it states the direction."""
    factor = _spreadsFor("power") / _spreadsFor("throughput")
    return f"It reproduces {factor:.1f} times worse"


@claim("5.4.5-gain-range", PAPER, "5.4.5")
def gainSpreadRange():
    """Best and worst reproducing workloads. Both are named because the RANGE is the claim -
    a mean alone would hide that one workload moves eleven times as much as another."""
    spreads = _gainSpreads()
    best = min(spreads, key=spreads.get)
    worst = max(spreads, key=spreads.get)
    return (f"from {spreads[best]:.1f} points (`{best}`) to {spreads[worst]:.1f} points "
            f"(`{worst}`)")


@claim("5.4.5-anchor-refutation", PAPER, "5.4.5")
def topPointIsNotTheNoisiest():
    """The refuted hypothesis. Pinned because a claim that only recorded the conclusion would
    not fail if the underlying numbers moved enough to reverse it."""
    byTarget = {}
    for name in SUITE_R1_SWEEPS:
        keyed, targets = _sharedTargets(name)
        for target in targets:
            byTarget.setdefault(target, []).append(
                _relativeSpread([k[target]["throughput"] for k in keyed]))
    ordered = sorted(byTarget)
    top = mean(byTarget[ordered[-1]])
    rest = mean(mean(byTarget[t]) for t in ordered[:-1])
    worst = max(ordered, key=lambda t: mean(byTarget[t]))
    return (f"{ordered[-1]:.0f} MHz reproduces to {top:.2f}% against {rest:.2f}% averaged over "
            f"every other point, and the worst point is {worst:.0f} MHz at "
            f"{mean(byTarget[worst]):.2f}%")


# --------------------------------------------------------------------------------------
# The status header - the one place the auditor could not previously audit
#
# A council review of the paper found the header advertising "143 numbers are pinned" while the
# real count was 192. That is the failure this whole file exists to prevent, sitting in the
# paragraph that ADVERTISES the mechanism, and nothing caught it because nothing pinned it.
#
# The claim below is deliberately SELF-REFERENTIAL: it counts itself, so adding any future claim
# forces the header to be updated or the audit fails. That is the intended friction. It is also
# why the number in the paper is one higher than the count before this claim existed.
#
# IT IS ALSO GUARDED, and the first version of it broke CI for exactly the reason the guard now
# exists. claims_reference.py registers 24 claims ONLY when data/raw/ is present, and that
# dataset is gitignored and fetched rather than committed - so the registry totals 193 on a
# machine that has it and 169 on one that does not. An unguarded count renders whichever number
# the environment produces and fails wherever the paper disagrees, which is both CI legs of the
# "checks" job. The guard is the same condition claims_reference.py itself uses, so this claim
# registers exactly where the count it reports is the complete one: locally, and in the CI job
# named "V100 reference claims" that fetches the dataset before auditing.
#
# THE SKIP IS NOT A PASS, for the same reason that module says so: a green audit without the
# dataset has not checked this number either.
# --------------------------------------------------------------------------------------

def _referenceDataPresent():
    """Whether the V100 set is fetched, and therefore whether CLAIMS is the complete registry."""
    return (_REPO_ROOT / "data" / "raw" / "dataset_performance.csv").exists()


if _referenceDataPresent():
    @claim("header-pinned-count", PAPER)
    def headerPinnedCount():
        """The header's own advertised claim count, rendered from the live registry."""
        return f"**{len(CLAIMS)} numbers are pinned by `analysis/audit_claims.py`**"


# --------------------------------------------------------------------------------------
# 3.5 - the real driver crash of 2026-08-30
#
# WHY THIS DOES NOT USE stabilityRun(). That loader requires all four artifacts a completed run
# writes - protocol, session, iterations and samples - and this run has only the samples. The
# operator stopped it on seeing the crash, so neither JSON was ever written. That is not an
# inconvenience to work around; it is the fact 3.5 reports when it says the UNSTABLE verdict was
# reconstructed rather than emitted. A claim that quietly reached for the missing files would be
# asserting the run completed.
#
# The samples exist at all because the logger flushes each row as it writes it, which is what
# lets the record cover the four-second gap where sampling itself stopped.
# --------------------------------------------------------------------------------------

CRASH_SAMPLES = "data/stability-runs/20260830-123609_uv-875mv-3ghz_samples.csv"


def _crashSamples():
    """Every telemetry row of the crashed run, in order."""
    rows = []
    with open(_REPO_ROOT / CRASH_SAMPLES, encoding="utf-8-sig") as handle:
        import csv as _csv
        for raw in _csv.DictReader(handle):
            rows.append({
                "mhz": float(raw["sm_clock_mhz"]),
                "memory": float(raw["memory_clock_mhz"]),
                "watts": float(raw["power_draw_w"]),
                "util": float(raw["gpu_utilization_pct"]),
            })
    return rows


def _largestPowerDrop():
    """The consecutive pair with the steepest fall in power. Found rather than indexed, so the
    claim keeps pointing at the event and not at a row number that a re-export could shift."""
    rows = _crashSamples()
    pairs = zip(rows, rows[1:])
    return max(pairs, key=lambda pair: pair[0]["watts"] - pair[1]["watts"])


@claim("3.5-crash-signature", PAPER, "3.5")
def crashSignature():
    """The failure signature: power collapses while utilisation still reads 100%. Both samples are
    rendered because the CLAIM is that the counter did not move while the power did, which one
    number cannot express."""
    before, after = _largestPowerDrop()
    return (f"{before['watts']:.2f} W to {after['watts']:.2f} W in one second while the card still "
            f"reported {before['mhz']:.0f} MHz and {before['util']:.0f}% utilisation")


@claim("3.5-offsets-cleared", PAPER, "3.5")
def offsetsCleared():
    """The memory clock either side of the reset. 16301 is the +2500 offset, 13801 is stock, and
    the difference is the whole reason a run continued past this point would have been measuring
    something other than what its settings string claimed."""
    before, _ = _largestPowerDrop()
    final = _crashSamples()[-1]
    return f"read {before['memory']:.0f} MHz before the event and {final['memory']:.0f}"


# --------------------------------------------------------------------------------------
# 5.7.3 - the crossbar mechanism
#
# This is the largest original finding in the paper and it carried NO claims until 2026-09-04:
# its table was checked by eye when written and never again. The two extracts below are the
# distilled HWiNFO joins committed beside the sweeps they came from, and every figure 5.7.3
# quotes is recomputed from them here.
#
# The ratio is crossbar / ACHIEVED core clock, not crossbar / target. The card undershoots its
# lock at several of these points, and dividing by a clock it did not reach would understate the
# stock ratio at exactly the points where the argument needs it to be near unity.
# --------------------------------------------------------------------------------------

VOLT_DIR = "data/frequency-sweeps/membw-anomaly-20260819/"
VOLT_STOCK = VOLT_DIR + "20260820-211630_5060ti-stock-volt-membw_sweep_voltage.csv"
VOLT_TUNED = VOLT_DIR + "20260820-210822_5060ti-oc-volt-membw_sweep_voltage.csv"


def _voltageExtract(relativePath):
    """One distilled HWiNFO join, keyed by commanded target."""
    import csv as _csv
    out = {}
    with open(_REPO_ROOT / relativePath, encoding="utf-8-sig") as handle:
        for raw in _csv.DictReader(handle):
            out[int(raw["target"])] = {
                "achieved": float(raw["achieved"]),
                "throughput": float(raw["throughputGbs"]),
                "voltage": float(raw["voltage"]),
                "crossbar": float(raw["crossbar"]),
            }
    return out


def _ratios(relativePath):
    """Crossbar-to-core ratio at every point, ordered by target."""
    rows = _voltageExtract(relativePath)
    return [rows[t]["crossbar"] / rows[t]["achieved"] for t in sorted(rows)]


@claim("5.7.3-stock-ratio-band", PAPER, "5.7.3")
def stockRatioBand():
    """At stock the interconnect tracks the core. The BAND is the claim, not a midpoint."""
    values = _ratios(VOLT_STOCK)
    return f"its ratio to core clock holds between {min(values):.3f} and {max(values):.3f}"


@claim("5.7.3-ratio-collapse", PAPER, "5.7.3")
def ratioCollapse():
    """The headline: under the flattened curve the ratio falls away instead of holding. Rendered
    as first-to-lowest rather than max-to-min, because the CLAIM is a collapse with frequency and
    an unordered range would also match a curve that merely wobbled."""
    values = _ratios(VOLT_TUNED)
    return f"that ratio collapses from {values[0]:.3f} to {min(values):.3f}"


@claim("5.7.3-voltage-rise", PAPER, "5.7.3")
def voltageRise():
    """What the flattened curve actually does, in volts. Both numbers, because the contrast is
    the point - one configuration responds to frequency and the other does not."""
    stock = _voltageExtract(VOLT_STOCK)
    tuned = _voltageExtract(VOLT_TUNED)
    stockRise = max(r["voltage"] for r in stock.values()) - min(r["voltage"] for r in stock.values())
    tunedRise = max(r["voltage"] for r in tuned.values()) - min(r["voltage"] for r in tuned.values())
    return (f"stock core voltage rises {stockRise:.3f} V while the tuned card's rises "
            f"{tunedRise:.3f} V")


@claim("5.7.3-agree-where-voltages-agree", PAPER, "5.7.3")
def agreeWhereVoltagesAgree():
    """The control that makes the mechanism a measurement rather than a correlation: at the one
    point where both configurations sit at the same voltage, they deliver the same bandwidth."""
    stock = _voltageExtract(VOLT_STOCK)[1402]
    tuned = _voltageExtract(VOLT_TUNED)[1402]
    both = (stock["throughput"] + tuned["throughput"]) / 2.0
    return (f"at 1402 MHz both sit at {stock['voltage']:.3f} V\nand both deliver "
            f"~{both:.0f} GB/s")


# --------------------------------------------------------------------------------------
# The header's OTHER count
#
# The status header advertised "67 committed sweeps" while the repository held 112. Same defect
# as the claim count it sits beside, found the same way - by measuring instead of reading - and
# 24 of the missing 45 were added by suite replicates r2 and r3 alone.
#
# Counted from the filesystem rather than from git, because the audit has no git dependency and
# does not want one. That is only equivalent while nothing untracked lives under
# data/frequency-sweeps; it was verified equal (112 both ways, working tree clean) when this
# claim was written. Voltage extracts end _sweep_voltage.csv and are joins rather than sweeps,
# so the glob excludes them - there are 11, and counting them would inflate this by a tenth.
#
# NOT guarded on the reference dataset, unlike header-pinned-count: these CSVs are committed, so
# the number is the same with or without data/raw.
# --------------------------------------------------------------------------------------

@claim("header-sweep-count", PAPER)
def headerSweepCount():
    """The header's advertised sweep count, recomputed from the committed CSVs."""
    sweeps = [p for p in (_REPO_ROOT / "data" / "frequency-sweeps").rglob("*_sweep.csv")
              if not p.name.endswith("_sweep_voltage.csv")]
    return f"**{len(sweeps)} committed"
