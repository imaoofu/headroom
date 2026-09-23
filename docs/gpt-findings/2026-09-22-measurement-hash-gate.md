# Measurement-file hash gate, 2026-09-22

This completes Job 2 in [GPT-PROMPT-NEXT.md](../agents/GPT-PROMPT-NEXT.md). The existing claims audit, tests and manifest checks all passed after a voltage reading was altered. This work adds a separate integrity check for that failure mode. It does not change a measurement or a claim formula.

## Design

[`analysis/check_data_hashes.py`](../../analysis/check_data_hashes.py) implements `--write` and `--check`. The proposed baseline is `docs/data-measurement-hashes.json`, outside `data/`, because the Claude edit guard denies writes inside `data/` by default. Keeping the baseline separate also keeps `data/MANIFEST.json` focused on its existing sweep census.

The gate covers Git-tracked and newly added, nonignored CSV/JSON files anywhere under `data/`. It excludes `data/MANIFEST.csv` and `data/MANIFEST.json`, which are generated census metadata, and excludes Markdown. Gitignored raw HWiNFO dumps, fetched third-party datasets and declared smoke-test output are outside this portable baseline. A new nonignored sweep CSV or JSON **fails** until its hash is reviewed and added; a deleted tracked file fails too. A file changed after its hash was recorded fails. The current tree has **1,030 candidates and no missing files**, computed by the script's read-only collection function on 2026-09-22.

Each SHA-256 input is the file's bytes after replacing CRLF and lone CR line endings with LF. Other bytes, including a UTF-8 BOM if present in a measurement file, are retained. This convention is written in the JSON baseline itself. It makes a Windows CRLF checkout and a Linux LF checkout hash identically without parsing or reformatting CSV/JSON. The checker accepts a PowerShell-style UTF-8 BOM on the baseline JSON, though its own writer emits no BOM.

I wired `python analysis/check_data_hashes.py --check` into the `checks` job of [CI](../../.github/workflows/ci.yml) as a separate step after the test suite. CI cannot silently regenerate its own reference hashes. The distinct step makes an integrity failure visible even when tests and the claims audit pass. The gate uses Git's index plus nonignored new files to include deletions and additions; a jointly altered measurement and hash-list commit still requires human review. This is detection against a reviewed baseline, not prevention against someone who can rewrite that baseline.

## Demonstration

[`analysis/test_check_data_hashes.py`](../../analysis/test_check_data_hashes.py) copies the committed `rtx3070ti-20260825/hwinfo-silent/20260827-170331_rtx3070ti-silent-gemm-matched2130-hwinfo_sweep_voltage.csv` into a temporary Git repository. It writes a baseline **there**, verifies that the copy passes, changes only the 855 MHz row from **0.819 to 0.900 V**, and verifies that the check fails with `[changed]` and the file path. It also checks LF/CRLF/lone-CR equivalence, a missing baseline, deletion, an unhashed new CSV, out-of-scope Markdown/metadata/ignored data, a BOM on the hash list, and unsupported manifest metadata. All **14 checks pass**. The real source file is read only.

The full `python run_tests.py --quiet` run passed **849 checks in 25 suites** after the new suite was added.

## Activation handoff

I **did not run `--write` against the real `data/` tree**, as Job 2 requires. The first real baseline write is for review. Until `docs/data-measurement-hashes.json` is generated, inspected and committed, the new CI step intentionally fails closed. Running `python analysis/check_data_hashes.py --check` now exits 1 with “hash list missing.” After reviewing the implementation and current measurements, the reviewer can run `python analysis/check_data_hashes.py --write`, inspect the entire new JSON file and its diff, then run `--check`. Later `--write` runs also require diff review: they can legitimize an accidental measurement change if accepted blindly.

No measurement file, paper text, claims formula, GPU setting, or existing Job 1 record was changed. The initial baseline's hashes, cross-platform CI result after it is added, and any future data changes remain unverified in this record.

## Review by Claude, 2026-09-22 — accepted, with the scope widened

**Checked:** the code was read in full. The 14 tests pass. The 1,030 candidate count reproduces
(562 CSV + 470 JSON − 2 manifests). Before the baseline was written, `data/` was confirmed identical
to git: nothing modified, nothing untracked. `run_tests.py` leaves no file behind in `data/`, so CI's
test step cannot trip the gate.

**Changed: the scope.** CSV/JSON only left **76 tracked provenance files unguarded**:
- 10 `.cfg`: the Afterburner profile snapshot, the only backup of the tuned curves
- 30 `.log`: collection-kit and stability-run logs
- 36 `.txt`

That gap came from the job brief, which said "CSV, JSON", not from this implementation. Scope is now
every tracked file under `data/` except Markdown, `.gitkeep` and the two manifests. Three tests were
added. The new `.cfg` test was confirmed to **fail under the original scope**, so it is not vacuous.

**Baseline written and accepted:** 1,106 files. ✅ **All 1,106 hashes were checked against the
COMMITTED blobs** via `git cat-file`, not only against the working tree. So the baseline records
exactly what git already had, and nothing unreviewed entered it. The 855 MHz row reads 0.819 V.
