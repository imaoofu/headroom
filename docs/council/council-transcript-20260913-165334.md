# Council transcript — 20260913-165334

**Question:** Grade the Headroom GPU DVFS research project: its novelty after seven retractions, its
recent findings, and its next goals.

**Grading bar chosen by Raymond:** publishable as undergraduate research.

**Panel:** upgraded — five advisors on different models. Contrarian on Opus, First Principles on
Sonnet, Expansionist on Sonnet (Fable was out of credits and the lens was relaunched), Outsider on
Haiku, Executor on Sonnet. Five peer reviewers on Haiku, each given a different adjudication focus.
Advisor↔letter mapping was randomised before review and is disclosed at the bottom of this file.

---

## 1. FRAME

**The decision:** whether Headroom is publishable as undergraduate research in its current state,
what its remaining novelty actually is, and what it should do with a closing window.

**What is at stake:** the mentorship's stated role is to support publishing this work, so the output
is a real submission rather than a course deliverable. The project has just absorbed seven novelty
retractions in about a month, none of which were measurement errors.

**Key constraints:** solo undergraduate; ~3 month window, partly elapsed; no funding; consumer
hardware on his own desktop; multiple physical GPUs reachable only because he builds PCs on the
side; voltage cannot be written through any documented API, so curve edits are made by hand in MSI
Afterburner; some experiments need admin elevation he must be physically present for.

**What the project holds:** 359 dataset-grade sweeps across four consumer chips and three
architectures; a causal manipulation of the vendor V/F curve with a negative control and
predictions registered before collection; a boundary condition on an RTX 2060 Super; a crossbar
mechanism result with a repair predicted in advance; a null reported as a headline; and a mechanical
claims auditor holding 282 claims against the raw CSVs.

---

## 2. ADVISORS (verbatim, anonymised as presented to reviewers)

See `packet.md` in the session scratchpad for the exact text served to reviewers. Reproduced here in
full.

### Response A

The obvious thing nobody is saying: **they're doing literature search backwards.**

Seven retractions isn't a sign they're being too bold; it's a sign their workflow is broken. They're
writing up results, discovering during that process what's already published, and retracting. That's
expensive and demoralizing.

The experimental work looks genuinely solid — registered predictions before measurement, negative
controls, honest reporting of losses, boundary conditions noted. The 282 checks on their data is the
kind of obsessive self-auditing that usually means the core findings are sound. But they're
discovering prior art at the *publishing stage* instead of using it to scope the claim *before*
experiments.

The citation errors (four author names wrong) and wrong corrections (twice) suggest they're working
too fast or too tired at the write-up stage. That's a symptom, not the disease.

**What they should do: Don't publish yet. Do a full literature review first — actually read the
field, not search-as-you-write. Then rewrite what they're claiming in light of what exists. Only
then publish.**

This takes time. But the alternative is: publish, get reviewed, discover the reviewer found things
they already knew, retract in print instead of in a private repo.

The experimental chops are there. The meta-process isn't. Fix that first.

One more thing: they built a model that lost and published it. That's exactly right. So don't take
the retractions as a sign the entire project is unsound — just that the literature-handling piece
needs a rebuild before it meets a journal.

### Response B

**Verdict: the survivors are selected by the same process that produced seven retractions.**

Every surviving claim is phrased as *not found elsewhere*. This project has a documented 0-for-7
record at predicting what the literature already contains, and each retraction came from searching
*after* writing. The process hasn't changed; only the vocabulary has. Apply that base rate to the
three survivors and you should expect one or two of them to fall — most likely the crossbar chain,
given LACT documented the domain a fortnight before you measured it. Publishing now means publishing
before the search that kills it.

**The statistical flaw nobody has named: the causal result is pseudoreplicated.** "+465 MHz in 12 of
12 workloads" is n=1 chip, 12 correlated measurements on one piece of silicon with one curve edit.
Twelve workloads on one GB206 is not twelve trials. The negative control shares the same chip, the
same session, the same operator. A reviewer who knows DVFS will see this in thirty seconds. Four
chips across three architectures sounds like breadth; it is four n=1 studies stacked.

And the manipulation is **hand-made in Afterburner**. "Openly and reproducibly" is half a claim: the
data is open, the intervention is a GUI drag nobody can replicate exactly.

The 282 claims, 701 tests and CI are not rigour — they are *displacement*. Enormous effort poured
into verifying internal consistency, the one axis that has never once been the failure mode here.

**Grade: C+.** Excellent lab notebook, a paper with no defensible novelty claim left.

**Kill:** the Ridge model thread (the null is publishable nowhere), further chips, further auditor
coverage, and the word "first" in any form.

**Next:** replicate the A/B/B/A manipulation on a *second 5060 Ti* — you sell these. That single run
is worth more than everything else queued. Then reframe as an artifact/dataset paper and target a
workshop.

### Response C

Monday morning, in order:

