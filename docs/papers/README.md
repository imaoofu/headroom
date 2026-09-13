# `docs/papers/` — local copies of the sources

**PDFs in this directory are gitignored and are NOT redistributed.** The index with every link is
[`../RELATED-WORK.md`](../RELATED-WORK.md); this directory only holds whatever has actually been
downloaded onto a given machine, so a paper here on one machine will be absent on another.

That is deliberate. `data/raw/` follows the same rule — the V100 CSVs are fetched rather than
committed because their license was never checked — and a paper PDF is a stronger version of the
same problem.

## Getting one back

Every entry in `RELATED-WORK.md` carries a link. Two are known to be awkward:

- **Mei, Wang, Chu 2017 survey** — ScienceDirect returns HTTP 403. Needs an institutional login.
- **Mei et al., HotPower 2013** — `comp.hkbu.edu.hk` returns 403 to automated fetches. The copy read
  on 2026-09-13 was downloaded by hand in a browser. ⚠️ It is a **scanned image with no text layer**,
  so it cannot be grepped or extracted; render the pages to images to read it.

## Reading a scanned PDF in this repo

`pymupdf` is available. There is no `pdftoppm`, so the built-in PDF reader cannot render pages.

```bash
python -c "import pymupdf, sys; d=pymupdf.open(sys.argv[1]); [d[i].get_pixmap(dpi=190).save(f'page{i+1}.png') for i in range(d.page_count)]" docs/papers/<file>.pdf
```
