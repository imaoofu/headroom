# RTX 5060 Ti — the bench list

**Rewritten 2026-09-22**, after the unattended session that cleared eight items. This is the local
machine, so nothing here expires. Shared protocol (preflight, curve rules, logging):
[`GPU-BENCH-RULES.md`](GPU-BENCH-RULES.md). Times below are **measured** on 2026-09-22: a
twelve-workload suite takes **~55 min** through the logging wrapper, and a 13-point fine sweep
**~5.5 min**.

🔑 **Unattended runs are the normal mode now.** HWiNFO logging is automated and proven on 61 of 61
sweeps. What still needs Raymond:

1. Opening HWiNFO and its Sensors window before leaving, because launching it needs UAC.
2. Building curves.
3. ~~The first NVML offset write.~~ Done 2026-09-22. Offset runs can now be unattended.
4. OCCT, which is a GUI program.

---

## 🛠️ Curves to build — the full list, in order

**P1 is the only free slot.** P2–P5 hold configurations that committed data references, and all
five are preserved byte-for-byte in `data/afterburner-profiles/5060ti-profiles-20260918/`
(re-verified against the live store 2026-09-22). **So each new curve goes into P1, one at a time.**
Claude snapshots P1 before each rebuild.

| # | curve | build | into | verify before any run | for |
|---|---|---|---|---|---|
| **1** | **Rung B** | Apply **P5**. Raise **every point at or below 840 mV by exactly +170 MHz**. Leave **845 mV and above untouched**. Sliders untouched (memory stays +2500). Save → **1** | P1 | 720 mV reads **1700**, inside the registered window **1624–1777**. ≥860 mV identical to P5. <850 mV between stock and P4 | **4e** |
| **2** | **Rung C** | Same as rung B with **+320**: 720 mV → **1850**, 840 mV → 2307 | P1, after 4e runs | 720 mV inside **1778–1931**. Same other checks | **4f** |
| **3** | **P4, memory +0** | Apply **P4**. Set the **memory slider to +0**. Touch nothing else. Save → **1** | P1, after 4f runs | memory under load reads **13801**, not 16301. Curve identical to P4 | **4j** |

✅ **Both rungs are applicable as registered — checked against P5's decoded curve, 2026-09-22.**
Raising everything at or below 840 mV creates **no new downward step**: 840 mV lands at 2157 (B) or
2307 (C), still below 845 mV's 2362. The one downward step, **845 → 850 mV (2362 → 2180)**, is
already in P5, and Afterburner accepts it there.

🛑 **Safe by construction:** below 850 mV every point sits between stock (+0) and P4 (+472), and at
or above 860 mV the curve is P5 unchanged. Both bounds have run multi-hour suites. ⛔ **Wrong at
650–690 mV, found 2026-09-22 when rung B was decoded.** P4 **is** stock there, so a raised rung sits
above P4: rung B has 997 MHz at 650 mV where P4 has 817. The card never runs below 0.720 V under load,
so those points only apply at light load, but the "inside a tested envelope" claim does not hold there.

✅ **Rung B was built into P1 on 2026-09-22 and decoded.** 720 mV reads **1702**, the predicted grid
point. The floor region is lifted +165 to +172, because Afterburner stores clocks on a grid where
+170 exactly does not exist. Everything at 850 mV and above is identical to P5.
✅ **845 mV RESOLVED, and rung B is READY (snapshot `data/afterburner-profiles/5060ti-profiles-20260922-rungB/`).**
The editor shows 2362, +0, and a re-save produced a byte-identical file. The stored "+176" is the
decoder mispairing the offset at a boundary, not a different curve. ⚠️ Points below 700 mV cannot be
edited in the GUI, yet decode as lifted; they matter only at light load. **Above-floor equivalence to
P5 is checked by measurement:** compare the 4e suite's voltage extracts with P5's at the same targets. **Never use the
core-clock slider** for these, because it would move the top of the curve.

**Not curves, but also yours to do:** OCCT (4l, 4g). The first NVML offset write (4c) is done.

---

## Open items, in suggested order

| # | id | what | time | needs Raymond for | tier |
|---|---|---|---|---|---|
| 1 | **A/B** | **Activity A/B test**, `REGISTERED-PREDICTIONS.md` §5 | ~80 min + uptime wait | HWiNFO open | 2 |
| 2 | **4e** | **Rung B suite**, `REGISTERED-PREDICTIONS.md` §1 | ~55 min | building curve 1 | 3 |
| 3 | **4f** | **Rung C suite** | ~55 min | building curve 2 | 3 |
| 4 | **4o** | 🆕 **NVML offset ladder**, e.g. −150 / −300 / −450, a suite per rung. Needs registering first | ~3 h | nothing | 3 |
| 6 | **4j** | memory-matched flattened vs stock, `membw` + `gemm` | ~25 min | building curve 3 | 2 |
| 7 | **4n** | 🆕 `membw` fine grid around the **1627 MHz stall**, stock + P5 | ~25 min | nothing | 3 |
| 8 | **4m** | `reduce` residual: suite order or mechanism? | ~45 min | nothing | 2 |
| 9 | **4l** | stability soak of the repaired curve (P2) | 35 min | OCCT | 2 |
| 10 | **4g** | >30-minute soak | 90 min | OCCT | 3 |

### A/B — do isolated losses come from activity?

