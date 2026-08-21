"""
Known-answer checks for ask_local.py.

WHY THESE
    This script's job is to stop a local-model run from failing silently, so the checks are
    mostly about the two guards that decide whether a reply is trustworthy at all.

    The one that matters most is the FENCE rule. Both models tested wrap their answer in
    ```python despite being told not to, so the fence has to come off - but a fence that
    appears in the MIDDLE of a reply means something different: the model produced prose as
    well as code, and the caller needs to see that rather than have it quietly concatenated
    into a source file. A stripper that removes every fence it finds would turn "here is my
    reasoning, then the code" into a file that looks like code and is not.

    The token estimate is checked for DIRECTION, not accuracy. Over-estimating the prompt
    costs a needless warning. Under-estimating sends a request that truncates mid-answer,
    which is the failure that cost the most time and is the hardest to recognise from the
    output. So the constant is asserted to be conservative against the usual 4.0 rule of
    thumb, and against the one real measurement available.

A REAL BUG THESE CHECKS FOUND, recorded because the fix is not obvious from the code
    The first stripFences matched an opening fence, then a DOTALL '.*', then a closing
    fence anchored to the end, and returned the group. That '.*' is GREEDY, so a reply
    made of TWO fenced blocks matched as though it were one: the span ran from the first
    opening fence to the LAST closing one, and the prose sitting between the blocks was
    spliced into the middle of the output file. The
    "two separate fenced blocks are left alone" check below failed on the first run and the
    guard that rejects a body still containing a line-initial fence was added in response.

    The single-block and prose-then-code checks both passed against the broken version, so
    neither would have found it. It took a case with a fence at the start AND at the end AND
    something in between.

PROVENANCE
    Written directly. Ten deliberate mutations were introduced into ask_local.py and all ten
    were caught:

      - stripFences using re.sub over every fence it finds
      - stripFences keeping the greedy match without the inner-fence guard
      - stripFences dropping the re.DOTALL flag
      - stripFences returning text unchanged
      - stripFences not stripping surrounding whitespace first
      - findToolCall comparing against the raw reply instead of the lowered copy
      - findToolCall returning True/False instead of the marker
      - rate dividing without the zero guard          (detected as an uncaught exception)
      - buildUserMessage inserting the spec before the context files
      - CHARS_PER_TOKEN raised to 4.5

    Delete __pycache__ between mutations; a same-length edit can leave stale bytecode running
    while the source on disk reads correct.
"""

import importlib.util
import tempfile
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "ask_local", Path(__file__).resolve().parent / "ask_local.py")
askLocal = importlib.util.module_from_spec(spec)
spec.loader.exec_module(askLocal)

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
# Fence handling
# --------------------------------------------------------------------------------------

check(
    "a fence wrapping the whole reply is removed",
    askLocal.stripFences("```python\ndef f():\n    return 1\n```") == "def f():\n    return 1",
    f"got {askLocal.stripFences('```python\ndef f():\n    return 1\n```')!r}",
)

check(
    "a fence with no language tag is removed",
    askLocal.stripFences("```\ndef f():\n    pass\n```") == "def f():\n    pass",
)

check(
    "leading and trailing whitespace does not defeat the match",
    askLocal.stripFences("\n\n  ```python\ndef f():\n    pass\n```  \n") == "def f():\n    pass",
    "models emit a trailing newline after the closing fence more often than not",
)

check(
    "a multi-line body survives intact",
    askLocal.stripFences("```python\na = 1\n\nb = 2\n```") == "a = 1\n\nb = 2",
    "without re.DOTALL the '.' stops at the first newline and nothing matches",
)

check(
    "a reply with no fence is returned unchanged apart from stripping",
    askLocal.stripFences("  def f():\n    pass  ") == "def f():\n    pass",
)

# The important negative. A fence that does not wrap the WHOLE reply means the model wrote
# prose too, and silently removing it would produce a file whose first line is English.
proseThenCode = "Here is my reasoning.\n\n```python\ndef f():\n    pass\n```"
check(
    "a fence in the MIDDLE of a reply is NOT stripped",
    askLocal.stripFences(proseThenCode) == proseThenCode,
    f"got {askLocal.stripFences(proseThenCode)!r}; the caller must see that prose came back",
)

