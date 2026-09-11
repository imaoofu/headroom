# `kitverify-20260823` — the collection kit verified against the machine it was built on

<!-- dataset-grade: no -->

**Two runs, `gemm` and `membw` each, 2026-08-23**, on the 5060 Ti — the machine whose data the rest
of this repository is built from. The point was never the measurement: it was to check that
`RUN-ME.bat` on a USB stick produces the same numbers as the repository's own tooling before the kit
was carried to a machine nobody could debug on.

| run | configuration |
|---|---|
| `…kitverify-ogtune` | the original tuned profile |
| `…kitverify-idle` | idle / as-found |

## ⚠️ Read `CORRECTION.txt` in each directory before using either run

Both carry a correction written at collection time. **The `-idle` run is the one `CLAUDE.md`
discusses**: its `applied_settings` asserted that NVIDIA Instant Replay had re-enabled itself, and
that was an attribution written without evidence — the operator had switched it back on after a
guard test and confirmed so when asked. There is no software-hygiene finding in this data and none
should be written into the paper.

**Kept because the correction is the useful part.** A field whose entire purpose is accuracy was
filled in with a guess, roughly forty minutes after `CLAUDE.md` gained a warning against doing
exactly that.

## Why these are not dataset-grade

- Collected to verify tooling, not to answer a question.
- They predate the video-engine guard and the verified-quiet protocol in §5.4.4, so contamination
  is neither excluded nor measured.
- n=1 per configuration, and the configurations are not the current Afterburner profile set.

🔑 **They existed only on the USB kit until 2026-09-10**, when a hash comparison run before the drive
was reused found 28 files with no copy in the repository. See `data/collection-kit-logs/README.md`.
