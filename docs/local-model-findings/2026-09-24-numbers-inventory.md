# Numbers inventory: sections 5.4.2, 5.7 (introduction) and 5.7.7

The local model's answer to job L3 (queue 2026-09-24, attempt 2), **verbatim**. It passed
`tools/local-model/specs/accept_numbers_inventory.py`: 40 rows for 40 numbers, and every quote is
verbatim. **The kind and likely-source columns are the model's and are NOT corrected here.** The
review is in `2026-09-24-queue-L1-L3.md`.

| section | number | quote | what it is | kind | likely source |
|---|---|---|---|---|---|
| 5.4.2 | 1 | `gemm` pass 1 froze for six minutes mid-sweep with the GPU clock-locked and idle. | pass index in the gemm sweep | setting | unknown |
| 5.7 | 2% | 5.7.1 had read a 2% power agreement as meaningfully tighter than 3% | read power agreement width | measurement | unknown |
| 5.7 | 3% | 5.7.1 had read a 2% power agreement as meaningfully tighter than 3% | read power agreement width | measurement | unknown |
| 5.7 | 2.07% | inside the 2.07% at which power reproduces (5.4.5) | power reproduction spread | restated | section 5.4.5 |
| 5.7 | +2500 | a **memory overclock** (+2500 MHz offset, 16301 against a 14001 rating) and a **core V/F curve** | memory clock offset applied | setting | unknown |
| 5.7 | 16301 | (+2500 MHz offset, 16301 against a 14001 rating) and a **core V/F curve** pinned flat | tuned memory frequency | measurement | unknown |
| 5.7 | 14001 | (+2500 MHz offset, 16301 against a 14001 rating) and a **core V/F curve** pinned flat | stock memory rating | measurement | unknown |
| 5.7 | 3000 | a **core V/F curve** pinned flat near 3000 MHz at every voltage at and above ~925 mV. | core frequency pin target | setting | unknown |
| 5.7 | 925 | pinned flat near 3000 MHz at every voltage at and above ~925 mV. | voltage floor for the flat curve | setting | unknown |
| 5.7 | 1% | `gemm` (compute-bound) \| nothing measurable, plus or minus 1% | noise margin around zero | measurement | unknown |
| 5.7 | -17% | the entire benefit: -17% to -28% power at matched clock, +12.1% sustainable ceiling | lower bound of power reduction | measurement | unknown |
| 5.7 | -28% | the entire benefit: -17% to -28% power at matched clock, +12.1% sustainable ceiling | upper bound of power reduction | measurement | unknown |
| 5.7 | +12.1% | the entire benefit: -17% to -28% power at matched clock, +12.1% sustainable ceiling | sustainable ceiling gain | measurement | unknown |
| 5.7 | +3.6% | the entire benefit: +3.6% to +16.1% over stock \| actively harmful: up to -29.6% throughput across 1560-1867 MHz | lower bound of throughput gain | measurement | unknown |
| 5.7 | +16.1% | the entire benefit: +3.6% to +16.1% over stock \| actively harmful: up to -29.6% throughput across 1560-1867 MHz | upper bound of throughput gain | measurement | unknown |
| 5.7 | -29.6% | actively harmful: up to -29.6% throughput across 1560-1867 MHz | maximum throughput loss | measurement | unknown |
| 5.7 | 1560 | actively harmful: up to -29.6% throughput across 1560-1867 MHz | lower bound of the swept frequency band | measurement | unknown |
| 5.7 | -1867 | actively harmful: up to -29.6% throughput across 1560-1867 MHz | upper bound of the swept frequency band | measurement | unknown |
| 5.7.7 | 14 | stock at 14:33 on 2026-08-19, full tuned at 20:42 the same day, memory-only at 18:13 | hour of the stock run | other | unknown |
| 5.7.7 | 33 | stock at 14:33 on 2026-08-19, full tuned at 20:42 the same day, memory-only at 18:13 | minute of the stock run | other | unknown |
| 5.7.7 | 20 | full tuned at 20:42 the same day, memory-only at 18:13 the next - switching configurations required | hour of the full tuned run | other | unknown |
| 5.7.7 | 42 | full tuned at 20:42 the same day, memory-only at 18:13 the next - switching configurations required | minute of the full tuned run | other | unknown |
| 5.7.7 | 18 | memory-only at 18:13 the next - switching configurations required a manual Afterburner change when these runs | hour of the memory-only run | other | unknown |
| 5.7.7 | 13 | memory-only at 18:13 the next - switching configurations required a manual Afterburner change when these runs | minute of the memory-only run | other | unknown |
| 5.7.7 | 5.8 | so configuration is now a scriptable variable; §5.8 is the first comparison collected that way and §5.5.8's | section number of the new comparison | other | section 5.8 |
| 5.7.7 | 40 | Idle temperature was 40-42 C at the start of each, the only cross-run control available. | lower bound of idle temperature | measurement | unknown |
| 5.7.7 | -42 | Idle temperature was 40-42 C at the start of each, the only cross-run control available. | upper bound of idle temperature | measurement | unknown |
| 5.7.7 | 29.6% | Effect sizes up to 29.6% are far outside plausible day-to-day drift so the direction is safe | maximum observed effect size | measurement | unknown |
| 5.7.7 | 2.07% | Section 5.4.5 puts power reproducing at 2.07% and efficiency at 2.08% across three replicates of one unchanged | power reproduction spread | restated | section 5.4.5 |
| 5.7.7 | 2.08% | puts power reproducing at 2.07% and efficiency at 2.08% across three replicates of one unchanged configuration, and | efficiency reproduction spread | restated | section 5.4.5 |
| 5.7.7 | 8 | across three replicates of one unchanged configuration, and limitation 8 puts cross-session drift at 1.47% on | limitation identifier | other | unknown |
| 5.7.7 | 1.47% | limitation 8 puts cross-session drift at 1.47% on throughput. Since the three configurations here were measured | cross-session throughput drift | restated | unknown |
| 5.7.7 | 3% | any percentage in this subsection smaller than roughly 3% should be read as indistinguishable from zero. | noise floor for significance | setting | unknown |
| 5.7.7 | 1 | n = 1 chip, one profile. Two `gemm` points outside the comparison band (2475 and 2625 MHz) show | number of chips tested | count | unknown |
| 5.7.7 | 2475 | Two `gemm` points outside the comparison band (2475 and 2625 MHz) show memory-only drawing 5.8% and 6.6% | lower out-of-band frequency | measurement | unknown |
| 5.7.7 | 2625 | Two `gemm` points outside the comparison band (2475 and 2625 MHz) show memory-only drawing 5.8% and 6.6% | upper out-of-band frequency | measurement | unknown |
| 5.7.7 | 5.8% | band (2475 and 2625 MHz) show memory-only drawing 5.8% and 6.6% more power than stock with only 1.2 | power increase at lower frequency | measurement | unknown |
| 5.7.7 | 6.6% | band (2475 and 2625 MHz) show memory-only drawing 5.8% and 6.6% more power than stock with only 1.2 | power increase at upper frequency | measurement | unknown |
| 5.7.7 | 1.2 | drawing 5.8% and 6.6% more power than stock with only 1.2 and 2.1 C to account for it; | temperature difference at lower frequency | measurement | unknown |
| 5.7.7 | 2.1 | drawing 5.8% and 6.6% more power than stock with only 1.2 and 2.1 C to account for it; | temperature difference at upper frequency | measurement | unknown |