"""
Checks for the mutation harness itself, which has to be trustworthy before its verdicts are.

WHY THIS SUITE IS NOT OPTIONAL
    run_mutants.py edits tracked source in place and then reports a number that will be quoted
    in the paper. Two of its failure modes are silent and both would inflate that number:

      - a mutant applied to the WRONG LINE still breaks something, so it scores as killed while
        having tested nothing that was intended;
      - a mutant that does not parse is killed by every suite that imports the module, which
        also scores as killed and also tests nothing.

    Both are refused by validateMutant, so most of what follows is aimed there. A third failure
    mode is destructive rather than misleading - restoration that does not round-trip byte for
    byte would leave the repo subtly rewritten after a clean run - and it gets its own checks
    on CRLF files, because universal-newline translation is exactly how that happens.

HERMETIC
    No GPU, no llama-server, no network, and nothing outside a temporary directory is written.
    The real repository is only ever READ. That matters more here than in most suites: this is
    the one suite whose subject can modify the working tree, so it must not be able to.

Run: python tools/mutation/test_mutation.py
"""

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import run_mutants
from run_mutants import applyMutant, purgePycache, readLines, splitEnding, validateMutant
from generate_mutants import extractJsonArray, numberSource

failures = []


def check(description, condition, detail=""):
    if not condition:
        print(f"[FAIL] {description}")
        if detail:
            print(f"  Detail: {detail}")
        failures.append(description)
    else:
        print(f"[PASS] {description}")


def readRaw(path):
    """Read without universal-newline translation. Path.read_text(newline=) is 3.13+."""
    with open(path, encoding="utf-8", newline="") as handle:
        return handle.read()


def writeRaw(path, text):
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(text)


# A throwaway repo with one allowlisted file, so validateMutant can be exercised against real
# bytes on disk without the real sources ever being opened for writing.
scratch = tempfile.TemporaryDirectory()
fakeRoot = Path(scratch.name)
(fakeRoot / "analysis").mkdir()
SUBJECT = "analysis/load_data.py"
BODY = "def scale(value, factor):\n    if value > 10:\n        return value * factor\n    return value\n"
writeRaw(fakeRoot / SUBJECT, BODY)


def mutant(**overrides):
    base = {"file": SUBJECT, "line": 2, "original": "    if value > 10:",
            "mutated": "    if value >= 10:"}
    base.update(overrides)
    return base


# --- validateMutant: the guard that makes a misremembered line cheap ---------------------

check("a correct mutant validates",
      validateMutant(mutant(), fakeRoot) is None,
      validateMutant(mutant(), fakeRoot))

check("original text that does not match the file is refused",
      "but the mutant says" in (validateMutant(
          mutant(original="    if value > 11:"), fakeRoot) or ""))

# The specific miscount this format exists to catch: right text, wrong line number. Line 3 is
# real, so nothing crashes - the mutant would simply have been applied somewhere else.
check("right text on the wrong line number is refused",
      validateMutant(mutant(line=3), fakeRoot) is not None)

check("a line number past the end of the file is refused",
      "outside" in (validateMutant(mutant(line=99), fakeRoot) or ""))

# Asserting only "is not None" here was too weak, and the harness's own gate caught it: with the
# range check widened to accept 0, this mutant is still refused - but by the text comparison,
# because lines[0 - 1] is the LAST line and does not match. The reason has to be checked, or the
# check passes whether or not the bound is right.
check("line 0 is refused as out of range, not by wrapping to the last line",
      "outside" in (validateMutant(mutant(line=0), fakeRoot) or ""))

check("a non-integer line number is refused",
      "not an integer" in (validateMutant(mutant(line="2"), fakeRoot) or ""))

# True is an int in Python, so `isinstance(line, int)` alone would accept it and index line 1.
check("a boolean line number is refused",
      "not an integer" in (validateMutant(mutant(line=True), fakeRoot) or ""))

check("a mutant identical to the original is refused",
      "identical" in (validateMutant(
          mutant(mutated="    if value > 10:"), fakeRoot) or ""))

check("a mutant that does not parse is refused, not scored as a kill",
      "does not parse" in (validateMutant(
          mutant(mutated="    if value > 10"), fakeRoot) or ""))

check("a multi-line replacement is refused",
      validateMutant(mutant(mutated="    x = 1\n    y = 2"), fakeRoot) is not None)

check("a file outside the allowlist is refused",
      "allowlist" in (validateMutant(
          mutant(file="analysis/secrets.py"), fakeRoot) or ""))

check("an allowlisted file that does not exist is refused",
      "does not exist" in (validateMutant(
          mutant(file="analysis/characterize.py"), fakeRoot) or ""))

for field in ("file", "line", "original", "mutated"):
    incomplete = mutant()
    del incomplete[field]
    check(f"a mutant missing {field!r} is refused",
          "missing field" in (validateMutant(incomplete, fakeRoot) or ""))

check("a backslash path is normalised rather than rejected",
      validateMutant(mutant(file="analysis\\load_data.py"), fakeRoot) is None)


# --- applyMutant and restoration: must round-trip byte for byte --------------------------

path, original = applyMutant(mutant(), fakeRoot)
after = readRaw(fakeRoot / SUBJECT)
check("applyMutant replaces the target line",
      "if value >= 10:" in after)
check("applyMutant changes exactly one line",
      sum(1 for a, b in zip(BODY.splitlines(), after.splitlines()) if a != b) == 1)
