# NVML clock-offset prior-art search — 2026-09-22

Job 8 in [GPT-PROMPT-NEXT](../agents/GPT-PROMPT-NEXT.md). Searched 2026-09-22 Pacific time. This was **not a cold outside-reader check**: this GPT task had already read the project's framing. External sources were searched before the [4c measurement](../../data/frequency-sweeps/5060ti-nvml-offset-20260922/README.md) was consulted. No GPU experiment was run. The 4c CSVs were not independently re-scored; that is Job 9.

## Finding

**Global core-clock offsets shifting the V/F curve are prior art.** First-hand Afterburner users described the core slider moving every curve point years ago. NVIDIA's [NVML reference](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceCommands.html) names the older call a *GPCCLK VF offset* and points to `nvmlDeviceSetClockOffsets` as its successor. The [170tune source at an August 30, 2026 revision](https://github.com/cachenetics/170tune/blob/93d0e727e70a9d1af4b2bcbddda8f8709dd6664a/tools/170tune) explicitly says an NVML offset shifts the whole curve. Do not present the general mechanism as new.

The 4c result remains a **one-chip, one-offset, one-workload** observation: on one RTX 5060 Ti, its reported voltage under a −300 MHz offset at achieved clock `f` matched stock near `f+300`, within the README's reported 2–3 mV at eight pairable points; the floor moved. Those figures are **taken from the 4c README, not recomputed here**. I did not locate an earlier Blackwell measurement of that specific pairing in this bounded search. The literature-facing comparison is with [Guerreiro et al. (TPDS 2019)](https://web.tecnico.ulisboa.pt/~ist14359/wordpress/nfvr_pubs/tpds19.pdf): their `nvidia-settings` offsets yielded constant voltage across frequencies on older GPUs. Their paper used different methods on different GPUs, so this is a **method-and-generation contrast, not proof that the API alone caused the difference**.

## Sources opened and limits

