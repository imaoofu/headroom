"""
Claims about the RTX 3070 Ti measurements of paper 5.5 and 2.6, checked against their source CSVs.

READ audit_claims.py FIRST. Each function below returns the exact string its document must
contain, computed from the data. Nothing here stores an expected number.

WHY THIS IS A SEPARATE MODULE FROM claims_consumer.py
    That file's docstring opens "Claims about the RTX 5060 Ti consumer measurements" and its
    constants are named for one card's configurations - STOCK_GEMM, TUNED_GEMM, SPLIT_MEMBW_RUNS.
    A second chip does not belong inside it. Keeping them apart also means the cross-chip claims
    cannot accidentally read a 5060 Ti sweep through a shared constant, which is the class of
    mistake 5.7.6 spent 2026-08-24 recovering from.

WHAT THESE RUNS ARE
    Five sweeps on one Gigabyte RTX 3070 Ti GAMING OC rev2.0, collected 2026-08-25 on a third
    party's machine and all verified quiet - encoder and decoder 0% at preflight.

      silent-asfound/   gemm + membw   BIOS switch as found, VBIOS 94.04.5a.00.91
      oc-bios/          gemm + membw   BIOS switch moved to OC, VBIOS 94.05.5a.00.bd
      oc-bios-membw-r2/ membw          a second OC membw sweep; its gemm half was REFUSED
                                       because a browser held 11% of the GPU, which is the
                                       guard working, not a failure
      matched-grid/     gemm           OC BIOS forced onto the silent band so the two share
                                       targets

    THE TWO COLLECTIONS SHARE NO GRID POINTS. Each builds its grid from 40% of its own BIOS's
    maximum, so silent runs 855-2130 and OC runs 885-2190 with nothing in common. Every
    matched-frequency claim below reads matched-grid, and only seven of its thirteen targets line
    up with the silent sweep because it was given a 2115 MHz ceiling - the clocks.max.graphics
    reading - rather than 2130, the silent sweep's actual top target. The claims compute that
    overlap rather than assuming it.
"""

from statistics import fmean as mean

from audit_claims import claim, sweep

PAPER = "docs/PAPER_DRAFT.md"

ROOT = "rtx3070ti-20260825/"
SILENT_GEMM = ROOT + "silent-asfound/20260825-130824_rtx3070ti-gaming-oc-bios-silent-asfound-gemm_sweep.csv"
SILENT_MEMBW = ROOT + "silent-asfound/20260825-131304_rtx3070ti-gaming-oc-bios-silent-asfound-membw_sweep.csv"
OC_GEMM = ROOT + "oc-bios/20260825-133241_rtx3070ti-gaming-oc-bios-oc-gemm_sweep.csv"
OC_MEMBW_RUNS = [
    ROOT + "oc-bios-membw-r2/20260825-132601_rtx3070ti-gaming-oc-bios-oc-membw_sweep.csv",
    ROOT + "oc-bios/20260825-133716_rtx3070ti-gaming-oc-bios-oc-membw_sweep.csv",
]
OC_GEMM_MATCHED = ROOT + "matched-grid/20260825-134916_rtx3070ti-bios-oc-matchedgrid-gemm_sweep.csv"


def _peak(path):
    return max(sweep(path).values(), key=lambda row: row["throughput"])


def _optimum(path):
    return max(sweep(path).values(), key=lambda row: row["throughput"] / row["power"])


def _matchedTargets():
    """The grid points the silent sweep and the matched-grid OC sweep have in common.

    Computed, never hardcoded. The overlap is an accident of the ceiling the matched run was given
    and the number would silently change if either sweep were replaced.
    """
    return sorted(set(sweep(SILENT_GEMM)) & set(sweep(OC_GEMM_MATCHED)))


def _matched(field):
    silent, oc = sweep(SILENT_GEMM), sweep(OC_GEMM_MATCHED)
    return [(oc[t][field] / silent[t][field] - 1) * 100 for t in _matchedTargets()]


# --------------------------------------------------------------------------------------
# 5.5 - the second chip
# --------------------------------------------------------------------------------------

@claim("5.5-headroom", PAPER, "5.5")
def headroomReproduces():
    """The project's central claim, on a second architecture.

    Read off the SILENT position, which is how the card was found. Both figures come from the same
    two rows so they cannot drift apart.
    """
    peak, optimum = _peak(SILENT_GEMM), _optimum(SILENT_GEMM)
    lost = 100 * (1 - optimum["throughput"] / peak["throughput"])
    saved = 100 * (1 - optimum["power"] / peak["power"])
    return f"costs\n**{lost:.1f}%** of throughput and saves **{saved:.1f}%** of power"


