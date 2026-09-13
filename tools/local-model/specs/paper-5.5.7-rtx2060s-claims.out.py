SUITE_2060S = {
    name: (
        "rtx2060s-20260912/20260912-124138_rtx2060super-suite/"
        f"{stamp}_rtx2060super-suite-{name}_sweep.csv"
    )
    for name, stamp in {
        "copy": "20260912-124145",
        "reduce": "20260912-124640",
        "softmax": "20260912-125127",
        "layernorm": "20260912-125620",
        "bgemm32": "20260912-130111",
        "bgemm64": "20260912-130628",
        "bgemm128": "20260912-131127",
        "bgemm256": "20260912-131626",
        "bgemm1024": "20260912-132131",
        "attention": "20260912-132644",
        "conv": "20260912-133217",
        "gemm": "20260912-133734",
    }.items()
}

# The suite grid starts above the load floor and cannot see it, so the low-range sweep is the
# only extract that reaches the floor; the voltage floor claims must read it, not the suite.
_VOLT_2060S_LOWRANGE = (
    "rtx2060s-20260912/20260912-142900_rtx2060s-lowrange/"
    "20260912-142900_rtx2060s-lowrange-gemm_sweep_voltage.csv"
)


def _voltageFloorTopWithin(relativePath, toleranceV):
    """Like _voltageFloorTop but the highest clock within toleranceV of the floor.

    The TU106 sensor steps about six millivolts, so "still at the floor" and "one step off"
    give different answers and the paper reports both.
    """
    import csv
    with open(_REPO_ROOT / "data" / "frequency-sweeps" / relativePath,
              encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    floor = min(float(row["voltage"]) for row in rows)
    eps = 1e-9
    candidates = [
        float(row["achieved"])
        for row in rows
        if abs(float(row["voltage"]) - floor) <= toleranceV + eps
    ]
    return max(candidates)


@claim("5.5.7-knee-2060s", PAPER, "5.5.7")
def kneeTwentySixty():
    """Section 5.5.7 table row: the TU106 floor exit is too gradual for the rule to decide."""
    median = _medianSuiteOptimum(SUITE_2060S)
    strict = _voltageFloorTop(_VOLT_2060S_LOWRANGE)
    lenient = _voltageFloorTopWithin(_VOLT_2060S_LOWRANGE, 0.006)
    floorV = _voltageFloorValue(_VOLT_2060S_LOWRANGE)
    agree, total = _suiteAgreement(SUITE_2060S)
    emdash = chr(0x2014)
    return (
        "| RTX 2060 Super (Turing TU106) | "
        f"{median:.0f} MHz | {strict:.0f} or {lenient:.0f} MHz {emdash} see below | "
        f"{floorV:.3f} V | {agree} of {total} |"
    )


@claim("5.5.7-2060s-strict-reading", PAPER, "5.5.7")
def strictReadingTwentySixty():
    """Strict reading: the floor ends at the strict clock, one grid step below the median."""
    median = _medianSuiteOptimum(SUITE_2060S)
    strict = _voltageFloorTop(_VOLT_2060S_LOWRANGE)
    grid = sorted(sweep(SUITE_2060S["gemm"]))
    nearest = min(grid, key=lambda g: abs(g - strict))
    return (
        f"the floor ends at {strict:.0f} MHz and the nearest grid point is "
        f"{nearest:.0f}, one step below the measured {median:.0f}"
    )


@claim("5.5.7-2060s-lenient-reading", PAPER, "5.5.7")
def lenientReadingTwentySixty():
    """Lenient reading: one sensor step of slack lands the floor exactly on the median grid point."""
    median = _medianSuiteOptimum(SUITE_2060S)
    lenient = _voltageFloorTopWithin(_VOLT_2060S_LOWRANGE, 0.006)
    grid = sorted(sweep(SUITE_2060S["gemm"]))
    nearest = min(grid, key=lambda g: abs(g - lenient))
    if nearest != median:
        raise ValueError(
            f"lenient reading {nearest} does not equal the median optimum {median}"
        )
    return f"it ends at {lenient:.0f}, whose nearest grid point is {nearest:.0f} exactly"


@claim("5.5.7-2060s-flat-band", PAPER, "5.5.7")
def flatBandTwentySixty():
    """Honest width of the region actually at the floor; expected to fail against the paper's span."""
    floorV = _voltageFloorValue(_VOLT_2060S_LOWRANGE)
    import csv
    with open(_REPO_ROOT / "data" / "frequency-sweeps" / _VOLT_2060S_LOWRANGE,
              encoding="utf-8-sig") as handle:
        rows = list(csv.DictReader(handle))
    eps = 1e-9
    atFloor = [
        float(row["achieved"])
        for row in rows
        if abs(float(row["voltage"]) - floorV) <= eps
    ]
    span = max(atFloor) - min(atFloor)
    return f"{floorV:.3f} V held across more than {span:.0f} MHz"


@claim("5.5.7-2060s-agreement", PAPER, "5.5.7")
def agreementTwentySixty():
    """How many workloads pick the median on the TU106, against the other cards' range."""
    agree, _total = _suiteAgreement(SUITE_2060S)
    return f"{agree} of 12, against 6 to 10 elsewhere"