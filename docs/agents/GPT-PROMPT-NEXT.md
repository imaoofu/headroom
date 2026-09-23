# GPT — the next prompts, batch 2 (Jobs 7–14), 2026-09-22

**Written 2026-09-22 by Claude, after GPT's Jobs 1–6 were all reviewed and committed.** Batch 1 is
in git history: `git show ee82b33:docs/agents/GPT-PROMPT-NEXT.md`. Earlier: `git show fc1ca61:…`.

## How batch 1 went — every job was used, and every one needed something at review

| job | outcome | what review found |
|---|---|---|
| 1 audit of the 09-22 results | ✅ every figure reproduced | caught three overclaims: the "dip" never fell, "activity-driven" was confounded, one stock pair is one draw |
| 2 hash gate | ✅ in CI, both OSes | scope was CSV/JSON only and missed 76 provenance files. **That gap was in Claude's brief** |
| 3 Session D scorer | ✅ after fixes | **scored on achieved clock with EXACT equality**; every fixture had achieved == target, so no test could see it. Also found the registration-vs-runsheet mismatch, which was confirmed |
| 4 DOI verifier | ✅ | one read label (preprint vs published) tightened |
| 5 directed literature | ✅ clean | — |
| 6 grid-aware clock count | ✅ after fixes | **the new file was not added to the USB kit sync**, and **its test broke CI's Linux leg**: PowerShell 7 unrolls a top-level JSON array, 5.1 does not |

🔑 **Three of those defects share a shape: the code was right for the case the author pictured and
wrong for a case one step away.** Achieved ≠ target. Kit ≠ repo. PowerShell 7 ≠ 5.1. Rules 9–12
below exist for that.

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
>    not even temporarily. Work on copies in a temp directory.
> 2. **Never edit `docs/PAPER_DRAFT.md`.** Proposed paper text goes in a separate draft file.
> 3. **Never change a claim formula in `analysis/claims_*.py` to make the audit pass.** A claim that
>    does not match the paper is a *finding*: report it.
> 4. **Never change GPU state.** No `nvidia-smi -lgc/-rgc/-pl`, no Afterburner, no NVML writes, no
>    HWiNFO control, and **never execute a runner under `tools/hwinfo-logging/experiments/`**.
> 5. 🛑 **Check the GPU is not mid-sweep before running anything heavy**, including
>    `python run_tests.py`. The test suite beside a sweep cost **9.38% throughput**. Run this, and if
>    it prints anything, wait:
>    `Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'Invoke-(Frequency|Logged)Sweep[.]ps1|gpu_workload[.]py|Run-(Activity|Offset)' -and $_.CommandLine -notmatch 'Get-CimInstance' } | Select-Object ProcessId, CommandLine`
> 6. **Shared tree.** Run `git status` first. Do not edit a file that already has someone else's
>    uncommitted changes unless the job names it. **Do not commit.** List every file you touched.
> 7. **Recompute; do not reason from a summary.** Say, for every number, whether you recomputed it
>    or took it from a document.
> 8. **One job per session.** If it grows, stop and report rather than widening it.
> 9. 🆕 **Never run `python analysis/check_data_hashes.py --write`.** It re-baselines the measurement
>    hashes, and only a reviewer who has read the diff may do that.
> 10. 🆕 **Test fixtures must include the awkward case, not just the pictured one.** Achieved clocks
>     that are *not* equal to their targets. An even split of twelve that puts the median between
>     two grid points. A clipped bin. **If every fixture is exact, a comparison bug is invisible.**
> 11. 🆕 **CI runs Python tests on Linux under PowerShell 7 as well as Windows 5.1.** Any test that
>     shells out to PowerShell must work under both. Known difference: PS7's `ConvertFrom-Json`
>     unrolls a top-level array; wrap input as an object.
> 12. 🆕 **If a sweep or kit tool gains a file it depends on, add that file to
>     `tools/collection-kit/Sync-Kit.ps1`.** Otherwise the shop-machine kit breaks, at the end of a
>     run.
>
> **Finish every job by** running `python run_tests.py`, `python analysis/audit_claims.py`,
> `python analysis/build_data_manifest.py --check`, `python analysis/verify_citations.py --check`
> and `python analysis/check_data_hashes.py --check` (after rule 5), then filing
> `docs/gpt-findings/YYYY-MM-DD-<slug>.md` with a row in that README. State what you did **not**
> verify.

---

## Job 7: pre-flight review of tomorrow's unattended activity test. **Send first — it runs tomorrow.**

**Why first:** it runs unattended on the bench with nobody watching, and nobody outside has read it.
The last registered scorer written before its data (Session D) had a verdict-breaking bug.

