# Headroom — paper draft

> **Status: complete in structure, still a draft in places.** Results rest on **538 committed
> sweeps across four consumer GPUs**, including core-voltage and crossbar telemetry.
> **292 numbers are pinned by `analysis/audit_claims.py`**, which recomputes each from the source
> CSVs at audit time and fails if the text and the data disagree; it runs on every push. That count
> is itself pinned, so adding a claim without updating this line fails the audit. It counts the
> tool's whole coverage — the paper, two data READMEs, and `CLAUDE.md` — not the paper's share
> alone. No `[PENDING]` placeholders remain, but **14 numbered sections carry no claims at all** —
> `--coverage` lists them, and a green audit says nothing about those. **That count is now pinned
> too**, as of 2026-09-05.
>
> **No section carries a `- DRAFT` marker any more.** That marker meant "written the day the
> measurements were taken, no second pass"; the last three were on 3.5 and 5.7 and both had their
> pass on 2026-09-04. It does NOT mean every measurement is clean - 5.7.4 and 5.7.5 still predate
> the capture-software finding of 5.4.4 and say so in place, and a prose pass cannot fix that.
>
> Citation reliability is flagged per entry in [References](#references). Anything marked
> ⚠️ needs the primary source opened before it appears in a submitted version.

---

## Abstract

Graphics processors ship with conservative default operating points, because a vendor's
voltage-frequency behaviour must hold across millions of individually varying dies for a warranty
period measured in years. That margin, and the fact that a GPU's energy-optimal core frequency
lies below its default clock, are established results on hardware from 2013 through 2022 — on
consumer parts as well as datacenter ones. **What is not available, for silicon later than 2014, is
the data.** The one released consumer collection that sweeps far below stock covers a GTX 980, a
2014 part. The modern consumer sets released alongside it — a GTX 1080 Ti and an RTX 2070 Super —
sweep a narrow window bracketing their default clock, reaching only 89% of it, while the efficiency
optimum on a comparably swept datacenter part sat at 62% of maximum. A reader wanting to re-analyse
the region where the optimum sits, on any consumer architecture after Maxwell, has no sweep that
descends into it.

This work contributes an open dataset of consumer-GPU frequency, power and performance
measurements swept across 40–100% of maximum core clock, released with its collection tooling and
a locked protocol: **538 dataset-grade sweeps across four chips and three architectures** — 478 on
an RTX 5060 Ti (Blackwell GB206), 25 on an RTX 3070 Ti (Ampere GA104), 18 on an RTX 2060 Super
(Turing TU106), 14 on an RTX 3060 (Ampere GA106), and three early three-point verification runs.

On a public V100 reference set, running each of 33 workloads at its own efficiency optimum rather
than at stock recovers 44.4% efficiency on average. Per-workload *prediction*, however, does not
beat a single fixed frequency — 0.883% mean regret against 0.837%, leave-one-workload-out. That
null inverts under a performance constraint: at a 95% floor, probe-based selection reaches 25.4%
mean efficiency gain where the best fixed frequency reaches 4.9%. The fitting earns none of it,
since straight-line interpolation between four probes beats every fitted variant, and the fitted
model only appears to win by violating the floor it was given.

The central result concerns *where* the optimum sits, and it tests a **published relationship
rather than a new one**. That the optimum coincides with the highest frequency the
voltage-frequency curve reaches at its flat low-voltage region — the **ridge point** — was reported
by Schoonhoven et al. (arXiv:2211.07260) on an A100 and an RTX A4000. That changing the
voltage-frequency relationship moves the optimum is also published: Mendes, Tomás and Roma
(SBAC-PAD 2020) moved an EDP optimum on an AMD Vega 10 by writing voltage directly. On NVIDIA,
where voltage cannot be written through any documented interface, this work edits a region of the
vendor's curve instead, and adds a negative control:

> **On four consumer GPUs across three architectures we locate the V/F curve's low-voltage region
> and the energy-efficiency optimum, and on one of them we change the curve and re-locate the
> optimum: switching between two profiles whose decoded curves differ by +465 MHz below 840 mV
> moved the median twelve-workload optimum by +465 MHz, with all twelve workloads moving upward; a
> separate, larger edit ABOVE the floor moved the median by nothing. We identify a card on which
> the rule cannot be applied at all, because its voltage leaves the floor six millivolts at a
> time.**

⚠️ **How far that sentence reaches:**
- **The causal evidence is one chip and one profile contrast.** The twelve workloads are repeated
  outcomes on it, and their shifts range from +79 to +540 MHz.
- **The control is partly leaky.** It left the median unmoved but moved 4 of 12 workloads against
  the same-session stock bracket.
- **The two profiles also differ by −98 MHz at 875 and 925 mV**, a sixth of the control's dose.
- **The manipulation's result was found in a run registered for a different prediction, which
  failed.** The control and the cross-architecture tests were registered in advance.
- **On a fine grid, the top of the floor bounds the optimum from above rather than marking its
  peak.**

⛔ **This paragraph carried the version retracted on 2026-09-19 until 2026-09-24**: *"we reshape
the vendor's voltage-frequency curve region by region… moving +465 MHz in 12 of 12 workloads…
with every prediction registered before collection"*, introduced by *"Every prior treatment we
found observes that correspondence… This work intervenes on it."* The retraction reached
CLAUDE.md and §5.5, not the abstract. The last sentence was also false once Mendes et al. was
read on 2026-09-22.

⛔ The floor *voltage* does not transfer — 0.631 V, 0.720 V, 0.756 V and 0.812 V across the four
cards. That per-chip voltage variation is itself established (Leng et al., MICRO-48 2015, across
five physical GTX 780s; Trakosa et al., IOLTS 2025, on six Radeon boards); what we add is its
consequence for prediction, measured: borrowing the 5060 Ti's 0.720 V for the RTX 3060 predicts
~1530 MHz against a true optimum of 1260 MHz, a **270 MHz** error.

On consumer hardware, a bandwidth-bound workload plateaus under a flattened voltage-frequency
curve. Each link is measured: core voltage pinned across a rising core clock, the crossbar clock
pinned with it, and bandwidth ceasing to scale. A repair derived from that diagnosis behaved as
predicted. ⚠️ **The links are measured as an association, not isolated as causes.** The crossbar
was never set independently, and the stock control is not memory-clock matched (§5.7.3). That the
crossbar is a distinct, voltage-coupled clock domain invisible to `nvidia-smi` was documented
independently on Blackwell in August 2026 by community reverse-engineering, slightly ahead of this
work; the domain is therefore not our finding. The measured association from a flattened curve to
a bandwidth plateau, with a stock control and a repair predicted in advance, is. Comparing two vendor BIOS positions on
one 3070 Ti, the "OC" position draws roughly a quarter more power at matched frequency for 0.56%
more peak compute; a prediction registered in advance that this difference was voltage was
**refuted**, both positions holding the same voltage floor while the difference proved to be a
roughly constant 34 W offset that does not scale with core clock and remains unexplained.

A methodological result affects all of the above and, we suspect, other work: ordinary desktop
capture software depresses measured GPU throughput and inflates run-to-run spread roughly
five-fold, invisibly at idle. Measurements taken without controlling for it are biased downward in
the mid-band.

**Limits are stated throughout and are not incidental.** Four chips, one unit each, so nothing
here separates a property of a model from a property of an individual die; every *tuning* result
comes from a single card. ⚠️ This abstract said "three chips" in one paragraph and four in another
until 2026-09-13. Nothing here outperforms vendor boost algorithms, and no claim is made to having
discovered guardband, inter-chip voltage variation, the ridge-point relationship, the existence
of a below-default consumer optimum, or that changing the voltage-frequency relationship moves the
optimum — **all five are established literature, and §2 says by whom.** What is contributed is an
open, current-generation, reproducible dataset over the range that existing releases omit, and a
region-targeted test of the ridge-point relationship on NVIDIA hardware, with a negative control.
⛔ This sentence ended *"a causal test of a relationship the prior work only observes"* until
2026-09-24.

---

## 1. Introduction

Graphics processors ship with conservative default operating points. A vendor's default
voltage-frequency behaviour must hold across millions of individually varying dies, in unknown
thermal environments and unknown chassis, for a warranty period measured in years. That requirement
necessarily produces margin, and the margin is not small: Leng et al. [8] measured approximately a
20% voltage guardband on commercial GPUs, and showed that eliminating it entirely would yield up to
25% energy savings.

That result is a decade old, and it was obtained on cards — the GTX 480 and GTX 680 — released in
2010 and 2012. In the intervening period consumer GPU power management has changed considerably:
successive generations of automatic boost, finer-grained factory binning, and per-chip
characterisation now shipped as standard.

⚠️ **That comparable margin remains on consumer parts IS established**, and this paragraph claimed
otherwise until 2026-09-13. Mei, Wang and Chu measured a below-default, board-level efficiency
optimum on a GeForce GTX 980 in 2017 — 30 of 42 kernels minimising below the default clock [19] —
and Tang et al. reported the same direction on a GTX 2080 Ti in 2019 [15]. **What is not
established is the position on current silicon, and what does not exist is released data over the
range where it sits.** Those are narrower questions than the one this paragraph used to pose, and
they are the ones this work answers.

**Why margin is worth locating at all needs stating, because on its face the trade looks bad.**
Moving a chip to its efficiency optimum costs performance — on the hardware measured here, up to
40.6% of it on a compute-bound workload — and no one chasing frame rate would accept that. The
answer is that raw performance is the objective in fewer deployments than it appears to be. Where
a fixed power budget is the binding constraint — a rack, a cooling envelope, a battery, a rented
instance billed on draw — the quantity that determines total work done is performance *per watt*,
not performance. That makes the trade arithmetic rather than a sacrifice: the same measurement
that costs 40.6% of per-chip throughput improves work per joule by 63.1%, and under a fixed power
budget an improvement in work per joule *is* an improvement in aggregate throughput of the same
size. Per-chip performance falls and total output rises.

**The unconstrained optimum is nonetheless the wrong form of the question, and this paper reports
both forms.** Best efficiency at any cost gives up a mean 13.7% of performance on the reference
dataset, which almost no operator wants. Constrained to keep at least 95% of stock performance,
the same data gives up **3.3%** on average for **23.4%** less power (§5.6) — two-thirds of the
available gain for a quarter of the cost. That constrained form is what a deployment would
actually run, and §5.6.1 shows it is also the form under which knowing the workload starts to
matter. Where the constraint is latency rather than power, none of this applies, and the paper
does not argue otherwise.

Answering that question from published data turns out not to be possible, for a reason that is
itself worth reporting. Two public DVFS datasets covering consumer GPUs exist, and both sweep core
frequency only **at and above** the card's rated boost clock — 101–126% for a GTX 1080 Ti, 95–118%
for an RTX 2070 Super. An efficiency optimum lies *below* stock: in the one public dataset that
sweeps low enough, it sits at 62% of maximum frequency. The existing consumer datasets therefore
cannot locate an optimum, and their correspondingly small measured efficiency gaps (1.00% and 3.34%)
invite precisely the wrong conclusion — that consumer GPUs have little headroom — when what they
actually show is a truncated measurement range (§2.7).

A second constraint shapes what can be measured rather than what has been. On the hardware studied
here, GPU voltage cannot be *set* through any documented interface, and the vendor management API
does not report it either: enumeration of the driver's full management API surface returns no
voltage-related function among 260 device operations (§3.2). It can be *read* through third-party
instrumentation, and §5.7.3's mechanism depends on doing so - but a quantity that can only be
observed, never commanded, is not an independent variable. Direct guardband measurement in the
manner of [8], which requires undervolting until failure, is therefore unavailable. What remains accessible — and what this work measures — is
the relationship between core frequency, power draw, and delivered performance.

This paper makes three contributions:

1. **An open dataset** of consumer-GPU frequency–power–performance measurements swept across
   40–100% of maximum core clock, a range that contains the efficiency optimum, released with the
   collection tooling and protocol.
2. **A characterisation of why existing public consumer DVFS data cannot answer efficiency
   questions**, placing each dataset on a common axis of swept range relative to rated boost clock,
   and reproducible in a single script.
3. **An evaluation of whether per-unit measurement is worth its cost** against a fixed-frequency
   policy — reported including the case where it is not. On the reference dataset, a probe-based
   model ties a single constant frequency, while the same probes reconstruct the full efficiency
   curve accurately enough to reduce measurement effort by 77%. Those are distinct results and are
   reported as such.

🔑 **The contribution is an intersection, not an ingredient.** Every individual piece of this has
been done somewhere. Sub-stock sweeping is established, on datacenter parts [10] and on consumer
parts a decade ago. Voltage guardbands are measured [8]. Chip-to-chip variation is characterised [9].
The crossbar is a documented clock domain [11] that others have deliberately tuned [12], and
interconnect-stalls-core is patented prior art [13]. What has not been done is the **combination**:
current-generation consumer silicon, swept below stock, with voltage telemetry, released as
downloadable per-frequency data — plus one mechanism result that requires exactly that combination
to be visible at all.

That last clause is structural rather than fortunate. §5.7.3's plateau could not have been found by
the datacenter studies (wrong hardware), by the crowdsourced undervolting databases (single operating
points, no sweep), or by the overclocking work on the same domain (opposite direction, and no
bandwidth measured). It needed all four legs at once, which is the argument for the dataset as much
as for the finding.

Two claims are explicitly **not** made. This work does not outperform vendor boost algorithms, which
already incorporate per-chip factory binning and against which a small independent study has no
plausible advantage. And it does not claim the discovery of guardband or of inter-chip variation;
both are established [8, 9]. The contribution is open, current-generation, reproducible measurement
of a relationship whose public data is either datacenter-only or swept over too narrow a window to
contain the answer.

⚠️ **These claims have been searched against, not merely asserted.** Two delegated literature sweeps
on 2026-09-06 — fourteen agents, roughly sixty queries — were pointed at falsifying rather than
confirming them. Two claims narrowed as a result and are stated here in their narrowed form; none
collapsed. §2.5.1 records what those sweeps could *not* reach, which is the part that bounds how
strongly any absence here can be read.

---

## 2. Related Work

### 2.1 GPU DVFS and energy efficiency

Dynamic voltage and frequency scaling is a mature technique for trading performance against power,
and its application to GPUs has been studied for over a decade. Measurement studies established
early that substantial energy savings are available at modest performance cost. Mei, Yung, Zhao and
Chu (HotPower 2013) report an average 19.28% energy reduction for under 4% performance loss across
37 benchmark applications on a GTX 560 Ti — read in full and confirmed against the source. ⚠️ **That
figure is whole-system energy measured at the wall, against an 85 W idle floor of which only 29 W is
the card**, not board power, which is what this work measures throughout (§3.4). Energy figures
reported at different measurement scopes are never compared directly here without saying so.

Workload character strongly mediates this effect. Compute-bound kernels scale close to linearly
with core clock, while memory-bandwidth-bound kernels are limited elsewhere and are comparatively
insensitive to it [4]. This work reproduces that distinction directly (§3.2) and uses it to select
benchmark workloads.

### 2.1.1 The ridge point

The shape behind that savings curve is a published mechanism, not folklore. Schoonhoven et al.
[18] (*Going green: optimizing GPUs for energy efficiency through model-steered auto-tuning*,
Kernel Tuner, arXiv:2211.07260) define the **ridge point** — the frequency at which core voltage stops
being constant and begins rising — and state the consequence directly:

> "Reducing the clock frequency beyond the ridge point does not make the GPU more energy efficient,
> as performance drops with f while v is constant below the ridge point."

They measure the ridge at **1025 MHz (70% of peak) on a Tesla A100** and **1290 MHz (72% of peak) on
an RTX A4000**, with predicted energy-optimal clocks of 985 and 1298 MHz — close to the observed
ridge points. **Both parts are datacenter and workstation silicon; neither is a consumer GPU.** [10]
models the same transition as a piecewise power fit with a transition frequency f_t on A40, A100,
H100 and H200, and reports that the energy optimum "clusters near f_t but does not necessarily
coincide" — a qualification §5.5 also makes about its own result, on different hardware.

**What their method can and cannot see.** Their voltage readback is architecture-limited, and they
say so: querying core voltage *"is only available with fairly recent NVIDIA drivers (510 and newer)
in combination with **Ampere** GPUs (e.g. A100, A4000, A6000)"*. For the rest — *"such as the Tesla
V100 and Titan RTX"* — they do not measure voltage at all but estimate it, assuming *"there exists
a threshold τf_t after which the voltage increases with a rate β"* and fitting that two-regime form
to **power** data (their Equation 3). **The flat floor is an assumption of the model for those
parts, not an observation of them**, and the two ridge points they report are both Ampere.

Two consequences matter for §5.5. First, **no Turing voltage-frequency curve has been measured in
this literature** — their one Turing part is in the group whose voltage could not be read — which is
the architecture on which §5.5.7 reports the rule becoming undecidable. Second, a piecewise fit
returns a breakpoint whatever the underlying curve does, so this class of method has no failure mode
that reports "no floor here". *That second point is our inference from the form of the model, not a
limitation either paper states.*

**Positioning.** The mechanism, and its location on datacenter and workstation parts, is
established. So is its constant-voltage region on consumer NVIDIA parts: Guerreiro et al.
(HPCA 2018) measured it on a GTX Titan X and a Titan Xp with MSI Afterburner. And moving the
optimum by changing the voltage–frequency relationship is published too: Mendes et al.
(SBAC-PAD 2020) moved an EDP optimum on an AMD Vega 10 by writing voltage directly. §5.5 is
narrower than any of these:
- on an NVIDIA card whose voltage cannot be written, it edits a region of the vendor's curve;
- it predicts the new optimum from a floor voltage measured on other data;
- it adds a negative control, a larger edit above the floor.

⚠️ **The manipulation's result came from a run registered for a different prediction, which
failed; the control and the cross-architecture tests were registered in advance.** The two profiles
differ in two regions, not one (§5.5). ⛔ This paragraph said §5.5 changes the curve *"region by
region… with predictions registered before collection"* until 2026-09-24. Both clauses were
retracted in the project notes on 2026-09-19, and the Mendes result was read on 2026-09-22.
`docs/drafts/section2-related-work-proposal.md` proposes the full rewrite of §§2.1–2.5.

### 2.2 Voltage guardbands and manufacturing variation

Vendors set operating points with margin for worst-case silicon, temperature, and ageing. Leng et
al. [8] measured this margin directly on commercial off-the-shelf cards by progressively undervolting
until program output became incorrect, and report:

> "there exists about **20% voltage guardband** on those GPUs spanning two architectural
> generations, which, if 'eliminated' completely, can result in **up to 25% energy savings** on one
> of the studied GPU cards."

Per-card figures are finer-grained: a 9–18% guardband between nominal voltage and Vmin on a GTX 680,
geometric-mean energy savings of 21% (GTX 680) and 15.8% (GTX 480), with savings ranging 14–25% and
8–22% respectively. They further establish that Vmin is **program-dependent** rather than a single
per-chip constant, and that voltage noise affects it more than process or temperature variation.

**Two points about [8] matter for positioning this work, and neither is a criticism of it.**

*First, it studied consumer cards — GTX 480 (Fermi, 2010) and GTX 680 (Kepler, 2012).* The
guardband question has therefore already been answered on consumer silicon; it has simply not been
revisited on parts more than a decade newer, whose power management (successive GPU Boost
generations, finer factory binning) differs substantially.

*Second, and more fundamentally, [8] measures a quantity this work cannot access.* They undervolt
directly and detect the Vmin failure point. On the hardware studied here, voltage is neither
readable nor writable through any documented interface (§3.2). This work therefore measures the
**frequency–power–efficiency** relationship, not the voltage guardband. These are related but
distinct quantities and are not presented as interchangeable.

Chip-to-chip variation has been characterised at cluster scale by Sinha et al. [9], who collected
over 18,800 hours of data across more than 90% of the GPUs in five HPC systems (Summit, Vortex,
Frontera, Longhorn, Corona) and report **8% average performance variation (max 22%) between
nominally identical GPUs of the same SKU**, with outliers up to **1.5× slower than the median GPU**.
Consumer-facing exposure of such variation has been limited and short-lived — GPU-Z's "ASIC quality"
reading surfaced leakage-based binning for a period before being deprecated as unreliable.

**Positioning.** The existence and approximate size of both the guardband and inter-chip variation
is therefore *established*, not novel. What this work adds is open, released measurement of the
frequency–efficiency relationship on current consumer parts, across a range that includes the
optimum.

**The guardband finding is not a 2015 NVIDIA artifact.** NAVIgator [14] repeats the direct
measurement on three modern AMD RDNA3 consumer cards (RX 7600 XT, 7700 XT, 7800 XT), reaching the
full −300 mV offset on some workloads and reporting **14% average power saving**, with stability
judged by silent data corruption rather than by crash alone. It also finds real chip-to-chip
variation — "the 7700 cards exhibit the largest voltage-margins followed by the 7600 and 7800-series
cards" — on three chips, which is more per-architecture replication than this study has.

⚠️ **It moves the OTHER lever, and that matters for reading it against §5.7.7.** Its abstract is
explicit: *"Reducing the supply voltage, while maintaining a fixed frequency."* Voltage is varied,
frequency is held. This work does the reverse — frequency is varied and voltage is observed, because
voltage cannot be written through any documented API on the hardware here (§3.2). §5.7.7 measures
those two levers to be substitutes rather than complements, so the two studies are attacking one
inefficiency from opposite sides rather than measuring different things.

### 2.3 Prediction models for frequency scaling

The closest prior work, Fan, Cosenza and Juurlink [1], predicts a Pareto-optimal set of core and
memory frequency configurations for an unseen kernel from static code features, without executing
the kernel. They train on 106 synthetic micro-benchmarks and evaluate on a **GTX Titan X (Maxwell,
consumer)** and a **Tesla P100**, sweeping 85 core frequencies from 135–1392 MHz against 4 memory
frequencies through **NVML only — no voltage control and no curve reshaping** — and report accurate
extrema and Pareto-set predictions on 10 of 12 test benchmarks. A follow-up compares six model
families and reports XGBoost achieving R² ≈ 0.9646 on Volta [2]. Related approaches predict
execution time and power across frequency settings for deadline-aware scheduling ⚠️.

**Positioning.** This work does not claim a better predictor than [1]. **It is closest not to §5.5's
causal V/F-curve result but to §5.2's null** — the probe-based Ridge model that loses to a fixed
constant. Fan et al. report success at predicting per-kernel optimal configurations from richer
inputs than that null uses: static code features rather than probe points, a 2D core×memory space
rather than 1D, and purpose-built micro-benchmark training rather than a 33×13 matrix with no
feature columns. That difference is stated here so the null is not read as contradicting a published
success. [1] also corroborates a measurement hazard found independently in this work (§5.4.2): NVML
reports some configurations as supported when the setting call does not actually change the
frequency — on the Titan X, requests above 1202 MHz silently return 1202.

### 2.4 Energy-performance tradeoffs in modern workloads

Recent work characterises LLM inference under DVFS across five decoder-only models and four NLP
benchmarks, sweeping 180–2842 MHz, and reports approximately 42% energy savings for a 1–6% latency
increase, noting that the decode phase is largely frequency-insensitive [3]. That figure is a useful
independent corroboration: it is the same order of magnitude as the 44.4% efficiency gap measured
here on a different architecture and a different workload class (§5.1).

### 2.5 Measurement methodology

GPU power figures reported by `nvidia-smi` are not raw instrument readings. A detailed study of
NVIDIA's built-in power sensor documents its update frequency, transient response, and a boxcar
averaging window applied to reported values [5]. Any work sampling power through `nvidia-smi` — this
work included — inherits those characteristics, and §3.4 states the consequences explicitly rather
than treating the sensor as ground truth.

### 2.5.1 The crossbar clock domain, and what is already known about it

**Searched 2026-09-06.** §5.7.3 attributes a bandwidth plateau to the crossbar — the on-chip
interconnect between the SMs and the memory controllers, which NVIDIA calls XBAR. Two things about
it are already public and this work claims neither.

**XBAR is an independently documented clock domain on Blackwell.** loong0x00's analysis of GB202
(RTX 5090), published 2026-08-13, establishes that XBARCLK has its own PMU object, clock source,
127-point V/F table, hardware measurement entry point and runtime control path, arguing explicitly
that public tooling had mistaken it for a software statistic. It reports a 0.8999:1 GPC-to-XBAR
constraint in the propagation topology.

**Raising it deliberately is also published, and earlier.** LACT issue #1147, opened 2026-08-10 on
the same project, reports applying +60 to +450 MHz XBAR offsets under Linux and measuring up to
+10.6% FPS on an RTX 5090. **Both sources were found independently of this project, and both predate
its own crossbar-plateau measurement (begun 2026-08-19) by roughly a week to ten days** — the domain
was reached from outside this project first, which is what the positioning below credits.

⚠️ **The direction of both is the opposite of this study's.** Neither reports memory-bandwidth
measurements in GB/s, an XBAR-to-core ratio measured across a swept range, the behaviour of the
domain under a *flattened* V/F curve, or the DRAM clock during such an event. Both were read in full
rather than judged from a search snippet. A third source [12] covers the opposite regime again —
*raised* voltage at a fixed high clock, with instability from overclocking XBAR rather than pinning
it.

**The general concept is older than any of them and is not claimed here.** A 2013 patent [13]
describes decoupling an interconnect clock from a core clock so that a slow interconnect stalls a
faster core. It is CPU/uncore, describes a deliberate closed-loop controller rather than an
unintended side effect of a V/F curve, and never touches voltage-pinning or a GPU crossbar — but the
idea that interconnect frequency can bottleneck a faster core is prior art and is cited here so a
reviewer does not have to raise it.

**What §5.7.3 contributes is therefore a measured association, not the domain's existence or its
controllability**: a flattened curve goes with a collapsed core-to-crossbar ratio and a bandwidth
plateau on a real workload, with the memory overclock applied on the plateaued card; a repair
predicted in advance removes both; and the same setting helps one kernel and harms another. ⛔
**This paragraph said *"pinning core voltage collapses the core-to-crossbar ratio and produces a
bandwidth plateau… with the DRAM clock shown constant throughout"* until 2026-09-24.** The crossbar
was never isolated as the cause, and the stock control ran at stock memory clock (§5.7.3).

🛑 **What this section does NOT establish, stated because the distinction is easy to lose.** The
searches above did not find XBAR disclosed in NVIDIA's own documentation — but NVIDIA's Blackwell
whitepaper **could not be text-extracted**, GTC session transcripts were reached only as search
snippets, and the NVAPI SDK headers and full DCGM reference were not searched. The patent sweep used
the Google Patents mirror only: Espacenet classification search and non-English filings
(Samsung, Qualcomm, MediaTek GPU interconnect IP) were not searched at all. **The supportable
statement is "not found in the sources we could read", never "not documented by the vendor."**

🔑 **The narrower claim is the defensible one**, and it is stated narrowly here because the broader
version did not survive a fifteen-minute search. §2.2 records the same lesson from a claim that had
to be retracted outright.

*One thread remains unresolved: a search summary referred to XBAR/SYS clocks collapsing while the GPU
clock rose with no slowdown reason reported, which would be closer to this study's observation than
anything above. Fetching the cited page did not confirm it. It is recorded as unconfirmed rather
than cited or dismissed.*

### 2.6 Vendor auto-tuning

NVIDIA ships automated overclock scanning (exposed through the NVIDIA App and bundled with
third-party tools such as MSI Afterburner). Inspection of the bundled scanner confirms it is
NVIDIA's own implementation, driving the voltage-frequency curve through NVAPI and reporting a
confidence level for a discovered curve.

**Positioning.** These tools optimise for *maximum stable clock*, not for *efficiency*, and they are
closed — they return a curve, not an explanation. This work targets the efficiency objective and
publishes its method.

**Vendor tuning also ships in firmware, and 5.5.1 measures an instance of it.** A board partner's
factory-overclocked SKU carries a voltage-frequency curve chosen by the manufacturer, and on a card
with a dual-BIOS switch two such curves can be compared on the same silicon. Measured that way, the
overclocked BIOS did identical work at matched frequency for **23.11%** more power, and returned
**0.56%** of peak compute and nothing measurable on bandwidth. The objective those tools optimise
for is not the one a buyer running below peak would choose, and the gap between the two is large
enough to measure on shipping hardware without modifying anything.

**Combining overclocking and undervolting has been done, but only with fault recovery attached.**
SAOU [16] deliberately runs *past* safe limits — above `f_safeMax` and below `V_safeMin` — and
catches the resulting errors with an enhanced checkpoint-recovery scheme, reporting up to **22%
energy reduction** on a 10K×10K cuBLAS matrix multiply on a GTX 980. It is a fault-tolerance result:
it assumes corruption will occur and engineers around it. This work stays inside stable operation
and treats a driver crash as a failure rather than an input (§3.5), so the two are not alternatives
to one another.

### 2.7 Existing public datasets, and the gap between measurement and release

The below-stock efficiency optimum on consumer silicon is not an unmeasured quantity. Mei, Wang and
Chu [19] swept an ASUS Strix GTX 980 from 480 to 1080 MHz against a 950 MHz default and found 30 of
42 kernels minimising GPU-level energy below that default, half of them between 680 and 880 MHz —
board-level, below-default, on a GeForce card, in 2017. Mei, Yung, Zhao and Chu [20] preceded it in
2013, sweeping a GTX 560 Ti through Afterburner. **What is missing from both is not the measurement
— it is a downloadable file that contains it.** Neither carries a data-availability statement or a
dataset link; every reference in both resolves to a vendor page or a measurement tool, never to
data.

The sharpest case is Fan, Cosenza and Juurlink [1], because their sweep is **wider than any released
dataset and wider than this work's own**: 85 core frequencies from **135 to 1392 MHz** on a GTX
Titan X, a consumer Maxwell part whose rated boost is 1089 MHz — down to **12% of boost**, against
the 40% floor used here and the 89% floor of the released consumer files below. That sweep would
answer the question this section is about outright. It was never released: across all eleven pages
the paper contains no repository link, no artifact-evaluation appendix and no data-availability
statement, and all four of its URLs are DOIs resolving to papers. ⚠️ **That is an absence in the
published version, not proof no data exists** — the authors were not asked.

| Dataset | Hardware | Core sweep | vs *reference* boost | vs the default the **authors declare** |
|---|---|---|---|---|
| GPU-DVFS-Dataset [6] | 1× Tesla V100 | 757–1530 MHz | 55–111% | — |
| Wang & Chu [21] | GTX 980 (two files) | 500–1000, 700–1500 MHz | 41–123% | below base (1127 MHz) |
| Wang & Chu [21] | Titan X, GTX 1080 Ti | 1600–2000 MHz | 101–126% | **89–111%** (1800 MHz) |
| Wang *et al.* [22] | RTX 2070 Super | 1680–2080 MHz | 95–118% | **89–111%** (1880 MHz) |

⚠️ **Two corrections are folded into that table, both made on 2026-09-13, and both ran in the
direction of overstating this work's contribution.**

**First, the release does contain below-stock consumer sweeps.** A draft of this section said it did
not. Its GTX 980 files sweep core frequency 500–1000 MHz and 700–1500 MHz — well below that card's
1127 MHz base clock — and two further GTX 980 files in the same repository sweep 400–1000 MHz. The
error came from reading a companion *features* file, whose frequency columns are normalised
multipliers rather than absolute megahertz, and generalising from it.

**Second, and more consequential: the two modern consumer sets are not overclocking sweeps.** This
work scored them against the rated boost clock from a specs database, which yielded 101–126% and
95–118% and the conclusion that they "start at or above stock and go up". That compares a measured
sweep against a **reference** card. The authors state the default operating clock of the cards they
actually used — 1800 MHz for the GTX 1080 Ti and 1880 MHz for the RTX 2070 Super — and against
those numbers each sweep **brackets** its default, with **two of five core frequencies sitting below
it**, down to 89%. Both declared values fall exactly on a swept grid point, in the memory axis as
well as the core axis, which is what identifies them as the sweep's centre rather than a nominal
figure.

**What survives is a claim about RANGE, not direction.** A sweep that reaches 89% of its default
cannot locate an optimum that sat at 62% of maximum clock on the V100, and the efficiency gaps these
datasets report — 1.00% and 3.34% — are bounded by that window rather than by the silicon. They
remain unusable as evidence that consumer GPUs lack headroom, which is the only load this section
needs them to bear. For consumer parts from Pascal onward, no released sweep descends far enough
below default for the region to be re-analysed at all.

⛔ **And this work does not get to claim that observation. The dataset's own authors made it first,
in the paper that releases the artifact.** A draft of this section asserted that no prior source
had criticised these specific artifacts on these grounds. That was false, and the refutation is in
[22] §5.1.1 and §5.2. They state the interval:

> "On our real GPU platform, the scaling interval is: V^Gc ∈ [0.8, 1.24], f^Gc ∈ [0.89, g1(V^Gc)],
> f^Gm ∈ [0.8, 1.1]."

— the **0.89 lower bound is their own published figure**, not an independent derivation here. They
name the window as the cause of their small measured saving:

> "Our realistic experiments show that the average energy conservation of 20 benchmarks is 4.3% for
> GTX 1080Ti... The reason for this low effect is (1) The static power P_G0 takes a big portion in
> the total power consumption; (2) **The scaling intervals of f^Gc and f^Gm are narrow.**"

And they run the widened-window counterfactual, reporting that with `f^Gc ∈ [0.5, ...]` the average
energy conservation "finally achieves an average value of **36.4%**", noting that in both cases "the
optimal core voltage/frequency is relatively low, **close to the allowed lowest setting**" — a
boundary optimum, which is what a window too narrow to contain the answer looks like from inside.

**Their 4.3% → 36.4% is structurally the same argument as this work's 1.00% → 44.40%.** ⚠️ It is
not the same measurement: theirs is **system energy at the wall** against a 37 W idle floor (24 W
CPU, 13 W GPU), and their wide case is a **simulation with static power artificially shrunk**, not a
measurement. Do not equate the two figures.

✅ **This strengthens the section rather than weakening it, and it is the form to state.** The
criticism is not this work's to claim — it is corroboration from the people who produced the data,
and their own conclusion is that the honest version of the experiment requires a wider sweep than
their platform allowed. **What this work contributes is that sweep, measured on real consumer
silicon across four chips and three architectures, where [22] could only simulate it.**

Both halves are checkable: the ranges via `analysis/compare_consumer.py`, which now prints each
sweep against both reference boost and declared default, and the GTX 980 counter-example by opening
`csvs/raw/gtx980-low-dvfs-real-small-workload-Performance-Power.csv` in the same public repository.

### 2.7.1 The strongest counter-result found, and it is not dismissed

⛔ **Tang et al. [15] swept a consumer GPU below its default and report NO efficiency valley on it.**
This is the most direct challenge to this work's thesis located in any search, it comes from the
same group that released the consumer dataset critiqued above, and it is stated twice in their text:

> "P100 and V100 generally perform a valley trend in the energy scaling curve with increasing core
> frequency. They achieve a sweet spot of the best energy efficiency in the middle core frequency
> level, **while GTX 2080Ti seems to benefit more from a higher core frequency.**"

> "the performance of GTX 2080Ti **always has a faster-growing trend than the power consumption,
> which results in that the best energy efficiency is mostly achieved at the highest core
> frequency.**"

Their RTX 2080 Ti range is **[950, 1150, 1350, 1550, 1750, 1950] MHz against a 1350 MHz default** —
two points below default. **They did look below stock on consumer silicon and found no valley**, so
this cannot be answered by the swept-range argument of §2.7. (The paper writes "GTX 2080Ti"
throughout; the product is an RTX 2080 Ti.)

**Four differences that may explain it, none of which is established here:**

1. **Their workload is not GPU-bound end to end.** They say so: *"DNN training includes the data
   loading step that is not operated on GPUs. Whether the data loading latency can be well hidden
   significantly affects the GPU core utilization."* Wall-clock that the GPU does not control biases
   the energy metric toward higher clocks — finish the GPU part sooner and a fixed overhead is
   amortised. Every workload in §3.3 here is pure GPU with no host-side stage.
2. **Their own explanation is a power-curve difference:** *"two Tesla GPUs have a dramatically
   increasing power consumption when the core frequency surpasses 1,000 MHz, while GTX 2080Ti does
   not have this issue."* If a card's power does not turn up sharply, no valley exists. Whether
   Blackwell behaves like their Turing part or like their Teslas is an empirical question, and §5.5
   answers it for this chip: it has a valley.
3. **Their ceiling is 1950–2050 MHz.** The 5060 Ti here sustains ~2590 MHz at stock and is commanded
   to 3090. The steep region of a power curve is near the top, and their sweep may simply not reach
   it on that part.
4. **Turing 2018 against Blackwell 2025**, seven years and four architectures apart.

⚠️ **Read their Table III with the direction in mind.** The 2080 Ti's average energy conservation of
**8.7%** (training) is achieved by moving *up* from default, not down — a different mechanism from
the P100's 23.1% and V100's 14.5%, which come from moving *down* into a valley. Those three numbers
are not the same measurement and should not be averaged or quoted as one range.

### The counter-result is explained, using their own stated mechanism

**Tang et al. name the reason themselves**, and it is testable against data already collected here:

> "two Tesla GPUs have a dramatically increasing power consumption when the core frequency surpasses
> 1,000 MHz, **while GTX 2080Ti does not have this issue.**"

A valley requires power to turn up faster than performance somewhere in the swept range. If a card's
power rises close to linearly, no valley exists and the optimum sits at the ceiling — which is what
they report. So the question is not whether their result contradicts this one, but **which of their
two power-curve shapes this card has.** Mean power across twelve workloads and five stock replicates,
as the slope between adjacent grid points:

| band (MHz) | dP/df, W per 100 MHz |
|---|---|
| 1237 → 1545 | **1.85 – 2.09** |
| 1545 → 2010 | 4.50 – 6.30 |
| 2167 → 2475 | 5.98 – 8.56 |
| 2475 → 2625 | **9.96** |

🔑 **The slope steepens 5.4-fold across the swept band.** The RTX 5060 Ti has the Tesla-shaped power
curve, not the one Tang et al. describe for their RTX 2080 Ti. **Their explanation and this result
are consistent**, and the disagreement is between two consumer cards seven years apart rather than
between consumer and datacenter silicon as a class.

*Slopes above 2625 MHz fall to ~0.1 W/100 MHz because the card clamps near 2590 MHz and the top
three commanded points deliver the same achieved clock (§5.4.3); the meaningful range is
1237–2625 MHz.*

⚠️ **This does not make the valley universal, and it is not offered as proof that Tang et al. are
wrong.** It replaces "two papers disagree" with a measurable property that predicts which outcome a
given card will show — **does its power curve turn up inside the swept range?** That is checkable on
any card by anyone, from data this method already collects, and it is a more useful statement than
either paper's result alone.

🛑 **What this costs this paper.** It bounds the generality claim, not the measurement. §5.5's 55.9%
is measured on this chip across twelve workloads and six replicates and is not in doubt. What [15]
shows is that **a consumer GPU exists for which the valley was not found**, so "consumer GPUs have
substantial headroom below stock" is a claim about the chips measured here, not about consumer
silicon as a class. §5.5.4 already establishes that per-workload ordering does not transfer between
two architectures; this is the stronger version of the same warning applied to the effect itself.

**What they find on the parts that do show a valley matches this work's shape.** Energy curves
"generally show a valley trend and there exists a sweet spot", the optimum conserving **23.1%
(P100)** and **14.5% (V100)** on training and **26.4%** and **22.3%** on inference, against default.

⚠️ **Those percentages are not comparable to §5.1's 44.4% or §5.5's 55.9% without care**, and the
difference is the baseline, not the effect. Tang et al. measure against each card's **default**
clock; this work measures against the **highest achieved** clock. On a datacenter part with a
conservative default those are far apart; on a consumer card boosting to near its ceiling they are
close. Any comparison of the two numbers must say which baseline it means.

⚠️ **Both consumer rows are the same citation.** They are two cards from one released collection
[21], not two independently produced datasets, and **no systematic survey established that they are
the only public consumer DVFS sweeps in existence.** The claim made here is therefore about the
consumer DVFS data we were able to locate, not about a surveyed population. That distinction is
stated rather than glossed because this project has already retracted one novelty claim for
exactly this failure — asserting an absence in the literature without searching for it (§2.2). A
dated search across the dataset repositories and artifact appendices would be needed before any
stronger wording is justified, and has not been performed.

What the two ranges show is arithmetic and does not depend on the survey being complete. Each spans
a window of roughly 22 percentage points centred on the default clock its authors declare, reaching
no lower than 89% of it. Because the efficiency optimum lies well below stock — at 62% of maximum in
the V100 data — neither swept range contains it. ⚠️ **A draft of this paragraph called them
overclocking sweeps that "begin at or above the rated boost clock".** That compared them against a
specs-database reference card rather than the hardware the authors describe; two of five core
frequencies in each dataset sit below the declared default (§2.7).

The consequence is a trap for anyone reading them naively. The GTX 1080 Ti data yields a mean
efficiency gap of 1.00% and the RTX 2070 Super 3.34%, against 44.40% for the V100. Read without
reference to stock clock, that pattern invites the conclusion that consumer GPUs lack headroom.
The correct reading is that the measurements stop short of where headroom appears — evidenced by
60% of 1080 Ti applications (18 of 30) having their measured optimum at the lowest frequency
tested, the signature of a truncated range.

⚠️ **That signature is much weaker on the second card, and both figures are given here because
quoting only the stronger one would overstate the evidence.** The RTX 2070 Super has 20% of its
units at the boundary (4 of 20) against the GTX 1080 Ti’s 60%. The truncation argument therefore
rests on the swept ranges themselves, which are arithmetic and independent of workload, rather than
on the boundary share — which is corroborating on one card and weak on the other.

---

## 3. Methods

### 3.1 Hardware and software

| Component | Detail |
|---|---|
| GPU | NVIDIA GeForce RTX 5060 Ti 16 GB (Blackwell, GB206, compute capability 12.0) |
| **Board** | **Zotac Twin Edge OC**, a dual-fan partner card |
| Driver | **610.88 for the earliest measurements; 616.56 from 2026-09-02 onward**, which covers the majority of the collected data. §5.4.5 records the change falling between suite replicates r1 and r2, and §5.5.4 marks the affected comparisons driver-mixed. Read the driver off a sweep's JSON rather than off this table. |
| Rated clocks | Base 2407 MHz, boost 2572 MHz (reference). **Measured stock boost ~2584 MHz** under a compute load |
| Lock-target ceiling | **3090 MHz** — the highest value the driver accepts for `-lgc`, *not* a clock the card runs at |
| Power limit | 180 W default, 200 W configured, adjustable range 150–200 W |
| Memory | 16 GB GDDR7, 128-bit bus, 448 GB/s at the 14001 MHz rating |
| OS | Windows 11 |
| Framework | PyTorch 2.11.0+cu128 |

The second cross-chip unit is a **Gigabyte RTX 3070 Ti GAMING OC rev2.0** (Ampere, GA104, 8 GB
GDDR6X, 256-bit, 608 GB/s), a customer machine measured at stock in both positions of its dual
BIOS and returned as found.

**The board model is recorded because it is load-bearing, not for completeness.** Three results in
this paper depend on board-level rather than chip-level facts:

- **The sweep grid's top end is a driver capability, not a clock the board reaches.** ⚠️ An earlier
  version of this section attributed the 3090 MHz figure to the board's factory overclock and said
  a stock sweep reaches it. **Both were wrong.** 3090 MHz is the highest value `nvidia-smi` accepts
  as a lock target - the top of the supported-clock table - and it is reported identically whether
  the card is at stock or carrying a hand-drawn curve, which is exactly why it cannot evidence an
  overclock. Measured at stock, targeting 3090 MHz achieves **2584 MHz**, against a reference
  rating of 2572. Whatever factory bump this board carries, this project's own data cannot
  demonstrate it, and no result here depends on one.
- **§5.5's entire subject is a vendor BIOS pair.** The dual-BIOS switch is Gigabyte's feature, not
  NVIDIA's; the 23.11% power gap and the 34–57 W offset are properties of two BIOSes that a
  particular board vendor shipped on one card.
- **§5.5.1.1's thermal inversion** — the OC position running 5–7 °C cooler while drawing more
  power — is a statement about a cooler and a fan curve, both of which are the board vendor's.

Naming the boards narrows the claims rather than broadening them, which is the point. Results here
are one Zotac Twin Edge OC and one Gigabyte GAMING OC — not "the RTX 5060 Ti" and "the RTX 3070 Ti"
as model lines, and certainly not Blackwell and Ampere as architectures. Two partner cards of the
same chip differ in factory clocks, power limits, cooler capacity and fan curves, and this work has
measured effects attributable to every one of those.

#### Three different things are called an overclock in this paper

Both board names contain "OC" and neither refers to what 5.7 tunes. The three are distinct in
origin, in what they change, and in who applied them, and conflating them misreads every
stock-versus-tuned comparison here.

| term | what it is | who applied it | where |
|---|---|---|---|
| **board branding** | Zotac's "Twin Edge OC" name implies a factory bump. Measured stock boost is ~2584 MHz against a 2572 MHz reference rating, so any bump is marginal and **this project cannot demonstrate one** | the board vendor, at manufacture | 3.1 |
| **tuned** | a voltage-frequency curve drawn **by hand in MSI Afterburner**, flattened to ~3010 MHz above 925 mV, plus a **+2500 MHz memory offset** | the author | 5.7 |
| **OC BIOS** | an alternate vendor firmware selected by a physical switch on the 3070 Ti | the board vendor, as shipped firmware | 5.5 |

🔑 **"Stock" in this paper means the board as shipped with no Afterburner profile applied**, which
is what the reset button in that tool restores. Measured, that is a ~2584 MHz boost under load
against a 2572 MHz reference rating - essentially reference behaviour. Every stock-versus-tuned
comparison in 5.7 is therefore *as-shipped against as-shipped-plus-hand-drawn-curve*, and the whole
of the gap those sections report is the author's curve rather than any vendor's tuning.

**Nothing in this work applies a curve programmatically.** Voltage cannot be written through any
documented interface (3.2), so the tuned configuration is set by hand in Afterburner's curve editor
and read back through HWiNFO. That is also why 5.7's configurations are not measured
contemporaneously - switching between them is a manual step (5.7.7) - and why separating the memory
offset from the core curve had to be done by hand to study them as two knobs rather than one.

Additional units are drawn opportunistically from a small PC-building operation, giving on the order
of one new machine every 2–3 weeks. Sample size is therefore small and heterogeneous by
construction, and is reported explicitly wherever results are stated.

### 3.2 Frequency control

Control capability was established empirically rather than from documentation, by enumerating the
NVML export table on the target driver and invoking functions through P/Invoke:

| Mechanism | Result on target hardware |
|---|---|
| `nvidia-smi -lgc` (lock core clock) | **Supported.** Volta+. Requires administrator. 389 discrete clocks, 180–3090 MHz. |
| `nvidia-smi -pl` (power limit) | **Supported**, 150–200 W. Requires administrator. |
| `nvmlDeviceSetClockOffsets` | **Available.** Graphics ±1000 MHz, memory −2000/+6000 MHz per P-state. Returns `NO_PERMISSION` un-elevated (not `NOT_SUPPORTED`). |
| `nvmlDeviceGetGpcClkVfOffset` | **`NOT_SUPPORTED`** on this device. |
| Voltage read or write | **Unavailable.** No voltage-related exports across 260 NVML device functions. |

**This is the central methodological constraint of the work: voltage is neither observable nor
controllable through any documented interface.** Consequently this study measures *frequency versus
power*, not voltage versus frequency. It is not an undervolting study, and results are not presented
as such. Per-point voltage-frequency curve manipulation is possible only through undocumented NVAPI
entry points, which were deliberately excluded as unstable across driver revisions.

Measurements therefore fix the core clock and observe the power the card draws to sustain it.

**Third-party V/F curve overrides silently defeat clock locking.** `nvidia-smi -lgc` is not
authoritative when another utility owns the voltage-frequency curve. On the target device with an
MSI Afterburner profile applied — the curve flattened to ≈3010 MHz for every voltage above 925 mV —
a request for 2167 MHz produced a sustained **2942 MHz**, overshooting the cap by 775 MHz, while
1237 MHz locked normally. Repeating the identical sweep with the curve reset to stock, 2167 MHz
produced 2143.8 MHz and held. The flattened curve is therefore the cause rather than merely
consistent with the observation.

The failure is not benign, because it is not a random error. Requests falling inside the overridden
region collapse onto the **same** achieved clock, so a grid reports more distinct frequencies than
it measured and silently overweights one, while every row still looks well-formed. In the affected
sweep, 2 of 3 targets landed on one clock. Sweeps therefore record the direction of any lock miss:
*below* target indicates the device could not sustain the request (power or thermal limits, expected
at the top of the range where maximum boost is a bin no device holds — 3090 MHz sustains 2617.6 MHz
here), whereas *above* target indicates the cap was never applied, which `nvidia-smi` cannot do
unaided. Distinct achieved clocks are counted against planned points and reported per session.

This generalises beyond the present setup: any measurement or auto-tuning tool that assumes
`-lgc` is authoritative will silently mis-sample on the many consumer systems that run a persistent
overclocking profile.

### 3.3 Workload design

Performance measurement requires **fixed work**, not fixed time. Standard stress tools (OCCT,
FurMark, and NVIDIA's bundled `gpu_stressor`) run for a specified duration regardless of device
speed and so yield no throughput measure. Two fixed-work benchmarks are used, chosen to span the
compute/memory-bound axis identified in §2.1:

- **`gemm`** — dense matrix multiplication (8192², FP32) through cuBLAS. Compute-bound; scales
  approximately linearly with core clock. Matrix multiplication was chosen over a bespoke kernel
  specifically because `GeMM` appears in the reference V100 dataset [6], making the two directly
  comparable.
- **`membw`** - a scaled elementwise add over a 256 M-element buffer (~3 GB of traffic per
  iteration). Intended as the bandwidth-bound counterpart; substantially less sensitive to core
  clock than `gemm` - measured elasticity of throughput to core clock is ~0.36 against ~1.12 for
  `gemm` (section 5.4) - but **it is not bandwidth-saturated over most of the swept range**, and
  that is a material limitation rather than a detail. See 3.3.1.

Both perform identical arithmetic on every invocation, so wall-clock duration is a valid performance
metric and efficiency follows as work ÷ (duration × power).

Iteration counts are fixed per workload (120 for `gemm`, 1200 for `membw`), sized for approximately
8–9 s of device work at full boost, and **held constant across every frequency in a sweep**.
Preliminary runs at 30 iterations completed in 0.7–4.1 s, which proved too short for the device to
reach steady clock and thermal state and left kernel-launch overhead visible in throughput.

`membw`'s count was originally 600, which appeared to yield a 9.4 s run. Once instrumentation
overhead was excluded from the timer (§3.4) only 4.7 s of that proved to be memory traffic, and the
count was doubled to restore the intended duration.

#### 3.3.1 `membw` is issue-limited, not bandwidth-limited, below roughly 2000 MHz

An earlier version of this section placed the issue-limited regime below ~1200 MHz. Direct
measurement puts it far higher, and the correction matters: it means the frequency-prediction
results of section 5.2 were tested against a workload whose memory-bound premise does not hold
where the test was run.

A DRAM-limited kernel is flat against core clock. `membw` is not: on stock it rises 264.9 to 352.2
GB/s from 1237 to 2932 MHz, i.e. 59% to 79% of the card's 448 GB/s rating, flattening only at the
very top.

Three independent attempts to construct a genuinely saturated kernel all fail, and converge:

1. **Six access patterns** - triad, copy, a width-doubled copy, scale, read-only reduction, and
   in-place add - measured at 1395 and 2760 MHz. Elasticity to core clock ranges 0.45 to 0.96. None
   is DRAM-limited. The read-only reduction is the *worst* (0.957): it carries dependency chains and
   performs one add per 4 bytes, making it more issue-hungry per byte moved than the triad. The
   width-doubled copy is indistinguishable from the plain one, indicating the library kernels already
   emit vectorised accesses.
2. **Concurrency** - four independent copies on separate streams at 1395 MHz reach 281.2 GB/s
   aggregate, against 218.3 for one, then plateau; eight streams add nothing.
3. **A hand-written CUDA kernel** issuing 1 to 16 independent `float4` loads into registers before
   storing any, so a single thread holds up to 16 memory requests in flight. At 1395 MHz it delivers
   268.3 GB/s at unroll 1 and 281.9 at unroll 16 - a 5% spread across a 16x change in memory-level
   parallelism.

Methods 2 and 3 agree to within 0.24% (281.2 against 281.9 GB/s) from entirely different mechanisms
for raising memory-level parallelism. That is a hardware ceiling at roughly 54% of the bandwidth
available, not a defect in any one kernel.

⚠️ **Probe 3 was run with the memory overclock applied, and the `membw` figures above were not.**
Its theoretical peak is therefore 521.6 GB/s - the 448 GB/s rating scaled by the +2500 offset -
which is the denominator the 54% is taken against, while the 59-79% earlier in this section is
against 448. The two should not be differenced. This does not affect the argument, which rests on
the *elasticity* of throughput to core clock and on two methods agreeing at ~281 GB/s, neither of
which depends on the denominator; it is stated because a percentage without its denominator is
exactly the omission this project keeps finding.

**A DRAM-saturated workload at 1400 MHz is therefore not constructible on this part.** What sets the
281 GB/s ceiling is not identified: it is neither per-thread parallelism nor concurrency, and it sits
well below both the DRAM peak and any plausible instruction-issue bound. Naming it would require
hardware performance counters this study does not read.

#### 3.3.2 What limits `membw` is not one thing, and it moves with frequency

Section 5.7.3 identifies a third limiter, and taken together the three make a more honest picture
than "the memory-bound workload":

| regime | binding constraint |
|---|---|
| low core clock | SM instruction issue rate, and a ceiling near 281 GB/s that neither concurrency nor per-thread unrolling lifts (3.3.1) |
| mid core clock, flattened V/F curve | **the crossbar clock, or a domain that moves with it**, held low while the curve holds voltage flat (5.7.3: associated, not isolated) |
| high core clock | DRAM bandwidth, at roughly 78% of the rated peak |

Only the last of these is what "bandwidth-bound" is normally taken to mean. A workload's identity as
memory-bound is therefore **frequency-dependent on this hardware**, and a study that assumes it holds
across a swept range is assuming something measurably false.

This matters for how the crossbar result should be read. It is not that a core-domain setting
mysteriously reaches into memory. The path from a streaming multiprocessor to a DRAM device is
mostly on-die logic - crossbar, L2 slices, memory controllers - and only its final stage, the PHY
and the GDDR devices themselves, sits in the memory clock domain. A "core" V/F curve governs the
rest of it. The measurements are consistent with the crossbar clock being derived from core voltage
rather than from the locked graphics clock: locking the graphics clock 32.8% higher while voltage is
held constant moves the crossbar 2.3%, whereas at stock the crossbar holds a near-constant 0.96
ratio to the graphics clock across the same range. The rail topology itself was not probed; what was
measured is the behaviour. ⚠️ **"Core voltage" here means the curve's voltage, not the reported
value.** At 1477 and 1560 MHz the two configurations both report 0.720 V, yet their crossbar clocks
differ by 82 and 128 MHz (5.7.3).

#### 3.3.3 The governing clock is invisible to standard telemetry

`nvidia-smi` exposes four clock domains - graphics, SM, memory and video - and on this device
graphics and SM report identical values. **There is no crossbar or fabric clock among them**, and
NVML's field-value interface does not supply one either (see 6, item 1). The clock that best predicts
`membw` throughput on a tuned card - elasticity 1.31, against 0.51 for the graphics clock - cannot be
read by the tooling that essentially every published GPU DVFS study relies on.

Every measurement of it here comes from HWiNFO, joined to the sweep by binning samples on the
graphics clock they were taken at. That is a workable method and it is also a reason this effect
could persist unnoticed in the literature: a study logging `nvidia-smi` telemetry on a card with a
modified V/F curve would record a clean frequency sweep and a well-behaved power curve, and would
have no column in which the actual limiter appears.

### 3.4 Measurement protocol

For each target frequency:

1. Lock the core clock (`nvidia-smi -lgc`) and verify the lock held; readings deviating more than
   30 MHz from target are flagged, **with the direction recorded** (§3.2).
2. Wait 8 s for the device to settle.
3. Launch the benchmark as a separate process and **sample telemetry concurrently at 2 Hz while it
   runs**, recording SM clock, memory clock, power, temperature, utilisation, the decoded
   throttle-reason bitmask, and a timestamp per sample.
4. On completion, record the benchmark's internally-timed duration and **restrict the power average
   to the samples falling inside that same timed interval**, which the benchmark reports in epoch
   time.
5. Reset clocks (`nvidia-smi -rgc`) in a `finally` block that executes on every exit path, including
   interrupt, and verify the reset took effect.

**Measurement-instrumentation defects.** Three separate defects in this protocol produced
plausible-looking but wrong data, and are recorded because each was invisible on inspection and
detectable only by checking measurements against known device limits.

*Post-hoc sampling.* An early implementation sampled after the workload completed and therefore
recorded **idle** power at every frequency. Concurrent sampling is essential rather than incidental.

*Instrumentation inside the timed region.* The benchmark's temperature check invoked `nvidia-smi`
every 5 iterations between the start and stop of its performance timer. Each invocation is a process
spawn costing ≈42 ms, so `membw` at 600 iterations spent **50.5%** of its measured duration waiting
on a subprocess, and `gemm` 10.0%. Corrected throughput moved from 204.83 to 414.23 GB/s and from
15.60 to 17.62 TFLOP/s, both halves measured back-to-back under identical device state. (These
particular runs were taken with a memory overclock applied; the corrected `membw` figure should
therefore not be compared against the 448 GB/s stock rating, an error made in an earlier draft.
Measured later at stock memory the same benchmark reaches 343.7 GB/s, or 77% of rating — an
unremarkable stream efficiency, and the uncorrected 46% was the signal something was wrong.)
Polling is now time-based (an iteration-based cadence samples a fast device more often
than a slow one) and its cost is measured and subtracted; `duration_seconds` is work-only, with
`wall_seconds` and `monitoring_overhead_seconds` reported alongside for audit.

*Mismatched averaging windows.* Power was averaged over the workload **process** while performance
was taken from the benchmark's internal timer, so the power average included ≈2.3 s of interpreter
startup and CUDA initialisation at idle: 124.77 W recorded against 148.52 W actually drawn. Since
efficiency is throughput ÷ power, this divided a load measurement by a partly-idle one.

Neither of the latter two was a constant offset. Both were fixed wall-clock costs, so each shrank as
a proportion of the run as the clock was locked lower, and they biased the efficiency curve in
**opposite** directions — instrumentation-in-timer penalising high frequencies, power dilution
flattering them. A frequency-dependent bias in either duration or power is a bias in the *location*
of the efficiency optimum, which is the quantity of interest. Measured on a validation sweep, the
power correction alone recovered 8.6% at 1236 MHz against 22.8% at 2942 MHz, and changed the
apparent efficiency gap between those points from 7.9% to 21.1%.

The sweep grid spans **40–100% of the device maximum** (1237–3090 MHz here, 13 points). The floor is
deliberate: consumer devices report supported clocks as low as 180 MHz, which are never
efficiency-optimal for real work and make fixed-work benchmarks impractically slow. The V100
reference swept 55–111% of rated boost and located its optimum at 62% of maximum.

**Contention control.** Baseline utilisation is measured before each sweep and the run is aborted
above 10%. This is not a formality: a validation run conducted during an active gaming session
recorded 79% baseline utilisation, with benchmark throughput falling from 8.03 to 4.84 TFLOP/s from
contention alone. Competing load cannot be separated from the measurement after the fact.

**Instrument limitations.** Power is read through `nvidia-smi`, which applies boxcar averaging and
has finite update frequency and transient response [5]. Reported power is therefore a smoothed
device-side estimate, not a shunt measurement, and short transients are not resolvable. All
comparisons are made between measurements taken through the same instrument.

### 3.5 Stability testing

Stability is assessed separately from efficiency, using OCCT's GPU:3D test in Adaptive mode with
error detection enabled, for 10 minutes per configuration. Adaptive mode was chosen over FurMark
because contemporary drivers detect FurMark's constant synthetic load pattern specifically.

Telemetry is logged throughout and the Windows System event log is checked for display-driver reset
events (ID 4101) within the run window. Runs are classified `CLEAN`, `FLAGGED` (thermal or hardware
throttling observed), or `UNSTABLE` (driver reset or telemetry failure).

**The classifier has been tested against induced failures, and since 2026-08-30 against a real
one.** Until 2026-08-20 the logger had only ever run on sessions that went well, so a tool that
unconditionally reported `CLEAN` would have been indistinguishable from a working one. Three
45-second cases were run: sustained load throughout (reported `CLEAN`, 95% of samples loaded), an
idle device (`INCONCLUSIVE`, 0% loaded), and a load that stops a third of the way through
(`INCONCLUSIVE`, 28% loaded). The positive control is load-bearing: without it a classifier stuck
on `INCONCLUSIVE` would have passed both failure cases.

**The driver-reset detector has now fired on genuine hardware instability, not only on an induced
event.** Its first firing, in that same exercise, was on an `nvlddmkm` context-reset produced by
force-terminating a CUDA process - real, but not the failure class the classifier exists for. On
2026-08-30 an undervolt deliberately set past the edge, 875 mV pinned at 3000 MHz, crashed the
display driver, and the detector returned 11 events over the run window. The full record is in
`../data/stability-runs/README-uv-875mv-3ghz-20260830.md`.

Three properties of that failure bear on the *method* rather than on the configuration, which is
why they are recorded here:

- **The signature is a power collapse under sustained reported utilisation.** Power fell from
  92.21 W to 24.05 W in one second while the card still reported 2970 MHz and 100% utilisation.
  Work had already stopped; the utilisation counter had not noticed. That is 5.4.3's decoupling of
  `utilization.gpu` from real throughput appearing inside a failure instead of a measurement, and
  it means a monitor keyed on utilisation would not have seen this one.
- **The driver reset silently cleared the applied offsets.** The memory clock read 16301 MHz before
  the event and 13801 - stock - after it. Any run continued past that point would have been
  measuring stock silicon under a settings string still claiming an undervolt.
- **The crash preceded the benchmark process by fourteen seconds.** Ordinary desktop compositing
  was enough to boost the card to ~2970 MHz at 875 mV. A protocol that inspects only its own load
  window would have missed the event entirely.

⚠️ **The `UNSTABLE` verdict was reconstructed rather than emitted.** The operator stopped the run
on seeing the crash, so neither `_session.json` nor `_stability_protocol.json` was written, and the
detector function was re-run unmodified over the same event-log window. That is sound, but it is
not the tool having produced the verdict itself and the difference is kept rather than glossed.
What makes the record exist at all is that the logger flushes each sample as it is written, so
`_samples.csv` covers the whole event including the four-second gap in which sampling stopped.

**n = 1, and the crash was spontaneous rather than provoked at a known load.** It establishes that
875 mV at 3000 MHz is unstable on this card and nothing about where the edge sits; **no threshold
should be quoted from it.** One of the eleven events post-dates the operator's intervention and is
not attributable to the card.

**An actual hard lock still remains untested.** The card recovered on its own here, so what is now
tested is genuine instability rather than a hang, and a true lock can by construction still only be
inferred from a truncated log.

**A `CLEAN` result is reported as "no failure observed in 10 minutes," never as "stable."**
Undervolt-induced instability commonly requires hours to manifest. Separately, GDDR7 employs error
correction that silently retries on failure, so a memory overclock may be free of crashes while
being net *slower* — stability testing and performance testing are therefore treated as distinct
checks and both are required.

### 3.6 Analysis

**Efficiency** is defined as performance per watt, normalised per unit to its value at the highest
measured frequency — the convention used by the reference dataset [6], preserving comparability.

**Validation** uses leave-one-unit-out cross-validation, where a unit is a workload (V100 data) or a
physical chip (collected data). Splitting on individual measurements rather than units would allow a
model to observe the same unit at a neighbouring frequency and inflate its apparent skill.

**Metric.** Strategies are scored by *regret*: the efficiency given up relative to that unit's own
optimum, in percentage points. Regret is preferred to exact-match accuracy because selecting a
neighbouring frequency on a flat curve costs almost nothing, while exact-match scores it identically
to selecting the worst available frequency.

**Baselines**, chosen to be difficult rather than flattering:

1. **Stock** — always run at maximum frequency. What the device does by default.
2. **Best fixed frequency** — a single frequency selected from training units only, applied to all
   held-out units. Requires no per-unit measurement, and is the baseline any per-unit method must
   justify its cost against.

**Datasets are never pooled.** The V100 and consumer measurements differ in architecture, workload
type, and feature space. Models are fitted separately and compared.

---

## 4. Data availability

All code, protocols, and collected data are released at
`https://github.com/imaoofu/headroom`. Third-party datasets are fetched by script rather than
redistributed. Collected sweeps are published as CSV with an accompanying schema.

---

## 5. Results

### 5.1 Efficiency headroom in the reference dataset

Running each of 33 workloads at stock (1530 MHz) rather than at its own efficiency optimum gives up
a mean of **44.4%** efficiency (median 45.7%, range 15.1–62.8%), costing a mean 13.7% performance
and saving a mean 40.1% power. Measured directly; no model involved.

### 5.2 Per-unit prediction does not beat a fixed frequency

| Strategy | Mean regret | Median | Worst | Exact match |
|---|---|---|---|---|
| Stock (do nothing) | 44.396% | 45.68% | 62.81% | 0.0% |
| **Best fixed frequency (952 MHz)** | **0.837%** | 0.00% | 6.89% | **72.7%** |
| Probe model (Ridge, 4 probes) | 0.883% | 0.00% | 6.89% | 69.7% |

The probe model does not improve on a single fixed frequency. The mechanism is visible in the data:
952 MHz is optimal for 24 of 33 workloads (73%), so a constant already captures 43.56 of the 44.4
available percentage points and little per-unit variation remains to exploit. Workload sensitivity
is present and directionally consistent with §2.1 — correlation −0.666 between performance retained
at the lowest frequency and optimal frequency — but insufficient to beat the constant.

**[1] reports success at a task this section reports a loss on, and the difference is the input
space, not the method.** Fan, Cosenza and Juurlink predict per-kernel Pareto-optimal core-and-memory
configurations for a kernel that has never been executed:

| | Fan et al. [1] | this section (§5.2) |
|---|---|---|
| features | static code features | probe points only |
| space | 2D, core × memory | 1D, core only |
| training | 106 purpose-built micro-benchmarks | a 33×13 matrix with no workload feature columns |

The Ridge model above has none of [1]'s inputs — no code features, no memory axis, and a dataset
that structurally cannot carry them (§5.1: the matrix has no workload feature columns at all). **The
null is therefore not "per-unit prediction does not work"; it is "per-unit prediction from four probe
points on a feature-free, single-axis dataset does not earn its cost over a constant."** Both are
true at once, and reading this table as contradicting [1] answers a question this section did not
ask.

**This null is reported as the result.** The analysis script emits this verdict about its own output.

⚠️ **It is the *unconstrained* null, and that is the version of the question almost nobody asks.**
Under a performance floor the ranking inverts and probing becomes worth its cost by a wide margin
(§5.6.2). Both halves are reported, and of the two it is *this* measurement that misleads, because
a performance guarantee is what essentially every real deployment has. Do not read this table
without §5.6.1 and §5.6.2.

### 5.3 Probe-based curve reconstruction

While probe measurements do not improve frequency *selection*, they do reconstruct the full curve
accurately, which reduces measurement cost:

| Probes | Frequencies selected (MHz) | Curve MAE | Measurement reduction |
|---|---|---|---|
| 3 | 757, 825, 1530 | 0.0290 | 77% |
| 4 | 757, 825, 885, 1530 | 0.0261 | 69% |
| 5 | + 952 | 0.0243 | 62% |

These are distinct claims and are not conflated: reconstruction succeeds while selection ties,
because when one frequency is optimal for most units a constant is already near-optimal.

#### 5.3.1 How few probes, which ones, and whether choosing them matters

The table above fixes the probe count and reports what it achieves. Three further questions decide
whether probing is a useful protocol rather than an observation, and all three are answered on the
same 33-workload reference set. Reproduce with `python analysis/models/select_probes.py`.

**Probe selection must happen inside the fold, and here it makes no difference.** Choosing which
frequencies to probe is part of fitting, so choosing them once over all 33 workloads and then
scoring leave-one-workload-out lets the selection see every unit it is later judged on. Re-running
the selection inside each fold, on the 32 training units only, gives **identical error to four
decimal places at every probe count**, because all 33 folds select the same frequencies — one
distinct probe set in 33 folds. ⚠️ **The shortcut was wrong in principle and worth 0.0000 here.**
Nothing guaranteed that in advance; it was checked afterwards, on one dataset.

**Selecting probes beats spacing them evenly, on the curve.** The no-analysis alternative is
frequencies spread evenly across the swept range:

| informative probes | selected, error | evenly spaced, error | selected frequencies (MHz) |
|---|---|---|---|
| 1 | 0.0336 | 0.0336 | 757 |
| 2 | **0.0290** | 0.0336 | 757, 825 |
| 3 | **0.0261** | 0.0318 | 757, 825, 885 |
| 4 | **0.0243** | 0.0294 | 757, 825, 885, 952 |
| 5 | **0.0230** | 0.0281 | 757, 825, 885, 952, 1012 |

Selection wins by 14–18% from two probes upward and ties at one, where both strategies pick the
same frequency. The reason is mechanical rather than clever: per-frequency variance across units
falls monotonically from 0.142 at 757 MHz to **exactly zero** at 1530 MHz, so selection concentrates
probes at the low end while even spacing spends them near the top.

⚠️ **"Informative probes" is one fewer than the probe count in §5.3's table, and the difference is
not cosmetic.** Every curve is normalised to the highest frequency, so that column is exactly 1.0
for all 33 workloads — zero variance, no information as a regression feature. The measurement is
still genuinely required, because it *is* the normalisation reference, so the cost figures in §5.3
are right; but a "four-probe" model is fitting on three features. Probe counts quoted anywhere in
this work should be read with that distinction in mind.

##### 🔑 Reconstruction accuracy and decision quality are not the same quantity

Going from one probe to five improves the reconstructed curve by **31%**. It improves the decision
made from that curve by **nothing at all**:

| informative probes | 1 | 2 | 3 | 4 | 5 |
|---|---|---|---|---|---|
| curve error | 0.0336 | 0.0290 | 0.0261 | 0.0243 | 0.0230 |
| **mean regret, %** | **0.837** | **0.837** | **0.837** | **0.837** | **0.837** |

🔑 **The regret is not merely similar across probe counts, it is identical — and identical to §5.2's
fixed-frequency baseline, 0.837%, to four decimal places.** The reconstruction's peak lands on
**952 MHz in 33 of 33 folds at every probe count**, and 952 MHz is that baseline. The probe model
does not approximate the constant; it reproduces it exactly, because the efficiency curve is flat
near its maximum and a measurably better curve selects the identical operating point.

**This is the §5.2 null restated in its sharpest form, and it generalises past this dataset as a
warning.** "The model reconstructs the curve to MAE 0.023" reads as progress and is progress, for
the curve. It is worth nothing for the choice the curve exists to inform. **Any claim that better
curve-fitting yields better tuning has to demonstrate the decision moving, not the fit improving** —
and on this data it does not move at all.

⚠️ **No probe count tested reconstructs to within this work's own measurement noise.** Five probes
give 0.0230 against the ~0.0076 within-session spread of §5.4.5 — still three times outside it. So
"characterise a card from a handful of probes" is supported here only at the level of the single
decision, where one probe already equals thirteen, and not at the level of the curve.

### 5.4 Consumer hardware measurements

`[n = 1 unit, 2 workloads, 13 frequencies each. Single-chip result; no cross-unit claim.]`

Thirteen-point sweeps on an RTX 5060 Ti, stock V/F curve, 464–3090 MHz requested
(`20260816-001048_5060ti-gemm-floor15`, `20260816-001734_5060ti-membw-floor15`). Reproduce with
`python analysis/analyze_sweep.py`.

| | `gemm` (compute-bound) | `membw` (bandwidth-bound) |
|---|---|---|
| Efficiency optimum | **1552 MHz** | **1552 MHz** |
| — as % of sustained max | 59% (of 2609 MHz) | 56% (of 2753 MHz) |
| Efficiency gain vs sustained max | **+63.1%** | **+50.1%** |
| Performance cost at optimum | −40.6% | **−9.8%** |
| Power saved at optimum | −63.6% | −39.9% |

**The V100 headroom result reproduces on consumer silicon.** The reference dataset gives a 44.4%
mean efficiency gain for a 13.7% performance cost and 40.1% power saving, with its optimum at 62%
of maximum (§5.1). The `membw` figures here — a **50.1%** efficiency gain for a **9.8%**
performance cost, saving **39.9%** of power, at 56% of sustained maximum — exceed the reference
set's efficiency gain and cost less performance, while saving almost exactly the same power
(39.9% against 40.1%), on a 2025 consumer part measured independently seven years and four
architectural generations later.

⛔ **This sentence quoted 41.6%, 11.3% and 37.4% until 2026-09-11, which were the superseded
numbers.** They came from the 2026-08-16 sweep, taken before the capture-software contamination of
§5.4.4 was known and controlled for; the table above is the clean 2026-08-22 rerun and is pinned by
the auditor, so the table and the prose beneath it disagreed for three weeks. **The prose was not
covered by any claim, which is exactly how it drifted** - and it is the clearest argument in this
work for pinning sentences rather than tables. This is the central empirical claim of the work: the efficiency
headroom identified on datacentre hardware is not an artefact of datacentre hardware.

**The compute/memory distinction appears in what the optimum costs, not where it sits.** Both
optima land on the same grid point, so at this resolution they are *indistinguishable* — which is
not the same as equal, and separating them requires a finer sweep around 1300–1800 MHz rather than
a wider one. What does separate cleanly is the price of operating there: `gemm` surrenders 40.6% of
its throughput to reach its optimum, `membw` only 9.8%. For bandwidth-bound work, running at 56%
of maximum clock is close to free — 39.9% less power for a 9.8% slowdown. For compute-bound work
it is a genuine trade. Any recommender built on this must therefore be workload-aware in its
*advice*, even where the optimal frequency itself is common.

Both curves are single-peaked with the optimum well inside the swept range, so these are interior
optima rather than artefacts of where the sweep stopped. One minor irregularity: `gemm` efficiency
at 1987 MHz (119.58 GFLOP/J) sits marginally below 2205 MHz (124.03), breaking monotonicity by 3.7%
— larger than the 0.6% the contaminated dataset showed for the same irregularity, and no
longer comfortably inside run-to-run variation. It is recorded as an open irregularity rather
than dismissed; a third pass over this region would settle whether it is structure or noise.

#### Correction: the earlier 3-point diagnosis was wrong

A preceding 3-point sweep (1237 / 2167 / 3090 MHz) found efficiency highest at its lowest point and
concluded **the sweep floor was too high to contain the optimum.** That was a misdiagnosis, recorded
here rather than removed because the reasoning error is instructive.

The optimum is at 1552 MHz — comfortably *inside* the original 40%-floor range (1237–3090 MHz). The
floor was never the problem. Three points were. The error was over-applying this work's own
criterion from §2.7, where an optimum landing on the lowest frequency tested signals a range that
stops short: **that inference holds only for a dense sweep.** On a sparse one, an optimum at the
lowest sampled point is equally consistent with the true optimum lying between the first and second
points, which is precisely what occurred. A criterion for detecting truncated *ranges* was applied
to what was actually insufficient *resolution*.

Lowering the floor to 15% nevertheless earned its place, for a reason other than the one given at
the time: efficiency falls monotonically from 1552 MHz down to 464 MHz, which establishes the
optimum as interior. Had the sweep begun at 1237 MHz, the peak would have been found but could not
have been shown to be a peak rather than an edge.

The superseded 3-point measurements are retained in `data/frequency-sweeps/` as validation runs.

**The compute-bound / memory-bound contrast is confirmed, and is smaller than assumed.** Across the
full 464–2750 MHz range the elasticity of throughput to core clock is **1.18** for `gemm` and
**0.32** for `membw` — a 3.7× difference in clock sensitivity, which is the effect the two-workload
design exists to produce. But `membw` still gained 75% throughput over a 5.9× clock increase, so it
is strongly sub-linear rather than insensitive, and §3.3's original "comparatively insensitive"
framing is corrected accordingly. The residual sensitivity is expected and its cause is visible in
the curve: the device sustains 200.3 GB/s at 464 MHz against 351.4 GB/s at 2754 MHz, i.e. it cannot
issue memory requests fast enough to saturate DRAM at low core clock, and is issue-limited rather
than bandwidth-limited there. Bandwidth saturates only above roughly 1990 MHz, beyond which a
further 39% of clock buys 2.5% of throughput while costing 34% more power.

**Sustained maximum boost is workload-dependent**, so "stock" is not a single frequency. Requesting
3090 MHz yielded 2597 MHz under `gemm` (171.9 W) but 2754 MHz under `membw` (86.2 W): the
more power-intensive workload sustains a *lower* clock. Consequently the top of any grid built from
`clocks.max.sm` is unreachable, and grid points above roughly 2800 MHz will collapse onto one
achieved clock — a second, benign mechanism for the collapse described in §3.2, and one that must be
distinguished from it. Any stock-versus-tuned gap must define stock as the clock the device selects
*for that workload*, not as a nameplate figure.

**Workload type does shift the optimal frequency — in the direction opposite to the prediction.**
§2.1's compute/memory-bound distinction and the V100's −0.666 correlation between performance
retained at the lowest frequency and optimal clock both predict that the *less* frequency-sensitive
workload should prefer a *lower* optimum. A fine sweep resolves the two optima and finds the
reverse: `gemm` optimises at **1488 MHz** and `membw` at **1634 MHz**, a difference of
**146 MHz (95% CI 93–187 MHz)**, with the bandwidth-oriented workload preferring the *higher*
clock. Method, evidence and the reasons for caution are in §5.4.1.

**Incidental comparison: a manual tune beat stock at the top of the range.** The earlier validation
sweep ran with an Afterburner profile applied (flattened V/F curve, ≈3010 MHz above 925 mV). At the
maximum-boost request, that configuration sustained 2942 MHz at 162.91 W and 17.42 TFLOP/s, against
stock's 2617.6 MHz at 167.03 W and 15.40 TFLOP/s — **+13.1% throughput for −2.5% power, ≈15.9%
better efficiency.** This is the paper's central thesis in miniature: conservative stock behaviour
leaves measurable headroom that an empirically-found configuration recovers. It is reported as an
observation, not a result. The two sweeps were run separately rather than interleaved, background
utilisation differed (6.2% against 3.6%), thermal state was not matched, and n = 1 chip, 1 workload,
1 configuration. A controlled stock-versus-tuned comparison on the same unit is required before this
is more than suggestive, and is the obvious next measurement.

#### 5.4.1 Resolving the two optima

**This subsection uses the 2026-08-22 clean-protocol repeat**, matching §5.4. The 2026-08-16
originals are superseded and remain in the repository; `python analysis/compare_protocol.py`
reports what moved. Reproduce these fits with
`python analysis/analyze_fine_sweep.py --pattern "*fine-p*-rerun_sweep.csv" --bootstrap 5000`.

The coarse sweep placed both workloads' optima in the same 217 MHz bin, which is a statement about
grid resolution rather than about the hardware. Separating them required a design change, because
the obvious approach does not work.

**An efficiency curve is flat near its optimum by construction, so its argmax is largely noise.**
In the 13-point coarse run `gemm`'s peak stood only 3.4% above its nearer neighbour ±218 MHz away, while
the same run contained an unexplained 3.7% non-monotonicity between 1987 and 2205 MHz. On synthetic
curves with a known peak, this grid and realistic noise, the raw argmax moved **53–60 MHz between
identical passes**. Comparing two argmaxes would have compared two coin flips. The measured
repeatability under the clean protocol is median 1.25% for `gemm` (worst 2.65%) and 2.25% for
`membw` (worst 4.81%), driven by power rather than by throughput. Note the asymmetry: against the
contaminated 2026-08-16 passes `gemm` improved from 2.4% and `membw` got worse, from 1.7%. Removing
a background SM competitor helps the compute-bound workload and does little for the bandwidth-bound
one, which is consistent with §5.4.4 but is reported here as measured rather than as expected.

The design therefore: **13 points over 1200–1900 MHz, two passes per workload, run in the order
`gemm`, `membw`, `membw`, `gemm`**, with the optimum located by fitting the curve rather than by
selecting a point. Three choices carry weight.

*The band is wider than the peak.* A fit needs curvature to constrain a vertex; across 1300–1800 MHz
the curve falls only ~2% from peak, against 8–9% across 1200–1900 MHz. Tightening a fine sweep
around the peak buys frequency resolution and pays for it in signal.

*The order is counterbalanced.* Sweeps run ascending and the card warms over a ~30 minute session,
so run position is confounded with temperature. The ABBA order put each workload in one early and
one late slot. It worked: `gemm` ran at 47.5–53.5 °C then 44.0–50.8 °C, `membw` at 39.0–49.0 °C
then 45.9–52.0 °C,
so drift landed on both workloads rather than on the difference between them.

*The estimator is a cubic, not a parabola.* Efficiency curves are asymmetric — steep rise, gentle
fall — and a symmetric parabola fitted to a skewed curve places its vertex on the shallow side.
Measured on synthetic curves peaking at 1550 MHz: the parabola returned 1550/1564/1578/1587 MHz at
skews of 0.0/0.3/0.6/0.8 with ±2 MHz scatter, while the cubic returned 1550 MHz at every skew with
±5 MHz scatter. **The parabola is precise and wrong.** This is not a cosmetic difference: the two
workloads have differently-shaped curves, so the bias does not cancel in the difference. Given two
synthetic curves with an *identical* optimum at 1550 MHz and skews of 0.8 and 0.0, the parabola
reported "+37 MHz, 95% CI +29 to +45, the optima do differ" — a false positive of the same size and
direction as the effect being sought. The cubic reported no difference, correctly. That failure was
caught by `analysis/test_analyze_fine_sweep.py`, which checks the estimator against curves whose
answers are known by construction, and not by inspection of the code.

**Result.** Each of the four sweeps locates a vertex independently, and they agree:

| | vertex | 95% CI |
|---|---|---|
| `gemm` pass 1 | 1467 MHz | 1446–1491 |
| `gemm` pass 2 | 1513 MHz | 1492–1536 |
| `membw` pass 1 | 1598 MHz | 1552–1636 |
| `membw` pass 2 | 1611 MHz | 1582–1633 |

⚠️ **The four vertices are pinned by `analysis/audit_claims.py`; the four confidence intervals are
not.** Re-running the bootstrap from the recorded seed reproduces every vertex exactly and lands one
megahertz off on one bound of all four intervals, whichever way the generator is seeded. One
megahertz is not a disagreement worth changing the numbers over, and it is also not a match — so no
claim renders them, because a claim written to reproduce them would be a formula fitted to the
document rather than to the data. Their provenance is an invocation this code path does not
reproduce, and that is stated rather than papered over.

The two `gemm` fits agree within 46 MHz and the two `membw` fits within 13 MHz, while the gap
between workloads is ~112 MHz — so the effect remains larger than the disagreement between
repeats of the same measurement, though by a narrower margin than the contaminated dataset
suggested. No footnote is needed here: unlike the 2026-08-16 passes, no point in either pass
was excluded.

Pooled: `gemm` **1492 MHz**, `membw` **1604 MHz**, difference **−112 MHz (95% CI −146 to −70)**. The interval excludes zero, so the optima do differ, and the bandwidth-bound workload prefers the higher clock.
All 52 points held their locked clock exactly, none overshot, and all 52 had power windowed to the
benchmark's timed region.

**There is no contamination in this dataset to be robust to, and that is checkable.** The
2026-08-16 measurement had one: a console-selection freeze (§5.4.2) interrupted `gemm` pass 1 at
its 1725 and 1785 MHz points, which read 7.0% and 4.5% below their pass-2 counterparts and
produced throughput *falling* as clock *rose* — physically impossible, and identifiable without
reference to the conclusion. That section reported a four-way sensitivity analysis showing the
effect surviving every way of handling those points.

The repeat was run headless, with no console attached, so the freeze could not occur. The data
confirms it did not:

| | 2026-08-16 | 2026-08-22 |
|---|---|---|
| worst pass-1 deficit against pass 2 | −7.0% at 1725 MHz | −2.2% at 1320 MHz |
| points where throughput falls as clock rises | 1 (pass 1, 1665→1725 MHz) | **none, either pass** |

The sensitivity table is therefore retired rather than recomputed: with no contaminated points
there is nothing to be sensitive to, and transcribing four variants of an analysis whose premise
no longer holds would be worse than dropping it. The check above replaces it.

For reference, on the 2026-08-16 data the contamination accounted for ~20 MHz of a ~150 MHz
effect, so it was never the source of the finding there either. The coarse sweep — a separate
run on a different grid — independently gives the same sign.

**Why this is not yet a refutation of the V100 correlation.** Two reasons, and both should survive
into any write-up.

First, **`membw` is not memory-bound by the V100's own criterion.** That correlation classifies
workloads by performance retained at the lowest frequency swept, with memory-bound meaning ≥90%
retained. Evaluated at the same *relative* floor the V100's 757 MHz represented (49% of sustained
maximum), `gemm` retains 46% — properly compute-bound — but `membw` retains **78%**, which falls in
neither the ≥90% memory-bound class nor the <70% compute-bound class. §5.4 already established that
this kernel is issue-limited rather than bandwidth-limited below ~1990 MHz. The prediction is
therefore being tested outside the domain where its premise holds, and the mechanism is visible in
the data: across 1200–1890 MHz `gemm` gains 66.9% throughput for 67.1% more power, while `membw`
gains 26.8% for 25.8% more power. `membw`'s power grows more slowly with core clock because its
consumption is dominated by a memory subsystem running at fixed clock, so it can afford more core
clock before power overtakes throughput — which is exactly a *higher* optimum. A genuinely
bandwidth-saturated kernel would not behave this way, and building one is the correct next test.

Second, **the effect is statistically clear and practically small.** Running `gemm` at `membw`'s
optimum costs 1.6% efficiency; running `membw` at `gemm`'s costs 1.8%. The optima differ, but the
penalty for using one frequency for both is under 2% — which is itself a useful result for a
recommender, and a caution against over-reading the 150 MHz gap.

#### 5.4.2 An instrumentation hazard worth recording

`gemm` pass 1 froze for six minutes mid-sweep with the GPU clock-locked and idle. The cause was not
the benchmark, the sweep script, or the driver: Windows consoles enable QuickEdit by default, so a
single click inside the window enters selection mode, and **selection mode blocks all output to that
console**, suspending any process that writes progress. There is no error, the process stays alive,
and the only visible trace is the word `Select` prepended to the window title.

This is recorded because it is a silent failure mode for exactly the kind of long, unattended,
elevated run this project depends on, and because its damage was *not* obvious: the interrupted
point itself looked normal (it reheated during the settle interval), while the two neighbouring
points were measurably corrupted. Both sweep tooling and the stability logger now disable QuickEdit
at startup.

#### 5.4.3 The sub-100% utilisation is a telemetry artifact, not lost work

Sweep points recorded GPU utilisation below 100% even after subtracting the measured `nvidia-smi`
monitoring cost, and the residual appeared to grow with clock: 0.9% at 1200 MHz, 5.5% at 1897 MHz,
7.5% at 2754 MHz. Read naively this is the signature of a CPU that cannot launch kernels fast enough
as they shorten — which would suppress high-clock throughput, understate high-clock efficiency, and
bias `membw`'s optimum downward. That would undermine §5.4.1, so it was tested.

**The counterbalanced passes already answer it.** Each target frequency was measured twice in
opposite order. At 1897 MHz the two passes recorded utilisation of **91.8% and 94.0%** — and
throughput of **350.2 and 350.3 GB/s**. At 1605 MHz, 91.6% and 91.7% utilisation gave 328.8 and
328.4 GB/s, the *lower*-utilisation pass being marginally faster. A two-point utilisation
difference with throughput identical to within 0.03% means the two are decoupled: whatever
`utilization.gpu` is varying over, it is not work.

**This leg of the argument is weaker than it was, and the reason is instructive.** Measured on
the contaminated 2026-08-16 dataset the same two passes read 99.0% and 92.7%, a six-point
spread, against 2.2 points here. The clean dataset shows both a lower absolute utilisation and
far less variation in it, which is consistent with §5.4.4: a background consumer inflates the
run-to-run scatter in this reading as well as depressing throughput. A smaller gap is less
striking evidence for decoupling, so the case now rests mainly on the launch-count experiment
below, which is a direct manipulation rather than an observation.

**A direct test confirms it.** Holding total bytes moved constant while varying bytes-per-kernel
over a 32× range changes the launch count from 320 to 10240. Throughput across that range spans
415.3–417.6 GB/s — a **0.5% spread**, running the wrong way for the hypothesis, with the smallest
kernels marginally fastest. Replaying the identical sequence from a CUDA graph, which removes nearly
all per-launch CPU work, moved throughput **−0.1%**. Clock was steady at 2992 MHz across every
condition (measured spread 0 MHz).

The instructive detail is that the CPU cost is genuinely large and still not binding. At 16 M
elements per kernel the CPU spent **90% of wall time** submitting launches; at 512 M it spent 0.0%.
Throughput was the same. **A high CPU cost is not a CPU bottleneck** — the submission thread stays
ahead of the GPU until it doesn't, and 90% occupancy is not 100%. The sweep's own configuration sits
at 0.1% submit, three orders of magnitude clear of the edge.

The conclusion for methodology is narrow but worth stating: `utilization.gpu` averaged over ~25
samples is too coarse to support an argument about lost work, and should not be used as one.
Throughput is the measurement; utilisation is a diagnostic hint. Data in `data/probes/`.

#### 5.4.4 Default-enabled capture software shifts the measured optimum

This subsection reports a contaminant that biased this study's own measurements, was not detected
for several weeks, and is not caught by the quiet-GPU check the sweep tool performs. It is reported
as a result rather than as a caveat because it moved a quantity this paper reports, not merely the
confidence in one.

**How it surfaced.** Two `gemm` sweeps run minutes apart on identical hardware settings disagreed by
5.5% at 1545 MHz and 5.5% at 1852 MHz while agreeing to 0.08% at the peak. Repeating a sweep that
had previously only ever been run once is what exposed it; no single run looked wrong.

**The controlled comparison.** NVIDIA Instant Replay is a continuous capture feature, enabled by
default with the NVIDIA app, which keeps a rolling buffer of recent gameplay. It has no window. Five
sweeps were run on one configuration in one session, three with it enabled and two with it disabled,
with nothing else changed:

| condition | peak `gemm` | spread |
|---|---|---|
| Instant Replay enabled | 17.97 / 17.98 / 17.99 TFLOP/s | 0.09% |
| Instant Replay disabled | 18.24 / 18.24 TFLOP/s | 0.04% |

The disabled condition is faster at all thirteen grid points. **The penalty is frequency-dependent:
4.22% mean across 1237-2010 MHz against 1.71% across 2167-3090 MHz.** The achieved clock is
unchanged - 2975.9, 2976.5 and 2977.1 MHz enabled against 2977.0 MHz disabled - so the card runs at
the same speed and only the share of it available to the measured workload differs. Power rises
along with throughput rather than falling, which is what removing a competitor looks like and not
what a faster card looks like. Temperature is excluded: the fastest run was also the warmest at the
affected points.

**It is a variance source as well as a bias, and that is the more damaging half.** Mean run-to-run
spread is 1.82% with the feature enabled against 0.35% with it disabled. At 1545 MHz the spread is
6.95% enabled against 0.13% disabled.

**It moves the reported optimum.** Because the penalty is larger at low frequency than at high, it
tilts the efficiency curve rather than shifting it uniformly, and curve shape is what this study
measures:

| | efficiency optimum | gain over the top grid point |
|---|---|---|
| Instant Replay enabled | 1395 MHz | +26.4% |
| Instant Replay disabled | 1545 MHz | +32.6% |

One full grid step of movement in the optimum, and 6.2 percentage points of the efficiency gain.

**Why a quiet-GPU check does not catch it.** Encode and decode execute on NVENC and NVDEC, engines
separate from the streaming multiprocessors, and `nvidia-smi`'s `utilization.gpu` reports neither.
On the machine used here the feature raised idle SM utilisation from 4.3% to 10.8%, which does cross
this study's 10% refusal threshold - but only incidentally, and a capture tool that sat quieter on
the SMs would pass unnoticed. The discriminating signal is `utilization.encoder`, which reads 0%
with the feature disabled and 21% with it enabled and nothing being recorded to screen. The sweep
tool now refuses to start on any encoder or decoder activity and records both in the session
metadata.

**The category, not the instance.** Always-on clip capture is common on the consumer hardware that
consumer DVFS measurements are made on: NVIDIA Instant Replay and ShadowPlay, the OBS replay buffer,
Discord and Steam recording, Xbox Game Bar, AMD ReLive. Any of these occupies the video engines
continuously while remaining invisible to a utilisation check and, in most cases, to the operator.

**What this does and does not support.** It is one feature, one card, one workload, one session. The
claim is that on this hardware a default-enabled capture feature shifted a measured efficiency
optimum by a grid step and its gain figure by 6.2 points, and that idle SM utilisation is an
insufficient precondition check. It is **not** a claim that any published dataset is affected: the
measurement conditions of those datasets are not documented, which is itself the point, and
asserting contamination without evidence would repeat the error corrected in section 2.
`gemm` renders nothing to the screen, so the capture feature has little new frame content to encode
during these measurements; the cost measured here is plausibly a floor rather than a typical case,
and a graphics workload was not tested.

**Consequence for this study.** The feature was enabled during every sweep in this paper predating
2026-08-22. Because it was enabled uniformly, comparisons between configurations retain their
direction and their large effects - the 29.6% bandwidth plateau of section 5.7.2 is six times the
contaminant. Absolute throughput figures from those runs are understated, and the optimum locations
and efficiency gains in sections 5.4 and 5.4.1 are subject to the shift demonstrated above. Those
sweeps are being repeated under the corrected protocol.

#### 5.4.5 What reproduces between sessions, and what does not

The twelve-workload suite was collected three times at stock on separate days - 2026-08-29,
2026-08-30 and 2026-09-02 - specifically so that the figures derived from it could carry an
interval rather than a point. The third set was required to be on a different day because 6.8's
cross-session drift is the larger variance component, so same-sitting repeats would measure only
the smaller one. All three are verified-quiet: every sweep records encoder and decoder at 0%.

⚠️ **Six stock replicates now exist (r1-r6); every figure in this section is the THREE-replicate
one and deliberately stays that way.** r4 and r5 were collected back-to-back on 2026-09-04 and r6 on
2026-09-05, after this decomposition was written. Recomputing it at n = 6 is real work rather than a
larger number — r4/r5 are a within-session pair, so pooling all six would mix the two variance
components this section exists to separate, and the session-structure argument would have to be
rebuilt before the figures meant anything. §5.5.4 uses all six because a rank correlation does not
care about that structure. Until this is redone, read every number below as n = 3.

Mean spread across the three replicates, over twelve workloads and thirteen commanded frequencies
each:

| quantity | mean spread across r1/r2/r3 |
|---|---|
| throughput | **0.87%** |
| power | **2.07%** |
| efficiency (throughput per watt) | **2.08%** |
| reported efficiency gain | **4.34 percentage points** |

🔑 **Power is the dominant noise source, not throughput.** It reproduces 2.4 times worse, and
efficiency tracks power almost exactly - 2.08% against 2.07% - because throughput noise is
negligible beside it. This is consistent with limitation 4: power here is a device-side,
boxcar-averaged estimate rather than an external measurement, and it is the term every efficiency
result in this paper divides by.

**The gain spread follows arithmetically from that, and is not an additional effect.** Efficiency
gain is `100 x (peak / reference - 1)`. Both terms carry roughly 2.08%, so their ratio carries
about 2.9%, and multiplying by the ratio itself - about 1.56 at the mean gain - predicts a spread
near 4.6 points against the 4.34 observed. **The three replicates agree.** The metric simply
amplifies power noise by a factor of roughly five.

⚠️ **The ~0.76% this paper quotes elsewhere is THROUGHPUT reproducibility on `gemm`, and must not
be used as an uncertainty on anything derived from watts.** Efficiency and every gain computed from
it reproduce several times worse. Two figures in earlier drafts were read against the wrong bar for
exactly this reason; both are corrected in place.

**What this permits and forbids.** The headline effect is untouched: the twelve workloads gain
between 33% and 78% at their optima, an order of magnitude outside this noise. But per-workload
spreads range from 1.1 points (`bgemm256`) to 8.8 points (`layernorm`), so **no ordering of
workloads by efficiency gain is supported across gaps smaller than roughly five points.**

**A hypothesis of this study's own, tested and refuted.** The gain ratio is anchored on the highest
measured frequency, which is where the undershooting points are (2-4 per sweep, always undershoot),
so that anchor was expected to be the noisiest term. It is the least noisy: 3090 MHz reproduces to
0.71% against 0.88% averaged over every other point, and the worst point is 1237 MHz at 1.37%. The
gain spread is not an artifact of an unstable denominator.

**Caveats.** n = 3 is three measurements, not a distribution; these are ranges, not confidence
intervals. One chip. The driver changed between r1 and r2 (610.88 to 616.56) but does not explain
the variance and appears to run the wrong way - mean absolute gain difference is 1.99 points for
the driver-differing pair against 3.07 for the driver-matched one. Full record in
`../data/frequency-sweeps/suite-replicate-r3-20260902/README.md`.

### 5.5 Cross-chip variation

Every result before this section was measured on one RTX 5060 Ti. This section adds a second chip
of a different architecture, and - because that card carries a dual-BIOS switch - a controlled
comparison of two vendor-authored voltage-frequency curves on identical silicon.

**The card.** A Gigabyte RTX 3070 Ti GAMING OC rev2.0: Ampere, 8 GB of GDDR6X, measured on a
third party's machine with the collection kit of 3.4 and returned to the state it was found in.
It shares nothing with the reference card but the measurement protocol.

| | RTX 5060 Ti | RTX 3070 Ti |
|---|---|---|
| architecture | Blackwell | Ampere |
| memory | 16 GB GDDR7 | 8 GB GDDR6X |
| clock ladder | 389 bins, 180-3090 MHz | **116-120 bins, 405-2190 MHz** |
| default power limit | 180 W | **290-310 W** |

The clock ladder is the difference that matters for this method: the older card exposes roughly a
third as many discrete frequencies over a range half as wide, so a 13-point sweep steps 105 MHz at
a time rather than 154 MHz over a much longer span.

**The central result reproduces.** Running the compute workload at its efficiency optimum rather
than at its peak-throughput point costs **21.7%** of throughput and saves **37.3%** of power on
this card, against 44.4% and 62% on the reference dataset and comparable figures on the 5060 Ti.
The magnitude differs; the shape does not. A second architecture, a different memory technology
and a different vendor board reach the same qualitative conclusion.

**Neither BIOS reaches its own clock ceiling.** Both peak near **1765 MHz achieved** - 1765.0 in
one position and 1772.0 in the other - against ceilings of 2130 and 2190 MHz. Above roughly
1710 MHz the commanded clock stops being reached and throughput flattens. That is the same
power-limited-not-clock-limited behaviour 5.4 reports for the 5060 Ti, now on hardware that shares
none of its design decisions, which makes it a property of how these cards are configured rather
than of one board.

#### 5.5.1 Two vendor BIOSes on one chip: a quarter more power for nothing

The card was found with its BIOS switch in the **SILENT** position, which is not the factory
default. Both positions were measured in one session, minutes apart, on the same silicon in the
same case at the same ambient.

| | SILENT (as found) | OC |
|---|---|---|
| VBIOS | `94.04.5a.00.91` | `94.05.5a.00.bd` |
| top supported clock | 2130 MHz | 2190 MHz |
| power limit, default, maximum | 290 / 290 / 320 W | 310 / 310 / 350 W |

The OC position raises the clock ceiling and the power envelope together, which is worth noting on
its own: 5.7 spends its length separating those two knobs, and the vendor ships them coupled.

**At matched frequency the two BIOSes do identical work and the OC position draws a quarter more
power.** Seven grid points from 855 to 1485 MHz, with achieved clocks equal to 0.0 MHz at every
one of them and the memory clock unchanged:

| | mean | range |
|---|---|---|
| throughput, OC against SILENT | **-0.00%** | -0.15% to +0.07% |
| power, OC against SILENT | **+23.11%** | +19.37% to +27.53% |

**The thermal explanation runs backwards.** Silicon leaks more when it is hot, so if temperature
were driving this the hotter run should draw more power. The SILENT run was the hotter of the two
at five of the seven points, 55.8-58.8 C against 51.8-54.0 C, and it drew less. Whatever separates
the two curves is not thermal, and correcting for temperature would widen the gap rather than
close it.

No voltage telemetry was available in this session - the machine belonged to somebody else and the
kit installs nothing - so the mechanism could not be measured here. A prediction was registered
from this gap on the assumption that it was voltage, and a later session refuted it. That exchange
is 5.5.1.1, and the short version is that **the extra power is not voltage and the two BIOSes hold
the same voltage floor.** What follows in this subsection is what the gap buys, which does not
depend on what causes it.

**What the extra power returns.**

| | SILENT | OC | difference |
|---|---|---|---|
| peak `gemm` | 16.96 TFLOP/s at 273.1 W | 17.05 TFLOP/s at 289.1 W | **+0.56%** |
| peak `membw` | 550.9 GB/s | 551.1 GB/s | **+0.04%** |
| band-mean `membw` power | 149.7 W | 202.2 W | **+35.1%** |
| best `gemm` efficiency | 77.51 GFLOP/J at 1380 MHz | 64.47 GFLOP/J at 1425 MHz | **-16.82%** |

Half a percent of peak compute, nothing measurable on bandwidth, and a sixth of the card's best
efficiency given away to get it. On the bandwidth-bound workload the two positions deliver the
same throughput for 35% more power, because that workload never approaches the frequency where the
higher ceiling could matter.

**What this does and does not show.** It shows that a vendor's own upward tune, on its own silicon,
can cost a quarter of the board's power and return half a percent of compute when the extra
frequency it enables is not being used. That is a statement about the *trade* the OC position makes,
it was authored by the manufacturer rather than by us, and it stands on the measurements above
whatever the mechanism turns out to be.

An earlier version of this paragraph went further and called this "the clearest evidence in this
work that the shipped voltage is not the required voltage", pairing it with 5.7's hand-undervolting
of the 5060 Ti as the same conclusion reached from the opposite direction. **That pairing is
withdrawn.** It rested on the inference refuted in 5.5.1.1: the two BIOSes ship the *same* voltage,
so nothing here says the shipped voltage exceeds the required one. 5.7's finding is unaffected -
it is a direct measurement on a different card and never depended on this one.

##### 5.5.1.1 A prediction registered from this gap, and its refutation

The gap above was measured without voltage telemetry. Section 5.5.3 recorded a prediction before
the measurement that would test it: if the 23.11% is core voltage and nothing else, then at equal
clock and equal work power scales with V-squared, and the SILENT BIOS should hold its floor near
0.819 / sqrt(1.2311) = **0.738 V**.

**It was measured on 2026-08-27 and the prediction failed.** The SILENT floor reads
**0.812-0.819 V** against the OC position's 0.819-0.825 V. Within this sensor's 6-7 mV
quantisation the two BIOSes hold **the same voltage floor**. The predicted separation was 81 mV,
about twelve sensor steps; the measured separation is zero to one.

The gap itself reproduced. Seven matched points, both sessions verified quiet: **+22.27% mean
power** against Session A's +23.11%, **+0.42% mean throughput**, and a voltage difference of
+0.003 V that is exactly zero at four of the seven points.

**Where the inference went wrong is specific, and worth stating because the error is reusable.**
Fit each BIOS's matched-band power as `P(f) = intercept + slope*f`. The slope is the term
`P = C*V^2*f` actually governs; the intercept is everything that does not scale with core clock.

| | SILENT | OC | difference |
|---|---|---|---|
| slope (frequency-scaling) | 87.7 +/- 5.4 W/GHz | 79.3 +/- 6.4 W/GHz | -8.4 +/- 8.4, consistent with zero |
| intercept (constant) | 53.6 +/- 6.4 W | 97.5 +/- 7.6 W | **+43.9 +/- 9.9 W, 4.4 sigma** |

**The frequency-scaling term is the same in both BIOSes within error, and all of the resolvable
difference is in the constant.** `V^2*f` is a statement about the slope; the +23.11% was measured
on total board power and lives entirely in the intercept. The inference fed a whole-quantity ratio
into a law governing one term of it, and that term had not changed.

Described as an offset rather than a ratio, the gap is **34.1 W, relative spread 9.9%, against
22.3% at 19.0%** as a percentage - the additive description fits more than twice as tightly. Under
leave-one-out across the seven points, fitting each model's single parameter on six and predicting
the seventh, the additive model predicts to **2.95 W against 6.43 W for the ratio model, a 54%
reduction**. The ratio model's errors are also structured, overshooting at the bottom of the band
and undershooting at the top, which is the signature of a wrong functional form rather than noise.

**34.1 W and 43.9 W are not the same quantity.** 34.1 W is the measured mean offset across the
seven matched points and is the number that describes the card. 43.9 W is the difference between
the two fits' intercepts, an extrapolation to zero frequency that no measurement reaches. They
differ because the slopes differ slightly, so the two lines converge as frequency rises.

**This is an improvement in description, not in explanation. It still does not say what draws the
34 W.** What it does is exclude, and the exclusions are tighter than 5.5.1 previously had:

- **not core voltage** - the floors are identical within one sensor step
- **not core dynamic power** - it does not scale with core clock at all, across a 74% rise
- **not memory clock** - identical at 9251 MHz in both positions
- **not crossbar clock** - at 1485 MHz both positions hold 1410 MHz and the offset there is
  30.4 W, larger than the 29.0 W at 1380 MHz where the crossbar clocks differ by 75 MHz
- **not leakage** - leakage rises with temperature, and the card drawing *less* power is the
  *hotter* one by about 5 C at every matched point, in both sessions independently
- **not cooling** - see below

**Cooling was the last live candidate and it is now excluded.** An earlier version of this list
kept it open, on the reasoning that the thermal inversion requires more cooling work in the OC
position and fan power sits inside the board figure `nvidia-smi` reports. It also said separating
that contribution needed fan RPM logged alongside power, "which HWiNFO can report and this session
did not capture." **That was wrong: the session did capture it.** The raw logs carry 327 columns
including both GPU fan tachometers; fan RPM was dropped when the logs were distilled, not when they
were recorded, so the measurement existed already and needed no further access to the card.

Binned by core clock across eight bins shared by both positions, **the two lowest bins have both
fans reading exactly zero in both BIOS positions** - the card's zero-RPM mode holding through
130-175 W of load, 62 of 62 samples on one side and 16 of 16 on the other - **and the offset there
is still +32.7 W and +36.3 W.** Across the rest of the band fan speed ranges from 0 to 1453 rpm
while the offset stays between 30.5 and 43.8 W with no relationship to it. That bounds any fan
contribution at roughly 3 W of a 35 W gap, and two axial fans at those speeds cannot draw more than
a couple of watts in any case.

The same binning re-derives the offset itself as **+35.5 W**, against the **34.1 W** measured from
the sweep CSVs - two instruments, `nvidia-smi` per sweep point against HWiNFO board power binned by
clock, agreeing to 1.4 W by different routes.

**No mechanism is claimed, and the exclusion list is now longer rather than shorter.** What remains
unexplained is not only where the power goes but why the OC position is 5-7 C *cooler* at every
matched point while drawing more of it - at the two lowest points, with both fans stopped. Either
heat is moving differently or the extra power is dissipated somewhere that is not the die. Neither
is established here.

##### 5.5.1.2 The offset is not constant - it scales with memory traffic

Everything above measures the gap on `gemm`. The matched-frequency `membw` sweep that Session B
planned and did not collect was run on 2026-08-29, and it changes the description.

Across 13 shared targets from 855 to 2130 MHz the OC position draws **+56.3 W** for **+0.65%**
bandwidth - the same shape as `gemm`'s trade and a different magnitude. Restricted to the identical
855-1485 MHz band and the same seven points the `gemm` comparison uses:

| workload | approximate memory traffic | offset, OC against SILENT |
|---|---|---|
| `gemm` | ~12 GB/s | **+34.1 W** |
| `membw` | ~545 GB/s | **+57.0 W** |

**Same card, same BIOS pair, same frequencies, same instrument, and a 67% larger offset on the
workload moving 45 times more memory traffic.** A genuinely constant board-level draw cannot do
that, so "a roughly constant 34 W" is the right description of the `gemm` case and the wrong
description of the effect.

**This points where the earlier exclusions did not reach.** 5.5.1.1 ruled out memory *clock*, which
is identical at 9251 MHz in both positions - but a matching clock says nothing about the power the
memory subsystem draws at that clock. A higher memory rail voltage, or a more permissive memory
controller, would give exactly this signature: near-zero cost on a compute-bound workload and a
large one on a bandwidth-bound one.

⚠️ **That is a lead and not a finding, and it is offered with this section's own track record in
view.** Two hypotheses about this gap have been registered and refuted here already. What is
established is the measurement - the offset depends on the workload - and not any account of why.

The sweep also reproduces 5.5.3's flatness result on the other BIOS: SILENT `membw` spans 544.1 to
546.5 GB/s across 855-2130 MHz, 0.44% while core clock rises 149%, against 0.28% measured on the OC
position. That behaviour is not a property of one BIOS.

**n = 1 per side, four days apart**, both verified quiet and both HWiNFO-logged so the conditions
match in the ways this project has previously been caught by. The magnitude is far outside any
run-to-run spread measured here, which is the only reason a direction is reported at n = 1.

#### 5.5.2 The measurement is tighter on this card than on the reference one

The two `membw` sweeps taken on the OC BIOS agree to **+0.30%** on average across all thirteen
shared targets, from +0.24% to +0.39%. The 5060 Ti needed three sweeps of one configuration to
establish that its own `membw` figures carry a run-to-run spread near 1%, with single points
moving by up to 7%.

That difference is not explained here, and it matters for reading both sections: the sub-percent
comparisons 5.7 declines to make on the 5060 Ti might be available on this card, and the
1% resolution floor established there should not be assumed to transfer.

#### 5.5.3 What the OC BIOS spends its extra power on

> **Draft, 2026-08-26.** Written from the HWiNFO joins, which arrived four days after the sweeps
> themselves. NVML exposes neither core voltage nor crossbar clock; HWiNFO 8.52-6060 portable
> exposes both on this device, and the two were joined on timestamp by
> `tools/frequency-sweep/join_hwinfo_voltage.py`.

Section 5.5.1 measured the OC BIOS drawing 23.11% more power at matched frequency for no
throughput. It could not say what the power bought, because voltage was not observed. This section
observes it - but note what 5.5.1.1 established with the SILENT position measured too: **the floor
reported below is not what separates the two BIOSes, because both hold it.** What follows
characterises the OC position's operating behaviour; it does not explain the gap.

**The OC BIOS holds a hard voltage floor.** Across a ten-point fine sweep from 1200 to 1590 MHz,
HWiNFO reports **0.819 V** at all 10 points from 1200 to 1590 MHz - no movement at all - while
power rises 195.1 to 227.0 W (+16.4%). Voltage is constant while the core clock rises by a third
and the board draws 16% more.

The join threshold is part of that measurement and is stated rather than buried. At the tool's
30 W default an idle-gap sample - taken between sweep points, where the card sits at boost voltage
- drags the reported floor to 0.822 V. At `--min-power 120`, which is below every loaded reading
on a 310 W card and above every idle one, the floor is flat to the last millivolt HWiNFO reports.

**The crossbar has a floor of its own.** On the matched-grid sweep it is pinned at **1410 MHz**
across 7 of 13 targets, so the crossbar-to-core ratio falls from 1.649 to 0.947 before tracking
the core again above it. That is the same shape §5.7.4 found on the 5060 Ti, reached from the
opposite direction: there the ratio was driven down by flattening the curve, here it is a stock
vendor BIOS doing it unprompted.

##### The bandwidth workload is flat, and that is a control rather than a curiosity

Across the whole 855-2130 MHz band, `membw` throughput on this card does not move. The thirteen
points span **1.5 GB/s (0.28%)** while core clock rises 855 to 2024 MHz (+136.7%). Running the
top of the band instead of the bottom costs **+41.5% power** for **+0.28% bandwidth**, with core
voltage rising 0.819 to 1.081 V.

This matters because §5.7.3 argues that the 5060 Ti's bandwidth workload responds to core clock
because the *interconnect* - which shares the core voltage domain, unlike the DRAM devices - is
the limiter there. That argument predicts that a chip whose DRAM is genuinely saturated should
show no core-clock sensitivity at all, because there is nothing left for a faster interconnect to
unlock. The 3070 Ti reaches **90.4%** of its 608 GB/s bus. The 5060 Ti, across its stock and
memory-overclocked configurations, reaches **76.8-78.3%** of its own bus - each measured against
the memory clock that configuration actually ran, since the overclock moves the denominator. The
3070 Ti's core-clock sensitivity is 0.28%; the 5060 Ti's is the whole subject of 5.7.2.

Two chips with opposite bus saturation and opposite core-clock sensitivity, in the direction the
mechanism predicts, is stronger evidence for §5.7.3 than anything measurable on one card. It is
still two chips.

##### The compute ceiling is the board power limit, not the silicon

The matched-grid `gemm` sweep stops scaling partway up: the top 4 targets, 1815 to 2130 MHz, all
collapse to 1769-1780 MHz, while the 9 below them hold their lock exactly. Read alone that looks
like a clock ceiling, and it is not one. Decoding `clocks_throttle_reasons.active` gives
**SwPowerCap** at exactly those 4 targets and at none of the 9 below, with power peaking at
296.4 W. No thermal or hardware slowdown appears anywhere in the run, and the hottest sample is
61 C. So the OC BIOS's advertised 2190 MHz is not reachable under a compute load here, and what
stops it is a power limit rather than the part.

**Which power limit cannot be cited from a committed file.** The sweep tool queries
`power.max_limit` - the maximum a user could *set*, 350 W on this card - and never `power.limit`,
the value actually enforced. The vendor BIOS table read at collection time gives 310/310/350 W for
this position, and the per-point maximum power samples do pin against roughly 310 W, but that
table is a hand-recorded note in the run README rather than instrument output. No sweep in this
repository records its enforced power limit. That is a collection gap, not an analysis one, and it
is listed in the roadmap.

##### A prediction recorded before the measurement that tests it - and refuted by it

If the 23.11% matched-frequency power gap of §5.5.1 is voltage and nothing else, then at equal
clock and equal work, power scales with V-squared, and the Silent BIOS should hold its own floor
near 0.819 / sqrt(1.2311) = **0.738 V**.

That number was committed here before the sweep existed, with the outcomes stated both ways: read
near 0.738 V and the mechanism is established, read near 0.819 V and the two BIOSes differ in
something other than voltage.

**The sweep was run on 2026-08-27 and returned the second branch.** The Silent floor reads
0.812-0.819 V - the same floor as the OC position, within one sensor step of 6-7 mV. The
prediction is refuted, the voltage explanation of §5.5.1 is withdrawn, and the decomposition that
replaces it is §5.5.1.1.

The registration is left standing here rather than deleted. A prediction that fails is only worth
what it was worth before the result if it is still legible afterwards, and this one narrowed the
question usefully: it converted "the OC BIOS spends its power on something" into a measured set of
exclusions.

#### 5.5.4 Per-workload ranking does not transfer across architectures

Everything above compares two chips on two workloads. Running the full twelve-workload suite at
stock on the RTX 3070 Ti - the same suite, the same grid construction, iteration counts calibrated
for that card - makes the *workload* the unit of comparison rather than the chip, and answers a
question this study could not previously ask.

**The headline effect reproduces; the ordering does not.** Mean efficiency gain across the twelve is
**55.9%** on the 5060 Ti (the mean of six stock replicates) against **38.9%** on the 3070 Ti. Both
are an order of magnitude outside the 4.95-point replicate spread of §5.4.5, so the finding that
large gains exist survives a change of architecture. Which workloads carry them does not:

| workload | 5060 Ti | 3070 Ti | 5060 rank | 3070 rank |
|---|---|---|---|---|
| `bgemm64` | 74.5% | 25.3% | 1 | **10** |
| `conv` | 73.0% | 27.8% | 2 | 8 |
| `bgemm32` | 70.8% | 39.8% | 3 | 7 |
| `softmax` | 64.8% | 50.2% | 4 | 4 |
| `bgemm1024` | 59.2% | 23.0% | 5 | **12** |
| `layernorm` | 55.6% | 56.4% | 6 | **1** |
| `gemm` | 55.0% | 25.1% | 7 | 11 |
| `attention` | 54.1% | 48.4% | 8 | 5 |
| `copy` | 53.2% | 51.0% | 9 | **2** |
| `reduce` | 39.4% | 50.3% | 10 | **3** |
| `bgemm256` | 38.0% | 42.6% | 11 | 6 |
| `bgemm128` | 33.6% | 26.6% | 12 | 9 |

🔑 **A sixth replicate was added on 2026-09-05 and did not move a single rank.** Every position in
the 5060 Ti column above is identical to the one the five-replicate version reported; only the
percentages shifted, by at most 0.9 points. That is a stronger statement about the ordering's
stability than the correlation below, because it is a direct observation rather than a statistic:
adding twelve fresh sweeps changed no part of the thing this section is about.

**Spearman rank correlation between the two cards: −0.273.** One card's best workload is the
other's tenth; its fifth is the other's last. Only `softmax` holds its position.

**A ranking of noisy quantities would scramble against anything, so the control is what makes this a
result.** The identical statistic computed for the 5060 Ti against its own six stock replicates,
all fifteen pairs, gives **+0.881 to +0.986, mean +0.929**. Within a card the ordering is a stable,
reproducible property; across architectures it carries no information at all, and the cross-card
figure falls far outside the within-card range.

⚠️ **The range widened when the sixth replicate joined, and that is expected rather than
reassuring.** A range grows monotonically with sample size; the mean is the figure to read across
different n, and it moved by 0.005. Note also that r6 agrees with the other five at mean **+0.940**,
slightly *above* the +0.929 the set gives among itself, so the newest replicate is not the one
holding the range open.

That control also bounds the n = 1 concern on the 3070 Ti. Single 5060 Ti replicates rank
consistently with one another at ρ ≥ 0.88, so one replicate's *ordering* is a reliable thing to
have even though its individual gain figures carry no interval of their own.

**The optimum also sits in a different part of each card's range** — median **49.7%** of maximum
clock on the 5060 Ti against **70.2%** on the 3070 Ti, both unchanged by the sixth replicate. In MHz
the two are not comparable; as a fraction of range they still differ by twenty points.

*Both figures are against the highest COMMANDED clock, not the highest achieved one — which is the
opposite convention to the gain column above, where §5.5's `suiteRowFigures` anchors on the highest
achieved clock because the top target is not a frequency any workload actually runs at. The two
conventions give 49.7% and 56.3% for the same card. Neither is wrong; quoting one as the other
would be, so both are now pinned with the method attached.*

⚠️ **What this costs the constrained result.** §5.6.1 establishes that under a performance floor,
workload identity is worth most of the available gain. That is unaffected *within* a card. What this
adds is a boundary on its portability: a per-workload policy learned on one architecture does not
carry to another, so a deployment spanning chip generations would have to re-measure rather than
inherit. It also sharpens the caution around §5.1's reference set — if two consumer cards four years
apart disagree this completely on ordering, a 2017 datacenter part is not a source of per-workload
expectations for current consumer silicon, only of the shape of the frequency response, which is
what this work takes from it.

**Caveats.** One pair of architectures, one chip each, and the 3070 Ti swept once. The six 5060 Ti
replicates are **not six independent sessions** — r4 and r5 were collected back-to-back without a
reboot, so the set is five sessions, and it is **schema-mixed** (r6 at 0.3.2 records VRAM occupancy;
r1–r5 at 0.3.1 record none, and cannot be audited for it retrospectively) and **driver-mixed** (r1
on 610.88, r2–r6 on 616.56). Silent BIOS only
— the OC position of §5.5.1 was not swept with the suite. Different machines and different drivers
(610.88 against 616.56); §5.4.5 found the driver did not explain between-replicate variance on the
5060 Ti, which is not the same as showing it cannot matter across cards. All twenty-four sweeps are
stock. Full record in `../data/frequency-sweeps/rtx3070ti-suite-20260904/README.md`.

#### 5.5.6 The same sweeps under energy-delay product

Every figure above is throughput-per-watt, which values a watt saved and a second lost equally. That
is the right metric for "how efficiently can this chip do work", and the wrong one for "should I
actually run it here". **Energy-delay product** weights delay once more and **ED2P** twice more, and
both are standard in this literature. The sweeps already contain what is needed — the workloads are
fixed-work, so time is proportional to 1/throughput and no new measurement is required:

> energy = power / throughput  ·  EDP = power / throughput²  ·  ED2P = power / throughput³

⚠️ **Energy and throughput-per-watt are the same statistic here, not two that agree.** For fixed work
they are exact reciprocals, so their optima coincide by construction. This is stated because the
coincidence is easy to present as corroboration, and it is not.

| metric | median optimum | improvement at its own optimum | performance cost |
|---|---|---|---|
| energy = perf/W | 1537 MHz | 55.9% | 25.4% |
| **EDP** | **2078 MHz** | **29.9%** | **8.3%** |
| ED2P | 2187 MHz | 22.4% | 3.0% |

**The median optimum moves from 1537 MHz to 2078 MHz** — 541 MHz higher — once delay is priced at
all. **EDP gives 29.9% better EDP for a 8.3% performance cost**; ED2P gives **22.4% better ED2P for
3.0%**.

🔑 **This is the honest counterweight to the headline.** §5.5's 55.9% is real and is what
perf-per-watt says. Under a metric that prices time, roughly half the gain remains and the optimum
sits far closer to stock. Anyone deciding where to actually run a card should be reading the EDP row,
and §5.6.1's constrained analysis reaches the same place from the other direction — a 10% performance
floor gives 36.9% for 6.5%, close to the EDP figures here.

**The workloads split, and the split is structural.** Bandwidth-bound and light kernels (`copy`,
`reduce`, `softmax`, `layernorm`, `bgemm32`, `bgemm64`) put their EDP optimum at 1537–1971 MHz, near
the perf/W optimum. Compute-heavy ones (`bgemm128`, `bgemm256`, `bgemm1024`, `attention`, `conv`,
`gemm`) put it at 2310–2354 MHz. Where time is cheap the two metrics agree; where the card is doing
dense arithmetic, pricing delay pushes the answer most of the way back to stock.

#### 5.5.7 The optimum sits at the knee of the vendor's voltage curve, on all three chips

The standard account of why an efficiency valley exists invokes **leakage** — a fixed per-second
drain that eventually cancels the dynamic saving as a job stretches out. That mechanism is real and
is not disputed here. But it is **borrowed rather than observed**: `nvidia-smi` reports one
board-level power figure and cannot separate static from dynamic, so this study cannot see leakage
at all, and saying it causes the left-hand fall-off would be asserting a mechanism the instrument
cannot reach.

What the instrument *can* reach, through HWiNFO, is the vendor's own voltage/frequency curve — and
it supplies a sharper explanation.

**Below some frequency the stock curve stops lowering voltage and holds a floor.** Write power as a
fixed part plus a switching part:

> P = P_fixed + C · V² · f

Above the floor, V rises with f and the switching term grows superlinearly, so coming down the curve
sheds power much faster than speed. **Below the floor V is constant**, so power falls only linearly
while runtime grows as 1/f — the two roughly cancel — and P_fixed does not shrink at all while the
job takes longer. Efficiency stops improving and then declines.

**The prediction is therefore specific: the efficiency optimum should sit at the last frequency at
which voltage is still falling.** This relationship is not new: Schoonhoven et al. define it as the
**ridge point** and state the same consequence — "reducing the clock frequency beyond the ridge point
does not make the GPU more energy efficient, as performance drops with f while v is constant below
the ridge point" (*Going green: optimizing GPUs for energy efficiency through model-steered
auto-tuning*, arXiv:2211.07260, 2022) — measured on an NVIDIA A100 (ridge at 1025 MHz, 70% of peak)
and an RTX A4000 (1290 MHz, 72%), both datacenter or workstation parts. What follows measures the
same relationship on four consumer chips and then moves the floor by hand to test it causally, rather
than only observing it on the vendor's shipped curve. It does, on all three chips:

