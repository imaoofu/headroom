# `afterburner-profiles` — verbatim snapshots of the tuning profiles the sweeps were taken under

<!-- dataset-grade: no -->

Not sweeps and not measurements. These are **snapshots of machine configuration**, kept so that a
configuration referenced by a sweep can still be reconstructed after the operator changes it.

## Why this exists

`docs/AFTERBURNER-PROFILES.md` tabulates the five profiles at five sampled voltages. That is enough
to tell them apart and **not** enough to rebuild one. Each curve has **127 points**, and the
operator edits these profiles by hand between sessions.

The specific risk this guards against was raised on 2026-09-08: the plan to **raise Profile 4's
plateau from 3015 to 3030 MHz** so it matches Profile 5's, which is a good experimental control —
it removes the top-clock difference and leaves the low-band voltage shape as the only variable
between them. But it also means **"Profile 4" would refer to two different configurations either
side of that edit**, and the `a1`/`a2` legs of the 2026-09-08 ABBA run measured the earlier one.

A slot number is not an identity. This file is what makes the identity recoverable.

## Contents

`5060ti-profiles-20260908.json` — all five slots plus `[Startup]`, captured before any edit:

- `power_limit_pct`, `core_clk_boost_khz`, `mem_clk_boost_khz` as stored
- `vf_curve_hex` — the raw blob, so a profile can be restored exactly
- `curve_points` — all 127 decoded points per profile as
  `{voltage_mv, base_mhz, offset_mhz, applied_mhz}`
- `source_sha256` of the whole cfg, so a later snapshot can be compared without diffing curves

`[Startup]` holds empty values — no settings, i.e. stock. **It is not reachable from the command
line**, which is why applying stock programmatically is currently impossible and why a slot has to
be sacrificed to get one.

## How to use it

- **To identify what a sweep ran under:** match the sweep's date against a snapshot, then the
  snapshot's curve against the `applied_settings` string.
- **To restore a profile after an edit:** the `vf_curve_hex`, power limit and memory boost are
  everything the cfg stores for that slot.
- **To check whether anything changed:** compare `source_sha256` between snapshots. Cheaper and
  stricter than comparing curves.

**Take a new snapshot whenever a profile is edited**, named by date. Do not overwrite an existing
one — the whole point is the history.

## Known decoder caveat

A naive stride-3 read of the curve blob mispairs at one record — the boundary between the
zero-offset and non-zero-offset regions — and produces an impossible ~6000 MHz point near 937 mV.
The `curve_points` here are written as decoded, including that artifact, because filtering during
capture would make the snapshot lossy. **Filter on read** to the card's supported range
(≤3090 MHz, the top of its supported-clock table).
