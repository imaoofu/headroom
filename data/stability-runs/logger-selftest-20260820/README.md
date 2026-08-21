# Does the stability logger notice a failure? — 2026-08-20

`ROADMAP.md` lists this as `[CORE]` and it had sat undone since the beginning. The logger had
only ever run on sessions that went fine, which means **a logger that unconditionally reported
CLEAN would have looked identical to a working one up to this point.**

Run with `tools/stability-logger/Test-LoggerCatchesFailure.ps1`. Three 45-second cases:

| case | expected | got |
|---|---|---|
| load throughout (positive control) | CLEAN | **CLEAN**, 95% of samples loaded |
| load never starts (idle GPU) | not CLEAN | **INCONCLUSIVE**, 0% loaded |
| load dies partway | not CLEAN | **INCONCLUSIVE**, 28% loaded |

The positive control is the reason this is a test rather than a formality. Without it, a logger
stuck on INCONCLUSIVE would have "passed" both failure cases.

**The logger discriminates.** The load-fraction detector is accurate to the sample: 95% / 0% /
28% against a 50% threshold.

## What the first run found

Two file sets are kept here on purpose. The `1842xx` timestamps are the FIRST run, which is the
one that found things.

**The idle case came back UNSTABLE, not INCONCLUSIVE**, flagging a display-driver crash event.
No crash had occurred. The event was `nvlddmkm` Error 153 at 18:43:40 — the exact second that
case opened its window. Cause: the harness called `Stop-Process -Force` on the previous case's
workload one second earlier, and force-killing a process with live CUDA kernels makes the driver
reset the GPU context, which logs a genuine driver error.

So the logger's crash detection is **correct, and that was the first time it had ever fired.**
The fault was in the test, not the tool. Two harness fixes: the idle case now runs first, since
it is the only one whose verdict a stray driver event can flip, and every case gets a 12-second
settle so teardown events land outside the next window.

The matcher was also checked for over-breadth, since `ProviderName -like "*nvlddmkm*"` would
match informational events too. Over 14 days this machine logged 3 such events, all Error 153.
No false-positive spam, so the filter was left alone rather than tightened on speculation.

## Two real defects in the logger, both fixed

**The crash flag was unfalsifiable.** It reported `1 display-driver crash/reset event(s)` and
nothing more — no event id, no level, no timestamp. Determining that the first run's flag was a
self-inflicted false alarm required going to the Windows event log by hand. Provider, id, level
and time are now in both the flag text and a structured `crash_events` field. Event 153 is a
context reset rather than the hard crash the bare wording implies, and that distinction now
survives into the log.

**`session.json` carried a UTF-8 BOM.** `Out-File -Encoding utf8` writes one on Windows
PowerShell 5.1, and a BOM in front of `{` fails every standard JSON parser — Python's
`json.load` raises `Expecting value: line 1 column 1`. This was hit while trying to read the
file during this very investigation. A machine-readable artifact that no downstream tool could
parse. Now written BOM-less via `[IO.File]::WriteAllText`.

## What this does NOT establish

- **No real crash was induced.** All three cases test the load-fraction and event-log detectors.
  Whether the logger survives an actual hard lock is still untested, and by its own admission it
  can only infer that from a truncated log.
- **45-second windows.** Real stability testing runs for hours. This tests the detectors, not
  the card.
- The UNSTABLE verdict path was exercised only by accident, and only for a context reset. A
  4101 TDR has still never been seen by this tool.
