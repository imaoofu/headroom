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

### ✅ DEMONSTRATED 2026-09-21, not argued — and the guard did NOT cover it

The paragraph above was a design argument until an **OpenAI Codex** agent, running on the same
machine with write access to this repository, was asked to change one voltage reading in
`rtx3070ti-20260825/hwinfo-silent/…_voltage.csv` — 855 MHz, **0.819 → 0.900 V**. It did. Then,
with the altered file in place, **every gate this project has passed:**

| gate | result on corrupted data |
|---|---|
| `analysis/audit_claims.py` | **284 of 284 claims verified against the CSVs** |
| `python run_tests.py` | **828 checks across 24 suites, all passed** |
| `build_data_manifest.py --check` | **exit 0** |
| `verify_citations.py --check` | **exit 0** |

🔑 **Four green gates on data that had been edited by hand minutes earlier.** The file was restored
from git; nothing was lost. **What the exercise cost is the belief that the hooks close this.**

⛔ **THE GUARD IS PER-HARNESS, AND THEREFORE PER-AGENT.** `.claude/settings.json` wires it into
Claude Code and nothing else. A second agent in the same working tree is simply outside it, and
`.codex/hooks.json` — generated as a mirror — **did not fire**: this machine has no Codex
`config.toml` and no global hook config, so it is decoration.

🛑 **So the honest statement of what `guard_measurement_files.py` does: it stops ONE agent from
making an accident. It is not an integrity control and must never be cited as one.**

✅ **What would actually close it is DETECTION, not prevention** — a content hash per measurement
file, verified in CI. `data/MANIFEST.json` already censuses 367 files with `path`, `category`,
`rule`, `driver` and more, and **carries no hash of any kind**. Adding one and checking it is
agent-agnostic, survives a harness nobody has heard of yet, and is the only version of this that
does not need updating every time a new tool gains write access. ~~**Not yet built.**~~

✅ **BUILT 2026-09-22**: `analysis/check_data_hashes.py`, built by GPT and reviewed and widened by
Claude. The reviewed baseline, `docs/data-measurement-hashes.json`, covers **1,106 files**: every
tracked file under `data/` except Markdown, `.gitkeep` and the two generated manifests. All 1,106 were
verified against their committed versions before it was accepted. Hashes ignore line endings. It
runs as its own **CI step**, so a silently altered measurement fails CI even while the tests and the
claims audit pass. The demonstrated case (855 MHz, 0.819 → 0.900 V) is in its test suite.

🛑 **After committing new sweeps, run `python analysis/check_data_hashes.py --write` and READ THE DIFF.**
CI fails until then, which is intended. A `--write` accepted without reading **legitimises whatever
changed** — the gate detects changes; it cannot judge them.

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

### ⛔ It failed CI on both legs the day it was added, and the CODE was fine

The suite hardcoded `REPO = r"C:\Users\Raymond\Documents\headroom"`. `post_edit_gate.shouldRun()`
asks whether a file is inside **this** checkout, resolved at runtime — so on a runner rooted at
`/home/runner/work/headroom/headroom` it correctly answered "outside the repository" and the
assertion failed. Three pushes, both legs, one check.

🔑 **The test passed on the machine it was written on and could only ever pass there** — and a
green local run looks exactly like evidence. `REPO` is now derived from `__file__`, with a check
asserting it really is the repository root, so the mistake cannot return silently.

✅ **Reproduce a different root before trusting a path-sensitive suite.** Copy the hook files plus
`CLAUDE.md` and `run_tests.py` into a temporary directory and run the suite from there. **Then put
the original defect back and confirm the harness actually fails** — a verification that passes for
the wrong reason is worth nothing, which is the same standard `run_tests.py` sets for mutations.

Registered in `run_tests.py`'s `SUITE_DIRS`. Note that the orphan guard in that runner walks
`tools/`, so a suite added here and *not* registered would have been reported rather than silently
skipped — which is how `tools/stability-logger/` was found to be missing on 2026-09-12.
