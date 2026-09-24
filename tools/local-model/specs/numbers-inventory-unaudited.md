TASK: inventory every number in three unaudited paper sections, as a Markdown table

Return ONE Markdown table and nothing else: no heading, no text before or after it.

## YOU HAVE NO TOOLS AND CANNOT READ ANY FILE

Everything you may state is in this message. Do not invent a value, a file, or a result. Your output
is checked by a script against the paper itself: every quote must appear in the section word for
word, and the numbers you list must match, one for one, the numbers a regular expression extracts
from each section. Missing one, adding one, or listing one twice all fail the check.

## Why

The project's paper is checked by an auditor that pins each number to the data file it comes from.
These three sections have no pinned numbers yet. Before anyone writes those checks, someone has to
list what each number is and where it probably comes from. That is this job. **You are writing an
inventory, not checking whether the numbers are right.**

## The table

Columns, in this order:

| section | number | quote | what it is | kind | likely source |

- `section`: `5.4.2`, `5.7` or `5.7.7`.
- `number`: the number exactly as the list below gives it, including any sign and `%`.
- `quote`: a verbatim run of 6 to 30 words copied from that section that contains the number. Copy
  characters exactly, but you may leave out `**` bold markers. Do not join text across a line that
  is only `>`. If a `|` character falls inside your quote, write it as `\|`.
