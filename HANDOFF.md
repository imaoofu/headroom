# Handoff — picking this up on another machine, or in a new chat

Everything needed to continue Headroom somewhere else.

**If you are an assistant reading this at the start of a new conversation:** read `CLAUDE.md`
next — it holds *what is established and must not be re-derived*, plus the standards this project
is held to. `ROADMAP.md` holds what is open and in what order. This file is about getting running
and knowing the current state. `docs/PAPER_DRAFT.md` is the write-up; every number in its audited
sections is pinned by `analysis/audit_claims.py` and must not be edited by hand without re-running
that.

Last updated **2026-08-29**.

---

## 1. Clone and install

```powershell
git clone https://github.com/imaoofu/headroom.git
cd headroom
```

**Python 3.12+** (3.12.10 was used). Note that installing VS Code does **not** install Python —
they are separate, and that tripped up the original setup.

```powershell
pip install -r requirements.txt
```

**PyTorch with CUDA** is separate and must come from NVIDIA's index, or you get a CPU-only build
that reports no CUDA device:

```powershell
pip install torch --index-url https://download.pytorch.org/whl/cu128
```

Verify before trusting anything:

```powershell
python -c "import torch; print(torch.__version__, torch.cuda.is_available(), torch.cuda.get_device_name(0))"
```

Expected on the original machine: `2.11.0+cu128 True NVIDIA GeForce RTX 5060 Ti`.
`cu128` is required for Blackwell (compute capability 12.0). Older CUDA wheels will install happily
and then fail at runtime.

## 2. Fetch the datasets

None are committed — the two DVFS datasets state no license at all, which under default copyright
means all rights reserved, so they must not be re-hosted here.

```powershell
.\scripts\Get-Dataset.ps1
```

Pulls the V100 set, the consumer GTX 1080 Ti / 2070 Super 2D sweeps, a 2,824-GPU specs table, and
mining efficiency data. See the table in `CLAUDE.md` for what each one is for.

## 3. Confirm it works

Run these four in order. Each has an expected output; a mismatch means stop and fix rather than
proceed.

```powershell
python run_tests.py
```

**`444 checks across 14 suite(s).`** then `All suites passed.` The runner also fails if it finds a
`test_*.py` under a directory it is not running — that guard exists because moving the model suites
into `analysis/models/` would otherwise have silently dropped three suites while still printing a
green result.

```powershell
python analysis/audit_claims.py
```

**149 claims, 0 failures** (fewer if `data/raw/` was not fetched - `claims_reference.py` registers nothing and says so). Every pinned number in the paper, recomputed from the CSVs and asserted
present verbatim and exactly once. If a claim fails, the paper and the data disagree — that is the
whole point of the tool, so read it as a real finding, not a broken script.

```powershell
python analysis/characterize.py
```

Should report a **44.4%** mean headroom gap. If it doesn't, something is wrong with the data fetch.

```powershell
python analysis/models/curve_model.py --probes 4
```

Should select probe frequencies `[757, 825, 885, 1530]` MHz with held-out curve MAE **0.0261**, and
report the probe model **tying** the fixed-frequency baseline at 0.837% regret. That tie is the
expected, correct result — it is a finding, not a bug. Do not tune until it wins.

## 4. The local delegation model (optional, and machine-specific)

`tools/local-model/ask_local.py` sends a spec to a local LLM. **It defaults to llama.cpp and will
fail if no server is listening on port 8099** — that is the most likely confusing failure on a new
machine, so either start the server or pass `--backend ollama`.

The server command is recorded as `SERVER_COMMAND` in `ask_local.py` itself:

```powershell
C:\Users\Raymond\llamacpp\llama-server.exe -m C:\Users\Raymond\models\Qwen3.8-27B-UD-IQ4_XS.gguf -c 65536 -ngl 99 --flash-attn on -ctk q4_0 -ctv q4_0 -np 1 --spec-type draft-mtp --spec-draft-n-max 1
```

Three of those flags are load-bearing and were each found the hard way:

