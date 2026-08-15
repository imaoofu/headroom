# Handoff — picking this up on another machine

Everything needed to continue Headroom somewhere else. Read `CLAUDE.md` first for *what is
established and what must not be re-derived*; this file is purely about getting running again.

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

None are committed — licenses are unchecked and re-hosting other people's data isn't done casually.

```powershell
.\scripts\Get-Dataset.ps1
```

Pulls the V100 set, the consumer GTX 1080 Ti / 2070 Super 2D sweeps, a 2,824-GPU specs table, and
mining efficiency data. See the table in `CLAUDE.md` for what each one is for.

## 3. Confirm it works

```powershell
python analysis/characterize.py
```

Should report a **44.4%** mean headroom gap. If it doesn't, something is wrong with the data fetch —
stop and fix that before doing anything else.

```powershell
python analysis/curve_model.py --probes 4
```

Should select probe frequencies `[757, 825, 885, 1530]` MHz with held-out curve MAE **0.0261**, and
report the probe model **tying** the fixed-frequency baseline at 0.837% regret. That tie is the
expected, correct result — it is a finding, not a bug. Do not tune until it wins.

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

**Multi-line commit messages:** use `git commit -F <file>`. PowerShell here-strings break on
embedded quotes and silently truncate the message into pathspec errors. This bit once already.

---

## Hardware requirements, by task

| Task | Needs |
|---|---|
| `analysis/*` — all modelling | Any machine. CPU only. No GPU required. |
| `tools/frequency-sweep/gpu_workload.py` | An NVIDIA GPU + CUDA PyTorch. |
| `tools/frequency-sweep/Invoke-FrequencySweep.ps1` | NVIDIA GPU, **Windows**, **elevated shell**. Locks clocks. |
| `tools/stability-logger/` | NVIDIA GPU, Windows. Observes only, no elevation needed. |

The analysis half is fully portable. Only the data-collection tools are tied to Windows and NVIDIA.

**Before any sweep on a new machine:** re-verify the control APIs there. The findings in `CLAUDE.md`
were probed on one specific card and driver (RTX 5060 Ti / 610.88). A different GPU or driver may
support a different set — `nvmlDeviceGetGpcClkVfOffset` returned `NOT_SUPPORTED` on the 5060 Ti but
may not elsewhere. Never assume; probe.

---

## State as of this handoff

**Done:** V100 analysis complete with both findings (the 44.4% gap and the null). Stability logger
built and tested at idle. Frequency sweep tool built and dry-run tested. Fixed-work benchmark built
and tested. Curve model with adaptive probe selection built and validated. Four external datasets
verified downloadable.

**Not done — this is the whole remaining project:**

1. **Zero real data has been collected.** No sweep has actually run. This is the next step and
   everything downstream depends on it.
2. **The failure detector has never seen a failure.** Deliberately crashing something and confirming
   the logger catches it is the highest-value single hour available.
3. **Specs conditioning is stubbed.** `loadSpecFeatures()` in `curve_model.py` returns `None` on
   purpose. The specs table now exists (`data/external/all-gpus.json`), but fitting specs → curve
   needs ~10+ distinct GPU models. Validate leave-one-*model*-out when activating, or two cards of
   the same model leak across the split.
4. **Inspirit deliverable format still unknown** — paper, poster, journal, or symposium.

**The immediate next command**, from an elevated shell on a quiet GPU (close games, browsers,
Discord — the sweep refuses above 10% baseline utilisation and will tell you what to close):

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-gemm-stock" -WorkloadCommand "python tools\frequency-sweep\gpu_workload.py --workload gemm --json"
```

Roughly 15 minutes, at stock settings, producing the first real data point.

---

## Reference

- Repo: <https://github.com/imaoofu/headroom>
- Execution plan (12 weeks): <https://claude.ai/code/artifact/48a334b3-243a-4af1-b412-6293445adac1>
- Scope survey: <https://claude.ai/code/artifact/3ca54133-0f66-4837-9d11-95a9155f276a>
- Full session transcript: `headroom-chat-export.md` (exported separately, not committed)