| | median suite optimum | stock voltage floor holds to | floor value | workloads picking it |
|---|---|---|---|---|
| RTX 5060 Ti (Blackwell GB206) | **1537 MHz** | **1552 MHz** | 0.720 V | — |
| RTX 3070 Ti (Ampere GA104) | **1485 MHz** | **1500 MHz** | 0.812 V | 7 of 12 |
| **RTX 3060 (Ampere GA106)** | **1260 MHz** | **1260 MHz** | **0.756 V** | **9 of 12** |
| **RTX 2060 Super (Turing TU106)** | **1065 MHz** | **975 or 1035 MHz — see below** | **0.631 V** | 5 of 12 |

⛔ **The fourth card does not confirm the relationship, and it does not refute it. It cannot decide
it**, and that is a boundary condition on the rule rather than a result about the card. Its floor is
**0.631 V held across 345 MHz** — seven consecutive points — and the whole low range is nearly as
flat: voltage moves **13 mV across the 570 MHz from 405 to 975 MHz**. It leaves the floor **6 mV at
a time**, one quantisation step of the reported voltage. Read strictly, the floor ends at 975 MHz and the nearest grid point is 960,
one step below the measured 1065. Allow a single sensor step and it ends at 1035, whose nearest grid
point is 1065 exactly. **The verdict turns on 6 mV.**

