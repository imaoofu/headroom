# Consumer-GPU DVFS artifact range and prior-art audit

**Date:** 2026-09-19  
**Task:** Check whether an artifact-specific argument has appeared elsewhere: that the
public GTX 1080 Ti and RTX 2070 Super DVFS tables do not bracket an energy-efficiency
optimum because each core-frequency sweep spans only about +/-11% around the authors'
declared default. Check the sweep-width arithmetic and how closely the authors themselves
make that argument.

## Result

The width calculation is correct, subject to one wording correction: the repository calls
1800 and 1880 MHz the cards' **base core frequencies**. The paper calls its normalized
GTX 1080 Ti reference a **factory default**. These numbers should not be described as
NVIDIA reference-card specifications. The repository's table spells the newer model
“GTX 2070 SUPER”; this appears to be a labeling error, and this record uses the product's
RTX 2070 Super name while preserving the repository's `gtx2070s` filename.

| Artifact row | Core grid | Authors' declared base | Exact endpoints relative to base |
|---|---:|---:|---:|
| GTX 1080 Ti | 1600, 1700, 1800, 1900, 2000 MHz | 1800 MHz | -11.111% to +11.111% |
| RTX 2070 Super | 1680, 1780, 1880, 1980, 2080 MHz | 1880 MHz | -10.638% to +10.638% |

Thus “roughly +/-11% around each card's own declared default” is accurate. A more exact
description is 88.89-111.11% of the GTX 1080 Ti base and 89.36-110.64% of the RTX 2070
Super base. Both declared base values are measured grid points and the midpoints of their
five-point grids.

The stronger statement needs qualification. The artifacts can identify the best point on
their sampled grid. They cannot establish an **unconstrained** optimum when the best point
is on a boundary, because the curve has not been bracketed. A direct calculation of
`1 / (time * power)` from every released core/memory combination gave:

| Artifact | Workloads | Best core at low boundary | Interior | High boundary | Either core boundary |
|---|---:|---:|---:|---:|---:|
| GTX 1080 Ti | 30 | 8 | 4 | 18 | 26/30 |
| RTX 2070 Super | 20 | 9 | 7 | 4 | 13/20 |

At maximum memory clock rather than optimizing over the joint core/memory grid, the counts
are 8/4/18 for the GTX 1080 Ti and 10/6/4 for the RTX 2070 Super. The result is therefore
not an assertion that the missing optimum is always below the sampled range. On the GTX
1080 Ti, most boundary optima are at the **high** end. The defensible claim is that these
sparse grids often fail to bracket a workload's optimum. The categorical claim that the
two artifacts “cannot locate an efficiency optimum” is too broad for the 4/30 and 7/20
workloads whose best sampled core point is interior, and it must specify whether “optimum”
means a measured-grid optimum or an unconstrained physical optimum.

## What the authors actually say

The 2022 TPDS paper reports its real experiment on the GTX 1080 Ti, not on the RTX 2070
Super. It normalizes the real GTX 1080 Ti core range to a lower bound of 0.89 of factory
default and identifies 1800 MHz as the 1.0 reference. It then:

- attributes part of the modest 4.3% mean energy saving in the 20 real benchmarks to the
  narrow core- and memory-frequency intervals;
- expands the simulated core range down to 0.5 to study DVFS potential; and
- says its fitted optimum in both the narrow and wide cases is relatively low and close to
  the allowed minimum.

That is strong primary-source support for saying that the GTX 1080 Ti experimental range
constrains the observed opportunity. It is not a statement that the released artifact is
incapable of locating any optimum. The paper says it derives an optimum inside each allowed
interval. “The authors say the artifact cannot locate the unconstrained optimum” is an
interpretation of their narrow-range and near-boundary findings, not their stated conclusion.

This attribution is weaker still for the RTX 2070 Super. The repository declares that card's
base clocks and releases its table, but the paper's reported real-platform experiment and
the 0.89 normalized interval are explicitly GTX 1080 Ti results. I found no author text that
separately calls the RTX 2070 Super table too narrow or says it cannot locate an optimum.

There is also an unresolved mapping issue. The paper discusses 20 GTX 1080 Ti benchmarks,
whereas the released GTX 1080 Ti CSV contains 30 application names. Its statement that the
fitted optima are low cannot be mapped one-for-one to all 30 released rows from the paper
alone. The raw-table boundary calculation above should not be presented as a reproduction
of the paper's model-derived Figure 4.

## Is the argument made elsewhere?

I did not find an independent publication, issue, repository, forum post, or archived page
making this exact criticism of these two files. Exact-filename searches, repository-name
searches, the associated papers' citation graphs, and searches combining the cards' five
frequency values with “optimum,” “energy,” “narrow,” and “DVFS” returned the originating
repositories and papers, not an outside range-truncation critique.

