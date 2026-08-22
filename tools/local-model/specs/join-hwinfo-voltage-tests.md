TASK: write tools/frequency-sweep/test_join_hwinfo_voltage.py

Write Python only. Create one new file. Do not modify join_hwinfo_voltage.py or any other file.

## What you are testing and why it matters

join_hwinfo_voltage.py joins HWiNFO voltage telemetry to a GPU frequency sweep. It produced
every voltage number in this project, and those numbers are the basis of its central result:
that a stock GPU raises voltage as frequency rises while a flattened V/F curve does not.

A defect in this file does not shift a decimal. It invents or erases that slope. It currently
has no tests at all. That is what you are fixing.

YOU HAVE NO TOOLS AND CANNOT RUN ANYTHING. Write the tests from this specification alone. Do not
guess at behaviour that is not described here.

## The five functions under test

    loadHwinfo(path)  -> (samples, indices)
    loadSweep(path)   -> list of dicts
    filterIdle(samples, minPower)                          -> list
    matchSamples(samples, achievedMhz, toleranceMhz=25.0)  -> list
    summarisePoint(matched, achievedMhz)                   -> (voltage, crossbar, ratio)

### loadHwinfo(path)

Reads an HWiNFO CSV with `encoding="latin-1"`. Row 0 is the header; each header cell is stripped
of surrounding whitespace before use.

It looks for columns named exactly `GPU Core Voltage [V]`, `GPU Clock [MHz]`,
`GPU Crossbar Clock [MHz]` and `GPU Power [W]`. Names may appear MORE THAN ONCE, because HWiNFO
on this machine emits two GPU sensor blocks and only one describes the NVIDIA card.

Resolution rules, in order:
  - If there is no voltage column or no clock column, it raises SystemExit.
  - clockIndex is the `GPU Clock [MHz]` column with the LARGEST spread (max minus min) over the
    data rows. Non-numeric cells are skipped when computing the spread; a column with no numeric
    values at all has spread 0.0. This is what rejects the phantom block, which sits at a fixed
    clock.
  - voltageIndex, crossbarIndex and powerIndex are each the candidate column CLOSEST IN INDEX to
    clockIndex, i.e. minimising abs(candidateIndex - clockIndex).
  - crossbarIndex and powerIndex are None when no such column exists.

Then, per data row:
  - a row too short to contain both the clock and voltage columns is skipped
  - a row whose clock or voltage cell is not a number is skipped
  - crossbar and power are None when their column is absent or the row is too short to reach it
  - kept rows become dicts with keys `clock`, `voltage`, `crossbar`, `power`

Returns `(samples, indices)` where indices is a dict with keys `clock`, `voltage`, `crossbar`,
`power`.

### loadSweep(path)

Reads a sweep CSV with `encoding="utf-8-sig"`, so a UTF-8 BOM must parse. Row 0 is the header.
Empty rows are skipped. Every other row becomes a dict:

    target        int(float(target_frequency_mhz))
    achieved      float(achieved_frequency_avg)
    throughputGbs float(bench_throughput) / 1e9
    powerW        float(power_avg_w)
    memoryMhz     float(memory_clock_avg_mhz), or float("nan") when the column is absent

NOTE, and test this: unlike the loader in analysis/analyze_sweep.py, this one does NOT filter on
bench_ok and does NOT drop rows whose clock lock overshot. It keeps every non-empty row.

### filterIdle(samples, minPower)

Keeps a sample when its power is None, OR its power is >= minPower. Everything else is dropped.

The None case is deliberate and must be tested: an absent power column means the log never
carried one, and dropping every sample would produce a silently empty join.

The boundary is inclusive. A sample exactly at minPower is KEPT.

### matchSamples(samples, achievedMhz, toleranceMhz=25.0)

Keeps a sample when abs(sample clock - achievedMhz) <= toleranceMhz. The boundary is inclusive:
a sample exactly toleranceMhz away is KEPT. Returns [] when nothing matches.

