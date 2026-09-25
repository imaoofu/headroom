"""
Send a task specification to a local model and save the code it returns.

BACKENDS
    llama.cpp (default) and Ollama. llama.cpp is the default because it is the only one of
    the two that can use the MTP self-draft head this model ships with: measured 2026-08-25
    on the 5060 Ti, 40.0 tok/s with --spec-type draft-mtp against 28.9 without, n=5 each,
    spreads 3.1% and 0.9%, byte-identical greedy output. Ollama's CUDA runner has no
    speculative path at all - its MTP code lives in the MLX runner and runs only on Apple
    Silicon. Ollama stays reachable via --backend ollama because the Headroom-prompted model
    is registered there too, which is a convenience rather than a capability llama.cpp lacks.

    That rationale used to read "because qwen3-coder lives there and has no llama.cpp
    counterpart on this machine." Both qwen3-coder models were deleted on 2026-09-08, so the
    Ollama backend no longer reaches anything llama.cpp cannot.

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
       user message loses to a system prompt. This script always uses a chat endpoint.

       On llama.cpp the trap does not exist: a bare GGUF carries no baked-in system block, so
       the system turn sent below is the only one there is. Behaviour is unchanged either way,
       because this script has always sent an explicit system turn and thereby overridden it.

    2. RUNNING OUT OF CONTEXT LOOKS LIKE A BAD ANSWER. A first attempt at the 5.7.2 claims
       spent 10,846 tokens deliberating and stopped mid-sentence, having produced no answer -
       5,538 prompt plus 10,846 output is exactly the 16,384 the model was loaded with. The
       output read like a model that could not do the task. It was a model that was not given
       room to finish. The budget is checked before sending and `done_reason` after.

    3. THINKING MODE IS NOT ALWAYS SEPARATED. Through Ollama the reasoning arrives in the
       ordinary response field with no <think> tags to strip, so it lands in the middle of what
       is supposed to be a file. llama.cpp does not have this problem - it routes reasoning to a
       separate reasoning_content field, verified on this model. Thinking is off unless asked
       for on both regardless, because either way it is charged against the same output budget
       as the answer, which is failure 2.

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
    python tools/local-model/ask_local.py spec.md --backend ollama --model qwen38 --out draft.py
    python tools/local-model/ask_local.py spec.md --think --num-predict 4000

    llama-server must already be running; see SERVER_COMMAND below.
"""

import argparse
from datetime import datetime, timezone
import json
import math
import re
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

try:
    from streaming import iter_sse_events
except ModuleNotFoundError:  # importlib-based checks load this file without its directory on sys.path
    import importlib.util
    _stream_spec = importlib.util.spec_from_file_location(
        "local_model_streaming", Path(__file__).resolve().parent / "streaming.py")
    _stream_module = importlib.util.module_from_spec(_stream_spec)
    _stream_spec.loader.exec_module(_stream_module)
    iter_sse_events = _stream_module.iter_sse_events

BACKENDS = {"llamacpp": "http://localhost:8099", "ollama": "http://localhost:11434"}

# Set from --backend in main(). Module level rather than threaded through every function
# because one run only ever talks to one backend.
BACKEND = "llamacpp"
HOST = BACKENDS[BACKEND]

SERVER_COMMAND = (
    r"C:\Users\Raymond\llamacpp\llama-server.exe "
    r"-m C:\Users\Raymond\models\Qwen3.8-27B-UD-IQ4_XS.gguf "
    r"-c 65536 -ngl 99 --flash-attn on -ctk q4_0 -ctv q4_0 -np 1 --no-mmap "
    r"--spec-type draft-mtp --spec-draft-n-max 1 --port 8099 "
    r"--jinja --chat-template-file C:\Users\Raymond\Documents\headroom\tools\local-model\qwen-chat-template-claude-code.jinja"
)
# The chat template is the model's own with ONE branch changed (2026-09-24): a system message after
# the first turn raised "System message must be at the beginning" and failed every Claude Code
# request with HTTP 500. It now renders as a system block. Reproduced on the original (500) and fixed
# on this one (200); ordinary requests render as before. docs/local-model-findings/2026-09-24-claude-code-harness-L1.md
# --port 8099 was missing until 2026-09-23: llama-server defaults to 8080 and BACKENDS above
# expects 8099, so this command, run as written, served where this script never looks. Found
# while writing run_queue.py, which starts the server from this string. No LLAMA_ARG_PORT is set.
# -np 1 is not a tidiness flag. llama-server defaults to four slots and allocates compute
# buffers per slot; at 64K that pushed the total past 16 GB, the driver spilled to system
# memory WITHOUT failing, and decode fell to 14.6 tok/s while prefill fell 6x. nvidia-smi
# still reported free VRAM throughout, because spilled memory is not counted. One slot is
# what makes 64K fit.

