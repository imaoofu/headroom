# Headroom — paper draft

> **Status: complete in structure, still a draft in places.** Results rest on **332 committed
> sweeps across two consumer GPUs**, including core-voltage and crossbar telemetry.
> **231 numbers are pinned by `analysis/audit_claims.py`**, which recomputes each from the source
> CSVs at audit time and fails if the text and the data disagree; it runs on every push. That count
> is itself pinned, so adding a claim without updating this line fails the audit. It counts the
> tool's whole coverage — the paper, two data READMEs, and `CLAUDE.md` — not the paper's share
> alone. No `[PENDING]` placeholders remain, but **20 numbered sections carry no claims at all** —
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
period measured in years. The margin this produces was quantified on GPUs released in 2010 and
2012; whether comparable margin remains on current consumer parts, and where it sits, is not
established. It also cannot be answered from published data, for a reason that is itself a
finding: the public consumer DVFS data we could locate — two cards, both from a single released
collection [7] rather than from independent groups — sweeps core frequency at and above the card's
rated boost clock, 101–126% and 95–118% of it, while the efficiency optimum lies *below* stock.
Their correspondingly small measured gaps invite the conclusion that consumer GPUs have little
headroom, when what they show is a truncated measurement range.

This work contributes an open dataset of consumer-GPU frequency, power and performance
measurements swept across 40–100% of maximum core clock, released with its collection tooling and
a locked protocol: 67 sweeps on an RTX 5060 Ti (Blackwell) and an RTX 3070 Ti (Ampere).

On a public V100 reference set, running each of 33 workloads at its own efficiency optimum rather
than at stock recovers 44.4% efficiency on average. Per-workload *prediction*, however, does not
beat a single fixed frequency — 0.883% mean regret against 0.837%, leave-one-workload-out. That
null inverts under a performance constraint: at a 95% floor, probe-based selection reaches 25.4%
mean efficiency gain where the best fixed frequency reaches 4.9%. The fitting earns none of it,
since straight-line interpolation between four probes beats every fitted variant, and the fitted
model only appears to win by violating the floor it was given.

On consumer hardware, a bandwidth-bound workload plateaus under a flattened voltage-frequency
curve. The mechanism is measured rather than inferred — core voltage pinned across a rising core
clock, the crossbar clock pinned with it, and the SM-to-memory path ceasing to scale — and a
repair derived from that diagnosis behaved as predicted. Comparing two vendor BIOS positions on
one 3070 Ti, the "OC" position draws roughly a quarter more power at matched frequency for 0.56%
more peak compute; a prediction registered in advance that this difference was voltage was
**refuted**, both positions holding the same voltage floor while the difference proved to be a
roughly constant 34 W offset that does not scale with core clock and remains unexplained.

A methodological result affects all of the above and, we suspect, other work: ordinary desktop
capture software depresses measured GPU throughput and inflates run-to-run spread roughly
five-fold, invisibly at idle. Measurements taken without controlling for it are biased downward in
the mid-band.

**Limits are stated throughout and are not incidental.** Two chips, one unit each; every *tuning*
result comes from a single card; two workloads. Nothing here outperforms vendor boost algorithms,
and no claim of discovering guardband or inter-chip variation is made — both are established
literature. The contribution is open, current-generation, reproducible measurement of a
relationship whose public data is either datacenter-only or swept over the wrong range.

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
characterisation now shipped as standard. Whether comparable margin remains, and where it sits, is
not established for current consumer parts.

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
of a relationship whose public data is either datacenter-only or swept over the wrong range.

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
early that substantial energy savings are available at modest performance cost — one such study
reported an average 19.28% energy reduction for under 4% performance loss across 37 benchmark
applications ⚠️. The general shape of the result is consistent across the literature: reducing core
frequency below stock improves performance-per-watt up to a point, after which fixed power costs
dominate and efficiency falls again.

Workload character strongly mediates this effect. Compute-bound kernels scale close to linearly
with core clock, while memory-bandwidth-bound kernels are limited elsewhere and are comparatively
insensitive to it [4]. This work reproduces that distinction directly (§3.2) and uses it to select
benchmark workloads.

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

The closest prior work predicts optimal core *and* memory frequency configurations for an unseen
kernel from static code features, evaluated across three NVIDIA architectures (Kepler, Maxwell,
Volta) using a suite of micro-benchmarks [1]. A follow-up compares six model families and reports
XGBoost achieving R² ≈ 0.9646 on Volta [2]. Related approaches predict execution time and power
across frequency settings for deadline-aware scheduling ⚠️.

**Positioning.** This work does not claim a better predictor than [1]. It asks a different question:
whether per-*unit* prediction is worth its measurement cost at all, against a fixed-frequency
baseline — and reports a null where it is not (§5.2).

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