1. **Run the 2060 Super sweep first — before anything else, before coffee gets cold.** ~10 minutes,
needs the GPU, and it's the single cheapest thing on this list relative to what it buys: a boundary
condition that's currently ±60 MHz goes to ±10, and it's the first measured Turing V/F curve in this
literature. If he touches nothing else today, this is non-negotiable.

2. **Same GPU session, same physical presence: build the two floor-ladder profiles and run their
suites.** He's already elevated, already at the machine, already in the headspace. Batching this
with #1 is the only way it happens this month — splitting these into separate sessions doubles the
setup tax for no reason. This is what converts "the optimum moves" into "the optimum moves
proportionally," which is the difference between a demo and a dose-response curve. That's the
paper's spine.

3. **While sweeps are running — rewrite the contribution sentence.** Laptop task, zero GPU needed,
and urgent precisely because it's embarrassing: if a reviewer reads "we reshape the curve region by
region" and thinks "that's just undervolting," the causal design underneath never gets read
charitably. Fix the framing before anyone external sees it.

4. **Same laptop block: draft the §5.7 pre-emption of the saturation objection.** Cheap, high
leverage, kills the most obvious referee report in advance.

**Off the list entirely, for now:** dataset publication prep and the ML-model framing exercise —
both real, neither blocks submission, and both are exactly the kind of work that expands to fill
however much time is left. Park them. The literature follow-ups and the minor items go on a single
"before final submission" checklist, reviewed weekly, not touched daily — this project's own history
shows searches decay when left as vague intentions, so give each a triggering date, not a good
feeling.

Grade: strong B+/A- undergraduate work, publishable at a workshop or applied venue once 1–4 land —
the causal manipulation plus registered negative control is the real result; everything else is
scaffolding around it.

### Response D

Is "novel enough to publish" even a coherent gate to apply here, or is it importing a norms-set
built for a different production function than this one?

Publication novelty gates exist to ration a scarce resource — reviewer attention and journal pages —
in a system where the default submitter is a funded lab with priors, infrastructure, and
institutional incentive to overclaim. None of that describes this artifact. This is one
undergraduate, one desktop, three months, and a mentorship whose *stated job* is to get the work
out, not to referee it against the Schoonhoven/Mei/Leng canon. Applying the lab-grade gate to it
measures the wrong thing: it asks "did a novel *claim* survive" when the actual production here is
"did a *process* survive," and the process is the finding.

Look at what seven retractions actually are. Every single one fired on the framing sentence, not the
measurement — the CSVs never lied, the search discipline caught the overclaim every time before it
calcified. That's not a student failing to be novel. That's a working falsification loop,
self-applied, at a cadence (weekly) that most funded labs don't sustain because their incentives
point the other way. The real deliverable is that loop plus the dataset it disciplined — 359 sweeps,
282 mechanically-checked claims, a boundary condition on hardware nobody's measured. "Novel enough"
asks you to evaluate the residue after the loop; it discards the loop itself, which is the part
actually worth a paper.

So reframe the goal: stop optimizing for "beat the literature" and start optimizing for "publish the
method that keeps catching you," with the causal manipulation and the 2060S boundary as the
empirical anchor. That's a different, better, and actually available paper — a
registered-report-style methods contribution, not a discovery claim competing with labs it was never
resourced to outcompete.

### Response E

The upside nobody in the room is naming is the tooling itself — specifically the audit
infrastructure — not the DVFS result.

Everyone will grade this on the ridge-point finding, because that's the paper-shaped artifact. But
look at what's actually reproducible and transferable here: 282 claims that are *rendered strings
computed from raw data at check time*, not stored expected values, asserted to appear verbatim-once
in the prose. That's a general solution to a problem every empirical field has and almost nobody has
open-sourced cleanly — the drift between what the data says and what the paper claims. Combine that
with the documented retraction trail (seven, with the actual search queries and dates preserved) and
you don't have a GPU paper with good hygiene. You have a redistributable *methodology paper* —
"mechanical claim auditing for reproducible empirical research" — that happens to be demonstrated on
GPU DVFS. That artifact generalizes to any lab running CSVs into a paper: economics, bio, ML
benchmarking. Release the auditor as a standalone package with the Headroom corpus as its worked
example and this stops being one undergrad's GPU paper — it's infrastructure other people cite and
adopt.

Second, underweighted: the boundary condition on the 2060 Super isn't a footnote, it's a second
paper. "No Turing V/F curve has ever been measured, the canonical reference paper assumed its shape
by fitting power" — that's not support for the main claim, that's an independent, citable correction
to existing literature, orthogonal to the ridge-point work. Measuring one more Turing card properly
and writing THAT as its own short paper (methods note / correspondence) is probably the fastest
actual publication in this whole project.

Third: the Afterburner curve-decode plus the `.cfg` format plus the crossbar-domain finding is,
quietly, a piece of hardware reverse-engineering documentation that the overclocking community would
want independently of any academic outcome — that's a second audience, not just a second
contribution.

The biggest miss: treating this as one paper instead of three artifacts with different audiences and
different time-to-publish.

---

## 3. PEER REVIEW

**Strongest-response votes: C ×2, B ×2, D ×1.** A genuinely split council.

