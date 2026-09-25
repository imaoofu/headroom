# §2 Related Work: proposed replacement text for §§2.1–2.5

**GPT Job 13, drafted by Claude on 2026-09-24 while GPT was at its usage limit.** A proposal only:
`docs/PAPER_DRAFT.md` is untouched. §2.6 (vendor auto-tuning) and §2.7 (datasets) are out of scope.

**Rules this draft follows** (from the job and from CLAUDE.md's contribution section):
- It is built only from sources `docs/RELATED-WORK.md` marks as read, with exceptions labelled.
- It says what each source did. It never uses "first", "novel" or "unpublished", and it does not
  regrow any of the four forms CLAUDE.md lists: "we found the rule", "we found it on consumer
  parts", "the floor voltage is per-card", "we showed that changing the V/F relationship moves the
  optimum".
- Every sentence resting on a partly read source carries a marker:

| marker | meaning |
|---|---|
| **[A]** | abstract or HTML only; the full text was not read |
| **[N]** | a news report of a primary source that was not reached |
| **[X]** | read and recorded in CLAUDE.md (2026-09-18), but **not yet in `RELATED-WORK.md`'s index**. Index it before this text goes in, or drop the sentence |

**Proposed new reference numbers** (the paper's list stops at [22]):

| # | source | read status |
|---|---|---|
| [23] | Guerreiro, Ilic, Roma, Tomás. *GPGPU Power Modeling for Multi-Domain Voltage-Frequency Scaling.* HPCA 2018, pp. 789–800. doi:10.1109/HPCA.2018.00072 | read in full, 2026-09-18 |
| [24] | Guerreiro, Ilic, Roma, Tomás. *Modeling and Decoupling the GPU Power Consumption for Cross-Domain DVFS.* IEEE TPDS 30(11):2494–2506, 2019. doi:10.1109/TPDS.2019.2917181 | read in full, 2026-09-18 |
| [25] | Mendes, Tomás, Roma. *Exploiting non-conventional DVFS on GPUs: application to Deep Learning.* SBAC-PAD 2020 | read from extracted text, 2026-09-22 |
| [26] | Mendes, Tomás, Roma. *Decoupling GPGPU voltage-frequency scaling for deep-learning applications.* JPDC 165:32–51, 2022. doi:10.1016/j.jpdc.2022.03.004 | read in full, 2026-09-18 |
| [27] | Price, Clark, Barsdell, Babich, Greenhill. K20 firmware voltage tables. arXiv:1407.8116, 2014 | read in full |
| [28] | Wang, Hao, Zhang, Wang. *Model-Free GPU Online Energy Optimization.* IEEE TSUSC 2023. doi:10.1109/TSUSC.2023.3314916 | **[A]** abstract only |

---

## What checking the current §§2.1–2.5 found

These are the reasons for most of the changes. Each was checked against the paper, the index or
the source on 2026-09-24.

| # | where | finding | severity |
|---|---|---|---|
| 1 | §2.1.1 positioning | Says the optimum moved *"with predictions registered before collection"* and that the curve was reshaped *"region by region"*. **CLAUDE.md retracted both on 2026-09-19**: the decisive manipulation was post hoc, and the contrast was not region-isolated (−98 MHz at 875 and 925 mV). The retraction never reached this paragraph | ⛔ false as written |
| 2 | §2.1.1 | No Mendes paper is cited. **SBAC-PAD 2020 [25] re-locates an EDP optimum under a changed V–F relationship** (1270 → 1530/1440/1530 MHz), which pre-empts the broad form of §5.5's causal claim | ⛔ missing bound |
| 3 | §2.1.1 | Guerreiro et al. [23] **measured the constant-voltage region on consumer NVIDIA in 2018**, with Afterburner and NVIDIA Inspector. §2.1.1 presents the ridge-point literature as datacenter-only | ⛔ missing bound |
| 4 | §2.3 | Quotes *"XGBoost achieving R² ≈ 0.9646 on Volta [2]"*. The index marks [2] **not read**, and its rule is that an unread source is never cited for a number | ⛔ rule broken |
| 5 | §2.3 | *"Related approaches… deadline-aware scheduling ⚠️"* has no citation. [22] (Wang et al., TPDS, read in full) is exactly that, and the paper already cites it in §2.7 | 🟡 unsourced |
| 6 | §2.4 | Calls ~42% LLM energy savings at 1–6% latency *"independent corroboration… the same order of magnitude as the 44.4% efficiency gap"*. Energy saved at a latency cost is not efficiency gain against the sustained maximum. The paper refuses this comparison for Mei's 5.24% and Zhang's 26.7% | ⛔ incommensurable |
| 7 | §2.2 | Says Leng et al. studied the GTX 480 and GTX 680. The index records **GTX 480/580/680/780, with Vmin measured across five physical GTX 780s** differing by a roughly constant offset. That is the fact that makes "the floor voltage is per-card" prior art | 🟡 incomplete |
| 8 | §2.2 | Says voltage is *"neither readable nor writable through any documented interface"*. **It is readable**: HWiNFO's core-voltage readings carry §5.5 and §5.7.3. It is not *writable* | ⛔ contradicts the paper |
| 9 | §2.2 | The GPU-Z "ASIC quality" sentence has **no source** in the index or the reference list | 🟡 unsourced |
| 10 | §2.1 | The compute/memory distinction cites [4], a placeholder (*"multiple; consolidate to one citation"*). It also points to §3.2 when the distinction is in **§3.3**, and §3.3.2 shows "memory-bound" is **frequency-dependent** on this card | 🟡 placeholder and wrong pointer |
| 11 | §2.5.1 | Treats the loong0x00 article and LACT #1147 as two sources, *"found independently"*. CLAUDE.md, verified via `gh api` on 2026-09-18: **same author (`Loong0x00`), same RTX 5090.** It also omits the earlier and closer prior art CLAUDE.md records (Hardwareluxx 2023, NVIDIA/open-gpu-kernel-modules #1266, overclockers.ru) **[X]**, and GIGAZINE's 2026-06-08 date **[N]** | ⛔ overcounts one source |
| 12 | §2.5 | Omits Guerreiro et al. [24]: **the observed V/F behaviour depends on how the frequency is changed** (NVML lock against clock offset). That is a methodology result, and §3.2 and 4c depend on it | 🟡 missing |
| 13 | §2.1 | HotPower's *"average 19.28% energy reduction for under 4% performance"* was **re-checked against the abstract today and is correct as written.** 18.91% for 3.45% is a single setting in the body. The index quotes the second, so a reader may think they conflict; they do not | ✅ no change |

---

## Proposed text

### 2.1 GPU DVFS and energy efficiency

Dynamic voltage and frequency scaling trades performance against power, and its application to
GPUs has been measured for over a decade. Mei, Yung, Zhao and Chu [20] report, on one GTX 560 Ti
across 37 applications, an average 19.28% energy reduction against the default setting for no more
than 4% of performance. ⚠️ **That is whole-system energy at the wall, against an 85 W idle floor of
which 29 W is the card.** This work measures board power throughout (§3.4), and energy figures of
different scope are never compared here without saying so.

The same group's later survey [19] moves the measurement to the GPU itself. On an ASUS Strix GTX 980
it sweeps the core clock from 480 to 1080 MHz against a 950 MHz default, with voltage held at a
fixed 0.987 V and energy read from the on-chip sensors. **30 of 42 kernels take their minimum energy
below the default clock, half of them between 680 and 880 MHz.** Locating a below-default,
board-level efficiency optimum on consumer GeForce silicon is therefore established, and this work
does not claim it. Its mean saving (R̂ 5.24%) is energy against the default clock and is not
comparable with the efficiency gains against the sustained maximum reported in §5. Tang et al. [15]
report the same valley shape for deep-learning training and inference on a P100, a V100 and a
consumer GTX 2080 Ti.

How strongly a workload responds depends on what bounds it. This work uses a compute-bound and a
bandwidth-bound kernel (§3.3). §3.3.2 then shows that on this hardware **"memory-bound" is itself
frequency-dependent**, so the distinction is used with that qualification.

### 2.1.1 The ridge point, and who has measured it

The shape behind the savings curve is a published mechanism. Schoonhoven et al. [18] define the
**ridge point**, the frequency at which core voltage stops being constant and begins rising, and
state the consequence directly:

> "Reducing the clock frequency beyond the ridge point does not make the GPU more energy efficient,
> as performance drops with f while v is constant below the ridge point."

They report ridges at 1025 MHz on a Tesla A100 and 1290 MHz on an RTX A4000, with predicted
energy-optimal clocks of 985 and 1298 MHz, close to the ridges. Their voltage readback is limited to
Ampere. For the V100 and the Titan RTX they fit a two-regime form to power data instead of reading
voltage (their Equation 3), so on those parts the flat floor is an assumption of the model. Afzal et
al. [10] model the same transition on A40, A100, H100 and H200 as a piecewise power fit with a
transition frequency f_t, and report that the energy optimum "clusters near f_t but does not
necessarily coincide" **[A]**.

**The constant-voltage region itself was measured on consumer NVIDIA hardware earlier.** Guerreiro
et al. [23] report, on a GTX Titan X (Maxwell) and a Titan Xp (Pascal), "two distinct regions for
the core voltage when scaling the core frequency: i) a constant voltage region, for lower
frequencies; and ii) after a specific frequency, the voltage starts increasing linearly with the
frequency". They read voltage with NVIDIA Inspector and MSI Afterburner, the tool lineage this work
uses. Their measurement is independent of their model: voltage enters the model as an unknown
estimated from power, and the readings validate it. Neither of their papers computes energy
efficiency or locates an optimal frequency; both are power models.

