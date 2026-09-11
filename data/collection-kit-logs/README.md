# `collection-kit-logs` — console logs from `RUN-ME.bat` sessions on other machines

<!-- dataset-grade: no -->

Not measurements. These are the **console transcripts** `Collect.ps1` writes on the collection
kit's USB drive, one per invocation, covering runs on the 5060 Ti, the 3070 Ti and the RTX 3060
between 2026-08-23 and 2026-09-10.

## Why they are here

🔑 **They existed nowhere else.** On 2026-09-10, before the USB kit was reused for a new build, a
hash comparison against the repository found **28 files present only on the drive** — these logs
among them. The sweeps they describe were already committed; the record of *how those sessions
went* was not.

That is the failure mode the kit has always carried: `tools/collection-kit/Sync-Kit.ps1` pushes
tooling **onto** the drive and nothing pulls results **off** it. Ingestion was manual, and manual
ingestion took the files someone thought to look for.

**Before wiping a collection kit, hash every file on it against the repository.** Do not assume the
sweeps were the only thing worth keeping.

⛔ **AND THAT RESCUE ITSELF MISSED TWO FILES — found 2026-09-11, one day later.**
`run-20260910-185301.log` and `run-20260910-191417.log`, the two RTX 3060 session transcripts, were
still present only on the drive when it was checked again while preparing the kit for an RTX 2060
Super run. They were missed for an ordinary reason: **the 3060 session ran after the sweep that
rescued everything else**, so a rescue that was complete when it was performed was already
incomplete by the end of the same day.

🔑 **The lesson is not "check harder", it is that a one-off audit expires.** The hash comparison has
to run immediately before the drive is reused, every time, and never be trusted from a previous
session. A second check found 126 files on the drive, of which 121 were committed, 3 matched
gitignored HWiNFO logs, and 2 existed nowhere else.

## What is in them

Preflight output, per-frequency sweep lines, refusals and their reasons, and the reset path's
read-back. A refused run leaves a log and no sweep, so **these are the only record of the runs that
did not happen** — which is exactly what a reader checking for selection effects needs.

⚠️ **They are transcripts, not data.** Nothing here is pinned by `analysis/audit_claims.py`, and
numbers quoted in a log are the tool's own rounded console output rather than the CSV's values.
Read the CSV for any figure that matters.