twoBlocks = "```python\na = 1\n```\n\nand also\n\n```python\nb = 2\n```"
check(
    "two separate fenced blocks are left alone",
    askLocal.stripFences(twoBlocks) == twoBlocks,
    "concatenating them would invent a file the model never wrote",
)

# --------------------------------------------------------------------------------------
# Tool-call detection
# --------------------------------------------------------------------------------------

check(
    "a <tool_call> block is detected and the marker is returned",
    askLocal.findToolCall("I'll check first.\n<tool_call>\n<function=Read>") == "<tool_call>",
)

check(
    "the <function= form is detected on its own",
    askLocal.findToolCall("<function=Bash>\n<parameter=command>ls") == "<function=",
)

check(
    "detection is case-insensitive",
    askLocal.findToolCall("<TOOL_CALL>") == "<tool_call>",
    "the tag's case varies between templates and a miss here means a tool call gets "
    "written out as if it were source",
)

check(
    "clean code is not flagged",
    askLocal.findToolCall("def f():\n    return call_tool()") is None,
    "a function whose NAME contains 'tool' must not trip the check",
)

check(
    "findToolCall returns the marker, not a boolean",
    isinstance(askLocal.findToolCall("<tool_call>"), str),
    "the marker is printed in the failure message so the caller can see which form it was",
)

# --------------------------------------------------------------------------------------
# Rate reporting
# --------------------------------------------------------------------------------------

check(
    "rate converts nanoseconds to tokens per second",
    abs(askLocal.rate(100, 2_000_000_000) - 50.0) < 1e-9,
    f"got {askLocal.rate(100, 2_000_000_000)}",
)

zeroRate = askLocal.rate(0, 0)
check(
    "a zero duration yields nan rather than raising",
    zeroRate != zeroRate,
    "Ollama omits the duration fields on some error replies, and a ZeroDivisionError there "
    "would lose the reply along with the statistics",
)

# --------------------------------------------------------------------------------------
# Prompt assembly
# --------------------------------------------------------------------------------------

with tempfile.TemporaryDirectory() as directory:
    root = Path(directory)
    specFile = root / "spec.md"
    specFile.write_text("THE TASK GOES HERE", encoding="utf-8")
    contextFile = root / "example.py"
    contextFile.write_text("REFERENCE CODE", encoding="utf-8")

    message = askLocal.buildUserMessage(specFile, [contextFile])

    check(
        "context is placed BEFORE the task, not after",
        message.index("REFERENCE CODE") < message.index("THE TASK GOES HERE"),
        "instructions read last are followed more reliably than instructions buried above "
        "several hundred lines of reference code",
    )
    check(
        "the context file is fenced with its own language tag",
        "```py\nREFERENCE CODE" in message,
    )
    check(
        "the reference file is named so the model can refer to it",
        str(contextFile) in message,
    )

# --------------------------------------------------------------------------------------
# The token estimate must err high
# --------------------------------------------------------------------------------------

check(
    "CHARS_PER_TOKEN is more conservative than the usual 4.0 rule of thumb",
    askLocal.CHARS_PER_TOKEN < 4.0,
    f"got {askLocal.CHARS_PER_TOKEN}; a higher value under-estimates the prompt, and an "
    f"under-estimate is what lets a request through that then truncates mid-answer",
)

# The one real measurement available: the 5.7.2 specification plus claims_consumer.py as
# context measured 5538 prompt tokens on Qwen3.8. At 17726 characters that is 3.20 chars per
# token, so the constant must not exceed it or that same prompt would be under-estimated.
check(
    "the constant does not exceed the measured density of a real prompt",
    askLocal.CHARS_PER_TOKEN <= 3.2,
    f"got {askLocal.CHARS_PER_TOKEN}; 17726 characters measured 5538 tokens = 3.20",
)

check(
    "the default system message forbids tools explicitly",
    "NO tools" in askLocal.DEFAULT_SYSTEM,
    "this is the line that stopped Qwen3.8 emitting tool calls instead of code; without it "
    "the Modelfile's own system prompt applies and the run fails in a way that looks like a "
    "bad answer",
)

if failures:
    print(f"{len(failures)} check(s) failed.")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")
