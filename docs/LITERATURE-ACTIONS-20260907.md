<!-- dataset-grade: no -->

# Literature action list — 2026-09-07

⚠️ **MACHINE-GENERATED AND NOT VERIFIED.** Produced by two delegated search workflows (fourteen
agents, ~60 queries). Kept because the actions are useful and the coverage is auditable, NOT because
its claims are checked. Every item marked "snippet-only" is unread by anyone.

**Already acted on:** the power-curve check the critique names as the highest-value unrun search was
run on 2026-09-07 and is written into §2.7.1 — the 5060 Ti's dP/df steepens 5.4x across the band, so
it has the Tesla-shaped curve and Tang et al.'s own explanation covers the disagreement.

**Do NOT cite anything from this file in the paper without opening the source first.** That rule
exists because acting on a snippet from one of these sweeps put a false corroboration into §2.7
earlier the same day.

---

# HEADROOM — Action List from Six-Search Literature Sweep

## 1. DO THIS WEEK

**1. Add EDP/ED2P to the existing sweep CSVs — zero new measurements, highest ROI in the pile.**
Motivated by: DEFT (ACM ICS 2026, uses generalized EDP for GPU DVFS policy) and the Mittal & Vetter survey (read in full — perf/watt is the field default for same-chip sweeps, EDP is for cross-device comparisons). This is a formula over columns you already have (frequency, throughput, power → time × avg_power). Report it next to the 55.9%/25.3% headline pair, not as a replacement. Effort: under an hour. Do this before anything else on this list.

**2. Write the "perf/watt is the correct metric here" defense sentence, sourced.** Cite Price et al. 2015 (arXiv:1407.8116, read in full, cites the same Leng et al. guardband work you already cite, uses perf/watt exclusively) plus the Mittal & Vetter survey's finding that perf/watt criticism in the literature targets rack/PUE-level analysis, not chip-level DVFS sweeps. This closes a plausible reviewer objection for the cost of one paragraph.

**3. Add nvidia-smi power-accuracy citations to your methods/limitations section.** arXiv 2312.02741 ("Part-time Power Measurements," full architecture sweep, quantifies NVML duty-cycle undersampling, ~4.5–5.4% error on RTX 3090/A100 specifically) plus the SC 2024 paper on the built-in power sensor. Both are read-level-verified as existing and on-point (snippet-only on exact numbers, but the papers themselves are confirmed real and relevant — pull the RTX-specific figure before quoting a percentage). This is a citable error band replacing a vague hedge you already owe the reader given your own honesty rule.

**4. Reframe the crossbar/XBAR mechanism using established "uncore-bound" vocabulary.** Intel's Uncore Frequency Scaling (UFS) is a decades-old, well-documented CPU analogue: an interconnect clock domain distinct from both core and memory clock, with bandwidth saturating below a threshold uncore frequency independent of DRAM speed. This is snippet-only on the exact numbers (2.0 GHz saturation, 13% drop — verify against arXiv 2105.09642 before quoting), but the concept match is strong and free. Reframes your contribution from "we found a weird GPU quirk" to "we found the GPU-side instance of a documented cross-architecture phenomenon, and ours is voltage-driven rather than an OS-exposed knob because no consumer NVIDIA API exposes the crossbar clock directly" — that last clause is also a clean, citable limitation.

