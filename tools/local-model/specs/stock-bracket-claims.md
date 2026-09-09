TASK: add claims covering data/frequency-sweeps/stock-bracket-20260909/README.md
to analysis/claims_consumer.py

Write Python only. Append to the end of analysis/claims_consumer.py. Do not modify anything
already in that file, and do not modify analysis/audit_claims.py.

## How a claim works

audit_claims.py provides a decorator. A claim function returns THE EXACT STRING the document
must contain, computed from the CSVs. The engine asserts that string appears in the document
verbatim and EXACTLY ONCE. It stores no expected number anywhere.

    @claim("<id>", BRACKET_README)
    def someName():
        return f"...{value:.2f}..."

YOU DO NOT NEED TO READ ANY CSV, AND YOU HAVE NO TOOLS HERE. A claim is code that will be RUN
LATER by the audit, at which point it reads the CSVs itself. Your job is only to write the
formula. You will never see, and must never hardcode, the resulting numbers.

⚠️ MATCHING TWICE IS A FAILURE, NOT A PASS. The engine reports `AMBIGUOUS`. This document
contains the string `56.99%` on three separate lines and `34.16%` on two, so the fragments below
have been chosen to be unique. Reproduce each fragment EXACTLY as given — do not shorten it, do
not reword it, do not drop the surrounding table pipes or backticks.

Helpers already in claims_consumer.py and audit_claims.py. Use them, do not reimplement:

    sweep(path)         -> dict keyed by COMMANDED frequency (int target). Each row is a dict
                           with keys: target, mhz, throughput, power, efficiency, unit.
                           `mhz` is the ACHIEVED core clock. `power` is watts.
    suiteRowFigures(path)
                        -> tuple (optimum MHz, efficiency gain %, performance cost %) for one
                           sweep. Element [1] is the efficiency gain this task needs.
    signedPct(ratio, minus="-")
                        -> "+30.1%" from a RATIO. Pass minus="−" where stated below.
    BRACKET_README      -> you must define this yourself, see Source files.

Bold markers (**) are stripped from both sides before matching, and runs of whitespace are
normalised, so do NOT render `**`. Everything else must match byte for byte.

## Source files

Add these four module-level constants at the point where you begin this section's block,
following the naming style already used in the file. Copy the paths EXACTLY. Do not invent,
abbreviate, correct or reorder any filename — every one of them exists as written.

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

⚠️ THE THREE DICTS HAVE IDENTICAL KEYS AND DIFFERENT VALUES. `BRACKET_STOCK` is the stock leg
and its filenames contain `-stock-suite-`; the other two are the tuned legs and contain
`-fulltune3030-`. Never mix a path from one dict into a computation meant for another. Every
computation below iterates over all twelve keys of the dict it names — never a subset.

## Shared helpers you should write

Two computations are reused. Define them as module-level functions with a leading underscore and
a prefix unique to this section, for example `_bracketMeanGain`. There are already helpers in
that file named `_optimum` and similar; a bare generic name would silently shadow one and break
unrelated claims. This has happened before and took a while to find.

    _bracketMeanGain(table)   -> the mean over the twelve sweeps in `table` of
                                 suiteRowFigures(path)[1].
    _bracketTuneGain()        -> the mean of _bracketMeanGain(BRACKET_TUNE_1) and
                                 _bracketMeanGain(BRACKET_TUNE_2).

⚠️ `_bracketTuneGain` is the mean OF THE TWO LEG MEANS, not the mean of all 24 sweeps pooled.
Both legs have twelve sweeps so the two happen to agree here, but write the leg-of-legs form —
it is what the document says and it stays correct if a leg is ever extended.

## The claims to write

Six claims. Use the id given for each, exactly.

1. `5.8-bracket-stock-mean`
   Fragment: `| stock (` + backtick + `r9` + backtick + `) | 56.99% |`
   written literally as:  | stock (`r9`) | 56.99% |
   Value: `_bracketMeanGain(BRACKET_STOCK)`, two decimal places, followed by a percent sign.

2. `5.8-bracket-tune-mean`
   Fragment, written literally:  | full tune (mean of `p4t1`, `p4t2`) | 34.16% |
   Value: `_bracketTuneGain()`, two decimals, percent sign.

3. `5.8-bracket-gap`
   Fragment, written literally:  | GAP | 22.83 points |
   Value: `_bracketMeanGain(BRACKET_STOCK) - _bracketTuneGain()`, two decimals, then the word
   `points`. It is positive; render it with no sign character at all.

4. `5.8-bracket-drift`
   Fragment, written literally:
       | this run, full tune `p4t1` → `p4t2`, ~2 h | −1.25 points |
   The arrow is U+2192 RIGHTWARDS ARROW and the minus is U+2212 MINUS SIGN. Neither is an ASCII
   character. Write them as the escapes `→` and `−` inside the f-string so the source
   stays ASCII, matching the style used elsewhere in the file.
   Value: `_bracketMeanGain(BRACKET_TUNE_2) - _bracketMeanGain(BRACKET_TUNE_1)`, two decimals.
   ⚠️ This value is NEGATIVE. Render the sign yourself: emit `−` followed by the ABSOLUTE
   value, so a sign flip in the data makes the claim fail rather than silently render `-1.25`
   with an ASCII hyphen that would not match. Do not use signedPct here.

5. `5.8-bracket-power-2010`
   Fragment, written literally:  | 2010 | 86.77 | 70.56 | +18.7% | 2002 / 2002 |
   Five values, all at COMMANDED target 2010, all averaged over the twelve workloads:
     - stock mean power, from `sweep(path)[2010]["power"]` over BRACKET_STOCK, two decimals.
     - tuned mean power: compute the twelve-workload mean for BRACKET_TUNE_1 and for
       BRACKET_TUNE_2 separately, then average those two. Two decimals.
     - the saving relative to STOCK. ⛔ **Do NOT use signedPct or deltaPct here.** signedPct
       renders a RATIO MINUS ONE, so handing it the saving-as-a-fraction 0.187 returns
       `-81.3%`, not `+18.7%`. Compute `(1.0 - tuned / stock) * 100.0` and render it yourself
       as `f"{saving:+.1f}%"`, then replace any ASCII hyphen with U+2212, because the negative
       rows of this table use U+2212. Keep the explicit `+` so a sign flip fails the claim.
       (An earlier version of this spec said to pass the fraction straight to signedPct. That
       instruction was wrong, the model followed it exactly, and the audit caught it — which is
       the whole point of the claims being self-checking.)
     - stock mean ACHIEVED clock (`["mhz"]`) over the twelve, rounded to an integer.
     - tuned mean achieved clock, computed as the average of the two legs' twelve-workload
       means, rounded to an integer.
   The two achieved clocks are separated by ` / `.

6. `5.8-bracket-r9-row`
   Fragment, written literally:  | r9 (this run) | 56.99% |
   Value: the same quantity as claim 1. Call `_bracketMeanGain(BRACKET_STOCK)` again rather
   than caching it in a module-level variable — every other claim in this file recomputes from
   source at audit time, and a cached value would be a stored expectation, which is the one
   thing the design forbids.

## Docstrings

Give every claim function a one-line docstring saying what it recomputes and from what, in the
style of the existing ones — for example "the stock leg's mean efficiency gain, recomputed from
its twelve sweep CSVs rather than read back from the table it checks."

## Output

Return ONLY Python source, in a single fenced code block, with no commentary before or after it.
It will be appended verbatim to analysis/claims_consumer.py.
