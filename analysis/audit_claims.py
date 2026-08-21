"""
Check that the numbers written in the prose still match the numbers in the CSVs.

WHY THIS EXISTS
    docs/PAPER_DRAFT.md is ~11,000 words citing eight frequency sweeps, and the data READMEs
    and ROADMAP.md restate many of the same figures. Nothing connected a sentence to the file
    it came from, so the failure mode was silent: a number could be mis-derived once and then
    copied forward, or a re-run could replace the data under a paragraph that still described
    the old result. Both happened.

      - "173% of theoretical peak" survived into a README because a probe sampled the memory
        clock at its idle P-state. Caught by noticing, not by any check.
      - A sweep was labelled `memonly` while the tuned profile was applied. Caught because the
        operator remembered, mid-run.
      - The gemm re-run under the repaired curve landed in a commit message and the roadmap,
        and the paper went on saying "the expected cost has not been measured" for a day.
      - The roadmap's "5-18% across 2317-2782 MHz" was computed from a run whose 1852 MHz row
        had overshot its lock by +1002.6 MHz. The real figure is up to 33.1% across
        1545-2782 MHz - a wider band and roughly double the effect.

    Every one of those is a claim that disagreed with the committed data. That is a mechanical
    property, so it should be checked mechanically.

HOW A CLAIM WORKS, AND WHY IT IS SHAPED THIS WAY
    A claim does NOT store an expected number. It stores a function that RENDERS the exact
    string the document should contain, computed from the CSVs at audit time, and the engine
    asserts that string appears in the document verbatim and exactly once.

    That single mechanism closes both directions of drift:

      - change the data (or fix a loader bug) and the rendered string no longer matches the
        prose, so the claim fails;
      - edit the prose and the prose no longer contains the rendered string, so the claim
        fails.

    Storing an expected value instead would only catch the first, and would need the value
    maintained in two places - which is the bookkeeping problem one level down.

    The consequence to understand before adding claims: THE RENDERED STRING IS THE
    SPECIFICATION. If a claim renders "+1.7%" the document must say "+1.7%", not "+1.70%" or
    "about 1.7%". That is deliberate. Prose that cannot be pinned to an exact rendering is
    prose whose number nobody can check.

WHAT THIS DOES NOT DO
    It does not verify anything no claim covers, and a green run is not a statement that the
    document is correct. The coverage report exists so that gap is visible rather than
    assumed: for every section that has at least one claim, it lists the numeric tokens NO
    claim pins. Sections with no claims at all are listed as unaudited.

USAGE
    python analysis/audit_claims.py
    python analysis/audit_claims.py --coverage      # also list unpinned numbers
    python analysis/audit_claims.py --filter 5.7.5
"""

import argparse
import csv
import re
import sys
from pathlib import Path

from analyze_sweep import loadSweep

REPO_ROOT = Path(__file__).resolve().parent.parent

# Claims register themselves here at import time. Kept module-level rather than passed around
# so a claims module is a flat list of decorated functions with no wiring.
CLAIMS = []

_documentCache = {}
_sweepCache = {}


def claim(claimId, document, section=None):
    """Register a function whose return value is the exact text the document must contain."""
    def register(render):
        CLAIMS.append({
            "claimId": claimId,
            "document": document,
            "section": section,
            "render": render,
        })
        return render
    return register


def readDocument(relativePath):
    if relativePath not in _documentCache:
        path = REPO_ROOT / relativePath
        if not path.exists():
            raise FileNotFoundError(f"audited document missing: {relativePath}")
        # newline="" so the file's own line endings survive. Every document here is CRLF, and
        # universal-newline translation would rewrite them to LF on read, so a claim rendering
        # a multi-line table would match text that is not what is on disk.
        # open(..., newline="") rather than Path.read_text(newline=""): read_text only grew a
        # newline argument in 3.13, and this repo runs 3.12.
        with open(path, encoding="utf-8", newline="") as handle:
            _documentCache[relativePath] = handle.read()
    return _documentCache[relativePath]


def sweep(relativePath):
    """Load a sweep CSV keyed by COMMANDED frequency, reusing analyze_sweep's row filter.

    Rows whose lock missed in the ABOVE direction are dropped by loadSweep, which is the
    behaviour this audit wants and the reason it is imported rather than reimplemented: the
    curvefixed gemm run has a row that overshot 1852 MHz by +1002.6 MHz, and an audit that
    silently included it would reproduce the exact class of error it exists to catch.
    """
    if relativePath not in _sweepCache:
        path = REPO_ROOT / "data" / "frequency-sweeps" / relativePath
        if not path.exists():
            raise FileNotFoundError(f"sweep CSV missing: {relativePath}")
        byTarget = {}
        for row in loadSweep(path):
            if row["target"] is None:
                raise ValueError(f"{relativePath} has no target_frequency_mhz column")
            byTarget[row["target"]] = row
        if not byTarget:
            raise ValueError(f"{relativePath} yielded no usable rows")
        _sweepCache[relativePath] = byTarget
    return _sweepCache[relativePath]


