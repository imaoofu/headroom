# Split-curve `membw`, clean protocol - 2026-08-24

One sweep. It withdraws a correction that was itself a correction, and the sequence is the
point of this directory.

## What was measured

`20260824-203810_5060ti-splitcurve-clean-membw-fine_sweep.csv` - the split-region curve of paper
5.7.6 on the 10-point 1400-2100 MHz grid, the same grid and timings as the clean memory-only
ceiling of 2026-08-23 and the rebuilt repaired curve of the same evening.

Configuration PROBED before starting, not assumed: at a locked 3090 MHz target the core read
2979.4 MHz mean (2977 min, 3000 max), which is the split signature - the original tune reads
~2947, the rebuilt repair ~2906, memory-only ~2593 and stock ~2610. Memory under load read
16301 MHz, confirming the +2500 offset against a stock 13801. Encoder and decoder both 0% at
preflight, recorded in the session JSON.

## Why it exists

Section 5.7.6 said twice that the split curve does something on `membw`, and both statements were
reached by comparing runs of unequal provenance.

  1. The first version compared a 2026-08-22 split-curve sweep against a 2026-08-20 memory-only
     sweep. Both predated the capture-software finding of 5.4.4 and neither verified its
     conditions. It concluded the split curve reached the ceiling, within 0.4% at seven of ten
     points. That conclusion was RIGHT, and it was right by accident: two similarly contaminated
     runs cancelled.

  2. The second version re-measured the ceiling clean and left the split curve where it was. Clean
     against contaminated, in the opposite direction, giving an apparent -3.18% deficit and a
     rewritten "three-way trade" built on it.

  3. This run cleans the other side. The split curve rose +3.19% over its predecessor and lands at
     -0.11% mean against the ceiling, 7 of 10 points within 0.4% - statistically the same place
     the repaired curve sits at -0.39%.

## Is the rise contamination, or a different curve?

Contamination, on three independent grounds:

  - MAGNITUDE. +3.19% against the +3.30% by which the memory-only ceiling moved when it was
    re-measured clean, and in the range 5.4.4 measured for capture software (+4.22% mid-band).
  - FREQUENCY SIGNATURE. The rise declines with frequency: +3.06% across 1402-1710 MHz against
    +2.24% across 1867-2100. That is the direction 5.4.4 measured. A voltage-curve difference
    would show as a step at the voltage boundary, not a smooth decline.
  - AN ISOLATED POINT. The largest single jump is +7.63% at 1792 MHz, flanked by +2.5% and +2.2%.
    No V/F curve produces a hole at one grid point. A transient contaminant does, and this is the
    same "roughly one run in three" outlier 5.4.4 attributes to capture software.

Controlled for: the memory offset was applied in all three runs (peak memory clock 16301-16312
MHz in each), so the difference is not a missing overclock.

## What is NOT established

The split-curve profile applied on 2026-08-24 is not proven bit-identical to the one applied on
2026-08-22 - the profile was not saved, and the probe reads clocks rather than the curve. The
clock signature matches and the three lines of evidence above all point at contamination, but a
small profile difference is not formally excluded.

n=1 per configuration on `membw`. The agreement between the ceiling, the repair and the split
curve is the only replication here.

## The lesson

**A comparison is only as clean as its dirtier half.** Correcting one side of a pair is not a
partial fix. It converts a symmetric error into an asymmetric one, and it looks like diligence
while doing it. The provenance audit had already flagged step 2 as a mixed comparison whose risk
ran against the finding, and recorded in `analysis/claims_consumer.py` that -3.18% was an upper
bound rather than a measurement. That note was written the same morning this run confirmed it.