> **Adversarially review the registered activity A/B test before it runs. Do not run it.**
> Read `docs/REGISTERED-PREDICTIONS.md` §5, `tools/hwinfo-logging/experiments/Run-ActivityAB.ps1`,
> `tools/hwinfo-logging/experiments/Start-ActivityLoad.ps1` and `analysis/score_activity_ab.py`.
>
> 1. **Does the runner do what §5 registers?** Check the uptime gate, the two warm-ups, S A A S × 3,
>    and that load detection runs identically in both conditions.
> 2. **PowerShell 5.1 traps.** Can function output leak into a return value? Does
>    `Start-Process -PassThru` give a real exit code? What happens if the activity generator
>    outlives its run? Is there non-ASCII inside a string literal?
> 3. **Does the scorer compute what §5 registers?** Test it on synthetic experiment directories
>    in a temp dir, with rule 10's awkward cases: a missing run, an excluded active run, losses
>    tied at the 2% threshold, a warm-up with losses, which must not count.
> 4. **Is the design able to fail?** Could the proxy activity be too light to produce any loss,
>    so the registered "supported" outcome is unreachable? Say so if yes. Do not change §5.
>
> Report defects with a proposed fix; **do not edit the registered thresholds.**

---

## Job 8: the search log that tonight's result now owes

**The search rule in CLAUDE.md fires:** a result that earns a 🔑 must carry a search log. Tonight's
4c result carries one: *"an NVML offset moves the load floor programmatically."*

> **Is it already known that a core-clock offset shifts the whole NVIDIA V/F curve, so that the
> voltage at clock f under offset −k equals the stock voltage at f+k?** Tonight's measurement, on one
> RTX 5060 Ti: `data/frequency-sweeps/5060ti-nvml-offset-20260922/README.md`.
>
> - **Search the enthusiast and tool communities first.** Afterburner's core-clock slider is widely
>   described as shifting the curve, and this may be common knowledge. Search MSI Afterburner and
>   Unwinder's docs and forum posts, LACT, GreenWithEnvy, `nvidia-settings` and Coolbits docs,
>   NVIDIA's own NVML reference for `nvmlDeviceSetClockOffsets`, and overclocking guides.
> - Then academic sources: GPU DVFS papers that apply clock offsets and log voltage.
> - **Specifically:** does anyone contrast it with Guerreiro et al. (TPDS 2019), who report voltage
>   *constant* under `nvidia-settings` offsets on Maxwell/Pascal/Kepler?
> - Write a **search log**: the queries, the date, what was found, what could not be reached. State
>   honestly if the curve-shift behaviour is well known, because then the only literature-facing
>   content is the Guerreiro contrast.

---

## Job 9: adversarial audit of the 4c offset result

> **Audit `data/frequency-sweeps/5060ti-nvml-offset-20260922/` against `REGISTERED-PREDICTIONS.md` §6**,
> registered in `d0b9724`, before the data. Recompute from the CSVs and voltage extracts.
>
> 1. **The pairing** "V_B(f) = V_A1(f+300)" interpolates voltage in achieved clock. Does a different
>    pairing rule change the verdict? How much does a 5 mV VID grid constrain the result?
> 2. **The reported voltage is a VID lookup, not a rail measurement** (CLAUDE.md). What exactly does a
>    shifted lookup demonstrate, and what does it not?
> 3. **Is "4d is superseded" right?** 4d's criterion was "power at f with −300 should match f+300
>    without". Is it truly ill-posed, or was it meant differently? Check the git history of the 4d
>    wording, e.g. `git log -S "f+300"`.
> 4. **The XBAR observation**: is it as "tracks the operating point" as the README says, across all
>    15 points?

---

## Job 10: register the NVML offset ladder (worklist 4o) — draft, before any data

**Why:** 4c showed an offset moves the load floor programmatically, so a ladder can run
unattended with no hand-built curves. It must be registered before it runs.

