TASK: add claims covering paper section 5.4 to analysis/claims_consumer.py

Write Python only. Append to the end of analysis/claims_consumer.py. Do not modify anything
already in that file, and do not modify analysis/audit_claims.py.

## How a claim works

audit_claims.py provides a decorator. A claim function returns THE EXACT STRING the document
must contain, computed from the CSVs. The engine asserts that string appears in the document
verbatim and exactly once. It stores no expected number anywhere.

    @claim("<id>", PAPER, "5.4")
    def someName():
        return f"...{value:.1f}..."

YOU DO NOT NEED TO READ ANY CSV, AND YOU HAVE NO TOOLS HERE. A claim is code that will be RUN
LATER by the audit, at which point it reads the CSVs itself. Your job is only to write the
formula. You will never see, and must never hardcode, the resulting numbers.

Helpers already in claims_consumer.py, use them, do not reimplement:

    sweep(path)         -> dict keyed by COMMANDED frequency (int target). Each row is a dict
                           with keys: target, mhz, throughput, power, unit. `throughput` is raw
                           units per second. `power` is watts.
    efficiency(row)     -> row["throughput"] / row["power"]
    signedPct(ratio, minus="-")
                        -> "+46.5%" from a RATIO. The `minus` argument replaces the sign
                           character used for negatives; see the character note below.
    deltaPct(new, old, minus="-")
                        -> signedPct(new / old, minus=minus)
    PAPER               -> "docs/PAPER_DRAFT.md"

`peak(rows)` also exists but returns the highest-THROUGHPUT row. Section 5.4 is about the
highest-EFFICIENCY row, which is a different row. Do not use peak() for the optimum.

Bold markers (**) are stripped from both sides before matching, so do not render them.

## Source files

Add these two module-level constants, following the naming style already in the file. Note they
sit directly under data/frequency-sweeps/ with no subdirectory:

    GEMM_FLOOR15  = "20260816-001048_5060ti-gemm-floor15_sweep.csv"
    MEMBW_FLOOR15 = "20260816-001734_5060ti-membw-floor15_sweep.csv"

## Two definitions used throughout

    optimum        = the row with the highest efficiency(row)
    sustained max  = the row with the highest achieved clock, row["mhz"]

Every figure below compares the optimum against the sustained max, within one workload.

## NON-ASCII CHARACTERS IN THE DOCUMENT

The source file must be ASCII only, but three of the strings you render contain characters that
are not. Produce them with chr(), never as literals:

    chr(0x2014)   EM DASH, used in the row label "<em dash> as % of sustained max"
    chr(0x2212)   MINUS SIGN, used for the NEGATIVE percentages in two rows

The document uses a real minus sign, not a hyphen, for negative values in this table. Pass
chr(0x2212) as the `minus` argument to signedPct or deltaPct where the value is negative.
Positive values in this table use an ordinary "+" and need no special handling.

## The claims to write

Six claims. Use the id given for each, exactly. Each of the first five is one table row.

1. `5.4-optimum`

       | Efficiency optimum | <gemm optimum MHz> MHz | <membw optimum MHz> MHz |

   Clock to zero decimals.

2. `5.4-pct-of-max`

       | <em dash> as % of sustained max | <g>% (of <gmax> MHz) | <m>% (of <mmax> MHz) |

   Percentages and clocks both to zero decimals. The percentage is the optimum's clock as a
   percentage of the sustained max clock.

3. `5.4-efficiency-gain`

       | Efficiency gain vs sustained max | <g> | <m> |

   Each is the optimum's efficiency against the sustained max's efficiency, as a signed
   percentage. Both are positive here.

4. `5.4-performance-cost`

       | Performance cost at optimum | <g> | <m> |

   Each is the optimum's throughput against the sustained max's throughput, signed. Both are
   negative, so these need the minus-sign character.

5. `5.4-power-saved`

       | Power saved at optimum | <g> | <m> |

   Each is the optimum's power against the sustained max's power, signed. Both negative.

6. `5.4-monotonicity-break`

   From GEMM_FLOOR15 only, using the two rows whose ACHIEVED clocks are 1987 and 2205 MHz. The
   achieved clocks are not round numbers in the file, so select the row nearest each. Renders:

       at <lower> MHz (<lower efficiency> GFLOP/J) sits marginally below <higher> MHz
       (<higher efficiency>), breaking monotonicity by <gap>%

   - clocks to zero decimals
   - efficiencies to two decimals, so divide by 1e9
   - the literal text "GFLOP/J" appears after the FIRST efficiency only, not the second.
     That asymmetry is how the paper writes it; reproduce it rather than tidying it up.
   - gap is how much the HIGHER-clock point exceeds the LOWER-clock one, as a percentage to one
     decimal, with no sign character at all
   - no trailing punctuation

## THIS MATTERS

A claim's job is to state what the data says. It is NOT to make the audit green. If a claim you
write correctly does not match the document, that is a finding and the correct outcome; leave
the claim as the data dictates and do not adjust the rendering to force a match. Do not work
backwards from the document's text to a formula that reproduces it.

## Conventions

- camelCase for function names, not snake_case.
- Comments only for a non-obvious WHY, never to restate what a line does.
- ASCII only in the source, using chr() for the characters named above.
- Open with a `# ---` banner naming the section, matching the ones already in the file. The
  section is titled "Consumer hardware measurements". Do not invent a description of what the
  section concludes.
- Write the five table-row claims with a shared helper where it makes sense rather than five
  near-identical functions, but do not force it if the rows differ too much.

## Output

Return only the Python to append. No explanation before or after, no markdown fences.
