# Two assistants, one repository

**Written 2026-09-17, when a four-month ChatGPT student trial made a second model available.**

This is not about splitting work in half. The two assistants are useful for **different reasons**,
and the difference is not capability — it is *what each has read*.

---

## The asymmetry that matters

**Claude Code has read `CLAUDE.md`.** That is ~10,000 words of established results, ruled-out
directions, and standards. It makes Claude fast and accurate inside this repository — and it means
Claude **inherits the project's framing, including its blind spots.**

🔑 **Seven novelty retractions say those blind spots are the expensive part.** `CLAUDE.md` is blunt
about why: *"All of that asks 'is this true of our data?' None of it asks 'is this already known?'
... internal rigour feels like diligence, which is exactly what makes it comfortable not to look
outward."*

An assistant briefed on the project cannot supply outside perspective, because it is no longer
outside. **That is the gap GPT fills, and it only works if the framing is withheld.**

---

## Division of labour

| task | who | why |
|---|---|---|
| **Prior-art and novelty checks** | **GPT, cold** | the one job that requires *not* having read this repo |
| Running sweeps analysis, the test suite, the auditor, the manifest | Claude Code | agentic loop, repo already built around it |
| Editing the paper against pinned claims | Claude Code | 284 claims recompute from CSVs at audit time |
| Tooling — PowerShell, Python, the collection kit | either | GPT needs `CLAUDE.md` + `AGENTS.md` first for this |
| **Adversarial review of a finished section** | **GPT** | a second reader who was not there when it was written |
| **Checking a statistical argument** | **GPT** | n=1 chip, pseudoreplication, 12 correlated measurements — an outside reader is harsher and should be |
| Deciding what a sweep means | **Raymond** | neither model runs the hardware or carries the consequences |

### ⛔ What GPT must NOT be handed for novelty work

`CLAUDE.md`, `AGENTS.md`, `PAPER_DRAFT.md`, `RELATED-WORK.md`, either `PRIOR-ART-*.md`, or this
file. Use [`NOVELTY-CHECK-BRIEF.md`](NOVELTY-CHECK-BRIEF.md), which is written to be pasted cold
and is checked by `analysis/test_repo_conventions.py` for leaked project vocabulary.

For **coding** work the rule inverts — give GPT `AGENTS.md` and `CLAUDE.md` in full. The traps in
this codebase (the BOM, cp1252, PowerShell 5.1, heredoc path mangling) are not guessable.

---

## The rule for anything either model produces

> **An AI-supplied fact is a LEAD, not a source, until a person or a script has checked it.**

This is not scepticism about GPT specifically. **The worst citation error in this project's history
was mine** — a four-author list invented for its most important reference, two of the names
belonging to nobody on the paper, written into the file whose entire purpose is accuracy. A second
model does not make that likelier; it makes it *cheaper to produce*, which is the same problem at
higher volume.

### 🆕 They can reach different sources, and that is not a small detail

**Discovered 2026-09-18 while verifying the XBAR search.** The two assistants do not have the same
reach, in both directions:

| | Claude Code | GPT |
|---|---|---|
| Reddit | ⛔ **403 to the JSON API and `old.reddit.com` alike** | ✅ opened several threads |
| Forums (Hardwareluxx, overclockers.ru, HWUpgrade, Guru3D) | 🟡 some work, some do not | ✅ reached German, Russian and Italian material |
| GitHub API — authorship, dates, issue metadata | ✅ `gh` is authenticated here | 🟡 web view only |
| Crossref / arXiv metadata | ✅ scripted and repeatable | 🟡 by hand |
| Local PDFs, the repository, running code | ✅ | ⛔ |

🔑 **So "could not verify" means different things from each of them, and neither list is the truth.**
The XBAR pass produced a concrete example: GPT read a January 2023 Hardwareluxx post *and* a 2022
Reddit post; Claude could open the first and independently confirm it, and **could not open the
second at all**. That Reddit source remains an unconfirmed lead for exactly that reason — not
because anyone doubts it, but because nobody here has seen it.

✅ **Use it deliberately.** Send GPT the sources Claude bounced off; send Claude the things that need
an API, a local file, or a script. **And record which assistant failed to reach what**, because a
gap in one is not a gap in the other.

### What checks what

| output | checked by |
|---|---|
| a citation | `python analysis/verify_citations.py --live` — every arXiv id in the repo must be registered by someone who opened it |
| a number in the paper | `python analysis/audit_claims.py` — recomputes from the CSVs |
| a sweep count | `python analysis/build_data_manifest.py --check` |
| code | `python run_tests.py` |
| *what a paper actually says* | **a person, with the PDF open.** Nothing automates this, and it is where all four citation errors lived |

---

## Working on the same repo without collisions

1. **One assistant at a time holds the working tree.** Claude Code commits directly; if GPT/Codex
   is editing files, let it finish and commit before starting a Claude session, or give it a branch.
2. **Never let either model resolve a conflict by picking a side.** This project has a documented
   case where correcting one half of a comparison "converted a symmetric error into an asymmetric
   one while looking like diligence."
3. **All four gates green before any commit**, whoever wrote the change.
4. **Attribute the source in the commit message** when a change originated with the other model, so
   a later reader knows which outputs have and have not been independently checked.

---

## The first three jobs to give GPT

**1. The cold novelty check.** [`NOVELTY-CHECK-BRIEF.md`](NOVELTY-CHECK-BRIEF.md). This is item 6
on the current to-do list and it has been open since the project started. It is the highest-value
thing a second model can do here, and it costs one paste.

**2. Attack the statistics.** Give it only this, with no other context:

> On one GPU, changing one region of the voltage-frequency curve moved the measured
> energy-efficiency optimum by +465 MHz in 12 of 12 compute kernels. A control edit elsewhere on
> the curve moved it by nothing. What is the strongest argument that this does not demonstrate what
> it appears to? What is n here, honestly?

The expected answer involves pseudoreplication — twelve correlated measurements on one chip under
one edit is not n=12. **If GPT says that unprompted, it has earned its place.** If it does not,
that is information about how much weight to give its other answers.

**3. Resolve the open citation discrepancy.** `verify_citations.py` flags arXiv 2104.00486: this
repository records the first author as Wang, arXiv orders it Mei first. Same six people, different
lead. The short form "Wang et al." appears throughout and §2.7 now rests on this source. **It needs
the published IEEE TPDS version opened** — not either value edited to match the other.

---

## What this does not change

**Neither model decides what is true.** They generate candidates; the CSVs, the claims auditor, the
registered predictions and the hardware decide. `CLAUDE.md`'s honesty rule applies identically to
both, and to anything either of them writes here:

> Do not state anything you have not verified. Do not soften a null. Do not claim novelty you have
> not checked for.
