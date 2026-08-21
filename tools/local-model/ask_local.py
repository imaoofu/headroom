"""
Send a task specification to a local Ollama model and save the code it returns.

WHY THIS EXISTS
    Delegating a mechanical task to a local model is fiddly in four specific ways, and all four
    cost real time before this script existed. Each is handled below, and each comment says
    which failure it prevents rather than what the line does.

    1. THE WRONG ENDPOINT SILENTLY CHANGES BEHAVIOUR. Ollama's /api/generate takes one flat
       string and applies whatever SYSTEM block was baked in at `ollama create` time. Only
       /api/chat accepts a system TURN, and only a system turn can override that baked-in
       block. This matters because the Headroom system prompt tells a model never to claim it
       read a file it did not read - good advice for a model with no tools, and actively
       harmful for Qwen3.8, which has tool-calling capability and reads it as an instruction to
       go and read the CSVs. Through /api/generate it emitted tool calls instead of code twice,
       including once after the task text explicitly said no tools were available: a line in a
       user message loses to a system prompt. This script always uses /api/chat.

    2. RUNNING OUT OF CONTEXT LOOKS LIKE A BAD ANSWER. A first attempt at the 5.7.2 claims
       spent 10,846 tokens deliberating and stopped mid-sentence, having produced no answer -
       5,538 prompt plus 10,846 output is exactly the 16,384 the model was loaded with. The
       output read like a model that could not do the task. It was a model that was not given
       room to finish. The budget is checked before sending and `done_reason` after.

    3. THINKING MODE IS NOT ALWAYS SEPARATED. On this GGUF the reasoning arrives in the ordinary
       response field with no <think> tags to strip, so it lands in the middle of what is
       supposed to be a file. Thinking is therefore off unless asked for.

    4. TOOL CALLS COME BACK AS PROSE. When a model decides to call a tool that was never
       offered, the call arrives as text that looks vaguely like an answer. Output is scanned
       for it so the run is reported as failed rather than written to disk as source.

WHAT THIS DELIBERATELY DOES NOT DO
    It does not check the answer. Verifying is the caller's job and is the entire point of the
    arrangement: for claims work that means running analysis/audit_claims.py, and for a test
    file it means the mutation gate. Nothing a local model returns has ever been committed here
    without being run first, and two of the specifications written for it turned out to contain
    errors of their own, so the checking catches both sides.

USAGE
    python tools/local-model/ask_local.py spec.md --context analysis/claims_consumer.py
    python tools/local-model/ask_local.py spec.md --model coder --out draft.py
    python tools/local-model/ask_local.py spec.md --think --num-predict 4000
"""

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

HOST = "http://localhost:11434"

# Short names for the models configured on this machine, so a caller does not have to remember
# which tag carries the Headroom system prompt and which is the stock upstream one.
MODELS = {
    "qwen38": "qwen38-headroom",
    "coder": "qwen3-coder-headroom",
    "coder-stock": "qwen3-coder:30b",
}

DEFAULT_SYSTEM = (
    "You are a code generator. You have NO tools and NO filesystem access in this session. "
    "You cannot read files or run commands, and any attempt to do so will fail. Everything you "
    "need is in the user message. Respond with source code only: no prose, no markdown fences, "
    "no tool calls.\n\n"
    "Repo conventions: camelCase function and variable names, not snake_case. Comments only for "
    "a non-obvious WHY, never restating what a line does. ASCII only."
)

# Substrings that mean the model tried to act rather than answer. Checked case-insensitively.
TOOL_CALL_MARKERS = ("<tool_call>", "<function=", "<|tool_call", "```tool_code")

# Rough characters-per-token for source code plus technical prose. Only used to decide whether
# to warn before sending, so an approximation is enough - but it is deliberately LOW, because
# under-estimating the prompt is the failure that silently truncates the answer.
CHARS_PER_TOKEN = 3.2


