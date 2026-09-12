TASK: write the claims covering paper section 5.6.3

Write Python only. The code you return will be INSERTED INTO an existing `else:` block in
analysis/claims_reference.py, so **every line you write must be indented by 4 spaces**, including
the decorators. Do not write `import`, do not write a module docstring, do not repeat any
existing code, and do not emit anything at column 0.

## How a claim works

A claim function returns THE EXACT STRING the document must contain, computed from the data.
The engine asserts that string appears in docs/PAPER_DRAFT.md verbatim and **exactly once**.
It stores no expected number anywhere. Matching twice is a FAILURE, not a pass.

    @claim("<id>", PAPER, "5.6.3")
    def someName():
        return f"...{value:.1f}..."

YOU HAVE NO TOOLS AND CANNOT READ ANY FILE. A claim is code that will be RUN LATER, at which
point it reads the data itself. Your job is only to write the formula. You will never see, and
must never hardcode, the resulting numbers. If a number appears in this specification it is
there to describe FORMAT, never to be pasted into your answer.

Bold markers (`**`) and runs of whitespace are normalised away on both sides before matching,
so do not render `**` and do not try to reproduce column padding or line wrapping.

## What is already in scope, use it, do not reimplement

These names are already bound in the enclosing block:

    PAPER       -> "docs/PAPER_DRAFT.md"
    SUMMARY     -> a pandas DataFrame, one row per workload, from the public V100 dataset.
                   Columns you need:
                       SUMMARY["performance_given_up_pct"]   percent of performance GIVEN UP
                                                             at each workload's own optimum
                       SUMMARY["power_saved_pct"]            percent of power SAVED there
                   Both are percentages already, e.g. 13.7 means 13.7 percent. Use .mean().
    DATA        -> a dict. DATA["floorRow"] is a dict for the 95%-performance-floor operating
                   point, with keys:
                       "loss_mean"          mean percent of performance LOST at that point
                       "power_saved_mean"   mean percent of power SAVED at that point
                   Both are percentages already.
    claim       -> the decorator

## The two operating points

Section 5.6.3 asks what the headroom is worth once the extra hardware is paid for. It resizes a
fleet so total output is held constant. For each operating point, define, all in percent:

    perfRetained   = 100 - (performance given up)
    powerPerUnit   = 100 - (power saved)
    units          = 100 / perfRetained          # units needed for equal total output
    fleetPower     = units * powerPerUnit        # percent of the stock fleet's power

For the UNCONSTRAINED point the two inputs are SUMMARY["performance_given_up_pct"].mean() and
SUMMARY["power_saved_pct"].mean(). For the 95% FLOOR point they are DATA["floorRow"]["loss_mean"]
and DATA["floorRow"]["power_saved_mean"].

Write one helper, `fleetRow(performanceGivenUp, powerSaved)`, returning whatever shape suits you,
and derive every claim below from it. Do NOT round intermediate values; round only at render.

## The claims to write

Six claims. Use each id exactly as given.

1. `5.6.3-unconstrained-row` — one table row:

       | unconstrained optimum (5.1) | <perfRetained>% | <powerPerUnit>% | <units> | <fleetPower>% |

   Percentages to ONE decimal. `units` to THREE decimals.

2. `5.6.3-floor-row` — the same shape for the floor point:

       | 95% floor (5.6) | <perfRetained>% | <powerPerUnit>% | <units> | <fleetPower>% |

3. `5.6.3-unconstrained-trade`

       trades <extraUnits>% more units for <fleetSaving>% less fleet power

   where extraUnits = units*100 - 100 and fleetSaving = 100 - fleetPower, both to ONE decimal.

   ⚠️ The bare figures also appear later in the same section, in a sentence beginning "buying".
   The words above are what make this match once. Render them exactly, including "trades".

4. `5.6.3-floor-trade`

       trades <extraUnits>% more units for <fleetSaving>% less

   Note this one ends at "less" with no "fleet power" after it. Reproduce that.

5. `5.6.3-unconstrained-breakeven`

       unconstrained <a> / <b> = lifetime energy must exceed <pct>% of unit price

   - a = extraUnits/100, to THREE decimals   (a fraction, not a percentage)
   - b = fleetSaving/100, to THREE decimals
   - pct = 100 * a / b computed from UNROUNDED values, to ZERO decimals
   - the document writes this inside an indented code block with several spaces after
     "unconstrained"; whitespace runs are normalised, so emit ONE space there

6. `5.6.3-floor-breakeven`

       95% floor <a> / <b> = lifetime energy must exceed <pct>% of unit price

   Same rules.

## Style

- camelCase function names, not snake_case. Names describe the claim, not the section number.
- ASCII only.
- Give claims 3 to 6 a one-line docstring saying WHY the claim exists — what would go
  unnoticed if it were absent. Do not restate what the code does.
- One comment, on `fleetRow`, explaining why rounding happens only at render.

## THIS MATTERS

A claim's job is to state what the data says, NOT to make the audit green. If a correctly
written claim does not match the paper, that is a finding about the paper. Never adjust a
formula to chase a string.

## Output

Return only the Python, indented 4 spaces. No explanation before or after. No markdown fences.
