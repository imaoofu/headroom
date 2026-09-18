"""Check this repository's arXiv citations against arXiv's own metadata.

WHY THIS EXISTS
    This project has recorded FOUR wrong citations, and one of them was invented outright - a
    four-author list for its single most important source, two of whose names do not appear on
    the paper. Every one came from a plausible-sounding summary rather than from the record.
    None was caught by review; all were caught later, by accident.

    From 2026-09-17 a second AI assistant works alongside this one. A model that returns a
    confident citation is the exact failure mode above, industrialised. So citations stop being
    something a reader trusts and become something a script checks.

THE GUARD THAT MATTERS MOST IS NOT THE COMPARISON
    It is that EVERY arXiv id appearing anywhere in the repository's markdown must be present in
    CITATIONS below. Add a citation without registering it and this fails. That is what makes an
    unverified citation from any contributor - human, me, or another model - impossible to land
    quietly. The comparison against live metadata is the second line, not the first.

    ⚠️ Registering an entry is an ASSERTION THAT SOMEONE OPENED THE SOURCE. It is not a formality
    and it is not something to do in bulk to make this pass. `docs/RELATED-WORK.md` carries read
    status for the same reason.

WHY curl AND NOT urllib
    arXiv's API returns 406 to Python's urllib from this environment and 200 to curl. Verified
    both ways 2026-09-17 rather than assumed. curl ships with Windows 10+ and every CI image
    this project uses.

Usage:
    python analysis/verify_citations.py            # offline: registry coverage only
    python analysis/verify_citations.py --live     # also fetch arXiv and compare
    python analysis/verify_citations.py --check    # exit non-zero if anything is wrong
"""

import argparse
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ATOM = {"a": "http://www.w3.org/2005/Atom"}

# arXiv id -> what this repository asserts about it.
#
# `firstAuthor` is the surname arXiv lists FIRST. It is recorded separately from the prose because
# "X et al." is the form that goes wrong: the set of authors can be right while the leading name is
# not, and only the leading name appears in most citations.
#
# `titleFragment` must appear in arXiv's title, case-insensitively, after whitespace collapsing.
CITATIONS = {
    "2211.07260": {
        "firstAuthor": "Schoonhoven",
        "authorCount": 4,
        "titleFragment": "optimizing GPUs for energy efficiency",
        "note": "The ridge point. THE retraction source. This repository invented two co-authors "
                "for it and used 'van Werkhoven et al.' for a day; van Werkhoven is THIRD.",
    },
    "1610.01784": {
        "firstAuthor": "Mei",
        "authorCount": 3,
        "titleFragment": "Survey and Measurement Study of GPU DVFS",
        "note": "Closes the consumer-optimum claim. GTX 980 swept 480-1080 against a 950 default.",
    },
    "1905.11012": {
        "firstAuthor": "Tang",
        "authorCount": 4,
        "titleFragment": "Impact of GPU DVFS on the Energy and Performance of Deep Learning",
        "note": "Swept below default and found the optimum there. Same HKBU group as the V100 set.",
    },
    "1407.8116": {
        "firstAuthor": "Price",
        "authorCount": 5,
        "titleFragment": "Optimizing performance per watt on GPUs",
        "note": "Recorded as 'Mei et al.' in PRIOR-ART-20260912.md until corrected 2026-09-13.",
    },
    "2104.00486": {
        "firstAuthor": "Mei",
        "authorCount": 6,
        "titleFragment": "Task Scheduling with Deadline Constraint",
        "note": "SEE discrepancy note in the module docstring of the check below. The repository "
                "cites this as 'Wang, Mei, Liu, Leung, Li, Chu'; arXiv orders it Mei, Wang, Chu, "
                "Liu, Leung, Li. Same six people, different lead author. UNRESOLVED.",
    },
    "2208.11035": {
        "firstAuthor": "Sinha",
        "authorCount": 6,
        "titleFragment": "Not All GPUs Are Created Equal",
        "note": "Chip-to-chip variability, 140 MHz / ~11%.",
    },
    "2501.08219": {
        "firstAuthor": "Maliakel",
        "authorCount": 3,
        "titleFragment": "LLM Inference Energy-Performance Tradeoffs",
        "note": "",
    },
    "2607.00819": {
        "firstAuthor": "Afzal",
        "authorCount": 3,
        "titleFragment": "Energy-Efficiency Sweet Spots in Modern GPUs",
        "note": "Reference [10], which had NO author in the paper until 2026-09-13.",
    },
}

