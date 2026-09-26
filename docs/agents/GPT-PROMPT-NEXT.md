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

✅ **DONE BY CLAUDE, 2026-09-24**, while GPT was at its usage limit. **Do not send.** Answer: yes, 8 of
10 historical sweeps on curves with the stock slope below the floor, 0 of 3 on the flattened full
tune. The record is in `data/frequency-sweeps/5060ti-membw-stall-20260924/README.md`, from
`analysis/membw_chord_history.py`. **Next on this list: Job 13.**

> On 2026-09-22, 5 of 6 silent `membw` runs sat below their own chord at **1627 MHz** achieved, while
> the rest of each curve sat above it. That is a **stall in the rise, not a fall**:
> `data/frequency-sweeps/5060ti-membw-silent-20260922/README.md`. **Using only committed CSVs**, check
> every other `membw` sweep on the 5060 Ti that has a point near 1627 MHz. Compute chord residuals
> at every interior point, in achieved clock, exactly as that README does. Does 1627 stand out
> historically, across configurations and dates? Report the count, and every sweep that does not
> fit.

---

## Job 13: draft replacement text for the paper's §2 — as a proposal file

✅ **DONE BY CLAUDE, 2026-09-24**, while GPT was at its usage limit. **Do not send.** The proposal is
`docs/drafts/section2-related-work-proposal.md`. It found 12 problems in the current §§2.1–2.5
and the retracted contribution sentence still in the introduction. **Next on this list: Job 14.**

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

✅ **DONE BY CLAUDE, 2026-09-24**, while GPT was at its usage limit. **Do not send.** §5.7's introduction
was chosen: it is on this list, had 17 numbers and no claim. Four claims now pin its header and its
two-knob table. **Two cells were findings, and the paper was corrected, not the formula:**
- `membw` memory "+3.6% to +16.1%" paired targets 15 MHz apart; at identical targets it is
  +2.4% to +17.1%;
- "−29.6%" was memory-only's lead written as a loss; the loss is 22.9%.
Counts: claims 288 → 292 (242 → 246 without fetched data); unaudited sections 15 → 14; §5.7 family
88 → 92. This list's jobs 12–14 are all done.

> CLAUDE.md lists unaudited sections that carry real numbers: 3.3.2, 3.3.3, 5.4.2, 5.5.5, 5.6.3, 5.7
> and 5.7.7. **Pick ONE, say why, and write claims for its numbers** in the right `claims_*.py`
> module. Follow "The claims auditor" section of CLAUDE.md exactly: each claim renders its string
> from the CSVs.
> - 🛑 **A claim that does not match the paper is a FINDING. Report it; change neither the paper nor
>   the formula to make it pass.**
> - Adding claims changes the counts in CLAUDE.md's canonical coverage block, which
>   `claims_repo.py` audits. Update **only that block**, and show the before/after counts.

---

## Job 15, larger: "Headroom Bench", a double-click app for shop machines. BUILD ONLY, never run on a GPU

**Why:** at a shop machine Raymond copies ~20 commands into an elevated PowerShell one at a time
(`docs/GPU-WORKLIST-3070TI.md`, Commands C0–C10), starts and stops every HWiNFO log by hand, and
reads each check by eye. **No agent can help there:** neither Claude nor GPT is installed on shop
machines. Only Raymond, the USB kit and whatever runs from it.

