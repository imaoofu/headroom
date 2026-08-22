"""
Known-answer checks for the claim auditor.

WHY THESE
    audit_claims.py exists to catch documents drifting away from data. A checker that cannot
    fail is worse than no checker, because it converts "nobody verified this" into "this is
    verified" without changing anything. So the checks below are mostly about making it FAIL,
    in each of the ways it is supposed to.

    Two properties matter more than the rest and are easy to lose in a refactor:

      - A claim matching TWICE must not pass. The engine's whole guarantee is that a claim
        pins one specific line; if the rendered string appears in two places, editing the
        intended line still leaves the claim green against the other copy. AMBIGUOUS exists
        for that and is asserted here.
      - Coverage must credit only PASSING claims. Crediting a failing claim would report a
        number as pinned in the same run that just proved it is not in the document at all.

    Section extraction and the noise filter are checked because the coverage report is the
    only signal for what ISN'T audited, and a filter that silently eats real numbers makes
    the gap invisible - which is the failure this whole module exists to prevent.

PROVENANCE
    Written directly, not delegated. Eleven deliberate mutations were introduced into
    audit_claims.py. TWO SURVIVED the first pass, and both were weaknesses in the checks
    rather than in the code:

      - "coverage does NOT credit a failing claim" used a failing claim whose number was not
        in the section at all, so the number stayed unpinned whether or not failing claims
        were credited. Rewritten to use a claim that renders a number the section DOES
        contain, inside a sentence the document does not.
      - "a sweep CSV with no target column raises" asserted only that the claim came back
        ERROR. Without the guard the claim still errors, on a KeyError from the lookup rather
        than the ValueError from the loader, so the guard could be deleted with the suite
        green. Rewritten to call sweep() directly and name the exception.

    Both of those are the same mistake: asserting an outcome that the mutation also produces.
    After the rewrite all eleven are caught:

      - occurrences == 1 relaxed to >= 1                    (ambiguity check)
      - AMBIGUOUS reported as PASS                          (ambiguity check)
      - normalise() made an identity function               (bold checks)
      - normalise() applied to the document only            (bold checks)
      - normalise() also stripping single '*'               (over-normalisation check)
      - readDocument dropping newline=""                    (CRLF check)
      - coverage crediting every claim, not just PASSes     (coverage check)
      - extractSection stopping at any later heading        (nesting check)
      - extractSection including its own heading line       (heading-excluded check)
      - the NOISE date pattern removed                      (noise check)
      - sweep() no longer raising on a missing target column (schema check)

    Delete analysis/__pycache__ between mutations; a same-length edit can leave stale bytecode
    running while the source on disk reads correct.
"""

import shutil
import sys
import tempfile
from pathlib import Path

import audit_claims

failures = []


def check(description, condition, detail=""):
    if not condition:
        print(f"[FAIL] {description}")
        if detail:
            print(f"       {detail}")
        failures.append(description)
    else:
        print(f"[PASS] {description}")


# --------------------------------------------------------------------------------------
# A throwaway repository, so no check can touch the real documents or data
# --------------------------------------------------------------------------------------

SWEEP_HEADER = ("target_frequency_mhz,achieved_frequency_avg,lock_held,lock_miss_mhz,"
                "lock_miss_direction,power_avg_w,bench_throughput,bench_throughput_unit,"
                "bench_ok\r\n")

SWEEP_ROWS = (
    "1000,999.0,True,1.0,below,100.0,1000000000000,FLOP/s,True\r\n"
    "2000,1998.0,True,2.0,below,200.0,1800000000000,FLOP/s,True\r\n"
    # Overshoots its lock, so loadSweep must drop it and sweepRaw must keep it. This is the
    # run-7 shape: the cap was never applied and the card ran far above its target.
    "3000,4500.0,False,1500.0,above,300.0,2500000000000,FLOP/s,True\r\n"
)

DOCUMENT = (
    "# Title\r\n"
    "\r\n"
    "## 1 First section\r\n"
    "\r\n"
    "Power at the top point is 200.0 W, taken on 2026-08-21 and described in 5.7.3.\r\n"
    "The file is `run-3000.csv` and the gain is **+80.0%** over the low point.\r\n"
    "\r\n"
    "### 1.1 A nested subsection\r\n"
    "\r\n"
    "Nested text mentioning 42 belongs to section 1 as well as to 1.1.\r\n"
    "\r\n"
    "## 2 Second section\r\n"
    "\r\n"
    "This paragraph is outside section 1 and mentions 999 which must not be counted.\r\n"
    "\r\n"
    "Repeated line for the ambiguity check.\r\n"
    "Repeated line for the ambiguity check.\r\n"
)