**XBAR is an independently documented clock domain on Blackwell.** A published analysis of GB202
(RTX 5090) establishes that XBARCLK has its own PMU object, clock source, 127-point V/F table,
hardware measurement entry point and runtime control path, arguing explicitly that public tooling had
mistaken it for a software statistic. It reports a 0.8999:1 GPC-to-XBAR constraint in the propagation
topology.

**Raising it deliberately is also published.** Work on runtime XBAR offsets under Linux reports
applying +60 to +450 MHz and measuring up to +10.6% FPS on an RTX 5090, August 2026.

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

**What §5.7.3 contributes is therefore the measured consequence chain, not the domain's existence
or its controllability**: pinning core voltage collapses the core-to-crossbar ratio and produces a
bandwidth plateau on a real workload, with the DRAM clock shown constant throughout, and a
workload-dependent sign where the same setting helps one kernel and harms another.

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

### 2.7 Existing public datasets, and why they are insufficient

| Dataset | Hardware | Core sweep (% of rated boost) | Suitable for efficiency-optimum questions? |
|---|---|---|---|
| GPU-DVFS-Dataset [6] | 1× Tesla V100 | 55–111% | **Yes** — spans below stock |
| HKBU-HPML [7] | GTX 1080 Ti | 101–126% | **No** — at/above stock only |
| HKBU-HPML [7] | RTX 2070 Super | 95–118% | **No** — at/above stock only |

This is a contribution in its own right and is reproducible via `analysis/compare_consumer.py`.

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
[7], not two independently produced datasets, and **no systematic survey established that they are
the only public consumer DVFS sweeps in existence.** The claim made here is therefore about the
consumer DVFS data we were able to locate, not about a surveyed population. That distinction is
stated rather than glossed because this project has already retracted one novelty claim for
exactly this failure — asserting an absence in the literature without searching for it (§2.2). A
dated search across the dataset repositories and artifact appendices would be needed before any
stronger wording is justified, and has not been performed.

What the two ranges show is arithmetic and does not depend on the survey being complete. Both are
effectively overclocking sweeps: they begin at or above the rated boost clock and increase from
there. Because the efficiency optimum lies *below* stock — at 62% of maximum in the V100 data —
neither swept range contains it.

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
| Driver | 610.88 |
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
| mid core clock, flattened V/F curve | **the crossbar clock**, pinned because core voltage is pinned (5.7.3) |
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
held constant moves the crossbar 2.3%, whereas at stock the crossbar holds a near-constant 0.95
ratio to the graphics clock across the same range. The rail topology itself was not probed; what was
measured is the behaviour.

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
of maximum (§5.1). The `membw` figures here — 41.6%, 11.3%, 37.4%, at 56% of sustained maximum —
are more favourable than that on two of four axes, on a 2025 consumer part measured
independently seven years and four
architectural generations later. This is the central empirical claim of the work: the efficiency
headroom identified on datacentre hardware is not an artefact of datacentre hardware.

**The compute/memory distinction appears in what the optimum costs, not where it sits.** Both
optima land on the same grid point, so at this resolution they are *indistinguishable* — which is
not the same as equal, and separating them requires a finer sweep around 1300–1800 MHz rather than
a wider one. What does separate cleanly is the price of operating there: `gemm` surrenders 40.6% of
its throughput to reach its optimum, `membw` only 9.8%. For bandwidth-bound work, running at 56%
of maximum clock is close to free — 37.4% less power for an 11.3% slowdown. For compute-bound work
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

#### 5.5.7 The optimum sits at the knee of the vendor's voltage curve, on both chips

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
which voltage is still falling.** It does, on both chips:

| | median suite optimum | stock voltage floor holds to | floor value |
|---|---|---|---|
| RTX 5060 Ti (Blackwell GB206) | **1537 MHz** | **1552 MHz** | 0.720 V |
| RTX 3070 Ti (Ampere GA104) | **1485 MHz** | **1500 MHz** | 0.812 V |

On the 5060 Ti the optimum is **1537 MHz against a voltage floor holding to 1552 MHz**; on the
3070 Ti, **1485 MHz against a floor holding to 1500 MHz**. Both optima fall within one grid step
below the top of their own card's floor, at different absolute frequencies and different floor
voltages.

🔑 **Two chips is what makes this a mechanism rather than a coincidence.** One card landing near its
own knee could be luck. Two architectures, two vendor curves, two different frequencies, each landing
at its own knee, is a regularity — and it makes a falsifiable prediction for any further card:
locate where its stock V/F curve stops flattening and the efficiency optimum should be there. That is
the cheapest available test on the incoming RTX 3060 and RTX 2060 Super, and it requires no new
method.