> Build **Headroom Bench**, an app Raymond runs from the USB kit on a shop machine. He double-clicks
> `RUN-BENCH.bat`, approves **one** UAC prompt, **picks runs from a list**, optionally
> **customises** them, and presses **Start**. The app then does everything a person does today:
> the gates, profile switches, HWiNFO logs, checks and sweeps, stopping only for what needs hands.
> Put it in `tools/bench-app/`. **You write and test the code in this repository. You never run it
> for real** (rule 4). Its first live run will be by Claude on the local RTX 5060 Ti.
>
> **Read first, in full:**
> - `tools/collection-kit/`: Collect.ps1, Sync-Kit.ps1, README;
> - `tools/hwinfo-logging/`: both scripts and the README, especially **"Why an agent cannot click
>   it"** and **"The two mistakes that cost an hour"**;
> - `tools/frequency-sweep/Invoke-FrequencySweep.ps1`;
> - the Commands section of `docs/GPU-WORKLIST-3070TI.md`;
> - `docs/GPU-BENCH-RULES.md`;
> - CLAUDE.md's "Safety invariants" and "Bugs found by testing".
>
> **HWiNFO logging: the app does it, not Raymond.** HWiNFO runs elevated, and Windows (UIPI)
> silently drops input from lower-integrity processes, which is why an AI agent cannot press its
> Log button. **An app that is itself elevated is at the same integrity level and can.**
> `tools/hwinfo-logging/Invoke-HwinfoLogging.ps1` already does exactly this. It was verified end to
> end and drove all 61 logs of 2026-09-22. **Reuse it; do not reinvent it.** The app also launches
> HWiNFO itself from the kit (no second UAC prompt: it inherits the app's elevation).
> - ⚠️ It was verified on HWiNFO **8.50-6020**. The kit carries **8.52-6060**. So if a
>   `hwinfo-start` fails (the script's exit codes 4, 6 or 7), **fall back to a `human` step**: show
>   "click Log Start in the Sensors window, save as <exact path>", then **verify the log is growing**
>   before continuing, exactly as the script does. Record in the session JSON which path was used.
> - ⛔ **Do not build a voltage reader of your own.** NVML exposes no voltage. The only alternatives
>   are undocumented NVAPI, which is out of scope in CLAUDE.md, and HWiNFO shared memory, which the
>   free version limits to 12 hours. HWiNFO's own CSV stays the voltage source.
>
> **What to build:**
> 1. **`RUN-BENCH.bat` plus a WinForms window written in PowerShell 5.1** (`Bench-Window.ps1`;
>    WinForms ships with Windows, so nothing is compiled or installed). The `.bat` **re-launches
>    itself elevated** (one UAC prompt) and opens the window. **An .exe is not wanted:** it adds a
>    compile step, SmartScreen warnings on every new PC, and antivirus suspicion of an unsigned
>    program that drives another program's window. **The window holds no measurement logic:** it
>    shows the list, collects choices, launches the engine and streams its output. It shows:
>    - **Requested runs:** the entries from a catalog file Claude writes (below), each with a short
>      "why", a time estimate, a priority and a checkbox. Raymond ticks some and drags to reorder.
>      Steps that must stay in order (for example a stock suite before its edits) are locked together.
>    - **Custom sweep:** workload, min/max MHz, point count, ascending/descending, iterations,
>      profile slot. It is added to the same queue and checked by the same validator.
>    - **Start / Pause after this step / Stop**, and, for steps that need hands, the instruction
>      with a **Continue** button.
>    - 🆕 **Ready to go when Claude has already chosen.** A catalog can mark runs `preselected`, with
>      their order and parameters set. The window then **opens with that queue already built**, so
>      the only click needed is **Start**. Raymond can still untick, reorder or edit anything. Every
>      difference from the catalog's version is **highlighted in the list** and written to the
>      session record, so a changed run can never pass as the requested one.
>    - 🆕 **A live view while it runs**, so Raymond can see what is happening:
>      - the current step's name, **step N of M**, and an overall progress bar;
>      - inside a sweep, **point i of N**, its target and achieved MHz;
>      - the estimated finish time for the step and for the session;
>      - **live readings once a second**: core clock, memory clock, power, temperature and
>        utilisation (from `nvidia-smi`), plus the latest core voltage, read from the tail of the
>        running HWiNFO CSV (shared read, never locking it);
>      - whether HWiNFO is logging, and to which file;
>      - a list of finished steps with their verdict (PASS / FAIL), duration and the witness readings;
>      - the scrolling output of the current step.
>    - ⛔ **The window must be light.** On 2026-09-23 a desktop app drawing 26% SM while rendering
>      tripped a sweep's 10% preflight guard. So: update at most **once a second**, no animations,
>      no redrawn charts, and **no GPU-accelerated controls**. Its own `nvidia-smi` polling must be
>      one query per second, not one per field.
> 2. **The engine, `Run-Plan.ps1`, Windows PowerShell 5.1**, which does all the work and runs
>    headless with `-DryRun` and `-Resume`. Step types, each with a pass/fail verdict:
>    - `gate-power`: power.limit/default/max must equal given values (the SILENT-BIOS check);
>    - `gate-quiet`: `pmon` baseline under a threshold, encoder and decoder at 0;
>    - `gate-hash`: a file's SHA-256 must start with a given prefix (the profile store check);
>    - `apply-profile`: `MSIAfterburner.exe -profileN -q`, then a settle. **A GUI exe does not set
>      `$LASTEXITCODE` reliably, so never judge by it.** The witness that follows decides;
>    - `witness`: run `gemm` for ~30 s (400 iterations, sampling while it runs; the worklist's
>      `Show-Load` notes explain why a 10 s window caught nothing), optionally under a clock lock.
>      Check peak core, memory and, when asked, HWiNFO core voltage from a short log. Discard the
>      start-up samples. Expected ranges come from the catalog;
>    - `hwinfo-start` / `hwinfo-stop`: as above, one log per run, never spanning two profiles;
>    - `suite`: `Collect.ps1` with the catalog's label, settings, workloads, iterations and
>      `-ExpectedMemoryClockMhz`. **Do not bypass or duplicate its guards**;
>    - `sweep`: `Invoke-FrequencySweep.ps1`;
>    - `human`: an instruction plus **Continue**, only for what needs hands (the BIOS switch, building
>      a curve, closing apps, and the HWiNFO fallback).
> 3. **The catalog, `catalog/*.json`**: named runs made of steps, written by Claude and carried on the
>    kit, with a `preselected` flag and a fixed order where Claude has already chosen. Ship
>    **`catalog/sessiond-3070ti.json`**, fully preselected, equal step for step to the worklist's C0–C10, with
>    the same thresholds, labels, iteration counts and the profile hash `1B08C2D0854460FF`. Say where
>    yours differs, and why. **Include `catalog/SCHEMA.md`** so Claude can write new catalogs without
>    reading the code.
> 4. **Fail closed.** The first failed gate or witness **stops the session**. In a `finally`,
>    **always** reset clocks (`nvidia-smi -rgc`) and stop any running HWiNFO log. Then, if the catalog
>    declares a revert profile, apply it and run its witness. Closing the window, Stop, and a crash of
>    the window must all unwind through that path.
> 5. **Resume, and never overwrite:** a state file records each finished step, and reopening the app
>    offers to continue. It refuses to overwrite any result or log.
> 6. **A session record:** one JSON per session, written as it goes. It holds every step's start and
>    end time, verdict and witness readings; the driver, power limits and profile hash; **which runs
>    Raymond selected and every customisation he made**; and whether each HWiNFO log was automatic or
>    by hand. That record is the provenance.
> 7. **A validator, `Test-Plan.ps1`**, used by both the window and the tests. It rejects:
>    - unknown step types and missing fields;
>    - relative paths;
>    - a suite with no `hwinfo-start` before it, and two runs sharing one log;
>    - custom sweeps outside the card's supported clocks;
>    - an iteration count that changes within a sweep.
>
> **Hard constraints:**
> - **No installs on the shop machine:** Windows PowerShell 5.1, .NET Framework 4 and the kit's
>   bundled Python only. **ASCII-only `.ps1` files.** No `??`, no ternary, no `&&`.
> - Every path derives from the kit root, found by the USB **volume label** (`ESD-USB` today, but
>   configurable), never a typed drive letter. Results stay on the USB.
> - Known traps from this repo's history:
>   - function output leaks into return values, so pipe child output to `Out-Host`;
>   - never `return` inside `try` at script scope;
>   - read `$p.Handle` before `$p.ExitCode`;
>   - PS 7's `ConvertFrom-Json` unrolls a top-level array.
> - The engine must also run **without the window** (`Run-Plan.ps1` from an elevated prompt), so a
>   broken GUI never blocks a session.
> - Add every new file to `tools/collection-kit/Sync-Kit.ps1` (rule 12).
>
> **Tests** (`analysis/test_bench_app.py`, under PS 5.1 and PS 7 as CI does, rule 11): run the engine
> in `-DryRun` with **mocked** `nvidia-smi`, Afterburner and HWiNFO, covering at least:
> - a full passing catalog;
> - a **preselected** catalog that runs start to finish with no interaction after Start;
> - an edited preselected run whose change is flagged and recorded in the session JSON;
> - a failed gate that stops the session and still runs the revert;
> - a witness reading **stock clocks after a profile was applied** (the silent driver-reset case);
> - a failed `hwinfo-start` that falls back to the human step and waits for file growth;
> - a resume after an interrupted suite;
> - a refused overwrite;
> - the validator rejecting each malformed plan and each out-of-range custom sweep.
>
> Also: the window must open and show the catalog in `-DryRun`, and every `.ps1` must parse cleanly
> under PowerShell 5.1.
>
> 🛑 **Rule 4 is absolute.** Do not run the engine for real, start HWiNFO, call Afterburner or lock a
> clock. Build and dry-run only. File what you could **not** verify, and do not commit.

---

## Job 16: Headroom Bench window fixes — estimate, status line, readings, and a verified stop

**Why:** the first live run (2026-09-23, local 5060 Ti, PASS) showed four things Raymond wants
fixed. **Fix only these.** Change nothing else unless it affects results or is a bug, and if you find
one, report it rather than widening the job.

> Fix four things in `tools/bench-app/` (mostly `Bench-Window.ps1`; the timer block is around lines
> 270–322). Read `tools/bench-app/README.md` and the Job 15 review in
> `docs/gpt-findings/2026-09-23-headroom-bench-job15.md` first. Four live-run bugs were fixed there,
> so do not reintroduce them: early `$p.Handle` reads, the exact-name voltage column, the resume
> filter, and the resume status.
>
> 1. **The session finish estimate never updates, and it is wrong after a resume.** It is
>    `record.start + runMinutes`, computed once. On a resume `record.start` is the **first**
>    attempt's start, so Raymond's screenshot showed "Session finish: 7:05 PM" beside "Estimated step
>    finish: 7:17 PM". **Compute it every tick as now + remaining work.** Remaining work is the
>    current step's estimate minus its elapsed time (never below zero), plus the estimates of every
>    step not yet finished in the active plan, skipping steps a resume will skip. When the current
>    step overruns its estimate, say so ("step running past its estimate") rather than showing a
>    finish time in the past. **Put the calculation in a small pure function** that can be tested
>    without a window.
> 2. **The status line.** It shows bare "Running" and ends as "Finished: PASS". Make it a caption
>    and a value, **`Status:` followed by the state on its right**: `Ready`, `Running`,
>    `Pause requested`, `Paused`, `Stop requested`, `Stopping and reverting`, `PASS`, `FAIL`.
>    Colour the value only if it costs nothing (plain `ForeColor`: green PASS, red FAIL). On FAIL,
>    show the session's `error` text beneath it.
> 3. **The live readings are one comma list:** `Core / memory / power / temp / util: 2572, 13801,
>    176.86, 62, 99`. Show labelled values with units in fixed positions, e.g.
>    `Core 2572 MHz   Memory 13801 MHz   Power 176.9 W   Temp 62 C   Util 99%   Voltage 0.720 V`.
>    Round power to one decimal. Show voltage only while a log is running. **ASCII only in `.ps1`**:
>    write `C`, or build the degree sign with `[char]0x00B0`, never type it. Still **one `nvidia-smi`
>    query per second**, with no new controls that redraw heavily (rule: the window must stay light).
> 4. **Make sure everything is stopped when a session ends, and show it verified rather than
>    assumed.** Today the window sets `HWiNFO: stopped` as fixed text when the engine exits; nothing
>    checks it. (It was in fact stopped after the live run: Claude checked the button state and file
>    growth by hand.) At the end of every session, PASS, FAIL or Stop, in the engine's `finally`,
>    after the existing cleanup:
>    - check logging with `Invoke-HwinfoLogging.ps1 -Status`. If it is still logging, stop it and
>      check again;
>    - read back that clocks are reset (`Reset-Clocks` already runs; record its read-back);
>    - confirm no process the engine started is still running (the `gpu_workload.py` witness, the
>      `Run-Child.ps1` child and its tree). Kill any survivor and record that you had to.
>    Write all three to a `finalState` object in the session JSON. The window shows
>    `HWiNFO logging: stopped (verified)`, or a red line saying what is still running.
>    **Do not close HWiNFO itself**: stop the logging only.
>
> **Tests** (extend `analysis/test_bench_app.py`; rule 11 applies, so they run under PS 5.1 and PS 7):
> - the estimate function: a fresh run; mid-run; **a resumed session whose `start` is an hour old**
>   (the screenshot's case); an overrunning step; and skipped steps;
> - the readings formatter, including a missing field;
> - the status text for each state;
> - a dry run whose mocked HWiNFO reports "still logging" at the end: the engine stops it and records
>   it in `finalState`.
>
> Keep every existing test passing. Every `.ps1` must parse under 5.1 and stay ASCII.
>
> 🛑 **Rule 4:** build and dry-run only. Do not run the engine for real, start HWiNFO, call
> Afterburner or lock a clock. Claude will re-run the live test on the 5060 Ti. File what you could
> **not** verify, and do not commit.

---

## Job 17: "Local Model Console", a local web page to prompt the local model and watch its runs

**Why:** Raymond wants to see what the local model (Qwen3.8 27B on llama.cpp, `tools/local-model/`)
is thinking and doing, and to prompt it, with Claude able to see the same. llama-server's built-in
page at `http://localhost:8099` already chats and shows reasoning. **What it cannot show:**
- an **agent run**: Claude Code driven by the local model, recorded as a `stream-json` transcript;
- the **queue results** of `run_queue.py`;
- whether a **sweep is running** on the same card.

It also keeps chats in browser storage, where Claude cannot read them.

> Build `tools/local-model/console/`: `server.py` (Python **standard library only**) and one
> `index.html` (inline JS and CSS, **no external requests at all**), plus a README. Read
> `tools/local-model/README.md` first; its hazard section is the reason for several rules below.
>
> **Serve on `127.0.0.1:8098` only.** llama-server is `:8099`; take its URL from `ask_local.BACKENDS`,
> never a new constant. Four parts:
>
> 1. **Status bar**, polled every 2 s:
>    - llama-server health (`/health`);
>    - VRAM used/total and GPU utilisation from one `nvidia-smi --query-gpu` call;
>    - a **red banner** when a measurement is running. Reuse `run_queue.measurement_running()`; do
>      not copy its marker list.
>
>    While that banner shows, and whenever the tab is hidden (`document.visibilityState`), **stop
>    every other poll**.
>
>    ⚠️ This is measured, not theoretical: on 2026-09-24 the Claude desktop app's redraws reached
>    **21% SM** and a sweep's preflight refused to start. The page must be close to silent when
>    nobody is looking.
> 2. **Chat.** A prompt box, an optional system prompt, and temperature. Send to llama-server
>    `/v1/chat/completions` with `stream: true`, rendering `reasoning_content` live in a collapsible
>    "Reasoning" block and `content` below it. At the end, show token counts and tok/s from the final
>    chunk's `timings`.
>
>    **Append every exchange** to `tools/local-model/runs/console/chat-YYYYMMDD.jsonl`:
>    - ISO time, system prompt, prompt;
>    - reasoning, answer;
>    - timings, and any error.
>
>    `runs/` is already gitignored. This file is how Claude reads what was said, so write it even
>    when the request fails.
> 3. **Agent-run viewer.** List `*.jsonl` under two roots: `tools/local-model/runs/` and
>    `C:\Users\Raymond\Documents\local-agent-sandbox` (both configurable in the README). Render the
>    chosen Claude Code `--output-format stream-json --verbose` transcript, **tailing it live** by byte
>    offset:
>    - `system/init`: model, tool count, cwd;
>    - assistant `thinking`, `text` and `tool_use` blocks, showing the tool name and its input;
>    - `tool_result`, truncated with an expand;
>    - `system/api_retry`, counted and not listed one by one;
>    - the final `result`: subtype, `is_error`, turns, duration, and the result text, **errors in red**.
>
>    A malformed line is shown as malformed, never dropped silently.
> 4. **Queue viewer.** List `tools/local-model/runs/*/summary.json` (written by `run_queue.py`) as a
>    table: job, attempt, verdict, seconds. Link to each answer and acceptance report.
> 5. **Claude's requests, live. This is the part Raymond asked for most:** he wants to watch what
>    Claude sends the model, its thinking, and its result, as it happens. Today `ask_local.py` (which
>    `run_queue.py` calls) waits for the whole reply, so nothing is visible until it ends.
>    - Change `ask_local.py` to **stream** from llama-server, and append events to
>      `tools/local-model/runs/console/requests-YYYYMMDD.jsonl`:
>      - `request_start`: time, request id, spec path, context file paths, sampling settings, and the
>        **full user and system messages** as sent;
>      - `reasoning` and `answer` chunks, flushed at least every 0.5 s;
>      - `request_end`: timings, `done_reason`, the output path, and any error.
>
>      `run_queue.py` adds the queue name, job and attempt to `request_start`, and an `accepted`
>      event with the acceptance verdict.
>    - **The file `ask_local.py` writes must be byte-identical to what it writes today** for the same
>      reply. Prove it with a fake streaming server in the tests. Keep all 48 existing
>      `test_ask_local.py` checks passing, including the four failure modes its docstring lists.
>    - The console shows these requests newest first, with **"running" requests expanding live**:
>      the prompt, a Reasoning block filling in, then the answer, and the verdict when it arrives.
>
>    This is how Claude and Raymond see the same thing: Claude reads the JSONL; Raymond watches the
>    page.
> 6. **A double-click launcher**, `tools/local-model/console/OPEN-CONSOLE.bat`. It starts `server.py`
>    and opens the page in its own window (`msedge --app=http://127.0.0.1:8098`, falling back to the
>    default browser), so it looks and feels like an app.
>
> **Server start/stop buttons:**
> - start runs `ask_local.SERVER_COMMAND`, and **refuses while `measurement_running()` is true**;
> - stop only kills a server **this console started** (track its PID);
> - never touch Afterburner, clocks, power limits or HWiNFO.
>
> **Security, because it is a local server:**
> - bind only `127.0.0.1`;
> - serve files read-only from the allow-listed roots above, with **path traversal refused** (resolve,
>   then check the prefix);
> - **no endpoint that runs an arbitrary command or writes outside `runs/console/`.**
>
> **Tests:** `tools/local-model/test_console.py`, stdlib `unittest`. **`run_tests.py` counts
> `[PASS]` lines, so report each passing test the way `analysis/test_bench_app.py` does** (a
> `TextTestResult` that prints `[PASS] <id>`), or the runner flags the suite as asserting nothing.
> Cover:
> - **the real transcript fixture** `tools/local-model/console/fixtures/claude-code-local-L1-apierror.jsonl`,
>   from a failed trial on 2026-09-24. The parser must report **10 `api_retry` events, 0 tool calls,
>   and a final result with `is_error: true`** whose text contains *"System message must be at the
>   beginning"*;
> - a synthetic transcript with thinking, `tool_use`, `tool_result` and a success result;
> - a fake SSE stream with `reasoning_content` and `content` deltas and final `timings`, parsed
>   without a network;
> - path traversal refused;
> - start refused while a (monkeypatched) measurement is running;
> - the chat log line written even when the request fails;
> - `ask_local.py` streaming against a fake server: the events appear in order, reasoning and answer
>   chunks join to the full text, and **the output file is byte-identical to the non-streaming
>   version's**;
> - a request that fails mid-stream still writes `request_end` with the error.
>
> 🛑 **Do not start llama-server or load the model in tests or during development; it runs on the card
> the project measures.** Mock every call to it. Do not run sweeps, do not touch `data/`, do not
> commit. File what you could **not** verify. Claude will run it live, with Raymond, and review it.

---

## Job 18: make the Local Model Console a live conversation view, like ChatGPT or Claude

**Why:** Job 17 works (live-tested 2026-09-24; Claude fixed three defects: Windows path separators,
10,047 progress rows listed one by one, and auto-selecting the newest run). Raymond's verdict: it
reads like **a transcript after the fact**. He wants to watch the model **as it works**:
- the prompt going in;
- its thinking streaming in word by word;
- each tool call appearing as it happens, then its result;
- the answer typing out.

The same goes for prompts Claude sends it. Read Job 17's review first:
`docs/gpt-findings/2026-09-24-local-model-console-job17.md`.

> Rework the **Agent runs** and **Claude requests** tabs of `tools/local-model/console/` (keep the
> Chat tab working, restyled to match):
>
> 1. **One conversation layout for both tabs:**
>    - a **prompt bubble** at the top, collapsed to its first lines if long (specs run to pages);
>    - then each assistant turn as a card with a **Thinking** block that is **open and streaming while
>      it is being written**, then collapses to "Thought for N s" when done, as Claude and ChatGPT do;
>    - **tool calls** as compact cards (`Bash · python -c "..."`, `Read · decode_profiles.py`), with
>      the arguments filling in live and the result attached underneath, collapsed, with an expand;
>    - the answer text streaming;
>    - the final result: turns, duration, and errors in red;
>    - for Claude requests, the acceptance verdict as a badge when it arrives.
> 2. **Stream at token level.** From now on Claude launches agent runs with
>    `--include-partial-messages`, so transcripts carry `stream_event` lines (`content_block_start`,
>    `content_block_delta` with `thinking_delta` / `text_delta` / `input_json_delta`,
>    `content_block_stop`, `message_stop`) **as well as** the whole `assistant` messages. Apply the
>    deltas live. When the whole message arrives, reconcile it with what was streamed, so nothing is
>    shown twice and nothing is lost. **Transcripts without partials** (all the existing ones) must
>    still render, turn by turn.
>
>    Claude requests already stream `reasoning` / `answer` chunks in `requests-*.jsonl`.
> 3. **Assemble on the server, render on the page.** Put the delta-to-turns assembly in Python, as a
>    pure function that is testable, returning normalized incremental events (`turn_start`,
>    `thinking_delta`, `text_delta`, `tool_start`, `tool_input_delta`, `tool_result`, `turn_end`,
>    `result`) with a byte offset. The page only applies them.
> 4. **Rendering must be incremental.** Append to the existing node; never rebuild the list. Today
>    `pollRequests` rebuilds every card on each change.
>    - **Auto-scroll** while at the bottom, and show a "Jump to live" button when the reader has
>      scrolled up.
>    - Poll every **500 ms only while something is running and the tab is visible**; otherwise every
>      5 s, and nothing while hidden or while the measurement banner shows.
>    - Keep the page cheap to draw. It sits on the card the project measures, and a redrawing app
>      window read **21% SM** on 2026-09-24.
> 5. **Keep everything Job 17 got right:** loopback only, confined file reads, no external assets, the
>    measurement banner and its refusals, start/stop of owned servers only, the logs Claude reads,
>    and Claude's three fixes. Each of those has a test in `tools/local-model/test_console.py`, and
>    all must still pass.
>
> **Tests** (`test_console.py`, with `[PASS]` reporting as now):
> - **A real partial-messages fixture**, `tools/local-model/console/fixtures/claude-code-local-partial.jsonl`,
>   recorded by Claude from the local model on 2026-09-24. ✅ **It is in the repo.** It is a small
>   real job (make `mean([])` raise `ValueError`): 5 turns, 60 s, ending in success. It holds
>   **5 thinking blocks (295 `thinking_delta`), 1 text block (35 `text_delta`), 4 tool calls
>   (132 `input_json_delta`)**, 5 `signature_delta`, 10 whole `assistant` messages and 4 tool
>   results. It also carries **295 `system`/`thinking_tokens` lines**, the flood Job 17 had to
>   fold into a counter. Today's parser reads 502 of its lines as `other`. The assembly must yield
>   the same thinking, text and tool calls as the file's whole `assistant` messages.
> - A tool call whose `input_json_delta` arrives in pieces.
> - A transcript cut mid-block (a live tail), then resumed from the returned offset without
>   duplication.
> - The existing non-partial fixture still assembles, turn by turn.
>
> 🛑 Same rules as Job 17: do not start llama-server or load the model; mock it. No sweeps, no
> `data/`, no commit. Claude runs it live with Raymond and reviews it.

---

## Job 19: adversarial audit of Session D (3070 Ti). **Send first: Session D2 runs 2026-09-25.**

✅ **DONE 2026-09-25, reviewed and accepted** (`docs/gpt-findings/2026-09-25-sessiond-3070ti-adversarial-audit.md`). **Do not send.**

**Why:** Session D is the project's second causal test. It came back mixed: the manipulation passed
twice, and the negative control failed. Every outside audit so far has found something real, and
this one should land before the 8d repeat is scored, not after.

> **Audit `data/frequency-sweeps/rtx3070ti-sessiond-20260924/` against
> `docs/REGISTERED-PREDICTIONS.md` §4a, §4b (with both amendments) and §8.** The scorer
> `analysis/score_session_d.py` was committed before the data. **Recompute the verdicts with your
> own code from the sweep CSVs and `_voltage.csv` extracts, not by calling the scorer**, and report
> every place the two disagree. Registered: 4a PASS (1222.5 MHz), 4b FAIL (1432.5 MHz), 8a PASS
> (1170), 8b FAIL (Edit 1's floor reaches 1230 MHz at 0.819 V).
>
> 1. **Is the 4b failure real, or a property of the median?** The control's twelve optima split
>    6/6 between 1380 and 1485. Identical stock suites disagree on 3–4 of 12 per-workload argmaxes.
>    Measure how often a stock suite's median would leave 1485–1500 if its per-workload optima moved
>    by the stock-to-stock noise seen here. Report that, **and do not propose re-scoring 4b**: it is
>    registered.
> 2. **Which workloads moved under the control, and why?** Compare per-workload efficiency curves,
>    not just argmaxes, for `edit2-3` against `stock-1` and `stock-4`. Did efficiency at 1380 rise,
>    or did it fall at 1485? Use temperatures, power and achieved clocks. Edit 2 lowered the 825 mV
>    point by 15 MHz, inside the floor band (Amendment 2 and
>    `data/afterburner-profiles/3070ti-profiles-20260923/`). Does the voltage extract show the
>    control's 1485 MHz point at a different voltage from stock's?
> 3. **Does 8b undermine 4a?** Edit 1's floor ends between 1230 and 1275 MHz, not at the 1200 the
>    as-built reading assumed. 4a's registered bins are 1170/1275. State whether the passing 4a
>    verdict depends on the wrong floor end in any way.
> 4. **The 8d repeat (Session D2):** stock-7 → edit2-8 → stock-9, one day after Session D. What can
>    it settle and what can it not? Is its stock-7 = 1485 eligibility rule sound? **Do not propose
>    changing it**; it is registered in `01623d3`.
> 5. **Anything else wrong** with the import, the joins or the README.
>
> Write `docs/gpt-findings/2026-09-25-sessiond-3070ti-adversarial-audit.md`. No edits to `data/`,
> the paper or the registration.

---

## Job 20: index the §2 sources that are read but unindexed

✅ **DONE 2026-09-25, reviewed and accepted** (`docs/gpt-findings/2026-09-25-section2-source-index.md`). **Do not send.**

**Why:** `docs/drafts/section2-related-work-proposal.md` (Job 13) marks five sentences **[X]**:
CLAUDE.md records the source as read, but `docs/RELATED-WORK.md` does not index it. The proposal
cannot go into the paper until they are indexed or dropped.

> For each source, **open the primary source**, and record the URL, date, author, what it
> establishes, and what it does not. Quote at most one short sentence. Add an entry to
> `docs/RELATED-WORK.md` §4 (the crossbar domain) marked **"GPT-read, pending Claude review"**:
> 1. Hardwareluxx post #184, **2023-01-25**, user EleCtricStream, RTX 4090: the crossbar clock
>    reads ~150 MHz lower under undervolt. The link is in
>    `docs/gpt-findings/2026-09-18-xbar-prior-art.md`.
> 2. `NVIDIA/open-gpu-kernel-modules` issue **#1266**: XBAR capped at 1493 MHz, FurMark 256 → 173
>    FPS.
> 3. overclockers.ru, 2026-08-18: Afterburner undervolting imposes an XBAR ceiling; workarounds.
> 4. The **single-author finding**: confirm with `gh api` that LACT #1147, #1266 and the
>    loong0x00.com article are all by `Loong0x00`, and record the evidence.
> 5. GIGAZINE, 2026-06-08 (`gigazine.net/gsc_news/en/20260608-rtx-5090-external-clock/`). **Try to
>    reach the primary source it reports**, PickleRick on the XtremeSystems forum. It was never
>    reached. If you cannot reach it, say so and leave it marked as a news report.
>
> Then update the **[X]** markers in the Job 13 proposal to what you verified. Remove any sentence
> whose source you could not confirm. Record the search in
> `docs/gpt-findings/2026-09-25-section2-source-index.md`. Do not edit the paper.

---

## Job 21: Wang et al. (TPDS) against their own released data — an open discrepancy

✅ **DONE 2026-09-25, reviewed and accepted, and review went one step further**: on the released parameters their narrow optima sit near the TOP of the window; Figure 4's low optima depend on the notebook's reductions of `p0` and `gamma` (`analysis/wang_tpds_figure4.py`; "static-power division" was wrong, see Job 22). §2.7 corrected. **Do not send.**

**Why:** CLAUDE.md has flagged this since 2026-09-19. §2.7 leans on Wang, Mei, Liu, Leung, Li & Chu
(arXiv:2104.00486) reporting that their optimum sits *"close to the allowed lowest setting"*. But a
raw-grid energy argmax on their released GTX 1080 Ti CSV puts **18 of 30** applications at the
**highest** sampled core clock, **8** at the lowest and **4** in between. Candidate explanations
exist, and **none has been checked**:
- their paper reports **20** benchmarks, and the CSV has **30** applications;
- theirs is a **fitted** optimum, and ours is a grid argmax;
- their energy is **system-scope** against a 37 W idle floor.

> Read §5.1.1, §5.2 and Figure 4 of arXiv:2104.00486 in full.
> 1. Which 20 benchmarks do they report? Map them onto the CSV's 30 applications.
> 2. Is *"close to the allowed lowest setting"* said of the **measured** case, the **simulated**
>    wide-interval case, or both? Quote it with its page.
> 3. **Recompute** the argmax counts for their 20 alone: raw grid, board-scope and, if their paper
>    gives enough to reproduce it, system-scope with the 37 W floor. The CSVs come from
>    `HKBU-HPML/GPU-DVFS-Job-Schedule` (branch **`master`**). ⛔ **Download to a folder outside the
>    repository. Never write under `data/`.**
> 4. **Does the discrepancy survive?** Is the paper's own strategy, citing them against their own
>    artifact, still sound? Propose exact wording for §2.7 and CLAUDE.md, as a proposal.
>
> Write `docs/gpt-findings/2026-09-25-wang-tpds-optimum-discrepancy.md`. No edits to the paper.

---

## Job 22: try to break Claude's reading of Wang et al.'s Figure 4. **Send now.**

✅ **DONE 2026-09-26, reviewed and accepted.** Every number reproduced; it caught three overstatements in Claude's correction (4.352% rounds to 4.4%, `gamma` is not static power, the grid agreement needs rounding and is in-sample) and that no saved fit matches the paper's stated parameter ranges. All applied. **Do not send.**

**Why:** reviewing Job 21, Claude went one step further and put the result into the paper (§2.7,
commit `9187f21`). The claim is that Figure 4's optima *"close to the allowed lowest setting"* come
from the **plotting code**, not from the authors' data. At commit `8a0a2e0`, `solve_dvfs` divides
the fitted `p0` by 4.75 and `gamma` by 4.65 in place. On the pickle's parameters **without** that
division, the narrow model gives **4.352%** (the paper says 4.3%). Only **3 of 20** optima sit at
the lowest setting, and all 20 land within one 100 MHz step of the raw CSV argmin. Widening alone
gives **7.174%**. **This is now a published-facing claim about another group's paper**, and every
outside audit of this project has found something real. Claude's own review is at the end of
`docs/gpt-findings/2026-09-25-wang-tpds-optimum-discrepancy.md`.

> 1. **Re-derive it before reading Claude's script.** From `8a0a2e0`, run the notebook's
>    `solve_dvfs` yourself under four conditions: narrow and wide, each with the parameters as
>    pickled and with the division undone. Then run
>    `python analysis/wang_tpds_figure4.py <your clone>` and report every number that disagrees.
> 2. **Attack the premise that the pickle holds the "original" parameters.** Read the history of
>    `apps.pkl` and every commit that touches it. Read whatever generates it (`model.py`, `gen.py`,
>    `parse.py`, `main.py`) and look for any other scaling of `p0` or `gamma`. Could the pickle be
>    stored already divided, or divided for a different experiment? If the "undivided" condition is
>    not the authors' fitted model, the headline falls. Say which, with file and line.
> 3. **Attack "the division is in the plotting code, not the data".** Quote §5.2's sentence about
>    shrinking static power exactly, with its page. Does it cover the **Narrow** bars, or only
>    **Wide**? Claude's wording says the reduction is described *"for its simulations"*. Is that
>    fair, or does the paper disclose more (or less) than §2.7 now implies?
> 4. **Attack the agreement with the raw grid.** The fitted parameters were fitted to the same 20
>    measurements per application that the CSV holds. So how much of "within one step for all 20"
>    is independent confirmation, and how much is circular? Say it plainly. Would §2.7 survive with
>    that sentence removed?
> 5. **Search** for anyone who has discussed Figure 4's parameters, the 4.75 or 4.65 factors, or a
>    correction to the TPDS paper: errata, later HKBU papers, citing papers, and issues or pull
>    requests on the repository. Log the exact queries.
> 6. Propose exact wording changes to `docs/PAPER_DRAFT.md` §2.7, the correction added 2026-09-25,
>    and to CLAUDE.md's "RESOLVED" paragraph, **as a proposal**. If nothing needs changing, say
>    that and why.
>
> ⛔ Clone and compute **outside the repository**. **Never write under `data/`.** No edits to the
> paper or CLAUDE.md. Do not contact the authors. Write
> `docs/gpt-findings/2026-09-26-wang-figure4-review-audit.md`.

---

## Job 23: adversarial audit of the 3070 Ti write-up, paper §5.5.9. **Send now.**

**Why:** Claude wrote the Session D/D2 results into the paper on 2026-09-26 (commit `4b6b504`).
The result is **mixed**: the registered manipulation passed twice, but the registered control
failed once, and its repeat could not be scored. A mixed result is the easiest kind to overstate,
or to understate to look careful. The same commit changed the abstract's contribution sentence
("on two of them we change the curve and re-locate the optimum"), §5.5.8's registration sentence
and limits, the conclusion's list of refuted predictions, CLAUDE.md's contribution sentence and the
README. Your Job 19 audited the data; this audits what the paper now says about it.

> 1. **Recompute every number in §5.5.9 from the committed data before reading
>    `analysis/claims_consumer.py`'s `5.5.9-*` claims**:
>    `data/frequency-sweeps/rtx3070ti-sessiond-20260924/` and `-sessiond2-20260925/`. You may run
>    `analysis/score_session_d.py`, but also derive the medians and per-workload optima yourself.
>    For D2, which the scorer refuses, recompute its descriptive medians and stock return on its
>    own grid and say whether §5.5.9's "held at 1485 MHz" is right.
> 2. **The direction counts need a baseline, and the section gives none.** §5.5.9 reports Edit 1's
>    workloads moving 6 down / 4 up (`edit1-2` against `stock-1`) and 6 down / 6 up (`edit1-5`
>    against `stock-4`). Compute the same down/up/unchanged counts between **identical stock
>    suites**: `stock-1`→`stock-4`, `stock-4`→`stock-6`, `stock-7`→`stock-9`. How many "up" moves
>    does stock-against-stock produce? Is "the workloads split in direction" a finding, or is it
>    within the noise the section itself cites (3–4 of 12 argmaxes change between stock suites)?
>    Is the 1590 MHz cluster (2, then 5 workloads) outside that noise?
> 3. **Why 1590?** Using the decoded Edit 1 curve (`REGISTERED-PREDICTIONS.md` §4b, Amendment 2,
>    and `data/afterburner-profiles/3070ti-profiles-20260923/`), say where 1590 sits against the
>    forced ramp at 0.831–0.869 V and the point where the curve rejoins stock. Offer a hypothesis
>    only if the data support one, and label it as a hypothesis.
> 4. **Read the new abstract sentence, and the abstract bullets under it, against §5.5.9.** Does
>    "on two of them we change the curve and re-locate the optimum" overstate the 3070 Ti, where
>    the median moved but half the workloads moved the other way? Does "a negative control above the
>    floor moved it too, once" fairly describe one failure plus one unscoreable repeat? Say where
>    the wording is too strong **or too weak**.
> 5. **Check what changed around it.** Check the rewritten sentence in §5.5.8's introduction, its
>    Limits bullet, conclusion item 4, the "does not claim" sentence, CLAUDE.md's contribution
>    section and load-floor list, and the README status bullet. **Grep the whole paper** for any
>    remaining statement that the causal test is one chip, or that tuning is 5060 Ti only.
>    ⚠️ The Future work section is known to be stale; list what is wrong in it, and do not rewrite
>    it.
> 6. Propose exact wording changes **as a proposal**. If a sentence should stay as it is, say so
>    and why.
>
> ⛔ **Never write under `data/`.** No edits to the paper, CLAUDE.md or README. No re-scoring of
> 4b or 8d: the registered verdicts stand whatever you find. Write
> `docs/gpt-findings/2026-09-26-section559-3070ti-writeup-audit.md`.

---

## ⛔ Still do not ask it

- **Anything settled.** `GPT-QUEUE.md` lists these.
- **To write the paper.** It drafts; Claude edits the paper after verification.
- **Anything the hardware settles faster.**
- **A cold novelty check.** This model has read the repository, so its boundary is closed. A
  genuine cold check needs a fresh chat, no repository, and `NOVELTY-CHECK-BRIEF.md`.
