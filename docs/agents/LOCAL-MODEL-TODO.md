# Local model: to-do list

**Written 2026-09-23 by Claude, at Raymond's request, to use the 5060 Ti's idle day (2026-09-24)**
while the 3070 Ti runs Session D. It is the local counterpart of `GPT-PROMPT-NEXT.md`. Results and
their reviews go in `docs/local-model-findings/`.

## Why this model gets different jobs from GPT

GPT can browse, read the repository and run code. The local model (`tools/local-model/`) **has no
tools**: it reads one spec plus the files passed with `--context`, and returns text, at ~40 tok/s
with 64K context. So its jobs must be:
- **mechanical**: a specified function, file or table, not open research;
- **self-contained**: every fact it needs is in the prompt;
- **checkable exactly**: each job has an acceptance script, written and verified by Claude
  **before** the model sees the task. A correct answer was run through each script and passed, and
  a broken one failed.

## 🛑 Before running anything

**The model runs on the 5060 Ti, the card the research measures.** It holds ~15 GB of the card's
16 GB at ~0% utilisation, which only the free-VRAM guard can see (`tools/local-model/README.md`).
`run_queue.py`:
- refuses to start if a sweep, suite or bench session is running;
- stops the server it started when the queue ends.

**Never run it during a 5060 Ti sweep.** The 3070 Ti is a different PC, so running tomorrow is
fine.

## How Raymond starts it, before leaving

In the repository folder (`C:\Users\Raymond\Documents\headroom`):

```
python tools/local-model/run_queue.py tools/local-model/queue-20260924.json
```

The runner:
1. starts `llama-server` from `SERVER_COMMAND` in `ask_local.py`;
2. waits up to 15 min for the model to load;
3. runs 3 jobs × 3 attempts;
4. checks every answer with its acceptance script;
5. writes `tools/local-model/runs/queue-20260924/summary.md`;
6. stops the server.

The whole queue should take well under an hour of the 8. It needs no input.

## The queue, 2026-09-24 — ✅ RUN AND REVIEWED the same day

Result: 5 of 9 attempts passed; L1 and L2 installed after review, L3 kept as a record. See
`docs/local-model-findings/2026-09-24-queue-L1-L3.md`.

| id | job | why now | exact check |
|---|---|---|---|
| **L1** | Teach `tools/afterburner/decode_profiles.py` to read the 3070 Ti's 3-slot store (with its nonzero tail), and add an opt-in **next-record pairing**. Existing behaviour and tests unchanged | The committed decoder refuses the 3070 Ti file, so its table was decoded by hand (ROADMAP open item 5) | `accept_decoder_3slot.py`: all 14 rows × 3 slots of the hand-decoded table; default behaviour unchanged on the 5060 Ti snapshots; CLI. 15 checks |
| **L2** | Write `analysis/compare_fine_pair.py`: per-point throughput, power, efficiency and temperature differences between two sweeps. It reports differences and attributes none | REGISTERED-PREDICTIONS §8c (the ascending/descending pair) needs exactly this after Session D | `accept_compare_fine_pair.py`: C8 against 2026-08-27, per-point deltas to 0.006 points, argmax 1500/1455, duplicate-target refusal. 12 checks |
| **L3** | Inventory the **40 numbers** in the three paper sections with numbers and no claims (§5.4.2, the §5.7 introduction, §5.7.7): quote, meaning, kind, likely source | Groundwork for pinning them. ROADMAP says §5.4.2 "may have little to pin" (it has 1 number) and that should be a finding, not an assumption | `accept_numbers_inventory.py`: the numbers must equal the claims auditor's own extraction, one for one; every quote verbatim in the paper |

**After the queue (Claude, when Raymond is back):**
1. Read `summary.md`, then **review every PASSED answer by reading it**.
   - L1: copy it over the real decoder in a clean tree and run `analysis/test_decode_profiles.py`
     and the full suite.
   - L2: add tests before committing.
   - L3: judge the "kind" and "likely source" columns, which the script cannot.
2. Write one record per job in `docs/local-model-findings/`, keeping failed attempts and any error
   in Claude's own spec or check.
3. Commit only what review accepts, with the review in the commit message.

## Candidates for later queues, not yet specced

A job goes into a queue only once its spec and acceptance check exist and have been run against a
correct answer.
- Draft claims for §5.7.7 from the L3 inventory. The check is `audit_claims.py` itself.
- Tests for `tools/bench-app/Hwinfo-Csv.ps1`'s column choice, from the iGPU case of 2026-09-23.
  PowerShell 5.1, which is a known weak spot for the model; that is worth measuring in its own right.
- A `--replicate` mode for `analysis/score_session_d.py` (§8a). ⚠️ **It is scoring code for a
  registered prediction, so Claude writes it**; the model could draft its test fixtures.
