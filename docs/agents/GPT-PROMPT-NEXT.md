# The next prompt — send this one

**Written 2026-09-19, after jobs 1 and 2 both landed and both produced retractions.**

🔑 **Why this one and not the literature holes.** The predictor and its regret metric are **the
other half of the paper and the only major surface that has never been audited**. Jobs 1 and 2 each
took a headline claim apart; this is the last headline claim standing. The ~95 citing papers are a
bigger hole but a diffuse one, and the MP2884A datasheet is a ten-minute errand that can ride along
any time.

⚠️ **Give it repo access.** This is an adversarial audit, not a cold novelty check, and **the cold
boundary is already closed for this model** — it has read `CLAUDE.md`. Record that beside any
novelty-flavoured answer it returns.

---

## Copy from here

> **Adversarial audit: the curve predictor and its regret metric.**
>
> You have audited this repository twice. Both times you took a headline claim apart and both times
> the corrections verified. Do it again to the one that has never been audited.
>
> **The claim.** `analysis/models/predict_from_curve.py` reads the applied voltage-frequency curve,
> finds the frequency at which it leaves the 720 mV load floor, and predicts the energy-efficiency
> optimum from that alone. Scored over **192 sweeps, 4 configurations, one RTX 5060 Ti**:
>
> | strategy | mean regret | worst | exact |
> |---|---|---|---|
> | oracle | 0.000 | 0.000 | 100.0% |
> | **mechanism — curve read at the load floor** | **0.675** | 11.939 | 74.0% |
> | best constant per configuration (hindsight) | 0.675 | 11.939 | 74.0% |
> | best single constant (hindsight) | 1.961 | 13.479 | 60.9% |
>
> Regret is efficiency given up, in percent. The repository's own summary is that the mechanism
> *"ties the hindsight-fitted per-configuration constant exactly"* while *"needing no measurement"*,
> and that the whole configuration axis is worth only **1.29 points** against a headroom of roughly
> **30–57 points**.
>
> **Audit it the way you audited the load-floor claim.** Recompute rather than reason from the
> summary. In particular:
>
> 1. **What is the effective n?** 192 sweeps come from one chip, four configurations and twelve
> workloads. Which of those axes are independent and which are repeated measures? State the
> effective sample size for each comparison in the table, not for the table as a whole.
> 2. **Is the comparator fair?** Both hindsight baselines are fitted on the same data they are
> scored on. What would an honest baseline be — leave-one-configuration-out, leave-one-workload-out,
> a pre-registered constant, something else? Recompute the table under it.
> 3. **How much of the 2.90× is one configuration?** Three of the four configurations leave the
> floor at 1530 MHz and the predictor picks 1545 for all three; only `fulltune` differs, at 2010.
> The best single constant is 1545. **Work out what remains of the advantage if `fulltune` is
> removed**, and say plainly whether this is a two-level classifier evaluated 192 times.
> 4. **Is "ties exactly" a result or an artifact of the grid?** The suite grid is ~155–158 MHz wide.
> How much of the 74.0% exact-match rate survives a finer grid, and what would it take to tell a
> mechanism that is right from one that is coarse enough not to be wrong?
> 5. **The residual is not flat.** `reduce` and `gemm` carry 70% of it — `reduce` alone is 4.790
> mean and 11.939 worst. Is that a mechanism failure, a workload property, or a measurement
> artifact? What would distinguish them?
> 6. **The 720 mV floor is a fitted parameter.** It was measured in `voltage-curve-20260908` on this
> same card. How sensitive is the whole table to it, and does the predictor still beat the baselines
> if that parameter is perturbed by one voltage code?
>
> **Then the other half.** `analysis/models/predict_optimal_frequency.py` reports a **null** on the
> public V100 set: the probe-based model scores **0.883%** mean regret against a best-fixed-frequency
> baseline at **0.837%** — the model *loses*, leave-one-workload-out over 33 folds. The two halves
> reach opposite conclusions about whether workload identity is worth modelling. **Are they
> consistent?** If not, which one is wrong, and what evidence would settle it?
>
> **Ground rules, same as before.** Verify every number against the committed data before you state
> it. Say what you could not check. A null is a result. Do not edit the paper; file the record in
> `docs/gpt-findings/` with a row in that README, and treat everything you produce as a lead until
> someone here recomputes it.

## To here

---

# Secondary, if there is room in the same session

> **Read Figure 4 and §5.1.1–§5.2 of Wang et al., TPDS 2022 (`10.1109/TPDS.2022.3181096`,
> preprint `arXiv:2104.00486`) against the counts you produced on 2026-09-19.**
>
> You reported that a raw-table energy argmax on their released GTX 1080 Ti CSV puts **18 of 30
> applications at the highest** sampled core clock and 8 at the lowest. The paper says its fitted
> optimum sits *"close to the allowed lowest setting"*. Those disagree.
>
> You named three candidate explanations — their 20 benchmarks against the CSV's 30 applications, a
> fitted optimum rather than a grid argmax, and system-scope energy against a 37 W idle floor.
> **Open the figure and decide which, or say it cannot be decided from the published text.**
>
> ⛔ **This is blocking.** The repository's §2.7 strategy is to cite these authors *against their own
> artifact*, and that strategy cannot be defended while their reported optimum and their released
> table point in opposite directions.

---

## What is still queued behind these

1. **The ~95 citing papers judged by title only** — the largest remaining literature hole.
2. **Verify the MP2884A datasheet** — 6.25 mV/LSB command path against 1 mV/LSB `READ_VOUT`. A short
   errand, load-bearing in `CLAUDE.md`, and nobody here has opened the PDF.
3. **The blocked retrievals** — Reddit "Method 4" (August 2022) above all. If it holds, the repair
   curve's *shape* is published prior art.

⛔ **Still do not ask it:** anything settled (`GPT-QUEUE.md` lists them), anything that writes into
the paper, and anything the hardware settles faster — `GPU-WORKLIST.md` item 4j answers a real
question in 35 minutes and no amount of searching substitutes for it.
