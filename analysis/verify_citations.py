"""Check this repository's arXiv and DOI citations against source metadata.

WHY THIS EXISTS
    This project has recorded FOUR wrong citations, and one of them was invented outright - a
    four-author list for its single most important source, two of whose names do not appear on
    the paper. Every one came from a plausible-sounding summary rather than from the record.
    None was caught by review; all were caught later, by accident.

    From 2026-09-17 a second AI assistant works alongside this one. A model that returns a
    confident citation is the exact failure mode above, industrialised. So citations stop being
    something a reader trusts and become something a script checks.

THE GUARD THAT MATTERS MOST IS NOT THE COMPARISON
    It is that EVERY arXiv id or DOI appearing in the repository's live markdown must be present
    in a citation or lead registry below. Add a citation without registering it and this fails.
    That is what makes an
    unverified citation from any contributor - human, me, or another model - impossible to land
    quietly. The comparison against live metadata is the second line, not the first.

    ⚠️ Registering an entry is an ASSERTION THAT SOMEONE OPENED THE SOURCE. It is not a formality
    and it is not something to do in bulk to make this pass. `docs/RELATED-WORK.md` carries read
    status for the same reason.

WHY curl AND NOT urllib
    arXiv's API returns 406 to Python's urllib from this environment and 200 to curl. Verified
    both ways 2026-09-17 rather than assumed. curl ships with Windows 10+ and every CI image
    this project uses.

DOI METADATA
    --live fetches CSL JSON from https://doi.org/<doi> using Crossref's documented Accept header.
    A DOI registry entry asserts that its bibliographic metadata was opened; readStatus states
    whether the paper itself was read. Metadata cannot verify a paper's scientific claims.

Usage:
    python analysis/verify_citations.py            # offline: registry coverage only
    python analysis/verify_citations.py --live     # also fetch arXiv and DOI metadata
    python analysis/verify_citations.py --check    # exit non-zero if anything is wrong
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
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
        "note": "RESOLVED 2026-09-18, and the REPOSITORY WAS RIGHT. arXiv's preprint metadata "
                "leads with Mei and omits 'Non-Preemptive'; the published IEEE TPDS version leads "
                "with Qiang Wang and includes it. DOI 10.1109/TPDS.2022.3181096, TPDS 33(12) "
                "4083-4099, 2022 - verified against publisher-deposited Crossref metadata. "
                "'Wang et al.' throughout the paper is correct. firstAuthor below is arXiv's, "
                "because that is what --live compares against.",
        "publishedAs": "Qiang Wang, Xinxin Mei, Hai Liu, Yiu-Wing Leung, Zongpeng Li, Xiaowen Chu; "
                       "'Energy-Aware Non-Preemptive Task Scheduling With Deadline Constraint in "
                       "DVFS-Enabled Heterogeneous Clusters'; IEEE TPDS 33(12):4083-4099, 2022; "
                       "doi:10.1109/TPDS.2022.3181096",
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

# DOI -> publisher-deposited CSL metadata checked through doi.org on 2026-09-22.
# The five DOIs from RELATED-WORK.md sections 8-9 are included here. Other live citations are
# registered too, because the offline coverage guard must not let a new DOI slip in silently.
# This registry verifies bibliographic identity, not the paper's claims. readStatus is the
# repository's own documented access level, not an inference from the Crossref record.
DOI_CITATIONS = {
    "10.1016/j.future.2023.07.011": {
        "title": "An automated and portable method for selecting an optimal GPU frequency",
        "authors": ("Ali", "Side", "Bhalachandra", "Wright", "Chen"),
        "readStatus": "cited in GPT finding; metadata checked",
    },
    "10.1016/j.jpdc.2022.03.004": {
        "title": "Decoupling GPGPU voltage-frequency scaling for deep-learning applications",
        "authors": ("Mendes", "Tomás", "Roma"),
        "readStatus": "full text read, RELATED-WORK section 8",
    },
    "10.1109/hpca.2018.00072": {
        "title": "GPGPU Power Modeling for Multi-domain Voltage-Frequency Scaling",
        "authors": ("Guerreiro", "Ilic", "Roma", "Tomas"),
        "readStatus": "full text read, RELATED-WORK section 8",
    },
    "10.1109/pmbs56514.2022.00010": {
        "title": "Going green: optimizing GPUs for energy efficiency through model-steered auto-tuning",
        "authors": ("Schoonhoven", "Veenboer", "Van Werkhoven", "Batenburg"),
        # Tightened at review: what was read in full is the arXiv preprint 2211.07260, not
        # this published version - the same distinction the TPDS 2022 entry already makes.
        "readStatus": "published metadata checked; arXiv 2211.07260 text read in full",
    },
    "10.1109/tpds.2019.2917181": {
        "title": "Modeling and Decoupling the GPU Power Consumption for Cross-Domain DVFS",
        "authors": ("Guerreiro", "Ilic", "Roma", "Tomas"),
        "readStatus": "full text read, RELATED-WORK section 8",
    },
    "10.1109/tpds.2020.3004623": {
        "title": "GPGPU Performance Estimation With Core and Memory Frequency Scaling",
        "authors": ("Wang", "Chu"),
        "readStatus": "cited in GPT finding; metadata checked",
    },
    "10.1109/tpds.2022.3181096": {
        "title": "Energy-Aware Non-Preemptive Task Scheduling With Deadline Constraint in DVFS-Enabled Heterogeneous Clusters",
        "authors": ("Wang", "Mei", "Liu", "Leung", "Li", "Chu"),
        "readStatus": "published metadata checked; arXiv text read",
    },
    "10.1109/tsusc.2023.3314916": {
        "title": "Model-Free GPU Online Energy Optimization",
        "authors": ("Wang", "Hao", "Zhang", "Wang"),
        "readStatus": "abstract only, RELATED-WORK section 9",
    },
    "10.1145/3307772.3328315": {
        "title": "The Impact of GPU DVFS on the Energy and Performance of Deep Learning",
        "authors": ("Tang", "Wang", "Wang", "Chu"),
        "readStatus": "full text read in repository related work",
    },
    "10.1145/3337821.3337833": {
        "title": "Predictable GPUs Frequency Scaling for Energy and Performance",
        "authors": ("Fan", "Cosenza", "Juurlink"),
        "readStatus": "full text read in repository related work",
    },
    "10.1145/3370748.3406553": {
        "title": "SAOU",
        "authors": ("Zamani", "Tripathy", "Bhuyan", "Chen"),
        "readStatus": "full text read in repository related work",
    },
    "10.1145/3583590": {
        "title": "GreenMD: Energy-efficient Matrix Decomposition on Heterogeneous Multi-GPU Systems",
        "authors": ("Zamani", "Bhuyan", "Chen", "Chen"),
        "readStatus": "abstract only, RELATED-WORK section 9",
    },
    "10.1145/3627703.3629584": {
        "title": "Improving GPU Energy Efficiency through an Application-transparent Frequency Scaling Policy with Performance Assurance",
        "authors": ("Zhang", "Wang", "Lin", "Xu", "Wang"),
        "readStatus": "full text read in repository related work",
    },
}

DOI_LEADS = {
    "10.1145/3605573.3605600": "PAPER_DRAFT says its figures could not be confirmed and omits them. "
                              "Keep this as an unread lead, not a verified citation.",
}

# ✅ THE ONE DISCREPANCY THIS CHECKER FOUND, AND HOW IT RESOLVED.
#
# For 2104.00486 the repository recorded "Wang, Mei, Liu, Leung, Li, Chu" and a title containing
# "Non-Preemptive". arXiv's metadata leads with Mei and has no "Non-Preemptive". Flagged here on
# 2026-09-17 as UNRESOLVED, with the instruction to open the published version rather than edit
# either side to match the other.
#
# 🔑 RESOLVED 2026-09-18: THE REPOSITORY WAS RIGHT AND arXiv WAS THE MISLEADING RECORD.
# The published IEEE TPDS version is Qiang Wang, Xinxin Mei, Hai Liu, Yiu-Wing Leung, Zongpeng Li,
# Xiaowen Chu - "Energy-Aware Non-Preemptive Task Scheduling With Deadline Constraint in
# DVFS-Enabled Heterogeneous Clusters", TPDS 33(12):4083-4099, 2022, doi:10.1109/TPDS.2022.3181096.
# Confirmed against publisher-deposited Crossref metadata, independently of the arXiv record.
#
# 🔑 THE LESSON IS THE ONE THE FLAG WAS WRITTEN ON: a preprint's author order and title are NOT
# authoritative for the journal version, and a journal version legitimately changes both. Had the
# rule been "make the registry match arXiv", this check would have INTRODUCED the project's fifth
# citation error while appearing to remove one.
#
# ⚠️ So the live comparison below still expects arXiv's "Mei", because that is genuinely what
# arXiv says. The `publishedAs` field carries what the paper should be cited as. They differ on
# purpose, and any future reader who tries to "fix" the mismatch should read this block first.
RESOLVED_DISCREPANCIES = {
    "2104.00486": "Repository was correct. Published TPDS leads with Qiang Wang and includes "
                  "'Non-Preemptive'; the arXiv preprint differs on both. Resolved 2026-09-18 "
                  "against doi:10.1109/TPDS.2022.3181096.",
}

UNRESOLVED_DISCREPANCIES = {}

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
DOI_ID = re.compile(r"10\.\d{4,9}/[^\s<>()\[\]{}\"'`]+", re.IGNORECASE)


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


def citedDois():
    """DOIs in live markdown, with duplicates and terminal punctuation removed."""
    found = {}
    for path in markdownFiles():
        rel = path.relative_to(REPO_ROOT).as_posix()
        if rel in COVERAGE_EXEMPT:
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for match in DOI_ID.finditer(content):
            doi = match.group().rstrip(".,;:!?").lower()
            found.setdefault(doi, set()).add(rel)
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


def fetchDoi(doi, timeoutSeconds=25):
    """CSL JSON through doi.org, or None when metadata cannot be fetched.

    Network failures are not citation defects; --check never calls this function.
    """
    try:
        result = subprocess.run(
            ["curl", "-fsSL", "-m", str(timeoutSeconds), "-A", "headroom-citation-check/1.0",
             "-H", "Accept: application/vnd.citationstyles.csl+json",
             f"https://doi.org/{doi}"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=timeoutSeconds + 10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode != 0 or not result.stdout.strip():
        return None
    try:
        record = json.loads(result.stdout)
    except (ValueError, TypeError):
        return None
    if (not isinstance(record, dict) or not isinstance(record.get("title"), str)
            or not isinstance(record.get("author"), list)):
        return None
    return record


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


def checkDoiCoverage():
    """Every live DOI citation must have opened metadata or be a declared lead."""
    problems = []
    cited = citedDois()
    for doi, files in sorted(cited.items()):
        if doi in DOI_LEADS:
            continue
        if doi not in DOI_CITATIONS:
            where = ", ".join(sorted(files)[:3])
            problems.append(f"DOI {doi} is cited ({where}) but NOT registered in "
                            "DOI_CITATIONS or DOI_LEADS. Open its metadata, then register it.")
    for doi in sorted(DOI_CITATIONS):
        if doi not in cited:
            problems.append(f"DOI {doi} is registered but no longer cited anywhere - "
                            "remove it from DOI_CITATIONS, or find out who dropped the citation.")
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


def normalizedMetadata(text):
    """Compare wording without capitalization, accents, or punctuation-only changes."""
    plain = "".join(char for char in unicodedata.normalize("NFKD", text)
                    if not unicodedata.combining(char)).casefold()
    return " ".join(re.findall(r"\w+", plain))


def checkLiveDoi(doi, record):
    """Compare a DOI's registered title and complete author order with CSL JSON."""
    live = fetchDoi(doi)
    if live is None:
        return None
    problems = []
    if str(live.get("DOI", "")).lower() != doi.lower():
        problems.append(f"DOI {doi}: resolver returned DOI {live.get('DOI')!r}")
    if normalizedMetadata(record["title"]) != normalizedMetadata(live["title"]):
        problems.append(f"DOI {doi}: registered title {record['title']!r} differs from "
                        f"Crossref title {live['title']!r}")
    authors = [author.get("family", "") for author in live["author"]
               if isinstance(author, dict)]
    if [normalizedMetadata(a) for a in record["authors"]] != [normalizedMetadata(a)
                                                               for a in authors]:
        problems.append(f"DOI {doi}: registered author order {record['authors']!r} differs from "
                        f"Crossref author order {tuple(authors)!r}")
    return problems


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--live", action="store_true",
                        help="Also fetch arXiv and DOI metadata. Needs network; skipped cleanly if "
                             "unavailable.")
    parser.add_argument("--check", action="store_true",
                        help="Exit non-zero if anything is wrong.")
    args = parser.parse_args(argv)

    print("Citation check. Each registry states its source-read status; DOI metadata alone "
          "does not verify a paper's claims.")
    print()

    problems, cited = checkCoverage()
    doiProblems, citedDoisByFile = checkDoiCoverage()
    problems.extend(doiProblems)
    print(f"{len(cited)} arXiv id(s) cited across the repository's markdown, "
          f"{len(CITATIONS)} registered, {len(LEADS)} recorded as unread leads.")
    print(f"{len(citedDoisByFile)} DOI(s) cited across live markdown, "
          f"{len(DOI_CITATIONS)} registered, {len(DOI_LEADS)} recorded as unread leads.")
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

        print("Fetching DOI CSL metadata through doi.org...")
        unreachableDois = []
        for doi in sorted(DOI_CITATIONS):
            liveProblems = checkLiveDoi(doi, DOI_CITATIONS[doi])
            if liveProblems is None:
                unreachableDois.append(doi)
                print(f"  [SKIP] {doi} - could not fetch DOI metadata")
                continue
            if liveProblems:
                for problem in liveProblems:
                    print(f"  [DIFF] {problem}")
                problems.extend(liveProblems)
            else:
                print(f"  [ok]   {doi} - title and complete author order match DOI metadata")
        if unreachableDois:
            print(f"\n  {len(unreachableDois)} DOI(s) unreachable. THIS IS NOT A PASS for them.")
        print()

    if UNRESOLVED_DISCREPANCIES:
        print("OPEN DISCREPANCIES - recorded deliberately, and NOT resolved by editing one side "
              "to match the other:")
        for arxivId, text in sorted(UNRESOLVED_DISCREPANCIES.items()):
            print(f"  [OPEN] {arxivId}: {text}")
        print()
    if RESOLVED_DISCREPANCIES:
        print("RESOLVED discrepancies - kept, because how one resolved is the useful part:")
        for arxivId, text in sorted(RESOLVED_DISCREPANCIES.items()):
            print(f"  [RESOLVED] {arxivId}: {text}")
        print()

    if problems:
        print(f"{len(problems)} problem(s):")
        for problem in problems:
            print(f"  [PROBLEM] {problem}")
        print()
        print("A citation problem is a FINDING. Fix the document or open the source - never "
              "adjust the registry to make this quiet.")
    else:
        print("No coverage problems. Every cited arXiv id and DOI is registered or a lead.")

    print()
    print("NOTE: metadata checks cannot tell you whether a paper SAYS what the text claims it "
          "says - only a person reading it can, and this project has been wrong about that "
          "four times.")

    if args.check and problems:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