# --no-mmap is a memory fix, not a speed flag, and it is the difference between this machine
# having 4 GB of headroom while the server runs and having 17. llama.cpp maps the GGUF by
# default and the mapped pages stay RESIDENT for the life of the process even though every
# weight has already been uploaded to VRAM. Measured 2026-09-02, same model and flags, one
# variable changed:
#
#     mmap (default)   working set 13.94 GB, system RAM 27.51 of 31.11 GB (88.4%)
#     --no-mmap        working set  1.27 GB, system RAM 13.84 of 31.11 GB (44.5%)
#
# Nothing is traded at inference. VRAM was 15.03 GB against 15.02, eval ran 37.75 tok/s, and
# MTP still drafted (acceptance 0.806, mean len 1.81). Only a COLD load should pay, to read
# 14.25 GB rather than map it - and that cost is NOT measured here, because the file was
# already in the OS cache both times. Do not quote a load-time figure from this.
#
# The trap worth remembering is the instrument, not the flag. PRIVATE BYTES DO NOT SHOW THIS:
# they read 17.52 GB against 17.54, because they count committed address space rather than
# resident pages. `\Memory\Cache Bytes` does not show it either - it measures the system
# cache, not a process's mapped views, and reading 0.29 GB there was briefly taken as proof
# that mmap was NOT the cause. Only the A/B settled it. Working set is the number that moves.

# Short names for the models configured on this machine, so a caller does not have to remember
# which tag carries the Headroom system prompt and which is the stock upstream one.
#
# "coder" -> qwen3-coder-headroom and "coder-stock" -> qwen3-coder:30b were removed 2026-09-08
# when both models were deleted to reclaim 17 GB. A short name pointing at a model that is not
# installed fails inside Ollama with a pull attempt rather than an argument error, which is a
# worse failure than not offering the name at all.
MODELS = {
    "qwen38": "qwen38-headroom",
    "qwen38-iq4": "qwen38-iq4",
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

# Sampling, sent explicitly on BOTH backends rather than left to whatever each one defaults to.
# These are the values the Ollama Modelfiles bake in, so results stay comparable with every
# spec-suite run recorded before the llama.cpp switch. A bare GGUF under llama.cpp would
# otherwise sample at the server's defaults and quietly stop being the same experiment.
SAMPLING = {"temperature": 0.7, "top_k": 20, "top_p": 0.8}
HERE = Path(__file__).resolve().parent
REQUEST_CONTEXT = None


def jsonSafe(value):
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, dict):
        return {key: jsonSafe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [jsonSafe(item) for item in value]
    return value


def appendConsoleEvent(event):
    """Append one visible request event; closing each write makes chunks promptly readable."""
    folder = HERE / "runs" / "console"
    folder.mkdir(parents=True, exist_ok=True)
    day = datetime.now(timezone.utc).strftime("%Y%m%d")
    with (folder / f"requests-{day}.jsonl").open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(jsonSafe(event), ensure_ascii=False, allow_nan=False) + "\n")


def isoNow():
    return datetime.now(timezone.utc).isoformat()


def readModelContext(model):
    """The context the model was actually loaded with, read from the server rather than assumed.

    This is the number that decides whether a long deliberation has room to reach an answer. On
    Ollama it comes from the Modelfile; on llama.cpp it is fixed at launch by -c, so a caller
    cannot raise it without restarting the server.
    """
    if BACKEND == "llamacpp":
        try:
            props = json.load(urllib.request.urlopen(f"{HOST}/props", timeout=60))
        except urllib.error.URLError as error:
            raise SystemExit(f"Cannot reach llama-server at {HOST}: {error}\n\n"
                             f"Start it with:\n  {SERVER_COMMAND}")
        context = (props.get("default_generation_settings") or {}).get("n_ctx")
        if not context:
            raise SystemExit(f"{HOST}/props reported no n_ctx. Is that really llama-server?")
        return int(context)

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


