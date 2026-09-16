# Weekend plan — everything that needs Raymond at a machine

**Written 2026-09-16 for the weekend of 19–21 September.** Three cards reachable at once, which has
not happened before and may not again: **RTX 3070 Ti**, **RTX 2060 Super**, **RTX 5060 Ti** (local).

🔑 **This list is ONLY the hardware-bound work.** Everything else — the paper edits, the proposal,
the dataset README — is in `docs/TODO-20260915.md` and none of it needs a card. Do not spend bench
time on anything that can be done at a desk.

🛑 **Every timing below is measured, not estimated.** Suite durations come from the two
twelve-workload suites already collected (60.6 and 64.0 min); the fine sweep from the 2026-09-15
run (12.4 min); the pair from `silent-asfound` and `rtx2060s-asfound` (8.4 and 13.4 min).

---

## The honest budget

| block | measured time | card |
|---|---|---|
| Suite calibration | ~10 min | per card, once |
| **12-workload suite** | **~62 min** | any |
| gemm + membw pair | ~11 min | any |
| 13-point fine sweep | ~12 min | any |
| Stability soak | 30 min + setup | any |
| Afterburner install + snapshot | ~15 min | shop machines only |
| One curve edit | ~10 min | by hand |
| Revert, verify, uninstall | ~20 min | shop machines only |

⚠️ **Preflight is ~3 minutes and it is per RUN, not per machine.** Instant Replay went 0% → 14%
inside one session once because someone switched it back on. Re-check every time.

---

# 🥇 SATURDAY — the RTX 3070 Ti. This is the day that matters.

**`data/frequency-sweeps/rtx3070ti-20260825/SESSION-D-RUNSHEET.md`. Predictions §4a–4b, registered.**

🔑 **It is the only item on this list that changes what the paper can claim** — one chip becomes two
chips and two architectures, which is the weakness a reviewer names in thirty seconds.

⛔ **Read the run sheet at the machine. It was wrong until 2026-09-16 and the fix matters:** the
table said `gemm, membw`, but 4a is registered on the **median suite optimum** over twelve
workloads. Two workloads cannot test it. **Every configuration is a full suite, ~62 minutes.**

### Order, ~5½ hours including everything

| # | what | time |
|---|---|---|
| 0 | Install Afterburner, **snapshot `Profiles\*.cfg` verbatim + SHA-256** | 15 min |
| 1 | `Calibrate-Suite.ps1` on **stock** — write the 12 numbers down, never re-run | 10 min |
| 2 | **Stock suite** — today's baseline, do not reuse the 08-27 sweeps | 62 min |
| 3 | Apply **Edit 1** (≤0.819 V → 1200 MHz, everything ≥0.831 V untouched) | 10 min |
| 4 | **Edit 1 suite** — the manipulation | 62 min |
| 5 | Apply **Edit 2** (flatten ≥0.831 V to 1500, floor region untouched) | 10 min |
| 6 | **Edit 2 suite** — the negative control | 62 min |
| 7 | Revert to stock, **verify it took three ways** | 10 min |
| 8 | **Stock suite** — closes the bracket, must match run 2 | 62 min |
| 9 | 🆕 **Descending stock fine sweep**, `-Descending` — tests §4d on a third architecture | 12 min |
| 10 | Uninstall Afterburner and its profile store | 10 min |

⛔ **Run the control or do not run the session.** A manipulation without its control is worth well
under half the pair. **The Edit-1 replicate is what got dropped**, not Edit 2 — runs 2 and 8 bracket
drift between them, which is most of what the replicate was doing.

✅ **Both edits are safe by construction.** After either, the card takes *more* voltage for a given
clock than stock. You are dragging points down, never up. Instability is not reachable.

🛑 **A driver reset silently clears Afterburner offsets.** If one happens mid-suite, that suite is
stock silicon wearing a tuned settings string. Watch for it and re-run rather than keep the data.

**Separate HWiNFO log per configuration** — the join bins by core clock and one log spanning two
curves mixes them with nothing to separate them afterwards.

---

# 🥈 SUNDAY MORNING — the RTX 2060 Super, ~3½ hours

## 2a. Part 1b — the descending fine sweep. **12 minutes. Do this first.**

`SESSION-E-RUNSHEET.md` Part 1b, registered §4d. Stock, nothing applied, nothing to clean up.

⚠️ **Lower stakes than it looked on 09-15.** The confound has been bounded from existing data: the
3060's floor is flat across a **10.2 °C** warm-up, moving less than one 6 mV code, while the 2060
Super fell 13 mV across 13.5 °C. **The flat floors are probably genuinely flat.** This now tests a
card-specific oddity, not a project-wide invalidation. Still cheap, still worth it.

## 2b. Part 2 — the boundary manipulation (§4c), ~3 hours

Registered as a **disjunction**: either the floor end becomes sharp enough to locate and the optimum
tracks it, or it stays undecidable and the ambiguity belongs to the silicon rather than the vendor's
curve. **Both outcomes are publishable**, which is why it is worth the time.

| # | what | time |
|---|---|---|
| 1 | Calibrate on this card (the 3070 Ti numbers do not transfer) | 10 min |
| 2 | **Stock suite** | 64 min |
| 3 | Apply the edit (≤0.650 V → 810 MHz, ≥0.669 V untouched) | 10 min |
| 4 | **Edit suite** | 64 min |
| 5 | Revert, verify, **stock suite** to close | 64 min |
| 6 | Uninstall Afterburner | 10 min |

