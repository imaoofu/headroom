# `splitcurve-suite-20260907` — the twelve-workload suite on a tuned card, and half the headroom is gone

**Twelve sweeps, 13 of 13 frequencies each, 49 minutes plus a top-up.** RTX 5060 Ti on the
**split-region V/F curve with memory +2500**, driver 616.64, schema 0.3.3, 2026-09-07.

**Dataset-grade.** Same suite, same 1236–3090 MHz grid, same iteration counts as every stock
replicate. **The first time the twelve-workload suite has been run on any tuned configuration** —
every prior tuned sweep in this project is `gemm` or `membw`, two points on the arithmetic-intensity
axis, and `softmax`, `layernorm`, `bgemm32`, `bgemm256` and `attention` had never been swept tuned.

---

## 🔑 The result: tuning captures about half the headroom, so the headroom is measured against a
## configuration a tuned user has already left

| | mean efficiency gain, optimum vs highest achieved clock |
|---|---|
| stock (r2–r6 mean) | **55.9%** |
| **split curve** | **27.4%** |

**The gap narrows by 28.5 points.** That is not a contradiction of §5.1 — it is what the thesis
predicts. Headroom exists because the stock configuration is inefficient at high clock; apply a
curve that fixes some of that and roughly half the recoverable efficiency has already been taken.
What remains — 27.4% — is the headroom still available *on top of* a well-tuned card.

⚠️ **This bounds who the 55.9% figure is for.** It is the gap for a user running stock. A user who
already undervolts has roughly half as much left. Any framing of the headline number should say
which population it describes.

**It is not an artifact of the reference point moving.** The split curve reaches ~2977 MHz against
stock's ~2593, so its reference sits at a *higher* clock — which should make the measured headroom
*larger*, not smaller. It shrank anyway, because the tuned card's efficiency at its own top clock is
so much better than stock's at stock's.

## Efficiency at matched commanded frequency

The fair comparison, 13 shared targets per workload, against the r2–r6 stock mean:

| workload | Δ efficiency | | workload | Δ efficiency |
|---|---|---|---|---|
| `attention` | **+26.0%** | | `bgemm256` | +13.3% |
| `bgemm1024` | +19.2% | | `layernorm` | +13.0% |
| `conv` | +17.1% | | `bgemm128` | +9.5% |
| `copy` | +15.6% | | `reduce` | +9.4% |
| `bgemm64` | +14.2% | | `gemm` | **+7.6%** |
| `softmax` | +14.0% | | | |
| `bgemm32` | +13.9% | | **mean** | **+14.4%** |

**Every workload gains, and the spread is 7.6% to 26.0%.**

🔑 **There is no benefit/harm crossover on this configuration.** The question this run was designed
to answer — where along the arithmetic-intensity axis the tune stops helping — has the answer
"nowhere, on the split curve." That is the split curve's whole point: §5.7 documents the *original*
tune costing up to 29.6% on bandwidth-bound `membw` at 1560–1867 MHz, and the split design was
derived to remove exactly that. Twelve workloads say it did.

⚠️ **Do not read this as the split curve dominating everywhere.** §5.7.5 records that the original
tune still beats it on `gemm` *efficiency* from 1545–2625 MHz by up to 30.5%. This run does not
include the original tune and cannot speak to that trade.

## Throughput and power

Peak throughput **+17.7%** mean (range +12.1% `conv` to +23.5% `bgemm256`), band-mean throughput
**+10.5%**, band-mean power **−4.9%**.

⚠️ **The peak figure is mostly overclocking, not efficiency.** The split curve reaches ~2977 MHz
where stock reaches ~2593, so a higher peak is expected and is not a headroom result. The
matched-frequency efficiency table above is the one that isolates the tune's effect.

## Provenance, and a labelling defect this run exposed

**Configuration identified by clock signature, not assumed**: peak core 2977 MHz, peak memory
16301 MHz under load before launch. This card's signatures are stock ~2593, memory-only ~2584,
rebuilt repair ~2906, full tuned ~2947, **split ~2977**. The operator independently described the
applied curve as "≈925 mV at 3 GHz", which is the split design. n=1 signature match — recorded as
identification, not proof.

**A read-only watcher ran for the whole session** (`run-watcher.csv`), polling the Windows System
log for Event 4101 / `nvlddmkm` and checking the memory clock under load every 20 s. Result: **zero
driver-crash events and zero offset clears**, with the last loaded sample at 16301 MHz — so the tune
is demonstrably still applied at the *end*, not merely at the start. That matters because a driver
reset silently clears Afterburner offsets (2026-08-30), and any sweep after such an event would be
stock silicon under a tuned label.

⚠️ **`copy` was refused during the main run** at a transient 10.8% baseline and re-run alone in the
same session, per the tool's own instruction. Same configuration untouched, baseline re-verified at
4%. Kept in-session deliberately: cross-session `gemm` drift on this card runs ~1.47%.

⛔ **EVERY FILE FROM THIS RUN WAS ORIGINALLY NAMED `5060ti-stock-suite-*`.**
`Invoke-SuiteReplicate.ps1` hardcoded "stock" into the session label, which was true when written —
every suite run was stock — and became a lie the first time the script was pointed at a tuned card.
The `applied_settings` inside each file was correct and loud, but a filename is what a person skims.
Files renamed and `samples_file` updated with them; the script now takes `-ConfigurationLabel`,
defaulting to "stock" so r1–r8 naming is unchanged.

## Limits

**n = 1** on the split curve, against n = 5 stock. Single session. The comparison to stock uses the
r2–r6 mean, which spans four sessions, so between-session variance is in the baseline but not in
this run. A second split-curve suite would be needed before any per-workload ordering here is
treated as real.

## Related

`../suite-replicate-r2-20260830/` … `../suite-replicate-r6-20260905/` (the stock baseline),
`../splitcurve-clean-20260824/` (the `membw` fine-grid runs that established the design),
`../membw-anomaly-20260819/` (the mechanism the split curve repairs).