🔑 **The rule needs a crisp exit from the floor, and not every card provides one.** The RTX 3060
jumps 0.756 → 0.787 V, a 31 mV step with no ambiguity anywhere. Stating the rule without this
condition would make it look more portable than it is. The ambiguity is visible in the voltage
column itself, not inferred from the answer it produces.

⚠️ This card also has the loosest per-workload agreement in the study — **5 of 12**, against 6 to 10
elsewhere — so its median is doing more work than the others'.

On the 5060 Ti the optimum is **1537 MHz against a voltage floor holding to 1552 MHz**; on the
3070 Ti, **1485 MHz against a floor holding to 1500 MHz**; on the 3060, **1260 MHz** against a floor
whose last point *is* 1260 MHz. Each optimum falls within one grid step of the top of its own card's
floor, at three different absolute frequencies and three different floor voltages.

🔑 **The third chip was a registered prediction, not a third observation.** An earlier version of
this section named the RTX 3060 as "the cheapest available test" and stated the method in advance:
locate where the stock V/F curve stops flattening, and the optimum should be there. The card was
measured on 2026-09-10 and **the prediction held**, with nine of its twelve workloads picking
1260 MHz individually. The two exceptions above it are `bgemm128` and `attention` at 1365 MHz and
the one below is `bgemm256` at 1155 MHz. The registering sentence is left in the history of this
document deliberately: the test was specified before the hardware arrived.

