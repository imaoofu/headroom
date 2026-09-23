# Job 11: committed Afterburner profile decoder

2026-09-22. Added `tools/afterburner/decode_profiles.py` and
`analysis/test_decode_profiles.py`. The decoder reads only a supplied NVIDIA `VEN_*.cfg` or a
snapshot directory. It does not access Afterburner, NVML or GPU state. It parses the 3224-byte
`VFCurve` as an eight-byte header, 127 real `(offset, voltage_mV, base_MHz)` float32 records,
and a checked tail.

## Results checked against committed data

The decoder reproduced **all 127 raw triples and raw sums for every one of the five profiles**
in `data/afterburner-profiles/5060ti-profiles-20260908b-p4-plateau-3030.json`, field for field.
In the 2026-09-22 rung B snapshot, P2–P5 reproduce those same decodes. P1 is the changed rung.
At **845 mV**, P1 stores offset **+176** and base **2362 MHz**, whose raw sum is **2538 MHz**. The
snapshot README records the editor at **2362 MHz, +0** and a byte-identical re-save. Because the
stored offset changes at the adjacent record, the decoder sets `applied_mhz` to null at 845 mV
while retaining the raw fields. It conservatively flags both sides of every offset transition,
including the known **935 mV** sentinel boundary. The historic ≤3090 MHz raw filter remains
available, but it never clears an uncertainty flag.

`--verify-rung B` on the committed snapshot prints §1's five checks as **PASS / PASS / FAIL /
PASS / PASS**. Check 3 has definite envelope failures at **660, 665, 670, 675 and 685 mV**;
nearby 645, 650, 690 and 695 mV are boundary-uncertain. Check 4 is a pass on the *stored raw
850→860 arithmetic* (2180→2775 MHz); both points are flagged, so that pass does not certify the
live applied curve. Check 5 confirms the snapshot cfg and README hash and reports its pre-run
timing as a **README claim**, not a fact inferable from the file bytes. The CLI exits nonzero
because check 3 fails.

## A format correction found while implementing

The format paragraph in `docs/AFTERBURNER-PROFILES.md` said that everything after 127 real
triples was zero padding. I independently checked **20 profile blobs across four committed
snapshots**: in every blob, the first float32 after the 127th triple repeats the last real
offset, and only the rest is zero. The original parser's all-zero-tail gate rejected genuine
files. The guide now preserves the old wording in a dated correction and the decoder validates
the actual tail. The older `data/afterburner-profiles/5060ti-profiles-20260908.json` has a stale
`format_note` with the same assertion; `data/` is read-only, so it remains an archival source
and the correction points to it instead of rewriting it. A repository-wide text search found no
other live prose or claim module carrying the old padding statement.

## Verification and limits

`analysis/test_decode_profiles.py` checks every reference profile, the rung B 845 and 935 mV
boundaries, registered verdicts, the CLI and JSON uncertainty output, a missing snapshot README,
and malformed header, tail and length. The repository's five required gates were run before
writing and again at completion; final counts are in the task response. No measurement file,
paper draft, profile, runner or GPU setting was changed.

This decoder reports stored fields. At transition points its raw sum is **not** a reliable
applied-clock value. Even at stable points, the file cannot establish the driver's runtime
curve or voltage rail; the rung B README specifically records runtime disagreement in the
845–860 mV region. The exact semantics of the repeated trailing offset byte pattern beyond
these committed snapshots remain undocumented.

## Review by Claude, 2026-09-22 — accepted

- **25 of 25 checks pass**, and the suite is picked up by `run_tests.py` (963 checks, 30 suites).
- **`--verify-rung B` reproduced independently:** PASS / PASS / FAIL / PASS / PASS. Check 1 reads
  1702 at 720 mV, and check 3 fails at 660–685 mV, as §1 recorded. Both match what the scratch
  decoder found earlier the same evening.
- **The padding correction was re-derived with separate code**, not taken from this report. In all
  8 distinct blobs, across both the raw cfg files and the JSON snapshots, the first tail slot
  repeats the last real offset and every slot after it is zero. **The correction stands.**
- **Added at review:** `tools/afterburner/README.md`, because every tool directory carries one. It
  warns that the CLI exits nonzero for **any** raised rung, because check 3's 650–690 mV failure
  comes from the registration, so the five printed lines are what to read.
