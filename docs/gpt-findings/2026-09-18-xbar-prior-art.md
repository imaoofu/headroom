# XBAR undervolting and bandwidth: expanded prior-art search

Search date: **2026-09-18, America/Los_Angeles** (some retrievals were September 19
UTC). Author: GPT/Codex. Archived at Raymond's request.

**Status:** relevant public precedents and mitigations found; the exact combined
causal experiment and repair were not located. This is a bounded search result,
not proof of novelty. Source-reported hardware measurements were not independently
reproduced. Multiple runs on one chip remain **N=1 chip**.

The search and original answer were completed without reading `CLAUDE.md` or the
project's prior-art files. The assistant subsequently read repository instructions
to archive this report. That later reading does not make future work in this same
context a cold novelty check. The conclusions below preserve the external search;
they do not incorporate a new audit of Headroom's experimental data.

## The prompt and claim under examination

Raymond requested a follow-up to an earlier prior-art search, specifically covering
internal clock-domain vocabulary, patent full text, reverse engineering,
overclocking forums, archives, and non-English communities.

The supplied claim was that, on an NVIDIA consumer GPU, flattening the core
voltage-frequency curve pins voltage while core frequency rises; XBAR then remains
at a low fixed frequency instead of tracking the core, imposing a global-memory
bandwidth plateau near 300 GB/s despite maximum DRAM clock. A diagnosis-derived
repair, stated before measurement, restores the stock slope only in the low-voltage
region and removes the plateau. These are the user's supplied experimental claims,
not measurements independently verified in this search.

The two questions were:

1. Has someone documented undervolting lowering the interconnect/fabric clock and
   demonstrated that this caps memory bandwidth as a causal chain?
2. Has someone published a repair or mitigation?

## Answers

**Question 1:** undervolting lowering XBAR is explicitly documented. Lower XBAR
reducing performance at unchanged DRAM clock has also been demonstrated through
intervention in a source-reported experiment. No located source joins the flattened
core-curve trigger to a measured global-memory bandwidth plateau in GB/s with XBAR
established as its cause.

**Question 2:** yes, broader mitigations are published: direct XBAR adjustment,
changing the core-to-XBAR propagation ratio, and using a voltage ceiling instead of
an Afterburner curve. The exact advance-stated repair of restoring only the
low-voltage stock slope, followed by measured removal of the bandwidth plateau,
was not located.

Consequently, neither "undervolting can suppress XBAR" nor "no workaround has been
published" is a defensible novelty claim. The shape of a curve retaining stock
behavior at lower voltages also has prior publication. Any narrower contribution
must describe the actual diagnosis, intervention, advance prediction, and measured
outcome, with the study's sample size.

The original answer did not establish Headroom's priority date. Compare the source
dates below with dated experiment and disclosure records before calling a 2026
source earlier than the project's result. Publication dates of edited issue bodies
do not, by themselves, date every later-added experiment in those bodies.

## 1. Hardwareluxx: explicit undervolting-to-XBAR observation, January 2023