⛔ **The floor VOLTAGE does not transfer between cards, and this is the more useful half of the
result.** That a chip's voltage differs from another's is not new by itself: Leng et al. [8] measured
it directly across five physical GTX 780 cards, one card's voltage consistently above another's by a
roughly constant offset, and Trakosa et al. [14] confirmed the same shape on six Radeon boards,
attributing it to process variation. ⚠️ **Both measure a different quantity** — V_min at a fixed
frequency, a correctness limit — **not the bottom of a dynamic V/F curve** — and neither connects a
chip's voltage to where its efficiency optimum sits. The three values measured here are 0.720 V,
0.756 V and 0.812 V. What is specific to this work is the quantified cost of ignoring the difference:
borrowing the 5060 Ti's 0.720 V for the 3060 would predict ~1530 MHz against a true optimum of 1260 —
a **270 MHz error**, worse than predicting a constant. Any application of this rule to a new card
must measure that card's floor first.

🔑 **A differing constant is a stronger outcome than a shared one would have been.** Had all three
read the same voltage, the most likely explanation would be a driver policy — interesting, but a
statement about software. They differ, so the floor is a property of the silicon **and the
relationship survives it anyway**, which is what makes this a finding about GPUs rather than about
one card.

⚠️ **And the floor is not explained by process node alone.** The RTX 3060 and the RTX 3070 Ti are
the same architecture on the same 8 nm node, and their floors differ by **56 mV**. Two parts that
share both an architecture and a process node cannot be told apart by either, so neither is
sufficient to determine the floor voltage.

