# Session E — the RTX 2060 Super fine floor sweep, and the boundary manipulation

**Work off this sheet at the machine.** Predictions for the manipulation are registered in
`docs/REGISTERED-PREDICTIONS.md` §4c. Part 1 applies nothing to the card and leaves nothing behind
— but it **does need an Administrator shell**, because locking clocks does.

**Why this card matters more than its size suggests.** No Turing voltage-frequency curve has ever
been *measured* in the ridge-point literature. Schoonhoven et al. can only read core voltage on
Ampere; their one Turing part, the Titan RTX, falls in the group where they **assume** a flat floor
and fit it from power (their Equation 3). Both ridge points they report are Ampere. **So this is the
first measured Turing floor**, and it is the architecture where this project's rule stops working.

---

## The stock curve, as measured on this card

From `20260912-142900_rtx2060s-lowrange` (60 MHz grid) and `20260912-114754_rtx2060s-asfound`
(105 MHz suite grid).

| core MHz | V | | core MHz | V |
|---|---|---|---|---|
| 405 | 0.644 | | **975** | **0.631 ← last floor point** |
| 465 | 0.644 | | 1035 | 0.637 ← **+6 mV, one sensor step** |
| 525 | 0.637 | | **1065** | **0.644 ← measured optimum** |
| 585 | 0.637 | | 1095 | 0.650 |
| 630–915 | **0.631** | | 1170 | 0.669 |
| | | | 1275 | 0.694 |

**Floor = 0.631 V across 345 MHz**, seven consecutive points from 630 to 975.
⚠️ **The curve is non-monotonic at the bottom** — 405–465 MHz read *higher* (0.644) than the floor.
Do not treat the lowest clocks as part of the floor.

### The ambiguity, stated precisely

**Read strictly**, the floor ends at **975 MHz** — the last point reading 0.631. Nearest suite grid
point is 960, which is **one step below the measured optimum of 1065**, so the rule *fails*.
**Allow a single 6 mV sensor step**, and the floor ends at **1035**, whose nearest grid point is
1065, and the rule *holds*.

🔑 **The entire verdict on this card turns on one sensor code.** That is what "undecidable" means
here, and it is why this session exists.

---

# PART 1 — the fine floor sweep (do this first; ~10–15 min, nothing applied)

**Grid: 900 → 1140 MHz in 20 MHz nominal steps**, 13 points. The tool will snap each to the nearest
supported clock; record what it actually locked, not what you asked for.

| | |
|---|---|
| workload | `gemm` |
| grid | 900, 920, 940, 960, 980, 1000, 1020, 1040, 1060, 1080, 1100, 1120, 1140 |
| what it decides | where voltage **first** leaves 0.631 V, to ±10 MHz instead of ±60 |
| applied settings | **none — stock** |

### 🛑 HWiNFO IS THE INSTRUMENT. Without it this run measures nothing.

**The sweep tool cannot read voltage — nothing in NVML can.** An exhaustive scan of field IDs
1–259 returns 44 readable fields and no voltage at any scale. **Every voltage number in this
project comes from an HWiNFO log**, joined afterwards by `join_hwinfo_voltage.py`. This session
exists to locate a voltage step, so a sweep run without HWiNFO logging is a wasted session.

`HWiNFO64.exe` **ships on the kit** and the kit's `HWiNFO64.INI` sets `SensorInterval=500`, so it
samples at **0.50 s**. Nothing to install.

⛔ **Start the log BEFORE the sweep and stop it AFTER.** One log must never span a settings
change — the join bins samples by core clock, so a log covering two configurations mixes them
silently. Part 1 is one configuration throughout, so one log covers it.

### The exact commands

⛔ **THE DRIVE LETTER IS THE KNOWN FAILURE MODE ON THIS EXACT CARD.** On 2026-09-12 a hand-written
invocation of this same script ran `D:\...\python.exe` against `F:\...\gpu_workload.py`. Python
started, failed to open the script, exited in 0.58 s, and the sweeper **timed an idle card at all
thirteen points and wrote a clean-looking CSV** — thirteen locked frequencies, no throughput, an
hour gone. See `failed-invocations/README.md`.

