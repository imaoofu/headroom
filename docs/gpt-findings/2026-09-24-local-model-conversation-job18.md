# Local Model Console conversation view (Job 18)

**Task.** Review the completed Job 17 console and build Job 18 from
`docs/agents/GPT-PROMPT-NEXT.md`: a live conversation view for Agent runs and Claude
requests, including partial Claude Code messages. Improve the Chat page to match.

**Built.** `tools/local-model/console/assembly.py` converts complete JSONL lines into
incremental events with ending byte offsets. It joins fragmented thinking, text, and
tool JSON, reconciles final assistant messages with streamed blocks, attaches tool
results, and accepts older whole-message transcripts. System progress rows become a
count. The server retains per-viewer assembly state across byte-offset reads. The
page appends deltas to existing conversation nodes. It shows a prompt, open thinking
while it streams, collapsed thinking and tool results afterward, answer text, final
duration/turns/errors, and request acceptance. The Chat tab has the same visual style.
Its request list is newest first. Scrolling up stops automatic following until
**Jump to live** is selected.

Active visible viewers poll at 500 ms, idle viewers at 5 s. A hidden tab does not
poll; a measurement pauses polling until **Check if finished** is selected. The
server still binds to loopback, confines file reads to its configured roots, refuses
chat and model start during measurement, and can stop only its own model process.
The page has no external assets; the server now sends a restrictive content security
policy for the page and `nosniff` headers for page and file responses.

**Evidence.** The recorded five-turn partial fixture
`tools/local-model/console/fixtures/claude-code-local-partial.jsonl` has SHA-256
`95AA96CD2C4EEE42E16AA896EE4E25A468B50910423C124A1B8EEE53C1744572`.
The assembly test compares each turn's thinking, answer, and decoded tool input with
the fixture's complete assistant messages. A synthetic case splits tool JSON across
deltas and resumes a transcript cut mid-line and mid-block; the returned offsets
produce no duplicate content. The older non-partial failure fixture still renders.
Request tests cover event order and thinking time across polls. All 19 console tests
pass. A mock-only server and Edge screenshot pass exercised the Chat, Claude requests,
and Agent runs tabs; no real model or GPU call was involved. Inline JavaScript syntax,
Python compilation, and `git diff --check` pass. The full suite reports **1,024
checks across 33 suites**; the claims audit, data manifest check, and citation check
exit successfully.

**Limits.** Claude Code's stream JSON can omit the original command-line prompt;
the recorded fixture does. The viewer shows a prompt from a user text message or an
optional adjacent `.jsonl.prompt.txt` file; otherwise it labels the prompt
unavailable. The recorded partial stream has no per-delta timestamps, so historical
thinking duration is unknown. A live displayed duration is approximate; Claude
request timing spans request start to first answer. The revised page has not been
tested against a running local model or a new live Claude Code run. No llama-server
was started, no model was loaded, no sweep was run, no `data/` file was changed, and
no commit was made. Claude and Raymond can supervise the live integration check.

## Claude's review, 2026-09-24: run live, accepted, no code changes

**Live run.** The console was restarted on this code and watched a real Claude Code job on the
local model with `--include-partial-messages`: add `median()` to a sandbox `stats.py`, write a
check and run it. 7 turns, 75.1 s, success. The job's work was checked independently: the check
script passes and the caller's list is not modified.

**Seen live, in the browser pane (the same page Raymond had open in Edge):**
- the prompt bubble, from the `.jsonl.prompt.txt` sidecar;
- an open **Thinking…** block filling in as the model wrote it, which folded to
  "Thought for ~N s" when the turn moved on;
- a tool card whose arguments were marked **streaming** while they arrived;
- tool results attached under their cards, then the final answer and a result card.

**Checked by hand:**
- The recorded fixture assembles to 5 turns and 4 tool calls. Feeding it one line at a time gives
  the same text as feeding it at once.
- The page never uses `innerHTML`, so model text cannot inject markup.
- Polling is 500 ms while running, 5 s idle, and off while the tab is hidden.
- 19 console tests pass.

**Small things, none blocking:**
- **Tool arguments are replaced once at the end of each tool call.** The finished message has the
  same input, re-serialised with spaces and with `replace_all` added. The card shows the streamed
  text, then the re-serialised form. Cosmetic.
- **The prompt needs the sidecar.** Claude Code does not write its `-p` prompt into the stream.
  Claude writes `<transcript>.prompt.txt` beside every agent run from now on.
- **At a very narrow window (~265 px) the header scrolls sideways**, and after the pane was
  resized, **Jump to live** appeared although nobody had scrolled. Following probably treats the
  scroll event from a reflow as the user scrolling up. Not seen at normal width.