Registered **before** collection with a fixed scoring rule: runner
`tools/hwinfo-logging/experiments/Run-ActivityAB.ps1`, scorer `analysis/score_activity_ab.py`. It
separates agent activity from warm-up and run order, which the 2026-09-22 data could not do. See
[`../data/frequency-sweeps/5060ti-finefloor-20260922/README.md`](../data/frequency-sweeps/5060ti-finefloor-20260922/README.md).
**It decides whether "replicate and take the maximum" is a sound protocol.**

### 4e / 4f — the floor ladder

**The predicted optima are 1702 (B) and 1852 (C)**, registered 2026-09-11. With A (1545, measured)
and D (2010, measured), that makes a four-rung ladder. 🔑 **This strengthens exactly what survived
the 2026-09-22 narrowing**, when Mendes et al. (SBAC-PAD 2020) turned out to have already shown an
optimum moving. What remains ours is the relocation **predicted from the floor voltage in
advance**, and a ladder is the quantitative form of that. ⚠️ The registration names the **median**
as the primary test. Its per-workload threshold (7 of 12) was set before 2026-09-22 showed that per-workload
optima reproduce only 9 of 12 between identical runs, so report it, but weight the median.

### 4c / 4d — NVML clock offsets — ✅ 4c DONE 2026-09-22; 4d superseded

✅ **Run with Raymond present, registered in advance (`REGISTERED-PREDICTIONS.md` §6).** The two
regions survive: −300 MHz shifts the whole V/F curve, the floor end moves to 1245–1290 MHz, and locks
still hold. **4d is superseded**: its "power should match" criterion cannot hold as worded, and the
voltage pairing answers its question directly.
`data/frequency-sweeps/5060ti-nvml-offset-20260922/`. 🆕 **Next: an offset ladder** (e.g. −150 / −300
/ −450) as a suite per rung. It can run unattended, because there is no curve to build. It needs
registering first.

The original plan, kept:

1. Apply stock.
2. Write a **−300 MHz** offset. Negative only: lower clock at every voltage, the safe direction.
3. Run the 1380–1760 gemm sweep with voltage logged.
4. Reset the offset to **0** and read it back.

**Why it gates 4d:** Guerreiro et al. (TPDS 2019) found the voltage response differs between NVML
and clock offsets. If the voltage stays flat throughout, 4d validates nothing. Stop there and write
it up.

### 4j — the memory-matched pair

The only committed pair carrying voltage and XBAR telemetry differs by **2500 MHz of memory
clock**. Running curve 3 against stock, both at 13801, removes that confound. ⛔ **It does not
restore XBAR mediation**, which needs runtime XBAR control this card does not have.

### 4n — what is at 1627 MHz on `membw`?

In 5 of 6 silent runs, 1627 is the one point **below the line between its neighbours**, while the
rest of the curve sits above its line. So the rise **stalls** there. **Throughput never falls.**
The 10-point grid steps ~78 MHz there, so the stall's width is unknown. A 13-point sweep across
**1550–1710** on stock and P5, twice each, would show whether it is a notch or a slope change.
[`../data/frequency-sweeps/5060ti-membw-silent-20260922/README.md`](../data/frequency-sweeps/5060ti-membw-silent-20260922/README.md).

### 4m — `reduce`

The curve predictor misses **all 16 `reduce` curves, every optimum ABOVE the prediction**, and 14 of
16 legs ran in the same suite order. Fine-sweep `reduce` and one matched workload in **randomised
order, replicated**. A stable offset means a workload property. An offset that follows run position
means every per-workload residual in the project is a benchmark artifact.

### 4l / 4g — soaks

The repaired curve (P2) behind §5.7 has **never been soaked**, and every tuned configuration has
been soaked for exactly thirty minutes. OCCT GPU:3D Adaptive, error detection on, via
`tools/stability-logger/Invoke-StabilityProtocol.ps1`. Say **"no failure observed in N minutes"**,
never "stable".

---

## ✅ Done — do not re-run

| id | what | where |
|---|---|---|
| 4a | fine floor 1380–1760, ×2 | `5060ti-finefloor-20260918/` |
| 4c | NVML −300 MHz offset: **the two regions survive, and the curve shifts by the offset** | `5060ti-nvml-offset-20260922/` |
| 4d | superseded by 4c's voltage pairing; its criterion could not hold as worded | — |
| 4i | ascending fine floor at 0.50 s, ×3: dither **only above** the floor | `5060ti-finefloor-20260922/` |
| 4b | descending fine floor, ×2: **matches ascending within ±0.08%** | same |
| 4h | floor end: **0.720 V through 1567, 0.730 at 1575** | same |
| 4k | Profile 1 suite: **registered median 2010, held** | `5060ti-p1-suite-20260922/` |
| — | P4 suite, same session | `5060ti-p4-suite-20260922/` |
| — | two identical stock suites: **per-workload optima 9 of 12** | `5060ti-stock-repro-20260922/` |
| — | `membw` silent ×6, stock and P5 | `5060ti-membw-silent-20260922/` |

## What is deliberately NOT on this list

- ⛔ **The voltage-shortfall test.** Refuted 2026-08-21. Do not re-run it.
- ⛔ **More `membw` configuration rankings at n≤3.** The spread between configurations (0.56%) is
  smaller than the spread within one (up to 0.98%).
- ⛔ **CPU and RAM undervolting.** Scoped out: BIOS-level, a reboot per point, and instability
  corrupts data silently.