def sweepRaw(relativePath):
    """Every row of a sweep CSV, including ones loadSweep drops.

    Needed because some claims are ABOUT the excluded rows - the paper documents a run whose
    1852 MHz point overshot its lock by +1002.6 MHz, and that number cannot be checked against
    a loader whose whole job is to remove it. Use sweep() for anything analytical; this is for
    quoting a failure.
    """
    key = ("raw", relativePath)
    if key not in _sweepCache:
        path = REPO_ROOT / "data" / "frequency-sweeps" / relativePath
        if not path.exists():
            raise FileNotFoundError(f"sweep CSV missing: {relativePath}")
        rows = {}
        with open(path, encoding="utf-8-sig") as handle:
            for raw in csv.DictReader(handle):
                rows[int(float(raw["target_frequency_mhz"]))] = {
                    "target": int(float(raw["target_frequency_mhz"])),
                    "mhz": float(raw["achieved_frequency_avg"]),
                    "power": float(raw["power_avg_w"]),
                    "throughput": float(raw["bench_throughput"]),
                    "lockHeld": raw.get("lock_held") in ("True", "true"),
                    "missMhz": float(raw["lock_miss_mhz"]) if raw.get("lock_miss_mhz") else 0.0,
                    "missDirection": raw.get("lock_miss_direction", ""),
                }
        _sweepCache[key] = rows
    return _sweepCache[key]


def voltageJoin(relativePath):
    """Load a *_voltage.csv produced by tools/frequency-sweep/join_hwinfo_voltage.py.

    Separate from sweep() because these are a different artifact with a different schema: they
    carry HWiNFO's core voltage and crossbar clock, which NVML does not expose at all, and they
    exist only for the runs where HWiNFO happened to be logging.
    """
    key = ("voltage", relativePath)
    if key not in _sweepCache:
        path = REPO_ROOT / "data" / "frequency-sweeps" / relativePath
        if not path.exists():
            raise FileNotFoundError(f"voltage join missing: {relativePath}")
        rows = {}
        with open(path, encoding="utf-8-sig") as handle:
            for raw in csv.DictReader(handle):
                rows[int(float(raw["target"]))] = {
                    "target": int(float(raw["target"])),
                    "mhz": float(raw["achieved"]),
                    "voltage": float(raw["voltage"]),
                    "crossbar": float(raw["crossbar"]),
                }
        if not rows:
            raise ValueError(f"{relativePath} yielded no rows")
        _sweepCache[key] = rows
    return _sweepCache[key]


def signedPct(ratio, minus="-"):
    """Format a ratio-minus-one as a signed percentage, e.g. 1.017 -> '+1.7%'.

    `minus` exists because the documents disagree: code and the paper's 5.7 tables use ASCII
    '-', while the data READMEs and ROADMAP use U+2212. A claim renders whatever its own
    document actually uses; it is not this function's job to decide which is right.
    """
    value = (ratio - 1.0) * 100.0
    text = f"{value:+.1f}%"
    return text.replace("-", minus) if minus != "-" else text


def deltaPct(new, old, minus="-"):
    return signedPct(new / old, minus=minus)


BOLD = re.compile(r"\*\*")


def normalise(text):
    """Strip bold markers before matching.

    Which numbers a section puts in bold is an editorial decision that changes as the prose is
    edited, and it is not a factual claim about the data. Without this, moving emphasis from
    one row of a table to another breaks a claim that is still perfectly true - and the fix
    would be to teach the claim WHICH rows deserve bold, putting an editorial judgement inside
    the checker. Both sides are normalised, so a claim may render the markers or not.

    The cost: a claim cannot pin emphasis. That is the intended trade.
    """
    return BOLD.sub("", text)


def audit(claims):
    results = []
    for entry in claims:
        try:
            expected = normalise(entry["render"]())
            text = normalise(readDocument(entry["document"]))
            occurrences = text.count(expected)
        except Exception as error:                    # noqa: BLE001 - reported, not raised
            results.append({**entry, "status": "ERROR", "expected": None,
                            "detail": f"{type(error).__name__}: {error}"})
            continue

        if occurrences == 1:
            status, detail = "PASS", expected
        elif occurrences == 0:
            status = "FAIL"
            detail = f"document does not contain: {expected!r}"
        else:
            # More than one match means the claim is not pinning the line anyone thinks it is,
            # so a change to the intended line would still pass against the other copy.
            status = "AMBIGUOUS"
            detail = f"{occurrences} occurrences of {expected!r}; anchor is not unique"
        results.append({**entry, "status": status, "expected": expected, "detail": detail})
    return results


# --------------------------------------------------------------------------------------
# Coverage
# --------------------------------------------------------------------------------------

HEADING = re.compile(r"^(#{1,6})\s+(.*)$", re.MULTILINE)