So the region is measured on Kepler, Maxwell and Pascal consumer parts [23, 24] and on Ampere
datacenter and workstation parts [18]. It is tied to the energy optimum on Ampere [18] and, in a
fitted model, on Ampere and Hopper [10]. **Among the sources read, none measures a Turing
voltage-frequency curve.** §5.5.7 reports one, on an RTX 2060 Super, where the rule cannot be
applied because voltage leaves the floor 6 mV at a time. A piecewise fit returns a breakpoint
whatever the curve does, so that class of method would not report such a card. *That is our
inference from the form of the models, not a limitation either paper states.*

**Changing the voltage–frequency relationship moves the optimum, and that is also published.**
Mendes, Tomás and Roma [25] decouple voltage from frequency on an AMD Vega 10 Frontier Edition,
writing voltage directly through `rocm-smi`. The EDP-optimal frequency for three of four CNN models
moves from 1270 MHz under the vendor's pairs to 1530, 1440 and 1530 MHz at the same 1.0 V. HotPower
2013 [20] made the observation in passing a decade earlier: for one application of 37, *"scaling
down f_core can save energy when V_core = 1.049 V, but this situation does not hold anymore when
V_core = 0.849 V."* Price et al. [27] edited a K20's voltage table point by point, but held
frequency fixed under the edited table and report no interior optimum.

