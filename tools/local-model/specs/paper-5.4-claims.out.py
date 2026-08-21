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
    return (f"at {lower['mhz']:.0f} MHz ({lowerEff:.2f}) sits marginally below "
            f"{higher['mhz']:.0f} MHz ({higherEff:.2f}), "
            f"breaking monotonicity by {gap:.1f}%")