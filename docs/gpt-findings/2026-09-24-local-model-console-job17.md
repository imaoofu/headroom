# Local Model Console (Job 17)

**Task.** Build the loopback console described in `docs/agents/GPT-PROMPT-NEXT.md`:
local-model chat and logs, Claude request stream, agent transcript and queue viewers,
measurement status, and owned model start/stop controls.

**Built.** `tools/local-model/console/server.py` serves a single local page on
`127.0.0.1:8098`. It reads model health from the URL in `ask_local.BACKENDS`, reads GPU
memory and utilization with one `nvidia-smi` query per status request, and calls
`run_queue.measurement_running()` for the red measurement state. Chat and model start
refuse during a measurement. The page pauses its viewer polls while that state shows
and all polls while hidden. The page has no external assets. The server can stop only
the model process it started. Readable files are confined to resolved paths under the
two configured roots.

`ask_local.py` now streams llama.cpp replies through `streaming.py` and appends full
request, reasoning, answer, and end events to `runs/console/requests-YYYYMMDD.jsonl`.
`run_queue.py` tags queue requests and records acceptance verdicts. Chat exchanges,
including failures, go to `runs/console/chat-YYYYMMDD.jsonl`. These logs contain full
prompts and are Git ignored. `OPEN-CONSOLE.bat` launches the page in Edge app mode with
a default-browser fallback. `tools/local-model/console/README.md` records operation
and the configurable transcript roots.

**Verification.** `tools/local-model/test_console.py` passes 11 mock-only checks.
The supplied Claude Code failure fixture yields 10 retries, 0 tool calls, and a final
error containing "System message must be at the beginning". A fake SSE server verifies
event order and byte-identical output against the nonstreaming write path; another
fake stream verifies a final error record after interruption. Tests also cover
transcript blocks, a partial byte-offset tail, malformed lines, traversal refusal,
measurement start refusal, owned-process stop, duplicate-server refusal, queue
acceptance logging, and chat failure logging. The existing 48 `ask_local` checks
pass. `python run_tests.py --quiet` reports **1,016 checks across 33 suites**;
`audit_claims.py`, `build_data_manifest.py --check`, and
`verify_citations.py --check` exit successfully. Python compilation, inline
JavaScript syntax, and `git diff --check` pass.

**Limits.** The page, Edge launcher, actual llama.cpp stream, GPU status query, and
process ownership have not been exercised live. No llama-server was started, no model
was loaded, no sweep was run, and no `data/` file was changed. A supervised live run
with Raymond and Claude is needed to check those integration points. No commit was
made for this job.

## ✅ Reviewed by Claude, 2026-09-24: accepted after a live run, with three fixes and one change

**Read in full:** `streaming.py`, the `ask_local.py` and `run_queue.py` diffs, and the server's
security path (loopback bind, resolved-prefix confinement, Host/Origin check on POST, owned-PID stop).
All 11 checks, the 48 `ask_local` checks and the full suite pass.

**Run live** in the browser pane and in an Edge app window, with the patched llama-server loaded:
- the status bar read VRAM 15,723 / 16,311 MiB;
- a chat streamed its reasoning live and was logged to `chat-YYYYMMDD.jsonl`: 7,028 characters of
  reasoning, 1,556 tokens at 41.8 tok/s. **The real stream carries the `timings` fields the code
  relies on;**
- an `ask_local` job streamed and was logged (34 tokens at 48.6 tok/s, correct output);
- a real 2.2 MB Claude Code transcript loaded in the agent viewer.

**Found only by running it, each fixed with a test that fails on the unfixed code:**
1. ⛔ **The Claude requests tab showed 0 while the log held a request.** On Windows the transcript list
   returned `console\requests-…` and the page filters on `console/requests-`. Paths are now
   `as_posix()`, in the list and in the queue links. The mocked tests could not see it: every
   fixture path was built on the same OS.
2. ⛔ **The agent viewer listed 10,047 `system/thinking_tokens` rows** around 42 real events (a real
   Claude Code run on the local model). System events other than init and retry are now `progress`,
   counted in the pill beside retries.
3. **The Agent runs tab opened empty**, so Raymond could not find the running job. It now selects the
   most recently written transcript and marks it "(newest)". The list carries `mtime`.

**And one change outside the job:** `SERVER_COMMAND` now loads
`qwen-chat-template-claude-code.jinja`, so a model started by the console, or by `run_queue.py`,
serves Claude Code without the HTTP 500s. See `docs/local-model-findings/2026-09-24-claude-code-harness-L1.md`.

**Carried into Job 18, not fixed here:**
- the status poll runs `measurement_running()`, which spawns PowerShell, every 2 s even during a
  sweep;
- `ask_local` writes one log line per streamed chunk;
- the viewer is a transcript, where Raymond wants a live conversation.
