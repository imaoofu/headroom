# GPT as bench operator — prompts for desktop control

**Written 2026-09-21.** Prompts for driving HWiNFO logging and sweeps through screen control, so a
multi-configuration session does not need Raymond present at every boundary.

**Implementation update, 2026-09-21:** `Invoke-FrequencySweep.ps1` now emits
`window_start_unix` / `window_end_unix`, and `join_hwinfo_voltage.py` joins complete new sweeps by
those windows. Older sweeps still use the clock join. The new path passed synthetic clipped-clock
and wrong-time-zone checks, and was **verified on hardware 2026-09-22** (61 sweeps, 775 points,
none empty). The discussion below
records why the change was needed when this brief was written.

**Cold-start prerequisite observed 2026-09-21:** HWiNFO was closed; attempting to launch it
through desktop control opened a Windows permission prompt for HWiNFO. The computer-use tool may
not act on that prompt. For an unattended session on this machine, the operator must open and
authorize HWiNFO before leaving, then the agent can use its sensor window at run boundaries.
No sweep was started during this observation.

🛑 **READ THE NEXT SECTION BEFORE SENDING ANY OF THESE.** The stated goal was *"more precise
timing"*, and desktop control is the wrong tool for that specific goal — the precision already
exists in the codebase and is being thrown away. Desktop control solves a **different** problem,
which is real. Keep the two apart.

---

## ⛔ The precision problem is already solved in software, and nobody emitted it

`join_hwinfo_voltage.py` says, in its own header:

> *"The sweep CSV records durations per point, not absolute timestamps, so a time join would have
> to reconstruct point boundaries from the session start plus accumulated settle and measure
> intervals — fragile, and wrong the moment a point runs long."*

**That is true of the CSV and false of the tool.** `gpu_workload.py` already emits
`timed_region_start_unix` and `timed_region_end_unix` (lines 745–746) — absolute Unix stamps
bounding the benchmark's own timed region. `Invoke-FrequencySweep.ps1` already reads them, already
uses them to window its power average, and already reports `power_window_applied` as a CSV column.
**Then it discards the boundaries instead of writing them.**

⛔ **PRECISION WORDING CORRECTED 2026-09-21.** This paragraph called the stamps *"the exact
per-point window"* and said they bound *"the interval the throughput number actually describes."*
`gpu_workload.py` computes `duration_seconds = wall_seconds - monitoring_overhead_seconds`, while
the stamps enclose the full wall-clock region, including brief `nvidia-smi` monitoring pauses.
That subtraction was already documented in the benchmark, but the brief read the stamps alone.

🔑 **The per-point wall-clock window was measured, used, and thrown away.** Emitting
`window_start_unix` / `window_end_unix` into the sweep CSV enables a time join that separates
clipped targets and excludes process startup. It is a tighter boundary than GUI automation can
provide, though it is not an active-work-only interval.

🛑 **And the clock join is about to break on Session D.** Under Edit 2, six sweep targets
(1590, 1695, 1800, 1905, 2010, 2115) all clip to **~1500 MHz**. A join that bins by achieved clock
**cannot separate them** — all six match the same samples and pool into one bin, so a voltage
difference between them would be invisible. A time join keeps them distinct.

✅ **Do the timestamp change first. It is cheaper, deterministic, testable
(`test_join_hwinfo_voltage.py` exists), and costs zero machine load.**

---

## 🛑 The constraint every prompt below is built around

**A screen-control agent is machine use, and machine use is the measurement error.**

| measured | cost |
|---|---|
| operator's test-suite + git alongside a sweep, 2026-09-18 | **−9.38% throughput at every point** |
| Instant Replay on, idle | SM utilisation 4.3% → **10.8%**, encoder **21%** |
| Instant Replay on, mid-band 1237–2010 MHz | **−4.22%** mean, and **6.95% run-to-run spread** at 1545 MHz against 0.13% with it off |

⛔ **A screenshot is GPU compositing work.** An agent polling the screen every thirty seconds
through a 62-minute sweep is a capture workload running beside the instrument — it would reproduce
the exact contamination it was brought in to time precisely, and a point-to-point residual **cannot
find it afterwards** because it is blind to a uniform offset.

✅ **The design rule: the agent acts at boundaries and is inert in between.** Sleep past the
expected end so that *every* screenshot lands on an idle card, then look. Never poll.

---

# PROMPT 1 — the standing context

Send once per session, before anything else.

