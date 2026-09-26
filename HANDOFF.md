# Handoff — picking this up on another machine, or in a new chat

Everything needed to continue Headroom somewhere else.

**If you are an assistant reading this at the start of a new conversation:** read `CLAUDE.md`
next — it holds *what is established and must not be re-derived*, plus the standards this project
is held to. `ROADMAP.md` holds what is open and in what order. This file is about getting running
and knowing the current state. `docs/PAPER_DRAFT.md` is the write-up; every number in its audited
sections is pinned by `analysis/audit_claims.py` and must not be edited by hand without re-running
that.

Last updated **2026-09-10**.

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

**`665 checks across 18 suite(s).`** then `All suites passed.` It is `663` where `data/raw/` was
not fetched: two checks in `models/test_predict_constrained_frequency.py` skip without it. The
runner also fails if it finds a
`test_*.py` under a directory it is not running — that guard exists because moving the model suites
into `analysis/models/` would otherwise have silently dropped three suites while still printing a
green result.

```powershell
python analysis/audit_claims.py
```

**256 claims, 0 failures**, or **224** where `data/raw/` was not fetched - `claims_reference.py`
registers its 28 claims only when the dataset is present, and FIVE more claims are guarded on the
same condition because a claim counting the registry is otherwise environment-dependent, so the gap
is 32 rather than 28. Every pinned number in the paper, recomputed from the CSVs and asserted
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
# THIS COPY WENT STALE ONCE ALREADY - it lost --no-mmap for three days after that flag landed
# on 2026-09-02. Read the command from SERVER_COMMAND in tools/local-model/ask_local.py, which
# is the copy the script itself uses and therefore cannot drift from what actually runs.
# tools/local-model/README.md explains why -np 1 and --no-mmap are load-bearing, not style.
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
Manager. **`gh` was authenticated on 2026-09-02** (account `imaoofu`, scopes `gist`, `read:org`,
`repo`, `workflow`). Keep pushing with plain `git push` — but **`gh` is the only way to read CI**,
because the repo is private and an unauthenticated API request returns `Not Found` rather than a
useful error:

```powershell
gh run list --limit 10
gh run view <run-id> --log-failed
```

⚠️ A `cancelled` run is usually not a failure — `ci.yml` sets `cancel-in-progress`, so a push that
supersedes a running one cancels it.

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
were probed on one specific card and driver (RTX 5060 Ti / 610.88 at the time of probing; the card has run 616.56 since 2026-09-02 and the probes have not been repeated on it). A different GPU or driver may
support a different set — `nvmlDeviceGetGpcClkVfOffset` returned `NOT_SUPPORTED` on the 5060 Ti but
may not elsewhere. Never assume; probe.

**Before any sweep at all: turn off NVIDIA Instant Replay.** It moved the measured optimum by a
full grid step. §5.4.4 is the write-up; the sweep tool now refuses to start above 10% baseline
utilisation and names the offending process.

---

## State as of 2026-09-26 — read this first; the 2026-09-10 block below is history