The closest independent source I opened was Ali et al., *An Automated and Portable Method
for Selecting an Optimal GPU Frequency*, DOI `10.1016/j.future.2023.07.011`. It cites Wang
and Chu's 2020 performance-model paper and describes its scope as application performance;
it does not discuss the GTX 1080 Ti/RTX 2070 Super CSV ranges or argue that their grids miss
an optimum. Later papers such as DSO, DRLCap, and DVFO cite the 2020/2022 work for GPU DVFS
modeling or scheduling, but the accessible texts I checked likewise do not make the
artifact-specific range argument.

This is a search null, not proof that no such statement exists.

## Artifact identity and provenance

- Later collection: `HKBU-HPML/GPU-DVFS-Job-Schedule`, commit
  `7ae3c9c8ebe766909cc7e3ee6fa0c752c62154c5`.
- Original GTX 1080 Ti collection: `HKBU-HPML/NV-DVFS-Benchmark`, commit
  `bc70c555d590be38900eff55300d61dc18e56aea`.
- The GTX 1080 Ti CSV in the two repositories is byte-identical, SHA-256
  `e5d3a6804ba09704dac0cf8687255c9ad18302ba066ff4102d85401dd61fe468`.
- The RTX 2070 Super CSV SHA-256 is
  `b0b0434460c72fe482057a94ee562354243ff81cc44f8d407738d6e3f19b032f`.
- The GTX file has 600 rows: 30 applications x 5 core clocks x 4 memory clocks.
- The RTX file has 400 rows: 20 applications x 5 core clocks x 4 memory clocks.

These are two card-specific tables, but they are not two wholly independent artifact
lineages: the later repository republishes the earlier GTX 1080 Ti table unchanged and adds
the RTX 2070 Super table.

I also did not verify the phrase “widely reused.” GitHub code search for each exact filename
found only the source repository. On the access date, the later repository exposed 15 stars
and one fork; the organization-owned original exposed four stars and no forks. The associated
papers are cited, but citation of a paper does not demonstrate reuse of its CSV. Public reuse
could exist under renamed files, in unindexed repositories, or offline. Until downstream
users are identified, “public reusable artifacts” is supported and “widely reused datasets”
is not.

## Primary identifiers and sources opened

- Repository and declared base clocks:
  <https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/tree/7ae3c9c8ebe766909cc7e3ee6fa0c752c62154c5>
- GTX 1080 Ti CSV at the audited commit:
  <https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/7ae3c9c8ebe766909cc7e3ee6fa0c752c62154c5/csvs/gtx1080ti-dvfs-real-Performance-Power.csv>
- RTX 2070 Super CSV at the audited commit:
  <https://github.com/HKBU-HPML/GPU-DVFS-Job-Schedule/blob/7ae3c9c8ebe766909cc7e3ee6fa0c752c62154c5/csvs/gtx2070s-dvfs-real-Performance-Power.csv>
- Original benchmark repository:
  <https://github.com/HKBU-HPML/NV-DVFS-Benchmark/tree/bc70c555d590be38900eff55300d61dc18e56aea>
- Q. Wang et al., *Energy-Aware Non-Preemptive Task Scheduling With Deadline Constraint
  in DVFS-Enabled Heterogeneous Clusters*, DOI `10.1109/TPDS.2022.3181096`:
  <https://doi.org/10.1109/TPDS.2022.3181096>; accessible author preprint:
  <https://arxiv.org/pdf/2104.00486>
- Q. Wang and X. Chu, *GPGPU Performance Estimation With Core and Memory Frequency
  Scaling*, DOI `10.1109/TPDS.2020.3004623`:
  <https://doi.org/10.1109/TPDS.2020.3004623>
- G. Ali et al., *An Automated and Portable Method for Selecting an Optimal GPU
  Frequency*, DOI `10.1016/j.future.2023.07.011`:
  <https://escholarship.org/uc/item/3cz016cf>

## Search coverage and limits

Searches included exact filenames; both repository names; the exact five-point frequency
grids; the paper titles and DOIs; combinations of `GTX 1080 Ti`, `RTX 2070 Super`,
`optimum`, `optimal`, `energy efficiency`, `narrow`, `scaling interval`, `range`, `DVFS`,
and `dataset`; GitHub code, issue, and fork searches; general web search; and OpenAlex
citing-work lists for both associated papers. Relevant accessible citing texts were opened
when they appeared likely to discuss frequency selection or GPU energy optimization.

The IEEE DOI landing pages were intermittently inaccessible to the browsing tool. The
author-hosted/arXiv full texts were available for the key claims. I could not search private
repositories, non-indexed code, renamed copies, closed discussion groups, or offline material.
I did not read every citing paper in full; several were paywalled or unrelated scheduling
papers. Search-engine and GitHub indexes are incomplete. Accordingly, the external-prior-art
answer remains “not found in the searched record,” not “does not exist.”

## Independence note

This was not a cold novelty check. Earlier work in the same conversation had already exposed
the repository framing and authority file before this prompt arrived. The result is therefore
an adversarial audit with external searching, not an independent cold-reader result under
`docs/agents/NOVELTY-CHECK-BRIEF.md`.
