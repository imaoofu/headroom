TASK: add claims covering paper section 5.7.4 to analysis/claims_consumer.py

Write Python only. Append to the end of analysis/claims_consumer.py. Do not modify anything
already in that file, and do not modify analysis/audit_claims.py.

## How a claim works

audit_claims.py provides a decorator. A claim function returns THE EXACT STRING the document
must contain, computed from the CSVs. The engine asserts that string appears in the document
verbatim and exactly once. It stores no expected number anywhere.

    @claim("<id>", PAPER, "5.7.4")
    def someName():
        return f"...{value:.1f}..."

YOU DO NOT NEED TO READ ANY CSV, AND YOU HAVE NO TOOLS HERE. A claim is code that will be RUN
LATER by the audit, at which point it reads the CSVs itself. Your job is only to write the
formula. You will never see, and must never hardcode, the resulting numbers.

Helpers already in claims_consumer.py, use them, do not reimplement:

    sweep(path)         -> dict keyed by COMMANDED frequency (int target). Each row is a dict
                           with keys: target, mhz, throughput, power, unit. `throughput` is raw
                           units per second - for membw that is BYTES per second, so divide by
                           1e9 to render GB/s. `power` is watts.
    voltageJoin(path)   -> dict keyed by COMMANDED frequency (int target). Each row is a dict
                           with keys: target, mhz, voltage, crossbar. `voltage` is volts,
                           `crossbar` is MHz. Use row["mhz"] as the ACHIEVED core clock.
    signedPct(ratio, minus="-")
                        -> "+30.1%" from a RATIO.
    deltaPct(new, old, minus="-")
                        -> signedPct(new / old, minus=minus)
    PAPER               -> "docs/PAPER_DRAFT.md"

Bold markers (**) are stripped from both sides before matching, so do not render them.

## Source files

Add these four module-level constants, following the naming style already in the file.

    FIXED_MEMBW        = "membw-anomaly-20260819/20260820-215336_5060ti-curvefixed-membw_sweep.csv"
    FIXED_MEMBW_VOLTS  = "membw-anomaly-20260819/20260820-215336_5060ti-curvefixed-membw_sweep_voltage.csv"
    TUNED_MEMBW_13PT   = "oc-comparison-20260819/20260819-162516_5060ti-oc-membw-stock_sweep.csv"
    TUNED_MEMBW_VOLTS  = "membw-anomaly-20260819/20260820-210822_5060ti-oc-volt-membw_sweep_voltage.csv"

⚠️ READ THIS BEFORE USING THE FOURTH FILE. `TUNED_MEMBW_13PT` has the word "stock" in its
filename and is NOT a stock run. It is the fully tuned card. The sweep tool used to paste
"-stock" into every session label regardless of configuration; that bug is fixed but the
filename it produced is permanent. Do not "correct" it, and do not substitute a differently
named file that looks more like what you expect.

⚠️ THE TWO CONFIGURATIONS WERE SWEPT ON DIFFERENT GRIDS IN SOME RUNS. The four files above are
the ones that match. Specifically:

    FIXED_MEMBW, FIXED_MEMBW_VOLTS, TUNED_MEMBW_13PT
        13-point grid: 1237 1395 1545 1702 1852 2010 2167 2317 2475 2625 2782 2932 3090
    TUNED_MEMBW_VOLTS
        10-point grid: 1402 1477 1560 1635 1710 1792 1867 1942 2025 2100

There is ALSO a 10-point tuned membw sweep in the repository. It is not used here. If a target
key you expect is missing, you have reached for the wrong file - do not fall back to a nearby
frequency, and do not interpolate. Every target named below exists in the file it is read from.

## The claims to write

Seven claims. Use the id given for each, exactly.

The document is hard-wrapped at ~100 characters, so each claim must pin a fragment that stays on
ONE line. The exact fragment is given for each. Reproduce its wording exactly, substituting the
computed numbers - do not reword, do not add or remove punctuation, and note that the document
uses ASCII hyphens throughout this section, not en dashes or minus signs.

1. `5.7.4-voltage-rises`
   Fragment: `0.720 V at 1545 MHz through 0.840 V at 2010, against a`
   From FIXED_MEMBW_VOLTS. The two voltages are at targets 1545 and 2010. Render each to three
   decimal places. The two frequencies are the COMMANDED targets, written as integers, not the
   achieved clocks.

2. `5.7.4-crossbar-restored`
   Fragment: `flat 0.720 V on the tuned card - and the crossbar-to-core ratio returns to 0.939-0.967 from 0.726.`
   Three numbers, and they come from two files.
     - The flat tuned voltage: TUNED_MEMBW_VOLTS at target 1867, three decimals.
     - The restored ratio range: from FIXED_MEMBW_VOLTS, crossbar / mhz at targets 1545, 1852
       and 2010 ONLY. Take the min and max of those three, three decimals, joined by a hyphen.
       Do NOT compute this over the whole file - across all thirteen points the ratio spans
       roughly 0.727 to 1.008 and the sentence would become false.
     - The tuned ratio: TUNED_MEMBW_VOLTS, crossbar / mhz at target 1867, three decimals.

3. `5.7.4-plateau-gone`
   Fragment: `383.2 GB/s at 1852 MHz`
   From FIXED_MEMBW at target 1852. One decimal place. Remember to divide by 1e9.

4. `5.7.4-plateau-comparison`
   Fragment: `against the tuned profile's 294.5, +30.1%.`
   Two numbers. The 294.5 is TUNED_MEMBW_13PT at target 1852, one decimal, in GB/s. The
   percentage is deltaPct of the repaired figure against that one - so FIXED_MEMBW at 1852
   over TUNED_MEMBW_13PT at 1852. It is positive, so the default minus argument is fine.
   Note the bold markers around the percentage in the document are stripped before matching,
   so render it plainly.

5. `5.7.4-peak-throughput`
   Fragment: `411.8 GB/s peak against`
   The single highest throughput row in FIXED_MEMBW, in GB/s, one decimal. Note this is the
   highest THROUGHPUT, which on this sweep is not the highest commanded frequency - 3090
   achieves less than 2932. Compute it as a max over the rows, do not read a fixed target.

6. `5.7.4-peak-comparison`
   Fragment: `the tuned 414.3, a 0.6% difference`
   The highest throughput row in TUNED_MEMBW_13PT, in GB/s, one decimal, then the magnitude of
   the difference between the two peaks as a percentage to one decimal. The document writes it
   as a bare positive magnitude with no sign - "a 0.6% difference" - so do NOT use signedPct or
   deltaPct here. Compute abs(1 - repairedPeak / tunedPeak) * 100 and render it yourself.

7. `5.7.4-peak-power`
   Fragment: `79.4 W against 82.4 W at 2932 MHz`
   Both at target 2932: FIXED_MEMBW power first, TUNED_MEMBW_13PT power second, one decimal
   each. The frequency is the commanded target as an integer.

## Style

Match the surrounding file. Short helper functions are fine if two claims share a computation;
name them with a leading underscore and a prefix unique to this section, for example
`_r574ratio`. There are already helpers in that file named `_optimum` and similar, and a
collision would silently shadow them and break unrelated claims - this has happened before and
took a while to find, so do not use a bare generic name.

Write the module-level constants once, at the point where you begin this section's block, in
the same style as the constants already scattered through the file.

## Output

Return ONLY Python source, in a single fenced code block, with no commentary before or after it.
It will be appended verbatim to analysis/claims_consumer.py.
