BRACKET_README = "data/frequency-sweeps/stock-bracket-20260909/README.md"

BRACKET_TUNE_1 = {
    "copy": "stock-bracket-20260909/20260909-103757_5060ti-fulltune3030-suite-copy-p4t1_sweep.csv",
    "reduce": "stock-bracket-20260909/20260909-104157_5060ti-fulltune3030-suite-reduce-p4t1_sweep.csv",
    "softmax": "stock-bracket-20260909/20260909-104610_5060ti-fulltune3030-suite-softmax-p4t1_sweep.csv",
    "layernorm": "stock-bracket-20260909/20260909-105006_5060ti-fulltune3030-suite-layernorm-p4t1_sweep.csv",
    "bgemm32": "stock-bracket-20260909/20260909-105408_5060ti-fulltune3030-suite-bgemm32-p4t1_sweep.csv",
    "bgemm64": "stock-bracket-20260909/20260909-105805_5060ti-fulltune3030-suite-bgemm64-p4t1_sweep.csv",
    "bgemm128": "stock-bracket-20260909/20260909-110202_5060ti-fulltune3030-suite-bgemm128-p4t1_sweep.csv",
    "bgemm256": "stock-bracket-20260909/20260909-110624_5060ti-fulltune3030-suite-bgemm256-p4t1_sweep.csv",
    "bgemm1024": "stock-bracket-20260909/20260909-111109_5060ti-fulltune3030-suite-bgemm1024-p4t1_sweep.csv",
    "attention": "stock-bracket-20260909/20260909-111555_5060ti-fulltune3030-suite-attention-p4t1_sweep.csv",
    "conv": "stock-bracket-20260909/20260909-112047_5060ti-fulltune3030-suite-conv-p4t1_sweep.csv",
    "gemm": "stock-bracket-20260909/20260909-112537_5060ti-fulltune3030-suite-gemm-p4t1_sweep.csv",
}

BRACKET_STOCK = {
    "copy": "stock-bracket-20260909/20260909-114339_5060ti-stock-suite-copy-r9_sweep.csv",
    "reduce": "stock-bracket-20260909/20260909-114746_5060ti-stock-suite-reduce-r9_sweep.csv",
    "softmax": "stock-bracket-20260909/20260909-115159_5060ti-stock-suite-softmax-r9_sweep.csv",
    "layernorm": "stock-bracket-20260909/20260909-115605_5060ti-stock-suite-layernorm-r9_sweep.csv",
    "bgemm32": "stock-bracket-20260909/20260909-120014_5060ti-stock-suite-bgemm32-r9_sweep.csv",
    "bgemm64": "stock-bracket-20260909/20260909-120420_5060ti-stock-suite-bgemm64-r9_sweep.csv",
    "bgemm128": "stock-bracket-20260909/20260909-120826_5060ti-stock-suite-bgemm128-r9_sweep.csv",
    "bgemm256": "stock-bracket-20260909/20260909-121250_5060ti-stock-suite-bgemm256-r9_sweep.csv",
    "bgemm1024": "stock-bracket-20260909/20260909-121737_5060ti-stock-suite-bgemm1024-r9_sweep.csv",
    "attention": "stock-bracket-20260909/20260909-122227_5060ti-stock-suite-attention-r9_sweep.csv",
    "conv": "stock-bracket-20260909/20260909-122719_5060ti-stock-suite-conv-r9_sweep.csv",
    "gemm": "stock-bracket-20260909/20260909-123211_5060ti-stock-suite-gemm-r9_sweep.csv",
}

