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

from audit_claims import claim, deltaPct, signedPct, sweep, sweepRaw, voltageJoin

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

def _powerRow171(target):
    stock, tuned, memonly = sweep(STOCK_GEMM), sweep(TUNED_GEMM), sweep(MEMONLY_GEMM)
    # No ** around the tuned column even though the document bolds it: audit_claims.normalise
    # strips emphasis from both sides, so rendering it here would be decoration only.
    return (f"| {target} MHz | {deltaPct(tuned[target]['power'], stock[target]['power'])} "
            f"| {deltaPct(memonly[target]['power'], stock[target]['power'])} |")


for _target in MATCHED_TARGETS:
    claim(f"5.7.1-power-{_target}", PAPER, "5.7.1")(
        lambda target=_target: _powerRow171(target))


@claim("5.7.1-memonly-within-3pct", PAPER, "5.7.1")
def memonlyReproducesStockPower():
    """The claim is a bound, so the rendering has to be a bound too: the sentence says "within
    3%" and what is checked is that 3 is the smallest whole percent that still contains every
    matched point."""
    stock, memonly = sweep(STOCK_GEMM), sweep(MEMONLY_GEMM)
    worst = max(abs(memonly[t]["power"] / stock[t]["power"] - 1.0) * 100.0
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

GEMM_FLOOR15 = "20260816-001048_5060ti-gemm-floor15_sweep.csv"
MEMBW_FLOOR15 = "20260816-001734_5060ti-membw-floor15_sweep.csv"


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