**5. Cite Leng et al.'s own per-chip presentation style as your n=1 justification template.** Leng et al. (MICRO-48) reported five individually-labeled GTX 780 chips rather than pooling into a confidence interval. This is a real, checkable precedent for exactly your n=1/n=2 problem: state plainly that with one chip per architecture you cannot characterize chip-to-chip variability at all, only report one point per architecture — citing the field's own accepted alternative (name each chip, don't fake a CI) rather than apologizing vaguely.

---

## 2. THE COUNTER-RESULT

**Partially bounded, not resolved — and the strongest counter-evidence is off-segment.**

- **Going Green (Schoonhoven et al., IEEE Cluster/arXiv 2211.07260)** — read in full, verified — finds a real efficiency ridge point well below peak clock (70% of peak on the RTX A4000, GA104 die — same silicon family as desktop RTX 3070) on Ampere/Turing workstation cards. This is the best documented counter to Tang et al.'s "no valley" claim: a valley on GA104-family silicon, at a similar magnitude to your own findings (GEMM: -27.5% speed for +50.9% efficiency on A100, same shape as your own trade curves).
- **The gap Going Green does NOT close: it's Quadro/workstation (A4000, A6000, Titan RTX), not GeForce.** State this caveat explicitly — it narrows but does not overturn the "does the valley exist on gaming-branded silicon" question, which is precisely the gap your 5060 Ti/3070 Ti data fills.
- **A genuine empty result, verified by five separate search angles (mining/hashrate academic literature, GeForce DVFS papers, power-capping valley studies, undervolting literature, blockchain-frequency papers): no peer-reviewed paper sweeps a GeForce/Radeon-branded card below stock with a formal efficiency metric, except Tang et al. itself.** That makes your result the second published sweep of gaming silicon and the first affirmative one (Tang found no valley; you found one). This is defensible to state directly in related work, and it upgrades your novelty claim beyond what CLAUDE.md currently states ("open reproducible data") to "first affirmative below-stock efficiency valley on gaming-branded silicon."
- **Do not resolve Tang et al. by assertion.** Tang's own explanation (2080 Ti's power curve doesn't turn up sharply past 1000 MHz the way Tesla's does) is architecture-specific and untested against your own data. If you want to actually settle this rather than bound it, the cheap move is: check whether your 5060 Ti's power-vs-frequency curve *does* turn up sharply (you likely already have this in the sweep CSVs) — if it does, that's a mechanistic explanation for why you see a valley and Tang didn't, without needing new hardware.
- **Uncited leads not worth chasing yet:** Stachowski et al. 2021 (blockchain DVFS, J. Supercomputing) is plausibly the most on-point paper if it tests GeForce mining cards, but it's blocked at 403 on ResearchGate and completely unverified — don't cite, don't rely on it, flag for manual retrieval only if you have library access.

---

## 3. NOVELTY (the substitution result)

**Survives, on genuinely weak-but-real evidence: an empty search, not a read paper that addresses it directly.**

- Five differently-worded queries targeting exactly this claim (joint DVFS+undervolt substitution, guardband-vs-frequency overlap, Vmin-curve overlap, "substitute not complement" framing) returned nothing that measures or states a quantitative overlap/redundancy decomposition between frequency reduction and undervolting.
- The closest prior statement is qualitative, not measured: the standard V-F guardband literature (Leng et al., already in your citations) establishes that voltage margin shrinks as frequency drops — which *implies* the substitution should exist, but nobody has run your specific experiment (freq-only vs. UV-only vs. both, against one common baseline, showing ~92% overlap).
- **State this precisely in the paper, per your own honesty rule: "not found in the literature searched," not "first ever."** You ran six search angles across two independent search sessions and got a consistent null — that's a reasonably strong absence for a claim of this specificity, but it is still an absence, not a confirmation, and should be written that way.
- One unverified lead: arXiv 2601.08539 ("Kernel-Level DVFS for LLM inference") apparently contrasts frequency vs. power-cap tuning with a similar "different regions of the operating curve" argument — different technique pair, snippet-only, worth a 10-minute read for framing/presentation template only, not as a citation of prior art on your actual claim.

---

## 4. METRICS AND METHOD