⛔ **That is the whole of what three cards support, and an earlier version of this paragraph claimed
more.** It said "within-node spread exceeds between-node difference", comparing the 56 mV same-node
gap against the 36 mV gap between the 3060 and the 5060 Ti. **That is one of two available
between-node pairings and it is the smaller.** The three pairwise gaps are 36 mV, 56 mV and 92 mV,
the largest being the 5060 Ti against the 3070 Ti — a cross-node pair. With one sample per
architecture-node combination, no ranking of within-node against between-node variation is
available at all, in either direction. The collection protocol for growing n is given in
`docs/FLOOR-VOLTAGE-PROTOCOL.md`.

**The 3070 Ti's optimum is not an artefact of its grid.** Its suite grid continues to 1590, 1695 and
1771 MHz, so 1485 is an interior maximum rather than an edge, and **7 of the twelve** workloads pick
it independently — a median produced by agreement rather than by a scatter with nothing at its
centre.

⚠️ **On the first two cards the voltage and the optimum come from different runs.** Voltage
requires HWiNFO, **binned onto the sweep by core clock** — not joined on timestamp, because the
sweep CSV records durations rather than absolute timestamps and reconstructing point boundaries
from them fails the moment a point runs long — and it was collected on `gemm`/`membw` sweeps, while
the optima come from the twelve-workload suites. Same card and same stock configuration in each
case, but not the same session, and this project measures ~1.47% cross-session drift on `gemm`
alone.

✅ **That caveat is now closed on the third card.** The RTX 3060's HWiNFO log covers the
twelve-workload suite itself, so its floor and its optimum are measured **in one session on one
configuration**. Joined against two suite workloads independently:

| target MHz | 840 | 945 | 1050 | 1155 | **1260** | 1365 | 1470 |
|---|---|---|---|---|---|---|---|
| core V, `gemm` | 0.756 | 0.756 | 0.756 | 0.756 | **0.756** | 0.787 | 0.831 |
| core V, `copy` | 0.756 | 0.756 | 0.756 | 0.756 | **0.756** | 0.787 | 0.831 |

⛔ **AN EARLIER VERSION OF THIS PARAGRAPH READ THAT AGREEMENT AS EVIDENCE. IT IS NOT. RETRACTED
2026-09-12, the day after it was written.** It said the two workloads "agree to the millivolt at
every point, which is what confirms the floor is a property of the card rather than of what is
running on it." They do agree — and they agree **tautologically**.

`join_hwinfo_voltage.py` bins samples onto a sweep **by core clock, with no time filtering**. One
HWiNFO log covered the whole twelve-workload suite, and every workload visits the same locked
targets, so both joins drew from **the same pooled samples**. The identical sample count on all
thirteen rows is the tell. The two columns diverge only above 1680 MHz, where `gemm` power-caps and
`copy` does not, so their achieved clocks finally differ and the bins separate.

🔑 **The floor value itself stands.** Voltage at a locked clock is a property of the applied V/F
curve, and pooling samples taken at that clock reads it correctly. What does **not** stand is using
two joins from one log as independent confirmation of anything. The suite's median optimum is
**1260 MHz** — the last point on that floor.

⚠️ **Demonstrating workload-independence requires a separate HWiNFO log per workload**, which no run
in this study has. It remains plausible — a V/F curve is a property of the card — but it is
untested here and is not claimed.

⚠️ **This does not refute the leakage account, and is not offered as an alternative to it.** P_fixed
contains leakage along with memory refresh, display output, VRM losses and fan power, none of which
this instrument separates. What changes is which part of the explanation this work can claim to have
*measured*: the voltage floor is in the data, the leakage decomposition is not.

#### 5.5.8 Moving the floor moves the optimum; moving the curve above it does not

§5.5.7 is an observation. Three cards, three floors, three optima that land on them — but the curve
was **read, not moved**, so what it establishes is a correlation across three samples. Two runs on
the RTX 5060 Ti intervene on the curve directly, and each registered its predicted outcome before
the measurement that tested it.

Both are possible only because this card's voltage-frequency curve can be reshaped by hand through
a third-party tool and applied from the command line, which makes the *applied* curve an
experimental variable rather than a fixed property of the card (§3.2).

##### The manipulation: change the floor region and the optimum follows it

Two applied curves, **Profile 4** and **Profile 5**, differ by a constant **+465 MHz through the
low-voltage region** — 1912 against 1447 MHz at 700 mV, 2317 against 1852 MHz at 800 mV, the same
offset at both. Profile 4 lifts the whole low-voltage region bodily, while Profile 5 leaves it at
the factory curve — every one of its 63 decoded points at or below 840 mV is identical to the stock
profile to the megahertz. (Two points at 845 and 850 mV are not, by +202 and −2 MHz; both sit well
above the 720 mV load floor and outside the region this comparison turns on.)

**Four twelve-workload suites, 48 sweeps, in ABBA order** — Profile 4 at positions 1 and 4,
Profile 5 at 2 and 3 — so that both configurations are centred on the same instant in the session
and linear drift cancels exactly. Every other cross-configuration comparison in this study is
day-against-day and carries the ~1.47% cross-session drift measured in §5.4.4; this design removes
it.

> **Prediction: if the optimum is the last frequency on the load floor, lifting the floor region by
> 465 MHz should move the optimum by 465 MHz.**

| | median suite optimum |
|---|---|
| Profile 5 (factory low-voltage region) | **1537 MHz** |
| Profile 4 (low-voltage region +465 MHz) | **2002 MHz** |
| shift | **+465 MHz** |

**The median optimum moved by the predicted amount, and every one of the twelve workloads moved
upward** — no workload stayed put and none moved down.

⚠️ **The per-workload shifts scatter, and saying "+465 MHz in 12 of 12" would overstate this.**
**6 of the 12 moved by exactly 465 MHz**, and the remaining shifts **range from 79 to 540 MHz**. A single workload's optimum
is one point on a ~155 MHz grid measured twice, so replicate disagreement moves its average by a
whole grid step. The median across twelve workloads is the robust statistic and it is the one the
prediction addresses; the unanimity claim that carries weight is **the direction**, which is 12 of
12.

##### The negative control: change the curve *above* the floor and nothing happens

A shift of the whole low-voltage region shows the optimum responds to *something*. It does not show
the optimum responds to the **floor specifically**, because a curve edit large enough to move the
floor also changes the card's behaviour everywhere else.

**Profile 2** supplies the other half. It is identical to Profile 5 **below 800 mV** and differs
from it enormously above:

| | 700 mV | 720 mV | 800 mV | 875 mV | 925 mV | plateau |
|---|---|---|---|---|---|---|
| Profile 2 | 1447 | **1530** | 1852 | **2280** | **2455** | 3022 |
| Profile 5 | 1447 | **1530** | 1852 | **2850** | **3030** | 3030 |
| difference | 0 | **0** | 0 | **570** | **575** | 8 |

Both reach the 0.720 V load floor at the same ~1530 MHz, so the mechanism predicts a **570 MHz
change to the mid-band should move the optimum by nothing at all.** The prediction was recorded in
the run's `applied_settings` field before collection.

| | median suite optimum |
|---|---|
| predicted | **1537 MHz** |
| measured | **1537 MHz** |

It did not move. **9 of 12 workloads land on 1537 MHz individually.** The three exceptions
are `layernorm` and `gemm` at 1695 MHz and `reduce` at 2160 MHz.

⚠️ **Nine of twelve is at the high end of this study's range but is not exceptional**, and an earlier
draft of this paragraph called it the tightest concentration of any configuration. Recomputed across
every single twelve-workload suite, per-workload agreement with the suite median runs **from 6 to
10 of 12** — the full tune's first ABBA leg reaches 10, and the stock leg of §5.8's bracket also
reaches 9.
What matters here is not that the concentration is unusual but that the *median did not move* when
the curve above the floor was changed by 570 MHz.

##### 🔑 Why the two runs are worth more together than separately

The negative control is what licenses the manipulation. Profile 4 and Profile 5 are **not** a
perfectly single-variable pair: alongside the +465 MHz floor difference they also differ by roughly
**100 MHz in the mid-band**, where Profile 4 sits *below* Profile 5. Taken alone, the manipulation
cannot exclude that mid-band difference as the cause.

The negative control excludes it quantitatively. A **570 MHz** mid-band change — nearly six times
larger, in the same region — moved the optimum by **zero grid points**. A 100 MHz mid-band
difference therefore cannot account for a 465 MHz shift.

Across every applied curve measured on this card:

| configuration | curve reaches 0.720 V at | median optimum | mean efficiency gain |
|---|---|---|---|
| stock (Profile 3) | 1530 | **1537** | 56.99% |
| split (Profile 5, run `b1`) | 1530 | **1537** | 29.20% |
| split (Profile 5, run `s2`) | 1530 | **1537** | 27.63% |
| repair (Profile 2) | 1530 | **1537** | 31.15% |
| full tune (Profile 4) | **2002** | **2002** | 34.79% |

Four configurations reaching the floor at the same frequency give the same optimum; the one that
reaches it elsewhere gives an optimum there instead. The mean efficiency gain varies by nearly a
factor of two across these rows and carries no relationship to the optimum's location — which is
the point. **The floor sets *where* the optimum is; it does not set how much is available there.**

##### What the rule is worth, stated so it is not oversold

Reading the curve at the load-floor voltage and taking the nearest grid point scores **0.675% mean
regret across 192 sweeps**, against **1.961%** for the best single fixed frequency chosen with
hindsight — a factor of 2.90. It **ties**, to three decimal places, a best-constant-*per-configuration*
baseline also fitted with hindsight, because it selects the identical frequency every time. Its
advantage over that baseline is not accuracy but cost: a per-configuration constant requires
sweeping every configuration first, and reading the curve requires no benchmark at all.

🛑 **The entire configuration axis is worth 1.29 points of regret against a headroom of 30–57
points.** Choosing the right frequency-selection *policy* barely matters next to choosing to select
a frequency at all. Any citation of the 2.90× without this sentence overstates the result.

##### Limits

⚠️ **Both interventions are on one chip.** The third-chip evidence in §5.5.7 is observational, and
the manipulation and control arms are not repeated on it, because reshaping an applied curve
requires software that was not installed on a machine this study does not own.

⚠️ **The frequency grid is approximately 155 MHz wide**, so a prediction needs only to fall within
half a step to select the correct point. The agreement is genuine and it is also coarse; §5.6
reports the same predictions under the finer regret metric, which does not round.

⚠️ **Four applied curves produce only two distinct predicted values**, 1537 and 2002 MHz, so
"configuration" behaves close to a binary variable in this dataset. A ladder of intermediate floor
offsets is registered in `docs/REGISTERED-PREDICTIONS.md` and has not been collected.

#### 5.5.5 Limits

Two chips is not a sample. The BIOS comparison is one sweep per position on the compute workload
and one against two on the bandwidth workload, on a card measured once, in one case, at one
ambient, in a single session. The +23% matched-frequency power gap is far outside anything
run-to-run variation in this project has produced; the +0.56% peak difference is not, and should
be read as "no measurable gain" rather than as a small one.

The matched-frequency comparison covers seven of thirteen grid points, 855-1485 MHz. The two
BIOSes build their sweep grids from their own maxima and therefore share no targets at all; the
seven come from an additional sweep run specifically to create an overlap, which was given the
wrong ceiling and produced half the intended match. The upper half of the band, including the
region where both cards flatten out, has no matched-frequency measurement.

Nothing about the tuning of 5.7 was applied to this card. It is a customer machine, and only the
configurations the vendor shipped were measured.

### 5.6 The performance-constrained optimum

§5.1's 44.4% is the *unconstrained* optimum: best efficiency at any cost, and the cost is a mean
13.7% performance. Almost nobody wants that trade. The question users actually ask is constrained —
maximise efficiency subject to keeping at least some fraction of stock performance — and the same
data answers it. Run `python analysis/analyze_constrained.py`.

**Reference dataset, 33 workloads.** Realised loss is below the floor because the optimum must land
on one of 13 grid points, so the constraint is usually overshot; every saving here is therefore a
lower bound on what a continuous knob would reach.

| floor | workloads that downclock | efficiency gain (mean / median) | realised perf lost (mean / worst) | power saved | median freq |
|---|---|---|---|---|---|
| 95% | 33/33 | **28.5% / 22.3%** | 3.3% / 4.9% | 23.4% | 1275 MHz |
| 90% | 33/33 | 35.8% / 36.6% | 6.5% / 9.9% | 30.5% | 1080 MHz |
| 85% | 33/33 | 41.1% / 43.3% | 9.4% / 15.0% | 35.5% | 952 MHz |

**Every workload benefits at a 5% budget** — the worst case is still +3.3% efficiency, and the mean
28.5% gain costs only 3.3% realised performance. Two-thirds of the unconstrained 44.4% survives a
constraint that removes three-quarters of its performance cost, which is the practically useful form
of the result.

**Against GEEPAFS [6], on the same chip.** Their online policy achieves 26.7% mean efficiency gain
for 5.8% performance loss. At a 95% floor this analysis reaches 28.5% for 3.3% — better on both
axes. **That comparison must not be presented as a win.** GEEPAFS chooses frequencies live with no
prior knowledge of the application; this is an offline oracle that has already measured the entire
curve for every workload. An oracle is *supposed* to beat an online policy, and a margin this
narrow — 1.8 points of efficiency — is the more notable observation: it bounds how much a perfect
predictor could add over an existing deployed method, and the answer is *not much*.

That bound applies to *adaptive* methods only, and reading it as a general statement about
frequency selection would be a mistake — §5.6.1 shows the comparison against a non-adaptive baseline
runs the other way entirely.

#### 5.6.1 The constraint is what makes workload identity valuable

§5.2 found that a probe-based model does not beat a single fixed frequency, and that null stands.
It was measured *without* a performance constraint. Applying the same baseline under one reverses
it.

A fixed-frequency policy must honour its guarantee on **every** workload it might meet, so it cannot
choose a frequency that is merely good on average — it is pinned by the most frequency-sensitive
workload in the set. On the V100 at a 95% floor, `BiCG` and `GeMM` need at least 1462 MHz, while
`CNN_1.5M`, `ViT_t` and `RL-PPO` would be fine at 757 MHz. One frequency has to serve both ends.

| floor | per-workload optimum | best single fixed frequency | pinned at | gap | share of available gain |
|---|---|---|---|---|---|
| 95% | 28.5% | **4.9%** | 1462 MHz | **23.6 pp** | **83%** |
| 90% | 35.8% | 10.2% | 1402 MHz | 25.6 pp | 72% |
| 85% | 41.1% | 22.2% | 1275 MHz | 18.9 pp | 46% |
| 80% | 43.1% | 27.5% | 1207 MHz | 15.6 pp | 36% |

**At a 95% floor, 83% of all available efficiency gain requires knowing which workload is running.**
The fixed policy can descend only one grid step below stock and captures 4.9% of an available 28.5%.

Robustness: excluding the four flat-top workloads of §5.6 whose curves may be noise, the gap is
still **20.7 pp of 25.8 pp** — 80%. The effect does not depend on the questionable points.

The consumer sweeps reproduce the mechanism at smaller scale, and one detail is worth stating
plainly: **at a 95% floor no single frequency is feasible for both workloads at all**, because
`gemm` needs 2592 MHz to hold 95% and no shared grid point that high exists in `membw`'s sweep. The
tool reports that rather than substituting a number. At a 90% floor the gap is 7.4 pp of 26.2 pp
(28%), smaller than the V100's — expected, since two workloads of similar clock sensitivity span
much less of the space than 33.

##### 5.6.1.1 Twelve consumer workloads, and the frequency a policy actually sets

Two workloads span little of the space. A suite of twelve, built to span arithmetic intensity from
0 to 1365 FLOP/byte, spans considerably more, and it moves this result from the reference dataset
onto hardware measured here (§3.3, `../data/frequency-sweeps/stock-suite-20260829/`).

**One methodological change is required first, and it is not a detail.** The comparison above keys
each curve by the clock the card *achieved*. On consumer hardware that does not work across a
workload population: at one commanded target each workload clamps to whatever its own power draw
allows, so twelve sweeps sharing thirteen commanded targets share only **5** achieved clocks —
`bgemm128` tops out at 2565 MHz where `copy` reaches 2751 — and no fixed-frequency comparison can
be computed at all. The V100 data has no clamping, so the distinction never arises there.

**A fixed-frequency policy sets a target and accepts what each workload sustains.** A deployment
runs `nvidia-smi -lgc 2625`; it does not get to choose the achieved clock. The policy variable is
therefore the commanded frequency, and keyed that way the twelve sweeps share all thirteen points.
`analyze_constrained.py --basis commanded` does this; `--basis achieved` remains the default and
every number elsewhere in this paper is unchanged by it.

| floor | per-workload | best fixed | at (commanded) | gap | share needing workload identity |
|---|---|---|---|---|---|
| 99% | 14.8% | 1.1% | 2782 MHz | 13.7 pp | 92% |
| **95%** | **31.7%** | **1.1%** | **2782 MHz** | **30.5 pp** | **96%** |
| 90% | 39.2% | 5.9% | 2625 MHz | 33.3 pp | 85% |
| 85% | 42.9% | 17.3% | 2475 MHz | 25.6 pp | 60% |
| 80% | 45.5% | 28.4% | 2317 MHz | 17.1 pp | 38% |

**At a 95% floor, 96% of the available efficiency gain requires knowing which workload is
running** — against 83% on the V100. The consumer case is the stronger one, and the reason is
visible in the suite: the twelve workloads' unconstrained optima cost between 4.0% and 47.8% of
performance (§3.3), so the workload that pins a fixed policy is far more demanding relative to the
rest than any of the V100's 33.