**Data: 695 dataset-grade sweeps plus 3 verification runs = 698** (rung C's 12 added 2026-09-26), across **four chips**:

| card | dataset-grade sweeps |
|---|---|
| RTX 5060 Ti | 526 |
| RTX 3070 Ti | 137 |
| RTX 2060 Super | 18 |
| RTX 3060 | 14 |

Read the counts off `python analysis/build_data_manifest.py --check`, never off this file.

**What changed since 2026-09-10, in one line each:**
- **The load-floor rule is prior art.** It is the ridge point (Schoonhoven et al.); see CLAUDE.md.
- **The 3070 Ti causal test (Session D):** the manipulation passed twice, but the negative
  control failed (4b). D2's repeat was not scoreable, and descriptively it held. **Attribution to
  the floor region is not established on that chip.**
- **§2.7's use of Wang et al. was corrected twice** (2026-09-25 and 09-26); see CLAUDE.md.
- **Headroom Bench runs whole sessions unattended from the USB.** It can now also run a stock-only
  protocol on any RTX 40/50 card (REGISTERED-PREDICTIONS §11).

**The ordered open list is ROADMAP.md, "Open right now — 2026-09-26".** Hardware this weekend:
- ~~the 3070 Ti ships~~ ✅ shipped 2026-09-25, bench software uninstalled first;
- Session E runs on the 2060 Super;
- the 5060 Ti gets rung C (4f), the memory-matched pair (4j) and the new-card practice run.

## State as of 2026-09-10

**Data. 349 committed sweep CSVs across THREE chips**, of which **342 are dataset-grade** — the
figure the paper's results rest on. The difference is three probe directories whose own READMEs
mark them not dataset-grade, plus four kit-verification sweeps.

| chip | arch / node | sweeps | what was done to it |
|---|---|---|---|
| Zotac RTX 5060 Ti Twin Edge OC 16 GB | Blackwell, 5 nm | 306 | everything, including all tuning |
| Gigabyte RTX 3070 Ti GAMING OC | Ampere, 8 nm | 25 | stock + two vendor BIOS positions |
| ASUS Phoenix RTX 3060 12 GB | Ampere, 8 nm | 14 | stock only |
| unlabelled, 2026-08-15/16 | 5060 Ti | 4 | early harness verification |

The 3070 Ti (2026-08-25) and the 3060 (2026-09-10) were customer machines, collected with the USB
kit and returned as found. **Every tuning result is 5060 Ti only**, and always will be on this route.

### Established, and not to be re-derived

🔑 **THE CENTRAL RESULT — the efficiency optimum is the last frequency the V/F curve reaches at the
card's LOAD-FLOOR voltage.** Confirmed on five configurations across two architectures, each
prediction registered in the run's metadata *before* the measurement:

| configuration | chip | floor | ends | optimum |
|---|---|---|---|---|
| stock / split / repair | 5060 Ti | 0.720 V | 1530-1537 | 1537 |
| full tune | 5060 Ti | 0.720 V | 2002 | 2002 |
| **stock** | **RTX 3060** | **0.756 V** | **1260** | **1260** |

Tested by **manipulation** (move the floor region: the **median** optimum moves +465 MHz, all 12
workloads move up, by +79 to +540), by **negative control** (move the curve above the floor by
570 MHz: the median moves by nothing, but 4 of 12 workloads move), and **across architectures**.
⚠️ Causal n = 1 chip, and the manipulation's result was not the registered prediction; see
CLAUDE.md's contribution section. ⛔ This said *"+465 MHz in 12 of 12 workloads"* and *"optimum
moves by nothing"* until 2026-09-24. The retraction of 2026-09-19 had not reached this file. ⛔ **The floor voltage is per card and does NOT transfer** — borrowing
0.720 V for the 3060 costs a 270 MHz error.

- **The 44.4% V100 headroom gap** and **the null** — per-workload prediction ties a fixed 952 MHz.
  🔑 **The consumer data now explains the null**: 61.9% of the optimum's variance sits on the
  *configuration* and 19.0% on the workload, and the V100 set has exactly one configuration, so 62%
  of the signal is invisible in it by construction. `analysis/models/predict_from_curve.py` scores a
  curve-reading predictor at **0.675% mean regret**, tying a hindsight-fitted per-configuration
  constant exactly. ⚠️ The whole axis is worth 1.29 points against a 30-57 point headroom.
- **The `membw` plateau**, traced to the core V/F curve and crossbar starvation, repaired by a change
  derived from the diagnosis. ⚠️ The mechanism statement was **generalised 2026-09-09**: it is not
  about flatness low down — *the crossbar tracks the core while voltage rises, and stops wherever
  voltage plateaus while the core keeps climbing.*
- **The first same-session stock-versus-tuned comparison**, 2026-09-09: gap **~23 points, ±1.3**,
  stock higher in 12 of 12 workloads. Everything earlier was assembled across days.
- **The vendor OC BIOS costs 23.11% more power at matched frequency for 0.56% of peak compute**, and
  it is **NOT voltage** — a ~34 W additive offset excluded from voltage, core dynamic power, memory
  clock, crossbar and leakage. No mechanism claimed.
- **Stock is applicable from the command line** as of 2026-09-08 — Profile 3 holds it, verified on
  disk and in application. That removed the constraint forcing every comparison to be tuned-vs-tuned.

### Corrections made recently, so they are not re-introduced

- ⛔ `abba-20260908`'s "the full tune reproduces to 0.04 points" is **retracted** — a second bracket
  drifted −1.25. At n=2 the tuned side's session reproducibility is **±1.3 points**.
- ⛔ CLAUDE.md's claim-count gap said 25; it is **28**. Five non-reference claims are guarded, not two.
- ⛔ `predict_from_curve.py`'s "the floor is assumed to transfer" — **falsified**, see above.

---

## Not done — roughly in order of value

1. **The NVML offset ladder.** The floor's *extent* is still read from a decoded curve rather than
   **set**. `nvmlDeviceSetClockOffsets` reads back 0 mV with a profile live, so it stacks on top of
   Afterburner and a negative offset slides the whole curve — four deliberate extents in one session.
   ~~⛔ **The write has never been exercised.**~~ ✅ **Exercised 2026-09-22:** −300 MHz shifts the curve
   (voltage at f = stock voltage at f+300: identical VID codes at 9 of 9 pairs), and the floor end
   moves to 1245–1290. `data/frequency-sweeps/5060ti-nvml-offset-20260922/`. ⛔ The old validation
   criterion, "power at locked *f* with −300 should match *f*+300 without", is not a valid prediction:
   retire it. The wider machine-state question is still open. See CLAUDE.md.
2. **Nothing in the profile set is stability tested.** Two 30-minute runs exist from 2026-08-23 on
   hand-set curves, and nothing verifies those match what is now in the slots.
3. **`reduce` is sub-optimal in 16 of 16 sweeps** and carries most of the curve-predictor's residual.
   Its throughput saturates just *past* where the voltage floor ends, so the optimum overshoots every
   time. A mechanism question, not a modelling one.
4. **More chips.** ROADMAP targets N=6-10 heterogeneous, stock-only; three are in. An RTX 2060 Super
   is the highest-value next one — Turing, 12 nm (a third process node), and a same-day sibling of
   the RTX 2070 Super whose published dataset swept the wrong range.
5. **`conv` runs 1.6× faster per iteration on the 3060 than the 5060 Ti** and is unexplained.
   Possibly TF32 gating differing on Ampere. **Do not use `conv` for cross-chip comparison until
   someone looks.**
6. **Specs conditioning is stubbed.** `loadSpecFeatures()` in `curve_model.py` returns `None` on
   purpose; fitting specs → curve needs ~10+ distinct models. Validate leave-one-*model*-out when
   activating, or two cards of one model leak across the split.
7. **Paper coverage is uneven.** 20 numbered sections carry no claim at all, including 3.1, 3.2, 3.4
   and 5.7. ✅ **The 2026-09-08..10 results ARE now in the paper** as of 2026-09-11 - the load-floor
   mechanism with its manipulation and negative-control arms (§5.5.8), the third chip (§5.5.7), the
   same-session stock bracket (§5.8) and probe selection (§5.3.1), all pinned.
8. **32 loose sweep CSVs sit in `data/frequency-sweeps/` root** from August, in no directory.
   Tidyable, but claims pin paths — move, run the auditor, fix references.

⚠️ **The raw HWiNFO logs (35 MB, 17 files) are gitignored and exist on one disk only.** The distilled
extracts are committed, so nothing published depends on them — but a re-join with different binning
would need them. Worth a manual backup.

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
