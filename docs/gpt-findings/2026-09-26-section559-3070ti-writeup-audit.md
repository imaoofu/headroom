# Job 23: adversarial audit of paper §5.5.9

**Scope.** I independently calculated the nine suite optima from the committed sweep CSVs before opening the `5.5.9-*` claim definitions. I then checked the scorer, voltage extracts, saved curve decode, registration, and surrounding prose. These are **one RTX 3070 Ti, two sessions, twelve workloads per suite**, not nine independent chips. The registered verdicts remain 4a PASS, 4b FAIL, 8a PASS, and 8d NOT SCOREABLE. This record proposes wording; it does not change the paper or data.

## Independent calculation

For each usable target row I computed `bench_throughput / power_avg_w` and selected its maximum by target MHz. For Edit 2 I replaced the six high, clipped targets with **one bin whose efficiency is their median**, then compared that bin with the seven lower points. This is the registration's six-draw correction. The independent CSV calculation used no claims module. The scorer, run afterward, agreed for D and 8a and rejected D2's changed grid.

| Suite | Independently derived median MHz | Per-workload optima, in order: copy, reduce, softmax, layernorm, bgemm32, bgemm64, bgemm128, bgemm256, bgemm1024, attention, conv, gemm |
|---|---:|---|
| stock-1 | 1485 | 960, 855, 1485, 1275, 1485, 1485, 1380, 1485, 1485, 1485, 1485, 1485 |
| edit1-2 | 1222.5 | 1170, 960, 1275, 1170, 1485, 1590, 1170, 1275, 1170, 1590, 1170, 1485 |
| edit2-3 | 1432.5 | 1170, 1065, 1485, 1275, 1500, 1485, 1275, 1485, 1500, 1500, 1380, 1380 |
| stock-4 | 1485 | 1065, 855, 1485, 1485, 1485, 1485, 1485, 1485, 1485, 1485, 1485, 1380 |
| edit1-5 | 1170 | 855, 1065, 1170, 1065, 1590, 1590, 1170, 1590, 1590, 1590, 1170, 1170 |
| stock-6 | 1485 | 1065, 855, 1485, 1170, 1485, 1485, 1485, 1485, 1485, 1485, 1380, 1485 |
| stock-7 | 1485 | 1065, 1065, 1485, 1380, 1485, 1485, 1485, 1485, 1485, 1485, 1380, 1380 |
| edit2-8 | 1485 | 855, 855, 1500, 1275, 1485, 1500, 1485, 1500, 1485, 1485, 1380, 1380 |
| stock-9 | 1485 | 1170, 855, 1485, 1065, 1485, 1485, 1485, 1485, 1485, 1485, 1380, 1485 |

Session D has 855–2115 MHz in 105 MHz steps; D2 has the same seven low targets but **1605–2130 MHz** for its top six. Thus the §5.5.9 statement that the D2 control **held at 1485 MHz descriptively on its own grid is correct**, as are both D2 stock medians. It cannot receive the registered 8d verdict. The registered scorer exits with a grid mismatch at stock-7/copy. Its refusal and 4b's earlier failure must remain.

The early §5.5.9 sentence “Each suite is ... 855–2115 MHz in 105 MHz steps” is **false of all three D2 suites**, even though the later paragraph explains the deviation. It needs “Each Session D suite ...” or a qualifier at first mention. All **108 suite sweep files have 13 rows**; D2 changed the upper targets, not the number of points.

I independently recomputed the worst **per-workload median absolute matched-target throughput change** for the stock returns: stock-1→stock-4 **0.6190706%**, stock-4→stock-6 **1.1924078%**, stock-7→stock-9 **0.5628032%**. The paper's 0.619%, 1.192%, and 0.563% are correctly rounded. The first two medians meet the registered 1.5% return limit; the D2 number is descriptive. The Edit 2 optima sort to **1065, 1170, 1275, 1275, 1380, 1380 | 1485, 1485, 1485, 1500, 1500, 1500**: the paper's six–six split and 1432.5 midpoint are correct. Independently enumerating all **3^12 = 531,441** workload-wise choices among Session D's three stock optima gives **13,122 (2.469%)** medians of 1432.5, matching the quoted outside audit. This constructed proportion is not a null probability; the three suites share one card, and the twelve workloads are correlated.