def buildRepository():
    root = Path(tempfile.mkdtemp(prefix="audit-claims-test-"))
    sweeps = root / "data" / "frequency-sweeps" / "fake"
    sweeps.mkdir(parents=True)
    with open(sweeps / "run_sweep.csv", "w", newline="") as handle:
        handle.write(SWEEP_HEADER + SWEEP_ROWS)
    docs = root / "docs"
    docs.mkdir()
    with open(docs / "DOC.md", "w", newline="") as handle:
        handle.write(DOCUMENT)
    return root


def useRepository(root):
    """Point the engine at the throwaway repo and drop every cache.

    The caches are keyed by relative path, so without this a second case would read the first
    case's file contents from memory and pass for the wrong reason.
    """
    audit_claims.REPO_ROOT = root
    audit_claims._documentCache.clear()
    audit_claims._sweepCache.clear()


def makeClaim(render, claimId="test", document="docs/DOC.md", section=None):
    return {"claimId": claimId, "document": document, "section": section, "render": render}


def statusOf(render, **kwargs):
    return audit_claims.audit([makeClaim(render, **kwargs)])[0]["status"]


repository = buildRepository()
useRepository(repository)

SWEEP = "fake/run_sweep.csv"

# --------------------------------------------------------------------------------------
# The three outcomes
# --------------------------------------------------------------------------------------

check(
    "a rendering that appears exactly once passes",
    statusOf(lambda: "Power at the top point is 200.0 W") == "PASS",
)

check(
    "a rendering absent from the document fails",
    statusOf(lambda: "Power at the top point is 999.9 W") == "FAIL",
)

check(
    "a rendering that appears twice is AMBIGUOUS, not PASS",
    statusOf(lambda: "Repeated line for the ambiguity check.") == "AMBIGUOUS",
    "two matches mean the claim does not pin the line anyone thinks it pins",
)

check(
    "a render function that raises is reported as ERROR, not propagated",
    statusOf(lambda: 1 / 0) == "ERROR",
    "one broken claim must not abort the other 29",
)

check(
    "a missing document is an ERROR naming the file",
    audit_claims.audit([makeClaim(lambda: "x", document="docs/NOPE.md")])[0]["status"] == "ERROR",
)

# --------------------------------------------------------------------------------------
# Drift in each direction - the property the whole module is for
# --------------------------------------------------------------------------------------

def powerRender():
    return f"Power at the top point is {audit_claims.sweep(SWEEP)[2000]['power']:.1f} W"


check(
    "a claim rendered from the CSV matches the prose while they agree",
    statusOf(powerRender) == "PASS",
)

mutatedData = buildRepository()
with open(mutatedData / "data" / "frequency-sweeps" / "fake" / "run_sweep.csv",
          "w", newline="") as handle:
    handle.write(SWEEP_HEADER + SWEEP_ROWS.replace("2000,1998.0,True,2.0,below,200.0",
                                                   "2000,1998.0,True,2.0,below,222.0"))
useRepository(mutatedData)
check(
    "changing the DATA under unchanged prose fails the claim",
    statusOf(powerRender) == "FAIL",
    "the CSV now says 222.0 W and the document still says 200.0",
)

mutatedProse = buildRepository()
docPath = mutatedProse / "docs" / "DOC.md"
with open(docPath, "w", newline="") as handle:
    handle.write(DOCUMENT.replace("is 200.0 W", "is about 200 W"))
useRepository(mutatedProse)
check(
    "rewording the PROSE around an unchanged number fails the claim",
    statusOf(powerRender) == "FAIL",
    "an unpinnable number is the thing this module refuses to call verified",
)

useRepository(repository)

# --------------------------------------------------------------------------------------
# Normalisation: emphasis is presentation, everything else is content
# --------------------------------------------------------------------------------------

check(
    "a render without bold matches a document line that has it",
    statusOf(lambda: "the gain is +80.0% over the low point") == "PASS",
)

check(
    "a render WITH bold also matches, so claims may write it either way",
    statusOf(lambda: "the gain is **+80.0%** over the low point") == "PASS",
)

check(
    "normalisation does not strip single asterisks",
    audit_claims.normalise("*emphasis* and **strong**") == "*emphasis* and strong",
    "stripping single '*' would silently match italic text against plain",
)

# Whitespace is presentation for the same reason bold is: the documents are hard-wrapped, so a
# sentence breaks wherever the wrap falls. Without collapsing it a claim can only pin what fits
# on one line, and re-wrapping a paragraph - which changes nothing factual - would break every
# claim in it.
check(
    "a claim may span a line break in the document",
    statusOf(lambda: "described in 5.7.3. The file is `run-3000.csv`") == "PASS",
    "this text is split across two lines in the fixture; pinning it must still work",
)

