TASK: write a NEW module analysis/claims_reference.py holding claims for paper section 5.1

Write Python only. One complete module, starting with its docstring. Do not modify any other
file. Do not import from claims_consumer.py or claims_crosschip.py.

## Why this module is separate

claims_consumer.py holds RTX 5060 Ti claims; claims_crosschip.py holds RTX 3070 Ti claims. Both
read sweep CSVs this project collected. Section 5.1 is about a DIFFERENT dataset entirely - the
public V100 set, 33 workloads by 13 frequencies, published by others and never pooled with the
consumer data. It gets its own module for the same reason those two are apart: a shared constant
is how a claim silently reads the wrong hardware.

## How a claim works

audit_claims.py provides a decorator. A claim function returns THE EXACT STRING the document must
contain, computed from the data. The engine asserts that string appears in the document verbatim
and exactly once. It stores no expected number anywhere.

    from audit_claims import claim

    PAPER = "docs/PAPER_DRAFT.md"

    @claim("5.1-some-id", PAPER, "5.1")
    def someName():
        return f"...{value:.1f}..."

YOU HAVE NO TOOLS AND NO FILESYSTEM HERE. A claim is code that will be RUN LATER by the audit, at
which point it loads the data itself. Your job is only to write the formula. You will never see,
and must never hardcode, the resulting numbers.

## The data, and the helper you must reuse

analysis/characterize.py already reduces this dataset to exactly the quantities 5.1 reports. Use
it. Do not reimplement the reduction, and do not read CSVs directly.

    from load_data import loadDataset
    from characterize import buildWorkloadSummary

    summary = buildWorkloadSummary(loadDataset(validate=False))

`summary` is a pandas DataFrame, one row per workload, 33 rows. Columns you need:

    headroom_gap_pct              efficiency given up by running at stock instead of this
                                  workload's own optimum, already in percent
    performance_given_up_pct      performance cost of moving to the optimum, percent
    power_saved_pct               power saved at the optimum, percent
    optimal_frequency_mhz         int, that workload's most efficient frequency
    performance_at_lowest_frequency
                                  fraction of stock performance surviving at the lowest
                                  frequency in the sweep

Load it ONCE at module level into a constant, not inside each claim - the audit calls every claim
in one run and reloading per claim is wasted work.

`loadDataset(validate=False)` is deliberate: validation re-checks the published efficiency matrix
and is a startup cost the audit does not need. Pass it explicitly rather than relying on a default.

## What section 5.1 says, and the strings to pin

The paper currently reads, as one wrapped sentence:

    Running each of 33 workloads at stock (1530 MHz) rather than at its own efficiency optimum
    gives up a mean of **44.4%** efficiency (median 45.7%, range 15.1-62.8%), costing a mean
    13.7% performance and saving a mean 40.1% power.

Write these claims, one per id. Render ONLY the fragment named, not the whole sentence - a
smaller fragment is likelier to stay pinned when the prose is rewrapped.

    5.1-workload-count       the workload count and the mean gap, as it appears:
                             "33 workloads at stock (1530 MHz)" - count from the summary,
                             1530 is the dataset's reference frequency, import it as
                             REFERENCE_FREQUENCY_MHZ from load_data rather than typing 1530
    5.1-mean-gap             "**44.4%**" - one decimal, and the asterisks are part of the
                             string the document contains
    5.1-median-gap           "median 45.7%"
    5.1-gap-range            "range 15.1-62.8%"
    5.1-performance-cost     "costing a mean 13.7% performance"
    5.1-power-saved          "saving a mean 40.1% power"

## Two more claims, for section 5.2's mechanism sentence

Section 5.2's prose contains two numbers that come from this same summary rather than from any
model. Target section "5.2" for both.

The paper reads:

    952 MHz is optimal for 24 of 33 workloads (73%), so a constant already captures 43.56 of the
    44.4 available percentage points

    correlation -0.666 between performance retained at the lowest frequency and optimal frequency

    5.2-modal-frequency      "952 MHz is optimal for 24 of 33 workloads (73%)" - compute the
                             modal optimal frequency and its count from the summary; do not
                             assume 952 or 24, derive both. Percent is rounded to a whole number.
    5.2-sensitivity-correlation
                             "-0.666" - Pearson correlation between
                             performance_at_lowest_frequency and optimal_frequency_mhz.
                             See the sign warning below.

DO NOT write claims for 5.2's regret table (44.396%, 0.837%, 0.883%, and the match rates). Those
come from a leave-one-out Ridge fit, not from this summary, and putting a model fit inside the
audit is a decision that is not yours to make here. Leave them alone and say so in the docstring.

## Rules that will fail the audit if you break them

1. THE MINUS SIGN. The paper writes the correlation with U+2212 MINUS SIGN, not ASCII hyphen. The
   gap range uses EN DASH between 15.1 and 62.8. Render the character the document actually
   contains. Write the literal character in the f-string; do not use an escape.
2. Render the string the PAPER contains, not what characterize.py prints. characterize.py's own
   output formats the range differently. They are not the same string and only the paper matters.
3. A claim's job is to state what the data says, not to make the audit green. If a correctly
   written claim does not match the paper, that is a finding - the paper gets fixed, never the
   formula.
4. Match on a fragment, never a whole paragraph. Whitespace runs and bold markers are normalised
   on both sides, so a fragment may span a line break, but a long string is fragile for no gain.

## Conventions

camelCase for functions and variables, not snake_case. ASCII only in comments and identifiers -
the rendered claim strings are the sole exception, and only where rule 1 requires it. Comments
only for a non-obvious WHY. Module docstring explains what this module is and why it is separate,
in the style described at the top of this spec.

Output the complete module. No prose, no markdown fences.