⚠️ **And the basis that makes this computable also exposes what it costs.** At the chosen commanded
2782 MHz the twelve workloads actually held **2564 to 2755 MHz, a spread of 191 MHz**. A
fixed-frequency policy on consumer hardware does not deliver a fixed frequency. That is a real
limitation of the policy rather than of the measurement, it applies equally to the fixed baseline
this table reports, and no analysis keyed on achieved clocks would have surfaced it.

**Caveats.** Twelve workloads, n = 1 each, one card, one configuration. Four of the twelve were
collected under looser conditions than the other eight — counts calibrated at a 7% baseline rather
than under 5%, and the machine under remote control with encoder and decoder verified idle
throughout (`../data/frequency-sweeps/suite-pilot-20260829/README.md`). Same-session run-to-run
spread on this card is ~0.76% on THROUGHPUT and cross-session drift ~1.47% (§6). ⚠️ Neither bar
applies to the figures in this table: they are efficiency gains, and §5.4.5 measures efficiency
reproducing at ~2.08% across three replicates because power - the term efficiency divides by -
reproduces at ~2.07% rather than 0.87%. **Read against the right bar the 1.1% fixed-policy figures
are below the noise floor rather than near it**, which strengthens rather than weakens the reading:
a fixed policy recovers nothing distinguishable from zero. The 30.5 pp gap remains far outside any
of these bars. An earlier draft judged the 1.1% against the throughput figure; that was the wrong
denominator.

**This is the reconciliation between §5.2 and the project's premise.** Unconstrained, the efficiency
curve is flat near its peak and one frequency serves nearly everything — hence the null, which is
real and stays reported. Constrained, the flat region is cut off from below by whichever workload
loses performance fastest, and workload identity becomes worth most of the available gain. The
defensible claim is therefore not *"per-workload tuning is worth its cost"* nor *"it is not"*, but
that **the answer inverts depending on whether a performance guarantee is required, and the
unconstrained measurement is the misleading one** — because a performance guarantee is what
essentially every real deployment has.

It also explains why GEEPAFS is a substantial result rather than an over-engineered one: adaptation
is doing real work under a constraint, which is precisely the regime it targets.

**Consumer hardware, and this is where the constraint bites unevenly.** The two workloads diverge
sharply once a performance floor is imposed, in a way the unconstrained optima did not reveal:

| floor | `gemm` (compute-bound) | `membw` (memory-bound) |
|---|---|---|
| 99% | 0% gain — cannot move | 21.6% gain, 0.9% lost, 18.5% power saved |
| 95% | **0% gain — cannot move** | **36.4% gain, 4.9% lost, 30.2% power saved** |
| 90% | 16.1% gain, 7.1% lost | 36.4% gain, 4.9% lost |

At a 5% performance budget `gemm` can do nothing at all, while `membw` gains 36.4% efficiency and
saves 30.2% power. The unconstrained optima differ by only 146 MHz (§5.4.1) with under 2% penalty
for using one for the other; **the constrained optima differ qualitatively.** Workload-aware
frequency selection matters far more under a performance constraint than without one — which is an
argument for the project's premise that the §5.4.1 result on its own does not make.

**Caveats, all reported by the tool rather than left to the reader.** Floors of 100% and 99% sit
inside a 1% noise band and are flagged as unquotable: 4 of the 33 V100 workloads (CNN_1.8M, FDTD,
CNN_1.5M, RL-PPO) record performance *above* their own 1530 MHz value at some lower frequency, by
+0.62 to +1.44 percentage points. Either those curves are genuinely flat across the top — which
would mean real downclocking at literally zero cost, and they are the memory-bound workloads where
that is most plausible — or a 1% excess is noise in a dataset averaging 5 repeats. The data cannot
separate the two and neither is asserted. Separately, the consumer reference is the card's
*sustained maximum* on an overclocked card whose offsets were never recorded, so the consumer half
is shape, not magnitude, until §5.4's interleaved stock-versus-tuned run exists.

The optimiser brute-forces the feasible set rather than using the closed form
`max(unconstrained optimum, lowest feasible frequency)`, and reports whether the two agree. They
agree on all 33 V100 workloads. They disagree on the consumer sweeps, but only by 1–5 MHz, and the
tool identifies why: the card clamped several high targets onto one achieved clock, so those are
repeat measurements of one condition rather than distinct grid points.

#### 5.6.2 Probing captures most of it - and the fitting earns none of it

§5.6.1 measured the *oracle* gap: what perfect knowledge of each workload's curve would be worth.
That is an upper bound, and it is not available to anyone who has to discover the curve first. This
section asks the usable question - whether a strategy that must **learn** each workload from a few
measurements captures the gap - and answers it with two results that have to be reported together.

Leave-one-workload-out over the same 33 workloads, four probes at **757, 885, 1012 and 1530 MHz**,
at a 95% floor. Run `python analysis/models/predict_constrained_frequency.py`.

| Strategy | Mean efficiency gain | Floor violations | Exact match |
|---|---|---|---|
| stock (do nothing) | 0.0% | 0 | 0.0% |
| best fixed frequency | 4.9% | 0 | 6.1% |
| **interpolation between the four probes, no fit** | **25.4%** | **0** | 33.3% |
| probe model (Ridge) | 28.1% | **8 of 33** — disqualified | 39.4% |
| probe model (Ridge, calibrated to respect the floor) | 19.6% | 0 | 15.2% |
| oracle (upper bound) | 28.5% | 0 | 100.0% |

**Efficiency taken below the floor is not efficiency the constraint permits**, so a strategy that
breaks it is disqualified rather than ranked. The giveaway is *negative regret* against the
oracle, which is arithmetically impossible for a strategy that stayed feasible; Ridge produces
exactly that at a 90% floor. The tool disqualifies rather than reporting a winner.

**First result: probing is worth its cost.** Straight-line interpolation between the four probes
reaches **25.4% against the fixed policy's 4.9%**, breaking the floor on no workload - **87% of the
gap** §5.6.1 identified between a fixed policy and the oracle. It holds at the other floors too:
94% of the gap at 90%, 91% at 85%.

**Second result: the fitting is not the part earning it.** Ridge appears to beat interpolation at
28.1%, but only by violating the floor on 8 of 33 workloads, worst by 3.81 points. Made to respect
the floor, it falls to **19.6% - below the 25.4% of drawing straight lines between the same four
probes.** No fitted variant beats plain interpolation on this data. The honest summary is *measure
a few points, interpolate, and attach a performance guarantee* - not *fit a model*.

⚠️ **This is not the claim [1] succeeds at.** [1] predicts a configuration for a kernel that has
never run, from static code features; every strategy in the table above, interpolation included,
already measures the same four points on the same kernel. The comparison here is between two ways of
using measurements already taken, not between measuring and not measuring — see §5.2 for the fuller
contrast.

**Why interpolation is the safe one is measured rather than assumed, and it is a property of the
curve rather than of the method.** Performance here is predominantly concave - **64.1%** of second
differences curve downward - so a straight line between two probes sits below the true curve.
Interpolated performance is an under-estimate **88%** of the time, by a mean of 0.90 points, which
biases every frequency choice upward. Under a floor, an upward bias is free safety.

⚠️ **On a convex performance curve the sign flips and interpolation would violate the floor more
often than the fitted model, not less.** "Interpolate the probes" is therefore a consequence of
this dataset's curve shape and must not be carried away as a general recommendation. The diagnostic
prints on every run so the condition travels with the result.

The fixed baseline is not automatically the safe choice either: at a 90% floor it breaks the floor
on 1 of 33 workloads, because the frequency that satisfies 32 workloads does not satisfy the 33rd.

**Caveat.** 33 workloads on one V100, every number in-dataset.

##### 5.6.2.1 It has now been retested on consumer silicon, and it holds

The caveat above previously ended *"this says nothing about consumer silicon until it is retested
there, and the collected consumer data does not yet carry enough workloads for a
leave-one-workload-out design."* The suite of §3.3 was built to remove that objection, and it does:
twelve workloads spanning 0 to 1365 FLOP/byte, on one card, keyed by commanded frequency for the
reason given in §5.6.1.1. Run `python analysis/models/predict_constrained_frequency.py
--source consumer`.

Leave-one-workload-out, 12 folds, probing at **1237, 1545, 1852 and 3090 MHz** — the V100's grid
*positions* carried across rather than probes selected on this data, because probes optimised
against the curves they are then scored on would be fitted to their own test set.

| strategy | mean gain | floor violations |
|---|---|---|
| stock (do nothing) | 0.0% | 0 |
| best fixed frequency | 1.5% | **1 of 12** — disqualified |
| **interpolation between the four probes, no fit** | **27.7%** | **0** |
| probe model (Ridge) | 31.8% | **2 of 12** — disqualified |
| probe model (Ridge, calibrated to respect the floor) | 23.9% | 0 |
| oracle (upper bound) | 31.7% | 0 |

**Both halves of the V100 result reproduce.** Probing is worth its cost — interpolation captures
**87% of the distance** between the fixed policy and the oracle, the same share it captures on the
V100, computed the same way by the same tool.
And the fitting still earns none of it: Ridge leads only by breaking the floor on 2 of 12
workloads, and made to respect it falls to 23.9%, below the 27.7% of drawing straight lines between
the same probes.

**The condition travels too, which is what makes the recommendation portable rather than lucky.**
§5.6.2 argued interpolation is safe here because performance is predominantly concave, and warned
that on a convex curve the sign flips. Measured on consumer silicon the curves are *more* concave
than the V100's — **68.2%** of second differences curve downward against 64.1%, and interpolated
performance under-estimates **91%** of the time against 88%. The upward bias that makes
interpolation floor-safe is larger on this hardware, not smaller.

⚠️ **The fixed-frequency baseline breaks the floor here, and on the V100 at this floor it does
not.** One workload of twelve. That is the same effect §5.6.1.1 measures from the other direction:
a single frequency chosen for twelve workloads of this spread cannot hold a 95% guarantee for all
of them, so the honest reading is that the fixed policy is not merely poor on consumer hardware but
infeasible at the floor most deployments would want.

**Caveats.** Twelve workloads on one card, n = 1 each, every number in-dataset. Chip-to-chip
variation is untested and needs repeat units of one SKU this project does not have. Four of the
twelve were collected under looser conditions than the other eight (§5.6.1.1).

#### 5.6.3 What the headroom is worth once the hardware is paid for

Every efficiency figure above is per-GPU at fixed work. A deployment does not buy efficiency, it
buys throughput, so the question that decides whether any of this is actionable is what happens when
total output is held constant and the fleet is resized to compensate. Running each unit slower means
buying more units, and the extra silicon is a real cost set against the saved energy.

The two operating points in this section answer it directly, using only measured quantities:

| operating point | perf retained | power per unit | units for equal output | fleet power |
|---|---|---|---|---|
| stock | 100% | 100% | 1.000 | 100% |
| unconstrained optimum (5.1) | 86.3% | 59.9% | **1.159** | **69.4%** |
| 95% floor (5.6) | 96.7% | 76.6% | **1.035** | **79.2%** |

The unconstrained optimum trades **15.9% more units for 30.6% less fleet power**. The 95% floor
trades **3.5% more units for 20.8% less**. Both rows follow arithmetically from the measured
performance cost and power saving; nothing is assumed yet.

**That converts to a single break-even ratio, which is the useful form.** The extra hardware is paid
once and the energy is saved continuously, so the trade pays exactly when lifetime energy cost
exceeds a fixed fraction of purchase price:

    unconstrained   0.159 / 0.306 = lifetime energy must exceed 52% of unit price
    95% floor       0.035 / 0.208 = lifetime energy must exceed 17% of unit price

**The constrained point is roughly three times easier to justify than the unconstrained one**, and
that gap is wider than the efficiency difference between them would suggest. Giving up two-thirds of
the headroom removes four-fifths of the extra capital. This is the same flatness near the efficiency
peak that 5.4.1 and the r1-versus-r2 replicate both report, seen through its consequence rather than
its shape.

⚠️ **The following worked examples are ILLUSTRATIVE and use assumed prices, not measurements.** Unit
prices, electricity tariffs, duty cycle and PUE are inputs a reader must supply for their own
deployment; they are stated here only to show the ratio being applied, and no claim in this paper
depends on them.

| illustrative case | assumed price | power | assumed lifetime energy | ratio | unconstrained | 95% floor |
|---|---|---|---|---|---|---|
| consumer card, high duty | $450 | 180 W | ~$850 (3 yr) | 1.89 | pays | pays |
| datacenter accelerator | $30,000 | 700 W | ~$5,200 (5 yr) | 0.17 | **loses** | marginal |

**The honest conclusion is that the unconstrained optimum is not a cost argument on expensive
silicon.** Where a unit costs tens of thousands and its lifetime electricity is a sixth of that,
buying 15.9% more units to save 30.6% of the power loses money, and this paper should not be read as
recommending it. The 95% floor survives that same arithmetic, which is a further reason to treat it
rather than 5.1's 44.4% as the deployable result.

**Two cases escape the trade entirely, and they are not edge cases.**

First, **a facility that cannot add units at all**. Where the binding constraint is provisioned
power, cooling, or rack space rather than capital, the compensating purchase is not available at any
price, and efficiency is the only remaining way to raise throughput per provisioned watt. The
capital argument never runs.

Second, **a fleet that is not saturated**. Resizing is only required if the existing units are
already at full utilisation. A deployment with slack keeps its output and simply pays less power, and
the trade is unconditionally favourable.

### 5.7 Separating the two tuning knobs

> **Written 2026-08-20, second pass 2026-09-04.** The mechanism of 5.7.3 was re-verified against
> the committed voltage extracts and its headline figures are now pinned by the claim auditor
> rather than only checked by eye. **One claim did not survive the pass and is withdrawn in
> place** - 5.7.1 had read a 2% power agreement as meaningfully tighter than 3%, and both sit
> inside the 2.07% at which power reproduces (5.4.5).
>
> **The contamination caveat on 5.7.4 and 5.7.5 is unaffected and stands.** Those measurements
> predate the capture-software finding of 5.4.4 and have no clean counterpart; a second pass over
> the prose cannot fix that, and does not claim to.

Every earlier consumer result treats "tuned" as one setting. It is two: a **memory overclock**
(+2500 MHz offset, 16301 against a 14001 rating) and a **core V/F curve** pinned flat near
3000 MHz at every voltage at and above ~925 mV. Three sweeps separate them - full tuned, memory
overclock only with the core curve reverted to stock, and stock - on the same card at identical
locked targets.

**The two knobs have opposite effects on the two workloads.**

| | memory overclock | core V/F curve |
|---|---|---|
| `gemm` (compute-bound) | nothing measurable, plus or minus 1% | the entire benefit: -17% to -28% power at matched clock, +12.1% sustainable ceiling |
| `membw` (bandwidth-bound) | the entire benefit: +2.4% to +17.1% over stock at identical targets | actively harmful: memory-only delivers up to 29.6% more, so the curve costs up to 22.9% of throughput across 1560-1867 MHz |

⛔ **The `membw` row read *"+3.6% to +16.1% over stock"* and *"up to -29.6% throughput"* until
2026-09-24**, when this table was first pinned by the auditor.
- **The first pair was not a matched comparison.** It paired stock at 1545/1702/1852/2010 MHz with
  memory-only at 1560/1710/1867/2025, a day apart, although the paragraph above promises identical
  locked targets. Against the one stock `membw` sweep on the same 10-point grid, the range is
  +2.4% to +17.1%.
- **The second was a ratio written as a signed loss.** Memory-only delivers 29.6% more than tuned
  at 1867 MHz; as a change from memory-only to tuned that is -22.9%. 5.7.2's own table reports the
  29.6% correctly, as memory-only over tuned. The number was never recomputed; only its base was
  misread.
- ⚠️ All three `membw` sweeps in these comparisons date from 2026-08-19/20, before the
  capture-software guard (5.4.4).

#### 5.7.1 The matched-frequency power reduction is entirely the core curve

Section 5.4 reports the tuned configuration drawing 17-28% less power than stock at identical core
clock on `gemm`, and attributes the efficiency gain to that rather than to the higher peak clock.
That was measured with both knobs applied and had not been separated. It survives separation:

**All three legs below are the 2026-08-22 clean-protocol runs, two sweeps per configuration,
averaged.** The originals were measured before the capture-software contamination of 5.4.4 was
known. Each configuration was confirmed applied before measuring rather than assumed: stock and
memory-only by the core clock collapsing to ~2610 MHz at a 3090 MHz target, tuned by it holding
2947.6 MHz, and memory-only additionally by memory reading 16301 MHz under load against stock's
13801 MHz - a memory overclock is invisible to a core-clock check. Measured cleanly the reduction
is 17-28% where the contaminated pair gave 18-26%, so the finding is slightly stronger than
published, not weaker.

| locked clock | tuned vs stock (power) | memory-only vs stock (power) |
|---|---|---|
| 1852 MHz | **-22.3%** | -0.2% |
| 2010 MHz | **-28.3%** | +1.1% |
| 2167 MHz | **-21.4%** | -0.1% |
| 2317 MHz | **-17.2%** | +1.6% |

Memory-only reproduces stock power to within 2%. ⚠️ **That is at the noise floor rather than
below it:** section 5.4.5 measures power itself reproducing at **2.07%** across three replicates of
an unchanged configuration. An earlier version of this passage read the 2% against the 3% the
contaminated pair had shown and concluded that cleaning the measurement had sharpened the result.
**That conclusion is withdrawn.** Both figures sit inside the reproducibility of the quantity being
compared, so neither is distinguishable from the other, and a 1-point difference between them
cannot be evidence of anything.

What survives is the direction, which is what this table is for: four points, two of each sign, no
systematic offset. Memory speed does nothing measurable for a compute-bound workload, which is the
sanity check this design should pass and does. Temperatures at these four points matched to within
0.6 C.

The curve additionally raises the sustainable ceiling: at stock and at memory-only the card cannot
hold the top three grid points, collapsing to ~2590 MHz and ~15.7 TFLOP/s, while with the curve it
holds 2948 MHz and reaches 17.61 TFLOP/s (+12.1%). The denominator is stock's own peak,
15.71 TFLOP/s at 2598 MHz. An earlier version of this sentence said +12.3%, which is the
comparison against stock's LAST grid point (15.68 at 2588 MHz) rather than its best, and
did not say so.

#### 5.7.2 The same curve costs a bandwidth-bound workload up to 22.9% (memory-only leads by up to 29.6%)

⛔ *This heading read "costs a bandwidth-bound workload up to 29.6%" until 2026-09-24. The table below reports 29.6% correctly, as memory-only over tuned; the loss as a share of memory-only's throughput is 22.9%.*

Across 1560-1867 MHz the fully tuned configuration runs `membw` flat at ~295 GB/s while stock rises
312 to 332 to 342. Five consecutive points sit inside a 1.3% band while core clock rises 20%.

Three mechanisms were eliminated before the curve was implicated. It is **not** contention from
concurrent monitoring - a repeat run with nothing else touching the device reproduces the plateau to
within 1%. It is **not** a memory downclock - memory-clock telemetry was added to the sweep tool for
this question and reads exactly 16301 MHz at every point, `min` equal to `max`. It is **not**
throttling - `clocks_throttle_reasons.active` was decoded across all runs and shows no power cap, no
thermal slowdown and no hardware slowdown, at 42-52 C.

Reverting only the core curve removes the plateau entirely; throughput becomes monotone, 291.8 GB/s
at 1402 MHz to 400.4 at 2100:

| locked clock | memory-only | full tuned | throughput delta | efficiency delta |
|---|---|---|---|---|
| ~1560 MHz | 323.0 | 294.1 | +9.8% | +8.8% |
| ~1710 MHz | 360.1 | 297.8 | +20.9% | +9.3% |
| ~1867 MHz | 385.7 | 297.5 | **+29.6%** | **+12.1%** |
| ~2025 MHz | 399.9 | 326.7 | +22.4% | +1.7% |

In this band the flattened curve costs more throughput than it saves power.

#### 5.7.3 Interpretation

At identical core clock and identical memory clock, the tuned configuration draws ~10% less power
and delivers ~20% less bandwidth. The remaining free variable is voltage. The working hypothesis is
that forcing the core clock into 1560-1867 MHz selects a voltage point *below* the curve's flattened
region, where the applied and stock curves diverge most, and that the memory controllers and
interconnect - which share the core voltage domain, unlike the DRAM devices themselves - become the
limiter. `gemm` is unaffected because at ~1365 FLOP per byte it is nowhere near saturating that path.

**This mechanism is measured as an association, not isolated as a cause.** NVML exposes neither
core voltage nor interconnect clock, but HWiNFO exposes both, and two further sweeps were run with it
logging alongside: one fully tuned, one at full stock.

⛔ **THIS PARAGRAPH OPENED *"This mechanism is established by direct measurement"* UNTIL
2026-09-24, AND THAT IS RETRACTED.** An outside adversarial audit found it on 2026-09-18, and every
figure was recomputed here from the committed extracts. The correction reached the project's notes
that day and this paper only now. What the sweeps show:
- the flattened curve goes with a low, flat crossbar clock and a ~300 GB/s plateau;
- restoring the curve's low-voltage slope removed both, as predicted in advance (5.7.4).

**That is an association plus a successful predicted intervention, not a demonstrated mediator:**
- **The crossbar was never set independently.** A limiter upstream of DRAM that firmware sets from
  the same V/F policy (L2, a memory-controller clock, or another low-voltage domain) would produce
  the same table, with the crossbar as a correlated indicator.
- **The two telemetry sweeps are not memory-clock matched**, as set out below.

Settling mediation needs the crossbar set directly, at a fixed core curve and a fixed memory clock.
This card offers no runtime control of it.

| core MHz | stock volts | stock crossbar | crossbar/core | tuned volts | tuned crossbar | crossbar/core |
|---|---|---|---|---|---|---|
| 1402 | 0.720 | 1335 | 0.953 | 0.720 | 1320 | 0.942 |
| 1560 | 0.720 | 1470 | 0.947 | 0.720 | 1342 | 0.863 |
| 1710 | 0.760 | 1642 | 0.965 | 0.720 | 1342 | 0.788 |
| 1867 | 0.805 | 1815 | 0.976 | 0.720 | 1350 | 0.726 |
| 2025 | 0.840 | 1942 | 0.963 | 0.720 | 1470 | 0.729 |

Across the swept range stock core voltage rises 0.120 V while the tuned card's rises 0.020 V: the
flattened curve holds one voltage, as configured. The consequence is the crossbar clock - the
SM-to-memory-controller interconnect. At stock its ratio to core clock holds between 0.928 and
0.976. Under the flattened curve that ratio collapses from 0.942 to 0.725: the interconnect
decouples from the core and stops scaling. ⚠️ The ratio is arithmetic on the two clocks already
tabulated, not a second measurement. It is a compact way to show the decoupling, and it cannot tell
a crossbar bottleneck from a shared policy that holds the crossbar and some unobserved domain low
together.

**The contribution claimed here is the measured association, not the domain.** That XBAR is an
independently clocked domain coupled to core voltage is established in the reverse-engineering
literature [11] and is not claimed as a finding of this work; §2.5.1 sets out what is already known
and what was searched for. What follows is what was measured alongside a pinned curve voltage.

⛔ **THE MEMORY IS NOT SLOWER, AND THAT IS THE POINT.** The obvious reading of a falling ratio is
that the memory overclock stopped working. On the tuned card it did not: its DRAM logs
15858–16301 MHz across the sweep, with the +2500 offset applied, while throughput sits on the
plateau. What stops scaling is upstream of the memory devices, on the chip. The memory can deliver
the bandwidth (the memory-only configuration of 5.7.2 does, at the same core clocks); the tuned card
does not use it.

⛔ **THIS PARAGRAPH SAID *"the DRAM runs at 16301 MHz throughout both configurations"* UNTIL
2026-09-24. FOR THE STOCK RUN THAT IS FALSE.** The stock sweep in the table logs 13477–13801 MHz:
stock memory, about 2500 MHz below the tuned run, so **the two columns are not memory-clock
matched.**
- **The direction is conservative.** The stock run has the slower memory and still the higher
  throughput, so the mismatch does not explain the plateau away.
- **But no committed pair is at once memory-matched, crossbar-instrumented and profile-verified.**
  The memory-matched comparison of 5.7.2 (tuned against memory-only, both +2500) has no crossbar
  telemetry.
- **How the error got in is not recorded.** It survived because no claim pinned either run's
  memory clock, so the auditor never rendered the number a reader could have checked. A claim now
  pins both ranges.

⚠️ **Nor is the crossbar slowing down — it is failing to speed up**, and the distinction matters for
anyone reading the ratio as a rate. Across 1402–1867 MHz the core climbs 33% while the tuned
crossbar moves 1320 → 1350 MHz, a rise of 2.3%. It is pinned, not throttled. The ratio falls because
its denominator grows. Stock over the same range takes the crossbar 1335 → 1815 MHz, tracking the
core, which is what the 0.928–0.976 band describes.

Within the tuned sweep, throughput responds to crossbar clock at **1.31** and to core clock at
**0.51**, and above the plateau a 14.4% crossbar increase goes with 14.1% more throughput, very
nearly one-to-one. **Throughput tracks the crossbar more closely than the core.** ⚠️ That is
covariance inside one sweep, not an intervention: the crossbar was never set, so the elasticities
describe how the two moved together, not what one does to the other.

**The table above shows five of the ten measured points**, chosen for spacing. The 0.725 is the
lowest of all ten and falls at 1942 MHz, which the table does not display; an earlier version of
this sentence read 0.726 off the displayed rows alone. Both extracts are committed beside the
sweeps they came from and every figure in this subsection is recomputed from them by the auditor.

Throughput follows the crossbar more closely than the core. On the tuned card, elasticity of
`membw` throughput to core clock is 0.51; to crossbar clock it is 1.31. Above the plateau a 14.4%
crossbar increase goes with 14.1% more throughput.

⛔ **THE SENTENCE THAT STOOD HERE IS RETRACTED, 2026-09-24.** It read: *"The two configurations
agree precisely where their voltages agree … and diverge from 1635 MHz, the first point at which
stock raises voltage and the tuned card does not."* **The divergence begins two grid points
earlier, while both configurations still report the same voltage:**

| core MHz | stock volts | tuned volts | stock crossbar | tuned crossbar | tuned throughput vs stock |
|---|---|---|---|---|---|
| 1402 | 0.720 | 0.720 | 1335 | 1320 | -1.1% |
| 1477 | 0.720 | 0.720 | 1402 | 1320 | -4.8% |
| 1560 | 0.720 | 0.720 | 1470 | 1342 | -5.5% |
| 1635 | 0.740 | 0.720 | 1545 | 1342 | -6.9% |

**So the reported voltage is not the state variable the chain needed.** A reconciliation exists,
and it is possible rather than measured. HWiNFO's value moves in 5 mV steps on this card and is
best read as a requested voltage code, not a measurement of the rail. Two configurations can
therefore report 0.720 V and differ in what is applied. That would rescue the physics, not the
evidence. **What the data supports is that crossbar clock and throughput track the curve
configuration, not the observed voltage.**

**How it got through: its claim pinned only the half that was true.** The auditor checked that both
configurations sat at 0.720 V and delivered ~282 GB/s at 1402 MHz, which they do, so it stayed green
on a sentence whose other half was false. The 1560 MHz row of the table above already contradicted
it, with the same voltage in both columns and a 128 MHz crossbar gap. The claim now pins the four
rows above instead.

⛔ **THE CHAIN WAS STATED AS ESTABLISHED HERE UNTIL 2026-09-24.** It read: *"flattened curve, so
pinned voltage, so pinned crossbar clock, so a non-scaling path to memory, so a bandwidth plateau
while DRAM itself is untouched at 16301 MHz."* **What the evidence supports is narrower.** On this
card, the flattened curve goes with a low reported crossbar clock and a ~300 GB/s plateau. Restoring
the low-voltage slope restored both, as predicted in advance (5.7.4). Each link is measured as an
association; none is isolated as a cause.

⚠️ **This does not require `membw` to be DRAM-saturated, and it is not.** Section 3.3.1 establishes
that no constructible kernel saturates DRAM below roughly 2000 MHz on this device, which covers
most of the band measured above — so a reader arriving from that section will reasonably ask
whether this plateau is simply that ceiling under another name. The difference between the two
configurations is not: an issue limit is a property of the part and applies to **both**
configurations equally, so it cannot by itself produce a difference between them. Stock and tuned
nearly agree at 1402 MHz and diverge from 1477 MHz on. What is measured here is that divergence at
matched core clock (not matched memory clock; see above), not an absolute bandwidth. Section 3.3.2
sets out which limiter governs which regime.

⚠️ **But the plateau itself may be that ceiling.** The tuned run's plateau begins at 280.6 GB/s,
the same ~281 GB/s that 3.3.1 could not lift. The flattened curve may not create the plateau so much
as keep the card from climbing out of a ceiling that is already there. The present data cannot tell
those two apart.

⛔ **This paragraph said the two configurations *"agree at 1402 MHz, where their voltages agree,
and diverge only from 1635 MHz"* and that the divergence was *"at matched core and memory clock"*
until 2026-09-24.** Both statements are false, as set out above. This was a second copy of the
retracted sentence.

**One relationship between the two is open and untested.** The ceiling 3.3.1 could not identify sits
at ~281 GB/s at 1395 MHz, and both configurations here deliver ~282 GB/s at 1402 MHz. 3.3.2 treats
the issue limit and the crossbar as separate limiters in separate regimes, which is the
conservative reading; whether the low-clock ceiling is *also* the crossbar has not been measured.
Logging the crossbar clock during a stock sweep at that frequency would settle it, and the HWiNFO
join built for this section is the instrument that could.