🔑 **THE SAME USB TAKES A DIFFERENT LETTER ON EVERY MACHINE, AND THAT IS THE WHOLE TRAP.** It mounts
as **`F:` on the authoring machine** and as **`D:` on the 2060 Super PC** — confirmed by the
successful 09-12 sweep, whose `workload_command` records `D:\headroom-kit\python\python.exe`. The
failed run mixed the target machine's `D:` with the authoring machine's `F:`. Past runs also record
`C:` and `F:\HEADRO~1`.

✅ **So bind the path ONCE and never type it twice.** Set `$kit` to whatever the kit mounts as on
the machine in front of you; every command below derives from it, so the interpreter and the script
cannot land on different drives. Check it with `Get-Volume`, do not assume it from this sheet.

✅ **And the guard that catches it is now on the kit.** Synced 2026-09-14 — `WorkloadResultVerdict.ps1`
was missing from `Sync-Kit.ps1`'s file list, so the sweep script's check for "did the benchmark
produce anything" had its caller but not its helper, and degraded to a printed NOTE. Fixed. The
sweep now **stops at the first frequency** if no benchmark JSON comes back, instead of burning the
rest of the run.

**1. Open PowerShell as Administrator**, and allow scripts for that window only:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
```

🛑 **`-Scope Process` only.** It applies to that window and is gone when it closes. Never
`LocalMachine` or `CurrentUser` on a machine that is not staying with you.

**2. Bind the kit path once — `D:` on the 2060 Super PC — and prove it is really there:**

```powershell
$kit = "D:\headroom-kit"
Test-Path "$kit\python\python.exe"; Test-Path "$kit\tools\frequency-sweep\gpu_workload.py"
```

⛔ **Both must print `True` before going further.** That one line is the entire defence against the
09-12 failure: it checks the two paths the sweep will actually use, on the machine it will use them.

```powershell
cd $kit
.\tools\Disable-QuickEdit.ps1
nvidia-smi --query-gpu=utilization.gpu,utilization.encoder,utilization.decoder --format=csv
```

Baseline under ~5%, encoder and decoder at **0**. Instant Replay off.

**3. Start HWiNFO logging.** Launch `D:\headroom-kit\HWiNFO64.exe` (it is on the kit — 10.9 MB,
beside `HWiNFO64.INI`), tick **Sensors-only**, then start CSV logging to:

```
D:\headroom-kit\results\2060s-finefloor-hwinfo.csv
```

**4. Run the sweep.** Both paths come from `$kit`, so the interpreter and the script cannot land on
different drives:

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -SessionLabel "rtx2060s-finefloor-gemm" -WorkloadCommand "$kit\python\python.exe $kit\tools\frequency-sweep\gpu_workload.py --workload gemm --json" -MinFrequencyMhz 900 -MaxFrequencyMhz 1140 -FrequencyCount 13 -AppliedSettings "stock, PL default, no OC - fine floor probe 900-1140"
```

⚠️ **Watch the first frequency.** If the workload cannot launch, the sweep now says so and stops
there rather than running the other twelve points against an idle card.

**5. Stop the HWiNFO log** when the sweep prints its summary. Copy **both** the sweep folder and
the HWiNFO CSV off the machine.

⛔ **KEEP THE RAW HWiNFO CSV.** The distilled extract holds one median per bin and throws away
exactly what the dither analysis below needs.

### ⚠️ Two things this sheet got wrong until 2026-09-14

**`-MeasureSeconds 60` was specified here and it is INERT.** The parameter's own documentation
says it "applies only when NO `-WorkloadCommand` is given; with a workload, sampling runs for as
long as it runs." A workload is given, so it would have changed nothing — and the sheet's claim
that throughput from this run is therefore incomparable with the 20-second sweeps was wrong in the
same stroke. **It is directly comparable**, provided the iteration count is the default.

