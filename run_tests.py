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
SUITE_DIRS = ["analysis", "tools/local-model"]


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
        "output": output,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--filter", default="",
                        help="Only run suites whose filename contains this substring.")
    parser.add_argument("--quiet", action="store_true",
                        help="Suppress per-suite output for suites that pass.")
    args = parser.parse_args()

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
    silent = [r for r in results if r["ok"] and r["passed"] == 0]
    if silent:
        for result in silent:
            relative = result["path"].relative_to(REPO_ROOT).as_posix()
            print(f"  SILENT: {relative} exited cleanly but asserted nothing.")

    if broken or silent:
        print(f"FAILED: {len(broken)} suite(s) failing, {len(silent)} asserting nothing.")
        return 1
    print("All suites passed. This means every assertion written passed, not that the code is "
          "correct - see the note on mutation testing at the top of this file.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