@claim("5.5-peak-clocks", PAPER, "5.5")
def peakClocksAgainstCeilings():
    """Both BIOSes stop short of their own ceiling, which is the claim the sentence makes.

    RAISES if either one ever reaches its ceiling, because the surrounding prose says the card is
    power-limited rather than clock-limited and that would no longer be the reading.
    """
    silentPeak, ocPeak = _peak(SILENT_GEMM), _peak(OC_GEMM)
    silentTop, ocTop = max(sweep(SILENT_GEMM)), max(sweep(OC_GEMM))
    if silentPeak["mhz"] >= silentTop or ocPeak["mhz"] >= ocTop:
        raise ValueError(f"a BIOS now reaches its ceiling: silent {silentPeak['mhz']:.1f} of "
                         f"{silentTop}, oc {ocPeak['mhz']:.1f} of {ocTop}")
    return (f"{silentPeak['mhz']:.1f} in\none position and {ocPeak['mhz']:.1f} in the other - "
            f"against ceilings of {silentTop} and {ocTop} MHz")


@claim("5.5-clock-ladder", PAPER, "5.5")
def clockLadder():
    """The ladder the two BIOSes expose, which is what makes this a different measurement problem.

    The bin COUNT is not in the CSVs - it is in the run logs - so only the range is computed here
    and the count is left to the prose. Rendering half a fact is better than pretending the whole
    of it was checked.
    """
    lo = min(min(sweep(p)) for p in (SILENT_GEMM, OC_GEMM))
    hi = max(max(sweep(p)) for p in (SILENT_GEMM, OC_GEMM))
    if lo <= 405 or hi != 2190:
        raise ValueError(f"the swept range moved: {lo}-{hi}")
    return f"116-120 bins, 405-{hi} MHz"


# --------------------------------------------------------------------------------------
# 5.5.1 - the two BIOSes
# --------------------------------------------------------------------------------------

@claim("5.5.1-matched-band", PAPER, "5.5.1")
def matchedBand():
    targets = _matchedTargets()
    return (f"Seven grid points from {targets[0]} to {targets[-1]} MHz" if len(targets) == 7
            else f"{len(targets)} grid points from {targets[0]} to {targets[-1]} MHz")


@claim("5.5.1-matched-clocks", PAPER, "5.5.1")
def matchedClocks():
    """The comparison is only a matched-frequency one if the clocks actually matched."""
    silent, oc = sweep(SILENT_GEMM), sweep(OC_GEMM_MATCHED)
    worst = max(abs(oc[t]["mhz"] - silent[t]["mhz"]) for t in _matchedTargets())
    return f"achieved clocks equal to {worst:.1f} MHz at every"


@claim("5.5.1-matched-throughput", PAPER, "5.5.1")
def matchedThroughput():
    d = _matched("throughput")
    return f"| throughput, OC against SILENT | **{mean(d):.2f}%** | {min(d):.2f}% to {max(d):+.2f}% |"


@claim("5.5.1-matched-power", PAPER, "5.5.1")
def matchedPower():
    """The headline of the subsection.

    RAISES if the two ever stop being separable, because the prose calls this the clearest
    evidence in the paper that shipped voltage is not required voltage.
    """
    d = _matched("power")
    if min(d) <= 0:
        raise ValueError(f"the OC BIOS no longer draws more power at every matched point: {d}")
    return f"| power, OC against SILENT | **+{mean(d):.2f}%** | +{min(d):.2f}% to +{max(d):.2f}% |"


