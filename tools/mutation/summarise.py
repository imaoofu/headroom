"""
Turn a mutant results file into the two things worth knowing: the score, and where the gaps are.

WHY THE ENCLOSING FUNCTION IS THE INTERESTING AXIS
    A bare mutation score says a suite caught 40% and leaves you guessing which 60% it missed.
    The first file run through this harness answered that immediately: on curve_model.py all
    three kills landed in the three functions test_curve_model.py imports and calls, and six of
    seven survivors landed in functions it never calls at all. The suite was not weak on what it
    covered - it was perfect on what it covered and absent everywhere else.

    That distinction changes what you do about it. "The tests are weak" invites rewriting them.
    "The tests cover the helpers and not the function that produces the number" tells you which
    function to write a test for.

HOW THE MAPPING IS DONE
    ast, not regex. A `def` inside a class or nested in a closure still has to attribute to the
    right name, and the line ranges have to nest correctly so an inner function wins over the
    outer one. ast.walk plus end_lineno gives that for free; a regex over `^def ` does not, and
    would silently attribute every method to whatever module-level function preceded it.

WHAT "CALLED BY THE SUITE" MEANS, AND ITS LIMIT
    The suite is parsed and every name in CALL position is collected, plus everything it imports
    from the module under test. A substring search was tried first and was too generous to be
    worth printing: it marked curve_model's report() and main() as covered because those words
    appear in the suite's prose, when the suite calls neither.

    Still one-directional evidence. "Never called" is solid - the suite cannot possibly exercise
    that function, so a survivor inside it is a coverage hole rather than a subtle assertion
    gap. "Called" proves only that the name is invoked somewhere, NOT that the branch the mutant
    changed was reached. So a survivor inside a called function still needs reading; it is just
    a different kind of finding.

USAGE
    python tools/mutation/summarise.py                       reads results.json
    python tools/mutation/summarise.py other-results.json
"""

import argparse
import ast
import json
import pathlib
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_mutants import KILLED, OWNING_SUITE, SURVIVED, TIMEOUT, normalisePath

REPO_ROOT = Path(__file__).resolve().parents[2]


def functionRanges(path):
    """[(startLine, endLine, qualifiedName)] for every def in a file, innermost last.

    utf-8-sig because one source carries a BOM and ast.parse refuses it otherwise - the same
    trap that made every gpu_workload.py mutant look unparseable.
    """
    tree = ast.parse(path.read_text(encoding="utf-8-sig"))
    ranges = []

    def walk(node, prefix):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                name = f"{prefix}{child.name}"
                if not isinstance(child, ast.ClassDef):
                    ranges.append((child.lineno, child.end_lineno, name))
                walk(child, name + ".")
            else:
                walk(child, prefix)

    walk(tree, "")
    # Sorted by span, widest first, so the LAST match for a line is the innermost function.
    return sorted(ranges, key=lambda item: item[1] - item[0], reverse=True)


def namesTheSuiteCalls(suitePath, moduleStem):
    """Every function name the suite invokes, plus what it imports from the module under test.

    Imports count because a suite that does `from curve_model import regretPercent` and then
    passes it somewhere is exercising it even if the Call node names something else. Attribute
    calls contribute their final component, so `analyzeSweep.loadSweep(...)` counts for
    loadSweep - several suites import the module rather than the names.
    """
    tree = ast.parse(suitePath.read_text(encoding="utf-8-sig"))
    called = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                called.add(target.id)
            elif isinstance(target, ast.Attribute):
                called.add(target.attr)
        elif isinstance(node, ast.ImportFrom) and (node.module or "").endswith(moduleStem):
            called.update(alias.name for alias in node.names)
    return called


def enclosingFunction(ranges, line):
    found = "<module level>"
    for start, end, name in ranges:
        if start <= line <= end:
            found = name
    return found


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("results", nargs="?", default="tools/mutation/results.json")
    args = parser.parse_args()

    results = json.loads(Path(args.results).read_text(encoding="utf-8"))

    rangesByFile, calledByFile = {}, {}
    for relative in OWNING_SUITE:
        rangesByFile[relative] = functionRanges(REPO_ROOT / relative)
        calledByFile[relative] = namesTheSuiteCalls(
            REPO_ROOT / OWNING_SUITE[relative], pathlib.Path(relative).stem)

    for result in results:
        relative = normalisePath(result["file"])
        result["function"] = enclosingFunction(rangesByFile[relative], result["line"])
        # The bare name, so a qualified "Class.method" matches a call to "method".
        leaf = result["function"].split(".")[-1]
        result["suiteMentions"] = leaf in calledByFile[relative]

    print(f"{'file':<52} {'killed':>7} {'lived':>6} {'invalid':>8} {'score':>7}")
    print("-" * 84)
    overall = Counter()
    byFile = defaultdict(Counter)
    for result in results:
        byFile[normalisePath(result["file"])][result["verdict"]] += 1
        overall[result["verdict"]] += 1

    for relative in sorted(byFile):
        counts = byFile[relative]
        killed = counts[KILLED] + counts[TIMEOUT]
        lived = counts[SURVIVED]
        scored = killed + lived
        score = f"{killed / scored:.0%}" if scored else "n/a"
        print(f"{relative:<52} {killed:>7} {lived:>6} {counts['INVALID']:>8} {score:>7}")

    killed = overall[KILLED] + overall[TIMEOUT]
    lived = overall[SURVIVED]
    scored = killed + lived
    print("-" * 84)
    print(f"{'TOTAL':<52} {killed:>7} {lived:>6} {overall['INVALID']:>8} "
          f"{killed / scored:>6.0%}" if scored else "no applicable mutants")

    survivors = [r for r in results if r["verdict"] == SURVIVED]
    unmentioned = [r for r in survivors if not r["suiteMentions"]]
    print(f"\n{len(survivors)} survivor(s). {len(unmentioned)} sit in functions the owning suite "
          f"never calls, so they are\ncoverage holes rather than weak assertions. The rest are "
          f"in functions the suite does reach.\n")

    grouped = defaultdict(list)
    for result in survivors:
        grouped[(normalisePath(result["file"]), result["function"],
                 result["suiteMentions"])].append(result)

    for (relative, function, mentioned) in sorted(grouped):
        tag = "" if mentioned else "   [SUITE NEVER CALLS THIS FUNCTION]"
        print(f"{relative}  ::  {function}(){tag}")
        for result in grouped[(relative, function, mentioned)]:
            print(f"    L{result['line']:<5} {result['original'].strip()[:70]}")
            print(f"           -> {result['mutated'].strip()[:70]}")
            if result.get("rationale"):
                print(f"           {result['rationale']}")
        print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