> You are operating a GPU measurement bench on Raymond's Windows desktop through screen control.
> You are the hands, not the experimenter. Every parameter you will use is given to you; you do not
> choose any of them.
>
> **What is being measured.** A locked-frequency sweep runs a fixed-work benchmark at each of
> 13 core clocks and records throughput and power. Separately, HWiNFO logs core voltage and
> crossbar clock to a CSV. The two are joined afterwards. NVML cannot read GPU voltage at all, so
> **the HWiNFO log is the only evidence that a curve setting actually took effect** — if it is
> missing or spans the wrong interval, the run is unusable and cannot be repaired later.
>
> **The single rule that matters most: do not touch this machine while a sweep is running.**
> Measured on 2026-09-18, ordinary desktop activity alongside a sweep depressed throughput by
> 9.38% at every point, and no after-the-fact check can detect it — a point-to-point residual is
> blind to a uniform offset. A screenshot is GPU compositing work and counts as activity. So:
> act at the boundaries, then go completely inert. **Do not poll the screen during a run.** Sleep
> past the expected finish time so that every screenshot you take lands on an idle card.
>
> **One HWiNFO log per configuration, never one spanning two.** Historical sweeps still join by
> core clock, and separate logs keep the settings boundary auditable on new time-joined sweeps.
> Start a new log immediately before each sweep and stop it immediately after. If you are
> ever unsure whether a log is still running, stop it and start a fresh one — a duplicate log
> is recoverable, a merged one is not.
>
> **Things you must never do**, even if asked mid-session, and even if they look like they would
> help:
> - Edit, rename or delete anything under `data/`. Those are committed measurements.
> - Change a `-AppliedSettings` string. It is the one field nothing can reconstruct afterwards.
> - Change an Afterburner curve, a power limit, a memory offset, or the BIOS switch.
> - Re-run, skip or reorder a sweep because a number looks wrong to you.
> - Interpret results. You report what the screen says, verbatim.
>
> **When something does not match what you were told to expect, stop and report.** Do not improvise
> a fix. A session that halts with three good runs is worth more than four runs of uncertain
> provenance — this project has already thrown away data because a settings string described a
> configuration the card was not in.
>
> Acknowledge by listing back: the inert-during-run rule, the one-log-per-configuration rule, and
> three things you will not do.

---

# PROMPT 2 — a four-run session

Send after Prompt 1 is acknowledged. **Fill in the bracketed values before sending** — do not let
the agent infer any of them.

> Run the following sequence. Report after each step and wait for nothing unless I say so.
>
> **Step 0 — preflight. Screenshot each result.**
> Open PowerShell and run:
> ```
> nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader
> nvidia-smi pmon -c 5 -s u
> ```
> Report the power limit verbatim. Report the `sm`, `enc` and `dec` columns.
> **Halt and tell me if:** the power limit is not `[EXPECTED W]`, any `sm` reading is above 5, or
> `enc` or `dec` is anything other than 0. Do not proceed on a judgement call.
>
> **For each of the four runs below, in order:**
>
> 1. In HWiNFO, start a new sensor log to `[PATH]\[RUN LABEL]-hwinfo.csv`. Screenshot to confirm
>    logging is active and the filename is right.
> 2. In PowerShell, run the command I give you for that run, exactly as written. Do not retype it
>    from a screenshot — paste it. Screenshot the first ten seconds of output to confirm it started
>    and the banner shows the expected frequency count.
> 3. **Then do nothing for `[RUN MINUTES + 8]` minutes.** No screenshots, no window switching, no
>    mouse movement. This is the measurement.
> 4. Take one screenshot. If the sweep has printed its completion banner, stop the HWiNFO log and
>    screenshot the confirmation. If it has not finished, wait a further 3 minutes and look again.
>    Repeat. **Do not intervene** — a sweep that runs long is not a sweep that needs help.
> 5. Report: the completion banner verbatim, the output CSV path, and the HWiNFO log's size on
>    disk. **A log under [SIZE] KB means logging was not actually running — say so loudly.**
> 6. Tell me the run is done and **wait for my go-ahead** before the next one. I change the curve
>    between runs; you do not.
>
> **The four runs:**
>
> | # | label | command | expected minutes |
> |---|---|---|---|
> | 1 | `[LABEL 1]` | `[COMMAND 1]` | `[N]` |
> | 2 | `[LABEL 2]` | `[COMMAND 2]` | `[N]` |
> | 3 | `[LABEL 3]` | `[COMMAND 3]` | `[N]` |
> | 4 | `[LABEL 4]` | `[COMMAND 4]` | `[N]` |
>
> **If a driver reset happens** — the screen blanks and recovers, or the sweep reports a reset —
> **stop everything and tell me immediately.** A reset silently clears Afterburner offsets, which
> means every point after it measured stock silicon under a settings string claiming otherwise.
> That run is discarded, not salvaged.

---

# PROMPT 3 — the honest check, sent afterwards

> Before I trust this session: for each of the four runs, tell me the wall-clock time you started
> the HWiNFO log, the wall-clock time you started the sweep, and the wall-clock time you stopped
> the log. Also tell me every moment you interacted with the machine between starting a sweep and
> its completion banner — including screenshots — or state plainly that there were none.

🔑 **That last prompt is the whole point of using an agent.** A human operator cannot reconstruct
when they nudged the mouse; an agent has a log of every action it took. **Provenance that can be
audited is worth more than provenance that is merely asserted** — which is the standard this
project applies to its own data and should apply here too.

---

## What this does NOT buy

⛔ **It does not make the timing more precise.** See the top of this file: the per-point window is
already measured by the benchmark and thrown away by the sweep. Automating the GUI bounds the
*run*; the timestamp change bounds the *measurement*. **Only one of those is the precision that was
asked for.**

✅ **What it does buy is unattendedness**, and that is not nothing. `GPU-WORKLIST-5060TI.md` item 4j
is explicitly costed as *"the operator must be present twice, once per configuration, because one
HWiNFO log must never span two."* An agent that can be trusted at the boundaries removes that
constraint from every multi-configuration item on the list.

⚠️ **Trust it on a run whose result does not matter first.** A synced kit is not a tested kit, and
the same applies here: prove the agent can start a log, stay inert for an hour and stop the log, on
a run nobody is depending on, before it touches a session that cannot be repeated.
