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

## Is there more for it to do? Not right now, and why (2026-09-24)

Raymond asked for more jobs, and whether we were wasting time. **The model's time was never the
constraint.** The whole queue took ~8 min of generation. Each job cost ~20–30 min of spec and
acceptance script, plus ~10 min of review. **A job is worth queueing only when it saves more than
that.** Keeping the card busy is not a reason.

Checked and dropped the same day:
- **Claims for §5.7.7.** Once L3 had shown which values were real, their sources took two minutes
  to find, so Claude wrote the two claims directly (`5.7.7-collection-times`,
  `5.7.7-memonly-out-of-band-power`). A spec would have cost more than the work.
- **Tests for `Hwinfo-Csv.ps1`.** It already has four tests, including the iGPU case, so the job
  would mostly measure the model's PowerShell.

## Future jobs, in order

**Status 2026-09-26.**
- **L4 is done by Claude.** Session D's `--replicate` and `--control-replicate` fixtures were
  written with the scorer, and the same pattern covered Session E and the new-card scorer; writing
  a spec would have cost more than the fixtures.
- **L7 is done.** `score_session_d.py` reports 8c directly.
- **L5 and L6 still wait on their blockers.**
- **L8, below, is new**, and is the next job worth a spec.
- ⛔ **Never run the model during a 5060 Ti sweep.** This weekend's runs (4f, 4j, the new-card
  practice run, perhaps §10) rule out those windows.

A job moves into a queue only when its spec and acceptance check exist **and have been run against
a correct answer and a wrong one**. None of these has a spec yet.

| id | job | waits for | exact check | value |
|---|---|---|---|---|
| ~~**L4**~~ | ✅ **Done by Claude, 2026-09-24/25**: the 8a and 8d fixtures in `test_score_session_d.py`, then Session E and the new-card scorer the same way | — | — | — |
| **L5** | Claims for §5.5 (15 of 352 numbers pinned, the least-covered section), one subsection at a time, where the sources are already identified | Claude identifying each subsection's source files, which is most of the cost | `audit_claims.py`: each new claim passes and matches exactly once | high if the sources are known, otherwise not worth delegating |
| **L6** | Data READMEs for directories that lack an inventory, from a generated table of files, points and settings (the `sweep-root-inventory` pattern) | a directory with a gap; `find data -name README.md` against the directory list | every filename checked against the filesystem, and no invented facts | medium |
| ~~**L7**~~ | ~~The ascending/descending comparison for §8c, run through the L2 tool, **written up as a table only**~~ ✅ done: `score_session_d.py` scores 8c | — | — | — |
| **L8** | **The §5.5.9 numbers still unpinned.** Claude pinned the Session D verdict table, the direction counts, the 1590 counts and the control's split (`5.5.9-*` in `claims_consumer.py`). Left: D2's descriptive rows (1485 ×3, 0.563%, grid 1605–2130), 8b's 0.819 V at 1230 MHz, and the control's −0.82/+0.58% and −4.7/+9.5 W ranges | ✅ the sentences exist (paper §5.5.9, 2026-09-26); D2 needs a descriptive scorer path, since `score_session_d.py` refuses its grid | `audit_claims.py`: each new claim passes and matches exactly once | high: these are the second-chip numbers |

**Not for the model:**
- **Anything that scores a registered prediction.** Claude writes it; the model may draft fixtures.
- **The auditor's `numbersIn` rule** (ROADMAP item 7). What it should count is a judgement, not a
  mechanical task.
- **Anything on the 5060 Ti while it is sweeping.**
