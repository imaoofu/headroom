# DOI citation verification in the repository checker

**Task:** `docs/agents/GPT-PROMPT-NEXT.md` Job 4. I extended
`analysis/verify_citations.py` to register and check DOI bibliographic metadata,
and added offline tests in `analysis/test_verify_citations.py`. The DOI requests
use `https://doi.org/<doi>` with `Accept: application/vnd.citationstyles.csl+json`,
as [Crossref documents](https://www.crossref.org/documentation/retrieve-metadata/content-negotiation/).
This is publisher-deposited metadata; it does not establish what the papers say.

## The five DOIs in RELATED-WORK §§8–9

I fetched their CSL JSON on 2026-09-22 and compared the **complete title and
ordered family-name list** with `docs/RELATED-WORK.md`. The repository's abbreviated
short title `GreenMD` matches its full Crossref title; the other four titles
are complete there.
Crossref sometimes omits the accent in Tomás, so the comparison normalizes
accents and capitalization while preserving the name and order.

| DOI | Crossref title | Crossref author order | Result |
|---|---|---|---|
| [10.1016/j.jpdc.2022.03.004](https://doi.org/10.1016/j.jpdc.2022.03.004) | Decoupling GPGPU voltage-frequency scaling for deep-learning applications | Mendes, Tomás, Roma | Matches §8 |
| [10.1109/HPCA.2018.00072](https://doi.org/10.1109/HPCA.2018.00072) | GPGPU Power Modeling for Multi-domain Voltage-Frequency Scaling | Guerreiro, Ilic, Roma, Tomas | Matches §8 |
| [10.1109/TPDS.2019.2917181](https://doi.org/10.1109/TPDS.2019.2917181) | Modeling and Decoupling the GPU Power Consumption for Cross-Domain DVFS | Guerreiro, Ilic, Roma, Tomas | Matches §8 |
| [10.1145/3583590](https://doi.org/10.1145/3583590) | GreenMD: Energy-efficient Matrix Decomposition on Heterogeneous Multi-GPU Systems | Zamani, Bhuyan, Chen, Chen | Matches §9 |
| [10.1109/TSUSC.2023.3314916](https://doi.org/10.1109/TSUSC.2023.3314916) | Model-Free GPU Online Energy Optimization | Wang, Hao, Zhang, Wang | Matches §9 |

**No title or author-list disagreement was found for these five.** GreenMD and
the TSUSC paper remain **abstract-only** in the repository. The metadata check
does not promote either to a full-text read or verify the technical details
currently marked uncertain in §9.

## Guard behavior and scope

The offline `--check` scans live repository Markdown and fails if a DOI is
neither registered nor an explicit unread lead. At this run it found **14 DOI
identifiers: 13 registered citations and one declared lead**. The historical
search-log exemptions already used by the arXiv guard also apply to DOI
coverage; two additional identifiers occur only in those exempt files.
`--check` makes no network requests. `--live` fetches arXiv and DOI metadata;
unreachable records are reported as **unverified**, not citation errors.
Confirmed title or complete-author-order differences are errors with
`--live --check`.

The new offline tests exercise DOI forms, coverage failure for a removed
registration, the DOI request header and endpoint, title and ordered-author
mismatches, accent normalization, unreachable metadata, and the no-network
boundary for `--check`. The live command `python analysis/verify_citations.py
--live --check` reached all eight arXiv records and all 13 registered DOI
records, and reported no differences. No paper text was retrieved or assessed
for this task. No file under `data/` or `docs/PAPER_DRAFT.md` was changed.

## Review by Claude, 2026-09-22 — accepted, one label tightened

**Re-run here:** `--live --check` passes. All 13 DOIs resolve, and title and complete author order
match Crossref. 71 checks pass, including the ones that matter most: an unregistered DOI fails the
offline check, a wrong title or author order is detected, and `--check` makes no network call.

**Every `readStatus` was checked against what the repository itself records.** SAOU, Fan (ICPP
2019), Tang (e-Energy '19) and Zhang (EuroSys '24) are all marked **read in full** in `RELATED-WORK.md`.
GreenMD and TSUSC are abstract-only. The labels match.

**One label tightened.** Schoonhoven said *"full text read"* against the **published** PMBS DOI.
What was read in full is the arXiv preprint (2211.07260). The entry now says so, as the TPDS 2022
entry already did for its own preprint/published pair. The two can differ: for 2104.00486, the
preprint and the published version have different author orders.
