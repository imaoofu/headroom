PLATEAU_BAND = (1402, 1867)   # the membw plateau: where the tuned card's crossbar is pinned
FULL_VOLT_BAND = (1402, 2100)  # every target in the tuned voltage extract


def _bandEnds(relativePath, band):
    """The lowest and highest rows whose COMMANDED target lies inside an inclusive band.

    Selecting on the commanded target rather than the achieved clock is not a detail: target
    1402 lands at 1400.6 MHz, so an achieved-clock filter silently drops the band's own floor.
    """
    rows = _voltageExtract(relativePath)
    targets = sorted(t for t in rows if band[0] <= t <= band[1])
    return rows[targets[0]], rows[targets[-1]]


@claim("3.3.2-crossbar-tracks-voltage-not-clock", PAPER, "3.3.2")
def crossbarTracksVoltageNotClock():
    """The evidence that the crossbar follows voltage, not the locked graphics clock."""
    low, high = _bandEnds(VOLT_TUNED, PLATEAU_BAND)
    if low["voltage"] != high["voltage"]:
        raise ValueError("voltage is not held constant across the plateau band")
    c = (high["achieved"] - low["achieved"]) / low["achieved"] * 100
    x = (high["crossbar"] - low["crossbar"]) / low["crossbar"] * 100
    return f"locking the graphics clock {c:.1f}% higher while voltage is held constant moves the crossbar {x:.1f}%"


@claim("3.3.2-stock-ratio-across-same-range", PAPER, "3.3.2")
def stockRatioAcrossSameRange():
    # "across the same range" fixes the window to PLATEAU_BAND, matching claim 1
    rows = _voltageExtract(VOLT_STOCK)
    targets = [t for t in sorted(rows) if PLATEAU_BAND[0] <= t <= PLATEAU_BAND[1]]
    r = sum(rows[t]["crossbar"] / rows[t]["achieved"] for t in targets) / len(targets)
    return f"the crossbar holds a near-constant {r:.2f} ratio to the graphics clock across the same range"


@claim("3.3.3-crossbar-elasticity", PAPER, "3.3.3")
def crossbarElasticity():
    """Which clock actually predicts membw throughput - the whole point of 3.3.3."""
    import math
    low, high = _bandEnds(VOLT_TUNED, FULL_VOLT_BAND)
    # log elasticity, not a percentage-change ratio; the two differ on this band
    gain = math.log(high["throughput"] / low["throughput"])
    a = gain / math.log(high["crossbar"] / low["crossbar"])
    b = gain / math.log(high["achieved"] / low["achieved"])
    return f"elasticity {a:.2f}, against {b:.2f} for the graphics clock"