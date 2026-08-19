# Stock vs tuned, one chip, one session — 2026-08-19

The controlled version of the comparison `ROADMAP.md` calls *"the project's whole thesis in
one comparison."* The previous stock-versus-tuned figures came from runs on different days
with different background load (6.2% against 3.6%) and unmatched thermal state, and were
explicitly recorded as worth nothing. These two runs are the same RTX 5060 Ti, the same tool,
the same 13 target frequencies, roughly 90 minutes apart in one session.

**Applied settings are recorded for the first time** — see `APPLIED-SETTINGS.txt` and
`afterburner-gpu-profile.cfg`. Memory +2500 MHz, core on a V/F curve pinned flat near
3000 MHz at every voltage at and above ~925 mV, power limit 111%. That is the field nothing
can reconstruct after the fact, and its absence is why the earlier tuned data is unusable.

## Headline

At each configuration's own sustained maximum:

| workload | throughput | power | efficiency |
|---|---|---|---|
| `gemm` | **+12.1%** | **−2.9%** | **+15.4%** |
| `membw` | **+17.6%** | **−3.7%** | **+22.1%** |

This closely reproduces the earlier uncontrolled +13.1% / −2.5%, so that figure is
corroborated rather than overturned — it simply now has a controlled measurement behind it.

`membw`'s gain has a coherent mechanism: memory runs at 16301 MHz tuned against a 14001 MHz
rating, a ratio of 1.164 against a measured throughput ratio of 1.176. A bandwidth-limited
workload tracking memory clock is what theory predicts.

## The more interesting result: power at matched frequency

With the core clock **locked to the same value** in both runs, `gemm` does the same work for
far less power. Achieved clocks matched to within 0 MHz and temperatures to within 1 °C, so
this is neither a clock difference nor thermal drift:

| locked clock | throughput Δ | power Δ | efficiency Δ |
|---|---|---|---|
| 1852 MHz | −2.0% | **−18.1%** | +19.8% |
| 2010 MHz | −2.3% | **−26.4%** | +32.7% |
| 2167 MHz | +0.8% | **−19.9%** | +25.8% |
| 2317 MHz | −1.2% | **−18.1%** | +20.7% |

Throughput differences sit inside this workload's measured run-to-run spread (median 2.56%
between identical passes). **The efficiency gain is mostly power reduction at matched
frequency, not the higher peak clock.** That is the voltage guardband, visible in the only
terms this project can measure.

Below ~1545 MHz the sign flips — the tuned configuration draws *more* power (+4.4% at
1237 MHz). Plausibly the custom curve sets a higher voltage floor at low clocks than stock
would, but with no voltage readback on this hardware that is a hypothesis, not a finding.

## An anomaly that is NOT resolved

Across 1545–1852 MHz the tuned `membw` run is flat at ~295 GB/s while stock rises
312 → 332 → 342. That is 11–14% **slower** with more memory bandwidth available, at identical
core clock and temperature. It looks capped and there is no confident explanation.

**A confound was introduced into the tuned run and not the stock one.** A stability logger ran
concurrently during the tuned sweep, spawning `nvidia-smi` once per second — a process spawn
measured at ~42 ms in this project's own instrumentation work, and the same class of
contention that once cost `membw` 50.5% of its reported duration. The two runs are therefore
not methodologically identical.

The contention does not obviously explain the shape — a per-sample penalty should be roughly
uniform, and the top-end points are unaffected — but it cannot be ruled out.

**Treat the 1545–1852 MHz `membw` comparison as unusable.** The top-end figures and all of
`gemm` are far less exposed: `gemm`'s matched-frequency rows are internally consistent across
four frequencies and have a coherent mechanism.

## Other caveats that stay attached

- **Sequential, not interleaved.** All of stock, then all of tuned. Thermal drift remains
  confounded with condition. Proper interleaving alternates them.
- **n = 1 chip.** Nothing here speaks to chip-to-chip variation.
- **Frequency versus power, not voltage.** No documented API on this hardware reads voltage
  back. The curve was *set* at these voltage points, not verified at them. This must not be
  described as a measured undervolt.
- **No stability verdict.** The concurrent logger was killed before it wrote its session JSON,
  so only the raw 584-sample telemetry (`oc-stability-samples.csv`) exists. No crash occurred
  — the card held 2948–2985 MHz across 26 locked frequencies — but that is an observation, not
  the tool's judgement.
- **Filenames are misleading on the tuned run.** They read `...-oc-gemm-stock_sweep.csv`
  because the collection kit hardcoded a `-stock` suffix. Fixed in the kit afterwards; these
  files keep their original names. `machine-info-OC.txt` records
  `peak_sm_clock_mhz[gemm] : 2948`, against stock's 2598 in the CSVs, which is the
  authoritative discriminator.