check(
    "a claim may itself contain a newline where the document has a space, and vice versa",
    statusOf(lambda: "taken on 2026-08-21\nand described in 5.7.3.") == "PASS",
)

check(
    "a doubled space is tolerated",
    statusOf(lambda: "the  gain is +80.0% over the low point") == "PASS",
)

# The limit of the tolerance. Collapsing whitespace must not start matching text that differs
# in any character that is not whitespace, which is where every number lives.
check(
    "a changed digit still fails",
    statusOf(lambda: "the gain is +80.1% over the low point") == "FAIL",
)

check(
    "a missing word still fails",
    statusOf(lambda: "the gain is +80.0% over low point") == "FAIL",
    "collapsing whitespace must not collapse the words either",
)

check(
    "CRLF line endings survive the read, so multi-line renderings can match",
    "\r\n" in audit_claims.readDocument("docs/DOC.md"),
    "universal-newline translation would make every multi-line claim fail on Windows",
)

# --------------------------------------------------------------------------------------
# The loaders, and the excluded row in particular
# --------------------------------------------------------------------------------------

check(
    "sweep() drops the row whose lock overshot, reusing analyze_sweep's filter",
    sorted(audit_claims.sweep(SWEEP)) == [1000, 2000],
    f"got {sorted(audit_claims.sweep(SWEEP))}; the 3000 MHz row missed ABOVE",
)

check(
    "sweepRaw() keeps that row, so a claim can quote the failure",
    sorted(audit_claims.sweepRaw(SWEEP)) == [1000, 2000, 3000],
)

check(
    "sweepRaw() reports the miss direction and magnitude it was kept for",
    audit_claims.sweepRaw(SWEEP)[3000]["missDirection"] == "above"
    and audit_claims.sweepRaw(SWEEP)[3000]["missMhz"] == 1500.0,
)

noTargets = buildRepository()
with open(noTargets / "data" / "frequency-sweeps" / "fake" / "run_sweep.csv",
          "w", newline="") as handle:
    handle.write(SWEEP_HEADER.replace("target_frequency_mhz,", "")
                 + "".join(row.split(",", 1)[1] for row in SWEEP_ROWS.splitlines(True)))
useRepository(noTargets)

# Asserting only that the CLAIM errors is not enough: without the guard, sweep() returns
# {None: row} and the claim still errors, on a KeyError from the lookup instead. The check has
# to name the failure, or the guard can be deleted with the suite still green.
try:
    audit_claims.sweep(SWEEP)
    schemaFailure = "no exception"
except ValueError as error:
    schemaFailure = "ValueError" if "target_frequency_mhz" in str(error) else str(error)
except Exception as error:                            # noqa: BLE001 - reported below
    schemaFailure = type(error).__name__

check(
    "a sweep CSV with no target column raises ValueError rather than keying rows on None",
    schemaFailure == "ValueError",
    f"got {schemaFailure}; collapsing every row onto a single None key would corrupt "
    f"every claim built on that file",
)
useRepository(repository)

# --------------------------------------------------------------------------------------
# Formatting helpers
# --------------------------------------------------------------------------------------

check(
    "signedPct renders a gain with an explicit plus",
    audit_claims.signedPct(1.017) == "+1.7%",
    f"got {audit_claims.signedPct(1.017)!r}",
)

check(
    "signedPct renders a loss with ASCII minus by default",
    audit_claims.signedPct(0.819) == "-18.1%",
    f"got {audit_claims.signedPct(0.819)!r}",
)

check(
    "signedPct can render U+2212 for the documents that use it",
    audit_claims.signedPct(0.819, minus=chr(0x2212)) == chr(0x2212) + "18.1%",
    f"got {audit_claims.signedPct(0.819, minus=chr(0x2212))!r}",
)

check(
    "a positive value is untouched by the minus substitution",
    audit_claims.signedPct(1.017, minus=chr(0x2212)) == "+1.7%",
    "replacing '-' on a string with no '-' must not corrupt it",
)

# --------------------------------------------------------------------------------------
# Section extraction and the coverage report
# --------------------------------------------------------------------------------------

body = audit_claims.extractSection(audit_claims.readDocument("docs/DOC.md"), "1")

check(
    "extractSection excludes its own heading line",
    "First section" not in body,
)

check(
    "extractSection runs THROUGH a deeper nested heading",
    "42 belongs to section 1" in body,
    "stopping at any later heading would silently halve the audited region",
)