The fine Edit 1 voltage extract records **0.819 V at 1230 MHz** and **0.838 V at 1275 MHz**. The paper's sampled floor-end bracket is correct. The saved profile's nominal 1200 MHz cap does not determine the observed loaded floor end. At the six moved-workload control comparisons (1380 and 1485 MHz), direct CSV calculations against the stock-1/stock-4 mean give throughput **−0.8168% to +0.5823%**, power **−4.68 to +9.495 W**, temperature **−0.55 to +1.50 °C**, and identical achieved clocks. The paper's rounded ranges are correct. Four workloads have a different displayed voltage code at 1485 MHz under Edit 2 than at least one stock suite: **reduce, bgemm32, bgemm64, conv**. These readings do not identify the physical cause of the power difference. The paper's “So the change is in the power denominator” is too categorical: throughput also changes, although less in the compared rows.

The two data directories contain **76** and **36** sweep files respectively: 72 D suite sweeps, three same-day fine sweeps and one earlier fine sweep, then 36 D2 suite sweeps. D's scorer reports driver **617.14** and the expected SILENT BIOS power limits. I did not independently verify the physical board identity from hardware; that is recorded in the sweep metadata. The paper's 0.812 V nominal stock floor and ~1500 MHz end come from its prior stock/fine characterization; the D stock suite itself only brackets the end between sampled 1485 and 1590 MHz, and its displayed 1485 MHz code varies between 0.812 and 0.819 V.

## The missing stock-to-stock baseline

| Comparison | Down | Up | Unchanged | At 1590 MHz afterward |
|---|---:|---:|---:|---:|
| stock-1 → stock-4 | 1 | 3 | 8 | 0 |
| stock-4 → stock-6 | 2 | 1 | 9 | 0 |
| stock-7 → stock-9 | 2 | 2 | 8 | 0; 1590 was not on D2's grid |
| stock-1 → edit1-2 | 6 | 4 | 2 | 2 |
| stock-4 → edit1-5 | 6 | 6 | 0 | 5 |

Stock against stock therefore produces **1–3 up moves**, as well as down moves, and **3–4 changed argmaxes of twelve**. The Edit 1 direction splits are real descriptions of these sweeps, but “workloads split in direction” alone is not specific to an edit. The 6 up moves in edit1-5 exceed these three observed stock comparisons; with only three stock pairs on one card, this is not a calibrated significance result. The **five-workload 1590 cluster in edit1-5** is outside the observed D stock pattern (none of stock-1, -4, -6 has a 1590 optimum); the two-workload cluster in edit1-2 is also absent from those stocks. D2 cannot test 1590 because its target is 1605. This is a distinctive **edit-associated** shape, not proof that the floor region alone caused it.

The curve decoded **before collection** in `docs/REGISTERED-PREDICTIONS.md` §4b Amendment 2 and `data/afterburner-profiles/3070ti-profiles-20260923/README.md` puts Edit 1 at **1200 MHz from 725 to 825 mV**, then a forced ramp from **1215 MHz at 831.25 mV to 1575 MHz at 868.75 mV**, rejoining stock at **1635 MHz/875 mV**. In the edited suites, the 1590 MHz target reads **0.869 V**, at the **top of the forced ramp, immediately before the stock rejoin**, not on the flat edited floor. For the five workloads that peak at 1590 in edit1-5, 1485 MHz reads **0.863 V** under Edit 1, against **0.812–0.819 V** in the stock suites. At 1590, Edit 1 reads 0.869 V against stock's 0.844–0.850 V. The edited 1485 point thus pays a larger displayed voltage-code increase than the edited 1590 point. The same five workloads' 1590-vs-1485 efficiency difference is positive under edit1-5 (**+1.59% to +4.42%**), whereas it is negative in both stock-1 and stock-4 (**−1.86% to −7.05%**).