def readModelContext(model):
    """The num_ctx the model will actually load with, from its own configuration.

    Read rather than assumed: this is the number that decides whether a long deliberation has
    room to reach an answer, and it is set per-model in the Modelfile.
    """
    try:
        body = json.dumps({"model": model}).encode()
        request = urllib.request.Request(f"{HOST}/api/show", data=body,
                                         headers={"Content-Type": "application/json"})
        info = json.load(urllib.request.urlopen(request, timeout=60))
    except urllib.error.URLError as error:
        raise SystemExit(f"Cannot reach Ollama at {HOST}: {error}. Is `ollama serve` running?")

    for source in (info.get("parameters", ""), ""):
        match = re.search(r"num_ctx\s+(\d+)", source or "")
        if match:
            return int(match.group(1))
    # Ollama's own default when a Modelfile says nothing.
    return 4096


def buildUserMessage(specPath, contextPaths):
    parts = []
    for path in contextPaths:
        text = Path(path).read_text(encoding="utf-8")
        suffix = Path(path).suffix.lstrip(".") or ""
        parts.append(f"Contents of {path}, for reference:\n\n```{suffix}\n{text}\n```")
    parts.append(Path(specPath).read_text(encoding="utf-8"))
    return "\n\n".join(parts)


def stripFences(text):
    """Remove one wrapping markdown code fence if the whole reply is inside it.

    Both models tested wrap their output in ```python despite being told not to, and every
    caller then has to strip it. Only a fence around the WHOLE reply is removed; a fence in the
    middle means the model produced prose as well as code, which the caller should see.
    """
    stripped = text.strip()
    match = re.match(r"^```[a-zA-Z0-9_+-]*\n(.*)\n```$", stripped, re.DOTALL)
    if not match:
        return stripped

    # The .* above is greedy, so a reply made of TWO fenced blocks matches as though it were
    # one: the span runs from the first opening fence to the last closing one, and whatever sat
    # between the blocks gets spliced into the middle of the file. A body that still contains a
    # fence at the start of a line was therefore never a single wrapping block, and the whole
    # reply is handed back so the caller sees what actually came out.
    body = match.group(1)
    if re.search(r"^```", body, re.MULTILINE):
        return stripped
    return body


def findToolCall(text):
    lowered = text.lower()
    for marker in TOOL_CALL_MARKERS:
        if marker in lowered:
            return marker
    return None


def appendReply(target, reply):
    """Append a reply to a source file without corrupting its encoding.

    This exists because the obvious shell equivalent is broken on this machine. PowerShell's
    `>>` and Out-File write a UTF-8 BOM - measured, bytes EF BB BF - so appending a draft to an
    existing .py inserts a BOM in the MIDDLE of the file and Python then refuses it with
    "invalid non-printable character U+FEFF". The stability logger had the same bug in its
    session.json for weeks. Read and rewrite the whole file in one encoding instead.
    """
    existing = ""
    if target.exists():
        # newline="" on the READ as well as the write. read_text() applies universal-newline
        # translation, so a CRLF target comes back as LF and gets written back as LF - turning
        # a three-line append into a diff that touches every line in the file.
        with open(target, encoding="utf-8", newline="") as handle:
            existing = handle.read()

    ending = "\r\n" if "\r\n" in existing else "\n"
    body = reply.strip().replace("\r\n", "\n").replace("\n", ending)
    with open(target, "w", encoding="utf-8", newline="") as handle:
        handle.write(existing.rstrip() + ending * 3 + body + ending)


