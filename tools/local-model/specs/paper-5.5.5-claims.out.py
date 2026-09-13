@claim("5.5.5-power-gap-is-large", PAPER, "5.5.5")
def powerGapIsLarge():
    """A wrong zero-decimal power gap would silently pass a two-decimal 5.5.1 match."""
    # 5.5.1 pins the gap at two decimals; this zero-decimal rendering is the only one that matches 5.5.5.
    return f"The +{mean(_matched('power')):.0f}% matched-frequency power gap"


@claim("5.5.5-peak-difference-is-not", PAPER, "5.5.5")
def peakDifferenceIsNot():
    """A non-positive OC peak would make the 'not' prose false; fail loudly instead of rendering a negative."""
    ocPeak = _peak(OC_GEMM)
    silentPeak = _peak(SILENT_GEMM)
    diff = (ocPeak["throughput"] - silentPeak["throughput"]) / silentPeak["throughput"] * 100.0
    if diff <= 0:
        raise ValueError("OC peak throughput is not ahead of silent peak throughput")
    # The same figure appears in the abstract, 2.6, 5.5.1's table, and 5.7.6; only this exact wording is unique to 5.5.5.
    return f"the +{diff:.2f}% peak difference is not"


@claim("5.5.5-matched-coverage", PAPER, "5.5.5")
def matchedCoverage():
    """Wrong English count words (seven/thirteen) would pass a digit-only match; fail loudly on mismatch."""
    targets = _matchedTargets()
    lo = int(targets[0])
    hi = int(targets[-1])
    matchedCount = len(targets)
    totalCount = len(sweep(SILENT_GEMM))
    matchedWord = "seven" if matchedCount == 7 else str(matchedCount)
    totalWord = "thirteen" if totalCount == 13 else str(totalCount)
    # The band endpoints also appear in 5.5.3; the 'covers ... grid points' wording is unique to 5.5.5.
    return f"covers {matchedWord} of {totalWord} grid points, {lo}-{hi} MHz"