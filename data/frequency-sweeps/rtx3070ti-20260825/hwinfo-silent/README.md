# Session B — SILENT BIOS with voltage telemetry, 2026-08-27

Collected on the Gigabyte RTX 3070 Ti GAMING OC, dual-BIOS switch in the **SILENT** position
(VBIOS `94.04.5a.00.91`), to test the prediction §5.5.3 recorded before the measurement existed.

## THE PREDICTION FAILED

> §5.5.3 predicted: if the OC BIOS's +23.11% matched-frequency power draw is voltage and nothing
> else, the SILENT floor should sit at **0.819 / √1.2311 = 0.738 V**.

**Measured floor: 0.812–0.819 V.** The OC floor is 0.819–0.825 V. Within this sensor's ~6–7 mV
quantisation the two BIOSes hold **the same voltage floor**. The predicted separation was 81 mV,
about twelve sensor steps; the measured separation is zero to one step.

This is the second branch of the outcome table written into `SESSION-B-PLAN.md` before collection:
*"if it reads near 0.819 V, voltage does not explain the power gap and §5.5.1 needs rewriting."*
That is what happened. **§5.5.1's "the overclock is almost entirely voltage" is wrong**, and
§5.5.3's account of what the OC BIOS spends its extra power on has to be rebuilt.

## The gap is real, reproduces, and is not voltage

Matched frequency, `gemm`, SILENT (today) against OC (2026-08-25). Both verified-quiet.

| MHz | SILENT V | OC V | ΔV | SILENT W | OC W | ΔW | SILENT xbar | OC xbar |
|---|---|---|---|---|---|---|---|---|
| 855 | 0.819 | 0.825 | +0.006 | 130.3 | 164.3 | **+26.1%** | 1335 | 1410 |
| 960 | 0.819 | 0.819 | **0.000** | 138.6 | 173.0 | +24.8% | 1335 | 1410 |
| 1065 | 0.812 | 0.819 | +0.007 | 145.7 | 184.0 | +26.3% | 1335 | 1410 |
| 1170 | 0.819 | 0.819 | **0.000** | 156.6 | 194.0 | +23.9% | 1335 | 1410 |
| 1275 | 0.819 | 0.819 | **0.000** | 161.4 | 196.6 | +21.8% | 1335 | 1410 |
| 1380 | 0.819 | 0.819 | **0.000** | 172.6 | 201.6 | +16.8% | 1335 | 1410 |
| 1485 | 0.812 | 0.819 | +0.007 | 188.3 | 218.7 | +16.2% | 1410 | 1410 |

- **Power gap: +22.27% mean**, against the +23.11% §5.5.1 measured on a different day from a
  different run. The effect reproduces.
- **Throughput gap: +0.42% mean.** The extra power buys essentially nothing, as §5.5.1 said.
- **Voltage gap: +0.003 V mean, exactly 0.000 at four of seven points.**
- **Memory clock is identical at 9251 MHz** in every position.

### What that leaves

Same voltage, same clock, same work, same memory clock — and 22% more power. Since P = V·I, the
honest restatement is that **the OC BIOS draws ~21.8% more current at the same voltage**, not that
it runs at a higher voltage.

The one systematic difference this session can see: **the crossbar clock floor is 1335 MHz on
SILENT and 1410 MHz on OC**, +5.6%, at every point below 1485 MHz where the two converge.

**That is a candidate, not a conclusion.** A +5.6% interconnect clock explaining a +22% power gap
is not something this data establishes, and it should not be written up as if it were. What is
established is the negative: it is not voltage, and it is not memory clock. Anything further needs
a measurement that separates the crossbar from whatever else the BIOS changes, and no such
measurement exists yet.

## Fine sweep — where the floor was read

`gemm`, 1200–1600 MHz, 10 points, n = 19–24 samples per point.

    1200  0.825 V  1335 xbar  158.7 W
    1245  0.819    1335       155.2
    1290  0.812    1335       163.3
    1335  0.812    1335       166.6
    1380  0.812    1335       170.3
    1410  0.812    1335       173.2
    1455  0.812    1380       177.6
    1500  0.812    1425       180.8
    1545  0.831    1470       194.3
    1590  0.850    1515       205.1

Six consecutive points at 0.812 V. The two lowest points read 0.819 and 0.825 — *higher* than the
middle of the band, which is the opposite of a voltage-frequency curve and is not explained here.
It does not affect the conclusion: every candidate reading is far above 0.738 V.

## What was collected, and what was not

| planned | outcome |
|---|---|
| `gemm` matched 852–2130, 13 pts | **two runs**, 16:53 and 17:03. Both 13/13, `aborted_by_user: false`. |
| `membw` matched 852–2130, 13 pts | ❌ **never collected.** No sweep output exists and no HWiNFO log covers a `membw` run. |
| `gemm` fine 1200–1600, 10 pts | ✅ 10/10 |

**The HWiNFO log filenames do not match their contents.** Established from the logs' own internal
timestamps and confirmed by the join:

| file as named | actually covers |
|---|---|
| `hwinfo-silent-gemm-matched.csv` | 16:36:39–16:49:42 — **nothing.** It was stopped 4 minutes before the first sweep started. Max power 74 W; no loaded samples at all. |
| `hwinfo-silent-membw-matched-ORPHAN.csv` | 17:03:23–~17:28 — the **second `gemm` matched run**. All 13 points bin cleanly, n = 19–58, power range 130.3–274.9 W matching that sweep exactly. |
| `hwinfo-silent-gemm-fine.csv` | 17:28:50–~17:32 — the **fine sweep**. Correct as named. |

The ORPHAN file keeps its misleading original name with a suffix rather than being renamed,
because the name is evidence about how the session ran.

**So the first matched run has no voltage data** and stands only as a throughput replicate. It is
a good one: run 1 against run 2 agrees to **−0.21% mean (−0.30 to −0.13%)**, and today against
Session A's SILENT sweep agrees to **−0.57% (−0.61 to −0.46%)** across seven shared targets.

## Provenance

All three sweeps `verified-quiet` — `encoder_util_pct` 0, `decoder_util_pct` 0,
`video_engines_allowed` false. Driver 610.88, schema 0.3.1.

**First sweeps in the project to record the enforced power limit.** Every session JSON here
reports `power_limit_enforced_w` 290.00, `power_limit_default_w` 290.00, `power_limit_w` 320.00 —
confirming the SILENT position and closing the gap §5.5.3 had to acknowledge for the OC session,
where the 310 W figure existed only in a hand-read note.

## Join parameters

`--min-power 120`, fixed **before** any voltage was inspected. Justification, in order:

1. The sweeps' own `power_avg_w` puts loaded draw at **130.3–275.3 W** (matched) and
   **155.2–205.1 W** (fine), independent of HWiNFO. Session A's SILENT sweep gave 129.9–277.1 W.
2. A power histogram of each HWiNFO log shows the idle population below 80 W and the loaded
   population above 155 W, with the gap straddling 120.
3. Anything above ~125 W would begin discarding the real 855 MHz point.

Every point retained n ≥ 19. The threshold was not revisited after the voltages were read.
