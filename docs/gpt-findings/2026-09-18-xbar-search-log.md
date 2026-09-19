# XBAR search record: coverage, supplementary sources, and open leads

Date: **2026-09-18 America/Los_Angeles**; retrievals also cross September 19 UTC.
Companion to the [main findings](2026-09-18-xbar-prior-art.md).

This file preserves the vocabulary coverage and source/navigation record available
from the conversation. **It is not a verbatim export of every search-tool call.**
The exact full sequence of query strings and timestamps was not preserved in this
artifact. No exhaustive query count is claimed, and representative strings have
not been invented and presented as executed queries. Future searches should log
exact strings as they run, as the [archive instructions](README.md) require.

## Requested search scope and what was attempted

The user explicitly requested the following vocabulary and venues. The completed
pass used these vocabulary families in combinations, site-restricted searches,
source navigation, and full-text searches within retrieved documents.

| Vocabulary or venue family | Coverage | Outcome |
|---|---|---|
| SYS clock, hub clock, fabric, fabric clock, L2 clock, uncore; also XBAR and crossbar | General and technical-source discovery, including old domain names such as L2C/GPC | Older BIOS/domain-tuning material and recent XBAR experiments found. |
| piecewise voltage frequency curve, knee, ridge, efficiency point | Patent-oriented searches and relevant full-text inspection | General V/F material found; no exact combined pathology and repair located. |
| crossbar clock, fabric clock, memory throughput, clock domain ratio | Patent and technical-source searches | NVIDIA adjustable-XBAR-ratio disclosure and Intel compute/I/O frequency balancing found. |
| Nouveau, envytools, VBIOS, PMU, GSP, NVIDIA open GPU kernel modules | Public documentation, selected source inspection, and reverse-engineering accounts | Architectural context and Loong0x00's causal experiments; no measured global-memory plateau matching the full supplied claim. |
| Overclock.net, HWBOT, Guru3D, TechPowerUp | Site-index discovery and attempted direct retrieval | HWBOT and a Guru3D post opened; Overclock.net and TechPowerUp access remained incomplete. |
| Non-English communities | German, Russian, Italian, Chinese, Japanese, and Korean discovery attempts | Substantive German/Russian findings; Italian archive pages and Chinese tool docs reached. No comprehensive language-community coverage. |
| Archived material | HWUpgrade archive-format pages and attempted Wayback CDX access | Italian archive-format text opened; no Wayback snapshots verified. |

The relevant sources were assessed against three separate requirements: the
flattened-core-curve trigger, a causal XBAR-mediated memory-bandwidth effect, and
the specific low-voltage-slope repair. Similarity on one requirement does not
establish all three. Rendering FPS was not converted into a claim about GB/s.

## Source register: principal findings

The report contains the detailed interpretation. These identifiers let a future
reader return directly to the primary material.

