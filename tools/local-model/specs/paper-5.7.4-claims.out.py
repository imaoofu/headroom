# ---------------------------------------------------------------------------------------------
# 5.7.4 - the repaired curve restores the membw plateau
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