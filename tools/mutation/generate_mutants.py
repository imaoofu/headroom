"""
Ask the local model to propose mutants for each source file, and keep only the applicable ones.

WHY A LOCAL MODEL DOES THIS PART
    Proposing a mutant is high-volume, low-precision work whose output is graded mechanically:
    run_mutants.py applies each one and the suites return a verdict. A wrong proposal costs a
    rejected record, never a wrong number in the paper. That is the whole reason this task was
    given to the 27B rather than done by hand - the three mutations that gated
    test_gpu_workload.py took real thought each, and ten suites need more than three.

THE SOURCE IS SENT WITH LINE NUMBERS
    A model asked to name a line number in an unnumbered file counts, and miscounts. Numbering
    the source turns counting into copying. The numbers are stripped from what the model echoes
    back: `original` must be the line's own text, and run_mutants.validateMutant refuses the
    mutant if it does not match the file byte for byte.

WHAT IS ASKED FOR
    Mutants that change BEHAVIOUR while still parsing - a flipped comparison, an off-by-one
    bound, a swapped operator, a dropped negation, a changed default. Explicitly not: renaming
    things, editing comments or docstrings, or deleting lines. Those either change nothing or
    change everything, and neither says anything about the assertions.

LAUNCH THE SERVER SMALLER THAN ask_local.py's SERVER_COMMAND SUGGESTS
    That command uses -c 65536, which is right for long interactive sessions and wrong here. The
    largest prompt this script sends is gpu_workload.py at roughly 14,900 tokens, so 24576 is
    ample:

      llama-server.exe -m ...\\Qwen3.8-27B-UD-IQ4_XS.gguf -c 24576 -ngl 99 --flash-attn on
                       -ctk q4_0 -ctv q4_0 -np 1 --spec-type draft-mtp --spec-draft-n-max 1

    This is not tidiness. At -c 65536 on a 31 GB box, llama-server's PRIVATE COMMIT climbed from
    17.1 GB at load to 24.5 GB after a dozen files, taking system commit to 35.9 GB against a
    37.8 GB limit. Nothing spilled - VRAM stayed at 15.8 of 16.3 GB and decode held 36.4 tok/s -
    but the machine ran out of headroom for everything else. The host-side commit tracks the
    context the server was LAUNCHED with, not the context a request uses, so the only lever is
    -c. Measured 2026-08-30.

USAGE
    python tools/mutation/generate_mutants.py                       every allowlisted file
    python tools/mutation/generate_mutants.py --filter curve_model  one of them
    python tools/mutation/generate_mutants.py --count 20 --out mutants.json

    A run stopped partway through can simply be re-issued: files already in the output file are
    skipped. --restart ignores them instead.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "tools" / "mutation"))

from run_mutants import OWNING_SUITE, validateMutant  # noqa: E402

ASK_LOCAL = REPO_ROOT / "tools" / "local-model" / "ask_local.py"

# Overrides ask_local's default system message, which demands source code and no markdown. Here
# the answer is data, not code, so that instruction would fight the task.
SYSTEM = (
    "You are a mutation-testing assistant. You have NO tools and NO filesystem access in this "
    "session. You cannot read files or run commands. Everything you need is in the user "
    "message. Respond with a single JSON array and nothing else: no prose, no explanation, no "
    "markdown fences."
)

SPEC = """Below is the full text of `{path}` from a research codebase, with a line number and a
tab before each line. The line numbers are NOT part of the file.

```
{numbered}
```

Propose exactly {count} MUTANTS for this file. A mutant is a single-line edit that changes what
the code DOES, used to test whether the project's test suite notices.

A good mutant:
  - changes behaviour on some realistic input;
  - still parses as valid Python;
  - is confined to ONE line;
  - targets logic: a comparison operator, a boundary, an arithmetic operator, an index or slice,
    a boolean connective, a default argument, a return value, the order of two operands.

Do NOT propose:
  - edits to comments, docstrings or blank lines;
  - renaming a variable or function;
  - deleting a line or replacing it with `pass`;
  - anything that would fail to parse;
  - changes to import statements.

Spread them across different functions rather than clustering in one.

Return a JSON array of exactly {count} objects, each with these four keys:

  "line"      the line number as an integer, from the numbering above
  "original"  that line's exact text WITHOUT the line number and tab, including its indentation
  "mutated"   the replacement text for that line, same style, one line only
  "rationale" a short phrase naming the behaviour that changes, e.g. "off-by-one on the upper
              bound" or "clamps below instead of above"

`original` must be copied character for character from the line you chose. A mutant whose
`original` does not match the file exactly is discarded without being run.

