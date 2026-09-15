# Session D — the causal replication on the RTX 3070 Ti

**Work off this sheet at the machine.** Predictions are already registered in
`docs/REGISTERED-PREDICTIONS.md` §4 — do not read them for the first time here, and do not change
them after seeing a result.

**Why this session exists:** every confirmation of the load-floor rule on this card so far is
*observational*. Only the 5060 Ti has a causal arm, which makes the headline result n=1 chip. This
session makes it two chips and two architectures.

⚠️ **Use the SILENT BIOS.** Every number below is measured from the silent-BIOS runs of 2026-08-27.
The OC BIOS has a similar floor but the 1500/1545 boundary was established on silent, and the
prediction is derived from it.

---

## The stock curve, as measured on this card

Not from a spec sheet — read out of `hwinfo-silent*/…_voltage.csv` in this directory.

| core MHz | measured V | | core MHz | measured V |
|---|---|---|---|---|
| 855 | 0.819 | | 1455 | 0.812 |
| 960 | 0.819 | | 1485 | 0.812 ← **measured optimum** |
| 1065 | 0.812 | | **1500** | **0.812 ← floor ENDS** |
| 1170 | 0.819 | | 1545 | 0.831 ← first rise |
| 1275 | 0.819 | | 1590 | 0.850 |
| 1380 | 0.812 | | 1695 | 0.894 |
| 1410 | 0.812 | | 1800+ | 0.931, **clips to ~1763** |

**Floor voltage 0.812–0.819 V** (±6 mV is one sensor step, so treat these as one value) **held
across 645 MHz**, 855 → 1500. Median suite optimum **1485 MHz**, 7 of 12 workloads picking it —
one grid step below the floor end, exactly as the rule says.

🔑 **The card is POWER-CAPPED at ~1763 MHz.** Only ~263 MHz of usable range exists above the floor
end. That single fact constrains the negative control below, and it is why this session's control
is smaller in magnitude than the 5060 Ti's 570 MHz. Say so in the write-up rather than quietly
comparing them.

---

## The two edits

Both are in the **safe** direction. Neither raises voltage, neither raises the power limit, neither
touches memory. In curve-editor terms you are dragging points **down**, never up.

### EDIT 1 — shorten the floor (this is 4a)

> **At every curve point at or below 0.819 V, set the clock to 1200 MHz. Leave every point above
> 0.831 V exactly at stock.**

Stock reaches 1500 MHz at 0.819 V; after the edit it reaches only 1200 MHz there, so voltage must
begin rising at **1200 instead of 1500** — the floor end moves **−300 MHz**.

| curve point | stock clock | set to |
|---|---|---|
| ≤ 0.812 V | ~1500 | **1200** |
| 0.819 V | 1500 | **1200** |
| 0.831 V and above | 1545 → 1763 | **unchanged** |

✅ **Why this is the safe direction, and why it is also the better experiment.** After the edit the
card uses *more* voltage for any given clock than stock, so instability is not possible by
construction. And the 5060 Ti manipulation moved the floor **up** (+465 MHz); moving it **down**
here tests the same claim in the opposite direction, which rules out "any curve edit pushes the
optimum upward". A same-direction replication could not do that.

**Registered prediction (4a):** the median suite optimum moves down from **1485 MHz** to the grid
point nearest the new floor end — **1170 or 1275 MHz** on the 105 MHz suite grid.
⛔ No movement, or upward movement, **refutes the causal claim on a second chip** and is the
headline if it happens.

### EDIT 2 — the negative control (this is 4b)

> **Flatten everything from 0.831 V upward to a constant 1500 MHz. Leave every point at or below
> 0.819 V at STOCK (i.e. reaching 1500 MHz).**

| curve point | stock clock | set to |
|---|---|---|
| ≤ 0.819 V | ~1500 | **unchanged (stock)** |
| 0.831 V | 1545 | **1500** |
| 0.850 V | 1590 | **1500** |
| 0.894 V | 1695 | **1500** |
| 0.931 V and above | ~1763 | **1500** |

That is a **−263 MHz** change at the top, which is all the range this card has above its floor.

**Registered prediction (4b):** the optimum stays at **1485 MHz**. The whole floor region is
untouched, so if the optimum moves, the rule's attribution to the *floor* region is wrong.

⚠️ **Expect the top of the sweep to clip.** Every target above 1500 will achieve ~1500. That is
intended and is the evidence the edit took — it is not a failed run.

🔑 **Run the control or do not run the session.** A manipulation without its control is worth well
under half the pair. If time runs short, drop a replicate, never Edit 2.

---

## Order of operations — A/B/B/A

Drift between sessions on one unchanged configuration has been measured at ~1.47% on `gemm`, which
is larger than several effects this project reports. A/B/B/A brackets it.

| # | config | workloads | why |
|---|---|---|---|
| 1 | **stock** | gemm, membw | today's baseline — do NOT reuse the 08-27 sweeps |
| 2 | **Edit 1** | gemm, membw | the manipulation |
| 3 | **Edit 1** | gemm, membw | replicate, catches within-config spread |
| 4 | **stock** | gemm, membw | closes the bracket; must match run 1 |