**Identifier:** EleCtricStream, January 25, 2023, post **#184**, in
[NVIDIA RTX4000 Undervolting-Sammler, page 7](https://www.hardwareluxx.de/community/threads/nvidia-rtx4000-undervolting-sammler.1325830/page-7).
**Read status:** relevant forum text opened; image attachments not independently
validated.

The author reports NVIDIA Inspector showing approximately **150 MHz lower crossbar
clock under undervolting**, using the stock Suprim core frequency. The proposed
explanation is performance loss at the same core clock. The post explicitly says
performance tests have not yet been done. This is an **N=1 RTX 4090 report**.

Subsequent posts include another participant's Time Spy Extreme stock/undervolt
comparison and discussion of the performance explanation. They do not isolate
XBAR, measure memory bandwidth, or establish the complete causal chain.

**Implication:** the undervolting-to-lower-XBAR observation predates this project.
It is not a demonstrated global-memory bandwidth mechanism.

## 2. NVIDIA issue #1266: causal low-XBAR intervention at fixed DRAM clock

**Identifier:** Loong0x00,
[NVIDIA/open-gpu-kernel-modules #1266](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1266),
opened **July 28, 2026**. **Read status:** issue text and reported tables opened.
This is a user report hosted in NVIDIA's repository, not an NVIDIA endorsement.

On **N=1 ASUS Astral RTX 5090**, the author reports that a finite maximum memory
clock constrains XBAR/SYS even when the maximum is non-binding for physical MCLK.
A direct XBAR-cap experiment is particularly relevant:

| Condition | Physical MCLK | Loaded core clock | Average FurMark FPS |
|---|---:|---:|---:|
| No temporary clock limit | 15,001 MHz | approximately 2,588 MHz | 256 |
| XBAR maximum 1,493 MHz | 15,001 MHz | approximately 2,952 MHz | 173 |

Rendered throughput falls **32.42% despite higher core frequency and unchanged
DRAM clock**. Resetting the memory-clock limits restores the reported state.
Directly imposing the XBAR limit makes this stronger than a correlation.

**Missing from the match:** the initiating condition is a memory-clock maximum,
not the flattened core curve, and the measured outcome is FPS, not global-memory
GB/s. It does not demonstrate the user's complete chain.

## 3. PMU/GSP account and limits of reproduction

**Identifier:** Loong0x00,
[XBAR in NVIDIA Blackwell GPUs: A Physical Clock Domain Ignored by Public Tooling](https://loong0x00.com/notes/blackwell-xbar-physical-clock-domain/),
August 13, 2026. **Read status:** technical account opened.

The account describes a distinct XBAR hardware domain, a GPC/XBAR ratio relation,
and shared-voltage relationships involving MCLK, XBAR, and SYS. It distinguishes
measured controls from inference about the current driver's exact propagation
implementation, which remains partly unresolved.

An NVIDIA engineer reportedly **did not reproduce** the memory-limit anomaly on
a different RTX 5090 and RTX 5070 Ti with driver 610.43.02. The original author
repeated the anomaly on 610.57.04 and under another VBIOS on the same physical
card. Those repetitions remain **N=1 chip**, not independent replication.

The NVIDIA issue, LACT issue below, and this author's related articles form one
connected research chain. Do not count them as separate independent discoveries.

## 4. LACT issue #1147: direct XBAR adjustment with measured performance benefit

**Identifier:** Loong0x00,
[ilya-zlobintsev/LACT #1147](https://github.com/ilya-zlobintsev/LACT/issues/1147),
opened **August 10, 2026**. **Read status:** issue text and performance table opened.

Runtime XBAR frequency and per-domain voltage controls are published for the
**same N=1 RTX 5090 research platform**. With physical MCLK fixed at 15,001 MHz
and a 600 W power limit, a +240 MHz XBAR request raises average FurMark FPS from
245 to 266. A +450 MHz request with a +20 mV domain-voltage request reaches 271 FPS.

The scored intervals are only **8-10 seconds**. The author explicitly treats them
as evidence of control and short-run throughput, not a stability qualification.
The higher frequency request without the voltage adjustment produced corruption.

**Implication:** direct XBAR adjustment is a published performance intervention.
This source neither removes the user's measured bandwidth plateau nor repairs the
low-voltage part of the core curve.

## 5. Overclockers.ru: an undervolting-related XBAR ceiling and workaround

**Identifiers:** August 18, 2026,
[RTX 5070-5080 discussion, page 650](https://forums.overclockers.ru/viewtopic.php?f=3&start=12980&t=642582),
including **tolikmixx post 18768562**, 13:47, edited 13:56, and Xatuman at 09:49.
**Read status:** Russian forum text opened; the following is a paraphrased
translation.

A quoted report says a custom curve restricted crossbar boost. tolikmixx warns
that Afterburner undervolting can impose an otherwise invisible XBAR-frequency
ceiling, and proposes changing **xbar ratio** in mVolt+ or setting the upper voltage
limit there. Xatuman reports that switching to mVolt increased crossbar frequency
by **300 MHz** on **N=1 RTX 5070 Ti**.

These are published mitigation advice and an anecdotal clock recovery. They are
not a controlled memory-bandwidth experiment. The controls are documented in the
[mVolt guide](https://github.com/b00nz/mVolt/blob/main/docs/guide.md), which was also
opened. Tool availability is not proof that it fixes the user's exact plateau.

## 6. Stock lower-curve recipes already existed in 2022

**Identifier:** kinggot, **August 5, 2022**, Reddit post **wghb9d**,
[I present to you "Method 4" of undervolting your GPU](https://www.reddit.com/r/nvidia/comments/wghb9d/i_present_to_you_method_4_of_undervolting_your_gpu/).
**Read status:** post and relevant comments opened.

The post describes an existing method that retains stock points below the target,
and a proposed compromise retaining stock settings at the lowest frequencies with
a gradual transition toward the target. The explanation concerns stability and
effective core clock. It does not diagnose XBAR or demonstrate a bandwidth repair.
The proposal's rationale is not itself experimental validation.

**Implication:** retaining a stock lower curve is already published as a recipe.
The regional diagnosis and the predicted bandwidth consequence must carry any
narrower distinction; the curve shape alone cannot.

## 7. Relevant patent disclosures

The search used web-index discovery and opened individual full texts. It was not
an exhaustive patent-family or classification search.

| Identifier and public date | Relevant disclosure | Limit of the match |
|---|---|---|
| **NVIDIA US20250322481A1**, *Application programming interface to identify processor settings*, published **October 16, 2025** | Adjustable XBAR ratio, including GPC-to-crossbar relationships, among workload-dependent processor settings. | No located flattened-curve bandwidth pathology or low-voltage-slope repair. [Full text](https://patents.google.com/patent/US20250322481A1/en) |
| **Intel US20240053789A1**, *Clock frequency management of multiple circuitries*, published **February 15, 2024**; later **US12717372B2**, granted August 25, 2026 | Compute/I/O clock relationships selected using stalls, memory latency, capacitance, and V/F-slope relationships. | Broader domain-balancing precedent, not a GeForce undervolting diagnosis. [Application](https://patents.justia.com/patent/20240053789), [grant](https://patents.justia.com/patent/12717372) |

No matching disclosure was located under the requested knee, ridge, efficiency
point, or piecewise wording. That is a search outcome, not a claim that no such
patent exists. Intel documents must not be attributed to NVIDIA merely because
NVIDIA appears in their citation network.

## 8. Internal-domain documentation and source inspection

- [envytools GF100+ clocks](https://envytools.readthedocs.io/en/latest/hw/pm/gf100-clock.html):
  opened. Distinguishes XBAR, HUB, GPC, and memory clocks, and describes XBAR between
  GPCs and ROPs. Older hardware and incomplete documentation; no undervolt/bandwidth
  intervention.
- [envytools PMU documentation](https://envytools.readthedocs.io/en/latest/nvrm/pmu/index.html):
  opened for firmware/DVFS context, not evidence of the specific repair.
- [NVIDIA virtual P-state table specification](https://nvidia.github.io/open-gpu-doc/virtual-p-state-table/virtual-P-state-table.html):
  opened. Older-generation V/F/performance-state and domain-frequency information;
  the document warns of changes starting with Pascal.
- NVIDIA open GPU kernel modules were inspected at commit
  **61dcc93722ecb418bb5f2e00923f05b4b8051dd1**, focusing on selected public clock
  headers and performance code. [Pinned clock-control header](https://github.com/NVIDIA/open-gpu-kernel-modules/blob/61dcc93722ecb418bb5f2e00923f05b4b8051dd1/src/common/sdk/nvidia/inc/ctrl/ctrl2080/ctrl2080clk.h).
  This was a targeted inspection, not a complete source audit or GSP disassembly.

SYS, HUB, L2, and XBAR were used as discovery vocabulary. They must not be treated
as interchangeable domains across GPU generations.

## 9. What was still inaccessible or incomplete

| Area | Actual coverage and remaining gap |
|---|---|
| Overclock.net | Site-index searches attempted; direct retrieval failed, including [post 29608363](https://www.overclock.net/posts/29608363/) and the RTX 5090 owners' thread page 2002. Those contents were not verified. No comprehensive internal search. |
| TechPowerUp forums | Search snippets available in places; attempted full-thread retrieval failed. Not comprehensively checked. |
| Guru3D | Specific post 6136954 was readable; broader retrieval/search access incomplete. |
| HWBOT | Relevant older thread opened; no matching complete causal chain located. No claim of complete forum coverage. |
| Archives | Italian HWUpgrade archive-format pages opened. Wayback CDX retrieval failed; no historical Wayback snapshots verified. An archive-format page is not an independently dated Wayback capture. |
| Non-English communities | Relevant German, Russian, Italian, and Chinese-language material reached. Chinese/Japanese/Korean searches yielded no verified matching causal experiment; limited coverage makes this weak negative evidence. |
| Patents | Individual full texts opened; native Google Patents search pages failed. No exhaustive all-office, classification, or family review. |
| Firmware | Public documentation and reverse-engineering accounts reviewed; no independent full PMU/GSP binary disassembly. |
| Other material | Private/unindexed communities, login-gated discussions, and unverified image attachments remain gaps. No hardware replication was performed. |

The [companion search record](2026-09-18-xbar-search-log.md) retains additional
source identifiers, read-status distinctions, and useful unresolved leads.
