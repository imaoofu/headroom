"""Checks for verify_citations.py.

The coverage guard is the part worth testing, because it is the part that has to hold when a
contributor - human or model - adds a citation nobody opened. It fails open in the dangerous
direction if the id regex misses a format, so most of these are regex checks against the shapes
this repository actually uses.

Network is NOT touched here. `--live` is exercised by running the tool, not by a test: a suite
that needs arXiv to be reachable fails on a train, and a test people skip is worse than none.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import verify_citations as vc

passed = 0


def check(description, condition):
    global passed
    if condition:
        passed += 1
        print(f"  [PASS] {description}")
    else:
        print(f"  [FAIL] {description}")
        raise AssertionError(description)


print("the id regex - it must catch every shape this repository writes")

shapes = {
    "arXiv:2211.07260": "2211.07260",
    "arxiv.org/abs/2211.07260": "2211.07260",
    "https://arxiv.org/abs/1407.8116": "1407.8116",
    "[arXiv:2104.00486](https://arxiv.org/abs/2104.00486)": "2104.00486",
    "arXiv 2607.00819": "2607.00819",
    "(arXiv [1905.11012](https://arxiv.org/abs/1905.11012))": "1905.11012",
}
for text, expected in shapes.items():
    found = vc.ARXIV_ID.findall(text)
    check(f"{text[:44]!r} -> {expected}", expected in found)

# A four-digit suffix and a five-digit suffix are both real arXiv formats, and this corpus has both
# (1407.8116 is four, 2211.07260 is five). A regex pinned to one silently drops half the corpus.
check("a 4-digit suffix parses", vc.ARXIV_ID.findall("arXiv:1407.8116") == ["1407.8116"])
check("a 5-digit suffix parses", vc.ARXIV_ID.findall("arXiv:2211.07260") == ["2211.07260"])

print()
print("the registry - every entry asserts someone opened the source")

for arxivId, record in vc.CITATIONS.items():
    check(f"{arxivId} records a first author", bool(record.get("firstAuthor")))
    check(f"{arxivId} records a title fragment", bool(record.get("titleFragment")))
    check(f"{arxivId} records a plausible author count",
          isinstance(record.get("authorCount"), int) and record["authorCount"] > 0)

check("no id is both a citation and a lead - it is one or the other",
      not (set(vc.CITATIONS) & set(vc.LEADS)))

print()
print("surname extraction")

check("a simple name", vc.surnameOf("Xinxin Mei") == "Mei")
check("an initialled name", vc.surnameOf("D. C. Price") == "Price")
check("a particle surname keeps only the last token - a KNOWN limitation, pinned so that a "
      "future corpus containing one is noticed rather than silently mishandled",
      vc.surnameOf("Ben van Werkhoven") == "Werkhoven")
check("an empty name does not crash", vc.surnameOf("   ") == "")

print()
print("coverage against the real repository")

problems, cited = vc.checkCoverage()
check("the repository cites at least the eight registered sources", len(cited) >= len(vc.CITATIONS))
check("coverage is currently clean - every cited id is registered or a recorded lead",
      problems == [])

# ⛔ THE REGRESSION THAT MATTERS. An unregistered id must FAIL, or the guard is decoration. This
# asserts the failure path directly rather than trusting that a clean run means it works.
realCitations = dict(vc.CITATIONS)
try:
    vc.CITATIONS.pop("2211.07260")
    problemsWithout, _ = vc.checkCoverage()
    check("removing a registration makes coverage FAIL - the guard has teeth",
          any("2211.07260" in p for p in problemsWithout))
finally:
    vc.CITATIONS.clear()
    vc.CITATIONS.update(realCitations)

check("the registry is restored after the failure-path test", "2211.07260" in vc.CITATIONS)

print()
print("the one discrepancy this checker found, and how it resolved")

# ✅ RESOLVED 2026-09-18, and the resolution is the part worth pinning: the REPOSITORY was right
# and arXiv's preprint metadata was the misleading record. Had the rule been "make the registry
# match arXiv", this checker would have INTRODUCED the project's fifth citation error while
# appearing to remove one. The mismatch between `firstAuthor` (arXiv's Mei) and `publishedAs`
# (TPDS's Wang) is therefore DELIBERATE and must not be tidied away.
check("no discrepancy is left open", vc.UNRESOLVED_DISCREPANCIES == {})
check("2104.00486's resolution is kept on the record", "2104.00486" in vc.RESOLVED_DISCREPANCIES)
check("the registry still expects arXiv's lead author for the live comparison",
      vc.CITATIONS["2104.00486"]["firstAuthor"] == "Mei")
check("...and separately records what the PUBLISHED paper should be cited as",
      "Qiang Wang" in vc.CITATIONS["2104.00486"]["publishedAs"]
      and "Non-Preemptive" in vc.CITATIONS["2104.00486"]["publishedAs"])

print()
print(f"{passed} checks passed.")
print("These check the GUARD, not the citations. Whether a paper says what this project claims "
      "it says is not decidable by a script - it needs a person with the PDF open, and this "
      "project has been wrong about it four times.")
