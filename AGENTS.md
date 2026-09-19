# AGENTS.md — entry point for any AI assistant working in this repository

🛑 **`CLAUDE.md` IS THE AUTHORITY. READ IT FIRST AND IN FULL.** It carries what has already been
established, what has already been ruled out, and the standards this project is held to. This file
is a router and a division of labour — it deliberately restates almost nothing.

⛔ **THIS FILE WAS A VERBATIM COPY OF `CLAUDE.md` UNTIL 2026-09-17, AND THAT WAS A BUG.** Ten
thousand words duplicated, four lines apart — just the filename swapped. `CLAUDE.md` warns against
exactly this in its own text (*"if you find a second copy, delete it rather than update it"*), and
it has already carried two contradictory values for one quantity simultaneously. **Two copies of
the authority file WILL drift, and nothing would have flagged which one was stale.** Pinned now by
a check in `analysis/test_repo_conventions.py`.

Owner: Raymond ([imaoofu](https://github.com/imaoofu)). Solo undergraduate research project for the
Inspirit AI mentorship, targeting a published paper.

---

## The one rule that outranks everything

> **Do not state anything you have not verified. Do not soften a null. Do not claim novelty you
> have not checked for.**

**A null result is a result and gets reported as one. Say the sample size out loud every time.
N=1 chip is N=1 chip.**

This is not a style preference. The project has retracted **seven** novelty claims and **four**
citations. Every retraction came from asserting something plausible instead of checking it.

---

## Who does what

Two assistants now work on this repository: **Claude** (via Claude Code) and **GPT** (via ChatGPT /
Codex). They are not interchangeable, and the reason is not capability.

| | Claude Code | GPT |
|---|---|---|
| **Best used for** | agentic work inside the repo — running sweeps analysis, the 737-check suite, the claims auditor, editing the paper, committing | **independent judgement from outside this project's framing** |
| **Has read `CLAUDE.md`** | always | **deliberately NOT, for novelty work** |
| **Writes to the repo** | yes | via Raymond, or its own branch — see the protocol |

### 🔑 GPT's highest-value job is the one Claude structurally cannot do

**Seven novelty claims were asserted and self-retracted. Every one was caught in-house, after
writing.** `CLAUDE.md` diagnoses why: *"All of that asks 'is this true of our data?' None of it
asks 'is this already known?'... internal rigour feels like diligence."*

An assistant that has read `CLAUDE.md` inherits the project's framing, including its blind spots.
**A model that has not read it is the cheapest available outside reader** — and outside reading is
the single axis on which this project keeps failing.

⛔ **So for novelty and prior-art work, do NOT give GPT this repository's framing.** Use
[`docs/agents/NOVELTY-CHECK-BRIEF.md`](docs/agents/NOVELTY-CHECK-BRIEF.md), which is written to be
pasted cold. Handing it `CLAUDE.md` first destroys the only property that makes it useful here.

For ordinary coding help, the opposite applies — give it everything, starting with `CLAUDE.md`.

---

## Before you write anything into this repository

1. **`python run_tests.py`** — every suite, one verdict.
2. **`python analysis/audit_claims.py`** — the paper's numbers against the CSVs.
3. **`python analysis/build_data_manifest.py --check`** — the sweep census against the abstract.
4. **`python analysis/verify_citations.py --check`** — every cited arXiv id is registered, by
   someone who opened it. `--live` also compares against arXiv's own metadata.

🛑 **Read counts off those tools, never off any markdown file.** Every root document in this repo
has carried a stale count at some point and `CLAUDE.md` once carried two contradictory ones at once.

---

## The traps that have already cost this project time

Listed because they are invisible on inspection and each one produced plausible, wrong data.

- **A claim's job is to state what the data says, not to make the audit green.** If a correctly
  written claim does not match the paper, that is a *finding*. Fix the paper, never the formula.
  The same goes for a failing test.
- **Never invent a citation, an author list, or a section number.** Run `verify_citations.py`.
  This project's most important source was cited with two co-authors who do not exist — written by
  an AI assistant, from memory, in a file whose whole purpose is accuracy.
- **PowerShell writes JSON with a UTF-8 BOM.** Read it `utf-8-sig` or it crashes.
- **The Windows console is cp1252 and cannot encode emoji.** Tool output must be ASCII-only. Two
  scripts have crashed printing their own warning markers.
- **PowerShell 5.1**: no ternary, no `??`, no `&&`. Use `git commit -F <file>` for multi-line
  messages — here-strings break on embedded quotes.
- **Python heredocs mangle Windows paths.** `\t` and `\f` in `tools\frequency-sweep` become TAB and
  FORMFEED. This has already corrupted a run sheet.

---

## GPT findings/results from prompts

Raymond requested a persistent archive for GPT results. After completing substantive
Headroom prompt work, save its findings, sources, verification status, and unresolved
limits in [`docs/gpt-findings/`](docs/gpt-findings/README.md) and update that index.
Link existing canonical records rather than duplicate them. For cold novelty work,
finish the independent search before reading the archive or project framing; archive
the result afterward and record when that boundary ended.

## Where things live

| file | answers |
|---|---|
| **`CLAUDE.md`** | **what is established, and the standards. The authority.** |
| `ROADMAP.md` | the ordered plan — what is open, what is closed and why |
| `README.md` | outward-facing results summary |
| `CONTEXT.md` | why this project exists |
| `HANDOFF.md` | how to get running on another machine |
| `docs/RELATED-WORK.md` | every source, with **whether the primary source was actually opened** |
| `docs/agents/` | 🆕 briefs and protocol for working alongside another assistant |
| `docs/TODO-20260915.md` | current priorities |

---

## Safety — this matters more than data

- **The sweep must always reset clocks**, through `try/finally`, unwinding on Ctrl+C too.
- **`Log-GpuStability.ps1` observes only.** It never applies settings.
- **`gpu_workload.py` never touches clocks, voltage, or power limits.**
- **Cards live in PCs built to sell.** Raymond owns them on the bench and no third party's data is
  on them, so tuning them is in scope — but every card is **reverted and verified three ways**
  before it ships. A driver reset silently clears Afterburner offsets, so a card can report a tuned
  settings string while running stock silicon.