check(
    "extractSection stops at the next heading of the same level",
    "999 which must not be counted" not in body,
)

check(
    "an unknown section id returns None rather than the whole document",
    audit_claims.extractSection(audit_claims.readDocument("docs/DOC.md"), "9.9") is None,
)

numbers = audit_claims.numbersIn(body)

check(
    "the noise filter removes dates",
    "2026" not in numbers,
    f"got {numbers}",
)

check(
    "the noise filter removes section cross-references",
    "5" not in numbers and "7" not in numbers,
    f"got {numbers}; '5.7.3' must not become three unpinned numbers",
)

check(
    "the noise filter removes numbers inside code spans",
    "3000" not in numbers,
    f"got {numbers}; `run-3000.csv` is a filename, not a measurement",
)

check(
    "real measurements survive the noise filter",
    "200.0" in numbers and "+80.0%" in numbers,
    f"got {numbers}",
)

passing = audit_claims.audit([makeClaim(
    lambda: "Power at the top point is 200.0 W", section="1")])

# The rendering CONTAINS 200.0, which is genuinely in the section, but does not match the
# document because of the wrong unit. That combination is what makes the check bite: if
# coverage credited failing claims it would mark 200.0 as pinned on the strength of a claim
# the same run reported as FAIL. A failing claim whose numbers are absent from the section
# would leave 200.0 unpinned either way and prove nothing.
failing = audit_claims.audit([makeClaim(
    lambda: "Power at the top point is 200.0 kW", section="1")])

check(
    "coverage counts a passing claim's numbers as pinned",
    "200.0" not in audit_claims.coverage(passing)[0]["unpinned"],
)

check(
    "coverage does NOT credit a failing claim",
    failing[0]["status"] == "FAIL"
    and "200.0" in audit_claims.coverage(failing)[0]["unpinned"],
    "a claim that just failed has not pinned anything, by definition",
)

check(
    "coverage flags a claim pointing at a section that does not exist",
    audit_claims.coverage(audit_claims.audit([makeClaim(
        lambda: "Power at the top point is 200.0 W", section="9.9")]))[0]["missing"],
)

check(
    "unauditedSections lists a numbered heading no claim references",
    ("docs/DOC.md", "2 Second section") in audit_claims.unauditedSections(
        {"docs/DOC.md"}, passing),
)

check(
    "unauditedSections does not list a section that has a claim",
    ("docs/DOC.md", "1 First section") not in audit_claims.unauditedSections(
        {"docs/DOC.md"}, passing),
)

# --------------------------------------------------------------------------------------
# Non-ASCII claims must survive being reported
# --------------------------------------------------------------------------------------

# Section 5.4's table uses U+2212 MINUS SIGN and U+2014 EM DASH, so claims covering it MUST
# render them - matching the document byte for byte is the entire mechanism. Printing them raw
# raises UnicodeEncodeError on a cp1252 console, which is what a plain `python` gets on Windows,
# and that killed the whole report rather than the one line that could not be shown.
audit_claims.makeConsoleSafe()

check(
    "makeConsoleSafe leaves stdout able to encode a minus sign without raising",
    (lambda: (chr(0x2212).encode(sys.stdout.encoding or "utf-8", errors=sys.stdout.errors),
              True)[1])(),
    "a console that cannot show U+2212 must degrade to an escape, not take the run down",
)

nonAscii = audit_claims.audit([makeClaim(lambda: "value is " + chr(0x2212) + "18.1%")])[0]
check(
    "a claim rendering non-ASCII is compared, not rejected",
    nonAscii["status"] == "FAIL" and chr(0x2212) in nonAscii["expected"],
    f"got {nonAscii['status']}; the character must reach the comparison intact",
)

# --------------------------------------------------------------------------------------
# The registry
# --------------------------------------------------------------------------------------

registered = len(audit_claims.CLAIMS)


@audit_claims.claim("test-registration", "docs/DOC.md", "1")
def registeredClaim():
    return "Power at the top point is 200.0 W"


check(
    "the claim decorator registers exactly one claim and returns the function",
    len(audit_claims.CLAIMS) == registered + 1 and registeredClaim() is not None,
)

check(
    "the decorator records the id, document and section it was given",
    audit_claims.CLAIMS[-1]["claimId"] == "test-registration"
    and audit_claims.CLAIMS[-1]["section"] == "1",
)

for directory in (repository, mutatedData, mutatedProse, noTargets):
    shutil.rmtree(directory, ignore_errors=True)

if failures:
    print(f"{len(failures)} check(s) failed.")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")
