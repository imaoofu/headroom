<!-- dataset-grade: no -->

# Verbatim Afterburner profile store, RTX 5060 Ti, 2026-09-18

**Raw `.cfg` files copied byte-for-byte before applying Profile 3 for the fine-floor sweep.**
Not a decoded snapshot — the two JSON files beside this directory are those. This is the fallback
the run sheets prescribe when no decoder is run: **copy the raw files and record each SHA-256.**

| file | SHA-256 (first 16) | bytes |
|---|---|---|
| `MSIAfterburner.cfg` | `95E4BD5D28365639` | 2931 |
| `Profile1.cfg` … `Profile5.cfg` | `CADE1B0DA7D80656` (all five identical) | 31 each |
| `VEN_10DE&DEV_2D04&…cfg` | `E5CBE0ECD89D899C` | 32897 |
| `VEN_1002&DEV_13C0&…cfg` | `62CDA03FAC784488` | 131 |
| `VEN_0000&DEV_0000&…cfg` | `B0D8CB40FA778F0E` | 94 |

🔑 **The five `ProfileN.cfg` files are 31-byte stubs and all hash identically** — they hold no curve
data. Everything is in the per-device `VEN_10DE&DEV_2D04&…cfg`, which carries `[Startup]` plus
`[Profile1]`–`[Profile5]` sections.

## What Profile 3 contained, checked rather than assumed

`CLAUDE.md`'s rule is that **a slot number is not an identity** — P3 held an aggressive curve one
day and stock the next. So it was read before being applied:

| slot | PowerLimit | CoreClkBoost | MemClkBoost |
|---|---|---|---|
| Profile1 | 100 | −502296 | 2000000 |
| Profile2 | 111 | −502296 | 2500000 |
| **Profile3** | **100** | **0** | **0** ✅ stock |
| Profile4 | 111 | −502296 | 2500000 |
| Profile5 | 111 | −502296 | 2500000 |

✅ **Matches the 2026-09-09 record exactly** — every offset zero, `PowerLimit 100` = the 180 W
factory default. The `−502296` on the other four is the `CoreClkBoost = −502 MHz` this project has
recorded and not explained.

## Verified in application, three ways

1. Power limit **200 → 180 W** after applying P3.
2. Memory clock under load **13801 MHz**, not the 16301 of a memory-overclocked profile.
3. Peak core under free boost **~2557 MHz**, against Profile 4's ~2976.

⚠️ **Driver was 616.92** at snapshot time — the reboot that preceded this session picked up an
update from 616.64. Read it off the sweep JSON, never off a document.