⚠️ **The edit's real point is that it makes the floor end SHARP** — reaching anything above 810 MHz
then requires crossing to 0.669 V, a **38 mV** jump instead of a 6 mV creep.

🔑 **If Saturday overran, do 2a and skip 2b.** Part 1b is 12 minutes and settles a registered
prediction; Part 2 is three hours for a secondary experiment.

---

# 🥉 SUNDAY AFTERNOON — the RTX 5060 Ti (local, no scheduling pressure)

**This card is always reachable, so it is the overflow.** Do it only once the two shop cards are
done — but these are real boxes and two of them are cheap.

## 3a. 🆕 Fine-resolution floor re-examination. **12 min. Highest value here.**

**The 0.720 V floor rests on a 158 MHz grid — three points.** The 2060 Super looked flat at 60 MHz
and turned out non-monotonic at 15. ⚠️ Nothing says the 5060 Ti hides the same shape, and its flat
reading across 5.1 °C is mild evidence against — but **the most load-bearing number in the project
has never been measured at fine resolution.**

```powershell
.\tools\frequency-sweep\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-finefloor-gemm" -WorkloadCommand "$kit\python\python.exe $kit\tools\frequency-sweep\gpu_workload.py --workload gemm --json" -MinFrequencyMhz 1380 -MaxFrequencyMhz 1760 -FrequencyCount 13 -AppliedSettings "stock Profile 3, PL 180 W default"
```

✅ **Band verified by dry run 2026-09-16, and it lands well.** Targets come out
`1380, 1410, 1440, 1470, 1507, **1537**, 1567, 1597, 1627, 1665, 1695, 1725, 1755` — **exactly on
the declared floor end of 1537**, with four points across the 1537→1702 gap where there is currently
no measurement at all. ~31 MHz steps against the present 158.

🛑 **CHECK THE POWER LIMIT BEFORE THIS RUN.** The same dry run reported **200.00 W enforced**, not
the 180 W stock default — so the local card is **not currently on Profile 3**. Apply stock, verify
it took (power limit reads 180, memory under load 13801 not 16301), and only then sweep. A "stock"
fine floor measured on a tuned card would quietly replace the number it is meant to confirm.

🛑 **HWiNFO log, and join with `--clock-tolerance 7`** — the ±25 MHz default will share samples on
a grid this fine, and it now refuses rather than doing it silently.

## 3b. 🆕 Descending twin of 3a. **12 min.** Same band, add `-Descending`.

Together 3a and 3b settle whether the project's headline floor is flat, sharp, and order-independent
— on the card the whole causal result rests on, in under half an hour.

## 3c. The two floor-ladder rungs. **~2¼ hours.** Registered, never built.

Turns the causal result from *directional* into *quantitative* — "the optimum moves
**proportionally**" — which is the half hardest to pre-empt. Registered prediction: **at least 7 of
12 workloads land individually on the predicted grid point on each rung.** So each rung is a full
suite: 2 × 62 min, plus the profile building.

⚠️ **No ladder profile is stability tested, and none may resemble the 875 mV @ 3 GHz that crashed
the driver.** Build them in the safe direction only.

## 3d. The NVML clock-offset validation pair. ⚡ **~25 min.**

Designed 2026-09-09, never run. Power at a locked *f* with a **−300 MHz** offset against power at
*f*+300 with none. ⛔ **The write has never been exercised on this card** — reading back works, and
that is all. **Claim nothing about it until this runs.** Negative offsets are the safe direction.

## 3e. The >30-minute stability soak. **1–2 h, unattended.**

Every tuned configuration behind the headline numbers has been soaked for exactly thirty minutes,
and undervolt failures routinely take hours to surface. ✅ **This one runs while you do something
else** — start it last and leave it. Say "no failure observed in N minutes", never "stable".

---

## If everything lands

| box | what it closes |
|---|---|
| 3070 Ti Session D | the causal claim becomes **two chips, two architectures** |
| §4b negative control | the attribution to the *floor* region, on a second chip |
| §4d × 3 cards | sweep order stops being an unexamined confound anywhere |
| §4c disjunction | the Turing boundary condition, either way |
| 5060 Ti fine floor | the project's most load-bearing number, finally measured finely |
| Floor ladder | *directional* → **quantitative** |
| NVML offset | a capability currently claimed on a read-back alone |
| Long soak | "no failure in thirty minutes" becomes a real number |

**That is eight registered or open items, and seven of them cannot be done without a card in front
of you.**

---

## The rules that do not bend

1. **Preflight every run.** Instant Replay off, encoder and decoder 0, baseline under ~5%. A 6%
   baseline once cost 10.3% at 1545 MHz.
2. **`-AppliedSettings` describes the curve actually applied.** Nothing reconstructs it later. This
   is why the earliest tuned data in this project is unusable.
3. **Snapshot the profile store before the first edit.** A slot number is not an identity — P3 held
   an aggressive curve one day and stock the next.
4. **One HWiNFO log per configuration.** Never one spanning a change.
5. **Bind `$kit` once** and derive every path from it. Mixing `D:` and `F:` in one command line has
   already cost an hour on the 2060 Super.
6. **Revert and verify three ways before any card ships** — power limit, memory clock under load,
   peak core against its stock ceiling. Then remove Afterburner and its profile store.
7. **A null is a result.** If the optimum does not move on the 3070 Ti, that is the headline and it
   gets written up as one.