**Hypothesis, not isolated mechanism:** the forced ramp may depress efficiency at 1485 enough to make 1590 a local winner for some workloads. The voltage readings, power, and argmax changes are compatible with this. They cannot distinguish the ramp's effect from the rest of Edit 1, run variation, or other unmeasured changes. It is therefore unsafe to describe the 1590 cluster as evidence that the floor alone set those workloads' optima.

## Wording audit and exact proposals

The abstract's “on two of them we change the curve and re-locate the optimum” is **literally true for median optima**, and broad enough to include the 3070 Ti, but reads like two successful causal floor tests without its next sentence. It is also **too weak on the 3070 Ti's mixed workload response**, which is the key distinction from 12/12 upward moves on the 5060 Ti. The following abstract bullet restores that distinction and records the failed control and unscoreable repeat. Keep those facts. “A negative control above the floor” is too clean: Edit 2 changes the **825 mV floor-band point by −15 MHz**. “Moved it too, once” fairly states the scored failure, but the unscoreable, descriptively held repeat belongs near it, not only in the bullet. “The causal evidence is two chips” overstates causal attribution on the second chip.

**Proposed abstract lead replacement:**

> On four consumer GPUs across three architectures we locate the V/F curve's low-voltage region and the energy-efficiency optimum. We edit the curves on two chips and measure where their median twelve-workload optima move. On the RTX 5060 Ti, a +465 MHz low-voltage curve difference moved the median by +465 MHz and all twelve workloads upward; a larger upper-curve edit left its median unchanged. On the RTX 3070 Ti, a registered floor-region edit moved the median into its predicted band in two suites, but only six of twelve workloads moved downward in each. A registered upper-curve control also moved the median once; its repeat held descriptively but was unscoreable under the registered grid. The 3070 Ti results do not isolate the floor region as the cause. We identify a card on which the rule cannot be applied, because its voltage leaves the floor six millivolts at a time.

This retains the **two-chip intervention**, the 5060 Ti's stronger directional result, and the 3070 Ti's registered successes without laundering the control failure. The last sentence is outside this audit's data scope and is kept from the existing abstract.

**Proposed abstract bullet heading:** replace “The causal evidence is two chips, and they disagree on the control” with “Curve interventions were tested on two chips; the controls disagree, and the 3070 Ti result does not isolate the floor.” Keep the two chip-specific bullets and their exact verdicts. Add “A stock-to-stock comparison on the 3070 Ti moves 3–4 workload argmaxes; Edit 1 moves 10 and 12, including 2 and 5 to 1590 MHz, a target no D stock suite selected.” This gives the direction counts their baseline without claiming significance.

**§5.5.8:** Its introductory registration sentence, its “Both interventions here are on one chip” limits bullet, and the cross-reference to §5.5.9 are accurate and should **stay**. The heading “Moving the floor moves the optimum; moving the curve above it does not” needs chip scope. Proposed: “**5.5.8 On the RTX 5060 Ti, moving the floor moves the median; the upper-curve control does not**.” The section's stronger “negative control excludes it quantitatively” and “floor sets where” language remains a separate causal-strength question; §5.5.9 does not validate those claims on the 3070 Ti.

**§5.5.9:** Keep the results table, its registered joint verdict, the D2 grid explanation and descriptive median, the fine-sweep bracket, the three stock return values, and the limits. Replace “Per-workload optima are also noisy here: identical stock suites disagree on 3 to 4 of 12” with: “**Identical stock suites have 1–3 upward moves and 3–4 changed workload argmaxes of twelve. Edit 1 has 4 and 6 upward moves, and 2 then 5 workloads at 1590 MHz; no Session D stock suite peaks at 1590. These are edit-associated shapes, but neither edit isolates the floor region.**” In the control paragraph, replace “So the change is in the power denominator” with: “**The compared rows have small throughput changes and larger changes in recorded power; the efficiency difference is mainly associated with the power denominator. These data do not identify why power changed.**” In “What this subsection supports,” change “a registered negative control moved it too, once” to “**the registered upper-curve control, which also lowered one point in the floor band, moved the median once; its D2 repeat held descriptively but was unscoreable**.” Keep “On this chip the move is not attributed to the floor region.”

