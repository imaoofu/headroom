# `claude-hooks` — harness-level guards for this repository

**Added 2026-09-20.** Until then this project had **no `.claude/` directory and no git hooks**:
every convention in `CLAUDE.md` was enforced by a human reading it, and by CI after the fact.

These two hooks close the gap for the two things a human reader reliably misses.

| hook | event | cost | what it stops |
|---|---|---|---|
| `guard_measurement_files.py` | **PreToolUse** on Edit / Write / MultiEdit / NotebookEdit | ~40 ms | an agent editing a committed measurement |
| `post_edit_gate.py` | **PostToolUse** on the same tools | **0.18 s**, markdown only | an arXiv id entering the repo unregistered |

Wired up in [`.claude/settings.json`](../../.claude/settings.json).

---

## Why a guard on `data/` and not on the source

🔑 **Because the claims auditor would VERIFY the damage.** `analysis/audit_claims.py` stores no
expected number — it renders the expected string *from the CSVs at audit time* and asserts the
paper contains it. So an edited measurement does not fail the audit. It becomes the number the
audit demands the paper carry, and the run reports **284 of 284 claims verified** against altered
data.

`CLAUDE.md` already records that this codebase's defects "do not look like defects." Every one in
that list was caught by a test. This is the one class that no test in the repository can see,
because the tests read the same files.

## Why the test suite is NOT in a hook

The three gates are not interchangeable:

```
python analysis/verify_citations.py --check    0.18 s
python analysis/audit_claims.py                9.0  s
python run_tests.py                            11.4 s
```

⛔ **Only the first is cheap enough to fire on every edit**, and the third would be actively
harmful. On 2026-09-18 the operator's own test-suite and git runs alongside a sweep depressed
measured throughput by **9.38% at every point**, on this same machine — and a point-to-point
residual cannot find it afterwards, because it is blind to a uniform offset. A hook spawning an
11-second suite on every write would reproduce that contamination automatically and silently.

**Set `HEADROOM_SKIP_HOOKS=1` during a bench session.** 0.18 s is still not nothing when the
measurement is the point.

## Default-deny inside `data/`, and the mutation run that forced it

The first version listed the protected extensions — `.csv`, `.json`, `.cfg` — with an "always
editable" list beside it for prose. ⛔ **A mutation run found that second list was dead code.** A
`README.md` never reached it: it had already failed the positive suffix test one line earlier and
was allowed for the wrong reason. Deleting the guard's single most important allowance changed no
behaviour and **the suite still passed**.

✅ The rule is now **default-deny inside a measurement directory, with `.md` the only exception**,
which fixes a second hazard the positive list carried: the stability logger writes
`_logger-stdout.txt` and `_logger-stderr.txt` into `data/stability-runs/`, and those are run
records that a list of extensions would have had to remember.

🔑 **This is `run_tests.py`'s own standard working as advertised** — *"tests that pass against a
broken function are worse than no tests"*. Four deliberate mutations are now caught, including
that one.

## What is deliberately NOT guarded

- **Every `.md`, everywhere.** `CLAUDE.md` requires each data directory to carry a README, and the
  session run sheets (`SESSION-D-RUNSHEET.md`, `SESSION-E-RUNSHEET.md`) live *inside*
  `data/frequency-sweeps/`. A guard that blocked those would be switched off within a day, and a
  switched-off guard protects nothing.
- **Anything outside the five measurement directories.** A scratch CSV is not the contribution.
- **Writes from a script.** The hook fires on the Edit and Write *tools*, not on a sweep writing
  its own output. That is the intent: tools write measurements, agents do not.

## Fail-open, on purpose

Malformed or absent stdin exits 0 with a warning on stderr. This guards against an accident, not
an adversary, and a hook that bricks all editing when it breaks gets removed. ⛔ **Do not harden
it to fail-closed** without first making it impossible to break.

## Tests

```bash
python tools/claude-hooks/test_claude_hooks.py
```

Registered in `run_tests.py`'s `SUITE_DIRS`. Note that the orphan guard in that runner walks
`tools/`, so a suite added here and *not* registered would have been reported rather than silently
skipped — which is how `tools/stability-logger/` was found to be missing on 2026-09-12.
