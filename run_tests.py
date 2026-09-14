"""
Run every test suite in the repository and report one verdict.

WHY THIS EXISTS
    The suites are plain scripts, not pytest, and each is run by invoking it directly. That was
    fine at two suites. At ten it means ten commands to answer "did I break anything", which in
    practice means the question stops being asked - and these suites exist because five separate
    defects in this project were invisible on inspection and only appeared under test.

WHY NOT PYTEST
    The suites deliberately use a hand-rolled `check()` that prints a sentence per assertion, so
    a human reading the output can see what was actually verified rather than a row of dots. That
    output is the point; pytest would hide it behind -v and add a dependency to a repo whose
    tools are meant to run on a shop machine with minimal setup. This runner keeps the suites as
    they are and only aggregates them.

WHAT A PASS DOES AND DOES NOT MEAN
    A green run means every assertion currently written passed. It does NOT mean the code is
    correct - the suites for `loadSweep`, `audit_claims` and `ask_local` were each accepted only
    after deliberate mutations were introduced and caught, because tests that pass against a
    broken function are worse than no tests. New suites should earn their place the same way.

    Note when running mutations by hand: delete __pycache__ between them. Swapping `/` for `*`
    leaves a file the same size, and stale bytecode once ran the mutated version while the
    restored source was on screen.

USAGE
    python run_tests.py
    python run_tests.py --filter sweep
    python run_tests.py --quiet
"""

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent

# Directories that hold suites. Listed rather than globbed from the repo root so that a stray
# test_*.py in a scratch directory or a virtualenv cannot silently join the run.
#
# The allowlist has a failure mode in the other direction: glob() does not recurse, so moving
# suites into a NEW subdirectory drops them from every future run while the output still reads
# "All suites passed". That is what would have happened when the model suites moved into
# analysis/models/. findOrphanSuites() below is the guard - the list stays an allowlist, it just
# refuses to stay quiet about a suite it can see and is not running.
#
# ⛔ THAT GUARD HAD THE SAME BLIND SPOT IT WAS WRITTEN TO CLOSE, until 2026-09-12. It walked only
# the directories ALREADY on this list, so it caught a new SUBdirectory of a listed one and was
# blind to a new SIBLING. tools/stability-logger/test_throttle_reasons.py was added and simply
# never ran, with the output still reading "All suites passed". It now walks SEARCH_ROOTS instead,
# which is deliberately wider than the allowlist - the point of a guard is to see what the list
# does not.
SUITE_DIRS = ["analysis", "analysis/models", "tools/frequency-sweep", "tools/local-model",
              "tools/mutation", "tools/stability-logger"]

# Directories the orphan guard walks looking for suites nobody runs. Broader than SUITE_DIRS on
# purpose - see findOrphanSuites().
SEARCH_ROOTS = ["analysis", "tools", "scripts"]

# Directory names that are never ours.
IGNORED_PARTS = {"__pycache__", ".venv", "venv", "node_modules", ".git"}


def findSuites(nameFilter):
    suites = []
    for relative in SUITE_DIRS:
        directory = REPO_ROOT / relative
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("test_*.py")):
            if nameFilter and nameFilter not in path.name:
                continue
            suites.append(path)
    return suites


def findOrphanSuites():
    """test_*.py files under a listed directory that no listed directory actually runs.

    Walks each SUITE_DIRS entry recursively and subtracts what findSuites() would pick up. A hit
    means someone added a subdirectory of suites and did not add it here, which is invisible in a
    green run - the count just gets smaller.
    """
    collected = {path.resolve() for path in findSuites("")}
    orphans = []
    for relative in SEARCH_ROOTS:
        directory = REPO_ROOT / relative
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("test_*.py")):
            if IGNORED_PARTS & set(path.parts):
                continue
            if path.resolve() not in collected:
                orphans.append(path)
    return sorted(set(orphans))