**Positioning.** §5.5 does not claim the mechanism, its measurement on consumer parts, or that
moving the V/F relationship moves the optimum. What it does is narrower:
- On an NVIDIA card whose voltage cannot be written, it edits a region of the vendor's curve by
  hand, and predicts the new optimum from a floor voltage measured on other data.
- It **runs a negative control**, a larger edit above the floor. [25] has none, and it optimises
  EDP rather than throughput per watt, so the two optima need not coincide.
- ⚠️ **The manipulation's result was found in a run registered for a different prediction, which
  failed**. Only the control and the cross-architecture tests were registered in advance.
- ⚠️ **The two profiles differ in two regions, not one** (§5.5).
- Mendes et al. [26] state why this route is needed on NVIDIA: *"The sole inclusion of AMD devices
  comes from the reduced availability of drivers and convenient software APIs from other
  manufacturers (e.g., NVIDIA) for an independent and decoupled control over the GPU frequency and
  voltage."*

### 2.2 Voltage guardbands and manufacturing variation

Vendors set operating points with margin for worst-case silicon, temperature and ageing. Leng et
al. [8] measured the margin directly on consumer cards (GTX 480, 580, 680 and 780), undervolting
until program output became incorrect:

> "there exists about 20% voltage guardband on those GPUs spanning two architectural generations,
> which, if 'eliminated' completely, can result in up to 25% energy savings on one of the studied
> GPU cards."

