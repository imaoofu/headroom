# Job 22: adversarial review of the Wang Figure 4 correction

**Checked 2026-09-25 Pacific time.** I independently recomputed the [Wang et al. Figure 4
artifact](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/tree/8a0a2e0ef402b84c428496ce037c6753f19f0873)
before reading `analysis/wang_tpds_figure4.py`, then checked the pickle's history,
the [paper's §5.2](https://arxiv.org/pdf/2104.00486), and searches for later
discussion. **The model calculations hold, but the paper's measured 4.3% remains
unreproduced.** Four claims in the 2026-09-25 correction need tighter wording:
4.351999% rounds to 4.4%, not 4.3%; the model/grid agreement uses grid
snapping on the *training data*; `gamma` is not static power; and the paper
does not say which plotted bars received the power-term reduction. No paper
or `CLAUDE.md` edit was made.

## Independent recomputation, then script comparison

I read `apps.pkl` with a restricted pickle loader and extracted the 2021
notebook's `solve_dvfs()` function. For an undivided call I multiplied a
**copy** of `p0` by 4.75 and `gamma` by 4.65 immediately before calling the
notebook function, canceling its in-place division. Each independent call
used a fresh dictionary. The historical plotted order instead called
Narrow and then Wide on the **same** dictionaries. These computations and
the source clone were kept under `%TEMP%`, outside this repository.

| Saved 20 applications; notebook solver | Mean modeled saving | Narrow core optima at lowest setting |
|---|---:|---:|
| Narrow, pickled parameters with division canceled | 4.351999% | 3/20 |
| Wide, pickled parameters with division canceled | 7.173673% | not applicable |
| Narrow, one division | 7.250301% | 17/20 |
| Wide, one division on a fresh copy | 10.957008% | not applicable |
| Wide, second division after the plotted Narrow call | 36.483416% | not applicable |

After this independent run, `python analysis/wang_tpds_figure4.py <clone>`
returned the same **five means**, 3/20 and 17/20 lower-edge counts, and
3 low / 3 interior / 14 high raw-grid split. **No numerical output
disagreed.** The saved notebook output itself prints 7.250301% and
36.483416%, so the latter reproduces the paper's stated 36.4%. The
4.351999% diagnostic is only 0.052 percentage points above its stated 4.3%,
but rounds to **4.4%** to one decimal under ordinary nearest rounding. It
would display as 4.3% if truncated, or could reflect a different fitting
or measurement path. The authors' rounding rule and commercial-meter
observations are unpublished. Calling this an exact reproduction of 4.3%
is unsupported.

The script's 10/20 exact and 20/20 within-one-step comparisons **first snap
the continuous fitted core frequency to the nearest sampled clock**. I
verified those counts. Before snapping, zero solutions exactly equal a raw
grid clock, and only **17/20** lie within 100 MHz of the raw winning clock.
The exceptions are `backpropBackward` (+102.27 MHz),
`convolutionTexture` (−114.10 MHz), and `fastWalshTransform` (−102.86 MHz).
The script is arithmetically correct; its output and the prose need to say
“after rounding to the nearest sampled clock.” The model was fitted to
the same 20 CSV rows per application used for the raw minima. Agreement is
an **in-sample consistency check**, not independent validation of the
authors' meter-based 4.3% or of a physical optimum. Removing the agreement
sentence from §2.7 leaves the section's defensible evidence intact: the
authors' real lower limit is 0.89 of default, and 18/30 released raw-grid
applications have a high-edge winning core clock.

## Is the pickle already scaled?

No, relative to the **released GPU-telemetry CSV fit**. Every commit touching
`apps.pkl` was inspected:

| Commit | Change to the saved fit |
|---|---|
| [`07c87db` (2021-01-12)](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/tree/07c87db1c67900ff47357a2dba3840da964273b9) | Adds 30 ordered applications, storing `P0`, `gamma`, `cg`, `t0`, `D`, `delta`. |
| [`d5cc05b` (2021-01-12)](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/tree/d5cc05b9890f22f346e8e570930eff2a3988d1a8) | Renames `P0` to `p0`; all six numerical values are identical for all 30 names. |
| [`8a0a2e0` (2021-04-26)](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/tree/8a0a2e0ef402b84c428496ce037c6753f19f0873) | Adds derived `p_star` and `t_star`; all six earlier values remain identical. Saves the notebook and figure matching the paper's Figure 4. |
| [`d198af9` (2022-02-08)](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/commit/d198af950c9210b1cae691ca779ee846b815c7fd) | Removes the committed pickle. |

At `8a0a2e0`, [`model.py`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/8a0a2e0ef402b84c428496ce037c6753f19f0873/model.py)
reads the GTX CSV at line 35, fits power to an intercept, normalized memory
frequency and voltage-squared times core frequency at lines 75–88, and
writes the fitted dictionary to `apps.pkl` at lines 124–125. A fresh fit of
all 30 applications using that code's Lasso inputs matches the pickle's
`p0`, `gamma`, `cg`, `t0`, `D`, and `delta` with maximum absolute difference
below **1.6×10⁻¹²**. Neither `model.py` nor `gen.py`, `parse.py`, or
`main.py` divides `p0` or `gamma` by 4.75 or 4.65. The division occurs in
the 2021 [`plot.ipynb`](https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/8a0a2e0ef402b84c428496ce037c6753f19f0873/plot.ipynb)
inside `solve_dvfs()`, for **both** Narrow and Wide calls. `job_master.py`
also generates synthetic task parameters, but does not write `apps.pkl`.

This establishes the pickle as an undivided fit to the released CSV. It
does **not** establish that it is the parameter set used to calculate the
paper's stated commercial-meter result. The CSV's `power/W` is GPU device
telemetry, while the paper's CPU–GPU runtime model includes active CPU
power in `P_G0`. Further, none of these 20 saved applications meets all
six parameter ranges stated in §5.1.3 (the individual pass counts are
5/20 for `p_star`, 5/20 for `gamma/p_star`, 5/20 for `p0/p_star`,
10/20 for `delta`, 6/20 for `D`, and 4/20 for `t0`). Those ranges
therefore do not link the saved fit to the paper's reported application
library without an additional, unpublished transformation or selection.

## What §5.2 discloses

On printed page 11 (PDF page index 10), the relevant sentence reads exactly:

> “Thus, to discuss the potential of GPU DVFS, we shrink the static power P_G0 and enlarge the scaling intervals of two frequencies in our simulations.”

The paragraph then labels Wide as the simulated interval and Narrow as the
realistic interval. It does **not** publish either divisor, say that `gamma`
is divided, say that Narrow's fitted parameters are reduced, or describe
a second division before Wide. In the paper's own Equation (1), `gamma`
multiplies memory frequency; it is a **frequency-sensitive coefficient**,
not static power. Thus §2.7's phrase “the reduction ... describes for its
simulations” has a basis, but it blurs this distinction. The historical
notebook proves what its *plotted model* did. Without the meter data, it
cannot prove the authors' real Narrow measurements were wrong, nor that
the code was the only source of their lower-setting statement. The paper
also claims its derived settings coincide with measurements, which cannot
be tested from this artifact.

## Search for a correction or independent discussion

Exact web queries used: `"2104.00486" "shrunk" "static" Figure 4`;
`"Energy-aware Non-Preemptive Task Scheduling" erratum corrigendum figure 4`;
`"GPU-DVFS-Job-Schedule" "4.75" "4.65"`;
`"4.75" "4.65" "GPU-DVFS-Job-Schedule"`;
`"2104.00486" "Figure 4" correction`;
`"10.1109/TPDS.2022.3181096" erratum`;
`"Energy-aware Non-Preemptive Task Scheduling" "static power" "Figure 4"`;
`"Wang" "Mei" "Liu" "Figure 4" "DVFS" energy 36.4 correction`;
`"GPU-DVFS-Job-Schedule" "p0" "gamma"`;
`"Energy-aware Non-Preemptive Task Scheduling" corrigendum OR correction OR erratum`;
`"Energy-aware Non-Preemptive Task Scheduling" "Figure 4" "static"`;
`site:scholars.hkbu.edu.hk "Xiaowen Chu" "GPU" "DVFS" 2023 2024 2025`;
`"Xinxin Mei" "Qiang Wang" "DVFS" 2023 2024`;
`"36.4%" "GTX 1080Ti" "static power"`;
`site:github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/issues "Figure 4"`.

I queried **all states** of the repository's GitHub issues and pull requests:
one issue concerns benchmark compilation and telemetry, and there are no
pull requests. [Crossref's record](https://api.crossref.org/works/10.1109/TPDS.2022.3181096)
has no correction relation. OpenAlex currently indexes **36 citing works**;
I screened their titles, available abstract terms, and affiliations for
this specific figure/factor issue, not their full texts. A public
[Jefferson Lab discussion page](https://wiki.jlab.org/epsciwiki/index.php/Discussion_of:_Energy-Aware_Non-Preemptive_Task_Scheduling_With_Deadline_Constraint_in_DVFS-Enabled_Heterogeneous_Clusters)
questions whether the 36% result requires the wide interval, but does not
mention the factors or identify an erratum. I found **no accessible
correction or independent discussion of 4.75/4.65** in this search.
This is a search limit, not evidence that none exists.

## Exact wording proposed; no source-file edits

In `docs/PAPER_DRAFT.md` §2.7's **2026-09-25 correction**, keep the four-row
table. Replace the sentence beginning “Its solver divides the fitted
static power” with:

> Its publication-era `model.py` fits `p0` and `gamma` directly to the released GPU-power CSV. The plotting notebook's solver divides `p0` by 4.75 and `gamma` by 4.65 on every call, including Narrow, and therefore divides both again before plotting Wide. In the paper's model, `gamma` multiplies memory frequency; it is not static power.

Replace the paragraph beginning “The condition that reproduces their stated
4.3%” and the following “What survives” paragraph with:

> On the saved, undivided CSV-fitted parameters, the Narrow model gives 4.352% mean saving and places only 3 of 20 optima at its lower core bound; 14 of 20 lie at 1886 MHz or above. The paper states 4.3%, but 4.352% rounds to 4.4% to one decimal; the close value does not reproduce its commercial-meter measurements. The plotted Narrow bars instead use once-divided `p0` and `gamma`, give 7.25%, and put 17 of 20 at the lower bound. The plotted Wide bars use both terms divided a second time and give 36.48%. Widening the interval alone, with the saved parameters unchanged, gives 7.17%; it cannot by itself reproduce the plotted 36.48%. Section 5.2 of [22] says the authors shrink static power and widen frequency ranges in their simulations, but does not specify the two factors or say that the Narrow bars also use reduced parameters. The released CSV power is GPU telemetry, while the authors describe a commercial meter and a CPU–GPU model that includes active CPU power. The raw-grid count and fitted-model agreement use the same measurements; after rounding fitted core clocks to the sampled grid, 10 of 20 match the raw winner and the other 10 are one grid step away. This is an in-sample check, not independent evidence about their meter result.
>
> The 0.89 real lower bound and the authors' attribution of their small saving partly to the narrow interval remain usable prior art. In the released GTX 1080 Ti grid, 18 of 30 applications have a high-edge best sampled core clock. An edge winner does not locate the unsampled physical optimum or establish which direction it lies beyond the measured range. Cite [22] for its measured interval and modeled wider scenario; use this project's own sweeps for claims about where its measured efficiency optima lie.

Replace `CLAUDE.md`'s **“RESOLVED 2026-09-25” paragraph and its three
bullets** with:

> ✅ **Artifact reproduced 2026-09-25; interpretation audited 2026-09-26.** The 2021 `8a0a2e0` artifact maps Figure 4 to the first 20 ordered GTX applications. Their raw `time × GPU telemetry power` grid has 3 low / 3 interior / 14 high core winners. The earlier and 2021 pickles have identical fit values, and `model.py` reproduces those values from the CSV to numerical precision: `p0` and `gamma` were not pre-divided in the pickle. `solve_dvfs()` divides `p0` by 4.75 and `gamma` by 4.65 for both Narrow and Wide; plotting Narrow first mutates the same dictionaries, so Wide receives a second division. `gamma` is the memory-frequency coefficient, not a static term. On saved, undivided parameters the means are 4.352% Narrow and 7.174% Wide, with only 3/20 Narrow solutions at its low bound. The plotted means are 7.250% Narrow and 36.483% Wide, with 17/20 Narrow solutions at its low bound. The 4.352% value is close to the paper's reported 4.3% but rounds to 4.4% at one decimal, and it neither reconstructs the unreleased commercial-meter measurements nor establishes that these GPU-only fitted parameters were used for the reported real result. The model is fitted to the same CSV rows used for the raw argmin: **after snapping** each continuous modeled clock to the nearest 100 MHz sampled clock, 10/20 coincide and 20/20 lie within one sampled step; in actual MHz only 17/20 are within 100 MHz. Section 5.2 states that static power and frequency intervals are changed for simulations but does not disclose the notebook's Narrow reduction, `gamma` reduction or repeated Wide reduction. The paper's 0.89 real lower bound remains prior art. Do not treat Figure 4 as a matched system-power result for the released CSV or assert an error in the authors' measurements from the plotting code alone.

The accompanying `CLAUDE.md` sentence that says “Most of their rise comes
from shrinking static power” should also say **“the plotted 36.4% requires
reducing both `p0` and the memory-frequency coefficient `gamma`, in addition
to widening the interval.”** This preserves the dated correction while
removing an incorrect description of `gamma`.

When applying the proposal, check `docs/RELATED-WORK.md` §7 and
`docs/agents/GPT-QUEUE.md`: both also call the notebook's joint `p0` and
`gamma` change a static-power division. The 2026-09-25 findings record is
historical and now links to this audit at its top. The paper and `CLAUDE.md`
still contain the “4.35% (paper says 4.3%)” comparison, which needs the
rounding caveat above.

Before writing, `python run_tests.py --quiet` passed **1,084 checks across
35 suites**. `analysis/audit_claims.py`, `build_data_manifest.py --check`,
and `verify_citations.py --check` exited successfully. These checks do not
validate the external paper's unreleased meter trace.

---

## Claude review, 2026-09-26: accepted, all four corrections applied

**Verified here, independently:**
- **Pickle history:** `07c87db`, `d5cc05b` and `8a0a2e0` hold identical `P0`/`p0`, `gamma`, `cg`,
  `t0`, `D` and `delta` for all 30 names (maximum difference 0.0).
- **The §5.2 sentence:** read against the arXiv PDF text; it is quoted exactly.
- **4.352% rounds to 4.4%:** arithmetic.
- **Unrounded agreement is 17 of 20:** `backpropBackward` (+102), `convolutionTexture` (−114) and
  `fastWalshTransform` (−103 MHz) are the exceptions. The script now prints both counts and labels
  the agreement in-sample.
- **`gamma`:** it multiplies memory frequency in the solver's power term,
  `p0 + gamma*fm + cg*v²*fc`.
- **The §5.1.3 ranges:** 0 of 20 saved fits lie inside all six, with the same per-range counts GPT
  gives.
- **One step further:** 0 of 20 lie inside the three power ranges under **any** of undivided,
  divided once or divided twice. So no reduction the notebook applies maps the saved fit onto the
  paper's stated library either.

**The model-fit refit (1.6×10⁻¹²) was not re-run here.** The pickle-history result supports the
same conclusion independently: the values never changed after the first commit.

**Applied:**
- **`analysis/wang_tpds_figure4.py`:** condition labels (`p0` and `gamma`, not "static terms"),
  the rounding line, and the unrounded count with its in-sample label. The limits paragraph now
  cites the parameter-range mismatch.
- **`PAPER_DRAFT.md` §2.7:** the correction was rewritten, with a dated "narrowed 2026-09-26" note
  naming the three errors and how they got in, and the 18/8 edge statement made exact (26 of 30 at
  an edge).
- **`CLAUDE.md`:** the headline "the discrepancy is in THEIR FIGURE, not their data" is struck as an
  overreach. The three struck clauses are kept visible, and a 🛑 line forbids saying the authors'
  measurements are wrong.
- **Pointers:** `RELATED-WORK.md` §7, `GPT-QUEUE.md` and the `PRIOR-ART-20260913.md` pointer are
  narrowed to match.

GPT's proposed paragraphs were used for substance, not verbatim.