- **`--spec-type draft-mtp`** uses the multi-token-prediction head the model ships with: **40.0
  tok/s against 28.9**, n=5 each, byte-identical greedy output. Ollama cannot do this on Windows —
  its MTP path is in the MLX runner and runs only on Apple Silicon.
- **`-np 1`** is not tidiness. llama-server defaults to four slots with per-slot compute buffers;
  at 64K that pushed past 16 GB, the driver **spilled to system RAM without failing**, and decode
  fell to 14.6 tok/s. `nvidia-smi` reported free VRAM throughout, because spilled memory is not
  counted. One slot is what makes 64K fit.
- **`-ctk q4_0 -ctv q4_0`** cuts the KV cache from 4.25 GiB to about 1.2 GiB at 64K.

Nothing this returns is ever committed without being run — for claims work that means
`audit_claims.py`, for a test file it means the mutation gate.

**On a machine without this exact setup, skip it.** Nothing in the analysis or collection path
depends on it.

---

## Git access

The original machine pushes with plain `git push` using a credential already in Windows Credential
Manager. `gh` was installed but its auth flow never completed and it is **not** needed — don't route
through it.

On a new machine, either set up `gh auth login` properly or let Git Credential Manager prompt on
first push. Commit identity used:

```
user.name  imaoofu
user.email 309965811+imaoofu@users.noreply.github.com
```

Set these **per-repo** (`git config user.email …`), not globally — the original machine has no
global git identity and that was deliberate.

**Multi-line commit messages:** use `git commit -F <file>` or a heredoc. PowerShell here-strings
break on embedded quotes and silently truncate the message into pathspec errors. This bit once
already.

---

## Hardware requirements, by task

| Task | Needs |
|---|---|
| `analysis/*` — all modelling and audit | Any machine. CPU only. No GPU required. |
| `tools/frequency-sweep/gpu_workload.py` | An NVIDIA GPU + CUDA PyTorch. |
| `tools/frequency-sweep/Invoke-FrequencySweep.ps1` | NVIDIA GPU, **Windows**, **elevated shell**. Locks clocks. |
| `tools/stability-logger/` | NVIDIA GPU, Windows. Observes only, no elevation needed. |
| `tools/local-model/` | 16 GB VRAM for the 27B at 64K; optional either way. |

The analysis half is fully portable. Only the data-collection tools are tied to Windows and NVIDIA.

**Before any sweep on a new machine:** re-verify the control APIs there. The findings in `CLAUDE.md`
were probed on one specific card and driver (RTX 5060 Ti / 610.88). A different GPU or driver may
support a different set — `nvmlDeviceGetGpcClkVfOffset` returned `NOT_SUPPORTED` on the 5060 Ti but
may not elsewhere. Never assume; probe.

**Before any sweep at all: turn off NVIDIA Instant Replay.** It moved the measured optimum by a
full grid step. §5.4.4 is the write-up; the sweep tool now refuses to start above 10% baseline
utilisation and names the offending process.

---

## State as of 2026-08-29

**Data.** 67 committed sweep CSVs across **two chips**: 55 on a Zotac RTX 5060 Ti Twin Edge OC 16 GB (Blackwell) and 9 on
a Gigabyte RTX 3070 Ti GAMING OC (Ampere), collected 2026-08-25 on a third party's machine and
returned to the state it was found in. Plus the stability logger's runs and the V100 public
dataset, which is never pooled with either.

**Established, and not to be re-derived:**

- **The 44.4% V100 headroom gap** and the **null** — per-workload prediction ties a fixed 952 MHz.
- **The `membw` plateau**, traced to the core V/F curve, explained by core voltage and crossbar
  clock through HWiNFO, and repaired by a change derived from that diagnosis (§5.7).
- **The central result reproduces on a second architecture** — 21.7% throughput for 37.3% power on
  the 3070 Ti (§5.5). Two chips is not a sample; every *tuning* result is still 5060 Ti only.
