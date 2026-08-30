"""
Apply proposed mutants one at a time and record whether the test suites catch them.

WHAT THIS MEASURES, AND WHAT IT DOES NOT
    run_tests.py says every assertion written passed. It cannot say whether the assertions are
    worth writing - a suite that imports a module and checks nothing exits green forever. The
    only way to find that out is to break the source deliberately and see whether the suite
    notices. That is what this does, at scale, instead of the three hand-made mutations that
    gated test_gpu_workload.py.

    A SURVIVOR IS NOT AUTOMATICALLY A BUG IN THE TESTS. It is one of two things and the
    difference needs a human:

      - a real gap: the mutant changes behaviour and nothing asserts on that behaviour;
      - an equivalent mutant: the mutant changes the source text but not what it computes,
        so no possible test could catch it and the survivor is correct.

    Nothing here tries to tell those apart. Survivors are reported with their rationale and
    their diff so they can be read.

WHY THE MUTANT FORMAT IS AN EXACT LINE MATCH
    A unified diff needs correct context lines, and a model that miscounts one silently patches
    the wrong place. Instead a mutant names a line NUMBER and the exact ORIGINAL TEXT of that
    line, and is refused unless the two agree. That makes a misremembered line a rejected mutant
    rather than a corrupted source file, which is the same reason audit_claims.py pins rendered
    strings instead of storing expected values.

SAFETY, WHICH MATTERS BECAUSE THIS EDITS TRACKED SOURCE
    - Refuses to start unless `git status --porcelain` is empty. If this process is killed
      mid-mutant, `git checkout .` is then a complete recovery and nothing of yours is lost.
    - Restores the file in a `finally`, and again on KeyboardInterrupt.
    - Verifies the tree is clean again at the end and says so loudly if it is not.
    - Runs a baseline first and aborts if it is not green: against a red baseline every mutant
      reads as killed and the score is meaningless.

    __pycache__ IS PURGED AROUND EVERY MUTANT. run_tests.py's own docstring records why: a
    mutant that swaps `/` for `*` leaves the file the same size, so the .pyc is not invalidated
    and the previous version runs while the mutated source is on screen.

USAGE
    python tools/mutation/run_mutants.py mutants.json
    python tools/mutation/run_mutants.py mutants.json --out results.json --timeout 180
    python tools/mutation/run_mutants.py mutants.json --filter analyze_sweep
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

# Source files this harness is allowed to mutate, each with the suite whose job it is to catch a
# mutation there. The mapping is not used to decide WHICH suites run - every mutant runs the
# whole battery, because a mutation caught only by a different module's suite is still caught,
# and knowing that is more interesting than a per-file score. It is here as an allowlist and as
# a statement of intent, so a survivor can be read against the suite that was supposed to own it.
OWNING_SUITE = {
    "analysis/analyze_sweep.py": "analysis/test_analyze_sweep.py",
    "analysis/analyze_constrained.py": "analysis/test_analyze_constrained.py",
    "analysis/analyze_fine_sweep.py": "analysis/test_analyze_fine_sweep.py",
    "analysis/characterize.py": "analysis/test_characterize.py",
    "analysis/load_data.py": "analysis/test_load_data.py",
    "analysis/audit_claims.py": "analysis/test_audit_claims.py",
    "analysis/compare_consumer.py": "analysis/test_compare_consumer.py",
    "analysis/models/curve_model.py": "analysis/models/test_curve_model.py",
    "analysis/models/predict_constrained_frequency.py":
        "analysis/models/test_predict_constrained_frequency.py",
    "analysis/models/predict_optimal_frequency.py":
        "analysis/models/test_predict_optimal_frequency.py",
    "tools/frequency-sweep/gpu_workload.py": "tools/frequency-sweep/test_gpu_workload.py",
    "tools/frequency-sweep/join_hwinfo_voltage.py":
        "tools/frequency-sweep/test_join_hwinfo_voltage.py",
    "tools/local-model/ask_local.py": "tools/local-model/test_ask_local.py",
}

KILLED = "KILLED"
SURVIVED = "SURVIVED"
TIMEOUT = "KILLED_TIMEOUT"
INVALID = "INVALID"


def normalisePath(value):
    return str(value).replace("\\", "/")


def readLines(path):
    """Read a file as a list of lines with their endings intact.

    newline="" on the read, because universal-newline translation turns a CRLF file into LF and
    writing it back would rewrite every line in the file rather than one.
    """
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.readlines()


def writeLines(path, lines):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.writelines(lines)


def splitEnding(line):
    """A line split into its text and its line ending, so a mutant cannot change the ending."""
    for ending in ("\r\n", "\n", "\r"):
        if line.endswith(ending):
            return line[: -len(ending)], ending
    return line, ""


def validateMutant(mutant, repoRoot=REPO_ROOT):
    """Return None if the mutant can be applied, or a sentence saying why it cannot.

    Every rejection here is a mutant that would otherwise have been applied to the wrong line or
    produced a file that does not parse, and been scored as a kill on that basis.
    """
    for field in ("file", "line", "original", "mutated"):
        if field not in mutant:
            return "missing field " + repr(field)

    relative = normalisePath(mutant["file"])
    if relative not in OWNING_SUITE:
        return relative + " is not in the allowlist"

    path = repoRoot / relative
    if not path.is_file():
        return relative + " does not exist"

    if not isinstance(mutant["line"], int) or isinstance(mutant["line"], bool):
        return "line " + repr(mutant["line"]) + " is not an integer"

    lines = readLines(path)
    if not 1 <= mutant["line"] <= len(lines):
        return f"line {mutant['line']} is outside {relative} (1-{len(lines)})"

    actual, ending = splitEnding(lines[mutant["line"] - 1])
    if actual != mutant["original"]:
        # The failure this whole format exists to catch. Reported with both strings because the
        # usual cause is a model that counted lines from a docstring-stripped view.
        return (f"line {mutant['line']} of {relative} is {actual!r}, "
                f"but the mutant says it is {mutant['original']!r}")

    if mutant["mutated"] == mutant["original"]:
        return "mutated text is identical to the original, so nothing would change"

    if "\n" in str(mutant["mutated"]) or "\r" in str(mutant["mutated"]):
        return "mutated text spans more than one line"

    # A mutant that does not compile is killed by every suite that imports the module, which
    # scores as a kill while testing nothing. Rejected rather than counted.
    candidate = list(lines)
    candidate[mutant["line"] - 1] = mutant["mutated"] + ending
    try:
        compile("".join(candidate), str(path), "exec")
    except SyntaxError as error:
        return f"mutated source does not parse: {error.msg} at line {error.lineno}"

    return None


def applyMutant(mutant, repoRoot=REPO_ROOT):
    """Write the mutated line and return (path, original lines) for restoration."""
    path = repoRoot / normalisePath(mutant["file"])
    original = readLines(path)
    _, ending = splitEnding(original[mutant["line"] - 1])
    mutated = list(original)
    mutated[mutant["line"] - 1] = mutant["mutated"] + ending
    writeLines(path, mutated)
    return path, original


def purgePycache(repoRoot=REPO_ROOT):
    """Delete every __pycache__ under the repo.

    Not hygiene. A mutation that preserves file size and mtime resolution leaves a stale .pyc
    that Python will happily reuse, so the suite runs the ORIGINAL function against the mutated
    file and reports a kill that never happened. run_tests.py's docstring records this biting a
    hand-run mutation already.
    """
    for cache in repoRoot.rglob("__pycache__"):
        if ".git" in cache.parts:
            continue
        shutil.rmtree(cache, ignore_errors=True)


def runSuites(timeout, repoRoot=REPO_ROOT):
    """Run every suite and return (verdict, failedSuites, note).

    Deliberately not run_tests.runSuite: that has no timeout, and an off-by-one mutant in a loop
    bound is exactly the kind that hangs. A hang IS a detected behaviour change, so it counts as
    a kill, but it is recorded separately because it says nothing about the assertions.
    """
    if str(repoRoot) not in sys.path:
        sys.path.insert(0, str(repoRoot))
    import run_tests

    failed = []
    for suite in run_tests.findSuites(""):
        relative = suite.relative_to(repoRoot).as_posix()
        try:
            completed = subprocess.run([sys.executable, str(suite)], capture_output=True,
                                       text=True, cwd=str(repoRoot), timeout=timeout)
        except subprocess.TimeoutExpired:
            return TIMEOUT, [relative], f"{relative} did not finish within {timeout}s"

        output = completed.stdout + completed.stderr
        # Mirrors run_tests.py: a suite that exits cleanly having asserted nothing is a failure,
        # because that is what an import-time error in a plain script looks like.
        if completed.returncode != 0 or output.count("[PASS]") == 0:
            failed.append(relative)

    return (KILLED if failed else SURVIVED), failed, ""


def describe(mutant):
    return (f"{mutant['file']}:{mutant['line']}  {mutant['original'].strip()}"
            f"  ->  {mutant['mutated'].strip()}")


def gitStatus():
    return subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True,
                          cwd=str(REPO_ROOT)).stdout.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("mutants", help="JSON file of proposed mutants.")
    parser.add_argument("--out", default="tools/mutation/results.json")
    parser.add_argument("--filter", default="",
                        help="Only run mutants whose file path contains this substring.")
    parser.add_argument("--timeout", type=int, default=180,
                        help="Seconds allowed for one suite before the mutant is called a hang.")
    parser.add_argument("--limit", type=int, help="Stop after this many mutants.")
    parser.add_argument("--allow-dirty", action="store_true",
                        help="Skip the clean-tree check. Only for a scratch clone - without it "
                             "a crash mid-mutant leaves edits you cannot tell from your own.")
    args = parser.parse_args()

    dirty = gitStatus()
    if dirty and not args.allow_dirty:
        raise SystemExit(
            "Working tree is not clean. This harness edits tracked source in place, and a clean "
            "tree is what makes `git checkout .` a complete recovery if it is interrupted.\n\n"
            f"{dirty}\n\nCommit or stash first, or pass --allow-dirty.")

    mutants = json.loads(Path(args.mutants).read_text(encoding="utf-8"))
    if args.filter:
        mutants = [m for m in mutants if args.filter in normalisePath(m.get("file", ""))]
    if args.limit:
        mutants = mutants[: args.limit]
    if not mutants:
        raise SystemExit(f"No mutants to run from {args.mutants}.")

    print("Baseline: running every suite unmutated.")
    purgePycache()
    verdict, failed, note = runSuites(args.timeout)
    if verdict != SURVIVED:
        raise SystemExit(
            f"BASELINE IS NOT GREEN ({verdict}): {', '.join(failed)}. {note}\n"
            "Every mutant would read as killed and the score would mean nothing. Fix first.")
    print("Baseline green.\n")

    results = []
    started = time.time()
    for index, mutant in enumerate(mutants, 1):
        reason = validateMutant(mutant)
        if reason:
            print(f"[{index}/{len(mutants)}] {INVALID:14} {reason}")
            results.append({**mutant, "verdict": INVALID, "reason": reason})
            continue

        path, original = applyMutant(mutant)
        try:
            purgePycache()
            verdict, failed, note = runSuites(args.timeout)
        except KeyboardInterrupt:
            writeLines(path, original)
            purgePycache()
            raise SystemExit(f"\nInterrupted. {path} restored.")
        finally:
            writeLines(path, original)
        purgePycache()

        results.append({**mutant, "verdict": verdict, "killedBy": failed, "note": note})
        marker = "" if verdict != SURVIVED else "  <-- review"
        print(f"[{index}/{len(mutants)}] {verdict:14} {describe(mutant)}{marker}")

    Path(args.out).write_text(json.dumps(results, indent=2), encoding="utf-8")

    killed = [r for r in results if r["verdict"] in (KILLED, TIMEOUT)]
    survived = [r for r in results if r["verdict"] == SURVIVED]
    invalid = [r for r in results if r["verdict"] == INVALID]
    scored = len(killed) + len(survived)

    print(f"\n{len(results)} mutant(s) in {time.time() - started:.0f}s -> {args.out}")
    print(f"  killed    {len(killed)}")
    print(f"  survived  {len(survived)}")
    print(f"  invalid   {len(invalid)}  (not scored: wrong line, no-op, or does not parse)")
    if scored:
        print(f"\nmutation score {len(killed) / scored:.1%} of {scored} applicable mutants")

    if survived:
        print("\nSURVIVORS - each is either a gap in the tests or an equivalent mutant:")
        for result in survived:
            print(f"  {describe(result)}")
            if result.get("rationale"):
                print(f"      {result['rationale']}")
            print(f"      owning suite: {OWNING_SUITE[normalisePath(result['file'])]}")

    leaked = [line for line in gitStatus().splitlines()
              if normalisePath(line.split()[-1]) in OWNING_SUITE]
    if leaked:
        print("\nA MUTATED FILE WAS NOT RESTORED. Run `git checkout .` before anything else:")
        for line in leaked:
            print(f"  {line}")
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
