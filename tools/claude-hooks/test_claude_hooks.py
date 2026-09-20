"""
Known-answer checks for the Claude Code hooks.

WHY THESE NEED TESTS
    A guard nobody exercises is a guard nobody can trust, and this one fails in two opposite
    directions that both look fine on inspection:

      - too permissive, and a measurement CSV gets edited and then VERIFIED by the claims
        auditor, because the auditor renders its expected string from the file it is checking;
      - too strict, and it blocks the READMEs and session run sheets that live inside
        data/frequency-sweeps/, at which point the operator turns the hook off and it protects
        nothing at all.

    The second failure is the likelier one and it has no error message, so it is tested first.

Run: python tools/claude-hooks/test_claude_hooks.py
"""

import io
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from guard_measurement_files import editedPath, verdict  # noqa: E402
from post_edit_gate import shouldRun  # noqa: E402

failures = []


def check(description, condition, detail=""):
    if not condition:
        print(f"[FAIL] {description}")
        if detail:
            print(f"  Detail: {detail}")
        failures.append(description)
    else:
        print(f"[PASS] {description}")


# ⛔ THIS WAS A HARDCODED `C:\Users\Raymond\Documents\headroom` UNTIL 2026-09-20, AND IT FAILED
# CI ON BOTH LEGS. `post_edit_gate.shouldRun()` compares against the REAL repository root at
# runtime, so on a runner rooted at /home/runner/work/headroom/headroom a path under C:\Users\...
# is correctly judged "outside the repository" and the check failed. The code was right.
#
# 🔑 The test passed on the machine it was written on and could only ever pass there - which is
# the hardest kind of wrong to see, because a green local run looks like evidence.
REPO = str(Path(__file__).resolve().parents[2])

# ✅ The verdict() cases below deliberately keep WINDOWS backslashes even on a Linux runner. That
# is not an oversight: the hook runs on Windows and receives backslashed absolute paths, so
# handling them is the behaviour under test. verdict() matches on a substring, so any prefix
# reaches the same answer - which is exactly why those cases were NOT what broke.

# The guard against that mistake returning: if REPO is not the repository root, every path below
# is fictional and the suite is asserting about nothing.
check("REPO resolves to the actual repository root",
      (Path(REPO) / "CLAUDE.md").exists() and (Path(REPO) / "run_tests.py").exists(),
      f"got {REPO!r}")


def inRepo(*parts):
    """A real path inside this checkout, with the platform's own separator."""
    return str(Path(REPO).joinpath(*parts))

# Test 1: the things that MUST stay editable. These come first because a guard that blocks them
# gets switched off, and a switched-off guard is the worst outcome available here.
allowed = [
    (f"{REPO}\\data\\frequency-sweeps\\README.md", "a data directory README"),
    (f"{REPO}\\data\\frequency-sweeps\\rtx3070ti-20260825\\SESSION-D-RUNSHEET.md",
     "a session run sheet living inside a protected directory"),
    (f"{REPO}\\data\\HWiNFO-Data\\README.md", "the HWiNFO README that .gitignore re-includes"),
    (f"{REPO}\\docs\\PAPER_DRAFT.md", "the paper"),
    (f"{REPO}\\analysis\\claims_consumer.py", "a claims module"),
    (f"{REPO}\\data\\frequency-sweeps\\5060ti-finefloor-20260918\\README.md",
     "a sweep directory README"),
]
for path, what in allowed:
    check(f"allows {what}", verdict(path) is None, f"got {verdict(path)!r}")

# Test 2: the measurements themselves.
blocked = [
    (f"{REPO}\\data\\frequency-sweeps\\20260918-202543_5060ti-finefloor-gemm-r2_sweep.csv",
     "a sweep CSV"),
    (f"{REPO}\\data\\frequency-sweeps\\abba-20260908\\x_sweep.json", "a sweep JSON"),
    (f"{REPO}\\data\\stability-runs\\20260823-183256_splitcurve_samples.csv",
     "a stability sample log"),
    (f"{REPO}\\data\\probes\\something.json", "a kernel-probe result"),
    (f"{REPO}\\data\\afterburner-profiles\\5060ti-profiles-20260918\\Profile4.cfg",
     "a verbatim Afterburner profile snapshot"),
    (f"{REPO}\\data\\MANIFEST.json", "the generated data manifest"),
    (f"{REPO}\\data\\stability-runs\\20260823-183256_splitcurve_stability_logger-stderr.txt",
     "a logger stderr record, which a list of protected EXTENSIONS would have missed"),
    (f"{REPO}\\data\\frequency-sweeps\\something_we_have_not_invented_yet.parquet",
     "a file type no tool writes yet, because the rule is default-deny"),
]
for path, what in blocked:
    check(f"blocks {what}", verdict(path) is not None)

