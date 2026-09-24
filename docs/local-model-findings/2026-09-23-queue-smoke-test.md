# Queue smoke test, 2026-09-23: one attempt of L3 before the unattended day

**What ran.** `run_queue.py` with `queue-smoke-20260923.json`: one attempt of L3, the numbers
inventory (`specs/numbers-inventory-unaudited.md`), the evening before the full queue. The purpose
was to prove the pipeline, not the model.

## The pipeline: ✅ works end to end

- `llama-server` started from `SERVER_COMMAND`, became healthy after about 20 s, and was stopped
  afterwards. The card went back to 649 MB used.
- `ask_local.py` returned an answer in 70.9 s, at ~35 tok/s.
- The acceptance script ran on it and wrote its report.

⛔ **The smoke test found a defect in the project's own record, before it cost a day.**
`SERVER_COMMAND` in `ask_local.py` had no `--port`. llama-server defaults to 8080, while
`ask_local.py` talks to 8099 and no `LLAMA_ARG_PORT` is set on this PC. Run as written, the command
served where the script never looks. It was fixed (`--port 8099`) before this run, and the healthy
server confirms the fix. Whoever started the server by hand before must have supplied the port
themselves.

## The answer: ❌ failed acceptance, 34 of 40 rows clean

It produced 40 rows for 40 expected numbers. Every row outside §5.7's table passed: the quote was
verbatim and contained its number. **All six failures are the six numbers inside §5.7's Markdown
table.** For those, the model quoted across cells, so each row gained one or two extra `|`
separators. One of them quoted `(compute-bound)`, a cell with no number in it.

**Whose error:** shared, and the larger part is Claude's. The spec said how to escape a `|` but
never said that §5.7 contains a table, or how to quote from one. **The spec was amended the same
night** (one cell, exactly six cells per row). This record keeps what the model did with the
original.

**Not reviewed:** the `what it is`, `kind` and `likely source` columns. Spot-read, they look
plausible but conservative: most sources are `unknown`. That is what the spec asked for, and it
also means the column adds little.

n = 1 attempt. It says nothing about the model's reliability on this job; the full queue runs it
three times.
