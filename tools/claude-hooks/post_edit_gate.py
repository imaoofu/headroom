"""
PostToolUse gate: run the citation coverage check after a markdown edit.

WHY THIS ONE AND NOT THE TEST SUITE
    Three gates guard this repository and they are not interchangeable in a hook:

        python analysis/verify_citations.py --check    0.18 s
        python analysis/audit_claims.py                9.0 s
        python run_tests.py                            11.4 s

    ⛔ Only the first is cheap enough to fire on every edit, and running the other two here would
    be actively harmful. On 2026-09-18 the operator's own test-suite and git runs alongside a
    sweep depressed measured throughput by 9.38% AT EVERY POINT, on the same machine this hook
    runs on. A hook that spawned an 11-second test suite on every file write would reproduce that
    contamination automatically, and a point-to-point residual cannot detect it afterwards
    because it is blind to a uniform offset.

    🔑 So the rule is not "run the gates on edit". It is "run the one gate whose cost is smaller
    than the thing it protects".

WHAT IT CATCHES
    Every arXiv id appearing in repository markdown must be registered by someone who opened the
    source. Two novelty claims and three citation errors in this project came from second-hand
    summaries, so an unregistered id is a real finding rather than bookkeeping.

TURNING IT OFF FOR A BENCH SESSION
    Set HEADROOM_SKIP_HOOKS=1. During a sweep the machine must be left alone, and 0.18 s of
    Python is still not nothing when the measurement is the point.

Run: python tools/claude-hooks/post_edit_gate.py   (reads hook JSON on stdin)
"""

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
GATE = ["python", str(REPO_ROOT / "analysis" / "verify_citations.py"), "--check"]

# Only markdown carries citations. Editing a .py file cannot change citation coverage, and
# firing on every edit would pay the cost for nothing.
WATCHED_SUFFIXES = (".md",)


def shouldRun(filePath):
    """True when this edit could plausibly change citation coverage."""
    if not filePath:
        return False
    path = str(filePath).replace("\\", "/").lower()
    if not any(path.endswith(suffix) for suffix in WATCHED_SUFFIXES):
        return False
    # Only files inside this repository. An edit to a markdown file elsewhere on the machine is
    # none of this gate's business.
    return str(REPO_ROOT).replace("\\", "/").lower() in path


def main():
    if os.environ.get("HEADROOM_SKIP_HOOKS"):
        return 0

    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError, UnicodeDecodeError) as error:
        print(f"[gate] could not read hook input, skipping: {error}", file=sys.stderr)
        return 0

    toolInput = payload.get("tool_input") or {}
    if not shouldRun(toolInput.get("file_path")):
        return 0

    try:
        completed = subprocess.run(GATE, capture_output=True, text=True, timeout=60,
                                   cwd=str(REPO_ROOT))
    except (OSError, subprocess.SubprocessError) as error:
        print(f"[gate] could not run the citation check: {error}", file=sys.stderr)
        return 0

    if completed.returncode == 0:
        return 0

    # Exit 2 feeds stderr back so the problem is fixed now rather than at push. The gate's own
    # output is the useful part - it names the unregistered id.
    print("[gate] verify_citations.py --check FAILED after this edit:", file=sys.stderr)
    print(completed.stdout.strip()[-2000:], file=sys.stderr)
    print(completed.stderr.strip()[-2000:], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
