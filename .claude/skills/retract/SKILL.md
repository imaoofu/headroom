---
name: retract
description: Record a retraction or correction the way this project does it - strike rather than delete, date it, quote what it said before, say how the error got in, then propagate to every file and claim module that carries the old value. Use when a claim, number or sentence in this repository turns out to be wrong.
disable-model-invocation: true
---

# Retract

This repository has retracted seven claims and corrected four citations, and it is better for it —
the record of being wrong is the thing that makes the rest believable. **The protocol is already
followed well by hand. The step that keeps getting missed is the last one.**

## The five steps

### 1. Verify it yourself first

⛔ **Recompute before you retract.** Everything an outside reader returns is a *lead*. Three GPT
audits produced retractions here and every figure was re-derived against the committed data before
a word changed — several matched to three decimals, and one of its proposed replacement sentences
was more cautious than the evidence required.

A retraction written on an unverified claim is just a second error with more ceremony.

### 2. Strike, do not delete

Leave the wrong text on the page inside a ⛔ block:

> ⛔ **THE SENTENCE THAT STOOD HERE IS RETRACTED, 2026-09-19.** It read: *"…"* — and here is what
> the data says instead.

**Why:** the history is the useful part. `CLAUDE.md` keeps two superseded explanations of the
Afterburner pairing artifact *"because a correction drawn from a single example is how the second
error got in, and it read as more rigorous than what it replaced."*

### 3. Date it, and say how the error got in

Not just what was wrong — **what let it through**. The entries that have paid off most are the
mechanism ones:

- *"a rule keyed to a phrase only catches the phrase"*
- *"reproducibility guarantees agreement, not correctness"*
- *"a point-to-point test measures SHAPE and is blind to a uniform offset"*
- *"correcting one half of a pair converts a symmetric error into an asymmetric one while looking
  like diligence"*

### 4. 🛑 PROPAGATE — this is the step that fails

**Run the `stale-reference-auditor` subagent, or grep by hand for the OLD value.**

On 2026-09-19 four corrections were made and three of them left the old value standing somewhere
else, including one stated as fact in the paper's introduction **330 lines above its own
retraction**. A single grep for `101–126` would have found it.

Check, every time:

- `docs/PAPER_DRAFT.md` — including §1 and §2, which are unaudited prose
- `CLAUDE.md`, `ROADMAP.md`, `README.md`, `HANDOFF.md`, `CONTEXT.md`
- the four `analysis/claims_*.py` modules
- every `README.md` under `data/`
- `docs/REGISTERED-PREDICTIONS.md` — it recorded a registration that never happened
- `docs/RELATED-WORK.md` if a citation is involved

### 5. Re-point the claim if the SOURCE was superseded

⛔ **A green audit does not mean the number is current.** `audit_claims.py` renders its expected
string from the file a claim names. If a finer measurement has landed, the claim keeps passing
against the old extract — that is exactly how §5.5.7 kept rendering **1552 MHz** after a 31 MHz
sweep had bounded the floor end at 1560–1590.

**Grep the claim modules for the filename the new measurement replaces.**

## Then the gates

```bash
python run_tests.py
python analysis/audit_claims.py
python analysis/verify_citations.py --check
python analysis/build_data_manifest.py --check
```

✅ **A claim that now fails is the point, not a problem.** Fix the paper, never the formula.

## Commit

`git commit -F <file>` — here-strings break on embedded quotes. Lead with what is now known to be
false, not with what replaced it.