- **The vendor OC BIOS costs 23.11% more power at matched frequency for 0.56% of peak compute**
  (§5.5.1), and its clock ceiling is a `SwPowerCap`, not silicon (§5.5.3). **It is NOT voltage** —
  this bullet said "almost entirely voltage" until 2026-08-28, which Session B refuted: both BIOSes
  hold the same floor within one sensor step, the gap is a ~34 W additive offset that does not
  scale with core clock, and it is excluded from being voltage, core dynamic power, memory clock,
  crossbar or leakage. No mechanism is claimed (§5.5.1.1).
- **The constrained result, added 2026-08-27** (§5.6.1 + `analysis/models/`): under a 95%
  performance floor, probing beats a fixed frequency **25.4% to 4.9%** mean efficiency gain — 87%
  of the available gap, zero floor violations. **But the fitting earns none of it**: straight-line
  interpolation between four probes beats every fitted variant. Ridge only appears to win by
  breaking the floor on 8 of 33 workloads; made to respect it, it does worse than the interpolation.

**Repo structure note:** `analysis/models/` now holds everything that *predicts* rather than
measures, with its own README giving each model's current verdict. `analysis/` keeps measurement
and the audit.

---

## Not done — roughly in order of value

1. ~~A fan-RPM log on the 3070 Ti~~ **DONE 2026-08-29 without the card** - the RPM was already in the raw HWiNFO logs and cooling is now excluded (§5.5.1.1). The remaining 3070 Ti item is the never-collected `membw` matched-2130 sweep. Session B ran
   2026-08-27 and refuted its own registered prediction: the two BIOSes hold the same voltage
   floor, and the ~34 W gap is an additive offset excluded from voltage, core dynamic power,
   memory clock, crossbar and leakage (§5.5.1.1). The one live candidate is board-level — the
   position drawing *more* power runs ~5 °C *cooler*, so the cooling system is doing more work and
   fan power sits inside `nvidia-smi`'s board figure. **HWiNFO reports fan RPM and Session B did
   not capture it.** That single addition would turn a set of exclusions into a mechanism, and it
   needs the card. `membw` matched-2130 was also planned and never collected.
2. **Nothing has been stability-tested**, including the configurations producing the best numbers.
   A ~2.5% low outlier appears in roughly one split-curve `gemm` run in three, against 0.06% spread
   on the tuned curve — so this has evidence behind it now rather than being prudence.
3. **The failure detector has never seen a failure.** Deliberately crashing something and confirming
   the logger catches it is still the highest-value single hour available.
4. **The paper does not yet carry the constrained result.** §5.2 reports the unconstrained null
   alone, with no indication that it inverts under a floor. The README carries both halves and the
   draft does not. Both halves go in together or neither does — reporting the inversion without the
   "interpolation beats the fitted model" half would overstate what a model achieved.
5. **A voltage contradiction in the paper.** Lines 41 and 109 say voltage is "neither readable nor
   writable" while §5.5.3 reports measured voltage. One of them is wrong and it is the early text.
6. **Two results exist only in working notes** — the split-region curve's `gemm` peak and a tuned
   control re-run were taken as ad-hoc single points and never written to disk. Re-measure before
   citing either.
7. **Specs conditioning is stubbed.** `loadSpecFeatures()` in `analysis/models/curve_model.py`
   returns `None` on purpose. The specs table exists (`data/external/all-gpus.json`), but fitting
   specs → curve needs ~10+ distinct GPU models. Validate leave-one-*model*-out when activating, or
   two cards of the same model leak across the split.
8. **Inspirit deliverable format still unknown** — paper, poster, journal, or symposium.

**To run a sweep**, from an elevated shell on a quiet GPU (close games, browsers, Discord — the
sweep refuses above 10% baseline utilisation and will tell you what to close):

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-gemm-stock" -WorkloadCommand "python tools\frequency-sweep\gpu_workload.py --workload gemm --json"
```

Roughly 15 minutes at stock settings.

---

## Reference

- Repo: <https://github.com/imaoofu/headroom>
- Execution plan (12 weeks): <https://claude.ai/code/artifact/48a334b3-243a-4af1-b412-6293445adac1>
- Scope survey: <https://claude.ai/code/artifact/3ca54133-0f66-4837-9d11-95a9155f276a>
- Full session transcript: `headroom-chat-export.md` (exported separately, not committed)
