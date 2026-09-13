TASK: add claims covering paper sections 3.3.2 and 3.3.3 to analysis/claims_consumer.py

Write Python only. It will be appended at MODULE LEVEL, so write at column 0. Do not modify
anything already in the file, do not write imports, do not repeat existing code.

## How a claim works

A claim function returns THE EXACT STRING the document must contain, computed from the CSVs.
The engine asserts it appears in docs/PAPER_DRAFT.md verbatim and **exactly once**. It stores no
expected number. **Matching twice is a FAILURE.**

    @claim("<id>", PAPER, "3.3.2")
    def someName():
        return f"...{value:.1f}..."

YOU HAVE NO TOOLS AND CANNOT READ ANY FILE. Write only the formula. You will never see, and must
never hardcode, the resulting numbers. Numbers below describe FORMAT and WINDOWS only.

Bold markers (`**`) and whitespace runs are normalised away. Do not render `**`.

## What already exists - use it, do not reimplement

    PAPER                        -> "docs/PAPER_DRAFT.md"
    VOLT_STOCK, VOLT_TUNED       -> path constants for two HWiNFO-joined membw extracts on the
                                    RTX 5060 Ti, stock and tuned
    _voltageExtract(relPath)     -> dict keyed by COMMANDED target (int). Each value is a dict
                                    with keys: achieved, throughput, voltage, crossbar
    claim                        -> the decorator

`math` is NOT imported in this file. Import it inside any function that needs it, the way
`_voltageExtract` does its own `import csv as _csv`.

## 🛑 EVERY WINDOW IS EXPLICIT, AND THAT IS THE POINT

This project has been bitten by aggregates whose frequency window was implicit - three figures
drawn from three different windows in one paragraph, each individually true. Both sections here
describe a band in prose without naming it, so **the band is given to you below and must appear
as a named module-level constant**, not as a bare literal inside a function.

Add exactly these two constants, with a comment on each saying what defines it:

    PLATEAU_BAND = (1402, 1867)   # the membw plateau: where the tuned card's crossbar is pinned
    FULL_VOLT_BAND = (1402, 2100) # every target in the tuned voltage extract

Write one helper, `_bandEnds(relativePath, band)`, returning the (lowest, highest) row dicts
whose commanded target lies within the inclusive band. Use it everywhere.

## The claims to write

Three claims. Use each id exactly.

1. `3.3.2-crossbar-tracks-voltage-not-clock`, section "3.3.2"

       locking the graphics clock <c>% higher while voltage is
       held constant moves the crossbar <x>%

   Over PLATEAU_BAND on VOLT_TUNED:
   - c = the rise in `achieved` from the low end to the high end, as a percentage, ONE decimal
   - x = the rise in `crossbar` across the same two rows, ONE decimal

   RAISE a ValueError if the two rows do not have equal `voltage` - the sentence says "while
   voltage is held constant", and if that stops being true the claim is measuring something else.

2. `3.3.2-stock-ratio-across-same-range`, section "3.3.2"

       the crossbar holds a near-constant <r>
       ratio to the graphics clock across the same range

   r = the MEAN crossbar/achieved ratio on VOLT_STOCK over PLATEAU_BAND, to TWO decimals.
   "across the same range" in the sentence is what fixes the window to the same band as claim 1;
   say so in the docstring.

   ⚠️ **This claim may not match the document, and you must not adjust it if it does not.** Write
   the mean over the stated band. A mismatch is a finding about the paper.

3. `3.3.3-crossbar-elasticity`, section "3.3.3"

       elasticity <a>, against <b> for the graphics clock

   Both over FULL_VOLT_BAND on VOLT_TUNED, as LOG elasticities - the log of the throughput ratio
   divided by the log of the clock ratio, between the two band ends:

       elasticity = log(throughputHigh / throughputLow) / log(clockHigh / clockLow)

   - a uses `crossbar` as the clock, b uses `achieved`. Both to TWO decimals.
   - ⚠️ A simple percentage-change ratio gives a visibly different answer here. Use the
     logarithmic form above and say in a comment that the two differ and which one this is.

## Style

- camelCase function names, not snake_case. Name the claim, not the section number.
- ASCII only.
- One-line docstring on each claim saying WHY it exists. Do not restate what the code does.

## THIS MATTERS

A claim's job is to state what the data says, NOT to make the audit green. Claim 2 is the case
to watch: write the honest mean even though it may disagree with the paper.

## Output

Return only the Python. No explanation before or after. No markdown fences.
