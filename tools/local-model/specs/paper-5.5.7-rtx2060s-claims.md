TASK: add claims covering the RTX 2060 Super parts of paper section 5.5.7 to
analysis/claims_consumer.py

Write Python only. It will be appended to the end of that file at MODULE LEVEL, so write at
column 0. Do not modify anything already in the file, do not write imports, do not repeat
existing code.

## How a claim works

A claim function returns THE EXACT STRING the document must contain, computed from the CSVs.
The engine asserts that string appears in docs/PAPER_DRAFT.md verbatim and **exactly once**.
It stores no expected number. **Matching twice is a FAILURE, not a pass.**

YOU HAVE NO TOOLS AND CANNOT READ ANY FILE. A claim is code RUN LATER, at which point it reads
the CSVs itself. Write only the formula. You will never see, and must never hardcode, the
resulting numbers. Numbers below describe FORMAT and STRUCTURE only - never paste one into a
returned string.

Bold markers (`**`) and runs of whitespace are normalised away on both sides. Do not render `**`.

## What already exists in this file - use it, do not reimplement

    PAPER                        -> "docs/PAPER_DRAFT.md"
    sweep(path)                  -> dict keyed by COMMANDED target (int); rows have keys
                                    target, mhz, throughput, power, efficiency
    _medianSuiteOptimum(table)   -> median per-workload efficiency optimum, in MHz, for a dict
                                    of {workloadName: path}
    _suiteAgreement(table)       -> (howManyWorkloadsPickTheMedian, howManyThereAre)
    _voltageFloorValue(relPath)  -> the MINIMUM core voltage in a joined voltage extract
    _voltageFloorTop(relPath)    -> the highest achieved clock still AT that minimum
    claim                        -> the decorator

Paths are relative to data/frequency-sweeps/.

## The constants to add

Add these at module level, following the naming and layout style of SUITE_3060 already in the
file. Build the suite dict with a comprehension over the stamp table, the way SUITE_3070_SWEEPS
does, rather than writing twelve full paths out:

    SUITE_2060S -> "rtx2060s-20260912/20260912-124138_rtx2060super-suite/"
                   f"{stamp}_rtx2060super-suite-{name}_sweep.csv"

    name        stamp
    copy        20260912-124145
    reduce      20260912-124640
    softmax     20260912-125127
    layernorm   20260912-125620
    bgemm32     20260912-130111
    bgemm64     20260912-130628
    bgemm128    20260912-131127
    bgemm256    20260912-131626
    bgemm1024   20260912-132131
    attention   20260912-132644
    conv        20260912-133217
    gemm        20260912-133734

    _VOLT_2060S_LOWRANGE -> "rtx2060s-20260912/20260912-142900_rtx2060s-lowrange/"
                            "20260912-142900_rtx2060s-lowrange-gemm_sweep_voltage.csv"

⚠️ The voltage extract is the LOW-RANGE sweep, not the suite. The suite's own grid starts above
the floor and cannot see it; that is the whole reason a second sweep was run. Say so in a
comment on the constant.

## The one new helper you must write

    _voltageFloorTopWithin(relativePath, toleranceV)

Same as `_voltageFloorTop` but returning the highest achieved clock whose voltage is within
`toleranceV` of the minimum, rather than exactly at it. Read the CSV the same way
`_voltageFloorValue` does: csv.DictReader, encoding "utf-8-sig", columns "achieved" and
"voltage", both float. Use a small epsilon so floating point does not exclude an exact match.

This exists because this card's sensor moves in steps of about six millivolts, so "still at the
floor" and "one step off the floor" give different answers and the paper reports both. Put that
in the docstring.

## What section 5.5.7 says about this card

The rule under test is that a card's efficiency optimum sits at the highest frequency its
voltage curve reaches while still at the load floor. On this card the floor's exit is so gradual
that the rule cannot be decided: read strictly it predicts one grid point, read with one sensor
step of slack it predicts another, and the two disagree.

## The claims to write

Five claims. Use each id exactly.

1. `5.5.7-knee-2060s` - the table row. **Model it on `kneeThirtySixty()`**, which renders the
   RTX 3060's row and is already in this file.

       | RTX 2060 Super (Turing TU106) | <median> MHz | <strict> or <lenient> MHz <EMDASH> see below | <floorV> V | <a> of <n> |

   - median from `_medianSuiteOptimum(SUITE_2060S)`, zero decimals
   - strict from `_voltageFloorTop`, lenient from `_voltageFloorTopWithin` at 0.006 V, both
     zero decimals
   - floorV from `_voltageFloorValue`, THREE decimals
   - a, n from `_suiteAgreement(SUITE_2060S)`
   - `<EMDASH>` is U+2014. **The source file must be ASCII**, so produce it with `chr(0x2014)`,
     never as a literal character.

2. `5.5.7-2060s-strict-reading`

       the floor ends at <strict> MHz and the nearest grid point is <g>, one step below the measured <median>

   `<g>` is the member of the suite's commanded grid closest to `<strict>`. Get the grid from
   `sorted(sweep(SUITE_2060S["gemm"]))` - these are the commanded targets. All three values to
   zero decimals.

3. `5.5.7-2060s-lenient-reading`

       it ends at <lenient>, whose nearest grid point is <g2> exactly

   `<g2>` is the grid member closest to `<lenient>`. Note there is no "MHz" after `<lenient>`
   here; reproduce that.

   RAISE a ValueError if `<g2>` does not equal the median optimum. The word "exactly" in the
   sentence is the entire claim, and if it stops being true the prose is wrong.

4. `5.5.7-2060s-flat-band`

       0.631 V held across more than <span> MHz

   ⛔ **Render the LITERAL floor voltage from `_voltageFloorValue` to three decimals in place of
   the 0.631 shown above** - it is printed here only so you can see the sentence shape.

   `<span>` is the width of the region where voltage is EXACTLY at the floor: the highest
   achieved clock at the floor minus the lowest, to zero decimals.

   ⚠️ **This claim is EXPECTED TO FAIL, and that is why it is being written.** The paper's
   figure appears to have been taken from the full swept span rather than from the region
   actually at the floor value. Write the honest formula. Do not widen the definition, do not
   add a tolerance, and do not try to reproduce the paper's number. A mismatch here is a finding
   about the paper, which is the point.

5. `5.5.7-2060s-agreement`

       <a> of 12, against 6 to 10 elsewhere

   a from `_suiteAgreement(SUITE_2060S)`. The "12" and the "6 to 10" are prose about the other
   cards; render them literally and pin only `<a>`.

## Style

- camelCase function names, not snake_case. Name the claim, not the section number.
- ASCII only in the source. Non-ASCII output characters come from chr().
- One-line docstring on each claim saying WHY it exists. Do not restate what the code does.

## THIS MATTERS

A claim's job is to state what the data says, NOT to make the audit green. Claim 4 is the clear
case: the honest formula is the deliverable even though it will not match.

## Output

Return only the Python. No explanation before or after. No markdown fences.