Their per-card figures include a 9–18% guardband on the GTX 680 and geometric-mean savings of 21%
(GTX 680) and 15.8% (GTX 480). They find Vmin program-dependent. **Across five physical GTX 780s,
one card's Vmin sits above another's by a roughly constant offset.** Trakosa et al. [14] repeat the
direct measurement on three AMD RDNA3 consumer cards (RX 7600 XT, 7700 XT, 7800 XT). They reach
−300 mV on some workloads, report 14% average power saving, and find chip-to-chip variation across
the three models. Mendes et al. [26] find a 15–25% safe undervolt and a >20% guardband at all
frequencies on two AMD GPUs. Zamani et al. [16] go past the safe limit on a GTX 980, at fixed
frequency, and recover from the resulting faults in the kernel.

**All of these hold frequency and lower voltage, and their quantity is Vmin, a correctness limit.**
This work does the reverse. Frequency is varied, and voltage is observed through HWiNFO but cannot
be written through any documented interface (§3.2). Its quantity is the efficiency optimum, which
is tied to the dynamic V/F curve's load floor rather than to a failure edge. On a fine grid, the
floor's end bounds where to run from above rather than marking the peak (§5.5). Vmin and the load-floor voltage
are related but distinct and are not used interchangeably. **That the floor voltage differs from
card to card is prior art in its Vmin form [8, 14].** What §5.5.7 adds is its consequence for
prediction: borrowing one card's floor voltage for another mispredicts the optimum by a measured
amount.

At cluster scale, Sinha et al. [9] report 8% average performance variation (22% maximum) between
nominally identical GPUs of one SKU, with outliers 1.5× slower than the median, over more than
18,800 GPU-hours on five systems.

**Positioning.** The existence and approximate size of the guardband and of chip-to-chip variation
are established. This work adds open, released frequency–efficiency measurements on current
consumer parts across a range that contains the optimum. §5.7.7 measures the two levers,
undervolting at fixed frequency and lowering frequency, as substitutes rather than complements.

### 2.3 Prediction models for frequency scaling

Fan, Cosenza and Juurlink [1] predict a Pareto set of core and memory frequency settings for an
unseen kernel from static code features, without executing it. They train on 106 micro-benchmarks
and evaluate on a GTX Titan X (Maxwell, consumer) and a Tesla P100, across 85 core frequencies from
135 to 1392 MHz against four memory frequencies. Control is through NVML only, with no voltage
control and no curve reshaping. They report accurate extrema and Pareto sets on 10 of 12 test
benchmarks. Wang et al. [28] search clock settings online with a PID controller on an RTX 3080 Ti,
reporting 26.2% mean energy saving at +3.4% time across 74 applications **[A]**. Scheduling work
uses per-setting time and power models under deadlines [22].

**Positioning.** This work does not claim a better predictor. It is closest to §5.2's **null**, a
probe-based Ridge model that loses to a fixed constant, and not to §5.5. [1] reports success from
richer inputs than that null uses:
- static code features rather than probe points;
- a 2D core×memory space rather than 1D;
- purpose-built training rather than a 33×13 matrix with no feature columns.

The null does not contradict it. [1] also reports a hazard this work met independently (§5.4.2):
NVML lists settings that do not take effect, and on the Titan X requests above 1202 MHz silently
return 1202.

### 2.4 Energy–performance trade-offs in modern workloads

Deep-learning workloads show the same valley: Tang et al. [15] for training and inference, and
Mendes et al. [25, 26] for CNN training on AMD. Mendes et al. [26] report up to 38% energy and 41%
EDP reduction, with an average 36.7% EDP improvement across complete CNN training. For LLM inference,
Maliakel, Ilager and Brandic [3] characterise the same trade-off across five decoder-only models and
report that the decode phase is largely frequency-insensitive. Zhang et al. [6] report a 26.7% mean
efficiency gain for 5.8% performance loss on a V100 under a performance constraint.

⚠️ **None of these figures is the quantity in §5.1.** They are energy saved against a default
clock, EDP, or efficiency under a performance constraint. §5.1's 44.4% is unconstrained efficiency
gain against the sustained maximum. They are cited for the shape of the trade-off, not as
corroboration of a number.

### 2.5 Measurement methodology

GPU power figures reported by `nvidia-smi` are not raw instrument readings. Yang et al. [5]
document the built-in sensor's update frequency, transient response, and a boxcar averaging window
applied to reported values. Any work sampling power this way inherits those characteristics, and
§3.4 states the consequences.

