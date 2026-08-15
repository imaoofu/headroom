# Context — who, why, and the constraints

Portable version of context that otherwise lives only in local Claude Code memory on one machine.
`CLAUDE.md` covers *what is technically established*; `HANDOFF.md` covers *how to get running*.
This covers *why this project exists and how to work on it*.

> This repository is **private**. Verified 2026-08-15 (the unauthenticated GitHub API returns 404
> for private repos rather than 403, and pushes succeed). If it is ever made public, re-read this
> file first and decide what should be trimmed.

---

## The project's actual goals, in priority order

1. **A finished, rigorous, differentiated project** for the Inspirit AI mentorship program.
   ~3 month window. The deliverable format (paper / poster / journal / symposium) is **still
   unconfirmed** despite being asked several times — worth pinning down early, since it changes
   how the write-up is structured.
2. **College application strength.** Stated directly. This sets the bar: the work has to survive
   someone knowledgeable poking at it. It does *not* need to advance the field, and pretending
   otherwise would be the fastest way to lose credibility. No project can be promised to move an
   admissions outcome, and nobody should claim otherwise.
3. **Genuine interest.** Raymond is a long-time PC builder and runs a small PC-building business.
   The topic was chosen because he actually cares about it, not because it was assigned.

## What actually differentiates it

Not the model — the null result already showed a regression isn't the story. What sets it apart:

- **Original data on hardware nobody has published.** Most student projects download a dataset.
  This one ships one.
- **A null was reported and kept.** The losing number is in the README table.
- **The access is genuinely his.** A PC-building business is the only reason multiple physical
  chips are reachable at all. Not replicable by someone else.
- **It is reproducible.** Locked protocol, public code, documented instrument limitations.

---

## Hard constraints

**Hardware access is the binding constraint.** The business turns over roughly **one build every
2–3 weeks**. Realistically 6–10 machines over three months, mostly *different* models rather than
repeats of one SKU. Any plan requiring many chips of the same model to study silicon-lottery
variance does not fit the window — size analyses to small-N reality and say N out loud.

**Do not automate tuning on customer machines.** Not primarily a technical risk — a business and
reputation one. Prove protocols on his own hardware first, and only ever ship a build at settings
that would have shipped anyway.

**⚠️ The GPU serves double duty.** Raymond runs **Ollama** (`qwen3:14b`, ~9.3 GB) locally on the
same RTX 5060 Ti that is the subject of this research, paired with OpenCode Desktop for bulk work.
**Ollama must be closed before any sweep or stability run.** A loaded model competes for the card,
and the frequency sweep's baseline-utilisation guard will refuse to start (correctly). This has
already caused one contaminated measurement — a test run during a gaming session showed 79%
baseline utilisation and throughput dropping from 8.03 to 4.84 TFLOP/s from contention alone.

---

## How to work with him

**He has a real rigor standard, and it predates this project.** It came out of a previous team
research project (BeSMART, UC Berkeley summer 2026 — SF combined-sewer / Bay water quality; the
team won, and it's a separate effort from this one, so don't conflate them). That project's
governing document enforced, after repeat corrections:

- **Verify before claiming.** Check the file, run the code, grep the source. An unverified claim is
  a defect even when it happens to be true, because it makes every *other* claim unauditable.
- **Zero sycophancy.** If something is weak, say so first.
- **Nulls are results.** That team reported a bloom-risk model with no out-of-sample skill as the
  finding rather than tuning until it won.
- **Separate measured from inferred, in the same breath.**

Those standards are why this repo's tools state their own limitations in their own output, and why
`predict_optimal_frequency.py` prints a verdict against itself.

**He can handle real technical depth** — dataset schemas, validation methodology, API-level
tradeoffs. He has shipped real code, including security fixes on the BeSMART repo. Do not
oversimplify.

**Framing that lands:** "will this hold up to scrutiny." Framing that does not: generic
encouragement.

---

## Things already corrected — don't re-make these mistakes

- ❌ *"Nobody has quantified this gap."* The voltage-guardband literature already had it. Retracted.
- ❌ *"The GPU load is Wallpaper Engine."* It was a game. Diagnose before naming a culprit.
- ❌ *"VS Code will give you Python."* It does not; they are separate installs.
- ❌ *"No crash means the memory overclock is validated."* GDDR7 error correction silently retries,
  so a memory OC can be stable *and* net slower. Stability and performance are separate tests.
- ❌ Assuming a documented API works on consumer hardware. `nvmlDeviceGetGpcClkVfOffset` returned
  `NOT_SUPPORTED` on the 5060 Ti. Probe, don't assume.

---

## Related work by the same person

**BeSMART 2026** — UC Berkeley summer program, four-person team, SF combined sewer → Bay water
quality → bloom risk. Presented and won 2026-08-07; research continued past the program. Separate
project, separate repo, cloned locally at `C:\Users\Raymond\BeSMART-2026-Final-Project-`. Relevant
here only as the origin of the working standards above.