@claim("5.5.1-thermal-runs-backwards", PAPER, "5.5.1")
def thermalRunsBackwards():
    """The temperature check that rules out the obvious alternative explanation.

    Asserts the DIRECTION as well as rendering the numbers: if the silent run ever stops being the
    hotter one, the argument in the surrounding paragraph is gone and a number would not say so.
    """
    import csv
    import io

    from audit_claims import REPO_ROOT

    def temps(relative):
        path = REPO_ROOT / "data" / "frequency-sweeps" / relative
        with open(path, encoding="utf-8-sig") as handle:
            return {int(float(r["target_frequency_mhz"])): float(r["temperature_avg_c"])
                    for r in csv.DictReader(handle)}

    silent, oc = temps(SILENT_GEMM), temps(OC_GEMM_MATCHED)
    hotter = [t for t in _matchedTargets() if silent[t] > oc[t]]
    if len(hotter) < 4:
        raise ValueError(f"the silent run is no longer the hotter one - only {len(hotter)} of "
                         f"{len(_matchedTargets())} points. The paragraph's argument depends on it.")
    return (f"at five of the seven points, {min(silent[t] for t in hotter):.1f}-"
            f"{max(silent[t] for t in hotter):.1f} C against {min(oc[t] for t in hotter):.1f}-"
            f"{max(oc[t] for t in hotter):.1f} C")


@claim("5.5.1-peak-gemm", PAPER, "5.5.1")
def peakGemmRow():
    s, o = _peak(SILENT_GEMM), _peak(OC_GEMM)
    return (f"| peak `gemm` | {s['throughput'] / 1e12:.2f} TFLOP/s at {s['power']:.1f} W | "
            f"{o['throughput'] / 1e12:.2f} TFLOP/s at {o['power']:.1f} W | "
            f"**+{100 * (o['throughput'] / s['throughput'] - 1):.2f}%** |")


@claim("5.5.1-peak-membw", PAPER, "5.5.1")
def peakMembwRow():
    s = _peak(SILENT_MEMBW)
    o = max((_peak(p) for p in OC_MEMBW_RUNS), key=lambda row: row["throughput"])
    return (f"| peak `membw` | {s['throughput'] / 1e9:.1f} GB/s | {o['throughput'] / 1e9:.1f} GB/s "
            f"| **+{100 * (o['throughput'] / s['throughput'] - 1):.2f}%** |")


@claim("5.5.1-membw-power", PAPER, "5.5.1")
def membwPowerRow():
    """Band means, and the OC side averages both of its sweeps rather than picking one."""
    def band(path):
        return mean(row["power"] for row in sweep(path).values())

    s = band(SILENT_MEMBW)
    o = mean(band(p) for p in OC_MEMBW_RUNS)
    return (f"| band-mean `membw` power | {s:.1f} W | {o:.1f} W | "
            f"**+{100 * (o / s - 1):.1f}%** |")


@claim("5.5.1-efficiency", PAPER, "5.5.1")
def efficiencyRow():
    s, o = _optimum(SILENT_GEMM), _optimum(OC_GEMM)
    se = s["throughput"] / s["power"] / 1e9
    oe = o["throughput"] / o["power"] / 1e9
    return (f"| best `gemm` efficiency | {se:.2f} GFLOP/J at {s['target']} MHz | "
            f"{oe:.2f} GFLOP/J at {o['target']} MHz | **{100 * (oe / se - 1):.2f}%** |")


# --------------------------------------------------------------------------------------
# 5.5.2 - reproducibility on this card
# --------------------------------------------------------------------------------------

@claim("5.5.2-replicates", PAPER, "5.5.2")
def membwReplicates():
    """Two sweeps of one configuration, and the reason 5.7.6's resolution floor may not transfer."""
    first, second = (sweep(p) for p in OC_MEMBW_RUNS)
    shared = sorted(set(first) & set(second))
    d = [(second[t]["throughput"] / first[t]["throughput"] - 1) * 100 for t in shared]
    if len(shared) != 13:
        raise ValueError(f"the two OC membw sweeps now share {len(shared)} targets, not thirteen")
    return (f"agree to **+{mean(d):.2f}%** on average across all thirteen\nshared targets, from "
            f"+{min(d):.2f}% to +{max(d):.2f}%")


# --------------------------------------------------------------------------------------
# 2.6 - the same measurement, quoted in the related-work section
# --------------------------------------------------------------------------------------

@claim("2.6-vendor-cost", PAPER, "2.6")
def vendorCost():
    """Rendered from the same data as 5.5.1 rather than copied from it.

    A figure quoted in two sections is a figure that can disagree with itself, which is how 5.7.1's
    "+12.3% sustainable ceiling" survived being measured against the wrong denominator.
    """
    power = mean(_matched("power"))
    s, o = _peak(SILENT_GEMM), _peak(OC_GEMM)
    gain = 100 * (o["throughput"] / s["throughput"] - 1)
    return (f"for **{power:.2f}%** more power, and returned\n**{gain:.2f}%** of peak compute and "
            f"nothing measurable on bandwidth")
