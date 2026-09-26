"""
Run every gate CI runs, both legs, on this machine, and report one verdict.

WHY THIS EXISTS
    GitHub Actions minutes ran out on 2026-09-26 for about five days, and until then the second
    leg below - the audit with no fetched datasets, which is what CI's "checks" job sees - was run
    by hand, by moving data/raw/ and data/external/ aside. That is five commands per leg and one
    easily forgotten restore. This runs them all.

    It is useful with CI working too: it answers "will CI pass?" before the push, not after.

THE TWO LEGS
    full     the working tree as it is, fetched datasets included. Mirrors CI's "V100 reference
             claims" job (fetch guards, then the full audit) plus the tests, hashes and citation
             gates, plus build_data_manifest.py --check, which CI does not run.
    bare     a COPY of what a checkout would contain - every tracked file plus every untracked
             file .gitignore does not exclude - in a temporary directory. Mirrors CI's "checks"
             job: data/raw/ and data/external/ are absent because they are gitignored, exactly as
             on the runner.

WHY A COPY, AND NOT MOVING THE DATA ASIDE
    Codex shares this working tree. Moving data/raw/ away, even for a minute, changes what any
    other agent running here sees, and a crash between the move and the restore leaves the repo
    silently short of its reference data. A copy touches nothing in place. It is ~21 MB.

    A copy also catches something the move never could: a file the gates need that exists here
    only because .gitignore hides it from git. CI would not have it, and neither does the copy.

    ⚠️ The copy includes UNTRACKED files, so it tests "what CI would see if everything were
    committed", not HEAD. Stage or delete scratch files before trusting it for a commit.

THE LEG GUARDS, AND WHY THEY ARE LOAD-BEARING
    If the copy ever picked up data/raw/, the bare leg would quietly become a second full leg and
    report green while checking nothing it exists to check. So the bare leg first asserts that
    `--filter 5.1-workload-count` matches NO claims, which can only be true if the V100 set is
    really absent - the inverse of the fetch guard CI uses in the reference job. Both guards check
    the printed reason, not just the exit code, so a crash cannot pass as an absence.

WHAT THIS DOES NOT CHECK
    - The Ubuntu leg. Case-sensitive paths and line endings are only exercised on Linux.
    - A FRESH dataset fetch. The full leg audits whatever is in data/raw/ and data/external/ now;
      CI re-downloads them, which is how it notices the upstream repositories moving.
    - Anything needing a GPU, same as CI.

🛑 NEVER RUN THIS DURING A MEASURED SWEEP. It runs the full test suite twice. 11 s of suite load
beside a sweep cost 9.38% throughput on 2026-09-18; this is several times that.

USAGE
    python run_gates.py
    python run_gates.py --leg full
    python run_gates.py --leg bare
    python run_gates.py --keep          # leave the bare copy on disk and print where it is
"""

import argparse
import os
import shutil
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent
PYTHON = sys.executable

NO_MATCH_TEXT = "No claims match --filter"

# (label, argv, expectation, verdict marker). "pass" means exit 0; "absent" means exit non-zero
# AND the auditor's no-match sentence in the output, which is the only way to tell an absent
# dataset from a crash. The marker picks each gate's own verdict line out of its output, so the
# counts are on screen; several gates print notes AFTER their verdict, so the last line is not it.
FULL_LEG = [
    ("V100 fetch landed", ["analysis/audit_claims.py", "--filter", "5.1-workload-count"], "pass",
     "claims verified"),
    ("consumer fetch landed", ["analysis/audit_claims.py", "--filter",
                               "2.7-declared-defaults-are-grid-points"], "pass", "claims verified"),
    ("tests", ["run_tests.py"], "pass", "checks across"),
    ("measurement hashes", ["analysis/check_data_hashes.py", "--check"], "pass",
     "measurement hashes"),
    ("claims audit", ["analysis/audit_claims.py"], "pass", "claims verified"),
    ("citation coverage", ["analysis/verify_citations.py", "--check"], "pass",
     "No coverage problems"),
    ("data manifest (not in CI)", ["analysis/build_data_manifest.py", "--check"], "pass",
     "They agree"),
]

BARE_LEG = [
    ("V100 set really absent", ["analysis/audit_claims.py", "--filter", "5.1-workload-count"],
     "absent", NO_MATCH_TEXT),
    ("consumer sets really absent", ["analysis/audit_claims.py", "--filter",
                                     "2.7-declared-defaults-are-grid-points"], "absent",
     NO_MATCH_TEXT),
    ("tests", ["run_tests.py"], "pass", "checks across"),
    ("measurement hashes", ["analysis/check_data_hashes.py", "--check"], "pass",
     "measurement hashes"),
    ("claims audit", ["analysis/audit_claims.py"], "pass", "claims verified"),
    ("citation coverage", ["analysis/verify_citations.py", "--check"], "pass",
     "No coverage problems"),
]