### summarisePoint(matched, achievedMhz)

Returns a 3-tuple `(voltage, crossbar, ratio)`.

  - voltage is the MEDIAN of the matched samples' voltages
  - crossbar is the MEDIAN of the matched samples' crossbar values, ignoring any that are None
  - ratio is crossbar / achievedMhz
  - when NO matched sample has a crossbar value, crossbar and ratio are both float("nan")

Median, not mean. Test that with a set where the two differ, so a swap would be caught.

## The cases that must be covered

Cover every function above. These specific ones are required, because each is a defect that
would be invisible on inspection:

1. loadHwinfo picks the moving clock column, not the first one. Build a header with TWO
   `GPU Clock [MHz]` columns where the FIRST is constant and the SECOND varies, and assert the
   varying one was chosen.
2. loadHwinfo resolves voltage to the column nearest the chosen clock, with two voltage
   candidates present.
3. loadHwinfo raises SystemExit when the voltage column is missing.
4. loadHwinfo skips a row whose voltage is not a number, and keeps the surrounding rows.
5. loadHwinfo returns crossbar None and power None when those columns are absent.
6. loadSweep parses a file written with a UTF-8 BOM.
7. loadSweep keeps a row with bench_ok False and a row whose lock overshot.
8. loadSweep gives memoryMhz nan when the column is absent. Assert with a nan-aware check, since
   nan does not equal itself.
9. filterIdle keeps a None-power sample.
10. filterIdle keeps a sample exactly at minPower and drops one below it.
11. filterIdle: an idle-voltage sample above the real ones is excluded, and this changes the
    result. Give three samples where two are under load at low voltage and one is a
    high-voltage idle sample, filter, then summarisePoint, and assert the median voltage is the
    loaded one. This is the manufactured-slope case and is the most important test in the file.
12. matchSamples keeps a sample exactly at the tolerance and drops one just outside.
13. matchSamples returns an empty list when nothing is near.
14. summarisePoint returns the median and not the mean.
15. summarisePoint ignores None crossbars but still uses the rest.
16. summarisePoint gives nan crossbar AND nan ratio when every crossbar is None.
17. summarisePoint's ratio equals crossbar divided by achievedMhz, on a case you can verify by
    hand.

## How to write it

An existing suite in this project's house style is included ABOVE this spec. Follow it exactly.
You have already been given everything you need; there is nothing to look up. In particular:

- No pytest, no unittest. A module-level `failures` list and a `check(description, condition,
  detail="")` helper that prints `[PASS] ...` or `[FAIL] ...`. At the end, print
  `ALL CHECKS PASSED` or raise SystemExit(1).
- The runner counts occurrences of the literal `[PASS]`, so print exactly that.
- Build inputs with `tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, ...)`,
  wrap the assertions in `try:` and delete the file in `finally:`. Use `encoding="utf-8-sig"`
  for the BOM case and `encoding="latin-1"` for HWiNFO files.
- Import with:

      import sys
      from pathlib import Path
      sys.path.insert(0, str(Path(__file__).resolve().parent))
      from join_hwinfo_voltage import (loadHwinfo, loadSweep, filterIdle,
                                       matchSamples, summarisePoint)

- filterIdle, matchSamples and summarisePoint take plain lists of dicts. Do not write a CSV to
  test them.
- camelCase for any helper you define, not snake_case.
- ASCII only.
- Comments only where a reader would ask WHY. Never restate what a line does.

## The module docstring

Open the file with a docstring covering: why this function needs tests at all (a defect
manufactures or erases the project's central finding rather than perturbing a number); what the
subtle cases are (the two sensor blocks, the inclusive boundaries, the None-power sample being
kept); and a `Run:` line. Match the tone of the docstring in the included example suite.

Do NOT write a PROVENANCE section and do NOT claim any mutation testing was done. That check
happens after you hand this back, and writing that it happened would be a false statement.

## Output

Return only the Python file contents. No explanation before or after. No markdown fences.