At §5.5.9's first grid description, replace “**Each suite is the twelve workloads on thirteen targets, 855–2115 MHz in 105 MHz steps**” with “**Each Session D suite uses twelve workloads and thirteen targets from 855 to 2115 MHz in 105 MHz steps. Session D2 also uses thirteen targets, but its six highest are shifted upward by 15 MHz, as documented below.**”

**Conclusion item 4:** Keep the 4b failure and the statement that floor attribution fails on the 3070 Ti. Add one sentence: “**The control's next-day repeat held descriptively but was unscoreable because its six highest targets differed from the registered grid.**” Without it, “the control moved” reads as the complete repeated result.

**“What this work does not claim”:** The current “every tuning result is from the 5060 Ti except the two curve edits ... 3070 Ti” is directionally correct and can stay, though “the two curve edits” are configurations measured in multiple suites. The abstract's “every tuning result comes from a single card” can be misread as *one card total*. Proposed: “**Each tuning result is measured on one physical unit of its model; curve edits were tested on the 5060 Ti and the 3070 Ti.**”

**CLAUDE.md contribution/load-floor section:** Its contribution paragraph records the failed control and D2's descriptive hold, so keep those facts. Change the heading-level guidance “**The single most transferable result ... the only one now confirmed on two chips and two architectures**” to: “**The stock floor/optimum association appears across measured chips, but curve-intervention attribution is supported differently on the two edited chips: the 5060 Ti control leaves the median fixed, while the 3070 Ti control fails once and its repeat is unscoreable.**” That section's table has stock 5060 Ti and 3060 entries but no 3070 Ti, so “confirmed on two chips” is ambiguous; add a direct §5.5.9 cross-reference rather than treating its median result as a confirmed floor mechanism. The contribution sentence should use the same qualified abstract wording above.

**README status:** The new top correction correctly reports mixed 3070 Ti results and should stay. The older, visibly superseded bullets below it still say “three chips,” “customer machines,” and “everything about tuning is still one chip.” They are easy to quote out of context. Proposed replacement for those two old bullets when the README is next edited: “**Four chips, one unit of each, across three architectures. The 3070 Ti, 3060 and 2060 Super were shop builds owned during measurement. Curve edits were measured on the 5060 Ti and 3070 Ti; on the latter, the registered median manipulation passed twice, the control failed once, and its repeat was unscoreable. No within-model population effect is estimated.**”

**Paper-wide search:** I found no live unqualified statement that the entire causal test is still on one chip or that all tuning is still 5060 Ti only. §5.5.8's “one chip” sentences explicitly mean *that section's* 5060 Ti interventions and point to §5.5.9. §5.5.4's “3070 Ti swept once” describes its earlier **cross-architecture suite comparison**, but is easy to misread after Sessions D/D2; proposed qualifier: “**the 3070 Ti was swept once for this comparison**.” In the abstract, the single-card sentence above is the remaining ambiguity.

**Future work is stale; do not silently update it in this audit.** It says “two architectures” and “one card per architecture,” although the paper now has **four cards across three architectures, including two different Ampere models**. It says the twelve-workload stock suite has run “on both chips”; that is only the §5.5.4 pair, not a full project inventory. “A second Ampere die” exists as a different model, so the useful unmeasured replication is **another unit of the same SKU**, or a matched cross-architecture design. The section also speaks of two chips while the abstract counts four. Its old question is closed for the original pair, but the current population question remains open. Proposed future-work replacement, for a later paper edit: “**The twelve-workload ranking comparison was completed on one 5060 Ti and one 3070 Ti and did not transfer between them (§5.5.4). The dataset now includes four cards across three architectures, but only one unit of each model. Testing whether that disagreement is typical requires repeated units of the same model and a matched design across models; additional workloads on these same units cannot supply that population evidence.**”