**This also unifies 5.7.1 and 5.7.2, which had read as two unrelated findings.** They are one
intervention with one mechanism. `gemm`, at ~1365 FLOP per byte, never loads the crossbar hard
enough to care, so the pinned low voltage is pure benefit - the 18 to 26% power reduction at
matched clock. `membw`, at 0.167 FLOP per byte, lives on that path, so the same pinned voltage is
pure cost. The undervolt's benefit and its harm are the same mechanism observed through two
workloads.

The practical consequence is that a profile tuned at the top of the V/F curve - the region a card
actually occupies in normal use - can be badly wrong in the mid-range, which is precisely where a
DVFS efficiency optimum is looked for. **There is no single tuned configuration that is right for
both workloads.** This is the section 5.6 result one level up: not only is the efficiency-optimal
frequency workload-dependent, so is the efficiency-optimal hardware configuration, and by a
considerably larger margin.

#### 5.7.4 A repair derived from the mechanism, and confirmed

> ⚠️ **Every measurement in this subsection and in 5.7.5 predates the capture-software finding of
> 5.4.4 and has no clean counterpart.** All four curve-fixed sweeps were taken on 2026-08-20/21
> with NVIDIA Instant Replay almost certainly running, while 5.4, 5.4.1, 5.7.1 and 5.7.6 were all
> re-measured clean on 2026-08-22. The magnitudes below are therefore expected to understate the
> repair, in the same direction and by roughly the same amount as everywhere else. **The
> qualitative findings were re-tested on 2026-08-23 and hold - see the confirmation at the end of
> this subsection.** The specific curve could not be re-measured: it was drawn by hand and never
> saved to a profile.

If the account in 5.7.3 is correct, the repair follows from it: leave the flattened region above
~925 mV intact and restore the stock voltage slope below it. A sixth sweep tested exactly that, on
the full 13-point grid with the memory overclock retained, with four outcomes stated in advance.

Voltage now rises where it had been pinned - 0.720 V at 1545 MHz through 0.840 V at 2010, against a
flat 0.720 V on the tuned card - and the crossbar-to-core ratio returns to 0.939-0.967 from 0.726.
The plateau disappears, and throughput lands on the memory-only curve: 383.2 GB/s at 1852 MHz
against the tuned profile's 294.5, **+30.1%**. The top end is unaffected: 411.8 GB/s peak against
the tuned 414.3, a 0.6% difference, with HWiNFO polling during this run and not the tuned one, so
the gap is if anything overstated.

For `membw` the repaired curve therefore dominates the fully tuned one at every point on the grid,
while remaining more efficient than either alternative across most of the range and drawing less
power at peak (79.4 W against 82.4 W at 2932 MHz).

This is the strongest evidence in this study that the mechanism is understood rather than merely
described. The intervention was derived from the diagnosis, its outcome was predicted before the
measurement, and it behaved as predicted at both ends of a range where the two configurations were
expected to differ in opposite directions.

**The predicted cost was then measured, and it is real.** Restoring stock voltage below the
flattened region should restore roughly stock power on `gemm`, giving up the 17-28%
matched-frequency saving of 5.7.1. That prediction was stated before the run and is confirmed in
5.7.5, which is why this section is titled a repair rather than an improvement.

**Confirmed on a second, independently drawn curve, 2026-08-23.** The original profile was never
saved, so it was rebuilt by hand from the design rather than restored - stock voltage slope below
~925 mV, flattened region above it intact, memory +2500 - and deliberately altered slightly. It is
a different curve: probed at a locked 3090 target it reads 2906.1 MHz on `gemm` against the
2026-08-20 runs' 2887.1 and 2898.5, and 2947.0 on `membw` against 2909.9.

**That makes it a better test than a replay would have been.** A bit-identical re-measurement
would only have shown the numbers were reproducible; an independently redrawn curve of the same
design tests whether the effect belongs to the mechanism or to one particular hand-drawn shape.

Measured on the same 10-point 1400-2100 MHz grid as the clean tuned and split-curve runs, so all
three are clean-protocol and directly comparable, with achieved clocks matched to **6.6 MHz in the
worst case and under 3 MHz at most points**:

| | vs full tuned | worst point |
|---|---|---|
| `membw` throughput | **+2.3% to +31.4%** | +31.4% at 1867 MHz |
| `membw` efficiency, 1402-1867 MHz | **+4.0% to +10.4%** | |

The plateau removal reproduces. The contaminated 2026-08-20 measurement gave +30.1% at 1852 MHz;
the clean, independently drawn curve gives **+31.4% at 1867 MHz** against a clean tuned reference.
Power behaves as 5.7.3 predicts: at matched clock the repaired curve draws **more** power than the
tuned one - 66.1 W against 52.4 W at 1867 MHz - which is consistent with the restored voltage slope
un-starving the crossbar, though it does not isolate the crossbar as the cause (5.7.3). The trade of 5.7.5 also reproduces: above 2010 MHz the tuned curve is
back ahead on efficiency, by 4.4% at 2025 and 6.0% at 2100 MHz.

**Against the split curve of 5.7.6, on `membw`, the repair wins throughput at all ten points** by
+1.6% to +7.7%. On efficiency it is closer and mixed - the repair leads at seven of ten points, the
split curve at 1867 and 1942 MHz. This does not change 5.7.6's conclusion about `gemm`, where the
split curve remains ahead and the repair gives up the compute advantage entirely.

#### 5.7.5 The repair is a trade, not a win

The repaired curve was swept on `gemm` twice, on the same 13-point grid, with HWiNFO logging
throughout. The first run is discarded at one point: under an 1852 MHz target the card ran at
2854.6 MHz and 151.6 W, an overshoot of +1002.6 MHz, which is the failure mode the sweep tool's own
comments describe - something outside `nvidia-smi` owning the V/F curve and the cap never being
applied. The tool flagged it. All numbers below are from the second run, where every point below
2782 MHz held its lock.

**The predicted loss is confirmed.** Matched-clock power returns to stock:

| locked clock | tuned vs stock | repaired vs stock |
|---|---|---|
| 1852 MHz | **-18.1%** | +1.7% |
| 2010 MHz | **-26.4%** | +0.2% |
| 2167 MHz | **-19.9%** | +1.8% |
| 2317 MHz | **-18.1%** | +1.2% |

Within 2% of stock at every point, against the tuned card's 18-26% saving. This is the same
signature the memory-only configuration produced in 5.7.1, and for the same reason: with the
sub-925 mV slope restored, the card sits at approximately stock voltage in this band.

**The loss extends well beyond those four points.** On efficiency the tuned curve beats the
repaired one across the entire mid-range, not just where power was matched:

| locked clock | tuned TFLOP/W | repaired TFLOP/W | tuned advantage |
|---|---|---|---|
| 1237 MHz | 0.1266 | 0.1284 | -1.4% |
| 1395 MHz | 0.1354 | 0.1365 | -0.8% |
| 1545 MHz | 0.1415 | 0.1375 | +2.9% |
| 1702 MHz | 0.1476 | 0.1344 | +9.8% |
| 1852 MHz | 0.1513 | 0.1242 | **+21.8%** |
| 2010 MHz | 0.1533 | 0.1152 | **+33.1%** |
| 2167 MHz | 0.1442 | 0.1123 | **+28.4%** |
| 2317 MHz | 0.1361 | 0.1114 | +22.2% |
| 2475 MHz | 0.1219 | 0.1079 | +13.0% |
| 2625 MHz | 0.1193 | 0.1085 | +9.9% |
| 2782 MHz | 0.1147 | 0.1089 | +5.4% |
| 2932 MHz | 0.1057 | 0.1078 | -1.9% |
| 3090 MHz | 0.1059 | 0.1075 | -1.4% |

The tuned curve is ahead at every point from 1545 through 2782 MHz, by up to 33.1%, and behind only
at the two lowest targets and the two highest. **The band it wins is the band that matters**: the
`gemm` efficiency optimum sits at 2010 MHz under the tuned curve, which is exactly where the gap is
widest.

At peak throughput the ranking inverts, and reporting only that would misrepresent the result. The
repaired curve reaches 16.82 TFLOP/s at 2898 MHz drawing 156.5 W, against the tuned card's 17.61 at
2948 MHz drawing 166.3 W - 4.5% less throughput for 5.9% less power, so 1.5% better efficiency at
that one point. Both beat stock, which cannot hold anything above ~2590 MHz and peaks at 15.71.

**Neither configuration dominates the other.** For `membw` the repaired curve wins at every point on
the grid (5.7.4); for `gemm` the tuned curve wins across the whole mid-range. The undervolt's
benefit and its harm are one mechanism (5.7.3), so removing the harm removes the benefit. This is
the 5.6 result one level up, and the stronger form of it: not only is the efficiency-optimal
*frequency* workload-dependent, so is the efficiency-optimal *hardware configuration*, and no
setting of this knob is right for both workloads at once.

##### The 2898 MHz ceiling is NOT a voltage shortfall - a second registered prediction, refuted

The repaired curve tops out 50 MHz below the tuned card, and this was recorded as unexplained. The
voltage telemetry gives a mundane candidate. **Both curve variants measure 0.895 V at every target
from 2625 MHz upward** - the first on its `membw` sweep, the second on this `gemm` sweep, since the
first `gemm` run was not voltage-logged. The two readings are identical to the millivolt, despite
the second curve having been redrawn specifically to raise the top point by roughly 10 mV. That
raise does not appear in the telemetry at all, on either workload.

The tuned card's top voltage was never measured. HWiNFO was not running during its `gemm` sweep, and
the two voltage-logged runs on that configuration cover only 1402-2100 MHz. The Afterburner curve
editor showed 0.925 V, which is a setting that was read off a screen, not a measurement. If it is
right, the repaired curve is running 30 mV short at the top, which is sufficient on its own to
explain a 50 MHz deficit and requires no inherent cost of the repair.

Two observations support that reading over an inherent-cost one. `membw` under the same repaired
curve lost only 0.6% at its peak, which does not fit a story where the repair caps the top of the
range. And no run of either configuration reports a hardware-slowdown, thermal or power-brake
throttle bit at any point; `SwPowerCap` appears intermittently on both and stock reports no reason
at all while still collapsing to ~2590 MHz. The ceiling is set by the curve, not by the card
protecting itself.

**That prediction was tested on 2026-08-21, and it is wrong.** The repaired curve's top point was
raised to 0.925 V and `gemm` re-run on the same grid. The ceiling did not rise: it fell, from
2898.5 MHz to 2876.6 MHz, 21.9 MHz in the wrong direction. Locking the curve flat at 925 mV
changed nothing further. HWiNFO shows 0.925 V requested delivering 0.920 V under roughly 170 W of
load, so the raise did reach the card - the 5 mV shortfall is ordinary vdroop, not a missing
voltage bin - and the card simply does not clock higher for it.

Peak throughput did improve slightly, to 16.90 TFLOP/s from 16.82, which narrows the deficit
against the tuned card's 17.61 TFLOP/s from -4.5% to -4.0%. The frequency gap is unchanged in
character: 2876.6 MHz against 2948.1 MHz, a shortfall of 71.5 MHz.

**The deficit is therefore real, reproducible, and unexplained.** Voltage is eliminated by this
sweep; thermals, power limit and throttle state were eliminated earlier. It is recorded here as an
open question rather than closed with a second guess, and it is still not used to argue anything
about the repair. What the failed prediction does establish is that the 0.895 V reading was not a
setting that failed to apply, which had been the reason for doubting the telemetry at the top of
the range.

#### 5.7.6 A split-region curve, derived from the mechanism, recovers both

Sections 5.7.4 and 5.7.5 describe a repair that removed the bandwidth penalty and gave up the
compute advantage with it, because the two share a mechanism. That framing suggests a third option
the earlier sections did not test: if the harm comes from pinned voltage *below* the flattened
region and the benefit comes from the flattened region *itself*, the two can be separated by
frequency rather than traded against each other.

**The design follows directly from 5.7.3.** Restore the stock voltage slope below ~845 mV, so the
crossbar clock scales with the core and the bandwidth-bound workload is not starved. Keep the
tuned flat shape from 850 to 920 mV, where `gemm` lives at its ceiling and the pinned low voltage
is pure benefit. Set the top point to 920 mV at 3000 MHz. Memory remains at +2500.

**On `gemm` the split curve wins, and the two configurations do not overlap.** Eight sweeps under
the clean protocol of 5.4.4, five on the tuned configuration and three on the split curve, each
with both axes of the configuration confirmed before measuring:

| configuration | peak `gemm` runs | mean | spread |
|---|---|---|---|
| original tune, n=5 | 17.98 / 17.88 / 18.02 / 17.98 / 17.93 | 17.96 TFLOP/s | 0.76% |
| **split curve, n=3** | **18.24 / 18.24 / 18.22** | **18.23 TFLOP/s** | **0.13%** |

The gap is **+1.53%**, and the lowest split-curve run exceeds the highest tuned run — 18.22 against
18.02 — so the split curve wins on every pairwise comparison the data admits. That statement does
not depend on averaging, which matters at these sample sizes. All three split runs peaked at 2977.0
MHz achieved, against the tuned card's 2946.5-2948.1 MHz.

**The split curve is also the steadier of the two**, 0.13% spread against 0.76%, a factor of 4.5 on
standard deviation. This reverses a concern carried through the earlier sections: the split curve
had been suspected of instability on the strength of a ~2.5% low outlier appearing in roughly one
`gemm` run in three. That outlier was the capture software of 5.4.4. With the contaminant removed
the configuration producing the best throughput is also the more reproducible one, and the
remaining run-to-run variation belongs to the original tune.

**On `membw` the three configurations that keep the memory overclock cannot be told apart, and
this measurement is not capable of telling them apart.** All three carry the same +2500 memory
offset and differ only in the core V/F curve. Six verified-quiet sweeps on the 10-point
1400-2100 MHz grid, achieved clocks matched to 8.0 MHz in the worst case and to 1.8 MHz at the
other forty-six, band-mean throughput in GB/s:

| configuration | sweeps | band mean per sweep | mean | within-configuration spread |
|---|---|---|---|---|
| memory-only (stock curve) | 1 | 368.8 | 368.8 | - |
| repaired curve | 2 | 367.5 / 371.1 | **369.3** | **0.98%** |
| split curve | 3 | 368.5 / 366.2 / 367.0 | **367.2** | **0.61%** |

**The configurations span 0.56%. A single configuration re-measured spans up to 0.98%, and the six
sweeps together span 1.32%.** The differences between the curves are smaller than the variation
between replicates of one curve, so no ranking among them is supported. What the six sweeps agree
on is the thing that matters: **the bandwidth cost of the flattened region is gone in both the
repair and the split curve.**

**"The ceiling" is a useful idea and not a hard limit at this precision.** The memory-only card is
the most bandwidth a core-curve change should be able to deliver, and on 2026-08-23 an
impossible-looking result - the repair exceeding it at all ten points - correctly identified a
contaminated reference. But the repaired curve's second sweep also sits **0.58%** above it, and
that is inside the noise established above rather than a signal. The reference is n=1 and carries
the same fragility as everything measured against it.

**Every per-point statistic this paragraph used to quote has been withdrawn**, including "within
0.4% at seven of ten points" and its successors. Read individually the three split-curve sweeps
give **-0.11%**, **-0.73%** and **-0.57%** against the memory-only reference, and the two repair
sweeps give **-0.39%** and **+0.58%**. Point estimates from one sweep moved by up to a full
percentage point between replicates taken within the hour on an untouched profile.

Against the fully tuned profile the plateau is removed outright - **+18.7% on average across the
band, +1.6% to +29.5%**, with the largest gains where 5.7.2 found the deepest losses. That range
is per-point and inherits the dip problem from both sides: the tuned sweep carries one of its own,
so read the band mean and not the endpoints.

**This paragraph has now been corrected three times, and the sequence is worth recording
because none of it is an arithmetic story.** The first version reported the split
curve landing within 0.4% of the ceiling at seven of ten points - the same conclusion as the table
above - but reached it by comparing a 2026-08-22 split-curve sweep against a 2026-08-20
memory-only sweep, both taken before the capture-software finding of 5.4.4 and neither verified
quiet. It was **right by accident**: two similarly contaminated runs cancelled.

The second version corrected only one side. Re-measuring the ceiling clean on 2026-08-23 raised it
by **+3.30% on average, from +1.86% to +6.25%**, in line with the +4.22% mid-band cost 5.4.4
attributes to capture software - so the section reported the split curve falling **3.18%** short
and rewrote the trade around that number. That comparison was clean against contaminated, in the
opposite direction to the first, and it was **wrong on purpose-built evidence**: the provenance
audit flagged it as a mixed comparison whose risk ran against the finding, and recorded that
-3.18% was an upper bound on the loss rather than a measurement of it.

Re-measured on 2026-08-24 with two verified-quiet sweeps, the split curve reads **+2.83%** above
its 2026-08-22 predecessor, or **+2.54%** with the one known dip in each run excluded. **The
withdrawal of the -3.18% rests on those two measurements and not on any diagnosis of the older
one**, which matters, because the diagnosis turns out to be the weaker half of the argument.

Three reasons were offered for calling that rise capture-software contamination rather than a
difference in the applied curve. Only one survives.

  1. **Magnitude - stands.** A uniform +2.77% rise, against the +3.30% the memory-only ceiling
     moved when it was re-measured, and against the **+4.22%** 5.4.4 measured for capture software
     across 1237-2010 MHz. Same sign, same order, somewhat smaller.
  2. **Frequency signature - withdrawn as never applicable.** The rise was reported as declining
     within the band, +3.06% below 1710 MHz against +2.24% above 1867. With both known dips
     removed it is flat: **+2.63%** against **+2.39%**. More importantly the test was not
     available here at all. 5.4.4's boundary is at roughly 2010 MHz and this grid runs 1402-2100,
     so nine of its ten points sit inside 5.4.4's low band, where a *uniform* offset is what that
     finding predicts. The internal split quoted earlier had no basis in 5.4.4 and was reading
     structure into noise.
  3. **An isolated deficit at one grid point - withdrawn.** The 2026-08-22 run's largest single
     deficit, +7.63% at 1792 MHz, was cited as proof of a transient on the grounds that no voltage
     curve can produce a hole at one frequency. The premise is true and the conclusion did not
     follow: the replicate taken twenty minutes after the first, encoder and decoder verified at
     0%, contains a **-6.91%** hole of its own at 1867 MHz.

What that leaves is a magnitude consistent with contamination and no independent confirmation of
it. **A slightly different applied profile is not excluded** - the 2026-08-22 curve was not saved,
and a probe reads clocks rather than voltages. The reading offered here is contamination on
magnitude alone, and it is offered as the leading explanation rather than an established one.

**Every verified-quiet `membw` sweep on this grid has a worst point, and how bad it is varies
continuously.** Across the seven of them the deepest single-point departure from the local trend
runs from **-0.36%** to **-6.91%**, with the others at -0.59%, -1.00%, -1.15%, -2.17% and -5.93%.
There is no clean separation into runs that have a dip and runs that do not.

That matters because an earlier version of this subsection drew one. It reported "two of five runs
carry a 6-7% dip", which was a threshold placed at 3% across a continuous distribution measured on
five samples. A third split-curve sweep landed at -2.17% and a second repair sweep at -1.15%, both
between the two groups, and the distinction did not survive either. **The honest statement is a
spread, not a count.**

What the three split-curve sweeps do establish is where the measurement is unreliable. Per-point
run-to-run standard deviation across them has a median of **0.46%** and a maximum of **4.19%**, and
eight of the ten points replicate to within 1%. The two that do not are 1477 and 1867 MHz. At
1867 MHz the same point reads 395.1 GB/s in one sweep and 367.1 in another taken twenty minutes
later on an untouched profile, so it is not a property of the configuration.

This retires an explanation carried since 2026-08-22, when the "wandering `membw` dip" was
attributed to the capture software of 5.4.4 on the strength of both being transient and both
moving between runs. **The variation survives the encoder guard**, so whatever produces it, that
is not what it is. Its cause is unidentified.

The practical consequence is a floor on what a single `membw` sweep resolves on this card. A worst
point of several percent is routine, and that is larger than every configuration difference this
subsection reports. Nothing here should be read from one sweep.

**The lesson is that a comparison is only as clean as its dirtier half.** Correcting one side of a
pair is not a partial fix; it can be worse than correcting neither, because it converts a symmetric
error into an asymmetric one while looking like diligence.

**The trade is between the tuned curve and the split curve, and the repair is dominated.** Three
configurations, and only two of them are on the frontier:

| | `gemm` | `membw` |
|---|---|---|
| fully tuned | best matched-frequency efficiency | loses up to 22.9% of throughput in the plateau band (memory-only ahead by up to 29.6%) |
| repaired curve | gives the compute advantage up entirely | at the bandwidth ceiling |
| **split curve** | keeps most of the compute advantage | at the bandwidth ceiling |

The repaired curve of 5.7.4 did its job, which was to identify the mechanism. As a configuration
to run, it is dominated - but the evidence for that is entirely on the `gemm` side, where eight
sweeps give ranges that do not overlap. On `membw` the two are indistinguishable, and the
subsection above says why that is a statement about the measurement rather than about the curves.
The claim is "the split curve gives up nothing measurable in bandwidth to keep its compute
advantage", not "the split curve matches the repair".

**What it does not recover.** The tuned curve still wins `gemm` efficiency across 1545-2625 MHz, by
up to 30.5% at 2010 MHz, which is where that workload's efficiency optimum sits. The split curve
buys peak throughput and bandwidth scaling; it does not buy back the matched-frequency power
advantage, and 5.7.5's conclusion that no single configuration dominates survives as a statement
about tuned versus split. What the split curve changes is the *shape* of that trade, not its
existence.

**Sample sizes.** Every `membw` figure in this subsection is one sweep per configuration. The
`gemm` results above rest on eight sweeps; these rest on four, one each. The three-way agreement
between the ceiling, the repair and the split curve is the only replication here, and a second
split-curve sweep is the cheapest thing that would strengthen it.

**It survived thirty minutes of sustained load, which is the first such test in this work.** Under
the protocol of the appendix - fifteen minutes of `gemm` then fifteen of `membw`, unlocked clocks,
96.9% of one-second samples above 50% utilisation - the configuration recorded no driver reset, no
aborted iteration and no thermal or hardware-slowdown sample. It did brush its power limit: 15 of
1765 samples reported the software power cap, which the logger classes as normal operation rather
than as throttling, and which is what a 196.1 W peak against a 200 W limit looks like at one-second
resolution. Post-soak throughput did not fall: `gemm` drifted
**-0.11%** and `membw` **+0.16%** between the first and last quarter of their post-soak iterations,
both of which are improvements or noise rather than degradation. Power averaged 140.2 W and peaked
at 196.1 W against a 200 W limit; temperature peaked at 79 C.

That drift figure is the part that matters, and it is not a crash test. GDDR7 corrects errors
silently, so a memory overclock can run for hours without a crash, an artifact or an event-log
entry while being net slower than stock. Measuring throughput continuously is the only way to see
that, and over thirty minutes there is no sign of it here.

**The original tune was then put through the same test, forty minutes later on the same card, and
also passed** - 33 iterations, zero aborted, zero driver resets, zero thermal or hardware-slowdown
samples, 14 of 1765 at the software power cap, 96.8% loaded, drift `gemm` +0.10% and `membw`
-0.28%. Two results follow from having both.

**The throughput gap reproduces under a completely different protocol.** Post-soak means over
eleven unlocked iterations each give `gemm` 18.23 TFLOP/s on the split curve against 17.98 on the
original tune, a gap of **+1.41%**. The +1.53% of the table above came from peak values in locked
thirteen-point sweeps. Two measurement designs that share no methodology - locked against unlocked,
peak-of-sweep against sustained mean, minutes apart against days apart - agree to within 0.12
percentage points. That is a stronger corroboration of the gap than either measurement alone.

**The `membw` advantage does not appear at all**, and this is the more practically important of
the two. Under sustained unlocked load the two configurations are indistinguishable on `membw`:
422.8 GB/s against 424.6, a difference of -0.44% and in the wrong direction to matter. The
difference stays small and stays negative whichever window it is read on - -0.08% across the soak
iterations, -0.33% across all seventeen - which is what indistinguishable looks like. This does
not contradict 5.7.2, it locates it. The plateau is a property of the **1402-1867 MHz band**,
where the flattened curve pins voltage and the crossbar clock stays low; a card left to boost freely sits
at 2968-2993 MHz, above the flattened region entirely, where both curves carry the same voltage.
The harm is real and reproducible when frequency is locked into that band, and absent when it is
not. Anyone reading 5.7.2's plateau loss (up to 22.9%, a 29.6% gap to memory-only) as a cost they would pay in ordinary use would be wrong.

**Both of those figures were previously assembled from three different windows.** An earlier
version gave the split curve's `gemm` mean over all sixteen iterations, its `membw` mean over the
five soak iterations alone, and the original tune's means over its eleven post-soak iterations,
beneath prose declaring all of them post-soak. Every number was a real measurement of something and
the pairing was still wrong. Read on the window the prose declares, the gap is +1.41% rather than
+1.45% and the `membw` difference -0.44% rather than -0.35%, which changes no conclusion here. It
is recorded because the defect was not the arithmetic: it was an aggregate whose window was
implicit. The reader that supplies these numbers to the audit now requires the window to be named
at the call site, so the same mistake cannot be made silently again.

**Neither run distinguishes the two configurations on steadiness.** All four drift figures fall
between -0.28% and +0.16%, in both directions, which is noise. The 4.5x reproducibility advantage
reported above is a spread across *separate sweeps*, not drift *within* a run, and these are
different quantities - so this does not overturn it. What it does say is that whatever produces
the original tune's wider run-to-run spread is not visible as degradation inside a single
half-hour of sustained load, which narrows where to look for it.

**Limits.** n=1 chip, one curve shape, and **one thirty-minute run**. The correct reading is "no
failure observed in thirty minutes", not "stable": undervolt failures routinely take hours to
appear, and a single session says nothing about thermal cycling, cold boots, or the driver updates
this configuration will meet in normal use. The degradation threshold the run was judged against is
uncalibrated - it was set at 2% before anybody knew what healthy drift looks like, and this run
suggests that is loose by an order of magnitude. The sub-845 mV region was also reshaped by hand
rather than by any principled optimisation. How much of the stock slope can be given back before
the crossbar starves is unmapped; only the two endpoints have been measured.

#### 5.7.7 Caveats

The three configurations were **not** measured contemporaneously: stock at 14:33 on 2026-08-19, full
tuned at 20:42 the same day, memory-only at 18:13 the next - switching configurations required a
manual Afterburner change when these runs were collected.

⛔ **That constraint expired on 2026-09-08 and this paragraph asserted it as permanent.** Afterburner
applies a stored profile from the command line, so configuration is now a scriptable variable; §5.8
is the first comparison collected that way and §5.5.8's ABBA design depends on it. The caveat below
still describes *these* runs correctly - it is a fact about when they were taken, not about what the
method can do. Idle temperature was 40-42 C at the start of
each, the only cross-run control available. Effect sizes up to 29.6% are far outside plausible
day-to-day drift so the direction is safe, but the precise percentages are softer than they look.

**How much softer is now measured rather than guessed.** Section 5.4.5 puts power reproducing at
2.07% and efficiency at 2.08% across three replicates of one unchanged configuration, and
limitation 8 puts cross-session drift at 1.47% on throughput. Since the three configurations here
were measured on different days, **any percentage in this subsection smaller than roughly 3% should
be read as indistinguishable from zero.** The large effects are untouched by that bar; the small
ones were never load-bearing and are now explicitly not.
n = 1 chip, one profile. Two `gemm` points outside the comparison band (2475 and 2625 MHz) show
memory-only drawing 5.8% and 6.6% more power than stock with only 1.2 and 2.1 C to account for it;
this is unexplained and recorded rather than trimmed.

---

---

### 5.8 Stock against tuned, measured in one session

`[n = 1 chip, 12 workloads, 36 sweeps. Single-chip result; no cross-unit claim.]`

Every stock-versus-tuned figure elsewhere in this work is assembled from sweeps taken on **different
days**, because stock could not be applied without touching the machine: all five Afterburner
profile slots carried offsets, so there was no scriptable stock configuration. On 2026-09-09 one
slot was found to hold the factory curve unmodified — every per-point offset zero, memory offset
zero, the default power limit — which made the comparison collectable in a single session for the
first time.

**Three twelve-workload suites, 36 sweeps, 10:38 to 13:39, zero failures**, with the stock leg
**centred between two tuned legs** so that linear session drift cancels on the tuned side:

| leg | configuration | enforced power limit |
|---|---|---|
| 1 | full tune | 200 W |
| 2 | **stock** | **180 W, the factory default** |
| 3 | full tune | 200 W |

| | mean efficiency gain |
|---|---|
| stock | **56.99%** |
| full tune, mean of both legs | **34.16%** |
| **gap** | **22.83 points** |

**Stock has more headroom than the tuned card in 12 of 12 workloads**, with no exceptions — one of
the few genuinely unanimous results in this work.

⚠️ **The margin is not uniform and the unanimity should not be read as uniformity.** Per-workload
gaps span **0.49 to 41.11 points**. The narrowest is well inside the ~0.76% within-session spread of
§5.4.5, so for that workload the direction is what survives, not the magnitude.

