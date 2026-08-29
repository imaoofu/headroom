"""Claims for paper section 5.1 (and two 5.2 mechanism numbers) over the public V100 set.

This module is separate from claims_consumer.py and claims_crosschip.py on purpose: those hold
claims over the consumer sweep CSVs this project collected, whereas section 5.1 is about the
public V100 dataset (33 workloads by 13 frequencies) published by others and never pooled with the
consumer data. A shared constant is how a claim silently reads the wrong hardware, so each dataset
keeps its own module.

The summary is built once at module level; the audit calls every claim in one run, so reloading per
claim is wasted work.

Deliberately NOT covered here: section 5.2's regret table (44.396%, 0.837%, 0.883% and the match
rates). Those come from a leave-one-out Ridge fit, not from this summary, and putting a model fit
inside the audit is a decision not made here.

WHY THIS MODULE CAN REGISTER NOTHING
    Every claim here needs data/raw/, which is gitignored and fetched by scripts/Get-Dataset.ps1.
    An unguarded load raises FileNotFoundError at import and takes the WHOLE audit down with it -
    all 129 claims, not just these 8 - because the audit imports its claims modules eagerly. So a
    missing dataset registers nothing and says so, matching what
    models/test_predict_constrained_frequency.py already does for the same data.

    THE SKIP IS NOT A PASS. A green audit on a machine that never fetched the dataset has not
    checked section 5.1 at all. CI is such a machine today, so the reference half of this project
    is exactly the half CI does not cover. Read the notice, not the tick.
"""

from audit_claims import claim
from load_data import loadDataset, REFERENCE_FREQUENCY_MHZ
from characterize import buildWorkloadSummary

PAPER = "docs/PAPER_DRAFT.md"

try:
    # validate=False: the published efficiency matrix re-check is a startup cost the audit does
    # not need.
    SUMMARY = buildWorkloadSummary(loadDataset(validate=False))
except FileNotFoundError:
    SUMMARY = None

if SUMMARY is None:
    print("  [SKIP] claims_reference: the public V100 dataset is not downloaded - run "
          "scripts/Get-Dataset.ps1. Section 5.1 is NOT audited in this run.")
else:

    @claim("5.1-workload-count", PAPER, "5.1")
    def workloadCount():
        return f"{len(SUMMARY)} workloads at stock ({REFERENCE_FREQUENCY_MHZ} MHz)"

    @claim("5.1-mean-gap", PAPER, "5.1")
    def meanGap():
        # The number alone is not an anchor: bold markers are normalised away on both sides, so
        # "44.4%" matches eight places in the paper. The surrounding words are what pin the line.
        return f"a mean of {SUMMARY['headroom_gap_pct'].mean():.1f}% efficiency"

    @claim("5.1-median-gap", PAPER, "5.1")
    def medianGap():
        return f"median {SUMMARY['headroom_gap_pct'].median():.1f}%"

    @claim("5.1-gap-range", PAPER, "5.1")
    def gapRange():
        # The paper uses an EN DASH between the two endpoints, not a hyphen.
        return (f"range {SUMMARY['headroom_gap_pct'].min():.1f}"
                f"–{SUMMARY['headroom_gap_pct'].max():.1f}%")

    @claim("5.1-performance-cost", PAPER, "5.1")
    def performanceCost():
        return f"costing a mean {SUMMARY['performance_given_up_pct'].mean():.1f}% performance"

    @claim("5.1-power-saved", PAPER, "5.1")
    def powerSaved():
        return f"saving a mean {SUMMARY['power_saved_pct'].mean():.1f}% power"

    @claim("5.2-modal-frequency", PAPER, "5.2")
    def modalFrequency():
        counts = SUMMARY["optimal_frequency_mhz"].value_counts()
        modalMhz = int(counts.idxmax())
        modalCount = int(counts.max())
        percent = round(100.0 * modalCount / len(SUMMARY))
        return f"{modalMhz} MHz is optimal for {modalCount} of {len(SUMMARY)} workloads ({percent}%)"

    @claim("5.2-sensitivity-correlation", PAPER, "5.2")
    def sensitivityCorrelation():
        correlation = SUMMARY["performance_at_lowest_frequency"].corr(
            SUMMARY["optimal_frequency_mhz"])
        # The paper writes the sign with U+2212 MINUS SIGN, not an ASCII hyphen.
        sign = "−" if correlation < 0 else ""
        # The bare figure appears twice - here and again in 5.4.1's discussion - so the anchor
        # carries the words that distinguish this occurrence from that one.
        return f"correlation {sign}{abs(correlation):.3f} between performance retained"