def looksLikeProseAndCode(text):
    """True when a reply is commentary AND code rather than code.

    stripFences declines to unwrap anything that is not one single fenced block, which is the
    right call - but it did so silently, so a reply that opened with a paragraph of reasoning
    before its fenced block was written straight out as a file that does not parse, with the run
    reported as clean. A surviving fence at the start of any line means unwrapping did not
    happen, whether because prose came first or because there was more than one block.
    """
    return bool(re.search(r"^```", stripFences(text), re.MULTILINE))


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


def rate(count, durationNs):
    """Tokens per second from a count and a nanosecond duration.

    Ollama reports durations; llama.cpp reports rates directly, so this is only used on the
    Ollama path. It stays at module level because it is pure and has its own tests.
    """
    return count / (durationNs / 1e9) if durationNs else float("nan")


def ask(model, system, user, think, numPredict, timeout, sampling, seed,
        *, stream=False, onEvent=None):
    """Send the task and return a backend-independent result dict.

    The two backends disagree on every field that matters - content, stop reason, token counts,
    rates - so they are normalised here rather than at each use site. Everything downstream then
    reads one shape, and a third backend would touch only this function.
    """
    messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    if BACKEND == "llamacpp":
        endpoint = "/v1/chat/completions"
        payload = {"model": model, "messages": messages, "max_tokens": numPredict,
                   "stream": bool(stream), "seed": seed,
                   # Qwen3.8 reasons by default. llama.cpp puts that in reasoning_content rather
                   # than in content so it cannot corrupt the file, but it is still charged
                   # against max_tokens, so it stays off unless asked for.
                   "chat_template_kwargs": {"enable_thinking": bool(think)},
                   **sampling}
        if stream:
            payload["stream_options"] = {"include_usage": True}
    else:
        endpoint = "/api/chat"
        payload = {"model": model, "messages": messages, "stream": False, "think": think,
                   "keep_alive": "30m",
                   "options": {"num_predict": numPredict, "seed": seed, **sampling}}

    request = urllib.request.Request(f"{HOST}{endpoint}", data=json.dumps(payload).encode(),
                                     headers={"Content-Type": "application/json"})
    started = time.time()
    if BACKEND == "llamacpp" and stream:
        reasoningParts, answerParts, toolCalls = [], [], []
        stopReason, usage, timings, done = None, {}, {}, False
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                for event in iter_sse_events(response):
                    kind = event["type"]
                    if kind == "reasoning":
                        reasoningParts.append(event["text"])
                    elif kind == "answer":
                        answerParts.append(event["text"])
                    elif kind == "tool_calls":
                        toolCalls.extend(event["value"])
                    elif kind == "finish":
                        stopReason = event["reason"]
                    elif kind == "stats":
                        usage.update(event["usage"])
                        timings.update(event["timings"])
                    elif kind == "done":
                        done = True
                    if onEvent and kind in ("reasoning", "answer"):
                        onEvent(event)
        except (OSError, ValueError, RuntimeError) as error:
            raise SystemExit(f"Request to {HOST}{endpoint} failed: {error}") from error
        if not done or stopReason is None:
            raise SystemExit(f"Request to {HOST}{endpoint} ended before a final finish reason.")
        return {
            "content": "".join(answerParts), "reasoning": "".join(reasoningParts),
            "stopReason": stopReason, "toolCalls": toolCalls or None,
            "promptTokens": usage.get("prompt_tokens"),
            "outputTokens": usage.get("completion_tokens"),
            "promptRate": timings.get("prompt_per_second", float("nan")),
            "outputRate": timings.get("predicted_per_second", float("nan")),
        }, time.time() - started
    try:
        response = json.load(urllib.request.urlopen(request, timeout=timeout))
    except urllib.error.URLError as error:
        raise SystemExit(f"Request to {HOST}{endpoint} failed: {error}")
    wall = time.time() - started

    if BACKEND == "llamacpp":
        choice = response["choices"][0]
        message = choice.get("message", {})
        usage = response.get("usage", {})
        timings = response.get("timings", {})
        return {
            "content": message.get("content") or "",
            "reasoning": message.get("reasoning_content") or "",
            # llama.cpp reports "length" for the token cap exactly as Ollama does, so the
            # truncation check downstream needs no backend branch.
            "stopReason": choice.get("finish_reason"),
            "toolCalls": message.get("tool_calls"),
            "promptTokens": usage.get("prompt_tokens"),
            "outputTokens": usage.get("completion_tokens"),
            "promptRate": timings.get("prompt_per_second", float("nan")),
            "outputRate": timings.get("predicted_per_second", float("nan")),
        }, wall

    message = response.get("message", {})
    return {
        "content": message.get("content") or "",
        "reasoning": message.get("thinking") or "",
        "stopReason": response.get("done_reason"),
        "toolCalls": message.get("tool_calls"),
        "promptTokens": response.get("prompt_eval_count"),
        "outputTokens": response.get("eval_count"),
        "promptRate": rate(response.get("prompt_eval_count", 0),
                           response.get("prompt_eval_duration", 0)),
        "outputRate": rate(response.get("eval_count", 0), response.get("eval_duration", 0)),
    }, wall


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("spec", help="Path to the task specification.")
    parser.add_argument("--context", action="append", default=[],
                        help="File to include before the spec. Repeatable.")
    parser.add_argument("--backend", default="llamacpp", choices=sorted(BACKENDS),
                        help="Which local server to talk to. Default llamacpp.")
    parser.add_argument("--host", help="Override the backend's default URL.")
    parser.add_argument("--model", default="qwen38",
                        help=f"Ollama only: short name {sorted(MODELS)} or a full tag. "
                             f"llama-server serves whichever GGUF it was launched with, so this "
                             f"is ignored there.")
    parser.add_argument("--out", help="Where to write the reply. Default: <spec>.out.py")
    parser.add_argument("--system", help="Replace the default no-tools system message.")
    parser.add_argument("--think", action="store_true",
                        help="Allow reasoning. Off by default; see item 3 in the docstring.")
    parser.add_argument("--num-predict", type=int, default=2000,
                        help="Output token cap.")
    parser.add_argument("--timeout", type=int, default=1800, help="Seconds.")
    parser.add_argument("--temperature", type=float, default=SAMPLING["temperature"],
                        help="Sent explicitly to both backends so the backend cannot change it.")
    parser.add_argument("--top-k", type=int, default=SAMPLING["top_k"])
    parser.add_argument("--top-p", type=float, default=SAMPLING["top_p"])
    parser.add_argument("--seed", type=int, default=-1,
                        help="-1 for a random draw. Set it to make one run reproducible; do NOT "
                             "set it across repeats, or every repeat returns the same sample and "
                             "n=3 measures nothing.")
    parser.add_argument("--raw", action="store_true", help="Do not strip a wrapping code fence.")
    parser.add_argument("--force", action="store_true",
                        help="Send even when the context budget check says it will not fit.")
    parser.add_argument("--append",
                        help="On success, also append the reply to this file. Refused if the "
                             "run had problems.")
    parser.add_argument("--request-id", help="Shared request id for a queue acceptance event.")
    parser.add_argument("--queue-name", help="Queue name for the console request log.")
    parser.add_argument("--job", help="Queue job id for the console request log.")
    parser.add_argument("--attempt", type=int, help="Queue attempt for the console request log.")
    args = parser.parse_args()

    global BACKEND, HOST
    BACKEND = args.backend
    HOST = args.host or BACKENDS[BACKEND]

    model = MODELS.get(args.model, args.model)
    system = args.system or DEFAULT_SYSTEM
    user = buildUserMessage(args.spec, args.context)

    global REQUEST_CONTEXT
    requestId = args.request_id or uuid.uuid4().hex
    plannedOutput = Path(args.out) if args.out else Path(args.spec).with_suffix(".out.py")
    REQUEST_CONTEXT = {"request_id": requestId, "output_path": str(plannedOutput.resolve()),
                       "timings": {}, "done_reason": None, "error": None,
                       "output_written": False}
    appendConsoleEvent({"type": "request_start", "time": isoNow(), "request_id": requestId,
                        "spec_path": str(Path(args.spec).resolve()),
                        "context_paths": [str(Path(path).resolve()) for path in args.context],
                        "queue_name": args.queue_name, "job": args.job, "attempt": args.attempt,
                        "backend": BACKEND, "host": HOST,
                        "sampling": {"temperature": args.temperature, "top_k": args.top_k,
                                     "top_p": args.top_p, "seed": args.seed,
                                     "num_predict": args.num_predict, "think": args.think},
                        "system": system, "user": user})

    contextLimit = readModelContext(model)
    estimated = int((len(system) + len(user)) / CHARS_PER_TOKEN)
    print(f"backend          {BACKEND} at {HOST}")
    print(f"model            {model if BACKEND == 'ollama' else 'as loaded by llama-server'}")
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

    sampling = {"temperature": args.temperature, "top_k": args.top_k, "top_p": args.top_p}
    print(f"sampling         temp {args.temperature} top_k {args.top_k} top_p {args.top_p} "
          f"seed {args.seed}")
    def recordChunk(event):
        appendConsoleEvent({"type": event["type"], "time": isoNow(),
                            "request_id": requestId, "text": event["text"]})

    result, wall = ask(model, system, user, args.think, args.num_predict, args.timeout,
                       sampling, args.seed, stream=(BACKEND == "llamacpp"),
                       onEvent=recordChunk)
    if BACKEND != "llamacpp":
        for kind, text in (("reasoning", result["reasoning"]), ("answer", result["content"])):
            if text:
                recordChunk({"type": kind, "text": text})
    REQUEST_CONTEXT["timings"] = {"wall_seconds": wall,
                                   "prompt_tokens": result["promptTokens"],
                                   "output_tokens": result["outputTokens"],
                                   "prompt_tok_s": result["promptRate"],
                                   "output_tok_s": result["outputRate"]}
    REQUEST_CONTEXT["done_reason"] = result["stopReason"]
    reply = result["content"]

    print(f"\nwall             {wall:.1f}s")
    print(f"prompt           {result['promptTokens']} tokens @ {result['promptRate']:.0f} tok/s")
    print(f"output           {result['outputTokens']} tokens @ {result['outputRate']:.1f} tok/s")
    print(f"stop reason      {result['stopReason']}")
    if result["reasoning"]:
        print(f"reasoning        {len(result['reasoning'])} chars, kept out of the file")

    problems = []
    # "length" means the cap or the context ran out, so the tail of the answer does not exist.
    # Reported as a failure rather than a note: a truncated file is not a shorter file.
    if result["stopReason"] == "length":
        problems.append("TRUNCATED: hit the output cap or the context limit. The reply is "
                        "incomplete - raise --num-predict or shorten the prompt.")
    if result["toolCalls"]:
        problems.append("The model returned structured tool_calls instead of an answer.")
    marker = findToolCall(reply)
    if marker:
        problems.append(f"The reply contains {marker!r}: the model tried to call a tool that "
                        f"was never offered, rather than answering. Check the system message.")
    if not reply.strip():
        problems.append("Empty reply.")
    # stripFences hands back the WHOLE reply when it is not one single fenced block, which is
    # the right call - but silently, so a reply of "here is my reasoning" followed by a fenced
    # block was written out as a file that does not parse, with the run reported as clean.
    if not args.raw and looksLikeProseAndCode(reply):
        problems.append("The reply is prose AND code, not code: it does not start with a fenced "
                        "block, so nothing was unwrapped and the file will not parse. Usually a "
                        "spec that invited commentary - check for an instruction to explain, or "
                        "to open a file the model cannot reach.")

    outPath = Path(args.out) if args.out else Path(args.spec).with_suffix(".out.py")
    outPath.write_text(reply if args.raw else stripFences(reply), encoding="utf-8")
    REQUEST_CONTEXT["output_written"] = True
    print(f"written          {outPath}")

    if problems:
        REQUEST_CONTEXT["error"] = "; ".join(problems)
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


def runLoggedMain():
    global REQUEST_CONTEXT
    try:
        return main()
    except BaseException as error:
        if REQUEST_CONTEXT and not REQUEST_CONTEXT.get("error"):
            REQUEST_CONTEXT["error"] = str(error)
        raise
    finally:
        if REQUEST_CONTEXT:
            appendConsoleEvent({"type": "request_end", "time": isoNow(), **REQUEST_CONTEXT})
            REQUEST_CONTEXT = None


if __name__ == "__main__":
    sys.exit(runLoggedMain())