- **Add EDP/ED2P** (see Do This Week #1) — the single concrete addition.
- **State the nvidia-smi power error band explicitly** (see Do This Week #3) rather than treating NVML power as ground truth — this is a limitation you should name, not something anyone found a fix for.
- **No formal statistical convention exists for n=1-chip DVFS studies** — confirmed by an empty search across position papers, reporting standards, and prior art. Nothing to add here beyond what your own honesty rule already does (report N explicitly, no fake CI). Leng et al.'s per-chip labeling (item 5 above) is the closest thing to a template.
- **Confirm Tang et al.'s own metric before contrasting your result against it.** The summary snippet suggests perf/watt language, but this was not read in full and should be checked before asserting the two results are metric-comparable — five-minute check per your own rules.

---

## 5. VENUE

- **ICPE 2026, Artifact Evaluation Track, Data-artifacts category** — verified, read in full. This is the closest fit for what you actually have: a released, documented dataset plus reproducible tooling, judged on Documented/Consistent/Complete/Exercisable with three badge tiers (Available/Functional/Reusable). Aim your repo READMEs directly at these four criteria — you're most of the way there already given the per-directory README convention this project already enforces.
- **GPGPU 2026 workshop, co-located with ASPLOS** — 6-page format, deadline ~Jan 14 2026, "energy-efficient GPU designs" explicitly in scope. Good fit for the crossbar-plateau mechanism + substitution result specifically (the mechanism paper), saving the full dataset for ICPE. Short turnaround matches your window.
- **ACM e-Energy 2026** — plausible, publishes closely analogous GPU power papers, but its CFP artifact/reproducibility policy could not be verified (403 on automated fetch). **Someone needs to open this URL by hand before committing**: https://energy.acm.org/conferences/eenergy/2026/pages/cfp.php
- **No dedicated null-results venue exists in GPU/architecture/energy systems** (checked — only NetNeg for networking, one-off past workshops in NLP/CV). Your null result (Ridge model losing to constant frequency) and the substitution finding go into the main measurement paper as a clearly labeled subsection, not shopped separately.
- **What you need first, regardless of venue:** the model-comparison paper "Watt Counts" (arXiv 2604.09048, read in full) is a directly comparable, successfully-framed precedent — dataset-scale-first abstract, named open harness as a first-class deliverable, headline percentage up front. Copy that structure for your own abstract/intro rather than leading with methodology.

---

## 6. DO NOT BOTHER

- **Mining/enthusiast downclocking guides (Tom's Hardware, etc.)** — real community practice pointing toward a valley on GeForce cards, but zero methodology, zero stated N, memory-bound crypto workloads. Uncitable as evidence. Use only as a throwaway motivating anecdote in the intro if at all — do not build any claim on it.
- **Stachowski et al. 2021 blockchain DVFS paper** — plausibly relevant but blocked at 403, completely unverified. Don't chase unless you already have institutional/library access; low expected value for the retrieval effort.
- **GPU NoC / crossbar architecture papers (MICRO 2024 "Real GPU NoC," PACT 2020 NoC bottleneck)** — both snippet-only, both simulation- or latency-focused rather than DVFS/voltage-focused, neither found a voltage-driven plateau. Fine as one-sentence "NoC-vs-DRAM separability is known in GPU architecture generally" background color, but do not attribute any specific number to either without reading the actual PDF — both failed to render in the search session (size limits, missing pdftoppm).
- **AMD Infinity Fabric / chipsandcheese article** — read in full, but explicitly confirmed to contain no measured FCLK-vs-bandwidth sweep, only qualitative concern. Cite for one sentence ("this concern is recognized outside NVIDIA too") and nothing more — do not attribute a percentage to it.
- **Searching further for a "null results" GPU venue** — confirmed not to exist; this search is exhausted, don't re-run it.
- **Chasing a formal statistical reporting standard for n=1 chip studies** — confirmed absent from the literature (treated as a result to measure, not a reporting convention to cite). Nothing more to find here; move on.

===CRITIQUE===
Highest-value search not run: the actual power-vs-frequency curve shape check the list itself proposes in section 2 ("check whether your 5060 Ti's power curve turns up sharply past some threshold, mirroring/contrasting Tang's Tesla-vs-2080Ti explanation") — this is listed as an action but never executed, and it's a zero-new-measurement analysis over existing CSVs. Run it before writing anything about Tang. Query/action: plot P(f) for gemm and membw on the 5060 Ti sweep, fit for an inflection, compare slope below/above stock.

Snippet-only items that would change the write-up if actually read:
- #4 (UFS/uncore analogy): the 2.0 GHz / 13% figures are explicitly unverified against arXiv 2105.09642. If those numbers don't match, the "documented cross-architecture phenomenon" framing weakens to a looser analogy — read before quoting any number.
- #3 (nvidia-smi power error, arXiv 2312.02741): the ~4.5–5.4% figure is flagged "pull the RTX-specific figure before quoting" — the paper measures RTX 3090/A100, not Blackwell/5060 Ti. If the actual figure is A100-specific and much smaller/larger on consumer cards, the limitation-section number is wrong on the exact hardware this project cares about.
- Section 2's Tang metric-comparability check ("confirm Tang's own metric before contrasting") is listed as a 5-minute task but treated as already assumed true everywhere else in the doc (e.g., the "second published sweep, first affirmative" novelty claim rests on comparability holding).

Cost > return for a solo 3-month researcher:
- #5 (Leng et al. per-chip citation as n=1 template) — real but trivial value; don't spend more than the one sentence it already proposes.
- The GPGPU 2026 + ICPE dual-venue strategy in section 5 risks splitting effort across two submissions' formatting/framing on top of everything else still open (EDP, error bars, Tang mechanism check). With ~3 months solo, pick one primary venue now rather than dual-drafting; the list doesn't flag this as a decision point, but two audiences means two abstracts, two scoping passes.

Contradiction in the list itself:
- Section 2 says the counter-result is "partially bounded, not resolved" and explicitly instructs "do not resolve Tang et al. by assertion" — then Section 3/5 (and the top-level novelty framing) already assert "first affirmative below-stock efficiency valley on gaming-branded silicon" as if settled, before the proposed power-curve check has been run. The novelty claim in section 2 is stated as available to use ("defensible to state directly") while the same section says the underlying question is unresolved. Pick one: either run the power-curve check first and let it decide whether Tang is mechanistically explained (then the novelty claim is earned), or keep the novelty claim provisional in the draft language.