**This is the expected direction, not a surprise.** A tuned card already runs closer to its
efficiency optimum at stock settings, so less remains to recover by lowering its clock. The value of
the measurement is the size and the cleanliness, not the sign.

#### 5.8.1 What the bracket says about every cross-session comparison in this work

The same gap assembled the old way — stock from the five suite replicates of §5.4.5, tuned from the
ABBA run of §5.5.8, different days — gives **21.60 points** against this run's **22.83**.

🔑 **The cross-session construction was low by 1.23 points, not wrong.** That matters more than the
new number does: it means the day-against-day comparisons throughout this work are **less precise
than they appear but not invalidated**, and it puts a measured bound on how much less precise.

#### 5.8.2 The bracket audited itself, and retracted a figure from §5.5.8

A bracket measures drift as a by-product: the two tuned legs are the same configuration, so
whatever separates them is session drift rather than effect.

| same configuration, measured twice | drift |
|---|---|
| §5.5.8's ABBA run, legs `a1` → `a2`, ~2.5 h | **+0.04 points** |
| this run, legs `p4t1` → `p4t2`, ~2 h | **−1.25 points** |

⛔ **The ABBA run's +0.04 was quoted as evidence that the tuned configuration reproduces to within
a rounding error. It does not.** Two brackets of comparable length on the same card and the same
profile disagree by a factor of thirty, so **±1.3 points is the honest figure for same-configuration
reproducibility over a couple of hours**, and the 0.04 was a single fortunate sample. Every
same-configuration agreement quoted in this work should be read against ±1.3 rather than against the
best case observed.

⚠️ **Two brackets is not a distribution either.** What is established is that same-configuration
drift can reach 1.25 points, not what it typically is.

## 6. Limitations

1. **Voltage is measured, but thinly, and not through the vendor API.** NVML does not expose it:
   `nvidia-smi` has no voltage field, and an exhaustive scan of NVML field IDs 1-259 via
   `nvmlDeviceGetFieldValues` returns 44 readable fields, none of them a core voltage at any scale.
   That scan also confirms the fields it *does* return are correct - IDs 185/186 give instantaneous
   and average power in milliwatts, and 187-192 give the power limits (150/180/200 W), matching both
   `nvidia-smi` and third-party tools. Earlier drafts asserted "no documented API exposes it" without
   testing; this is verified for NVML specifically.

   HWiNFO64 does read core voltage and the crossbar clock on this device, and an earlier version of
   this limitation named joining that log to a sweep as the highest-value outstanding experiment in
   the study. **That join was built and run, and the mechanism in 5.7.3 is a measurement rather
   than an inference.** The joining tool is `tools/frequency-sweep/join_hwinfo_voltage.py`; it bins
   samples by the core clock they were taken at rather than by timestamp, because the sweep CSV
   records durations per point and not absolute times.

   What remains limited is the coverage and the conditions, and those bound the voltage claims:

   - **The voltage-logged runs cover 1402-2100 MHz.** The tuned card's voltage at the top of its
     range was never measured, so statements about the top point rest on the Afterburner editor
     rather than on telemetry.
   - **HWiNFO polls throughout**, which is the class of contention this study has already been
     burned by, so throughput from a voltage-logged run is not quoted as a clean measurement.
   - **Idle samples must be excluded or the result inverts.** HWiNFO samples through the settle
     gaps and an idle card sits at boost voltage, so the join discards samples below 30 W. That
     threshold is a judgment call; it is the parameter this result is most sensitive to, and it is
     covered by tests for exactly that reason.
   - **One source log no longer exists.** HWiNFO reuses a single log filename, and the log for the
     `curvefixed-membw` run was overwritten by a later capture, so its committed distilled extract
     is now the only record and cannot be regenerated.
   - **N = 1 chip**, one set of curves.
2. **Small, heterogeneous sample.** Access is limited to roughly one machine every 2–3 weeks, mostly
   different models rather than repeats, which bounds any claim about chip-to-chip variation.
3. **Single vendor, recent architecture.** NVIDIA only; no AMD or Intel measurements.
4. **Power is a device-side estimate**, boxcar-averaged, not an external measurement [5].
5. **Stability windows are short.** Ten minutes is not proof of stability.
6. **Reference-dataset results are single-device.** The 44.4% figure is one V100; it is not a
   population estimate.
7. **The memory-bound workload is not memory-bound over most of the swept range.** `membw` is
   issue-limited below roughly 2000 MHz on this device, and no constructible kernel saturates DRAM
   there (3.3.1). Consumer results that depend on a workload being bandwidth-limited hold only near
   the top of the range.

   **This does not undercut 5.7, and the distinction is worth stating because the two sections
   otherwise look as though they collide.** That mechanism points to the crossbar clock, not DRAM,
   as the limiter, as an association rather than an isolated cause. It rests on a divergence
   between two configurations at matched core clock rather than on an absolute bandwidth. ⚠️ Not at
   matched memory clock: the stock telemetry run used stock memory, which is conservative, and this
   item said *"matched core and memory clock"* until 2026-09-24 (5.7.3). A ceiling
   shared by both configurations cancels in that comparison. 3.3.2 assigns the limiters by regime;
   read it before concluding that either section contradicts the other.
8. **Same-configuration measurements drift across sessions by more than the effects several
   comparisons here report.** Measured directly on 2026-08-29: an unchanged memory-overclocked
   configuration read **1.47%** faster on `gemm` than the same configuration seven days earlier.
   Within-session run-to-run spread on the same workload is ~0.76% **on throughput**, so a
   cross-day comparison carries roughly twice the noise of a same-day one. ⚠️ **That figure does
   not cover power or anything derived from it.** Across three stock replicates §5.4.5 measures
   throughput reproducing at 0.87% but power at 2.07%, efficiency at 2.08%, and a reported
   efficiency gain at 4.40 percentage points. Any uncertainty quoted on an efficiency or
   gain figure must come from those, not from 0.76%. This is not hypothetical - a same-day
   stock-versus-memory-overclock comparison gives -0.05% where the cross-day version of the same
   comparison gave -1.50%, and the difference is the drift. Any figure in this paper drawn from
   runs on different days should be read against that bar, and sign consistency across grid points
   does not rule it out, because a constant session offset produces exactly that signature.
9. **Tuning configurations were not measured contemporaneously.** The stock, fully tuned and
   memory-only sweeps of 5.7 are separated by hours to a day, because switching between them
   requires a manual change that cannot be scripted (5.7.7).
10. **Every measurement is single-GPU and fixed-work, so 5.6.3's fleet arithmetic is an upper bound
   on the benefit.** The workloads here are microbenchmarks run to completion on one device, and the
   deployment model in 5.6.3 scales them as `output = units x per-unit throughput`. Real multi-GPU
   work does not compose that way. Collective operations make every participant wait for the
   slowest, so uniformly downclocking a fleet lengthens each synchronisation rather than dividing
   cleanly; stragglers, interconnect latency and tail effects all worsen as per-unit throughput
   falls, and none of them appear in a single-device fixed-work benchmark. **Nothing in this study
   measures the multi-GPU case**, and the linear scaling assumed in 5.6.3 is therefore optimistic in
   an unquantified direction. A reader sizing a real cluster should treat the unit counts there as a
   floor on how much extra hardware would be required.

    The same caveat limits the workloads themselves. `gemm` at ~1365 FLOP/byte and `membw` at 0.167
    bracket a range, but a training step is a sequence of phases with different intensities, and 5.7
    shows the same voltage curve can help one phase and cost another up to 22.9%. A per-phase optimum
    is not measured here.

---

## 7. Conclusion

The question this work set out to answer is narrow and checkable: how much efficiency do
conservative stock defaults leave on the table on current consumer GPUs, what drives it, and is
per-unit measurement worth its cost. Three things can be said with the data collected.

**The gap is real and large, and the released consumer DATASETS could not have found it.** ⚠️ The
distinction between the data and the literature is the whole point and is easy to blur: the
*finding* that a consumer GPU's optimum lies below its default clock is published [19], [15], [20].
The *released* modern consumer collections sweep too narrow a window to contain it — each brackets
its own default clock and stops at 89% of it (§2.7) — so their small measured gaps are bounded by
range rather than by silicon. **A reader cannot re-analyse the region where the optimum sits on any
consumer architecture after Maxwell, because no released sweep descends into it.** That observation
is reproducible in a single script against files this work already reads, it sharpens the
justification for this project's own sweep design, and it is the contribution most likely to be
useful to someone else.

⚠️ **This paragraph twice claimed more than that and was twice wrong, in the same direction.** It
said the released consumer data sweeps only at or above stock, on the strength of a normalised
`*-features.csv` and then of a specs-database reference clock. Neither is what the datasets say.
The surviving claim is about the WIDTH of the released window, which is the least this section
needs and the only part that held up.

**Per-unit prediction is worth its cost only under a constraint, and the fitting is not the part
that earns it.** Unconstrained, a probe-based model ties a single fixed frequency, and that null is
reported as the result rather than tuned away (§5.2). Impose a performance floor and the ranking
inverts, because a fixed policy must satisfy the most frequency-sensitive workload it might meet
(§5.6.1, §5.6.2). The practical recommendation that survives is *measure a few points, interpolate
between them, and attach a performance guarantee* — not *fit a model*. That recommendation carries
a condition: it depends on the performance curve being concave, and on a convex curve the safety
argument reverses.

**A mechanism was measured as an association, and a repair predicted from it worked.** The
bandwidth plateau under a flattened voltage-frequency curve is traced link by link (pinned curve
voltage, pinned crossbar clock, bandwidth that stops scaling) with a stock control run. A repair
derived from the diagnosis behaved as predicted, including in its predicted cost (§5.7). ⚠️ No link
is isolated as a cause: the crossbar was never set independently, and the stock control is not
memory-clock matched (§5.7.3). This paragraph said *"A mechanism was measured, not inferred"* until
2026-09-24. This is the part of the work
that depended on physical access to hardware rather than on a download.

### What this work refuted, including its own predictions

Three predictions made inside this project were tested and failed, and each is reported where it
was made rather than removed:

1. **That a ~30 mV shortfall explained the compute ceiling of the repaired curve.** Raising the
   top of the curve *lowered* the ceiling. The deficit reproduces and is still unexplained
   (§5.7.5).
2. **That the vendor OC BIOS's power premium was voltage.** Registered in advance as a specific
   number, 0.738 V, and refuted: both BIOS positions hold the same floor, and the difference is an
   additive offset in the intercept rather than a ratio in the frequency-scaling term (§5.5.1.1).
3. **That per-workload prediction would beat a fixed frequency.** It ties (§5.2).

**And four claims of novelty were retracted, all to searching rather than to a reviewer.** They
are listed because the alternative is that a reader finds them:

4. **That the load-floor relationship was this work's own.** It is the published **ridge point**
   [18], stated in the same terms in 2022. Retracted 2026-09-12, four days after it had been
   promoted to this project's headline result and built upon.
5. **That locating an efficiency optimum on consumer silicon was unaddressed.** It is not [19],
   [15], [20]. Four successive narrowings of this claim were attempted and all four failed.
6. **That per-card floor voltage was a new observation.** Per-chip Vmin variation was measured
   across five physical GTX 780s in 2015 [8] and six Radeon boards in 2025 [14]. What survives is
   its quantified consequence for prediction, not the fact itself.
7. **That the crossbar's clock domain was this work's discovery.** It was documented on Blackwell
   weeks earlier, by one author on one card [11], [12]. The measured association remains, as an
   association (§5.7.3); the domain does not. ⛔ This item said *"The causal chain remains"* until
   2026-09-24.
8. **That changing the voltage–frequency relationship and re-locating the optimum had not been
   done.** Mendes, Tomás and Roma (SBAC-PAD 2020) did it on an AMD Vega 10 with voltage written
   directly, and the optimum moved from 1270 to 1530, 1440 and 1530 MHz for three of four CNN
   models. It was missed because a lead on that paper was closed after reading the same group's
   2022 paper instead. What survives is narrower: a region-targeted edit of a vendor curve whose
   voltage cannot be written, a negative control, and an optimum predicted from the floor voltage.

⚠️ **The common cause is worth more than the individual retractions: every check this project ran
was internal.** Registered predictions, a negative control, replication across chips and hundreds
of mechanical assertions all ask *is this true of our data*. None asks *is this already known*.

A further correction was methodological rather than physical: an early attribution of measured
contention to one piece of software was wrong, and the discriminating experiment identified a
different cause (§5.4.4). The pattern across all four is that the errors were invisible on
inspection and only appeared under measurement, which is the argument for the mechanical claim
auditing this paper is subject to.

### What this work does not claim

It does not outperform vendor boost algorithms, which already incorporate per-chip factory binning.
It does not discover voltage guardband or inter-chip variation; both are established [8, 9]. It
does not control voltage — voltage is observed telemetry here, never an independent variable. And
it is not a population estimate of anything: two chips, one unit each, and every tuning result from
a single card. The chip-to-chip variation a reader will ask about is published at roughly 11% and
remains unmeasured here, because measuring it needs repeat units of one model that this project
does not control.

### Future work

**The question this section previously named as future work has been answered, and the answer was
no.** It asked whether per-workload optima transfer across architectures; §5.5.4 measures a rank
correlation of −0.273 between the two chips, against a within-card reproducibility of +0.924. Both
halves of the plan are now done — the suite carries twelve workloads (§5.4.5) and has been run at
stock on both chips.

What that opens rather than closes is the population question. Two architectures cannot say whether
orderings *generally* fail to transfer or whether these two happen to disagree, and separating those
needs more chips rather than more workloads. A second Ampere die would be the sharpest next
measurement, because it distinguishes "this is an architecture effect" from "this is a chip
effect" — a distinction one card per architecture structurally cannot make.

One measurement item is outstanding. The stability protocol has been applied to three of the
configurations reported here; the others carry no failure evidence in either direction, and "no
failure observed in thirty minutes" is the strongest statement any of them supports.

**The 34 W offset of §5.5.1.1 is no longer on this list.** Cooling was its last live candidate and
§5.5.1.1 excludes it: the fan RPM this paragraph once said had not been captured was in the raw
HWiNFO logs all along, dropped when they were distilled rather than when they were recorded, and
the offset holds at +32.7 W and +36.3 W with both fans reading exactly zero. No mechanism is
claimed for it, which is a different state from an open measurement.

---

## References

**Verified** — primary source opened, quoted figures confirmed against it:

- [18] **Schoonhoven, Veenboer, van Werkhoven, Batenburg.** *Going green: optimizing GPUs for
  energy efficiency through model-steered auto-tuning.* arXiv:2211.07260, 2022 (Kernel Tuner).
  ⛔ **This entry read "van Werkhoven, Willemsen, Schoonhoven, Nieuwpoort" for one day.** Two of
  those names do not appear on the paper and the author order was wrong; Schoonhoven is first
  author. Verified against arXiv metadata 2026-09-13. The short form is **Schoonhoven et al.**, and
  this project called it "Schoonhoven et al." throughout for the same reason the ICPP paper was
  "Guerreiro" for months - a name repeated from a summary and never checked against the source.
  *Read in full 2026-09-12.* 🛑 **The source of this project's largest retraction.** Defines the
  **ridge point** — the frequency at which core voltage stops being constant and begins rising —
  and states the consequence this project had believed was its own: *"Reducing the clock frequency
  beyond the ridge point does not make the GPU more energy efficient, as performance drops with f
  while v is constant below the ridge point."* Measured on a Tesla A100 (ridge 1025 MHz, 70% of
  peak) and an RTX A4000 (1290 MHz, 72%), with predicted energy-optimal clocks of 985 and 1298 MHz.
  **Datacenter and workstation parts only.**
- [19] **Mei, Wang, Chu.** *A Survey and Measurement Study of GPU DVFS on Energy Conservation.*
  Digital Communications and Networks, 2017. arXiv:1610.01784. *Read in full 2026-09-13.*
  ⛔ **Establishes a board-level, below-default, per-kernel efficiency optimum on consumer GeForce
  silicon**, which is why no claim to having done that first appears in this paper. ASUS Strix
  GTX 980, core swept 480–1080 MHz against a 950 MHz default, voltage held fixed at the 0.987 V
  lower bound, **GPU-level energy from the on-chip sensors**: 30 of 42 kernels take their minimum
  energy below the default clock, half between 680 and 880 MHz. Mean R̂ 5.24%, mean Rmax 10.87%.
  ⚠️ **R̂ is energy against the DEFAULT clock and is not comparable to this paper's efficiency gains
  against the sustained maximum.** ⚠️ ScienceDirect returns 403; the arXiv version is open.
- [20] **Mei, Yung, Zhao, Chu.** *A Measurement Study of GPU DVFS on Energy Conservation.*
  HotPower '13. *Read in full 2026-09-13* (scanned, no text layer; direct fetch returns 403).
  One GTX 560 Ti, 37 benchmarks, fcore 480–880 MHz at fixed 1.049 V and 0.849 V, using NVIDIA
  Inspector and **MSI Afterburner 2.3.0** — the same instrument lineage this work uses. Reports
  18.91% energy for 3.45% performance at 0.849 V / 880 MHz. ⚠️ **Whole-system energy at the wall
  against an 85 W idle floor of which 29 W is the card**, which is why only 5 of its 37 applications
  benefit from lower core frequency: stretched runtime bills the system's fixed power. **Do not cite
  it against low-frequency headroom measured at board level.** 🔑 Also contains the closest prior
  observation to this work's causal result — *"for Kmeans, scaling down f_core can save energy when
  V_core = 1.049 V, but this situation does not hold anymore when V_core = 0.849 V"* — raised as an
  aside in one application of 37 and explicitly left as an open problem.
- [21] **Wang, Chu.** *GPGPU Performance Estimation with Core and Memory Frequency Scaling.*
  ICPADS 2018, pp. 417–424. Artifact: `github.com/HKBU-HPML/NV-DVFS-Benchmark` (branch `master`).
  🔑 **The origin of the GTX 980, Titan X and GTX 1080 Ti CSVs**, which earlier drafts attributed
  only to an unnamed "HKBU-HPML [7]". ⚠️ **It releases below-stock consumer sweeps**: two GTX 980
  files at 500–1000 and 700–1500 MHz, and two more at 400–1000 MHz, against that card's 1127 MHz
  base clock. A draft of this entry denied that on the strength of a companion `*-features.csv`
  whose frequency columns are normalised multipliers rather than absolute megahertz. ⚠️ **It is
  NOT the source of the RTX 2070 Super file** — see [22]; that attribution was also wrong for a
  day. The GTX 1080 Ti file is byte-identical in both repositories (verified by checksum), so
  either citation is defensible for that one, and this work fetches it from [22]'s.
- [22] **Wang, Mei, Liu, Leung, Li, Chu.** *Energy-aware Non-Preemptive Task Scheduling with
  Deadline Constraint in DVFS-enabled Heterogeneous Clusters.* IEEE TPDS. arXiv:2104.00486.
  Artifact: `github.com/HKBU-HPML/GPU-DVFS-Job-Schedule` (branch `master`) = [7], which is where
  `scripts/Get-Dataset.ps1` actually fetches both consumer files from. 🔑 **Its README states the
  default operating clocks of the cards used — GTX 1080 Ti 1800 MHz core / 5000 MHz memory, RTX
  2070 Super 1880 / 6300 — and those are the numbers that corrected §2.7.** Scored against them
  rather than against a specs-database reference clock, neither sweep is an overclocking sweep:
  each brackets its own default, two of five core points below it. Every declared value lands
  exactly on a swept grid point in both axes. ⛔ **It is also the source of §2.7's central
  observation, which this work briefly claimed as its own** - §5.1.1 states the 0.89 lower bound,
  §5.2 attributes their 4.3% measured saving on the GTX 1080 Ti partly to "the scaling intervals
  ... are narrow", and simulates a widened interval reaching 36.4%. *Read in full 2026-09-13; every
  quotation verified against the PDF.* ⚠️ Their energy is **system-scope at the wall** against a
  37 W idle floor, and the wide case is simulated with static power shrunk - not comparable to this
  work's board-power figures. ⚠️ The paper's own reported experiments are the GTX 1080 Ti; the
  RTX 2070 Super appears in the repository's configuration table, not in the arXiv text.

- [3] Maliakel, Ilager, Brandic. *Characterizing LLM Inference Energy-Performance Tradeoffs across
  Workloads and GPU Scaling.* arXiv:2501.08219.
- [5] Yang et al. *Accurate and Convenient Energy Measurements for GPUs: A Detailed Study of NVIDIA
  GPU's Built-in Power Sensor.* 2024. Code: `github.com/JimZeyuYang/GPU_Power_Benchmark`
- [6] Zhang, Wang, Lin, Xu, Wang. *Improving GPU Energy Efficiency through an
  Application-transparent Frequency Scaling Policy with Performance Assurance.* EuroSys '24,
  pp. 769–785. ACM. doi:10.1145/3627703.3629584.
  Dataset: `github.com/zyjopensource/GPU-DVFS-Dataset` — **no license stated**; not redistributed
  here, fetched locally by `scripts/Get-Dataset.ps1`. Their reported result is **26.7% mean V100
  efficiency gain for 5.8% performance loss**, which is performance-constrained and therefore not
  the same quantity as this project's unconstrained 44.4% (§5.1). The two must not be compared
  directly as if one beats the other.
- [7] HKBU-HPML/GPU-DVFS-Job-Schedule. `github.com/HKBU-HPML/GPU-DVFS-Job-Schedule` — the
  artifact of [22]. ⛔ **This entry read "not a data source for §2.7's table" until 2026-09-13.**
  It is the source this project downloads BOTH consumer files from, and its README carries the
  declared default clocks that overturned that table's central claim.
  The GTX 1080 Ti and RTX 2070 Super rows there come from `HKBU-HPML/NV-DVFS-Benchmark` instead,
  credited to Wang & Chu, ICPADS 2018, as [21] — which also releases below-stock GTX 980 sweeps.
- [8] Leng, Buyuktosunoglu, Bertran, Bose, Janapa Reddi. *Safe Limits on Voltage Reduction
  Efficiency in GPUs: a Direct Measurement Approach.* MICRO-48, December 2015. IBM T.J. Watson
  Research Center / University of Texas at Austin.
  PDF: `cs.sjtu.edu.cn/~leng-jw/resources/Files/leng15micro-gpuvminexp.pdf`
  *Figures confirmed by reading the paper: ~20% guardband across two generations; up to 25% energy
  savings on one card; 9–18% guardband on GTX 680 specifically; geomean savings 21% (GTX 680) and
  15.8% (GTX 480); ranges 14–25% and 8–22%.*
- [9] Sinha, Guliani, Jain, Tran, Sinclair, Venkataraman. *Not All GPUs Are Created Equal:
  Characterizing Variability in Large-Scale, Accelerator-Rich Systems.* SC '22. arXiv:2208.11035.
  *Figures confirmed: 8% average (max 22%) performance variation within identical SKUs; outliers up
  to 1.5× slower than median; >18,800 hours across five clusters.*

- [10] **Afzal et al.** *Modeling and Chasing the Energy-Efficiency Sweet Spots in Modern GPUs.*
  arXiv:2607.00819. *Abstract and HTML version read; the PDF was not retrieved.* ⚠️ **This entry
  carried NO author name until 2026-09-13**, while `docs/RELATED-WORK.md` had recorded one the whole
  time - the same shape as the citation error that left an ICPP paper misattributed for months.
  Full-range core-clock sweep below nominal on A40/A100/H100/H200 with an open dataset — the closest
  published analogue to this study's method, and **datacenter-only**, which is why it sharpens the
  consumer-availability gap of §2.7 rather than closing it. Its abstract states that efficiency
  regimes are architecture-dependent, which corroborates §5.5.4's framing.
- [11] *XBAR in NVIDIA Blackwell GPUs: A Physical Clock Domain Ignored by Public Tooling.*
  `loong0x00.com/notes/blackwell-xbar-physical-clock-domain/`. GB202. Establishes XBARCLK's own PMU
  object, clock source, 127-point V/F table and control path, and reports a 0.8999:1 GPC-to-XBAR
  topology constraint. **Cited as the source that establishes the domain, which this work therefore
  does not claim.** Reports no bandwidth figures and no swept ratio.
- [12] Runtime XBAR clock and per-domain MSVDD control on NVIDIA Blackwell. LACT issue #1147,
  `github.com/ilya-zlobintsev/LACT/issues/1147`, August 2026, RTX 5090. Applies +60 to +450 MHz XBAR
  offsets for up to +10.6% FPS. ⚠️ **A throughput-limit figure appears in that thread with no
  benchmark trace behind it and is deliberately not cited here or used as corroboration.**
- [13] *Dynamically controlling interconnect frequency in a processor.* WO2013137862A1. Prior art for
  the general concept that a slow interconnect stalls a faster core — **CPU/uncore, a deliberate
  closed-loop controller, no voltage-pinning and no GPU crossbar.** Cited to pre-empt the objection,
  not as a source for anything measured here.

*⚠️ Provenance note for [10]–[13]: located and read by delegated search agents on 2026-09-06, not
yet re-opened by the author. [11] and [13] were read in full and [10]'s abstract verified verbatim;
treat the summaries above as second-hand until re-read. Two further leads — arXiv:2001.07104 and
ACM 10.1145/3605573.3605600 — surfaced in the same sweep with figures that could NOT be confirmed
from source, and are deliberately omitted rather than cited as either support or threat.*

- [14] Trakosa, Chatzopoulos, Papadimitriou, Gizopoulos. *NAVIgator: Exploring the Voltage Limits of
  AMD NAVI GPUs for Energy Efficient Computing.* IOLTS 2025, University of Athens.
  `ceid.upatras.gr/webpages/faculty/gpapad/assets/papers/iolts2025_trakosa.pdf`
  *Read in full 2026-09-07. Confirmed from the text: RX 7600 XT / 7700 XT / 7800 XT; voltage reduced
  at FIXED frequency; up to −300 mV; 14% average power saving; chip-to-chip variation across the
  three models; datacenter extrapolation of 42 W per GPU.*
- [15] Tang, Wang, Wang, Chu. *The Impact of GPU DVFS on the Energy and Performance of Deep
  Learning.* e-Energy '19. arXiv:1905.11012. doi:10.1145/3307772.3328315.
  *Read in full 2026-09-07. Confirmed: P100, V100 and GTX 2080 Ti; energy curves show a valley with
  a sweet spot; 8.7–23.1% training and 19.6–26.4% inference energy conservation against DEFAULT
  clock; and the sentence quoted in §2.7 in which the consumer card is scaled UP from 1350 MHz while
  the datacenter defaults are already the ceiling.*
- [16] Zamani, Tripathy, Chen (and Bhuyan). *SAOU: Safe Adaptive Overclocking and Undervolting for
  Energy-Efficient GPU Computing.* ISLPED 2020. doi:10.1145/3370748.3406553.
  `cs.ucr.edu/~hzama001/publications/SAOU.pdf`
  *Read in full 2026-09-07. Confirmed: GTX 980, cuBLAS matrix multiply at 10K, MSI Afterburner used
  for the offsets, checkpoint-recovery for faults, up to 22% energy reduction.*

**⚠️ Located but not yet read in full** — open the primary source before submission:

- [17] ✅ **RESOLVED — see [19].** This entry read "NOT READ — ScienceDirect returned HTTP 403" and
  warned that the survey was "very likely to contain a swept-range comparison bearing directly on
  §2.7". It did, and worse: it contains a below-default consumer optimum that retired a claim this
  paper was still making. **It was on arXiv the whole time.** 🔑 Kept as a record that a paywall is
  not a dead end, and that the entry correctly identified its own risk for weeks before anyone acted
  on it.
- [1] **Fan, Cosenza, Juurlink.** *Predictable GPUs Frequency Scaling for Energy and Performance.*
  ICPP 2019. DOI 10.1145/3337821.3337833. Open-access postprint at TU Berlin DepositOnce.
  *Read in full 2026-09-13.* ⛔ **This entry read "Guerreiro et al." until then — a misattribution,
  under a note instructing the reader to open it, which is presumably part of why nobody did.**
  Confirmed from the text: GTX Titan X (Maxwell, consumer) and Tesla P100; 85 core frequencies
  135–1392 MHz × 4 memory frequencies; NVML only, **no voltage control**; ML over static code
  features trained on 106 micro-benchmarks, predicting a Pareto set without executing the kernel.
  🔑 **It is closest not to §5.5's causal result but to §5.2's NULL**, and it reports success where
  this project reports a loss — from richer inputs (code features, a 2D core×memory space,
  purpose-built training). Say so wherever the null appears.
  Also corroborates §5.4.2's class of hazard: NVML reports configurations as supported that do not
  actually take effect, and requests above 1202 MHz on Titan X silently return 1202.
- [2] *Accurate Energy and Performance Prediction for Frequency-Scaled GPU Kernels.* MDPI
  Computation 8(2):37.
- [4] Measurement studies of GPU DVFS energy conservation (multiple; consolidate to one citation).
- Rodinia benchmark suite. IISWC 2009.

### Corrections made during citation verification

Recorded because both errors would have reached a submitted draft:

- **"~140 MHz / ~11% frequency variation"** attributed to [9] was **wrong** — a garbled second-hand
  summary. The paper reports 8% average and 22% maximum *performance* variation, and 1.5× outliers.
- **"9–18% guardband"** as the headline figure for [8] was **wrong** — that is the GTX 680-specific
  range. The headline is ~20% across two architectural generations. This error came from a local
  model's extraction of the PDF and was caught by checking the raw text.