# ⛔ AN OPEN DISCREPANCY, RECORDED RATHER THAN PAPERED OVER.
#
# For 2104.00486 the repository records the author list as "Wang, Mei, Liu, Leung, Li, Chu" and the
# title as "Energy-aware NON-PREEMPTIVE Task Scheduling...". arXiv's metadata gives the order
# "Mei, Wang, Chu, Liu, Leung, Li" and a title without "Non-Preemptive".
#
# The SET of six authors agrees. Only the order and one title word differ, and both are things a
# journal version legitimately changes from a preprint. So this is NOT evidence the repository is
# wrong - it is evidence that nobody has checked the PUBLISHED TPDS version, which is the artifact
# actually cited.
#
# 🔑 It matters because the short form is "Wang et al." throughout, and if arXiv's order is the
# published one then every one of those should read "Mei et al.". §2.7 now rests on this source.
#
# RESOLVE IT BY OPENING THE TPDS PAPER, not by editing either value to match the other.
UNRESOLVED_DISCREPANCIES = {
    "2104.00486": "Repository says first author Wang; arXiv says Mei. Check the published IEEE "
                  "TPDS version - a preprint's author order is not authoritative for it.",
}

# Ids the repository mentions as UNREAD LEADS rather than citations. Recorded, not cited.
#
# 🔑 The distinction is the point. PAPER_DRAFT.md names these and says their figures "could NOT be
# confirmed from source, and are deliberately omitted rather than cited as either support or
# threat." That is the behaviour this project wants, so the checker must not punish it - but it
# must also not let a lead drift into a citation unnoticed. Promote one to CITATIONS the moment
# any sentence relies on it, and only after opening it.
LEADS = {
    "2001.07104": "Braun, Nikas, Song, Heuveline, Froening - 'A Simple Model for Portable and "
                  "Fast Prediction of Execution Time and Power Consumption of GPU Kernels'. "
                  "Surfaced by a delegated search agent 2026-09-06; figures unconfirmed from "
                  "source, so deliberately NOT cited. Metadata verified against arXiv 2026-09-17.",
}

# Files that may contain arXiv ids without registering them, because they are historical records
# rather than live citations. A search log records what a search FOUND, including things later
# discarded, so freezing its contents behind this check would be wrong.
COVERAGE_EXEMPT = {
    "docs/PRIOR-ART-20260912.md",
    "docs/PRIOR-ART-20260913.md",
    "docs/LITERATURE-ACTIONS-20260907.md",
}

ARXIV_ID = re.compile(r"arxiv[.:/]*(?:org/abs/)?\s*(\d{4}\.\d{4,5})", re.IGNORECASE)


def markdownFiles():
    """Every markdown file in the repository, excluding gitignored trees."""
    out = []
    for path in REPO_ROOT.rglob("*.md"):
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel.startswith(("docs/papers/", "node_modules/", ".git/")):
            continue
        out.append(path)
    return sorted(out)


def citedIds():
    """arXiv ids mentioned in the repository, mapped to the files that mention them."""
    found = {}
    for path in markdownFiles():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in COVERAGE_EXEMPT:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in ARXIV_ID.finditer(text):
            found.setdefault(match.group(1), set()).add(rel)
    return found