> **Draft a registration and a runner. Do not add them to `REGISTERED-PREDICTIONS.md`, and do not run
> anything.** Write:
> - `docs/agents/DRAFT-offset-ladder-registration.md`
> - `tools/hwinfo-logging/experiments/Run-OffsetLadder.ps1`, following `Run-OffsetPrecondition.ps1`
>   closely, including its reset-in-`finally` and its two fixed PowerShell traps
>
> - **Design:** stock Profile 3, the standard twelve-workload suite on the 13-point 1237–3090 MHz
>   grid, offsets **0 / −150 / −300 / −450** (the tool refuses below −500). Reuse the iteration counts
>   of `data/frequency-sweeps/5060ti-stock-repro-20260922/`, and cite where you got them.
> - **Predictions, derived from committed data and not tuned:** the stock floor ends at 1567–1575 MHz
>   (`../5060ti-finefloor-20260922/`). Under −k the rule predicts the median suite optimum at the grid
>   point nearest to (floor end − k). Work out each rung's predicted grid point, and **say which rungs
>   the 155 MHz grid can actually distinguish**. If two rungs predict the same point, say so; that
>   rung tests nothing.
> - **What refutes it**, stated per rung and for the monotone trend.
> - **What it does NOT test:** a global offset shifts the whole curve, while the Afterburner rungs
>   move only the floor region. Say how the two ladders complement each other.
> - Include a scorer or reuse one, with rule-10 fixtures.

---

## Job 11: a committed, tested Afterburner profile decoder

**Why:** the decoder that verified rung B tonight exists only in a scratch file. And tonight showed
it is **wrong at offset boundaries**: see the rung B snapshot README.

> Write `tools/afterburner/decode_profiles.py` and its tests. It reads the `VEN_*.cfg` `VFCurve`
> hex as documented in `docs/AFTERBURNER-PROFILES.md`: a header, then 127 × (offset, voltage mV,
> base MHz) float32.
> - **It must reproduce the committed decodes exactly.** Test against
>   `data/afterburner-profiles/5060ti-profiles-20260908b-p4-plateau-3030.json` for every profile.
> - **It must FLAG, not silently decode, any point where the offset field changes value.** Rung B's
>   845 mV point is stored (+176, base 2362); the editor shows 2362, +0; and a byte-identical re-save
>   proved they are one state. Snapshot: `data/afterburner-profiles/5060ti-profiles-20260922-rungB/`.
>   Test that this point is flagged.
> - Add a `--verify-rung` mode that runs §1's five registered pre-run checks against a snapshot and
>   prints each result. Rung B's expected outcome: checks 1, 2, 4, 5 pass and check 3 fails at
>   650–690 mV.

---

## Job 12, analysis only: is the `membw` 1627 MHz stall in the historical data too?

> On 2026-09-22, 5 of 6 silent `membw` runs sat below their own chord at **1627 MHz** achieved, while
> the rest of each curve sat above it. That is a **stall in the rise, not a fall**:
> `data/frequency-sweeps/5060ti-membw-silent-20260922/README.md`. **Using only committed CSVs**, check
> every other `membw` sweep on the 5060 Ti that has a point near 1627 MHz. Compute chord residuals
> at every interior point, in achieved clock, exactly as that README does. Does 1627 stand out
> historically, across configurations and dates? Report the count, and every sweep that does not
> fit.

---

## Job 13: draft replacement text for the paper's §2 — as a proposal file

**Why:** CLAUDE.md says §§2.1–2.5 need rewriting against `docs/RELATED-WORK.md`, and **the paper cites
no Mendes paper at all**, although SBAC-PAD 2020 now bounds the causal claim.

> **Write `docs/drafts/section2-related-work-proposal.md`. Do not touch `PAPER_DRAFT.md`.**
> Propose replacement text for §§2.1–2.5, built only from sources `RELATED-WORK.md` marks as read.
> Mark every sentence that depends on an abstract-only source. Follow the "What it must NOT grow
> back into" list in CLAUDE.md's contribution section: **no "first", no "novel", no "unpublished"**.
> Include a table mapping each current §2 sentence to its replacement and the reason. Claude
> reviews it and edits the paper.

---

## Job 14, larger: pin the numbers in one unaudited paper section

> CLAUDE.md lists unaudited sections that carry real numbers: 3.3.2, 3.3.3, 5.4.2, 5.5.5, 5.6.3, 5.7
> and 5.7.7. **Pick ONE, say why, and write claims for its numbers** in the right `claims_*.py`
> module. Follow "The claims auditor" section of CLAUDE.md exactly: each claim renders its string
> from the CSVs.
> - 🛑 **A claim that does not match the paper is a FINDING. Report it; change neither the paper nor
>   the formula to make it pass.**
> - Adding claims changes the counts in CLAUDE.md's canonical coverage block, which
>   `claims_repo.py` audits. Update **only that block**, and show the before/after counts.

---

## ⛔ Still do not ask it

- **Anything settled.** `GPT-QUEUE.md` lists these.
- **To write the paper.** It drafts; Claude edits the paper after verification.
- **Anything the hardware settles faster.**
- **A cold novelty check.** This model has read the repository, so its boundary is closed. A
  genuine cold check needs a fresh chat, no repository, and `NOVELTY-CHECK-BRIEF.md`.