**The sample-count arithmetic behind it was also wrong, in the useful direction.** It assumed ~40
HWiNFO samples per bin. The `lowrange` extract on this card records `sampleCount` of **67 to 165**,
because HWiNFO logs continuously across the whole fixed-work run rather than inside a measure
window. At 1095 MHz that is already 67 samples. **The dither analysis has what it needs at default
settings.** If more dwell is ever wanted the lever is `--iterations` on the workload, not
`-MeasureSeconds` — and changing it breaks comparability, which is the trade.

## ⚠️ The limit this sweep CANNOT beat, and what to do about it

**Finer frequency steps do not fix coarse voltage quantisation.** The sensor reports in ~6.25 mV
codes. If the true curve rises by less than one code across this range, no frequency resolution
resolves it — you would only be locating the first *observable* step, not the first *actual* rise.

✅ **But there may be a way through, and this run is the chance to test it.** The kit logs HWiNFO at
**0.5 s** (`SensorInterval=500`) across the whole fixed-work run, which on this card's `lowrange`
sweep gave **67 to 165 samples per frequency bin** at default iteration counts. If the true voltage
sits *between* two codes, a well-behaved sensor **dithers** between them, and the ratio of 0.631 to
0.637 samples estimates the sub-step voltage — resolution below one code, for free.

⛔ **Whether this sensor dithers at all is UNKNOWN.** The committed extracts hold one median per bin
(`n=1` per target), so nothing on disk can answer it. It may quantise hard and never dither, in
which case the idea is dead and that is itself worth recording.

🛑 **So: KEEP THE RAW HWiNFO LOG for this run.** Do not let it be cleaned up. The distilled extract
throws away exactly the information this technique needs — it is the one irreplaceable artifact
of the session.

---

# PART 1b — the DESCENDING sweep. ⚡ Run this while the card is still on the bench.

**Added 2026-09-15, after Part 1 ran.** Registered as §4d. Same grid, same settings, ~12 minutes,
nothing applied — the only thing that changes is the ORDER.

🔑 **Why it is now the most valuable 12 minutes available.** Part 1 found the voltage
**non-monotonic**: 0.644 V at 900 MHz falling to 0.631 at 975–1005, then rising to 0.662 at 1140.
But the sweep climbs in frequency while the card warms from **42.0 to 58.7 °C**, so on the falling
limb frequency and warm-up are perfectly collinear. On the rising limb they are not — temperature
has saturated within 3.2 °C while voltage climbs 31 mV — so that half is safe and the falling half
is not.

⛔ **And the falling limb is what sets where the floor BEGINS.** Every load floor this project has
measured, on all four cards, came from a low-to-high sweep. If the minimum is thermal, they all
inherit it.

```powershell
$kit = "D:\headroom-kit"; Test-Path "$kit\python\python.exe"; Test-Path "$kit\tools\frequency-sweep\gpu_workload.py"
```

