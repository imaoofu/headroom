# The local model as a Claude Code agent: job L1 again, 2026-09-24

**Question:** can the local model (Qwen3.8 27B `UD-IQ4_XS`, llama.cpp, 64K context) do a job better
as an **agent with tools** than as a single-shot answer? Raymond's goal is for it to take a role like
GPT's.

**Setup.**
- Claude Code 2.1.233, headless (`claude -p`), pointed at llama-server via `ANTHROPIC_BASE_URL`.
  llama-server serves Anthropic's Messages API natively; that was verified with a direct request
  first.
- A sandbox outside the repository, `C:\Users\Raymond\Documents\local-agent-sandbox\L1-decoder`:
  - the **pre-L1** decoder and its tests, from git at `bb4a1d1^`;
  - the profile snapshots, **without** the 3070 Ti README that holds the answer table;
  - the same L1 spec, with "you have no tools" replaced by "you can read, edit and run Python";
  - a short CLAUDE.md: stay in the folder, never edit `data/`, verify by running.
- Tools allowed: `Read, Edit, Write, Glob, Grep, Bash(python:*)`. No MCP. At most 60 turns.
- Scored afterwards with the **same hidden acceptance script** as the single-shot attempts
  (`tools/local-model/specs/accept_decoder_3slot.py`).

## First it did not run at all, and the fix was a chat template

Every request returned HTTP 500 from the model's own Jinja template: *"System message must be at the
beginning."* The template merges system messages at the start of a conversation and **raises on any
later one**, and Claude Code sends system content later.
- **Reproduced directly:** a chat of system, user, assistant, system, user gave the same 500 on the
  original template.
- **Fixed** in `tools/local-model/qwen-chat-template-claude-code.jinja`, a one-line change: render a
  late system message as a system block instead of raising. With it, the same request returned 200
  and an ordinary request still answered normally.
- **Loaded with** `--jinja --chat-template-file <that file>` on top of `SERVER_COMMAND`.
- The failed run's transcript is kept as a fixture for the Job 17 console
  (`tools/local-model/console/fixtures/claude-code-local-L1-apierror.jsonl`).

## Result: ✅ 15 of 15, but it ran out of context before its closing summary

- **What it did:** 29 assistant messages over 13 turns and 16.9 minutes; 4 reads, 3 Python commands,
  **5 edits**.
- **How it ended:** it stopped on `API Error: 400: request (73370 tokens) exceeds the available
  context size (65536)`. Reading the ~20 KB hex profile file was the largest single cost.
- **What it left was complete:**
  - the hidden acceptance check passes **15 of 15**;
  - `analysis/test_decode_profiles.py` still passes.
- **It did not make the single-shot attempt's mistake.** It skips an empty `VFCurve` only in
  lenient mode, so the default behaves exactly as before. The single-shot L1 attempt 1 changed the
  default, and review had to fix it.

| | single-shot (2026-09-24 queue) | agent with tools |
|---|---|---|
| attempts / passing the hidden check | 3 / **1** | 1 / **1** |
| failure shapes | stopped after one sentence; prose around code | ran out of context after finishing the code |
| defect review found in the passing answer | changed the default mode | none found so far |
| wall time | 107 s | 17 min |

⚠️ **n = 1 agent run.** That is one success, not a rate. It is not yet reviewed line by line the way
the installed L1 decoder was, and it is **not** installed; the committed decoder is the reviewed
single-shot version.

**What this says about the role Raymond wants for it:**
- **Tools helped quality:** it could run the code and read the real file.
- **Context is the binding limit, as predicted.** 64K is the most that fits beside the model on 16 GB.
  A job must fit its reading into that budget, so the next specs should point it at the few lines
  it needs rather than whole data files.
- **It still never runs beside a sweep on this card.**

## Run 4, with a context rule: ✅ 15 of 15 again, and out of context again

The sandbox CLAUDE.md gained one rule after run 3: never Read a `.cfg` store whole, inspect it with
short `python -c` commands instead. Same model, template, task, tools and hidden check.

| | run 3 | run 4 (context rule) |
|---|---|---|
| hidden check | **15 / 15** | **15 / 15** |
| sandbox tests (`test_decode_profiles.py`) | pass | pass |
| turns / assistant messages | 13 / 29 | 35 / 74 |
| tool calls | 4 Read, 3 Bash, 5 Edit | 4 Read, **15 Bash**, 10 Edit, 5 task-list |
| wall time | 16.9 min | 17.8 min |
| how it ended | out of context, 73,370 tokens | out of context, **65,612** tokens |

- **The rule was obeyed, and it moved the cost rather than removing it.** Run 4 inspected the
  stores through short Python commands, as told. It then spent the saved context **verifying**:
  15 Bash commands, most of them checks of its own finished code. It ran out during that pass,
  76 tokens over the limit.
- **The code was already complete when it stopped**, as in run 3. The result is kept beside the
  sandbox as `L1-run4-decoder-result.py`.
- **3 commands were refused by the permission list** (`Bash(python:*)`). Two began with `echo`.
  The third was a `python -c` whose file path contains `&`, which the harness probably read as a
  command separator. That is an inference; the transcript records only the refusal. The model
  carried on after each.

⚠️ **n = 2 agent runs, 2 of 2 passing the hidden check, 2 of 2 ending out of context.** The pass
rate is two successes, not a rate. The failure mode is now consistent.

**What to change for the next agent job, before running it:**
- **Budget the verification, not only the reading.** Tell it how many checks to run and to print
  only the verdict lines, since each command's output stays in context.
- **Or give it more room.** A smaller quant would leave VRAM for a longer context, or the job can be
  split into sessions that each start fresh. Neither has been tried.
- **Allow `echo`**, and avoid `&` in file paths the model has to type, or point it at a copy.
