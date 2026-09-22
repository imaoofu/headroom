# 5060 Ti fine floor at 0.50 s sampling — worklist item 4i, 2026-09-22

**Three ascending replicates, 1380–1760 MHz, 13 points (~31 MHz), stock Profile 3, driver 616.92.**
The first sweeps in this project **driven end to end with no human present** —
`tools/hwinfo-logging/Invoke-LoggedSweep.ps1` did preflight, HWiNFO log start, sweep and log stop.

Raw HWiNFO logs are in the gitignored `data/HWiNFO-Data/5060ti-finefloor-20260922/`; the distilled
`_voltage.csv` extracts beside each sweep are the dataset-grade files.

---

## Why it was run: the 2026-09-18 pair sampled too slowly to answer its own question

`5060ti-finefloor-20260918/` logged at the main machine's **2.00 s**, giving **5–9 samples per
frequency point** — enough for a constant median, not enough to see whether the voltage *dithers*
between adjacent codes. The RTX 2060 Super dithers **23–26%**. Whether this card does was unknown.

At `SensorInterval=500` these runs carry **22–28 samples per point**.

## ✅ The floor reproduces exactly

`..._asc-r3_sweep_voltage.csv`, the clean replicate:

| MHz | 1377 | 1402 | 1432 | 1462 | 1500 | 1530 | **1560** | **1590** | 1620 | 1657 | 1687 | 1717 | 1747 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V | 0.720 | 0.720 | 0.720 | 0.720 | 0.720 | 0.720 | **0.720** | **0.730** | 0.740 | 0.745 | 0.755 | 0.760 | 0.770 |

**0.720 V holds through 1560 and first rises at 1590**, matching 2026-09-18 at four times the
sampling rate. Throughput agrees with the committed quiet reference at all thirteen points within
±1.9%, mean ≈ 0.

## 🔑 4i's answer: the 5 mV grid DOES dither — but only ABOVE the floor

Distinct voltage values inside each point's benchmark window, r3:

| region | behaviour |
|---|---|
| floor, 1378–1560 | **one code**, with at most a single stray sample (4% of ~25) |
| 1590, 1657 | one code plus one stray |
| **1620** | **0.735 × 9, 0.740 × 15 — 38% minority** |
| **1717** | **17% minority** |
| **1747** | **0.765 × 7, 0.770 × 14, 0.775 × 1 — 36%, across THREE codes** |

⚠️ **A 4% minority is one sample of ~25 and is not dither** — most likely a window-edge sample
catching the ramp. The claim rests on 1620, 1717 and 1747, where the minority is 17–38%.

✅ **So the floor is genuinely single-code and the rising region is not.** That is a structural
difference the 2.00 s logs could not have shown, and it is consistent with the floor being a
clamp rather than a regulation target.

---

## ⛔ THE METHODOLOGICAL RESULT, WHICH MATTERS MORE THAN THE DITHER

**Three replicates of one configuration, 15 minutes apart, differ by up to 11% at isolated points —
and the number of bad points tracks how busy the driving agent was.**

| run | what the agent was doing | degraded points |
|---|---|---|
| `asc` | running `nvidia-smi pmon` checks and composing replies | **4** — 1560, 1590, 1620, 1747 |
| `asc-r2` | silent during the run, composing replies around it | **1** — 1590 |
| `asc-r3` | silent | **0** |

`bench_seconds` is the readable column, because at fixed work it must fall monotonically as clock
rises:

```
asc     14.05 13.75 13.45 13.18 12.85 12.60 13.86 13.59 13.05 11.66 11.41 11.22 12.01
asc-r2  14.05 13.75 13.44 13.18 12.84 12.62 12.42 13.30 12.35 11.66 11.41 11.22 11.03
asc-r3  14.06 13.76 13.46 13.19 12.85 12.64 12.43 12.14 11.94 11.67 11.42 11.24 11.05
```

Only r3 is monotonic. **A point that departs the trend and then returns to it is not warm-up** —
warm-up is monotonic and does not recover.

🔑 **This is NOT the 2026-09-18 contamination.** That was the test suite imposing a **uniform
−9.38% at every point**. This removes **8–11% from isolated points while their neighbours are
untouched**, and lands on different frequencies each time. ⚠️ **A point-to-point residual cannot
find either**, which is why three replicates were needed.

✅ **It is almost certainly the same unexplained defect CLAUDE.md has carried since August** —
*"every verified-quiet `membw` sweep on the 10-point grid has a worst point"*, *"a defect that
lands on a different frequency each time is transient"*. **This is the first time it has been
caught on `gemm` with a controlled A/B/C, and the first evidence that it is driven by machine
activity rather than being intrinsic.**

### The protocol that follows

**Replicate and take the maximum.** The defect only ever removes throughput, so the max across
replicates is the uncontended value — and r3 achieves it at all thirteen points. ⛔ **A single
fine-grid sweep is not trustworthy at the ~1% level no matter how quiet the machine looks**, and
the preflight cannot help: every one of these runs passed preflight at 2–3% SM baseline.

### What was eliminated

| hypothesis | why not |
|---|---|
| thermal throttling | temperature **fell** at the slow points while the clock rose; throttling raises it |
| warm-up from a cold card | real and visible (44 → 52 °C over the first six points) but monotonic, and the bad points recover |
| power cap | `throttle_masks_seen` shows `0x4` SwPowerCap at 1500, 1530 and 1657 — **all of which were fine** — and 72–82 W against a 180 W limit |
| clock not held | `lock_held=True` and achieved = target at every point, including the slow ones |
| the 0.5 s sampling itself | r3 is clean at 0.5 s and matches the 2.00 s reference |

⚠️ `0x400` appears on every point and is **not** decoded here — `tools/stability-logger/ThrottleReasons.ps1`
records it as an unknown bit that arrived with the 610.88 → 616.56 driver and appears in 589 of 603
samples of a healthy run.

---

## Provenance

⚠️ **The operator was absent and two AI agents were resident on the machine** (Claude Code driving
the runs, OpenAI Codex working in the repository). Each run's `applied_settings` says so. The
degradation above is the measured cost of that arrangement; **r3 is the run to cite**, and the
other two are kept because the comparison between them *is* the methodological finding.

**Files:** `_sweep.csv` / `_sweep.json` per run, `_sweep_voltage.csv` the HWiNFO join.
🆕 These are the first sweeps carrying `window_start_unix` / `window_end_unix`, so the voltage join
ran in **time mode** rather than binning by clock — its first use on hardware-collected data.