| Source | Read status | Finding / restriction |
|---|---|---|
| [Hardwareluxx RTX4000 thread page 7](https://www.hardwareluxx.de/community/threads/nvidia-rtx4000-undervolting-sammler.1325830/page-7), EleCtricStream #184, 2023-01-25 | Relevant text opened; images not independently verified | N=1 RTX 4090 report of lower XBAR under undervolting; performance explanation initially untested. |
| [NVIDIA issue #1266](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1266), Loong0x00, opened 2026-07-28 | Issue text and tables opened | N=1 RTX 5090; memory-limit trigger and direct XBAR intervention at fixed physical MCLK. FPS, not GB/s. |
| [Blackwell physical XBAR clock-domain account](https://loong0x00.com/notes/blackwell-xbar-physical-clock-domain/), 2026-08-13 | Opened | Same research chain; documents mechanism inferences and failed reproduction on other hardware/driver. |
| [LACT #1147](https://github.com/ilya-zlobintsev/LACT/issues/1147), opened 2026-08-10 | Issue text and tables opened | Same N=1 platform; runtime XBAR/per-domain voltage controls and short-run FPS benefit. |
| [Overclockers.ru RTX5070-5080 page 650](https://forums.overclockers.ru/viewtopic.php?f=3&start=12980&t=642582), 2026-08-18 | Relevant Russian text opened | Published XBAR ceiling/workaround advice; Xatuman's +300 MHz recovery is N=1 RTX 5070 Ti, without bandwidth measurement. |
| [mVolt guide](https://github.com/b00nz/mVolt/blob/main/docs/guide.md) | Opened, live documentation | Voltage ceilings, XBAR/SYS offsets, and propagation controls. Capability documentation, not proof of this repair. |
| [Reddit wghb9d](https://www.reddit.com/r/nvidia/comments/wghb9d/i_present_to_you_method_4_of_undervolting_your_gpu/), kinggot, 2022-08-05 | Post and relevant comments opened | Stock lower-curve and gradual-transition recipes; no XBAR diagnosis. |
| [US20250322481A1](https://patents.google.com/patent/US20250322481A1/en), NVIDIA | Relevant full text opened | Adjustable XBAR ratio; no exact pathology/repair located. |
| [US20240053789A1](https://patents.justia.com/patent/20240053789) and [US12717372B2](https://patents.justia.com/patent/12717372), Intel | Relevant full text opened | Compute/I/O frequency balancing; not GeForce undervolting. |

## Supplementary findings retained for future use

These did not improve the answer enough to lead with them. Their weaker evidence
status is part of the record.

| Source / identifier | Access and finding | Why it does not close the gap |
|---|---|---|
| [ComputerBase Lovelace thread page 35](https://www.computerbase.de/forum/threads/lovelace-4070-4080-4090-varianten-overclocking-undervolting-sammelthread.2107768/page-35), Gortha #692, 2023-04-19 | Relevant text opened; discussion associates undervolting with lower video/crossbar clocks. | No isolated global-memory bandwidth experiment. |
| [HWBOT thread 170346](https://community.hwbot.org/topic/170346-gtijason-geforce-gtx-970-16082206mhz-587977-dx11-marks-unigine-heaven-xtreme/), GtiJason, 2017-08-07 | Opened; describes factory-OC tradeoffs between GPC and XBAR/L2C/SYS clocks and BIOS tuning. | Older domain-tuning knowledge, not the undervolting causal chain. |
| [Guru3D post 6136954](https://forums.guru3d.com/posts/6136954/), A M D BugBear | Opened; a 2023 Maxwell BIOS-tuning account discusses GPC/L2C/XBAR/SYS/HUB and benchmark effects. | One four-GTX-970 SLI system is not four independent single-card replications; no matching GB/s experiment. |
| [Hardwareluxx RTX5090 thread page 142](https://www.hardwareluxx.de/community/threads/offizieller-nvidia-rtx-5090-overclocking-und-modding-thread.1363289/page-142), Sladen #4243, edited 2026-08-11 | Relevant text opened; N=1 BIOS comparison reports XBAR and benchmark differences at the same core clock. | BIOS changes introduce other differences; not an isolated repair or bandwidth test. Original publication date not established in the saved record. |
| [Reddit 1vq72r7](https://www.reddit.com/r/overclocking/comments/1vq72r7/undervolting_5070_affects_xbar_and_gpu_video/) | Opened; N=1 ASUS RTX5070 undervolting report describes lower crossbar clocks; discussion suggests mVolt XBAR adjustment. | No measured bandwidth plateau or controlled causal isolation. Exact original publication date not pinned here. |
| [HWUpgrade Italian archive page](https://www.hwupgrade.it/forum/archive/index.php/t-3024694-p-32.html), discussion including Eddie666, 2026-08-26 | Archive-format text opened; XBAR-offset and undervolt benchmark comparisons. | No controlled global-memory plateau/repair demonstrated in the inspected material. |
| [Reddit tw8j6r](https://www.reddit.com/r/nvidia/comments/tw8j6r/there_are_two_methods_people_follow_when/), 2022-04-04 | Opened; compares undervolt curve methods and effective-core-clock/performance behavior. | Lower-curve shape matters, but no XBAR/bandwidth diagnosis. |
| [Reddit 1dtjewg](https://www.reddit.com/r/nvidia/comments/1dtjewg/proportional_overclockingundervolting_need_some/), 2024 | Relevant main text opened; proportional curve-editing proposal. | Curve construction precedent, not the causal chain. |
| [vfctl GPU curve tool](https://erfi.dev/reference/vfctl-gpu-curve-tool/) | Opened; describes stock settings below a ramp, transition to the target, and flat upper region. | Publication date not verified. Similar shape is not evidence of an earlier XBAR diagnosis or measured repair. |
| [Blackwell independent clock domains](https://loong0x00.com/notes/blackwell-independent-clock-domains/) | Opened and searched within text; no matches for bandwidth, flatten, or GB/s in the retrieved text. | A textual no-match is not an exhaustive semantic audit. Same author's research, not an independent replication. |
| [Blackwell XBAR overclocking](https://kovasky.me/blogs/blackwell_xbar_overclocking/), 2026-08-25 | Page opened; introductory material inspected. N=1 RTX5060 account following Loong0x00's work. | Full benchmark evidence not analyzed in this pass; retain as a follow-up lead, not as verified quantitative support. |
| [SHANAjam/rtx5090-xbar-control Chinese README](https://github.com/SHANAjam/rtx5090-xbar-control/blob/main/README.zh-CN.md) | Opened; Windows RTX50 XBAR, MSVDD, propagation-ratio, and V/F controls; archived project points to mVolt. | Tool documentation is not a controlled global-memory bandwidth experiment. Publication priority not verified. |
| [1usmus Patreon post 167103633](https://www.patreon.com/1usmus/posts/about-xbar-nvvdd-167103633) | Public text opened; discusses XBAR tuning, with a later correction to its performance estimate. | Sample size and controls insufficiently established for use as quantitative evidence here. |
| [Reddit 1w3h7rn](https://www.reddit.com/r/overclocking/comments/1w3h7rn/memtest_vulkan_is_actually_pretty_good_for/) | Opened; N=1 RTX5090 report relating XBAR tuning to memory-test errors. | Stability/error behavior, not a measured GB/s plateau. |
| [Intel US10430310B2](https://patents.google.com/patent/US10430310B2/en), *Dynamic voltage-frequency curve management* | Relevant full text opened; general adaptive V/F/minimum-voltage management. | Not NVIDIA; no exact XBAR causal chain found. |

## Architectural references and source inspection

| Identifier | What was accessed |
|---|---|
| [envytools GF100+ clocks](https://envytools.readthedocs.io/en/latest/hw/pm/gf100-clock.html) | Clock-domain documentation opened. |
| [envytools PMU documentation](https://envytools.readthedocs.io/en/latest/nvrm/pmu/index.html) | PMU/DVFS context opened. |
| [Nouveau PowerManagement](https://nouveau.freedesktop.org/PowerManagement.html) | Search-result discovery; full page was not established as read in the retained record. |
| [NVIDIA virtual P-state tables](https://nvidia.github.io/open-gpu-doc/virtual-p-state-table/virtual-P-state-table.html) | Specification opened; older-generation scope explicitly retained. |
| NVIDIA open kernel modules, **61dcc93722ecb418bb5f2e00923f05b4b8051dd1** | Temporary sparse checkout outside Headroom; selected `src/common` and kernel performance paths inspected. No source files copied into the archive. |

## Concrete unresolved retrievals

- **Overclock.net:** [post 29608363](https://www.overclock.net/posts/29608363/)
  was linked by the Russian discussion, but direct opening failed. The discussion's
  characterization of it is not a substitute for reading the post.
- **Overclock.net:** [RTX5090 owners' thread, page 2002](https://www.overclock.net/threads/official-nvidia-rtx-5090-owners-club.1814246/page-2002)
  also failed direct retrieval.
- **TechPowerUp:** [Dell RTX3080 black-screen thread 300907](https://www.techpowerup.com/forums/threads/dell-rtx-3080-black-screen-under-heavy-load-ram-seems-to-be-fine.300907/)
  appeared in search snippets mentioning XBAR, but full retrieval failed. The
  snippet did not establish the user's claim.
- **Wayback:** an attempted CDX query for Overclock.net URLs containing XBAR failed.
  The Wayback homepage being accessible did not produce a verified archived thread.
- **Patents:** native Google Patents search pages failed; individual documents were
  retrieved through indexed discovery. Search-only leads such as **EP4272049A1**
  and **CN118113561B** were not used as full-text evidence of the claimed mechanism.
- **Attachments and private communities:** screenshots not opened, private chats,
  login-gated material, and unindexed posts cannot be counted as reviewed.

## Follow-up work that would strengthen the record

Retrieve the blocked Overclock.net and TechPowerUp leads; inspect dated captures or
edit histories for claims whose priority depends on exact publication timing;
complete the patent-family search; and seek an experiment measuring GB/s while
directly manipulating XBAR under a flattened core curve. These are outstanding
search tasks, not promises of scheduled future work or evidence that a matching
source exists.
