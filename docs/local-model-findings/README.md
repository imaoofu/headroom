# Local-model findings

Raymond asked for this archive on 2026-09-23, beside `docs/gpt-findings/`. It records what the
local model (Qwen3.8 27B `UD-IQ4_XS` on llama.cpp, `tools/local-model/`) was asked to do, what it
returned, and **what review found**. It is a research record, not an authority. Nothing the model
returns is used until it has been run and reviewed. Its jobs are listed in
`docs/agents/LOCAL-MODEL-TODO.md`.

**The model has no tools.** It sees one spec and the files passed with `--context`, and it returns
text. So every job is mechanical and bounded, and has a check written before the model sees it.
Each record keeps two kinds of error apart:
- **errors in the model's answer**;
- **errors in the spec or the check**, which were Claude's. Two earlier specs contained errors of
  their own (`tools/local-model/README.md`).

⚠️ **A PASS from an acceptance script is not a review.** It proves the answer meets what the script
checks, which is never everything. The record says what the review added.

| Date | Job | Result | Review |
|---|---|---|---|
| 2026-09-24 | [L1 decoder, L2 fine-pair comparison, L3 numbers inventory](2026-09-24-queue-L1-L3.md) | 5 of 9 attempts passed acceptance; every failure was reply shape (a one-sentence stop, prose around code, one misquote), none a wrong answer | ✅ L1 and L2 accepted, each after one fix the checks could not see (a changed default; an unrequired key column), with tests added. L3's facts accepted, its classification not; it shows §5.4.2 has nothing to pin and that ~11 of 40 extracted "numbers" are extractor artifacts |
| 2026-09-23 | [Queue smoke test: one L3 attempt](2026-09-23-queue-smoke-test.md) | Pipeline ✅ end to end; the answer ❌ failed acceptance, 34 of 40 rows clean, all six failures in §5.7's table | Found `SERVER_COMMAND` missing `--port 8099` (fixed). The failures are mostly a spec gap (the table was never mentioned), amended the same night |

## Saving a result

Use `YYYY-MM-DD-short-topic.md`, one per job. Each record gives:
- the spec, the context files and the queue;
- every attempt's acceptance verdict, with n (attempts are not independent draws of a fixed
  quality; they share the spec);
- what review checked beyond the acceptance script;
- what was accepted, changed or rejected, and why;
- errors found in the spec or check.

Keep the model's failures. **A job it cannot do is a finding about delegation, not something to
retry until it passes.**