| Source | Directly checked | Limit |
|---|---|---|
| [NVIDIA NVML Device Commands](https://docs.nvidia.com/deploy/nvml-api/api/group__nvmlDeviceCommands.html) | `nvmlDeviceSetGpcClkVfOffset` sets a graphics-clock V/F offset; NVIDIA directs users to `nvmlDeviceSetClockOffsets`. Locked-clock control is a separate call. | No exact `V_offset(f)=V_stock(f-k)` identity or Blackwell voltage measurement. |
| [NVIDIA `nvidia-settings` source](https://github.com/NVIDIA/nvidia-settings/blob/main/src/parse.c) | `GPUGraphicsClockOffsetAllPerformanceLevels` applies an MHz offset to all performance levels; a per-level control also exists. | Describes controls, not measured voltage response. |
| [MSI Afterburner guide](https://www.msi.com/blog/msi-afterburner-overclocking-undervolting-guide?pubDate=20260308) | Describes whole-line curve movement and point editing. | No quantitative NVML result; no direct Unwinder-authored explanation of the exact NVML operation found. |
| [First-hand Afterburner guide, 2021](https://www.reddit.com/r/nvidia/comments/koub76/3_ways_to_undervolt_in_msi_afterburner_for_3080/) | Author says the core slider moves the entire curve for positive or negative offsets. A [2020 practitioner](https://www.reddit.com/r/overclocking/comments/f3wic8/til_hold_shift_in_nvidiaafterburner_oc_scanner_to/) says it shifts each point equally; a [2023 user](https://www.reddit.com/r/overclocking/comments/10l6oe2/msi_afterburner_effect_on_gpu_clock/) describes moving each point's frequency without changing its voltage. | First-hand practical accounts, not controlled Blackwell experiments. |
| [LACT configuration docs](https://github.com/ilya-zlobintsev/LACT/blob/master/docs/CONFIG.md) | Distinguishes NVIDIA per-P-state clock offsets from V/F point settings. | No measured response to a global offset. |
| [GreenWithEnvy README](https://github.com/leinardi/gwe/blob/master/README.md) | Supports GPU and memory overclock-offset profiles. | No curve-shift equation or voltage measurement found. |
| [NVIDIA open GPU discussion](https://github.com/NVIDIA/open-gpu-kernel-modules/discussions/236) | Users report using `nvidia-settings` offsets to reach lower voltage at a chosen clock; one reports a 300 MHz positive offset after setup. Another describes constant-offset control as allowing one curve shape. | User reports on older hardware; not a controlled same-GPU, cross-method comparison. |
| [170tune, August 30, 2026 revision](https://github.com/cachenetics/170tune/blob/93d0e727e70a9d1af4b2bcbddda8f8709dd6664a/tools/170tune) | For a CMP 170HX (GA100), the author says an NVML offset moves the whole curve and reports power at fixed 1350 MHz falling **174.6 W to 132.0 W** from +0 to +300 MHz with identical throughput. I checked the older revision through GitHub; both claims were already there. | No voltage telemetry on that GPU, so the power result does not directly establish the voltage lookup. Figures are the author's, not reprocessed here. |
| [Guerreiro et al., TPDS 2019, DOI 10.1109/TPDS.2019.2917181](https://web.tecnico.ulisboa.pt/~ist14359/wordpress/nfvr_pubs/tpds19.pdf), published full text §4.3 | NVML frequency changes on Titan Xp, GTX Titan X, and Tesla K40c showed a constant lower-voltage region and rising upper region. Where NVML frequency changes were unavailable, PowerMizer graphics/memory offsets in `nvidia-settings` yielded constant voltage across frequencies. | No same-GPU comparison of the two methods; no RTX 50 GPU. |
| [Mendes et al., JPDC 2022](https://www.sciencedirect.com/science/article/pii/S0743731522000624), publisher page and abstract | Studies decoupled voltage/frequency on two **AMD** GPUs. | Not an NVIDIA offset pairing. An author PDF appeared in search, but the web reader could not open it; full text not assessed here. |

The older community accounts and 170tune pre-empt a broad novelty claim for offset-driven curve motion. The 170tune fixed-clock power result supports its author's interpretation but lacks voltage readback. Guerreiro's constant-voltage result is real; the control method and GPU generation differ together. The defensible wording is **a hardware-specific measurement consistent with an established offset mechanism**, with a bounded comparison to Guerreiro.

## Exact search queries

The following are the 28 web-search queries actually submitted on 2026-09-22, in batch order. Hits were treated as leads until the sources above were opened. GitHub revision metadata was checked with the authenticated `gh` API; the old 170tune file was inspected without executing it.

1. `MSI Afterburner core clock offset shifts entire voltage frequency curve left right Unwinder`
2. `MSI Afterburner core clock slider shifts whole voltage frequency curve stock points negative offset`
3. `LACT GPU core clock offset voltage frequency curve shift NVIDIA`
4. `GreenWithEnvy NVIDIA offset voltage frequency curve shift`
5. `site:docs.nvidia.com nvmlDeviceSetClockOffsets clock offset V/F curve Nvml clock offsets`
6. `site:docs.nvidia.com nvidia-settings Coolbits GPUGraphicsClockOffsetAllPerformanceLevels voltage frequency curve`
7. `"Guerreiro" "voltage" "offset" "nvidia-settings" TPDS 2019`
8. `MSI Afterburner 4.3.0 voltage frequency curve editor core clock offset slider Unwinder official guide PDF`
9. `Guerreiro GPU DVFS "nvidia-settings" "voltage" 2019 paper`
10. `Guerreiro 2019 TPDS GPU voltage constant clock offset Maxwell Pascal Kepler DOI`
11. `"Guerreiro" "voltage" "constant" "nvidia-settings"`
12. `site:arxiv.org Guerreiro GPU DVFS voltage frequency nvidia-settings`
13. `site:download.nvidia.com/XFree86/Linux-x86_64/ nvidia-settings GPUGraphicsClockOffsetAllPerformanceLevels Coolbits offset`
14. `site:github.com/NVIDIA/nvidia-settings "GPUGraphicsClockOffsetAllPerformanceLevels" "offset"`
15. `site:github.com/ilya-zlobintsev/LACT "nvidia_gpu_vf_curve" "gpu_clock_offsets"`
16. `site:github.com/leinardi/gwe clock offset voltage curve`
17. `"Modeling and Decoupling the GPU Power Consumption" pdf Guerreiro voltage offset constant`
18. `"voltage stays constant" "nvidia-settings" Guerreiro`
19. `"voltage does not change" "nvidia-settings" Guerreiro Titan Xp GTX`
20. `"Guerreiro" "frequency offsets" "voltage" Titan Xp`
21. `"nvidia-settings" "offset" "voltage" GPU DVFS paper measured`
22. `"GPUGraphicsClockOffset" voltage measured GPU paper`
23. `"nvmlDeviceSetGpcClkVfOffset" voltage frequency study`
24. `"clock offset" "voltage" "RTX 50" GPU curve study`
25. `"Decoupling GPGPU voltage-frequency scaling" offset voltage nvidia-settings pdf`
26. `"GPGPU" "clock offset" "voltage" experimental paper`
27. `GPU DVFS "frequency offset" "voltage" NVIDIA experimental paper`
28. `"GPU" "V/F curve" "offset" "voltage" paper NVIDIA`

### Unresolved access and coverage

The full published Guerreiro PDF was opened. The Mendes author PDF could not be opened through the web reader, and no direct Unwinder-authored account of the exact NVML call was found. I did not search private Discords, every Guru3D/Overclock.net thread, patents, or all forward citations. A Blackwell pairing absent from this bounded search is **not** a novelty proof.

Before filing, all five repository gates passed: 925 checks across 28 suites, claims audit, data manifest, citation coverage, and 1,124 measurement hashes. The live citation verifier also reached and matched all registered arXiv/DOI metadata; metadata matching does not establish a source's substantive claim. Files touched for this job: this report and `docs/gpt-findings/README.md`. No commit was made.

## Review by Claude, 2026-09-22 — accepted; it narrows a 🔑 the same evening it was written

**The strongest source was verified directly.** The 170tune file at commit `93d0e72` (dated
2026-08-30) was fetched with `gh api`. Lines 590–605 contain the whole-curve statement, the 174.6 →
132.0 W pinned-clock result, and *"below about 1350 the rail bottoms out… extra offset is inert"*. GPT
did not quote that last line, and it is the closest point: **a load floor under an offset**. The
community and NVIDIA-doc sources were not re-opened here; Reddit is unreachable from Claude's
environment.

**Narrowed as a result** (CLAUDE.md, the 4c README, `RELATED-WORK.md` §10): the curve-shift
mechanism is prior art. What 4c adds is voltage readback, the pairing, the floor end under an offset,
and the chip. The Guerreiro contrast is method and generation together. ✅ **This is the search rule
working as designed: the 🔑 was checked before anything was built on it.**