**The 3070 Ti's optimum is not an artefact of its grid.** Its suite grid continues to 1590, 1695 and
1771 MHz, so 1485 is an interior maximum rather than an edge, and **7 of the twelve** workloads pick
it independently — a median produced by agreement rather than by a scatter with nothing at its
centre.

⚠️ **On both cards the voltage and the optimum come from different runs.** Voltage requires HWiNFO
joined by timestamp and was collected on `gemm`/`membw` sweeps; the optima come from the
twelve-workload suites. Same card and same stock configuration in each case, but not the same
session, and this project measures ~1.47% cross-session drift on `gemm` alone. The alignment is
striking and the mechanism is coherent, but **a careful version measures voltage during the suite
itself**, and that is the next thing this section needs.

⚠️ **This does not refute the leakage account, and is not offered as an alternative to it.** P_fixed
contains leakage along with memory refresh, display output, VRM losses and fan power, none of which
this instrument separates. What changes is which part of the explanation this work can claim to have
*measured*: the voltage floor is in the data, the leakage decomposition is not.

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
| 95% floor (5.6) | 96.7% | 76.6% | **1.034** | **79.2%** |

The unconstrained optimum trades **15.9% more units for 30.6% less fleet power**. The 95% floor
trades **3.4% more units for 20.8% less**. Both rows follow arithmetically from the measured
performance cost and power saving; nothing is assumed yet.

**That converts to a single break-even ratio, which is the useful form.** The extra hardware is paid
once and the energy is saved continuously, so the trade pays exactly when lifetime energy cost
exceeds a fixed fraction of purchase price:

    unconstrained   0.159 / 0.306 = lifetime energy must exceed 52% of unit price
    95% floor       0.034 / 0.208 = lifetime energy must exceed 16% of unit price

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
| `membw` (bandwidth-bound) | the entire benefit: +3.6% to +16.1% over stock | actively harmful: up to -29.6% throughput across 1560-1867 MHz |

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

#### 5.7.2 The same curve costs a bandwidth-bound workload up to 29.6%

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

**This mechanism is established by direct measurement.** NVML exposes neither core
voltage nor interconnect clock, but HWiNFO exposes both, and two further sweeps were run with it
logging alongside: one fully tuned, one at full stock.

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
decouples from the core and stops scaling.

**The novelty claimed here is the chain, not the domain.** That XBAR is an independently clocked
domain coupled to core voltage is established in the reverse-engineering literature [11] and is not
claimed as a finding of this work; §2.5.1 sets out what is already known and what was searched for.
What follows is the measured consequence of pinning that domain's voltage.

⛔ **THE MEMORY IS NOT SLOWER, AND THAT IS THE POINT.** The obvious reading of a falling ratio is
that the memory overclock stopped working. It did not: **the DRAM runs at 16301 MHz throughout both
configurations**, the +2500 offset applied and holding at every point in the table. What stops
scaling is the on-chip path between the SMs and the memory controllers, not the memory devices. The
memory can deliver the bandwidth; the GPU cannot issue requests fast enough to use it.

⚠️ **Nor is the crossbar slowing down — it is failing to speed up**, and the distinction matters for
anyone reading the ratio as a rate. Across 1402–1867 MHz the core climbs 33% while the tuned
crossbar moves 1320 → 1350 MHz, a rise of 2.3%. It is pinned, not throttled. The ratio falls because
its denominator grows. Stock over the same range takes the crossbar 1335 → 1815 MHz, tracking the
core, which is what the 0.928–0.976 band describes.

That distinction is what makes the elasticities interpretable rather than merely suggestive:
throughput responds to crossbar clock at **1.31** and to core clock at **0.51**, and above the
plateau a 14.4% crossbar increase buys 14.1% more throughput — very nearly one-to-one. **Throughput
tracks the crossbar, not the core**, on a card whose DRAM clock never moved.

**The table above shows five of the ten measured points**, chosen for spacing. The 0.725 is the
lowest of all ten and falls at 1942 MHz, which the table does not display; an earlier version of
this sentence read 0.726 off the displayed rows alone. Both extracts are committed beside the
sweeps they came from and every figure in this subsection is recomputed from them by the auditor.

Throughput follows the crossbar, not the core. On the tuned card, elasticity of `membw` throughput
to core clock is 0.51; to crossbar clock it is 1.31. Above the plateau a 14.4% crossbar increase
buys 14.1% more throughput.

The two configurations agree precisely where their voltages agree - at 1402 MHz both sit at 0.720 V
and both deliver ~282 GB/s - and diverge from 1635 MHz, the first point at which stock raises
voltage and the tuned card does not.

The chain is therefore: flattened curve, so pinned voltage, so pinned crossbar clock, so a
non-scaling path to memory, so a bandwidth plateau while DRAM itself is untouched at 16301 MHz.

