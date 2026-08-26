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

A SECOND REAL BUG, in appendReply
    The first version read the target with Path.read_text(), which applies universal-newline
    translation. A CRLF file - which every file in this repo is - came back as LF and was
    written back as LF, so appending three lines produced a diff touching every line in the
    module. Caught by the CRLF check below on its first run. The fix reads with newline="" as
    well as writing with it, and converts the reply's own endings to match the target, because
    a model's reply always arrives with LF and leaving it produces a mixed-ending file instead.

PROVENANCE
    Written directly. Fifteen deliberate mutations were introduced into ask_local.py and all
    fifteen were caught. On appendReply:

      - reading without newline="", so CRLF is translated away on the way in
      - writing the reply verbatim, leaving mixed endings in a CRLF file
      - always using CRLF regardless of what the target uses
      - writing with utf-8-sig, putting a BOM in the middle of the file
      - dropping the existing content instead of appending to it

    And on the rest:

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

import json
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
# Appending without corrupting the target
# --------------------------------------------------------------------------------------

with tempfile.TemporaryDirectory() as directory:
    target = Path(directory) / "module.py"
    target.write_text("existing = 1\n", encoding="utf-8")
    askLocal.appendReply(target, "added = 2")

    check(
        "appending writes no BOM anywhere in the file",
        b"\xef\xbb\xbf" not in target.read_bytes(),
        "PowerShell's >> writes EF BB BF, measured on this machine. Appended to an existing "
        "module that lands mid-file and Python refuses it with 'invalid non-printable "
        "character U+FEFF'",
    )
    check(
        "appending keeps the existing content and adds the new",
        target.read_text(encoding="utf-8") == "existing = 1\n\n\nadded = 2\n",
        f"got {target.read_text(encoding='utf-8')!r}",
    )

    fresh = Path(directory) / "new.py"
    askLocal.appendReply(fresh, "x = 1")
    check(
        "appending to a file that does not exist yet creates it",
        fresh.read_text(encoding="utf-8").strip() == "x = 1",
    )

    # A CRLF target must stay wholly CRLF: the existing lines untouched, and the appended ones
    # converted to match. read_text() would translate the existing CRLF to LF on the way in and
    # write it back as LF, turning a three-line append into a diff over the whole file. Mixing
    # the two is the other failure, and is what a naive newline="" write produces because the
    # model's reply always arrives with LF.
    crlf = Path(directory) / "crlf.py"
    crlf.write_bytes(b"a = 1\r\n")
    askLocal.appendReply(crlf, "b = 2\nc = 3")
    written = crlf.read_bytes()
    check(
        "a CRLF target keeps its existing CRLF lines",
        written.startswith(b"a = 1\r\n"),
        f"got {written!r}",
    )
    check(
        "the appended lines are converted to the target's endings, not left mixed",
        b"\n" not in written.replace(b"\r\n", b""),
        f"got {written!r}; a bare LF among CRLF lines is a mixed-ending file",
    )

    lf = Path(directory) / "lf.py"
    lf.write_bytes(b"a = 1\n")
    askLocal.appendReply(lf, "b = 2")
    check(
        "an LF target is not promoted to CRLF",
        b"\r" not in lf.read_bytes(),
        f"got {lf.read_bytes()!r}",
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

# A reply that is commentary AND code was previously written out with no problem reported, so a
# file that does not parse looked like a clean run. That happened on the first delegation whose
# output was a test suite, and cost a debugging cycle before anyone looked at line 1.
FENCE = chr(96) * 3

check("prose before a fenced block is reported as prose-and-code",
      askLocal.looksLikeProseAndCode("Here is my reasoning.\n\n" + FENCE + "python\nx = 1\n" + FENCE))
check("two fenced blocks are reported as prose-and-code",
      askLocal.looksLikeProseAndCode(FENCE + "python\na=1\n" + FENCE + "\naside\n" + FENCE + "python\nb=2\n" + FENCE))
check("a single wrapping fence is NOT reported, it is the normal case",
      not askLocal.looksLikeProseAndCode(FENCE + "python\nx = 1\n" + FENCE))
check("bare code with no fence at all is NOT reported",
      not askLocal.looksLikeProseAndCode("x = 1\n"))

# ---------------------------------------------------------------------------------------------
# Two backends, one normalised result. Added when llama.cpp replaced Ollama as the default.
#
# WHAT THESE ARE FOR. ask() is the only place that knows a backend exists; everything downstream
# reads one shape. So the risk is not that a field is missing - it is that a field is present and
# WRONG, because both backends return plausible-looking numbers for the same request. A stop
# reason read from the wrong key comes back None, and None is not "length", so a truncated reply
# would be reported as a clean run - which is failure 2 in ask_local's docstring returning by a
# different door.
#
# THE BUG THESE WERE WRITTEN FOR. The llama.cpp payload was first written with "temperature": 0
# while the Ollama models carry temperature 0.7 / top_k 20 / top_p 0.8 in their Modelfiles.
# Switching backend then silently changed the sampler. Nothing in the output would have shown it:
# greedy code and sampled code both look like code. The sampling checks below fail against that
# version and pass against the fix.

captured = {}


def fakeUrlopen(request, timeout=None):
    """Capture the outgoing request and return a canned response for the backend under test."""
    captured["url"] = request.full_url
    captured["payload"] = json.loads(request.data.decode())

    if "/v1/chat/completions" in request.full_url:
        body = {"choices": [{"finish_reason": "length",
                             "message": {"content": "x = 1", "reasoning_content": "hmm"}}],
                "usage": {"prompt_tokens": 11, "completion_tokens": 22},
                "timings": {"prompt_per_second": 900.0, "predicted_per_second": 40.0}}
    else:
        body = {"message": {"content": "x = 1", "thinking": "hmm"},
                "done_reason": "length",
                "prompt_eval_count": 11, "prompt_eval_duration": 2_000_000_000,
                "eval_count": 22, "eval_duration": 2_000_000_000}

    class Fake:
        def read(self):
            return json.dumps(body).encode()

        def __enter__(self):
            return self

        def __exit__(self, *_):
            return False

    return Fake()


def callAsk(backend):
    captured.clear()
    askLocal.BACKEND = backend
    askLocal.HOST = askLocal.BACKENDS[backend]
    real = askLocal.urllib.request.urlopen
    askLocal.urllib.request.urlopen = fakeUrlopen
    try:
        result, _ = askLocal.ask("m", "sys", "usr", False, 500, 60,
                                 {"temperature": 0.7, "top_k": 20, "top_p": 0.8}, 1234)
    finally:
        askLocal.urllib.request.urlopen = real
        askLocal.BACKEND = "llamacpp"
        askLocal.HOST = askLocal.BACKENDS["llamacpp"]
    return result, dict(captured)


llamaResult, llamaSent = callAsk("llamacpp")
ollamaResult, ollamaSent = callAsk("ollama")

check("llama.cpp content is read from choices[0].message, not from a top-level message key",
      llamaResult["content"] == "x = 1")
check("llama.cpp reasoning goes to its own field and stays OUT of content",
      llamaResult["reasoning"] == "hmm" and "hmm" not in llamaResult["content"])
check("llama.cpp truncation is read from finish_reason",
      llamaResult["stopReason"] == "length",
      "read from the wrong key this comes back None, None != 'length', and a truncated reply "
      "is reported as a clean run")
check("llama.cpp rates are taken from timings, not recomputed from durations it does not send",
      llamaResult["outputRate"] == 40.0 and llamaResult["promptRate"] == 900.0)
check("llama.cpp token counts come from usage",
      (llamaResult["promptTokens"], llamaResult["outputTokens"]) == (11, 22))

check("Ollama truncation is read from done_reason",
      ollamaResult["stopReason"] == "length")
check("Ollama rates are computed from nanosecond durations",
      abs(ollamaResult["outputRate"] - 11.0) < 1e-9,
      "22 tokens in 2e9 ns is 11 tok/s; reading the field as seconds would give 11e9")

check("both backends return the SAME keys, so nothing downstream branches on backend",
      set(llamaResult) == set(ollamaResult))

# The actual bug. Sampling must be sent explicitly and identically, not left to a default that
# differs between a Modelfile and a bare GGUF.
for name, sent, where in (("llama.cpp", llamaSent, llamaSent["payload"]),
                          ("Ollama", ollamaSent, ollamaSent["payload"].get("options", {}))):
    check(f"{name} is sent the temperature it was given, not a hardcoded one",
          where.get("temperature") == 0.7,
          "hardcoding 0 here changes the sampler when the backend changes, and both settings "
          "produce plausible code so the output does not show it")
    check(f"{name} is sent top_k and top_p as well",
          where.get("top_k") == 20 and where.get("top_p") == 0.8)
    check(f"{name} is sent the seed, so a repeat can be made reproducible on purpose",
          where.get("seed") == 1234)

check("llama.cpp is asked for the chat endpoint, never the completion one",
      llamaSent["url"].endswith("/v1/chat/completions"))
check("Ollama is asked for /api/chat, because only a chat turn overrides a baked-in system block",
      ollamaSent["url"].endswith("/api/chat"))
check("thinking off is sent to llama.cpp as a template kwarg, since it has no think flag",
      llamaSent["payload"]["chat_template_kwargs"]["enable_thinking"] is False)

check("rate returns nan rather than dividing by zero when a duration is missing",
      askLocal.rate(100, 0) != askLocal.rate(100, 0))

if failures:
    print(f"{len(failures)} check(s) failed.")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")