- `what it is`: under 15 words.
- `kind`: one of `measurement`, `derived`, `count`, `setting`, `restated`, `other`. Use `restated`
  when the sentence plainly refers to a figure established in another section (for example "5.7.3
  shows ...").
- `likely source`: a directory from the list below, or `section X.Y` if the number is restated, or
  `unknown`. Guessing `unknown` is better than guessing wrong.

**Section 5.7 contains a Markdown table.** For a number inside that table, the quote is the text
of the ONE cell that holds the number, copied exactly, even if it is shorter than 6 words. Never
quote across two cells, and never put a `|` in a quote from the table. Every row of your output
must have exactly six cells. (Added 2026-09-23 after a smoke test: quoting across cells gave rows
with seven or eight cells.)

**One row per occurrence.** If a number occurs twice in a section, it gets two rows, each with its
own quote.

## The numbers to cover, per section, in the order the extractor finds them

- **5.4.2**: `1`
- **5.7**: `2%`, `3%`, `2.07%`, `+2500`, `16301`, `14001`, `3000`, `925`, `1%`, `-17%`, `-28%`, `+12.1%`, `+3.6%`, `+16.1%`, `-29.6%`, `1560`, `-1867`
- **5.7.7**: `14`, `33`, `20`, `42`, `18`, `13`, `5.8`, `40`, `-42`, `29.6%`, `2.07%`, `2.08%`, `8`, `1.47%`, `3%`, `1`, `2475`, `2625`, `5.8%`, `6.6%`, `1.2`, `2.1`

The extractor ignores dates, inline `code`, links and section cross-references such as 5.7.3, so those are not numbers here.

## Data directories that exist (`data/frequency-sweeps/`)

`5060ti-activity-ab-20260923`, `5060ti-finefloor-20260918`, `5060ti-finefloor-20260922`, `5060ti-membw-silent-20260922`, `5060ti-nvml-offset-20260922`, `5060ti-offset-ladder-20260923`, `5060ti-p1-suite-20260922`, `5060ti-p4-suite-20260922`, `5060ti-rungB-suite-20260923`, `5060ti-stock-repro-20260922`, `abba-20260908`, `curve-rebuild-20260823`, `dense-grid-20260829`, `driver-61664-probe-20260905`, `identity-probes-20260908`, `kitverify-20260823`, `membw-anomaly-20260819`, `memonly-clean-20260823`, `memonly-gemm-20260829`, `oc-comparison-20260819`, `repair-clean-20260824`, `repair-suite-p2-20260909`, `rtx2060s-20260912`, `rtx2060s-finefloor-20260915`, `rtx3060-20260910`, `rtx3070ti-20260825`, `rtx3070ti-suite-20260904`, `samplerate-probe-20260904`, `splitcurve-clean-20260824`, `splitcurve-suite-20260907`, `splitcurve-suite-s2-20260908`, `stock-bracket-20260909`, `stock-suite-20260829`, `suite-pilot-20260829`, `suite-replicate-r10-20260918`, `suite-replicate-r2-20260830`, `suite-replicate-r3-20260902`, `suite-replicate-r4-20260904`, `suite-replicate-r5-20260904`, `suite-replicate-r6-20260905`, `suite-replicate-r7-20260906`, `suite-replicate-r8-20260908`, `voltage-curve-20260908`, `voltage-curve-20260909`

## The three sections, verbatim

### Section 5.4.2

````markdown
`gemm` pass 1 froze for six minutes mid-sweep with the GPU clock-locked and idle. The cause was not
the benchmark, the sweep script, or the driver: Windows consoles enable QuickEdit by default, so a
single click inside the window enters selection mode, and **selection mode blocks all output to that
console**, suspending any process that writes progress. There is no error, the process stays alive,
and the only visible trace is the word `Select` prepended to the window title.

This is recorded because it is a silent failure mode for exactly the kind of long, unattended,
elevated run this project depends on, and because its damage was *not* obvious: the interrupted
point itself looked normal (it reheated during the settle interval), while the two neighbouring
points were measurably corrupted. Both sweep tooling and the stability logger now disable QuickEdit
at startup.
````

### Section 5.7

````markdown
> **Written 2026-08-20, second pass 2026-09-04.** The mechanism of 5.7.3 was re-verified against
> the committed voltage extracts and its headline figures are now pinned by the claim auditor
> rather than only checked by eye. **One claim did not survive the pass and is withdrawn in
> place** - 5.7.1 had read a 2% power agreement as meaningfully tighter than 3%, and both sit
> inside the 2.07% at which power reproduces (5.4.5).
>
> **The contamination caveat on 5.7.4 and 5.7.5 is unaffected and stands.** Those measurements
> predate the capture-software finding of 5.4.4 and have no clean counterpart; a second pass over
> the prose cannot fix that, and does not claim to.

Every earlier consumer result treats "tuned" as one setting. It is two: a **memory overclock**
(+2500 MHz offset, 16301 against a 14001 rating) and a **core V/F curve** pinned flat near
3000 MHz at every voltage at and above ~925 mV. Three sweeps separate them - full tuned, memory
overclock only with the core curve reverted to stock, and stock - on the same card at identical
locked targets.

**The two knobs have opposite effects on the two workloads.**

| | memory overclock | core V/F curve |
|---|---|---|
| `gemm` (compute-bound) | nothing measurable, plus or minus 1% | the entire benefit: -17% to -28% power at matched clock, +12.1% sustainable ceiling |
| `membw` (bandwidth-bound) | the entire benefit: +3.6% to +16.1% over stock | actively harmful: up to -29.6% throughput across 1560-1867 MHz |
````

### Section 5.7.7

````markdown
The three configurations were **not** measured contemporaneously: stock at 14:33 on 2026-08-19, full
tuned at 20:42 the same day, memory-only at 18:13 the next - switching configurations required a
manual Afterburner change when these runs were collected.

⛔ **That constraint expired on 2026-09-08 and this paragraph asserted it as permanent.** Afterburner
applies a stored profile from the command line, so configuration is now a scriptable variable; §5.8
is the first comparison collected that way and §5.5.8's ABBA design depends on it. The caveat below
still describes *these* runs correctly - it is a fact about when they were taken, not about what the
method can do. Idle temperature was 40-42 C at the start of
each, the only cross-run control available. Effect sizes up to 29.6% are far outside plausible
day-to-day drift so the direction is safe, but the precise percentages are softer than they look.

**How much softer is now measured rather than guessed.** Section 5.4.5 puts power reproducing at
2.07% and efficiency at 2.08% across three replicates of one unchanged configuration, and
limitation 8 puts cross-session drift at 1.47% on throughput. Since the three configurations here
were measured on different days, **any percentage in this subsection smaller than roughly 3% should
be read as indistinguishable from zero.** The large effects are untouched by that bar; the small
ones were never load-bearing and are now explicitly not.
n = 1 chip, one profile. Two `gemm` points outside the comparison band (2475 and 2625 MHz) show
memory-only drawing 5.8% and 6.6% more power than stock with only 1.2 and 2.1 C to account for it;
this is unexplained and recorded rather than trimmed.

---

---
````