Start a **new** HWiNFO log first (`…-finefloor-desc-hwinfo.csv`) — one log must never span two runs.

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -Descending -SessionLabel "rtx2060s-finefloor-desc-gemm" -WorkloadCommand "$kit\python\python.exe $kit\tools\frequency-sweep\gpu_workload.py --workload gemm --json" -MinFrequencyMhz 900 -MaxFrequencyMhz 1140 -FrequencyCount 13 -AppliedSettings "stock, PL default, no OC - fine floor probe 900-1140 DESCENDING order, thermal control for 4d"
```

✅ **`-Descending` did not exist until 2026-09-15 and had to be added.** The tool sorted its grid
ascending and walked it in that order with no way to vary it, which is why **every load-floor
measurement in this project shares the same warm-up confound**. The switch reverses the grid and
changes nothing else; the session JSON now records `sweep_order`, and a sweep with no such field is
ascending rather than unknown. Verified by dry run on the 5060 Ti — 1140 first, 900 last.

⚠️ **The kit needs re-syncing before this run.** The switch is in the repository; a kit synced
earlier does not have it and will reject `-Descending` as an unknown parameter.

| result | reading |
|---|---|
| minimum stays at **975–1005** | ✅ the shape belongs to the V/F curve; Part 1's Result 1 stands whole |
| minimum **follows the cold end** (now the top) | ⛔ it is thermal — and every floor extent in this project needs re-reading. The bigger finding. |
| partial movement | 🟡 both contribute; never quote a floor extent again without the sweep direction beside it |

🛑 **Keep this raw HWiNFO log too**, and this time the per-point temperatures are the independent
variable rather than a footnote.

---

## What Part 1 settles

| result | reading |
|---|---|
| voltage first leaves 0.631 V **at or below 1035** | the permissive reading was right; the rule **holds** on Turing and §5.5.7's "975 or 1035" resolves to 1035 |
| voltage holds 0.631 V **past 1065** | the rule **fails** on this card with the optimum inside the floor — a genuine counterexample, and the strongest single result available here |
| still unresolvable within one sensor code | the ambiguity is a **measurement** limit, not a silicon property — say exactly that, and the dither analysis above is the only remaining route |

---

# PART 2 — the boundary manipulation (only if Part 1 completes and time remains)

Registered as §4c, and deliberately as a **disjunction** — this is the one prediction here whose
interesting outcome is the negative one.

> **Reshaping the floor region on a card whose voltage leaves the floor 6 mV at a time will produce
> a floor end that is EITHER sharp enough to locate — in which case the optimum should track it —
> OR still undecidable, in which case the ambiguity is a property of the silicon rather than of the
> vendor's shipped curve.**

### The edit — shorten the floor, which is the safe direction

> **Set every curve point at or below 0.650 V to 810 MHz. Leave every point at 0.669 V and above
> exactly at stock.**

| curve point | stock clock | set to |
|---|---|---|
| ≤ 0.631 V | up to 975 | **810** |
| 0.637 V | 1035 | **810** |
| 0.644 V | 1065 | **810** |
| 0.650 V | 1095 | **810** |
| ≥ 0.669 V | 1170 → top | **unchanged** |

The floor end moves **975 → 810 MHz**, a −165 MHz shift, and — the point of the exercise — it
becomes a **sharp** end, because reaching anything above 810 now requires crossing to 0.669 V, a
**38 mV** jump rather than a 6 mV creep.

✅ **Safe by construction.** After the edit the card takes *more* voltage for every clock above
810 MHz than stock did. Instability is not reachable. You are dragging points down, never up.

**Prediction:** the median suite optimum moves from **1065 MHz** down toward **855 MHz** (the
nearest suite grid point above the new floor end).
⛔ If it does not move, the rule's attribution to the floor region fails on Turing — report it as the
headline.

### Sweep it on the suite grid

**855 → 2115 MHz in 105 MHz steps**, gemm and membw, so the optimum is comparable with the as-found
run of 2026-09-12. Hold iteration counts constant across both configurations, and **re-derive them
on this card first** — the 5060 Ti and 3070 Ti counts do not transfer.

**Order: stock → edit → stock.** Shorter than the 3070 Ti's A/B/B/A because this is the secondary
experiment; if the closing stock run does not match the opening one, the result is not interpretable.

---

## Before you touch anything

1. **Snapshot the Afterburner profile store verbatim** into `data/afterburner-profiles/` before any
   edit — this card has no decoded profile on file yet, so the snapshot is the only record.
2. **Preflight:** Instant Replay / ShadowPlay off; browsers, Discord, Steam, media players closed.
   Idle baseline **under ~5%**, encoder and decoder at 0%.
3. `tools\Disable-QuickEdit.ps1` first, and run from inside the kit directory.
4. Record the driver version off the sweep JSON, never off a document.

## After — before the card ships

5. **Revert to stock and VERIFY IT TOOK** three ways: power limit, memory clock under load, peak
   core against its stock ceiling. 🛑 A driver reset silently clears Afterburner offsets, so a card
   can report a tuned settings string while running stock silicon.
6. **Remove Afterburner and its profile store.** Part 1 leaves nothing behind; Part 2 does.

---

## If you only have time for one thing

**Do Part 1.** It applies nothing, needs no curve edit and no cleanup, it takes ten minutes, and it is
the first measured Turing voltage-frequency curve in this literature regardless of which way it
falls. Part 2 is the more interesting experiment and the more expensive one; Part 1 is the one that
would be a waste to leave undone with the card sitting on the bench.