Output the JSON array only."""


def numberSource(text):
    lines = text.splitlines()
    width = len(str(len(lines)))
    return "\n".join(f"{index:>{width}}\t{line}" for index, line in enumerate(lines, 1))


def extractJsonArray(text):
    """Pull the first balanced [...] out of a reply, ignoring anything around it.

    More forgiving than requiring a clean fence: the model sometimes opens with a sentence
    despite being told not to, and that sentence should cost nothing when the array itself is
    well formed. Brackets inside strings are skipped so a rationale containing one cannot end
    the scan early.
    """
    start = text.find("[")
    if start == -1:
        return None

    depth, inString, escaped = 0, False, False
    for index in range(start, len(text)):
        character = text[index]
        if inString:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                inString = False
            continue
        if character == '"':
            inString = True
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]
    return None


def askForMutants(relative, count, numPredict, timeout, seed):
    """Run one file past the model and return whatever JSON array came back, or []."""
    source = (REPO_ROOT / relative).read_text(encoding="utf-8")
    spec = SPEC.format(path=relative, numbered=numberSource(source), count=count)

    with tempfile.TemporaryDirectory() as scratch:
        specPath = Path(scratch) / "spec.md"
        outPath = Path(scratch) / "reply.json"
        specPath.write_text(spec, encoding="utf-8")

        completed = subprocess.run(
            [sys.executable, str(ASK_LOCAL), str(specPath), "--raw", "--system", SYSTEM,
             "--out", str(outPath), "--num-predict", str(numPredict),
             "--timeout", str(timeout), "--seed", str(seed)],
            capture_output=True, text=True, cwd=str(REPO_ROOT))
        print(completed.stdout.rstrip())
        if completed.stderr.strip():
            print(completed.stderr.rstrip())

        if not outPath.exists():
            return []
        reply = outPath.read_text(encoding="utf-8")

    # ask_local exits non-zero on truncation or a tool call. A truncated reply usually still
    # holds several complete objects before the cut, but the array never closes, so the scan
    # returns None and the whole file yields nothing. Reported rather than silently zero.
    block = extractJsonArray(reply)
    if block is None:
        print(f"  no JSON array in the reply for {relative} "
              f"({len(reply)} chars) - likely truncated, raise --num-predict")
        return []
    try:
        parsed = json.loads(block)
    except json.JSONDecodeError as error:
        print(f"  reply for {relative} is not valid JSON: {error}")
        return []
    return parsed if isinstance(parsed, list) else []


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--out", default="tools/mutation/mutants.json")
    parser.add_argument("--filter", default="",
                        help="Only ask about files whose path contains this substring.")
    parser.add_argument("--count", type=int, default=12, help="Mutants requested per file.")
    parser.add_argument("--num-predict", type=int, default=4000, help="Output token cap.")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument("--seed", type=int, default=-1,
                        help="-1 draws randomly, so a second run proposes different mutants.")
    parser.add_argument("--restart", action="store_true",
                        help="Ignore an existing output file instead of resuming from it.")
    args = parser.parse_args()

    targets = [path for path in OWNING_SUITE if args.filter in path]
    if not targets:
        raise SystemExit(f"No allowlisted file matches {args.filter!r}.")

    # Resume. The first version of this wrote the output file once, at the end, so a run stopped
    # partway through lost every file it had already done - which is what happened when the
    # server had to be killed for memory. Results are flushed after each file instead, and a
    # file already represented in the output is skipped rather than asked about again.
    outPath = Path(args.out)
    accepted, rejected = [], []
    if outPath.exists() and not args.restart:
        accepted = [(mutant, None) for mutant in
                    json.loads(outPath.read_text(encoding="utf-8"))]
        done = {mutant["file"] for mutant, _ in accepted}
        remaining = [path for path in targets if path not in done]
        if len(remaining) < len(targets):
            print(f"Resuming: {len(targets) - len(remaining)} file(s) already in {outPath}, "
                  f"{len(remaining)} to go. Pass --restart to ignore them.")
        targets = remaining

    for relative in targets:
        print(f"\n=== {relative} ===")
        for mutant in askForMutants(relative, args.count, args.num_predict, args.timeout,
                                    args.seed):
            if not isinstance(mutant, dict):
                continue
            # The model is not asked for the filename - it is told about one file and would only
            # add a chance to get it wrong. Stamped here instead.
            mutant["file"] = relative
            reason = validateMutant(mutant)
            (rejected if reason else accepted).append((mutant, reason))
        print(f"  {sum(1 for m, _ in accepted if m['file'] == relative)} accepted, "
              f"{sum(1 for m, _ in rejected if m['file'] == relative)} rejected")
        # Flushed here, not after the loop, so an interrupted run keeps what it has earned.
        outPath.write_text(json.dumps([m for m, _ in accepted], indent=2), encoding="utf-8")

    outPath.write_text(json.dumps([m for m, _ in accepted], indent=2), encoding="utf-8")

    print(f"\n{len(accepted)} accepted -> {args.out}")
    print(f"{len(rejected)} rejected:")
    for mutant, reason in rejected:
        print(f"  {mutant.get('file')}:{mutant.get('line')}  {reason}")
    if not accepted:
        return 1
    print("\nNow run them:\n  python tools/mutation/run_mutants.py " + args.out)
    return 0


if __name__ == "__main__":
    sys.exit(main())