Then, if time remains: **Edit 2**, gemm + membw, once.

⛔ **If run 4 does not come back to run 1 within ~1.5%, the session is drift-contaminated** and the
manipulation result is not interpretable. Report that rather than the effect.

**Grid: hold the suite grid constant across every run — 855 to 2115 MHz in 105 MHz steps.** A grid
that changes between configurations breaks the fixed-work property that makes duration a valid
performance metric.

⚠️ **Iteration counts must be re-derived on this card** and then held constant across all runs.
`SUITE-ITERATIONS.md` holds 5060 Ti counts and they do not transfer. Calibrate first; it needs no
elevation.

---

## The exact commands, and the one thing the kit does NOT have

✅ **The sweeps go through `Collect.ps1`.** This card's original suite used band **852–2130 MHz,
13 points, settle 8, measure 20**, which is the kit's default band on this GPU — so no explicit
frequency arguments are needed, and matching the original collection is what makes the comparison
valid.

```powershell
cd <KIT>
.\Calibrate-Suite.ps1                     # FIRST. Iteration counts are per card.
.\Collect.ps1 -Label "rtx3070ti-sessiond-stock-1" -AppliedSettings "stock, silent BIOS" -Iterations <from calibrate>
```

🛑 **RUN HWiNFO LOGGING ACROSS EVERY SWEEP.** `HWiNFO64.exe` ships on the kit; its `HWiNFO64.INI`
sets `SensorInterval=500`. NVML exposes no voltage at all, so **HWiNFO is the only evidence that a
curve edit actually took** — and a driver reset silently clears Afterburner offsets, which would
otherwise produce a whole sweep of stock silicon wearing a tuned settings string.

⛔ **A separate log per configuration.** The join bins samples by core clock, so one log spanning
stock and Edit 1 mixes two curves into one table with nothing to separate them. Stop the log at
every curve change and start a new file.

Then repeat with `-Label ...-edit1-2`, `...-edit1-3`, `...-stock-4` after each curve change, and
`...-edit2` for the control. **`-AppliedSettings` must describe the curve actually applied** — it is
the field nothing can reconstruct afterwards, and the reason the earliest tuned data in this project
is unusable.

⛔ **AFTERBURNER IS NOT IN THE KIT AND WILL NOT BE.** The kit installs nothing and leaves nothing
behind; that is its whole design. A manipulation needs Afterburner present on the target machine,
which means **installing it, applying curves, and removing it and its profile store afterwards**.
That is a materially larger footprint than a stock sweep and it is the part to plan for.

⚠️ **There is no script that snapshots a profile store.** The one committed snapshot
(`data/afterburner-profiles/5060ti-profiles-20260908.json`) was produced ad hoc and only
`predict_from_curve.py` reads it. For this card, **copy the raw `Profiles\*.cfg` verbatim into
`data/afterburner-profiles/` and record each file's SHA-256** — that satisfies the reconstruction
purpose with no tooling, and the device ID in the filename identifies the card.

## Before you touch anything

1. **Snapshot the Afterburner profile store verbatim** into `data/afterburner-profiles/` before the
   first edit. A slot number is not an identity — this convention exists because P3 held an
   aggressive curve one day and stock the next.
2. **Record the BIOS position** (silent) in `-AppliedSettings`, along with driver version read off
   the sweep JSON rather than from any document.
3. **Preflight:** Instant Replay / ShadowPlay **off**; browsers, Discord, Steam, media players
   closed. Verify idle baseline **under ~5%** and encoder/decoder at 0%. A passing 10% guard is not
   enough — a 6% baseline still cost 10.3% at 1545 MHz once.

## After the manipulation runs — before the card ships

4. **Stability protocol** on the final configuration. Say "no failure observed in thirty minutes",
   never "stable".
5. **Revert to stock and VERIFY IT TOOK**, three ways: power limit reads stock, memory clock under
   load reads stock, peak core reaches its stock ceiling. 🛑 **A driver reset silently clears
   Afterburner offsets**, so a card can report a tuned settings string while running stock silicon —
   that failure has already happened once in this project and would have produced a whole sweep of
   mislabelled data.
6. **Remove Afterburner and its profile store.** The collection kit installs nothing and leaves
   nothing behind; this session does, and that is the part to undo.

---

## What each outcome means

| result | reading |
|---|---|
| optimum moves to 1170/1275, control unmoved | ✅ **The causal claim replicates on a second chip and architecture.** This is the sentence the paper cannot currently write. |
| optimum moves, control ALSO moves | ⛔ The attribution to the floor region is wrong. Bigger finding than a clean pass, and it must be reported. |
| optimum does not move | ⛔ Refutes the causal claim off the 5060 Ti. Report as the headline; the 5060 Ti result becomes single-chip. |
| run 4 ≠ run 1 | ⚠️ Drift-contaminated. Report nothing about the effect. |

⚠️ **Whatever happens, this is still one chip per architecture.** A successful replication makes the
claim "causal on two chips across two architectures", not "general". The scope sentence in the
paper — *strong within-chip causal evidence, generalisation uncertain* — widens; it does not
disappear.
