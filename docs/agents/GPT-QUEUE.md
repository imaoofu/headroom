# GPT — the work queue

**Written 2026-09-19, after three prompts that between them retracted one claim, narrowed two, and
corrected a citation.** Track record so far, because it should inform how much weight the next
answers get:

| prompt | outcome |
|---|---|
| **B — cold novelty search** | Found undervolt→XBAR published **January 2023**; caught that three "independent" 2026 sources are **one author, one chip**. Invented nothing; three DOIs verified |
| **A — the 6 mV question** | Correctly refused to assert a universal step. Its documentation work made a **new result** possible from our own data (the grid is per-card) |
| **C — adversarial audit** | ⛔ **Retracted the XBAR mediation claim.** Three claims verified against our committed data. The most consequential external finding this project has had |

🔑 **It has not yet produced a claim that failed verification.** The droop hypothesis was refuted,
but it was a *good* hypothesis refuted by an experiment it prompted — which is worth more than
being right.

---

## ⛔ Read this before sending anything

**Two different jobs, and they need opposite handling:**

| job | give it the repo? |
|---|---|
| **Cold novelty / prior-art** | ⛔ **NO.** Use `NOVELTY-CHECK-BRIEF.md`. A model that has read `CLAUDE.md` inherits our blind spots and stops being an outside reader |
| **Adversarial audit of a specific result** | ✅ **YES** — it needs the data to audit it. But **record that the cold boundary closed**, because the two are not the same kind of evidence |

**Everything it returns is a LEAD until checked.** Prompt C's claims were only worth acting on
because each one was verified against the committed CSVs first.

**Where results go:** `docs/gpt-findings/`, with a row in that README. GPT has been filing these
itself and doing it well — the archive README correctly states that an entry *"does not establish
novelty, prove a source's experimental claims, or update the paper automatically."*

---

# 1. 🥇 Adversarial audit of the LOAD-FLOOR causal claim

**The obvious next job, because prompt C did exactly this to §5.7 and found it could not support
its own sentence. The load-floor result is the project's headline and has never had the same
treatment.**

Give it repo access, same as prompt C. Ask it to audit:

> On four consumer NVIDIA GPUs, the claim is that the energy-efficiency optimum is set causally by
> the top of the V/F curve's low-voltage region. Evidence: a curve edit to that region moved the
> measured optimum +465 MHz in 12 of 12 workloads; a larger edit above it moved the median by 0.
> Predictions were registered before collection.
>
> Audit this against the repository the way you audited the XBAR chain. Where do the comparisons
> share controls and where do they not? Is the optimum located the same way in every run being
> compared? What is the strongest case that the effect is configuration-level rather than
> mediated by the voltage floor specifically?

⚠️ **Three things it should be told, because we already know them and want them attacked, not
rediscovered:** the negative control is **partially leaky** (4 of 12 workloads move), the reported
voltage is a **coarse VID lookup** and not a rail measurement, and the floor end on the 5060 Ti was
**never measured at 1537** — it is between 1560 and 1590.

---

# 2. The §2.7 narrow-window claim, asked properly

⛔ **The first brief simplified it, and GPT answered the simplified version.** It reported the claim
pre-empted by the GTX 980 dataset — but the live claim is narrower and already cites the dataset's
own authors for it.

Ask it cold, with the actual claim:

> Two widely reused public consumer-GPU DVFS datasets — a GTX 1080 Ti set and an RTX 2070 Super set
> — sweep roughly ±11% around each card's own declared default clock. The argument is not that
> nobody has swept lower; it is that *these two specific reusable artifacts* cannot locate an
> efficiency optimum, and that their own authors say so. Is that argument made anywhere else about
> these artifacts, and is the characterisation of their sweep width correct?

---

# 3. The ~95 citing papers judged by title only

**The largest remaining hole in the literature, named in `PRIOR-ART-20260913.md` and never closed.**
Forward citations from Schoonhoven (2211.07260), Guerreiro (HPCA 2018 / TPDS 2019) and Mendes
(JPDC 2022), read beyond the title.

🔑 **Two of those three were found by GPT itself**, so it is working from a citation graph it
partly built.

---

# 4. Verify the MP2884A datasheet claim

⚠️ **The load-bearing documentation claim behind the voltage-grid finding, and I could not open
it.** The assertion is that MP2884A specifies **6.25 mV/LSB** for the reference DAC and
`VOUT_COMMAND`, and **1 mV/LSB** for `READ_VOUT`, explicitly described as *sensed* output voltage.

That distinction is what separates "command path" from "sensor resolution" and it is doing real
work in `CLAUDE.md`. **One person needs to open the PDF and confirm the two numbers and the wording.**

---

# 5. The blocked retrievals — it can reach what I cannot

🆕 **Recorded 2026-09-18: we have different reach, in both directions.** Reddit returns 403 to me
and GPT opened several threads; I have an authenticated `gh`, Crossref scripting, local PDFs and
code execution.

Still unread and inside its reach, not mine:
- **Reddit "Method 4" (August 2022)** — reportedly describes retaining stock curve points below the
  target. ⛔ **If real, the repair curve's SHAPE is published prior art** and only the diagnosis
  plus advance prediction carries the distinction. Currently an unconfirmed lead in `CLAUDE.md`.
- Overclock.net post 29608363 and the RTX 5090 owners' thread page 2002
- TechPowerUp thread 300907

---

# 6. Attack the regret metric and the predictor

**Not yet asked, and it is the other half of the paper.** `predict_from_curve.py` scores 0.675%
mean regret over 192 sweeps, "tying a hindsight-fitted per-configuration constant exactly while
needing no measurement."

> What is wrong with this evaluation? The comparator is fitted with hindsight on the same data.
> 192 sweeps come from four chips and a handful of configurations. What is the effective n, and
> what would a fair baseline be?

🔑 **Prompt 2 showed it is good at exactly this**, and it raised pseudoreplication unprompted.

---

## What NOT to ask it

⛔ **Anything already settled.** The consumer-optimum claim (four reformulations failed), the
narrow-window claim in its broad form, "we measured the constant-voltage region on consumer NVIDIA"
(Guerreiro 2018), "nobody modified a V/F relationship and re-found the optimum" (Mendes 2022).

⛔ **To write into the paper.** It files research records; the paper is changed here, after
verification, by a person who has read the source.

⛔ **To settle anything the hardware can settle.** Item 4j on the bench queue — the memory-matched
re-run — answers a real question in 25 minutes. No amount of searching substitutes for it.
