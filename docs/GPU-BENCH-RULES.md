# GPU bench rules — shared by every card's list

**Written 2026-09-22.** The protocol that applies to every run on every card. This is not a to-do list.
**The to-do lists are per card:**

| card | list | expires? |
|---|---|---|
| RTX 5060 Ti (local machine) | [`GPU-WORKLIST-5060TI.md`](GPU-WORKLIST-5060TI.md) | ❌ never |
| RTX 3070 Ti (shop machine) | [`GPU-WORKLIST-3070TI.md`](GPU-WORKLIST-3070TI.md) | ✅ ships, date unknown |
| RTX 2060 Super (shop machine) | [`GPU-WORKLIST-2060S.md`](GPU-WORKLIST-2060S.md) | ✅ ships, date unknown |

Non-GPU work is in [`TODO-20260918.md`](TODO-20260918.md). ⛔ **The combined `GPU-WORKLIST.md`,
`5060TI-SWEEP-QUEUE.md` and `WEEKEND-PLAN-20260919.md` were removed 2026-09-22.** Their open items
are in the card lists; the rest is in git history (`git show 994093f:docs/GPU-WORKLIST.md`).

---

## Which card first

**A card that leaves outranks one that does not**, whatever the items' importance: a result that
cannot be collected later is not comparable to one that can. Within a card:

| tier | rule |
|---|---|
| **0** | the card leaves |
| **1** | it gates other work |
| **2** | something in the paper is wrong or unsupported right now |
| **3** | it adds precision or completeness |

---

## The preflight — before every block

```powershell
nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader
nvidia-smi pmon -c 5 -s u
```

1. **The power limit must match the configuration you think is live.** A settings string is not
   evidence.
2. **Baseline under ~5%, read from `pmon`, not the aggregate.** `pmon` names the process.
3. **Instant Replay / ShadowPlay off**, encoder and decoder at 0. It is invisible at idle and once
   cost 10.3% at 1545 MHz.
4. ⛔ **Then leave the machine alone.** On 2026-09-18 the operator's own test suite beside a sweep
   cost **9.38% at every point** after a clean preflight. A passing preflight says nothing about the
   run.

---

## Curves — building, saving, applying

1. **Snapshot the Afterburner profile store before the first edit**, dated, never overwriting an
   older snapshot, into `data/afterburner-profiles/`. The curves live in the `VEN_*.cfg` file, not
   in `ProfileN.cfg`.
2. 🛑 **Afterburner will not apply a curve that goes DOWN as voltage goes up.** For a
   "shorten the floor" edit, **CAP** every point at or below the boundary at the target clock.
   Do not set one point and leave the points to its left above it. Learned on the 3070 Ti,
   2026-09-20.
3. **Build every curve a session needs BEFORE the first sweep**, into its own slot. Curve-building
   is exactly the desktop activity that contaminates a run, and building first is a free check that
   the edit can be applied at all.
4. ⛔ **Never use the global core-clock slider for a regional edit.** It moves the top of the curve
   too. The one hard crash on record is **875 mV at 3000 MHz** on the 5060 Ti.
5. **Apply from the command line and verify:** `MSIAfterburner.exe -profileN -q` applies and exits.
   Then check the power limit, the **memory clock under load** (the strictest witness), and peak
   core against the configuration's ceiling. **A slot number is not an identity.**
6. **A driver reset silently clears Afterburner offsets.** If one happens mid-suite, that suite is
   stock silicon under a tuned settings string. Re-run it; do not keep it.

---

## Logging

- **One HWiNFO log per configuration**, started before the sweep and stopped after. Never one log
  spanning a curve change.
- **On the 5060 Ti this is automated** (`tools/hwinfo-logging/`, 61 of 61 sweeps on 2026-09-22).
  Someone still has to open HWiNFO and its Sensors window first, because launching it needs UAC.
- ⚠️ **The automation is NOT on the USB kit.** On the shop machines, logs are still started and
  stopped by hand.

---

## The rules that do not bend

1. **Always log a stock baseline per machine** before any tuned setting. A tuned result with no
   same-chip stock comparison measures nothing.
2. **Change one variable at a time.** Core curve, memory and power limit are three variables.
3. **Iteration counts constant across every frequency in a sweep**, and matched across the
   configurations being compared.
4. **Bind `$kit` once** on a shop machine and derive every path from it. Mixing drive letters has
   already cost an hour.
5. **Revert and verify three ways before any card ships** — power limit, memory clock under load,
   peak core against its stock ceiling. Then remove Afterburner and its profile store.
6. **A null is a result** and gets written up as one.
