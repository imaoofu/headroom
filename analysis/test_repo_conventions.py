"""Checks on the repository's own structure, not on its data.

⛔ WHY THE FIRST CHECK EXISTS. On 2026-09-17 `AGENTS.md` was found to be a verbatim copy of
`CLAUDE.md` - ten thousand words, four lines different, and those four differed only by the
filename substituted into them. It had been committed by a `git add -A` without anyone deciding to
create it.

That is the precise failure `CLAUDE.md` warns about in its own text - "Nothing else in CLAUDE.md
restates them; if you find a second copy, delete it rather than update it" - and the project has
already carried two contradictory values for one quantity in a single file. Two copies of the
authority file WILL drift, and nothing would say which one was stale.

🔑 The check is a SIMILARITY bound, not an equality test. Forbidding only byte-identical files
would pass a copy with one word changed, which is strictly worse than an exact duplicate because
it looks deliberate.
"""

import difflib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

passed = 0


def check(description, condition):
    global passed
    if condition:
        passed += 1
        print(f"  [PASS] {description}")
    else:
        print(f"  [FAIL] {description}")
        raise AssertionError(description)


print("the authority file must have exactly one copy")

claudeMd = (REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
agentsMd = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")

check("CLAUDE.md exists and is substantial", len(claudeMd) > 10000)
check("AGENTS.md exists", len(agentsMd) > 0)
check("AGENTS.md is not byte-identical to CLAUDE.md", agentsMd != claudeMd)

similarity = difflib.SequenceMatcher(None, claudeMd, agentsMd).ratio()
check(f"AGENTS.md is not a near-copy of CLAUDE.md (similarity {similarity:.1%}, must be under 50%) "
      f"- a duplicated authority file drifts and nothing flags which copy is stale",
      similarity < 0.50)

check("AGENTS.md points at CLAUDE.md as the authority rather than restating it",
      "CLAUDE.md" in agentsMd and "AUTHORITY" in agentsMd.upper())

print()
print("the canonical count block lives in exactly one place")

# CLAUDE.md's coverage block is the only place a registry total is allowed to live, and it says so.
# A second copy anywhere is what produced two contradictory totals in one file on 2026-08-30.
countPhrase = "284 of 284"
holders = []
for path in sorted(REPO_ROOT.glob("*.md")):
    if countPhrase in path.read_text(encoding="utf-8"):
        holders.append(path.name)
check(f"the pinned claim total appears in at most one ROOT document (found in: "
      f"{holders or 'none'}) - counts belong to the tools, not to prose",
      len(holders) <= 1)

print()
print("agent-facing documents are present and say what they are for")

agentDocs = REPO_ROOT / "docs" / "agents"
check("docs/agents/ exists", agentDocs.is_dir())

brief = agentDocs / "NOVELTY-CHECK-BRIEF.md"
check("the cold novelty brief exists", brief.is_file())

briefText = brief.read_text(encoding="utf-8")

# ⛔ THE POINT OF THE BRIEF IS THAT IT CARRIES NO PROJECT FRAMING. If it names this project's own
# vocabulary, the outside reader stops being outside - which is the single property it exists to
# have. These are the terms whose absence makes the check meaningful.
leakedTerms = [term for term in ("Headroom", "CLAUDE.md", "Raymond", "Inspirit", "load floor",
                                 "load-floor", "ridge point", "ridge-point")
               if term.lower() in briefText.lower()]
check(f"the cold brief leaks no project framing (found: {leakedTerms or 'none'}) - naming this "
      f"project's own vocabulary would tell the outside reader what answer to reach",
      not leakedTerms)

protocol = agentDocs / "COLLABORATION-PROTOCOL.md"
check("the collaboration protocol exists", protocol.is_file())

print()
print(f"{passed} checks passed.")
print("These check the repository's SHAPE. They cannot tell you whether what CLAUDE.md says is "
      "true - only that there is one of it.")
