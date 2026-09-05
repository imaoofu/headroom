# `tools/local-model/` — delegating mechanical work to a local LLM

`ask_local.py` sends a written specification to a model running on this machine and saves what
comes back. It is a **labour-saving tool, not a source of results.** Nothing it returns has ever
been committed here without being run first — for claims work that means `analysis/audit_claims.py`,
for a test file it means the mutation gate.

The script's own docstring covers *why* it exists and the four failure modes it handles. This file
covers the things that are not visible from inside it.

---

## 🛑 THE HAZARD: the model runs on the card the research measures

**This is the most important thing in this directory, and it is not a property of `ask_local.py` —
it is a property of running a 27B on a 16 GB card that is also the instrument.**

`llama-server` with the flags below holds **15.03 GB of this card's 16.31 GB**, leaving ~1.3 GB
free. And it does so at **~0% SM utilisation and 0% encoder** when idle between requests.

That combination is invisible to two of the three sweep guards:

| guard | what it reads | does it see a loaded, idle model? |
|---|---|---|
| baseline utilisation | `utilization.gpu` | ❌ no — an idle model is ~0% |
| video engines | `utilization.encoder` / `.decoder` | ❌ no — inference uses neither |
| **free VRAM** | `memory.free` | ✅ **yes — this is the one that catches it** |

The free-VRAM guard was added to `Invoke-FrequencySweep.ps1` on **2026-09-05**. Before that date the
sweep had no way to see a resident model at all, and the collection kit's `preflight.py` was the
only tool in the repo that checked (it has since 2026-08-27).

**What an unguarded run would have produced.** `gemm` allocates ~768 MB and would have **run to
completion** under memory pressure, returning a number indistinguishable from a good one. `membw`
allocates ~3 GB and would not fit — failing outright, or falling back to system memory the way this
driver has already been shown to do *silently*, where throughput collapses and nothing errors.

⚠️ **Sweeps collected before schema `0.3.2` carry no record of VRAM occupancy.** They cannot be
audited for this retrospectively — the field did not exist. That is an unfixable cost of having
shipped the guard late, and it is why `free_vram_mb_at_start` is now written into every session JSON.

**Operationally: stop `llama-server` before any sweep.** The guard will refuse rather than let a
contaminated run start, but a refusal after the operator has walked away is an hour lost.

---

## Running it

`llama-server` must already be running. The exact command is `SERVER_COMMAND` in
[ask_local.py:80](ask_local.py:80) — read it there rather than copying it from here, so there is one
copy to keep right. Two of its flags are load-bearing and are **not** style choices:

- **`-np 1`** — the default of four slots allocates compute buffers per slot, which at 64K context
  pushed past 16 GB. The driver spilled to system memory **without failing**: decode fell to
  14.6 tok/s and prefill fell 6×, while `nvidia-smi` reported free VRAM throughout, because spilled
  memory is not counted. **VRAM-used is not a fit check near the limit** — watch a throughput number
  that should not have moved.
- **`--no-mmap`** — a memory fix, not a speed flag. llama.cpp maps the GGUF by default and the mapped
  pages stay resident for the life of the process even though every weight is already in VRAM.
  Measured 2026-09-02, one variable changed: working set **13.94 GB → 1.27 GB**, system RAM
  **88.4% → 44.5%**. Nothing traded at inference. Only a cold load should pay, and **that cost is not
  measured** — the file was in the OS cache both times. Do not quote a load-time figure.

Then:

```bash
python tools/local-model/ask_local.py specs/paper-5.7.4-claims.md
```

Writes to `<spec>.out.py` unless `--out` says otherwise. `--backend ollama` reaches qwen3-coder,
which has no llama.cpp counterpart on this machine. `--think` enables reasoning, at the cost of the
same output budget as the answer.

## `specs/`

Reusable task specifications, one per delegated job, each paired with the `.out.py` it produced.
They are kept because **two of them turned out to contain errors of their own** — the checking
catches both sides of the arrangement, not just the model's.

## Why llama.cpp and why this quantisation

Neither was a preference; both were measured.

**llama.cpp over Ollama** — this model ships an MTP self-draft head (`nextn_predict_layers = 1`).
Ollama's CUDA runner has no speculative path at all; its MTP code lives in the MLX runner and runs
only on Apple Silicon. With `--spec-type draft-mtp`: **40.0 vs 28.9 tok/s**, n=5 each, spreads 3.1%
and 0.9%, acceptance 0.978, and **byte-identical greedy output** — which is the check that matters,
because speculative decoding is only free if it is lossless.

**`UD-IQ4_XS`** is simply the largest quant that fits at 64K on 16 GB. Graded on
`specs/paper-5.7.4-claims.md` it beat `UD-Q3_K_XL` **87/91 against 71/91, p = 0.0057** — 🔑 **but
only at n=13 per model.** At n=3 it read 20/21 against 17/21 with overlapping ranges and did not
support a ranking at all. Note that the standard changes with the measurement: worst-of-A-beats-
best-of-B is right for tight repeated readings like the tok/s above, and **wrong** for a coarse
discrete score, where it would have discarded a real effect.

## Tests

`test_ask_local.py`, **48 checks**, run via `python run_tests.py`. Mutation-gated over the
two-backend normalisation — both backends must return the same keys, so nothing downstream branches
on which one answered.