# The markdown allowance has to be LOAD-BEARING, not decorative. A mutation run on 2026-09-20
# found the first version of it was unreachable: a README failed the positive suffix test one
# line earlier and was allowed for the wrong reason, so deleting the allowance changed nothing
# and the suite still passed. These two lines differ only in extension.
check("the markdown allowance is what saves a README inside a measurement directory",
      verdict(f"{REPO}\\data\\frequency-sweeps\\abba-20260908\\README.md") is None
      and verdict(f"{REPO}\\data\\frequency-sweeps\\abba-20260908\\README.csv") is not None)

# Test 3: the refusal has to say WHY, or the next session works around it. Every tool in this
# repo states its own limitations in its own output; a guard is no different.
reason = verdict(f"{REPO}\\data\\frequency-sweeps\\x_sweep.csv")
check("the sweep refusal explains the audit interaction",
      "auditor" in reason.lower(), f"got {reason!r}")
manifestReason = verdict(f"{REPO}\\data\\MANIFEST.json")
check("the manifest refusal names the script that rebuilds it",
      "build_data_manifest" in manifestReason, f"got {manifestReason!r}")

# Test 4: path normalisation. Windows hands back backslashes and is case-insensitive, so a
# comparison done on the raw string would pass every test above and fail in real use.
check("forward slashes reach the same verdict",
      verdict(f"{REPO}/data/frequency-sweeps/x_sweep.csv") is not None)
check("mixed case reaches the same verdict",
      verdict(f"{REPO}\\Data\\Frequency-Sweeps\\X_Sweep.CSV") is not None)
check("a repo-relative path reaches the same verdict",
      verdict("data/frequency-sweeps/x_sweep.csv") is not None)

# Test 5: a CSV OUTSIDE the measurement directories is ordinary work. tools/mutation writes JSON
# that .gitignore already treats as disposable, and scratch CSVs are not the contribution.
check("allows a CSV outside the protected directories",
      verdict(f"{REPO}\\scripts\\scratch.csv") is None)
check("allows tools/mutation JSON, which is regenerated on demand",
      verdict(f"{REPO}\\tools\\mutation\\results.json") is None)

# Test 6: payload shapes. Write and Edit carry file_path, NotebookEdit carries notebook_path, and
# a tool that writes nothing carries neither.
check("reads file_path from an Edit payload",
      editedPath({"tool_input": {"file_path": "a.csv"}}) == "a.csv")
check("reads notebook_path from a NotebookEdit payload",
      editedPath({"tool_input": {"notebook_path": "b.ipynb"}}) == "b.ipynb")
check("returns None when the tool writes no file",
      editedPath({"tool_input": {"command": "ls"}}) is None)
check("survives a payload with no tool_input at all",
      editedPath({}) is None)

# Test 7: the post-edit gate fires on repository markdown and nothing else. Firing on every
# source edit would pay 0.18 s for a check that cannot change.
# ⚠️ These three must use the REAL root with the platform's own separator. Unlike verdict(),
# which matches on a substring and so reaches the same answer for any prefix, shouldRun() asks
# whether the file is inside THIS checkout - so a path from another machine is not a formatting
# detail, it is a different question. That is what failed CI on both legs on 2026-09-20.
check("the gate fires on repository markdown", shouldRun(inRepo("CLAUDE.md")))
check("the gate ignores Python", shouldRun(inRepo("run_tests.py")) is False)
check("the gate ignores markdown outside the repository",
      shouldRun(str(Path(REPO).parent / "not-the-repo" / "notes.md")) is False)
check("the gate ignores a missing path", shouldRun(None) is False)

# Test 8: end to end through the real process boundary, because everything above tests the
# functions rather than the hook. Exit 2 is what actually blocks a tool call; exit 0 is what
# actually lets one through.
GUARD = [sys.executable, str(HERE / "guard_measurement_files.py")]


def runGuard(payload):
    return subprocess.run(GUARD, input=json.dumps(payload), capture_output=True, text=True)


blockedRun = runGuard({"tool_input": {"file_path": f"{REPO}\\data\\frequency-sweeps\\x_sweep.csv"}})
check("the guard process exits 2 on a measurement", blockedRun.returncode == 2,
      f"got {blockedRun.returncode}")
check("the guard process explains itself on stderr", "BLOCKED" in blockedRun.stderr,
      f"got {blockedRun.stderr!r}")

allowedRun = runGuard({"tool_input": {"file_path": f"{REPO}\\docs\\PAPER_DRAFT.md"}})
check("the guard process exits 0 on prose", allowedRun.returncode == 0,
      f"got {allowedRun.returncode}")

# Test 9: fail-open. A hook that crashes must not brick every edit in the repository - see the
# module docstring for why that trade is deliberate rather than lazy.
malformed = subprocess.run(GUARD, input="not json at all", capture_output=True, text=True)
check("malformed input fails OPEN rather than blocking", malformed.returncode == 0,
      f"got {malformed.returncode}")
check("but says so on stderr rather than failing silently",
      "could not read hook input" in malformed.stderr, f"got {malformed.stderr!r}")

if failures:
    print(f"FAILED: {', '.join(failures)}")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")