check("applyMutant returns the original lines for restoration",
      "".join(original) == BODY)

run_mutants.writeLines(path, original)
check("restoring returns the file byte for byte",
      readRaw(fakeRoot / SUBJECT) == BODY)

# A CRLF file is where restoration goes wrong: read_text() translates endings, so a naive
# round-trip rewrites every line and `git status` shows the whole file as modified.
CRLF_BODY = BODY.replace("\n", "\r\n")
writeRaw(fakeRoot / SUBJECT, CRLF_BODY)
crlfPath, crlfOriginal = applyMutant(mutant(), fakeRoot)
mutatedCrlf = readRaw(fakeRoot / SUBJECT)
check("a CRLF file keeps CRLF endings when mutated",
      "\n" not in mutatedCrlf.replace("\r\n", ""))
check("the mutated line does not gain or lose its ending",
      mutatedCrlf.count("\r\n") == CRLF_BODY.count("\r\n"))
run_mutants.writeLines(crlfPath, crlfOriginal)
check("restoring a CRLF file returns it byte for byte",
      readRaw(fakeRoot / SUBJECT) == CRLF_BODY)
writeRaw(fakeRoot / SUBJECT, BODY)

check("splitEnding separates CRLF",
      splitEnding("abc\r\n") == ("abc", "\r\n"))
check("splitEnding separates LF",
      splitEnding("abc\n") == ("abc", "\n"))
check("splitEnding handles a final line with no ending",
      splitEnding("abc") == ("abc", ""))
check("readLines keeps endings intact",
      readLines(fakeRoot / SUBJECT)[1] == "    if value > 10:\n")


# --- purgePycache: the stale-bytecode trap run_tests.py documents ------------------------

cache = fakeRoot / "analysis" / "__pycache__"
cache.mkdir()
(cache / "load_data.cpython-312.pyc").write_bytes(b"stale")
gitCache = fakeRoot / ".git" / "__pycache__"
gitCache.mkdir(parents=True)
(gitCache / "keep.pyc").write_bytes(b"keep")
purgePycache(fakeRoot)
check("purgePycache removes a __pycache__ directory",
      not cache.exists())
check("purgePycache leaves anything under .git alone",
      (gitCache / "keep.pyc").exists())


# --- extractJsonArray: the model's reply is not always clean -----------------------------

check("a bare array parses",
      json.loads(extractJsonArray('[{"line": 1}]')) == [{"line": 1}])
check("prose before the array is ignored",
      json.loads(extractJsonArray('Sure, here you go:\n[{"line": 1}]')) == [{"line": 1}])
check("a markdown fence around the array is ignored",
      json.loads(extractJsonArray('```json\n[{"line": 2}]\n```')) == [{"line": 2}])
# The reason for a bracket-matching scan rather than a regex: a rationale is free text and
# routinely contains a bracket, which a lazy match would treat as the end of the array.
#
# The bracket here is UNBALANCED on purpose. A balanced "[0]" inside a string leaves the depth
# count correct by accident, so the scan lands in the right place even with string tracking
# disabled - the harness's own gate caught that this check was passing for the wrong reason.
check("an unbalanced bracket inside a string does not end the scan",
      json.loads(extractJsonArray('[{"r": "closes ] early"}, {"r": "b"}]'))
      == [{"r": "closes ] early"}, {"r": "b"}])
check("an unbalanced opening bracket inside a string does not extend the scan",
      json.loads(extractJsonArray('[{"r": "opens [ here"}] trailing text'))
      == [{"r": "opens [ here"}])
check("an escaped quote inside a string does not end the scan",
      json.loads(extractJsonArray('[{"r": "he said \\"hi\\" [x]"}]'))
      == [{"r": 'he said "hi" [x]'}])
check("a nested array is spanned rather than cut short",
      json.loads(extractJsonArray('[{"r": [1, 2]}, {"r": 3}]')) == [{"r": [1, 2]}, {"r": 3}])
check("a truncated array returns None instead of a partial parse",
      extractJsonArray('[{"line": 1}, {"line"') is None)
check("a reply with no array at all returns None",
      extractJsonArray("I cannot do that.") is None)


# --- numberSource: the model copies line numbers rather than counting them ---------------

numbered = numberSource("alpha\nbeta\ngamma\n")
check("numberSource starts at 1",
      numbered.splitlines()[0] == "1\talpha")
check("numberSource separates the number with a tab",
      all(line.count("\t") >= 1 for line in numbered.splitlines()))
check("numberSource numbers every line",
      len(numbered.splitlines()) == 3)
# A file of 100+ lines that numbers 9 and 10 at different widths makes the column ragged and
# the model more likely to miscount the indentation that follows.
check("numberSource right-aligns to a constant width",
      numberSource("a\n" * 10).splitlines()[0].startswith(" 1\t"))
check("numberSource preserves leading whitespace after the tab",
      numberSource("    indented\n").splitlines()[0] == "1\t    indented")


# --- the allowlist describes files that are really there ---------------------------------

repoRoot = Path(__file__).resolve().parents[2]
for source, suite in run_mutants.OWNING_SUITE.items():
    check(f"allowlisted source exists: {source}", (repoRoot / source).is_file())
    check(f"its owning suite exists: {suite}", (repoRoot / suite).is_file())

scratch.cleanup()

if failures:
    print(f"FAILED CHECKS: {', '.join(failures)}")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")
