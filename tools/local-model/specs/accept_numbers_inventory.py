"""Acceptance check for the local model's numbers-inventory-unaudited.md output.

Written by Claude on 2026-09-23 BEFORE the model saw the task. It uses the claims auditor's own
section and number extraction, so "every number" means exactly what the auditor means by it.

    python tools/local-model/specs/accept_numbers_inventory.py CANDIDATE.md

Checks, per row: the section is one of the three, the quote appears verbatim in that section's own
text (bold markers, blockquote markers and whitespace runs normalised away on both sides), and the
number appears in the quote. Per section: the listed numbers equal the extractor's, as a multiset.
It does NOT judge "what it is", "kind" or "likely source"; that is the review's job.
"""

import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis"))
import audit_claims as auditor  # noqa: E402

SECTIONS = ("5.4.2", "5.7", "5.7.7")
KINDS = {"measurement", "derived", "count", "setting", "restated", "other"}


def own_text(document, section):
    body = auditor.extractSection(document, section)
    return re.split(r"\n#{2,6} ", body.split("\n", 1)[1])[0].strip()


def flatten(text):
    text = re.sub(r"(?m)^\s*>\s?", "", text.replace("**", ""))
    return re.sub(r"\s+", " ", text).strip()


def rows_of(markdown):
    rows = []
    for line in markdown.splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|\s*:?-{3,}", line):
            continue
        cells = [cell.strip().replace("\\|", "|") for cell in re.split(r"(?<!\\)\|", line)[1:-1]]
        if cells and cells[0].lower() == "section":
            continue
        rows.append(cells)
    return rows


def main():
    candidate = Path(sys.argv[1])
    document = auditor.readDocument("docs/PAPER_DRAFT.md")
    texts = {s: own_text(document, s) for s in SECTIONS}
    expected = {s: Counter(auditor.numbersIn(texts[s])) for s in SECTIONS}
    rows = rows_of(candidate.read_text(encoding="utf-8"))
    listed = {s: Counter() for s in SECTIONS}
    problems = []
    for number, cells in enumerate(rows, 1):
        if len(cells) != 6:
            problems.append(f"row {number}: {len(cells)} cells, expected 6: {cells}")
            continue
        section, value, quote, _what, kind, _source = cells
        value = value.strip("`")
        if section not in SECTIONS:
            problems.append(f"row {number}: unknown section {section!r}")
            continue
        listed[section][value] += 1
        if kind.strip("`") not in KINDS:
            problems.append(f"row {number}: kind {kind!r} is not one of {sorted(KINDS)}")
        if flatten(quote) not in flatten(texts[section]):
            problems.append(f"row {number}: quote not found verbatim in {section}: {quote[:80]!r}")
        elif value not in auditor.numbersIn(quote):
            problems.append(f"row {number}: {value!r} is not a number in its own quote")
    for section in SECTIONS:
        missing = expected[section] - listed[section]
        extra = listed[section] - expected[section]
        if missing:
            problems.append(f"{section}: missing {dict(missing)}")
        if extra:
            problems.append(f"{section}: listed but not in the section (or listed too often) {dict(extra)}")
    total = sum(sum(c.values()) for c in expected.values())
    print(f"{len(rows)} rows for {total} expected numbers.")
    for problem in problems:
        print("FAIL  " + problem)
    print("PASS" if not problems else f"\n{len(problems)} problem(s).")
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