BRACKET_TUNE_2 = {
    "copy": "stock-bracket-20260909/20260909-124707_5060ti-fulltune3030-suite-copy-p4t2_sweep.csv",
    "reduce": "stock-bracket-20260909/20260909-125108_5060ti-fulltune3030-suite-reduce-p4t2_sweep.csv",
    "softmax": "stock-bracket-20260909/20260909-125521_5060ti-fulltune3030-suite-softmax-p4t2_sweep.csv",
    "layernorm": "stock-bracket-20260909/20260909-125916_5060ti-fulltune3030-suite-layernorm-p4t2_sweep.csv",
    "bgemm32": "stock-bracket-20260909/20260909-130318_5060ti-fulltune3030-suite-bgemm32-p4t2_sweep.csv",
    "bgemm64": "stock-bracket-20260909/20260909-130714_5060ti-fulltune3030-suite-bgemm64-p4t2_sweep.csv",
    "bgemm128": "stock-bracket-20260909/20260909-131111_5060ti-fulltune3030-suite-bgemm128-p4t2_sweep.csv",
    "bgemm256": "stock-bracket-20260909/20260909-131531_5060ti-fulltune3030-suite-bgemm256-p4t2_sweep.csv",
    "bgemm1024": "stock-bracket-20260909/20260909-132016_5060ti-fulltune3030-suite-bgemm1024-p4t2_sweep.csv",
    "attention": "stock-bracket-20260909/20260909-132502_5060ti-fulltune3030-suite-attention-p4t2_sweep.csv",
    "conv": "stock-bracket-20260909/20260909-132955_5060ti-fulltune3030-suite-conv-p4t2_sweep.csv",
    "gemm": "stock-bracket-20260909/20260909-133444_5060ti-fulltune3030-suite-gemm-p4t2_sweep.csv",
}


def _bracketMeanGain(table):
    return sum(suiteRowFigures(path)[1] for path in table.values()) / len(table)


def _bracketTuneGain():
    return (_bracketMeanGain(BRACKET_TUNE_1) + _bracketMeanGain(BRACKET_TUNE_2)) / 2.0


@claim("5.8-bracket-stock-mean", BRACKET_README)
def bracketStockMean():
    """the stock leg's mean efficiency gain, recomputed from its twelve sweep CSVs rather than read back from the table it checks."""
    return f"| stock (`r9`) | {_bracketMeanGain(BRACKET_STOCK):.2f}% |"


@claim("5.8-bracket-tune-mean", BRACKET_README)
def bracketTuneMean():
    """the full-tune mean of the two tuned legs' mean efficiency gains, recomputed from their sweep CSVs rather than read back from the table it checks."""
    return f"| full tune (mean of `p4t1`, `p4t2`) | {_bracketTuneGain():.2f}% |"


@claim("5.8-bracket-gap", BRACKET_README)
def bracketGap():
    """the gap between the stock and full-tune mean efficiency gains, recomputed from the sweep CSVs rather than read back from the table it checks."""
    return f"| GAP | {_bracketMeanGain(BRACKET_STOCK) - _bracketTuneGain():.2f} points |"


@claim("5.8-bracket-drift", BRACKET_README)
def bracketDrift():
    """the drift between the two tuned legs' mean efficiency gains, recomputed from their sweep CSVs rather than read back from the table it checks."""
    return f"| this run, full tune `p4t1` \u2192 `p4t2`, ~2 h | \u2212{abs(_bracketMeanGain(BRACKET_TUNE_2) - _bracketMeanGain(BRACKET_TUNE_1)):.2f} points |"


@claim("5.8-bracket-power-2010", BRACKET_README)
def bracketPower2010():
    """the 2010 MHz power and achieved-clock figures for stock and full tune, recomputed from the sweep CSVs rather than read back from the table it checks."""
    stockPower = sum(sweep(path)[2010]["power"] for path in BRACKET_STOCK.values()) / len(BRACKET_STOCK)
    tunePower = (sum(sweep(path)[2010]["power"] for path in BRACKET_TUNE_1.values()) / len(BRACKET_TUNE_1)
                 + sum(sweep(path)[2010]["power"] for path in BRACKET_TUNE_2.values()) / len(BRACKET_TUNE_2)) / 2.0
    stockClock = sum(sweep(path)[2010]["mhz"] for path in BRACKET_STOCK.values()) / len(BRACKET_STOCK)
    tuneClock = (sum(sweep(path)[2010]["mhz"] for path in BRACKET_TUNE_1.values()) / len(BRACKET_TUNE_1)
                 + sum(sweep(path)[2010]["mhz"] for path in BRACKET_TUNE_2.values()) / len(BRACKET_TUNE_2)) / 2.0
    return f"| 2010 | {stockPower:.2f} | {tunePower:.2f} | {signedPct(1.0 - tunePower / stockPower)} | {round(stockClock)} / {round(tuneClock)} |"


@claim("5.8-bracket-r9-row", BRACKET_README)
def bracketR9Row():
    """the stock leg's mean efficiency gain, recomputed from its twelve sweep CSVs rather than read back from the table it checks."""
    return f"| r9 (this run) | {_bracketMeanGain(BRACKET_STOCK):.2f}% |"