**Collateral abstract count issue:** the manifest check reports **683 dataset-grade sweeps plus three verification sweeps = 686 counted sweeps**. The abstract calls all 686 “dataset-grade” while also listing the three verification runs. That adjective is wrong. Proposed replacement: “**686 counted sweeps: 683 dataset-grade across four chips and three early three-point verification runs.**” This does not affect §5.5.9's 76 + 36 file counts, and the count must be taken from `analysis/build_data_manifest.py --check` again at paper-edit time.

## Evidence and limits

Primary local records: `data/frequency-sweeps/rtx3070ti-sessiond-20260924/`, `data/frequency-sweeps/rtx3070ti-sessiond2-20260925/`, `data/afterburner-profiles/3070ti-profiles-20260923/README.md`, `docs/REGISTERED-PREDICTIONS.md` §4b Amendment 2 and §8d, `analysis/score_session_d.py`, `docs/PAPER_DRAFT.md` abstract/§5.5.8/§5.5.9/conclusion, `CLAUDE.md`, and `README.md`. The independent calculations used a temporary script **outside the repository**; no data or registered scorer was edited. Before writing this record, `python run_tests.py --quiet` passed **1,112 checks in 36 suites**; `python analysis/audit_claims.py`, `python analysis/build_data_manifest.py --check`, and `python analysis/verify_citations.py --check` passed. The claims module pins several D table/count strings but does not independently certify every interpretive sentence or D2's descriptive table. No hardware was operated and no physical voltage mechanism was isolated.

---

## Claude review, 2026-09-26: accepted; the corrections were applied, one of them more widely than proposed

**Verified here, independently:**
- **The three stock-against-stock direction counts** (1/3/8, 2/1/9, 2/2/8), from the scorer's
  per-workload optima and D2's README.
- **The 1590 MHz voltages:** 0.863 V at 1485 and 0.869 V at 1590 under `edit1-5`, against
  0.812–0.819 and 0.844–0.850 V at stock, for the same five workloads.
- **Their 1590-against-1485 efficiency:** +1.59% to +4.42% under Edit 1, and −1.86% to −7.05% in
  `stock-1`/`stock-4`.
- **The abstract census adjective.**

**The census error was in the claim as well as the prose.** `paper-dataset-grade-total` rendered
"{dataset-grade + verification} dataset-grade sweeps", so the formula enforced the wrong word. Both
now say "686 sweeps … of which 683 are dataset-grade".

**Applied:**
- **§5.5.9:**
  - the grid sentence now covers D2;
  - the direction table gains two stock-against-stock rows, pinned by the `5.5.9-edit1-directions`
    claim, and the 1590 claim now also checks that no stock suite peaks there;
  - the 1590 ramp position is given as a labelled hypothesis;
  - "power denominator" is softened;
  - the "supports" sentence now names the floor-band point and D2.
- **The abstract:**
  - the lead is GPT's substance: "edit the curve and measure where … moves", "only six of twelve
    moved down", with the control's floor-band point and D2 in the sentence;
  - the bullet heading is GPT's, and a baseline bullet is added;
  - "every tuning result comes from a single card" is corrected.
- **§5.5.8:** the heading is scoped to the 5060 Ti.
- **Conclusion:** item 4 gains D2's unscoreable repeat.
- **§5.5.4:** "for this comparison" added to its caveat.
- **Future work:** "a second Ampere die" is replaced by repeated units of one model, and an
  unresolved-control item is added.
- **CLAUDE.md:** the contribution sentence matches the abstract, the "confirmed on two chips"
  heading is struck and narrowed, and the baseline and 1590 notes are added.
- **README:** the "everything about tuning is still one chip" bullet is struck.

**Not applied:** the README's older "three chips / customer machines" bullet is left as history
under its dated correction block, which already supersedes it. It gets rewritten when the README is
next revised as a whole.
