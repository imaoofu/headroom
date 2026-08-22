# --------------------------------------------------------------------------------------
# 5.4.1 - Resolving the two optima
# 5.4.3 - The sub-100% utilisation is a telemetry artifact, not lost work
# --------------------------------------------------------------------------------------

GEMM_FINE_P1 = "20260816-124651_5060ti-gemm-fine-p1_sweep.csv"
MEMBW_FINE_P1 = "20260816-125959_5060ti-membw-fine-p1_sweep.csv"
MEMBW_FINE_P2 = "20260816-130549_5060ti-membw-fine-p2_sweep.csv"
GEMM_FINE_P2 = "20260816-131140_5060ti-gemm-fine-p2_sweep.csv"


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