def ask(model, system, user, think, numPredict, timeout):
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "stream": False,
        "think": think,
        "keep_alive": "30m",
        "options": {"num_predict": numPredict},
    }
    request = urllib.request.Request(f"{HOST}/api/chat", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    started = time.time()
    try:
        response = json.load(urllib.request.urlopen(request, timeout=timeout))
    except urllib.error.URLError as error:
        raise SystemExit(f"Request to {HOST}/api/chat failed: {error}")
    return response, time.time() - started


def rate(count, durationNs):
    return count / (durationNs / 1e9) if durationNs else float("nan")


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("spec", help="Path to the task specification.")
    parser.add_argument("--context", action="append", default=[],
                        help="File to include before the spec. Repeatable.")
    parser.add_argument("--model", default="qwen38",
                        help=f"Short name {sorted(MODELS)} or a full Ollama tag.")
    parser.add_argument("--out", help="Where to write the reply. Default: <spec>.out.py")
    parser.add_argument("--system", help="Replace the default no-tools system message.")
    parser.add_argument("--think", action="store_true",
                        help="Allow reasoning. Off by default; see item 3 in the docstring.")
    parser.add_argument("--num-predict", type=int, default=2000,
                        help="Output token cap.")
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds.")
    parser.add_argument("--raw", action="store_true", help="Do not strip a wrapping code fence.")
    parser.add_argument("--force", action="store_true",
                        help="Send even when the context budget check says it will not fit.")
    parser.add_argument("--append",
                        help="On success, also append the reply to this file. Refused if the "
                             "run had problems.")
    args = parser.parse_args()

    model = MODELS.get(args.model, args.model)
    system = args.system or DEFAULT_SYSTEM
    user = buildUserMessage(args.spec, args.context)

    contextLimit = readModelContext(model)
    estimated = int((len(system) + len(user)) / CHARS_PER_TOKEN)
    print(f"model            {model}")
    print(f"context limit    {contextLimit} tokens")
    print(f"prompt           ~{estimated} tokens (estimated)")
    print(f"output cap       {args.num_predict} tokens")

    # The check that would have saved the first 5.7.2 attempt. Thinking makes it far more
    # likely to bind, because deliberation is counted against the same budget as the answer.
    if estimated + args.num_predict > contextLimit:
        room = contextLimit - estimated
        message = (f"\nWILL NOT FIT: ~{estimated} prompt + {args.num_predict} output exceeds "
                   f"{contextLimit}.\nThe model would truncate mid-answer and the result would "
                   f"read like a bad answer rather than a cut-off one.\nOptions: drop a "
                   f"--context file, lower --num-predict to under {room}, or raise num_ctx in "
                   f"the Modelfile (which costs VRAM).")
        if not args.force:
            raise SystemExit(message + "\nUse --force to send anyway.")
        print(message + "\nSending anyway because --force was given.")

    response, wall = ask(model, system, user, args.think, args.num_predict, args.timeout)
    message = response.get("message", {})
    reply = message.get("content", "")

    print(f"\nwall             {wall:.1f}s")
    print(f"prompt           {response.get('prompt_eval_count')} tokens @ "
          f"{rate(response.get('prompt_eval_count', 0), response.get('prompt_eval_duration', 0)):.0f} tok/s")
    print(f"output           {response.get('eval_count')} tokens @ "
          f"{rate(response.get('eval_count', 0), response.get('eval_duration', 0)):.1f} tok/s")
    print(f"done_reason      {response.get('done_reason')}")

    problems = []
    # "length" means the cap or the context ran out, so the tail of the answer does not exist.
    # Reported as a failure rather than a note: a truncated file is not a shorter file.
    if response.get("done_reason") == "length":
        problems.append("TRUNCATED: hit the output cap or the context limit. The reply is "
                        "incomplete - raise --num-predict or shorten the prompt.")
    if message.get("tool_calls"):
        problems.append("The model returned structured tool_calls instead of an answer.")
    marker = findToolCall(reply)
    if marker:
        problems.append(f"The reply contains {marker!r}: the model tried to call a tool that "
                        f"was never offered, rather than answering. Check the system message.")
    if not reply.strip():
        problems.append("Empty reply.")

    outPath = Path(args.out) if args.out else Path(args.spec).with_suffix(".out.py")
    outPath.write_text(reply if args.raw else stripFences(reply), encoding="utf-8")
    print(f"written          {outPath}")

    if problems:
        print("\nPROBLEMS:")
        for problem in problems:
            print(f"  - {problem}")
        print("\nThe reply was still written so it can be inspected. Do not use it as source.")
        if args.append:
            print(f"NOT appended to {args.append}: the run had problems.")
        return 1

    if args.append:
        appendReply(Path(args.append), outPath.read_text(encoding="utf-8"))
        print(f"appended        {args.append}")

    print("\nNow VERIFY it. Nothing from a local model goes in without being run:")
    print("  python analysis/audit_claims.py        for claims work")
    print("  python analysis/test_<module>.py       for a test file, then mutate and re-run")
    return 0


if __name__ == "__main__":
    sys.exit(main())