**How the frequency is changed changes what is observed.** Guerreiro et al. [24] report that with
NVML clock control the core voltage shows two regions, constant then rising. When frequency is
changed through graphics-clock offsets in `nvidia-settings`, *"the voltage stays constant across
all frequencies."* This work locks clocks through NVML (`nvidia-smi -lgc`), the case in which they
see the two regions. Its offset experiment (4c) found the two regions **do** survive
`nvmlDeviceSetClockOffsets` on Blackwell. That differs from their Maxwell/Pascal/Kepler result, and
the contrast changes method and generation together.

### 2.5.1 The crossbar clock domain

§5.7.3 reports a bandwidth plateau that goes with a low crossbar (XBAR) clock under a flattened V/F
curve. Much about that domain is already public, and this work claims none of it:
- **The domain.** loong0x00's analysis of GB202 (RTX 5090), published 2026-08-13 [11], documents
  XBARCLK's own PMU object, clock source, 127-point V/F table and control path, and a 0.8999:1
  GPC-to-XBAR constraint. A news report dated 2026-06-08 describes RTX 5090 vBIOS work in which the
  crossbar clock "can only be partially adjusted by swapping the vBIOS" **[N]**.
- **Raising it.** LACT issue #1147 [12] applies +60 to +450 MHz XBAR offsets on an RTX 5090 for up
  to +10.6% FPS. ⚠️ **[11], [12] and a related NVIDIA kernel-module issue are by one author on one
  card**, so they are a single source, not independent corroboration **[X]**.
