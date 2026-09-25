# Job 20: Section 2 XBAR source index

**Task, 2026-09-25.** Reopen the direct sources behind the former `[X]` marks in
`docs/drafts/section2-related-work-proposal.md`, index them in `docs/RELATED-WORK.md` §4,
and try the primary source behind GIGAZINE's `[N]` report. This is a source check, not
an independent replication of any hardware result. The paper was not edited.

## Findings and limits

| Source, author, source date | What the opened page establishes | What it does not establish |
|---|---|---|
| [Hardwareluxx post #184](https://www.hardwareluxx.de/community/threads/nvidia-rtx4000-undervolting-sammler.1325830/post-29706606), EleCtricStream, 2023-01-25 | The author reports an NVIDIA Inspector XBAR reading about 150 MHz below stock with RTX 4090 undervolting. | The author says no performance test was done. This is not evidence of an FPS or GB/s loss, nor a controlled voltage-only intervention. |
| [NVIDIA/open-gpu-kernel-modules #1266](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1266), Loong0x00, opened 2026-07-28 | On an RTX 5090, the author reports 256 to 173 average FurMark FPS with an XBAR maximum of 1493 MHz. The table reports a higher loaded core clock and unchanged memory clock. | Author-reported FPS under an XBAR cap does not measure GB/s or show the effect of a flattened core V/F curve. It is not independent replication. |
| [overclockers.ru forum post](https://forums.overclockers.ru/viewtopic.php?f=3&start=12980&t=642582), tolikmixx, 2026-08-18 13:47, edited 13:56 | The reply warns that Afterburner undervolting can cause an unseen XBAR ceiling while raising XBAR; it suggests mVolt+ XBAR ratio or setting an upper voltage limit there. | It is advice, not a controlled measurement of the ceiling or either workaround. It is a forum post, not an article. |
| [LACT #1147](https://github.com/ilya-zlobintsev/LACT/issues/1147), Loong0x00, opened 2026-08-10; [NVIDIA #1266](https://github.com/NVIDIA/open-gpu-kernel-modules/issues/1266), Loong0x00, opened 2026-07-28; [site note](https://loong0x00.com/notes/blackwell-xbar-physical-clock-domain/), Loong0x00, published 2026-08-13 | The two issue `user.login` fields are `Loong0x00`. The note identifies its author as `Loong0x00` and links to that GitHub profile. Treat these reports as one displayed-author research line. | Shared authorship does not prove the same physical RTX 5090 across reports, validate any measurement, or create independent corroboration. |
| [GIGAZINE](https://gigazine.net/gsc_news/en/20260608-rtx-5090-external-clock/), log1i_yk, 2026-06-08 | The news page attributes external-reference-clock work and partial XBAR adjustment by vBIOS swap to PickleRick. It links an [XtremeSystems article](https://xtremesystems.us/post/external-clock-generation-on-rtx-50-series). | The linked page rendered only a generic article shell, without PickleRick's text. The primary claim remains unverified and stays marked `[N]`; the news report supplies no independently checked GB/s result. |

The former `[X]` claims now have direct page support and are indexed **GPT-read,
pending Claude review**. The proposed §2.5.1 wording now labels the forum advice as
advice, the issue's result as FPS rather than bandwidth, and the GIGAZINE statement
as a news report. No sentence was retained as a verified primary-source claim when
its underlying primary text could not be read.

The update also exposed two stale statements: `RELATED-WORK.md` still said §4 began
with the August 2026 LACT issue, and the historical
`docs/PRIOR-ART-20260912.md` verdict table counted the site and LACT issue as
independent confirmation. Dated corrections were added at both locations. The
historical table remains visible with its correction above it.

## Access and verification record

All pages above were opened on **2026-09-25**. This job used direct URL opens,
not a new keyword search, so there is no search-query string to reproduce. The
Hardwareluxx #184 permalink resolves to page 7 and displays the numbered post.
The GIGAZINE link to `https://www.xtremesystems.us/post/external-clock-generation-on-rtx-50-series`
redirected to the non-`www` URL; both attempts displayed only a generic page shell.

The author check used these exact commands on 2026-09-25:

```text
gh api repos/ilya-zlobintsev/LACT/issues/1147 --jq '{url: .html_url, author: .user.login, created: .created_at, title: .title}'
gh api repos/NVIDIA/open-gpu-kernel-modules/issues/1266 --jq '{url: .html_url, author: .user.login, created: .created_at, title: .title}'
```

They returned `author: Loong0x00` with issue creation times
`2026-08-10T23:08:25Z` and `2026-07-28T15:17:06Z`, respectively. The site note's
GitHub link opens the same [Loong0x00 profile](https://github.com/Loong0x00).

Before writing, the repository gates passed: `python run_tests.py --quiet`
(1,049 checks, 33 suites), `python analysis/audit_claims.py`,
`python analysis/build_data_manifest.py --check`, and
`python analysis/verify_citations.py --check`. The test count is the local
2026-09-25 run, not a sample size for any source above.

## Remaining review

Claude should review the new §4 index entries and proposed §2.5.1 text before
that text enters the paper. The PickleRick primary article remains unreadable in
this access path, so the GIGAZINE attribution cannot be promoted to a direct
primary-source claim.

## Claude's review, 2026-09-25: accepted

**Spot-checked against the primary sources:**
- **The authorship of both GitHub issues:** `gh api` returns `Loong0x00` for #1147 (created
  2026-08-10T23:08:25Z) and #1266 (2026-07-28T15:17:06Z).
- **#1266's numbers, in the issue's own table:** FurMark 256 → 173 average FPS at an XBAR maximum
  of 1493 MHz, loaded core ~2952 against ~2588 MHz, MCLK 15001 in both.
- **Hardwareluxx #184:** dated 25.01.2023; *"150 Mhz weniger"*; *"Tests habe ich noch keine
  gemacht"*.

Those three entries are marked reviewed in `RELATED-WORK.md` §4. **Four are left pending, not
re-read here:** the Loong0x00 article, LACT #1147's content, the overclockers.ru post and
GIGAZINE.

**Two corrections to CLAUDE.md follow from this job, both applied:**
- *"on the same RTX 5090 … one chip"* was more than authorship shows;
- overclockers.ru is a forum post, not an article.