# Stripped before numbers are extracted, because these are not measurements and counting them
# as unpinned would bury the real gaps in noise.
NOISE = [
    re.compile(r"`[^`]*`"),                        # inline code, including file names
    re.compile(r"\[[^\]]*\]\([^)]*\)"),            # markdown links
    re.compile(r"\d{4}-\d{2}-\d{2}"),              # dates
    re.compile(r"\b\d+\.\d+(?:\.\d+)+\b"),         # section cross-references, e.g. 5.7.3
    re.compile(r"\(\d+\.\d+\)"),                   # parenthesised section refs, e.g. "(5.6)"
]

NUMBER = re.compile("[+\\-\u2212]?\\d+(?:\\.\\d+)?%?")


def extractSection(text, sectionId):
    """Return the body under the heading whose title starts with sectionId, heading excluded."""
    matches = list(HEADING.finditer(text))
    for index, match in enumerate(matches):
        title = match.group(2).strip()
        if not title.startswith(sectionId):
            continue
        level = len(match.group(1))
        start = match.end()
        for later in matches[index + 1:]:
            if len(later.group(1)) <= level:
                return text[start:later.start()]
        return text[start:]
    return None


def numbersIn(text):
    stripped = text
    for pattern in NOISE:
        stripped = pattern.sub(" ", stripped)
    return NUMBER.findall(stripped)


def coverage(results):
    """For each audited section, the numeric tokens no passing claim pins."""
    bySection = {}
    for entry in results:
        if not entry["section"]:
            continue
        bySection.setdefault((entry["document"], entry["section"]), []).append(entry)

    report = []
    for (document, sectionId), entries in sorted(bySection.items()):
        body = extractSection(readDocument(document), sectionId)
        if body is None:
            report.append({"document": document, "section": sectionId,
                           "missing": True, "unpinned": [], "total": 0})
            continue
        # Only PASSING claims count as pinning anything. A failing claim's rendered string is
        # by definition not in the document, so crediting it would report coverage the audit
        # has just finished disproving.
        pinned = " ".join(e["expected"] for e in entries
                          if e["status"] == "PASS" and e["expected"])
        pinnedNumbers = set(numbersIn(pinned))
        found = numbersIn(body)
        unpinned = [n for n in found if n not in pinnedNumbers]
        report.append({"document": document, "section": sectionId, "missing": False,
                       "unpinned": unpinned, "total": len(found)})
    return report


def unauditedSections(documents, results):
    """Numbered headings in the audited documents that no claim references at all."""
    audited = {(e["document"], e["section"]) for e in results if e["section"]}
    out = []
    for document in sorted(documents):
        for match in HEADING.finditer(readDocument(document)):
            title = match.group(2).strip()
            sectionId = title.split()[0] if title else ""
            if not re.match(r"^\d+(\.\d+)*$", sectionId):
                continue
            if (document, sectionId) not in audited:
                out.append((document, title))
    return out


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--filter", default="",
                        help="Only run claims whose id contains this substring.")
    parser.add_argument("--coverage", action="store_true",
                        help="Also list numbers in audited sections that no claim pins.")
    args = parser.parse_args()

    import claims_consumer                             # noqa: F401 - registers claims

    selected = [c for c in CLAIMS if args.filter in c["claimId"]]
    if not selected:
        print(f"No claims match --filter {args.filter!r}. {len(CLAIMS)} registered.")
        return 1

    results = audit(selected)
    width = max(len(r["claimId"]) for r in results)
    for result in results:
        print(f"[{result['status']:>9}] {result['claimId']:<{width}}  {result['detail']}")

    bad = [r for r in results if r["status"] != "PASS"]
    print(f"\n{len(results) - len(bad)} of {len(results)} claims verified against the CSVs.")

    if args.coverage:
        print("\n--- coverage: numbers in audited sections that NO claim pins ---")
        for entry in coverage(results):
            where = f"{entry['document']} {entry['section']}"
            if entry["missing"]:
                print(f"  {where}: SECTION NOT FOUND")
                continue
            pinned = entry["total"] - len(entry["unpinned"])
            print(f"  {where}: {pinned}/{entry['total']} pinned")
            if entry["unpinned"]:
                print(f"      unpinned: {' '.join(entry['unpinned'])}")
        stray = unauditedSections({c["document"] for c in selected}, results)
        if stray:
            print(f"\n  {len(stray)} numbered section(s) in audited documents have NO claims:")
            for document, title in stray:
                print(f"      {document}: {title}")

    if bad:
        print(f"\n{len(bad)} claim(s) did not verify.")
        return 1
    return 0


if __name__ == "__main__":
    # Running this file directly binds it as `__main__`. A claims module then does
    # `from audit_claims import claim`, which imports a SECOND copy of this file under its real
    # name, and every claim registers into THAT copy's CLAIMS list - leaving the one `main()`
    # can see permanently empty. The symptom is "0 registered" with the claims file plainly
    # sitting next to it.
    #
    # Re-dispatching through the named module makes the two copies agree on which registry is
    # real. Do not "simplify" this back to sys.exit(main()).
    from audit_claims import main as entryPoint

    sys.exit(entryPoint())
