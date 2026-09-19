# GPT findings/results from prompts

Raymond requested this archive on 2026-09-18 so GPT findings remain available in
Headroom after a conversation ends. Save future substantive Headroom prompt results
here and add a row to this index. This is a research record, not a second project
authority or automatic approval to change the paper.

| Date | Result | Evidence status |
|---|---|---|
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
