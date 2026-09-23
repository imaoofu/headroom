# GPT findings/results from prompts

Raymond requested this archive on 2026-09-18 so GPT findings remain available in
Headroom after a conversation ends. Save future substantive Headroom prompt results
here and add a row to this index. This is a research record, not a second project
authority or automatic approval to change the paper.

| Date | Result | Evidence status |
|---|---|---|
| 2026-09-22 | [NVML clock-offset prior-art search](2026-09-22-nvml-offset-prior-art-search.md) | NVIDIA/tool documentation, first-hand community accounts, an August 2026 NVML tuning tool, and Guerreiro TPDS 2019 full text opened. Global curve shifting is prior art; the one-chip Blackwell pairing is a bounded observation, and the Guerreiro comparison is confounded by method and generation. Query/access log and limits recorded. No hardware run. ✅ **Reviewed by Claude:** 170tune verified at source (lines 590–605), including a floor-under-offset line GPT did not quote; the 4c 🔑 was narrowed in CLAUDE.md, the README and RELATED-WORK §10. |
| 2026-09-22 | [Activity A/B preflight review](2026-09-22-activity-ab-preflight.md) | Before collection, temporary scorer fixtures exposed an exact-2% false positive and scoring of active runs with no event log; code review found an incomplete-result verdict, weak stock gate, and generator lifecycle gaps. PowerShell 5.1 exit-code and AST probes passed. No GPU run or threshold edit. ✅ **Reviewed by Claude:** all five reproduced and fixed before collection, recorded under REGISTERED-PREDICTIONS §5. |
| 2026-09-22 | [Grid-aware achieved-clock count](2026-09-22-grid-aware-clock-count.md) | Corrected the prompt's run date: 10/13 came from the 09-15 RTX 2060 Super run, not the 09-18 RTX 5060 Ti runs. Reporting buckets now follow grid spacing; read-only tests cover five named runs and 404 coarse sweeps. No sweep run. |
| 2026-09-22 | [Directed DVFS literature follow-up](2026-09-22-directed-dvfs-literature-followup.md) | Table IV transcribed; five distinct indexed forward-citing works screened, 14 no-abstract records revisited, GreenMD details withdrawn as page-verified claims, and Wang's 20/30 mapping left unresolved. Primary-source and access limits recorded. |
| 2026-09-22 | [DOI citation verifier](2026-09-22-doi-citation-verifier.md) | Added offline DOI coverage and live CSL metadata comparison. All five RELATED-WORK §§8–9 DOI titles and complete author orders matched Crossref; GreenMD and Wang remain abstract-only. Live run reached all 13 registered DOIs. ✅ **Reviewed by Claude:** live check re-run clean; every read label checked against RELATED-WORK; the Schoonhoven label was tightened to "arXiv text read". |
| 2026-09-22 | [Precollection RTX 3070 Ti Session D scorer](2026-09-22-session-d-scorer.md) | Scorer and synthetic pass/fail/control fixtures written before Session D data; uses the existing sweep efficiency calculation, checks voltage extracts and the stock return, and records the original-registration versus amended-runsheet discrepancy. No hardware result or commit. ⛔ **Reviewed by Claude:** the optimum was compared by exact equality on achieved clocks, and an even 1170/1275 split scored as a fail. Both are corrected, with tests confirmed to fail on the original. GPT's registration-provenance finding is confirmed and recorded. |
| 2026-09-22 | [Measurement-file hash gate](2026-09-22-measurement-hash-gate.md) | Implemented line-ending-neutral SHA-256 checks for nonignored data CSV/JSON, CI wiring and 14 temporary-repository tests, including the 855 MHz voltage mutation. Reviewed by Claude: scope widened to every non-Markdown file under data/ (+76 logs and profile snapshots); baseline of 1,106 hashes checked against the committed blobs and accepted. |
| 2026-09-22 | [Adversarial audit: RTX 5060 Ti session results](2026-09-22-5060ti-session-results-audit.md) | Recomputed stock, P1/P4, membw and fine-floor CSV results; registration checked in a precollection git revision. Confirms the P1 median and floor bracket, but finds activity causation and recalibration of older controls unestablished. No hardware run. |
| 2026-09-22 | [GPT queue: forward citations, MP2884A datasheet, and blocked posts](2026-09-22-queue-literature-and-datasheet-check.md) | MPS register step sizes and sensed-voltage wording verified in the direct PDF; Reddit Methods 3 and 4 distinguished. A 109-record four-seed citation inventory includes 95 available abstracts; full-text novelty check and challenged forum pages remain open. Also reads Wang Figure 4 and documents an unresolved 20-versus-30 application mismatch. |
| 2026-09-21 | [Bench timestamp join and desktop-control gate](2026-09-21-bench-timestamp-join-and-desktop-gate.md) | Sweep CSV now preserves benchmark windows; synthetic clipped-clock and local-time checks passed, as did the 835-check suite and 284-claim audit. No hardware run: HWiNFO launch reached a Windows permission prompt. Live profile store matched the saved snapshot, while the card reported a 200 W limit rather than the 180 W stock limit. |
| 2026-09-20 | [Adversarial audit: the curve predictor and its regret metric](2026-09-20-curve-predictor-regret-adversarial-audit.md) | Headline table reproduced from 192 committed curves; held-out baselines, effective units, full-tune removal, grid and voltage-code sensitivity, later r10/fine-grid evidence, residual structure, V100 metric conversion, and git chronology checked. Finds a two-action lookup whose 2.90x advantage comes entirely from one configuration; no unseen configuration test exists. Lead pending independent recomputation. |
| 2026-09-19 | [Consumer-GPU DVFS artifact range and prior-art audit](2026-09-19-consumer-dvfs-artifact-range-audit.md) | Exact CSV grids, declared base clocks, hashes, raw boundary optima, author wording, GitHub reuse signals, and citation/search results checked. The roughly +/-11% description is correct; “authors say the artifacts cannot locate an optimum” and “widely reused” are too strong. No independent artifact-specific critique found. |
| 2026-09-19 | [Adversarial audit: does the reported V/F floor causally set the efficiency optimum?](2026-09-19-load-floor-causal-claim-adversarial-audit.md) | Repository data, run metadata, analysis code, and git chronology checked. Finds a strong configuration-level effect on one GB206 chip, but no isolation of physical voltage-floor mediation; the headline registration and 12-of-12 wording are overstated, the negative control is workload-level leaky, and the fourth GPU is undecidable. No new hardware run. |
| 2026-09-18 | [Adversarial audit: flattened V/F curve, XBAR clock, and the 300 GB/s plateau](2026-09-18-xbar-causal-claim-adversarial-audit.md) | Repository data/code and primary NVIDIA profiler documentation opened. Finds that the full causal chain is assembled from unmatched experiments, that the logged stock and flat runs use different MCLK, and that XBAR/throughput diverge before reported voltage does. No hardware reproduction or direct GB206 XBAR intervention. |
| 2026-09-18 | [NVIDIA GPU voltage quantisation: what the public documentation establishes](2026-09-18-nvidia-voltage-quantisation.md) | Public NVIDIA and controller documentation opened; no source establishes HWiNFO's exact physical voltage source or a universal 6.25 mV PWMVID step. Exact tested-board controller identities remain unresolved. |
| 2026-09-18 | [XBAR undervolting and bandwidth: expanded prior-art search](2026-09-18-xbar-prior-art.md) | Public-source search completed; exact combined result not located; substantial related observations and mitigations found. Hardware experiments were not independently reproduced. |
| 2026-09-18 | [Search coverage, supplementary sources, and unresolved access](2026-09-18-xbar-search-log.md) | Companion record with identifiers, read status, vocabulary coverage, and explicit retrieval gaps. |
| 2026-09-18 | [Earlier GPT outside-reader findings and subsequent project checks](../PRIOR-ART-20260918.md) | Existing canonical record, including later corrections and data checks. Indexed here rather than duplicated or moved, so existing links and correction history remain intact. |

## Saving future results

Use `YYYY-MM-DD-short-topic.md`. Give each record a descriptive title, the prompt
or a faithful task description, the result, evidence and source identifiers,
verification status, unresolved questions, and limitations. Preserve sample sizes
and distinguish source-reported measurements from independently checked results.

For research searches, record exact queries as they are run, access dates, what was
opened, and what could not be reached. If an earlier query transcript is unavailable,
say so; do not reconstruct it and label it an exact log. Keep supplementary search
details in a companion file when they make the main report hard to read.

Keep corrections dated and visible. Link existing canonical documents instead of
copying them into competing versions. An archive entry does not establish novelty,
prove a source's experimental claims, or update the paper automatically.

For a cold novelty check, finish the independent search before reading this archive
or the project's framing documents. Record when the cold-reader boundary ended.
The XBAR search below was completed before the assistant read `CLAUDE.md` to save
the results in the repository.

This directory is the destination for future results; it does not schedule searches
or collect unrelated conversations automatically.