def checkoutFiles(root):
    """Every path a commit of the working tree would carry: tracked, plus untracked-not-ignored."""
    listing = subprocess.run(["git", "ls-files", "--cached", "--others", "--exclude-standard",
                              "-z"], cwd=root, capture_output=True, check=True).stdout
    paths = [p for p in listing.decode("utf-8").split("\0") if p]
    # A tracked file deleted from the working tree is still listed by --cached. CI would not have
    # it either once the deletion is committed, so skip it rather than fail.
    return [p for p in paths if (root / p).is_file()]


def makeBareCopy(root, destination):
    for relative in checkoutFiles(root):
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, target)
    # check_data_hashes.py asks git which files under data/ are tracked, so the copy must be a
    # repository. actions/checkout makes a depth-1 clone; an index with everything added is the
    # nearest equivalent, and no commit is needed for ls-files --cached.
    subprocess.run(["git", "init", "-q"], cwd=destination, check=True, capture_output=True)
    subprocess.run(["git", "add", "-A"], cwd=destination, check=True, capture_output=True)

    leaked = sorted(str(p.relative_to(destination)) for p in destination.glob("data/raw/*.csv"))
    leaked += sorted(str(p.relative_to(destination)) for p in destination.glob("data/external/*.csv"))
    leaked += sorted(str(p.relative_to(destination)) for p in destination.glob("data/external/*.json"))
    if leaked:
        raise SystemExit("The bare copy contains fetched datasets, so it would not be a CI checkout: "
                         + ", ".join(leaked) + ". Check .gitignore before trusting either leg.")


def removeTree(path):
    # git marks object files read-only, and rmtree cannot delete those on Windows without help.
    def clearReadOnly(function, failedPath, _excinfo):
        os.chmod(failedPath, stat.S_IWRITE)
        function(failedPath)
    shutil.rmtree(path, onerror=clearReadOnly)


def runStep(label, argv, expectation, cwd):
    started = time.monotonic()
    completed = subprocess.run([PYTHON, *argv], cwd=cwd, capture_output=True, text=True,
                               encoding="utf-8", errors="replace",
                               env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    seconds = time.monotonic() - started
    output = completed.stdout + completed.stderr
    if expectation == "pass":
        passed = completed.returncode == 0
    else:
        passed = completed.returncode != 0 and NO_MATCH_TEXT in output
    return {"label": label, "passed": passed, "seconds": seconds, "output": output,
            "exitCode": completed.returncode, "expectation": expectation}


def lastLines(text, count):
    lines = [line for line in text.rstrip().splitlines() if line.strip()]
    return lines[-count:]


def verdictLine(text, marker):
    matching = [line.strip() for line in text.splitlines() if marker in line]
    return matching[-1] if matching else f"(no line containing {marker!r} - read the output)"


def runLeg(name, steps, cwd):
    print(f"\n=== {name} leg, in {cwd} ===")
    results = []
    for label, argv, expectation, marker in steps:
        result = runStep(label, argv, expectation, cwd)
        results.append(result)
        verdict = "PASS" if result["passed"] else "FAIL"
        print(f"  [{verdict}] {label} ({result['seconds']:.1f} s, exit {result['exitCode']})")
        print(f"        {verdictLine(result['output'], marker)}")
        if not result["passed"]:
            for line in lastLines(result["output"], 25):
                print(f"        | {line}")
        if not result["passed"] and expectation == "absent":
            print("        This guard expects the auditor to report that NO claim matches, which "
                  "proves the dataset is absent. It did not, so this leg is not a CI-equivalent "
                  "run and its other results do not mean what they appear to.")
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--leg", choices=["full", "bare", "both"], default="both")
    parser.add_argument("--keep", action="store_true",
                        help="leave the bare copy on disk instead of deleting it")
    args = parser.parse_args()

    allResults = []
    if args.leg in ("full", "both"):
        missing = [d for d in ("data/raw", "data/external")
                   if not any((REPO_ROOT / d).glob("*.csv"))]
        if missing:
            print(f"The full leg needs the fetched datasets and {', '.join(missing)} has none. "
                  "Fetch them with scripts/Get-Dataset.ps1 (no -Only). The full leg is NOT run, "
                  "so CI's reference job has no local equivalent in this result.")
            allResults.append({"label": "full leg: datasets present", "passed": False})
        else:
            allResults += runLeg("full", FULL_LEG, REPO_ROOT)

    if args.leg in ("bare", "both"):
        destination = Path(tempfile.mkdtemp(prefix="headroom-bare-"))
        try:
            makeBareCopy(REPO_ROOT, destination)
            allResults += runLeg("bare", BARE_LEG, destination)
        finally:
            if args.keep:
                print(f"\nThe bare copy was kept at {destination}. Delete it by hand when done.")
            else:
                removeTree(destination)

    failed = [r["label"] for r in allResults if not r["passed"]]
    print()
    if failed:
        print(f"{len(failed)} of {len(allResults)} gates FAILED: {', '.join(failed)}. "
              "Do not push on this result.")
    else:
        legs = "both legs" if args.leg == "both" else f"the {args.leg} leg"
        print(f"All {len(allResults)} gates passed, across {legs}. This covers what CI's Windows legs check, "
              "except a fresh dataset fetch; the Ubuntu leg is not exercised.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
