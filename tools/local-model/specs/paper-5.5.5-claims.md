TASK: add claims covering paper section 5.5.5 to analysis/claims_crosschip.py

Write Python only. It will be appended to the end of that file at MODULE LEVEL, so write at
column 0 with no extra indentation. Do not modify anything already in the file, do not write
imports, and do not repeat existing code.

## How a claim works

A claim function returns THE EXACT STRING the document must contain, computed from the CSVs.
The engine asserts that string appears in docs/PAPER_DRAFT.md verbatim and **exactly once**.
It stores no expected number. **Matching twice is a FAILURE, not a pass.**

    @claim("<id>", PAPER, "5.5.5")
    def someName():
        return f"...{value:.0f}..."

YOU HAVE NO TOOLS AND CANNOT READ ANY FILE. A claim is code RUN LATER, at which point it reads
the CSVs itself. Write only the formula. You will never see, and must never hardcode, the
resulting numbers. Numbers in this specification describe FORMAT and COLLISIONS only - never
paste one into a returned string.

Bold markers (`**`) and runs of whitespace are normalised away on both sides before matching.
Do not render `**`.

## What already exists in this file - use it, do not reimplement

    PAPER              -> "docs/PAPER_DRAFT.md"
    SILENT_GEMM        -> path constant, the "silent" BIOS position
    OC_GEMM            -> path constant, the "OC" BIOS position
    OC_GEMM_MATCHED    -> the OC sweep forced onto the silent band
    OC_MEMBW_RUNS      -> a LIST of the OC bandwidth sweeps
    sweep(path)        -> dict keyed by COMMANDED target (int). Rows are dicts with keys
                          target, mhz, throughput, power, unit.
    _peak(path)        -> the highest-THROUGHPUT row of that sweep
    _matchedTargets()  -> sorted list of targets SILENT_GEMM and OC_GEMM_MATCHED share
    _matched(field)    -> list of per-target percentage differences, OC against silent, for
                          that field. Already a percentage: 23.11 means +23.11%.
    mean               -> statistics.fmean, imported as `mean`
    claim              -> the decorator

## What section 5.5.5 is

It is the Limits subsection for the two-BIOS study on one RTX 3070 Ti. It states which of the
section's numbers are large enough to survive the study's own noise and which are not. Wrong
numbers in a Limits section are the worst kind, which is why it is being pinned.

## ⚠️ THE COLLISIONS - read before writing any f-string

Every figure in 5.5.5 already appears elsewhere in the paper. The surrounding WORDS are what
make each claim match once. Reproduce them exactly.

1. The matched power gap is pinned in 5.5.1 at TWO decimals. **5.5.5 rounds it to ZERO
   decimals**, so rendering the precise value will not match at all.
2. The peak difference figure appears in the abstract, in 2.6, in 5.5.1's table and again in
   5.7.6 about something unrelated. Five occurrences.
3. The band endpoints also appear in 5.5.3.

## The claims to write

Three claims. Use each id exactly.

1. `5.5.5-power-gap-is-large`

       The +<g>% matched-frequency power gap

   g = mean of `_matched("power")`, to ZERO decimals, with a literal "+" before it.

2. `5.5.5-peak-difference-is-not`

       the +<p>% peak difference is not

   p = the OC peak throughput against the silent peak throughput, as a percentage, to TWO
   decimals, with a literal "+". Use `_peak(OC_GEMM)` and `_peak(SILENT_GEMM)`.

   RAISE a ValueError if that difference is not positive - the sentence asserts the OC position
   is nominally ahead, and if it ever goes negative the prose is wrong rather than the number.

3. `5.5.5-matched-coverage`

       covers seven of thirteen grid points, <lo>-<hi> MHz

   - lo and hi are the first and last of `_matchedTargets()`, as integers, joined by an ASCII
     hyphen.
   - **"seven" and "thirteen" are English words in the document, not digits.** Follow the
     pattern `matchedBand()` already uses in this file: emit the word when the computed count
     is that value, and fall back to the digit otherwise, so the claim fails loudly rather than
     silently rendering a wrong word. The counts are `len(_matchedTargets())` and
     `len(sweep(SILENT_GEMM))`.

## Style

- camelCase function names, not snake_case. Name the claim, not the section number.
- ASCII only.
- One-line docstring on each claim saying WHY it exists - what would go unnoticed without it.
  Do not restate what the code does.
- Where you handle a collision, say so in a short comment naming the competing location.

## THIS MATTERS

A claim's job is to state what the data says, NOT to make the audit green. If a correctly
written claim does not match the paper, that is a finding about the paper. Never adjust a
formula to chase a string.

## Output

Return only the Python. No explanation before or after. No markdown fences.