- **Capping it.** That kernel-module issue (NVIDIA/open-gpu-kernel-modules #1266) caps XBAR at
  1493 MHz and reports FurMark falling from 256 to 173 FPS, at a higher core clock and unchanged
  DRAM clock **[X]**.
- **Undervolting lowers it.** A Hardwareluxx forum post of 2023-01-25 reads the crossbar clock
  about 150 MHz lower under undervolt on an RTX 4090, with no performance measured **[X]**.
- **Mitigating it.** An overclockers.ru article (2026-08-18) warns that Afterburner undervolting
  imposes an invisible XBAR ceiling, and proposes workarounds **[X]**.
- **The general idea.** A 2013 patent [13] decouples an interconnect clock from a core clock so a
  slow interconnect stalls a faster core. It is a CPU/uncore closed-loop controller, cited so a
  reviewer need not raise it.

**What §5.7.3 contributes is a measured association with a predicted repair, not a mechanism.**
- a flattened curve goes with a collapsed crossbar-to-core ratio and a ~300 GB/s plateau, in GB/s,
  against a stock control;
- a repair stated in advance removes both;
- the same setting helps one kernel and harms another.

The crossbar was never set independently, and the stock control ran at stock memory clock, so
mediation is not shown (§5.7.3).

The searches did not find XBAR in NVIDIA's own documentation. But the Blackwell whitepaper could
not be text-extracted, the NVAPI headers and full DCGM reference were not searched, and non-English
patent filings were not reached. **The supportable statement is "not found in the sources we could
read".**

---

## Mapping: each current passage → its replacement, and why

| current (§, opening words) | replacement | reason |
|---|---|---|
| 2.1 ¶1 "Dynamic voltage and frequency scaling is a mature technique…" | 2.1 ¶1, kept in substance | HotPower figure re-verified (finding 13); scope warning kept |
| — | 2.1 ¶2 (Mei 2017, Tang 2019) | the consumer below-default optimum is prior art, and §2.1 did not say so; [19] and [15] are read and already in the reference list |
| 2.1 ¶2 "Workload character strongly mediates… [4]… (§3.2)" | 2.1 ¶3 | placeholder citation removed, pointer corrected to §3.3, frequency-dependence qualification added (finding 10) |
| 2.1.1 ¶1–2 ridge point, A100/A4000, [10] | 2.1.1 ¶1–2, kept | [10] marked **[A]**; "neither is a consumer GPU" dropped, because ¶3 now names consumer measurements |
| 2.1.1 ¶3 "What their method can and cannot see" | folded into 2.1.1 ¶2 and ¶4 | same content, shorter |
| — | 2.1.1 ¶3 (Guerreiro [23]) | the 2018 consumer measurement was missing (finding 3) |
| 2.1.1 ¶4 "no Turing voltage-frequency curve has been measured in this literature" | 2.1.1 ¶4, **"among the sources read"** | narrowed to what the search supports; the Turing statement itself still holds against the index |
| — | 2.1.1 ¶5 (Mendes [25], HotPower aside, Price [27]) | the broad form of the causal claim is pre-empted (finding 2) |
| 2.1.1 "Positioning. …region by region… with predictions registered before collection" | 2.1.1 Positioning, rewritten | two retracted clauses removed and the registration history stated (finding 1); Mendes [26] quote added |
| 2.2 ¶1–3 Leng et al. | 2.2 ¶1–2 | all four cards and the five-GTX-780 per-card result added (finding 7) |
| 2.2 "First, it studied consumer cards…" / "Second… voltage is neither readable nor writable" | 2.2 ¶3 | "readable" corrected (finding 8); the Vmin/load-floor distinction and the per-card prior art made explicit |
| 2.2 ¶4 Sinha et al. + GPU-Z "ASIC quality" | 2.2 ¶4, Sinha only | ASIC-quality sentence dropped: unsourced (finding 9) |
| 2.2 "The guardband finding is not a 2015 NVIDIA artifact" (NAVIgator) + "It moves the OTHER lever" | 2.2 ¶2–3 | merged, with [26] and [16] as further fixed-frequency undervolting work |
| 2.3 ¶1 Fan et al., "[2]… R² ≈ 0.9646", "deadline-aware scheduling ⚠️" | 2.3 ¶1 | [2]'s number removed (finding 4); [22] cites scheduling (finding 5); [28] added **[A]** |
| 2.3 Positioning | 2.3 Positioning, kept | unchanged in substance |
| 2.4 "…approximately 42% energy savings… useful independent corroboration…" | 2.4, rewritten | incommensurable comparison removed (finding 6). ⚠️ **The 42% and 180–2842 MHz figures are not repeated**, because the index records [3] only as "read" with no figures checked. Re-verify before restoring them |
| 2.5 Yang et al. | 2.5 ¶1, kept | — |
| — | 2.5 ¶2 (Guerreiro [24]) | methodology result the paper relies on (finding 12) |
| 2.5.1 "Searched 2026-09-06…" through "not documented by the vendor" | 2.5.1, restructured | one-author overcount corrected; earlier and closer prior art added with **[X]**/**[N]** (finding 11); today's §5.7.3 wording kept |
| 2.5.1 "The narrower claim is the defensible one…" and "One thread remains unresolved…" | dropped | process history, which belongs in the search logs rather than in the paper |

---

## Before this goes into the paper

1. **Index the [X] sources in `RELATED-WORK.md`**, or drop their sentences. They are Hardwareluxx
   #184 (2023-01-25), NVIDIA/open-gpu-kernel-modules #1266, overclockers.ru (2026-08-18), and the
   one-author finding about [11]/[12]. CLAUDE.md records them as read, with the source record in
   `docs/gpt-findings/2026-09-18-xbar-prior-art.md`.
2. **Re-open [3]** (Maliakel et al.) for its figures if §2.4 should carry numbers.
3. ⛔ **Checked: the INTRODUCTION carries the retracted contribution sentence verbatim**
   (`PAPER_DRAFT.md` lines 57–62): *"we reshape the vendor's voltage-frequency curve region by
   region… moving +465 MHz in 12 of 12 workloads… with every prediction registered before
   collection"*. CLAUDE.md retracted all three clauses on 2026-09-19 and gives the replacement
   sentence. Line 54–55's *"Every prior treatment we found observes that correspondence… This work
   intervenes on it"* is also false in its broad form, because Mendes et al. [25] intervene. This is
   the same propagation failure as §2.1.1 (finding 1), in the paper's most-read paragraph. §5.5
   itself is already corrected (line 2189: *"saying '+465 MHz in 12 of 12' would overstate
   this"*). ⚠️ Line 66 says Trakosa et al. used *"six Radeon boards"*; the index and §2.2 say three
   models. Check the paper before either is repeated.
4. **Add [23]–[28] to the reference list** with their read status, in the format of [18]–[22].
5. The claims auditor pins no §2.1–2.5 sentence (they are unaudited prose), so none of this changes
   the claim count. Run `python analysis/verify_citations.py --check` after the reference list
   changes.