def runSuite(path):
    # cwd is the repo root because several suites resolve data paths relative to it, and the
    # claims auditor imports its claims module by name.
    completed = subprocess.run([sys.executable, str(path)],
                               capture_output=True, text=True, cwd=str(REPO_ROOT))
    output = completed.stdout + completed.stderr
    return {
        "path": path,
        "ok": completed.returncode == 0,
        "passed": output.count("[PASS]"),
        "failed": output.count("[FAIL]"),
        # A suite that cannot run on this platform says so, on its own line, and asserts nothing.
        # That is NOT the silent-zero-assertion failure the guard below exists to catch - see the
        # comment there for why the two must be told apart.
        "skipped": any(line.lstrip().startswith("[SKIP]") for line in output.splitlines()),
        "output": output,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--filter", default="",
                        help="Only run suites whose filename contains this substring.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-suite output for suites that pass.")
    args = parser.parse_args()

    # Checked before anything runs, so an unlisted directory is reported even if every suite
    # that DID run passes.
    orphans = findOrphanSuites()
    if orphans:
        print("Suites found but NOT run - their directory is not in SUITE_DIRS:")
        for path in orphans:
            print(f"  {path.relative_to(REPO_ROOT).as_posix()}")
        print("Add the directory to SUITE_DIRS in run_tests.py, or delete the file.\n")

    suites = findSuites(args.filter)
    if not suites:
        where = " and ".join(SUITE_DIRS)
        print(f"No suites matching {args.filter!r} under {where}.")
        return 1

    results = [runSuite(path) for path in suites]

    print(f"Ran {len(results)} suite(s) under {' and '.join(SUITE_DIRS)}.\n")
    for result in results:
        relative = result["path"].relative_to(REPO_ROOT).as_posix()
        status = "ok  " if result["ok"] else "FAIL"
        print(f"  {status}  {relative:<44} {result['passed']:>3} passed"
              + (f", {result['failed']} failed" if result["failed"] else ""))

    broken = [r for r in results if not r["ok"]]
    if broken and not args.quiet:
        for result in broken:
            relative = result["path"].relative_to(REPO_ROOT).as_posix()
            print(f"\n--- output from {relative} ---")
            print(result["output"].rstrip())

    total = sum(r["passed"] for r in results)
    print(f"\n{total} checks across {len(results)} suite(s).")

    # A suite that reports zero assertions is treated as a failure. It almost always means the
    # file errored before reaching its checks, or was gutted - both of which exit 0 in a plain
    # script and would otherwise be reported as a pass.
    #
    # ⚠️ EXCEPT when the suite DECLARED a skip. The two PowerShell suites need a shell that does
    # not exist on macOS, so they print "[SKIP] ..." and assert nothing - which this guard called
    # SILENT and failed the whole run. CI never caught it because GitHub's ubuntu runners ship
    # pwsh and the suites really do execute there; it only fires on a developer's Mac, where it
    # trains exactly the habit the guard was written to prevent - ignoring red.
    #
    # A declared skip is reported on its own line and does NOT fail the run. It is still printed
    # every time, because the failure mode being guarded against is a zero-assertion suite going
    # UNNOTICED, and a loud skip is not that.
    skipped = [r for r in results if r["ok"] and r["passed"] == 0 and r["skipped"]]
    for result in skipped:
        relative = result["path"].relative_to(REPO_ROOT).as_posix()
        print(f"  SKIPPED: {relative} declared a skip and asserted nothing on this platform. "
              f"It is NOT covered by this run.")

    silent = [r for r in results if r["ok"] and r["passed"] == 0 and not r["skipped"]]
    if silent:
        for result in silent:
            relative = result["path"].relative_to(REPO_ROOT).as_posix()
            print(f"  SILENT: {relative} exited cleanly but asserted nothing.")

    if broken or silent or orphans:
        print(
            f"FAILED: {len(broken)} suite(s) failing, {len(silent)} asserting nothing, "
            f"{len(orphans)} not run at all."
        )
        return 1
    print("All suites passed. This means every assertion written passed, not that the code is "
          "correct - see the note on mutation testing at the top of this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
