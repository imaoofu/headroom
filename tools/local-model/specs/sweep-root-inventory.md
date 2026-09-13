TASK: write the missing inventory section for data/frequency-sweeps/README.md

Write MARKDOWN only. It will be inserted into an existing README under its own heading. Do not
write a top-level `#` heading, do not restate the file's existing sections, and do not invent any
fact that is not in the table below.

## The situation

`data/frequency-sweeps/` holds 32 sweep CSVs loose in its own root, alongside 32 subdirectories.
The README describes six of them individually and says nothing about the other 26. Every data
directory in this project is supposed to carry a README saying what it holds and what is
dataset-grade. This closes that.

## YOU HAVE NO TOOLS AND CANNOT READ ANY FILE

Every fact you may state is in the table below. **Do not invent a throughput, a clock, a date
beyond the one in the filename, or a conclusion about what a run showed.** You are writing an
inventory, not results. If you catch yourself describing what a sweep FOUND, delete the sentence.

Filenames must be reproduced EXACTLY. They are checked against the filesystem afterwards, and an
invented or misspelled one fails that check.

## The 26 undescribed sweeps

Append `_sweep.csv` to each stem for the actual filename.

| stem | points | workload | schema | applied_settings |
|---|---|---|---|---|
| `20260816-125959_5060ti-membw-fine-p1` | 13 | `membw` | 0.1.0 | NULL |
| `20260816-130549_5060ti-membw-fine-p2` | 13 | `membw` | 0.1.0 | NULL |
| `20260816-131140_5060ti-gemm-fine-p2` | 13 | `gemm` | 0.1.0 | NULL |
| `20260822-160740_5060ti-splitcurve-gemm-r1` | 13 | `gemm` | 0.2.0 | yes |
| `20260822-161322_5060ti-splitcurve-gemm-r2` | 13 | `gemm` | 0.2.0 | yes |
| `20260822-161921_5060ti-splitcurve-membw-r2` | 10 | `membw` | 0.2.0 | yes |
| `20260822-163705_5060ti-splitcurve-gemm-r3-quiet` | 13 | `gemm` | 0.2.0 | yes |
| `20260822-165213_5060ti-splitcurve-gemm-r4-instantreplay-on` | 13 | `gemm` | 0.2.0 | yes |
| `20260822-165944_5060ti-splitcurve-gemm-r5-instantreplay-off` | 13 | `gemm` | 0.2.0 | yes |
| `20260822-173451_5060ti-gemm-floor15-rerun` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-174118_5060ti-membw-floor15-rerun` | 13 | `membw` | 0.3.0 | yes |
| `20260822-174624_5060ti-gemm-fine-p1-rerun` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-175205_5060ti-membw-fine-p1-rerun` | 13 | `membw` | 0.3.0 | yes |
| `20260822-175706_5060ti-membw-fine-p2-rerun` | 13 | `membw` | 0.3.0 | yes |
| `20260822-180206_5060ti-gemm-fine-p2-rerun` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-182129_5060ti-tuned-gemm-clean-r1` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-182619_5060ti-tuned-gemm-clean-r2` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-183112_5060ti-tuned-membw-clean` | 10 | `membw` | 0.3.0 | yes |
| `20260822-201101_5060ti-stock-gemm-clean-r1` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-201554_5060ti-stock-gemm-clean-r2` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-211705_5060ti-memonly-gemm-clean-r1` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-212156_5060ti-memonly-gemm-clean-r2` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-213750_5060ti-tuned-gemm-clean-r3` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-215317_5060ti-tuned-gemm-clean-r4` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-215811_5060ti-tuned-gemm-clean-r5` | 13 | `gemm` | 0.3.0 | yes |
| `20260822-220443_5060ti-splitcurve-gemm-clean-r3` | 13 | `gemm` | 0.3.0 | yes |

## What the columns mean, and what to say about them

- **points** - frequencies measured. 13 is the standard grid, 10 is the narrower `membw` band.
- **schema** - the sweep tool's output version, and the useful one:
  - `0.1.0` has **no video-engine telemetry**, so it cannot be checked for capture-software
    contamination retrospectively.
  - `0.2.0` adds it.
  - `0.3.0` adds windowed power.
- **applied_settings** - `NULL` means **the configuration was not recorded**. State plainly that
  null does NOT mean stock: it means nothing reconstructs what the card was set to.

## Structure to produce

1. A short lead paragraph: what these root-level files are and why they sit here rather than in a
   subdirectory - they predate the convention of one directory per investigation. Two or three
   sentences.
2. **Group the runs into sections by what the filename indicates**, using your own judgement on
   the groupings the names suggest. Within each group, a table with the stem, points, workload and
   schema.
3. A short paragraph per group saying what the group IS, drawn only from the filenames and the
   table. For example a group whose names end `-rerun` is a re-measurement of an earlier set.
4. A closing block flagging, with counts you compute from the table:
   - how many of the 26 carry schema `0.1.0` and therefore cannot be checked for contamination
   - how many carry a null `applied_settings`
   Say what each limitation costs a reader. Do not soften either.

## Style

- Markdown. Bold for the load-bearing clause of a sentence, not for decoration.
- Complete sentences. This gets read by someone deciding whether a file is usable.
- Never write "various" or "several" where the table gives a number.
- ASCII only in your output.

## Output

Return only the markdown. No explanation before or after. No code fences.
