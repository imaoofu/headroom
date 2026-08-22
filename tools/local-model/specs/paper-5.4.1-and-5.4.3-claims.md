TASK: add claims covering paper sections 5.4.1 and 5.4.3 to analysis/claims_consumer.py

Write Python only. Append to the end of analysis/claims_consumer.py. Do not modify anything
already in that file, and do not modify analysis/audit_claims.py.

## How a claim works

audit_claims.py provides a decorator. A claim function returns THE EXACT STRING the document
must contain, computed from the CSVs. The engine asserts that string appears in the document
verbatim and exactly once. It stores no expected number anywhere.

    @claim("<id>", PAPER, "5.4.1")
    def someName():
        return f"...{value:.1f}..."

YOU DO NOT NEED TO READ ANY CSV, AND YOU HAVE NO TOOLS HERE. A claim is code that will be RUN
LATER by the audit, at which point it reads the CSVs itself. Your job is only to write the
formula. You will never see, and must never hardcode, the resulting numbers.

Helpers already in claims_consumer.py, use them, do not reimplement:

    sweep(path)         -> dict keyed by COMMANDED frequency (int target). Each row has keys:
                           target, mhz, throughput, power, unit, windowed, utilisation.
                           `throughput` is raw units per second, `power` is watts,
                           `utilisation` is percent or None, `windowed` is a boolean.
                           Rows whose lock overshot are already dropped.
    sweepRaw(path)      -> the same keying but EVERY row, including overshoots. Its rows have
                           target, mhz, power, throughput, lockHeld, missMhz, missDirection.
                           No windowed and no utilisation.
    PAPER               -> "docs/PAPER_DRAFT.md"

Bold markers (**) and runs of whitespace are both normalised away before matching, on the
document AND on what you return. So a claim MAY span a line break in the paper, and you do not
need to know where the paper wraps. Write the whole sentence.

## Source files

Add these four module-level constants, following the naming style already in the file. They sit
directly under data/frequency-sweeps/ with no subdirectory:

    GEMM_FINE_P1  = "20260816-124651_5060ti-gemm-fine-p1_sweep.csv"
    MEMBW_FINE_P1 = "20260816-125959_5060ti-membw-fine-p1_sweep.csv"
    MEMBW_FINE_P2 = "20260816-130549_5060ti-membw-fine-p2_sweep.csv"
    GEMM_FINE_P2  = "20260816-131140_5060ti-gemm-fine-p2_sweep.csv"

These are the four passes of the fine sweep: two workloads, two passes each, run in the order
gemm, membw, membw, gemm. Each has 13 points on the same target grid.

## A NOTE ON WHAT IS NOT HERE

Section 5.4.1 also reports fitted vertices and 95% confidence intervals. Those are NOT in this
task and must not be attempted. The intervals come from a bootstrap in analyze_fine_sweep.py
that draws from a single shared random generator consumed in run order, so a claim recomputing
one workload's interval in isolation would not reproduce the published number even with the
same seed. Covering them needs that module refactored to expose its summary, which is separate
work. Write only the three claims below.

## The claims to write

Three claims. Use the id given for each, exactly.

1. `5.4.1-point-count`, section "5.4.1"

   Across all four fine-sweep files, count three things: the total number of rows, how many held
   their locked clock, and how many had power windowed. Renders:

       All <total> points held their locked clock exactly, none overshot, and all <total> had
       power windowed to the benchmark's timed region.

   The same total appears twice.

   Two helpers are needed because neither carries everything:

     - `sweepRaw(path)` keeps every row including any that overshot, and its rows have a
       `lockHeld` boolean. Use it for the total and the lock count.
     - `sweep(path)` rows have a `windowed` boolean. Use it for the windowed count.

   The sentence asserts all three counts are equal. If they are not, the sentence is false, so
   RAISE a ValueError naming all three counts rather than rendering a sentence that misdescribes
   the data.

2. `5.4.3-decoupled-1897`, section "5.4.3"

   From MEMBW_FINE_P1 and MEMBW_FINE_P2 at target 1897. Renders:

       At 1897 MHz the two passes recorded utilisation of <p1 util>% and <p2 util>% <dash> and
       throughput of <p1 thru> and <p2 thru> GB/s.

   - utilisation to one decimal
   - throughput in GB/s to one decimal, so divide by 1e9
   - `<dash>` is an EM DASH, chr(0x2014), with a space either side. The source must stay ASCII,
     so produce it with chr().
   - the sentence ends with a full stop

3. `5.4.3-decoupled-1605`, section "5.4.3"

   From the same two files at target 1605. Renders:

       At 1605 MHz, <p1 util>% and <p2 util>% utilisation gave <p1 thru> and <p2 thru> GB/s

   Same number formatting. No dash and no trailing punctuation.

## THIS MATTERS

A claim's job is to state what the data says. It is NOT to make the audit green. If a claim you
write correctly does not match the document, that is a finding and the correct outcome; leave
the claim as the data dictates and do not adjust the rendering to force a match. Do not work
backwards from the document's text to a formula that reproduces it.

Where a task above tells you to RAISE rather than render, do that. A claim that quietly returns
a sentence the data does not support is worse than one that fails.

## Conventions

- camelCase for function names, not snake_case.
- Comments only for a non-obvious WHY, never to restate what a line does.
- ASCII only in the source, using chr() for the em dash.
- Open with a `# ---` banner naming the sections. Use the section titles, which are "Resolving
  the two optima" and "The sub-100% utilisation is a telemetry artifact, not lost work". Do not
  invent a description of what the sections conclude.

## Output

Return only the Python to append. No explanation before or after, no markdown fences.