def fetchArxiv(arxivId, timeoutSeconds=25):
    """Live metadata for one id, or None if it could not be fetched.

    Returns None rather than raising on a network failure: being offline is not a citation
    defect, and a check that fails when the wifi drops teaches people to skip it.
    """
    try:
        result = subprocess.run(
            ["curl", "-sS", "-m", str(timeoutSeconds), "-A", "headroom-citation-check/1.0",
             f"https://export.arxiv.org/api/query?id_list={arxivId}"],
            capture_output=True, text=True, timeout=timeoutSeconds + 10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        entry = ET.fromstring(result.stdout).find("a:entry", ATOM)
    except ET.ParseError:
        return None
    if entry is None:
        return None
    titleNode = entry.find("a:title", ATOM)
    if titleNode is None or titleNode.text is None:
        return None
    authors = [a.find("a:name", ATOM).text for a in entry.findall("a:author", ATOM)
               if a.find("a:name", ATOM) is not None]
    return {"title": " ".join(titleNode.text.split()), "authors": authors}


def surnameOf(fullName):
    """Last whitespace-separated token, which is the surname for every name in this corpus.

    ⚠️ Not true in general - it breaks on particles and on name orders this corpus does not
    contain. Stated rather than silently assumed, because a citation checker that is itself
    sloppy about names would be the wrong tool entirely.
    """
    return fullName.strip().split()[-1] if fullName.strip() else ""


def checkCoverage():
    """Every cited id must be registered. This is the guard that matters."""
    problems = []
    cited = citedIds()
    for arxivId, files in sorted(cited.items()):
        if arxivId in LEADS:
            continue
        if arxivId not in CITATIONS:
            where = ", ".join(sorted(files)[:3])
            problems.append(f"arXiv {arxivId} is cited ({where}) but NOT registered in "
                            f"CITATIONS or LEADS. Open the source, then register it.")
    for arxivId in sorted(CITATIONS):
        if arxivId not in cited:
            problems.append(f"arXiv {arxivId} is registered but no longer cited anywhere - "
                            f"remove it from CITATIONS, or find out who dropped the citation.")
    return problems, cited


def checkLive(arxivId, record):
    """Compare one registered citation against arXiv. Returns a list of problem strings."""
    live = fetchArxiv(arxivId)
    if live is None:
        return None
    problems = []
    if record["titleFragment"].lower() not in live["title"].lower():
        problems.append(f"arXiv {arxivId}: title fragment {record['titleFragment']!r} is not in "
                        f"arXiv's title {live['title']!r}")
    surnames = [surnameOf(a) for a in live["authors"]]
    if not surnames:
        problems.append(f"arXiv {arxivId}: arXiv returned no authors")
    elif surnames[0] != record["firstAuthor"]:
        problems.append(f"arXiv {arxivId}: registered first author {record['firstAuthor']!r} but "
                        f"arXiv lists {surnames[0]!r} first (full order: {', '.join(surnames)})")
    if len(live["authors"]) != record["authorCount"]:
        problems.append(f"arXiv {arxivId}: registered {record['authorCount']} authors, arXiv "
                        f"lists {len(live['authors'])}")
    return problems


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true",
                        help="Also fetch arXiv and compare. Needs network; skipped cleanly if "
                             "unavailable.")
    parser.add_argument("--check", action="store_true",
                        help="Exit non-zero if anything is wrong.")
    args = parser.parse_args()

    print("Citation check. A registered citation asserts someone OPENED the source.")
    print()

    problems, cited = checkCoverage()
    print(f"{len(cited)} arXiv id(s) cited across the repository's markdown, "
          f"{len(CITATIONS)} registered, {len(LEADS)} recorded as unread leads.")
    if COVERAGE_EXEMPT:
        print(f"  ({len(COVERAGE_EXEMPT)} search log(s) exempt from coverage - a log records what "
              f"was found, including sources later discarded.)")
    print()

    if args.live:
        print("Fetching arXiv metadata...")
        unreachable = []
        for arxivId in sorted(CITATIONS):
            liveProblems = checkLive(arxivId, CITATIONS[arxivId])
            if liveProblems is None:
                unreachable.append(arxivId)
                print(f"  [SKIP] {arxivId} - could not reach arXiv")
                continue
            if liveProblems:
                for problem in liveProblems:
                    print(f"  [DIFF] {problem}")
                problems.extend(liveProblems)
            else:
                print(f"  [ok]   {arxivId} - first author and title match arXiv")
        if unreachable:
            print(f"\n  {len(unreachable)} id(s) unreachable. THIS IS NOT A PASS for them.")
        print()

    if UNRESOLVED_DISCREPANCIES:
        print("OPEN DISCREPANCIES - recorded deliberately, and NOT resolved by editing one side "
              "to match the other:")
        for arxivId, text in sorted(UNRESOLVED_DISCREPANCIES.items()):
            print(f"  [OPEN] {arxivId}: {text}")
        print()

    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  [PROBLEM] {problem}")
        print()
        print("A citation problem is a FINDING. Fix the document or open the source - never "
              "adjust the registry to make this quiet.")
    else:
        print("No coverage problems. Every cited arXiv id is registered.")

    print()
    print("NOTE: this checks arXiv metadata only. It cannot tell you whether a paper SAYS what the "
          "text claims it says - only a person reading it can, and this project has been wrong "
          "about that four times.")

    if args.check and problems:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
