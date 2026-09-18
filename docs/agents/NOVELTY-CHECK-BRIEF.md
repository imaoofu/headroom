# Prior-art brief — paste this cold into a fresh conversation

**Do not supply any other file from this repository with it.** Not the paper, not the standards
document, not the related-work index. The whole value of this brief is that the reader has no idea
what answer is wanted, and reading one paragraph of this project's own framing destroys that.

⚠️ **Start a NEW conversation.** A model that has already discussed this work in the same thread is
no longer an outside reader.

---

## Why this exists

Over four months this work has asserted and then withdrawn **seven** claims of novelty. Every
withdrawal came from the same place: a check that asked *"is this true of our data?"* rather than
*"is this already known?"* Every one was found in-house, after writing, usually within two search
queries of the paper that pre-empted it.

No reader outside the project has ever been asked. This brief is that ask.

---

# The brief — everything below this line is what to paste

I have a set of GPU measurements and I need to know whether the findings are already published. I
want you to try hard to **pre-empt** them. Assume they are not novel and look for the work that
beats them.

## What was measured

Consumer NVIDIA graphics cards — four physical chips across three architectures (Turing, Ampere,
Blackwell), one card of each model. Desktop parts, 170–290 W class, not datacenter accelerators.

For each card, a fixed-work benchmark was run at each of ~13 core clock frequencies, locked via
`nvidia-smi`, spanning roughly 40–100% of the card's maximum clock. Board power and throughput were
recorded at each point, and core voltage was read from a hardware monitoring utility (it cannot be
read through NVIDIA's management library on these parts, and cannot be written at all). Energy
efficiency was computed as throughput per watt and the frequency maximising it was located.

Twelve different compute kernels were used per card, spanning a wide range of arithmetic intensity.

## The specific findings I want checked

**1. A causal relationship between the shape of the voltage-frequency curve and where the
efficiency optimum sits.**

On these cards the vendor's voltage-frequency curve can be reshaped by hand, point by point, using
a third-party tuning utility. Two separate edits were made on one chip:

- Changing the curve in the region where **core voltage stays constant while clock rises** moved
  the measured efficiency optimum by **+465 MHz, in 12 of 12 kernels**.
- Changing the curve **above** that region — a larger edit, 570 MHz — moved the optimum **by
  nothing**.

Both predictions were written down before the measurements were taken.

**Questions.** Has anyone published a study that *manipulates* a GPU's voltage-frequency curve
region by region and then re-locates the energy-efficiency optimum? Specifically with a negative
control — an edit deliberately made where the effect is predicted *not* to appear? Is the
correlation itself (between that constant-voltage region and the optimum) established, and if so,
by whom and on what hardware?

**2. Whether the constant-voltage region has ever been directly measured on Turing.**

One card's voltage readings show that region ending ambiguously: voltage leaves its minimum in
steps of about 6 mV, one sensor quantum at a time, so where it ends is undecidable to within a
frequency step. Two independent sweeps also show the voltage curve is **non-monotonic** — it falls
by ~13 mV before rising.

**Questions.** Are there published *measurements* (not model fits) of core voltage against core
clock on Turing consumer GPUs? Does anyone report a non-monotonic voltage-frequency curve on any
GPU? Is voltage-sensor quantisation discussed as a limit on this kind of analysis?

**3. A bandwidth collapse caused by undervolting.**

Flattening the voltage curve so core voltage stays pinned while clock rises caused a
memory-bandwidth-bound kernel to plateau at roughly 300 GB/s. Telemetry showed an on-die
interconnect clock pinned near a fixed value instead of tracking the core clock, while the DRAM
clock stayed at its maximum throughout. A repair derived from that diagnosis was stated in advance
and behaved as predicted.

**Questions.** Is this chain — undervolt pins interconnect clock, interconnect clock gates
achievable memory bandwidth — documented anywhere for GPUs? Vendor whitepapers, reverse-engineering
projects, driver or firmware work, and overclocking-community measurement all count.

**4. How wide published consumer GPU DVFS datasets sweep.**

Two widely reused public datasets for consumer cards sweep a window roughly ±11% around the cards'
default clock. This work sweeps from 40% of maximum.

**Questions.** Are there other *downloadable* DVFS datasets for consumer GPUs that sweep
substantially below default? How far below?

## How to answer

- **Lead with anything that pre-empts these.** That is the useful outcome, not confirmation.
- **Every citation needs a verifiable identifier** — arXiv ID, DOI, or a URL. I will check them.
- **If you are not sure a paper says what you think, say so.** Do not reconstruct an author list
  or a section number from memory. I would rather have "there is something in this area, I am not
  certain of the reference" than a clean citation that turns out not to exist.
- **Non-academic sources count fully**: patents, vendor whitepapers, GitHub issues, overclocking
  forums, a well-documented enthusiast measurement.
- Search in vocabulary I might not have used. Academic phrasing for this topic rarely matches the
  words above.
- **Tell me what you could not check**, and which venues you could not reach.

Finally: if you think one of these findings *is* genuinely unpublished, say which, and say what
would have to be searched to be confident — not just that you did not find anything.

---

# After GPT answers

🛑 **Do not paste the reply into the repository.** Run every identifier it gives through:

```bash
python analysis/verify_citations.py --live
```

and add new sources to `docs/RELATED-WORK.md` **only with read status recorded**. An AI-supplied
citation is a lead, not a source, until someone opens it — this project has already written four
wrong citations, one of them an author list invented outright by an AI assistant for the single
most important paper it cites.

✅ **A "nothing found" reply is worth recording too**, with the queries, per the search rule. Put it
in a dated `docs/PRIOR-ART-<date>.md` alongside the existing logs.