⚠️ **This does not require `membw` to be DRAM-saturated, and it is not.** Section 3.3.1 establishes
that no constructible kernel saturates DRAM below roughly 2000 MHz on this device, which covers
most of the band measured above — so a reader arriving from that section will reasonably ask
whether this plateau is simply that ceiling under another name. It is not, and the table itself
shows why: an issue limit is a property of the part and applies to **both** configurations equally,
so it cannot produce a difference between them. Stock and tuned agree at 1402 MHz, where their
voltages agree, and diverge only from 1635 MHz, where stock raises voltage and the tuned card does
not. What is measured here is that divergence at matched core and memory clock, not an absolute
bandwidth. Section 3.3.2 sets out which limiter governs which regime.

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
tuned one - 66.1 W against 52.4 W at 1867 MHz - because the restored voltage slope is what
un-starves the crossbar. The trade of 5.7.5 also reproduces: above 2010 MHz the tuned curve is
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
| fully tuned | best matched-frequency efficiency | loses up to 29.6% in the plateau band |
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
where the flattened curve pins voltage and starves the crossbar; a card left to boost freely sits
at 2968-2993 MHz, above the flattened region entirely, where both curves carry the same voltage.
The harm is real and reproducible when frequency is locked into that band, and absent when it is
not. Anyone reading 5.7.2's "-29.6%" as a cost they would pay in ordinary use would be wrong.

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
tuned at 20:42 the same day, memory-only at 18:13 the next - switching configurations requires a
manual Afterburner change that cannot be scripted here. Idle temperature was 40-42 C at the start of
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
   otherwise look as though they collide.** That mechanism identifies the crossbar clock, not DRAM,
   as the limiter — it asserts DRAM is *untouched* — and it rests on a divergence between two
   configurations at matched core and memory clock rather than on an absolute bandwidth. A ceiling
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
    shows the same voltage curve can help one phase and cost another up to 29.6%. A per-phase optimum
    is not measured here.

---

## 7. Conclusion

The question this work set out to answer is narrow and checkable: how much efficiency do
conservative stock defaults leave on the table on current consumer GPUs, what drives it, and is
per-unit measurement worth its cost. Three things can be said with the data collected.

**The gap is real and large, and the published consumer data could not have found it.** Both
public consumer DVFS datasets sweep at or above rated boost, and the optimum lives below stock, so
their small measured gaps are an artifact of range rather than evidence of absence (§2.7). That
observation is reproducible in a single script, it sharpens the justification for this project's
own sweep design, and it is the contribution most likely to be useful to someone else.

**Per-unit prediction is worth its cost only under a constraint, and the fitting is not the part
that earns it.** Unconstrained, a probe-based model ties a single fixed frequency, and that null is
reported as the result rather than tuned away (§5.2). Impose a performance floor and the ranking
inverts, because a fixed policy must satisfy the most frequency-sensitive workload it might meet
(§5.6.1, §5.6.2). The practical recommendation that survives is *measure a few points, interpolate
between them, and attach a performance guarantee* — not *fit a model*. That recommendation carries
a condition: it depends on the performance curve being concave, and on a convex curve the safety
argument reverses.

**A mechanism was measured, not inferred.** The bandwidth plateau under a flattened
voltage-frequency curve is traced link by link — pinned core voltage, pinned crossbar clock, an
SM-to-memory path that stops scaling — with a stock control run, and a repair derived from the
diagnosis behaved as predicted including in its predicted cost (§5.7). This is the part of the work
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

A fourth correction was methodological rather than physical: an early attribution of measured
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
- [7] HKBU-HPML DVFS datasets. `github.com/HKBU-HPML/GPU-DVFS-Job-Schedule`,
  `github.com/HKBU-HPML/NV-DVFS-Benchmark`
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

- [10] *Modeling and Chasing the Energy-Efficiency Sweet Spots in Modern GPUs.* arXiv:2607.00819.
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

- [17] Mei, Wang, Chu. *A survey and measurement study of GPU DVFS on energy conservation.*
  Digital Communications and Networks, 2017. `sciencedirect.com/science/article/pii/S2352864816300736`
  ⛔ **NOT READ — ScienceDirect returned HTTP 403.** Surfaced repeatedly in searches as the standard
  survey of this area and is very likely to contain a swept-range comparison bearing directly on
  §2.7. Nothing in this paper cites it for a figure, and nothing should until someone opens it.
  Try an institutional login or the authors' own copy.
- [1] Guerreiro et al. *Predictable GPUs Frequency Scaling for Energy and Performance.* ICPP 2019.
  DOI 10.1145/3337821.3337833 — **the closest prior art; read this before finalising any novelty
  claim.**
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
