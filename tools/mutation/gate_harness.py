"""
Break the mutation harness on purpose and confirm its own suite notices.

WHY THIS IS A SCRIPT AND NOT A RUN OF run_mutants.py
    run_mutants.py is not in its own allowlist, deliberately: mutating the mutation runner while
    it is running is a way to lose the restore path along with the file. The harness therefore
    gets the same treatment every other suite in this repo got before it was accepted - a small
    set of hand-written mutations, applied and reverted around a single suite invocation.

    Mutations are addressed BY LINE NUMBER with the expected text checked, not by text search.
    Line 107 of run_mutants.py contains backslash escapes, and passing those through a shell
    heredoc to a search-and-replace mangled them silently: the anchor matched nothing, the
    mutation was skipped, and the run reported a clean skip rather than an untested line.

WHAT A SURVIVOR MEANS HERE
    That test_mutation.py does not check the behaviour the mutation changed. Two were found the
    first time this ran - a line-0 check that passed for the wrong reason, and a bracket-in-
    string check whose bracket was balanced - and both are now checked properly.

Run: python tools/mutation/gate_harness.py
"""

import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUITE = REPO_ROOT / "tools" / "mutation" / "test_mutation.py"

# (file, line number, expected text at that line, replacement, what it breaks)
MUTATIONS = [
    ("tools/mutation/run_mutants.py", 'if actual != mutant["original"]:',
     'if False and actual != mutant["original"]:',
     "drop the original-text match check"),
    ("tools/mutation/run_mutants.py",
     'return f"mutated source does not parse: {error.msg} at line {error.lineno}"',
     'return None',
     "accept mutants that do not compile"),
    # RAW strings. The line being matched contains the two characters backslash-r, not a
    # carriage return, and a plain literal here evaluates to the control character instead - so
    # the anchor matches nothing and the mutation is silently skipped. That is exactly the
    # failure the docstring above describes, and it happened here first.
    ("tools/mutation/run_mutants.py", r'for ending in ("\r\n", "\n", "\r"):',
     r'for ending in ("\n", "\r\n", "\r"):',
     "check LF before CRLF, so a CRLF line keeps a stray carriage return"),
    ("tools/mutation/run_mutants.py", 'if not 1 <= mutant["line"] <= len(lines):',
     'if not 0 <= mutant["line"] <= len(lines):',
     "allow line 0, which indexes the last line instead"),
    ("tools/mutation/run_mutants.py", 'if ".git" in cache.parts:',
     'if False:',
     "purge caches under .git as well"),
    ("tools/mutation/run_mutants.py", 'compile("".join(candidate).lstrip("﻿"), str(path), "exec")',
     'compile("".join(candidate), str(path), "exec")',
     "stop stripping the BOM for the compile check"),
    ("tools/mutation/run_mutants.py", 'if mutant["mutated"] == mutant["original"]:',
     'if False:',
     "accept a mutant that changes nothing"),
    ("tools/mutation/generate_mutants.py", 'if inString:',
     'if False:',
     "stop tracking strings when scanning for the JSON array"),
    ("tools/mutation/generate_mutants.py",
     'return "\\n".join(f"{index:>{width}}\\t{line}" for index, line in enumerate(lines, 1))',
     'return "\\n".join(f"{index}\\t{line}" for index, line in enumerate(lines, 1))',
     "drop the constant-width line numbering"),
    ("tools/mutation/generate_mutants.py", 'start = text.find("[")',
     'start = text.rfind("[")',
     "scan from the LAST bracket instead of the first"),
]


def findLine(lines, wanted):
    """The 1-based line whose stripped text equals `wanted`, or None if it is not unique."""
    hits = [index for index, line in enumerate(lines, 1) if line.strip() == wanted]
    return hits[0] if len(hits) == 1 else None


def purge():
    for cache in REPO_ROOT.rglob("__pycache__"):
        if ".git" not in cache.parts:
            shutil.rmtree(cache, ignore_errors=True)


def main():
    caught, survived, skipped = [], [], []

    for relative, expected, replacement, label in MUTATIONS:
        path = REPO_ROOT / relative
        with open(path, encoding="utf-8", newline="") as handle:
            original = handle.read()
        lines = original.splitlines(keepends=True)

        number = findLine(lines, expected)
        if number is None:
            skipped.append(f"{label}: {expected!r} is not a unique line in {relative}")
            continue

        indent = lines[number - 1][: len(lines[number - 1]) - len(lines[number - 1].lstrip())]
        ending = lines[number - 1][len(lines[number - 1].rstrip("\r\n")):]
        mutated = list(lines)
        mutated[number - 1] = indent + replacement + ending

        with open(path, "w", encoding="utf-8", newline="") as handle:
            handle.writelines(mutated)
        try:
            purge()
            result = subprocess.run([sys.executable, str(SUITE)], capture_output=True,
                                    text=True, cwd=str(REPO_ROOT), timeout=120)
        finally:
            with open(path, "w", encoding="utf-8", newline="") as handle:
                handle.write(original)

        if result.returncode != 0:
            failed = [line for line in result.stdout.splitlines() if line.startswith("[FAIL]")]
            caught.append((label, failed))
        else:
            survived.append(label)

    purge()

    for label, failed in caught:
        print(f"  CAUGHT    {label}")
        for line in failed[:2]:
            print(f"              {line}")
    for label in survived:
        print(f"  SURVIVED  {label}  <-- test_mutation.py does not check this")
    for note in skipped:
        print(f"  SKIPPED   {note}")

    print(f"\n{len(caught)}/{len(MUTATIONS)} deliberate bugs caught, "
          f"{len(survived)} survived, {len(skipped)} skipped")
    return 1 if survived or skipped else 0


if __name__ == "__main__":
    sys.exit(main())