### Reviewer 1 (general)
**Strongest: D** — the only response that answers B's pseudoreplication critique by refusing to play
the game, repositioning the deliverable as the falsification process itself.
**Biggest blind spot: C** — its entire Monday roadmap assumes the causal effect is solid and just
needs extension. It never engages with whether one chip × twelve workloads demonstrates the effect.
**What all five missed:** *nobody proposed external verification of novelty before submission.* The
student has a documented 0-for-7 record at predicting what the literature contains, yet every
recommendation depends on him solving that alone. D's reframing is especially dangerous here because
it *lowers* the novelty bar and could create false confidence in searches he has already failed at.

### Reviewer 2 (confidence vs correctness; is the harshest the most rigorous?)
**Strongest: C** — the only response that identifies what would actually make this publishable:
converting "the optimum moves" into "the optimum moves proportionally".
**Biggest blind spot: B's dismissal of the negative control.** B calls it weak because it shares
chip, session and operator — "but that's precisely *why* it's strong. A negative control doesn't
need to be on different hardware; it needs variables controlled. B is confusing narrow scope (real:
n=1 chip) with invalid design (false)."
**What all five missed:** nobody asks what the 2060 Super failure *reveals mechanistically*. Does
the rule require sub-6 mV stepping? The boundary condition is evidence about which hardware
properties determine applicability, not a footnote or a scope narrowing.

### Reviewer 3 (the person, not the artifact)
**Strongest: C** — the only one that respects the actual constraint: a student with a finite window
who has just absorbed seven retractions and needs to finish. A adds 2–4 weeks; B's C+ could
demoralise; D is elegant but doesn't say what to do tomorrow; E adds scope.
**Biggest blind spot: D** — it assumes the process self-corrects at publication scale and ignores
asymmetric career risk. An eighth retraction caught *after* publication reads very differently to a
hiring committee than one caught in a repo.
**What all five missed:** the measurement that settles novelty risk has not been taken. One
floor-ladder sweep on Turing changes everything downstream — novelty risk, venue, what gets
headlined, whether D's reframe is necessary or premature. Every response treats it as optional or
future.

### Reviewer 4 (adjudicate the pseudoreplication dispute)
**Strongest: B** — pseudoreplication is what a DVFS reviewer will name in thirty seconds, and B
proposes a concrete, reachable fix.
**Biggest blind spot: B's treatment of the negative control** — same finding as Reviewer 2, reached
independently. "B underestimates what registered prediction + negative control proves about
causality *on one chip*... The right statement is: **'strong within-chip evidence, generalization
uncertain,'** not 'pseudoreplicated, period.'"
**What all five missed:** the null result could be the *first* publication — a genuine
negative-result contribution, achievable in 2–3 weeks, establishing a record and buying time for the
harder claims. A dismisses it, B says it is publishable nowhere, C/D/E ignore it.

### Reviewer 5 (which venue is actually reachable?)
**Strongest: B** — names the statistical flaw, the Afterburner reproducibility wall, a concrete fix,
and an actual venue, without pretending a literature review solves the novelty problem.
**Biggest blind spot: C** — most actionable, but sidesteps replication entirely. Three more sweeps
on one additional card still leaves a reviewer looking at four separate n=1 studies.
**What all five missed:** *the actual deadline.* The mentorship "gets the work out", which probably
means delivering a credible artifact before a hard date, not achieving journal acceptance. Every
recommendation in the packet scales to infinite time.

---

## 4. CHAIRMAN'S SYNTHESIS

See `council-report-20260913-165334.html` for the rendered verdict. Summary of the position taken:

- The council splits C vs B; both are half right, and two reviewers independently found the same
  error in B — it conflates *narrow scope* with *invalid design*.
- The defensible statement of the causal result is **"strong within-chip causal evidence,
  generalisation uncertain."** Not "proven", not "pseudoreplicated, period."
- B's concrete fix is the best single action anyone proposed and was on nobody's to-do list: a
  **second RTX 5060 Ti**, which Raymond can reach because he sells them.
- Reviewer 1's catch is the most important thing in the whole session: **no one proposed external
  verification of novelty**, and the mentorship is the obvious unused instrument for exactly that.
- Reviewer 5's catch is the most practically urgent: nobody knows the real deadline, and every plan
  assumes infinite time.

**Grade against the chosen bar (publishable as undergraduate research): B+.**

---

## Advisor ↔ letter mapping (disclosed after review)

| letter | lens | model |
|---|---|---|
| A | The Outsider | Haiku |
| B | The Contrarian | Opus |
| C | The Executor | Sonnet |
| D | The First Principles Thinker | Sonnet |
| E | The Expansionist | Sonnet (relaunched; Fable out of credits) |

Reviewers 1–5 all ran on Haiku with different adjudication briefs.

## Chairman's disclosure

The chairman of this session is the same assistant that co-authored the seven retractions under
discussion, and wrote the framing that four of them corrected. Its reading of Response D — that the
falsification loop is itself the finding — is therefore not disinterested, and is discounted in the
verdict for that reason.
