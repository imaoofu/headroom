# GPT — the next prompts, 2026-09-22

**Written 2026-09-22 by Claude, after GPT's 09-21 tooling pass and 09-22 literature pass both
checked out.** The previous version of this file (the predictor audit, completed 2026-09-20) is in
git history: `git show fc1ca61:docs/agents/GPT-PROMPT-NEXT.md`.

🔑 **What changed: GPT now gets in-repo work, not just searches.** Its record says it can take it:

| pass | what was checked here | result |
|---|---|---|
| 09-21 time-join tooling | ran on hardware across **61 sweeps, 775 points** on 09-22 | ✅ no empty point, 1.99 samples/s against a 0.50 s interval |
| 09-22 inventory counts | re-derived from its CSV | ✅ 109 / 95 / 56 exact |
| 09-22 MP2884A, Reddit Method 3/4 | spot-checked | ✅ |
| 09-22 SBAC-PAD 2020 | **read here in full** | ⚠️ it cited Table IV without flagging that Table IV **relocates the optimum**. That turned out to narrow a live claim (`RELATED-WORK.md` §9). **Report what a table shows, not only what the paper is about.** |

**Literature work continues** (Job 5). It is no longer the only kind of job.

---

## 📌 Send this once per session, before any job

> You are working inside a research repository shared with two other agents (Claude Code and a
> Codex session) on the same Windows machine and the same working tree. Read `AGENTS.md` and
> `CLAUDE.md` in full before touching code. The traps in this codebase (PowerShell 5.1, BOM and
> cp1252 encoding, CRLF line endings, the claims auditor's design) cannot be guessed.
>
> **Hard rules for every job:**
>
> 1. **`data/` is read-only.** Never write, re-save, re-encode or re-line-end any file under it,
>    not even temporarily. The edit guard in `tools/claude-hooks/` covers Claude only; it does not
>    cover you, and all four CI gates **pass on a silently altered measurement**. Work on copies in
>    a temp directory.
> 2. **Never edit `docs/PAPER_DRAFT.md`.** Findings about the paper go in your record.
> 3. **Never change a claim formula in `analysis/claims_*.py` to make the audit pass.** A claim that
>    does not match the paper is a *finding*: report it.
> 4. **Never change GPU state.** No `nvidia-smi -lgc/-rgc/-pl`, no Afterburner, no NVML writes, no
>    HWiNFO control.
> 5. 🛑 **Check the GPU is not mid-sweep before running anything heavy**, including
>    `python run_tests.py`. The test suite beside a sweep cost **9.38% throughput** on 2026-09-18.
>    Run this first, and if it prints anything, wait:
>    `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'Invoke-FrequencySweep|Invoke-LoggedSweep|gpu_workload' } | Select-Object ProcessId, CommandLine`
> 6. **Shared tree.** Run `git status` first. Do not edit a file that already has someone else's
>    uncommitted changes unless the job names it. **Do not commit.** Leave your changes for review
>    and list every file you touched.
> 7. **Recompute; do not reason from a summary.** Say, for every number in your record, whether you
>    recomputed it or took it from a document.
> 8. **One job per session.** If it grows, stop and report what you found rather than widening it.
>
> **Finish every job by** running `python run_tests.py`, `python analysis/audit_claims.py`,
> `python analysis/build_data_manifest.py --check` and `python analysis/verify_citations.py --check`
> (after rule 5's check), then filing `docs/gpt-findings/YYYY-MM-DD-<slug>.md` with a row in that
> README. State what you did **not** verify.

---

## Job 1: adversarial audit of today's 5060 Ti results. **Send first.**

**Why first:** five results landed on 2026-09-22 and none has had an outside reader. All three of
GPT's earlier audits produced retractions that held up when checked.

> **Adversarial audit: the RTX 5060 Ti results of 2026-09-22.** One chip, one session, driver
> 616.92, run unattended. Recompute each from the committed CSVs. For each, say whether the
> README's conclusion follows, and give the strongest case that it does not.
>
> | claim | directory under `data/frequency-sweeps/` |
> |---|---|
> | Per-workload optima reproduce **9 of 12** between two identical stock suites; winner margins median **0.99%**; this recalibrates three existing claims | `5060ti-stock-repro-20260922/` |
> | Large historical `membw` dips are **activity-driven**; a **reproducible ~0.5–0.85% dip at 1627 MHz** appears in 4 of 6 silent replicates across two configurations | `5060ti-membw-silent-20260922/` |
> | The registered Profile 1 prediction **holds** (median 2010, 7 of 12 individually) | `5060ti-p1-suite-20260922/`, `5060ti-p4-suite-20260922/`, `docs/REGISTERED-PREDICTIONS.md` §2 |
> | The floor ends between **1567 and 1575 MHz**; descending equals ascending (**+0.00%**) | `5060ti-finefloor-20260922/` |
> | Isolated 8–11% point losses are **caused by agent activity** (4 bad points, then 1, then 0 as the agent went quiet) | `5060ti-finefloor-20260922/README.md` |
>
> Attack these specifically:
>
> 1. **9 of 12:** is "agree" defined on the target grid or on achieved clock? What agreement rate
>    would chance produce, given 13 grid points and near-ties? Can **n = 2 passes** recalibrate
>    the P1/P4 comparison and the negative control, as the README says it does?
> 2. **The 1627 MHz dip:** how is "departure from the local trend" computed, and does the dip
>    survive a different trend definition? Is it a grid artifact? Check achieved clock, memory
>    clock and power at that point against its neighbours.
> 3. **Activity as the cause:** the operator noted the card had **just been switched on** that
>    morning. Is "agent went silent" confounded with warm-up or time since boot? What would
>    separate them?
> 4. **P1 "holds":** compare the result with what `REGISTERED-PREDICTIONS.md` §2 said *before*
>    collection. Was a success criterion stated? Is 7 of 12 consistent with it?
> 5. **+0.00%:** what quantity was compared between the descending and ascending runs, and over
>    which points?

---

## Job 2: content-hash integrity gate for measurement files

**The known hole** (`docs/TODO-20260918.md` item 16): a Codex agent changed one voltage reading, and
the audit, 828 tests and both `--check` gates all passed.

> **Build a content-hash gate for `data/`.** Detection, not prevention: it must catch an altered or
> deleted measurement file whichever agent or person made the change.
>
> - **Decide where the hashes live, and justify it in the record.** Put them **outside `data/`**.
>   Claude's edit guard denies writes inside `data/` by default, so a file there would block the
>   agent that most often adds sweeps. `data/MANIFEST.json` has no hashes today.
> - 🛑 **Make the hashes independent of line endings.** Windows working copies are CRLF, CI checks
>   out LF, and this repository already has two third-party hashes that differ only by line ending
>   (`CLAUDE.md`, the consumer-dataset section). Normalise before hashing, and record the convention
>   inside the hash file.
> - Write `--write` and `--check` modes. Wire `--check` into `run_tests.py` or CI
>   (`.github/workflows/ci.yml`), and state which one and why.
> - **Scope:** measurement files (CSV, JSON). Exclude `.md`, which is legitimately edited.
>   Decide what an **unhashed new file** does: fail or warn. A new sweep must not slip in unhashed.
> - **Prove it catches the demonstrated case.** Use a temp copy of
>   `rtx3070ti-20260825/hwinfo-silent/*_voltage.csv`, change 855 MHz from 0.819 to 0.900 V in the
>   copy, and show the gate fails. Include a test suite.
> - ⛔ **Do not run `--write` against the real `data/` tree.** Hand the first real write to review.

---

## Job 3: a registered analysis for Session D, written before the data exists

**Why this matters:** RTX 3070 Ti Session D is the planned causal replication on a second chip, and
its predictions are registered in the runsheet. If the scoring code is committed before collection,
the **analysis** is registered too, and nobody can tune it to the result afterwards.

> **Write `analysis/score_session_d.py`.** Read the registered predictions in
> `data/frequency-sweeps/rtx3070ti-20260825/SESSION-D-RUNSHEET.md`: **4a** (Edit 1, shorten the
> floor), **4b** (Edit 2, the negative control), and the section "What each outcome means".
> ⚠️ **The edits may still change before collection.** Applying Edit 1 in Afterburner is unresolved
> at the time of writing. Keep every runsheet-derived number (edit boundaries, predicted optima,
> floor voltage) in **one named constants block** that quotes the runsheet line it came from, so a
> changed edit is a one-place diff and not a silent retune. Given a Session D sweep directory, the script computes the median and
> per-workload efficiency optima, the floor extent from the voltage extracts, and a verdict
> against **each** registered outcome, including the ones where the claim fails.
>
> - Efficiency and optimum must be computed **exactly as the existing suites compute them**. Find
>   that code, reuse it rather than re-deriving it, and cite where it lives.
> - Report the median. Apply the **9 of 12 reproducibility result** (Job 1's first claim): do not
>   let a per-workload count carry a verdict alone.
> - Under Edit 2, six targets clip to about 1500 MHz. The runsheet says to report the clipped rows
>   as **one bin**. Handle that.
> - Test on synthetic fixtures covering a pass, a fail and a control-also-moves case. **Never edit
>   the runsheet's predictions.**

---

## Job 4: DOI support in `verify_citations.py`

> `analysis/verify_citations.py` registers arXiv ids only. Add DOIs via Crossref
> (`https://doi.org/<doi>` with `Accept: application/vnd.citationstyles.csl+json`). Follow the
> arXiv path's existing contract: offline is not a citation failure, and `--check` must stay
> network-free in CI. Register the DOIs cited in `docs/RELATED-WORK.md` §8–9, and report any whose
> Crossref title or author list disagrees with what the file says. **This project has
> invented a co-author before.**

---

## Job 5: literature, targeted at the claim that just narrowed

**The cold boundary is closed for this model:** it has read `CLAUDE.md`. So this is a directed
search, not a novelty check. A genuine cold check still needs a fresh chat, no repository, and
`NOVELTY-CHECK-BRIEF.md`.

> 1. **Forward citations of Mendes, Tomás & Roma, SBAC-PAD 2020**, *Exploiting non-conventional
>    DVFS on GPUs*. Its Table IV moves an EDP optimum when the V–F relationship changes. Find who
>    built on it, and look specifically for: a **region-targeted** curve edit rather than a global
>    voltage; **NVIDIA** hardware; a **negative control** (an edit that should not move the
>    optimum); or an optimum **predicted in advance** from a floor voltage. Report the table
>    evidence, not the abstract's framing.
> 2. **GreenMD** (ACM TOPC 2023, `10.1145/3583590`): verify the GTX 1660 Super, MSI Afterburner
>    and 10 mV details you reported. **None is in the abstract.** Quote the page they come from, or
>    withdraw them.
> 3. **The 14 no-abstract records** in `docs/gpt-findings/2026-09-22-forward-citation-abstract-inventory.csv`.
> 4. **Wang et al. Figure 4, 20 benchmarks against the CSV's 30 applications:** check
>    `HKBU-HPML` GitHub repositories (branch `master`, not `main`) for a benchmark list that maps
>    the two.

---

## Job 6, small: `distinct_clocks_measured` false-alarms on fine grids

> `docs/TODO-20260915.md` item 17. `Invoke-FrequencySweep.ps1` buckets achieved clocks at a fixed
> **25 MHz**, so a fine grid under-reports: the 2026-09-18 fine-floor run recorded
> `distinct_clocks_measured` **10** against **13** genuinely distinct clocks, with every lock held.
> It is the same fixed-width assumption the voltage join had. Make the bucket width follow the
> grid spacing. Reproduce the 10-versus-13 miscount from the committed 09-18 CSV (read-only) before
> fixing it, and show that the coarse grids already committed give **unchanged** counts. You are
> editing a script that locks GPU clocks: **edit and test it, never run a sweep with it.**
> Misreporting, not corruption: low priority.

---

## ⛔ Still do not ask it

- **Anything settled.** `GPT-QUEUE.md` lists these.
- **To write the paper.** It files records; the paper is changed after verification.
- **Anything the hardware settles faster.** The 1627 MHz fine grid is an unattended sweep Claude
  can run, not a question to reason about.
