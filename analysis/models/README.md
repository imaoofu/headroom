# Prediction models

Everything in this repository that **predicts** rather than **measures**.

The split is not organisational tidiness. The project's headline results are measurements —
`characterize.py` reports the stock-vs-optimum gap with no model involved, and `analyze_sweep.py`
reads what the card actually did. Those numbers stand on their own. Everything in this directory
outputs an *estimate*, and every estimate here has so far been beaten or tied by something that
needed no fitting at all. Keeping them in one place makes that pattern visible instead of
scattered across ten files.

| File | Question it asks | Current verdict |
|---|---|---|
| `predict_optimal_frequency.py` | Which frequency gives the best performance-per-watt? | **Ties** a fixed 952 MHz — 0.883% vs 0.837% mean regret |
| `predict_constrained_frequency.py` | Same, subject to keeping ≥95% of stock performance | **Loses** to straight-line interpolation between the same probes |
| `curve_model.py` | Can a few probes reconstruct the *whole* curve? | **Reconstruction works** (MAE 0.0261); frequency *selection* ties |

Each has a `test_*.py` beside it. All three are mutation-gated: the suites were accepted only
after deliberate bugs were introduced and caught.

## The result this directory exists to keep honest

Read the three verdicts together and they say something more useful than any one of them:

- **Probing carries real information.** Under a 95% performance floor a probe-based strategy
  reaches 25.4% mean efficiency gain against a fixed frequency's 4.9% — 87% of the gap between the
  fixed policy and a perfect oracle.
- **The fitting is not what extracts it.** The strategy that gets there is four straight line
  segments. Ridge appears to do better only by breaking the floor on 8 of 33 workloads; made to
  respect it, it does worse than the interpolation.
- **And unconstrained, none of it matters**, because 952 MHz is optimal for 24 of 33 workloads and
  a constant is nearly the right answer everywhere.

So the honest summary is *measure a few points, interpolate, and attach a performance guarantee* —
not *fit a model*. That conclusion is only visible because the baselines were built to embarrass
the models rather than to flatter them, which is the rule these files are held to.

## What these models actually are, and the weakness in how they are built

Worth stating plainly, because "model" oversells them. Every file here fits **`Ridge(alpha=1.0)`** —
ordinary least squares with an L2 penalty. No trees, no ensembles, nothing deep. The fitted object
has `coef_` of shape `(13, 8)`, which means it is **13 independent linear equations**, one per
frequency in the sweep, each predicting efficiency there as a weighted sum of the same 8 features:
performance at 4 probe frequencies, and power at those same 4 expressed as a ratio against stock.

**117 learned parameters against 32 training rows** in each leave-one-out fold. More parameters
than examples, which is why the L2 penalty is load-bearing rather than decorative.

That is the right size of model for this data and not an apology. With 33 workloads and a matrix
carrying no workload feature columns at all, anything larger overfits on contact. The comparison
ladder the three files establish runs *constant → nonparametric interpolation → regularised linear
→ oracle*, and two of those four are not statistical models: the fixed-frequency baseline is a
constant predictor using zero features, and the interpolation baseline has zero learned parameters
and simply joins the probes with straight lines.

⚠️ **THE WEAKNESS: the 13 output equations are fit independently, so nothing constrains the
predicted curve to be smooth or single-peaked.** `chooseByProbeModel` takes `argmax` over 13
unconnected linear predictions. In principle that argmax can land on a jagged artifact rather than
a peak, and no part of the construction prevents it.

It is mitigated rather than solved. Predicting the whole curve and taking its peak — instead of
regressing the optimal frequency directly — means a wrong answer tends to land on a neighbouring
frequency on a flat part of the curve rather than somewhere arbitrary, which is why the code is
written that way and says so. But that is a property of the efficiency curve being flat near its
top, not a guarantee the model provides.

**It is deliberately not fixed.** The obvious repair is to fit a parametric curve shape, or to
constrain the outputs to be unimodal. That is effort spent making a model that already loses to
straight-line interpolation lose by less. If the constrained result is ever revisited on data with
real workload features — the consumer suite characterises arithmetic intensity, which the V100
matrix does not have — the fix belongs in that work rather than this one.

If a reader asks why no parametric curve was fitted, the answer is the honest one: a fit was tried,
and the unfitted baseline beat it.

## Running them

Every file is a script, run directly. No package, no `-m`, no install:

```bash
python analysis/models/predict_constrained_frequency.py
```

They import `load_data.py` from `analysis/`, one level up, via an explicit `sys.path` line at the
top of each file. That is deliberate rather than a `__init__.py` package: the whole toolchain is
built to run on a machine with no setup, and relative imports would force `python -m` and break
every command written down in the README, `HANDOFF.md` and the paper.

**If you add a suite here, it is already covered** — `analysis/models` is listed in
`run_tests.py`, and that runner now fails if it finds a `test_*.py` under a directory it is not
running. It gained that guard because moving these three files into this directory would
otherwise have dropped them from every future run while still printing *All suites passed*.

## What is deliberately not here

`analyze_constrained.py` computes the constrained **oracle** — the best achievable answer with the
whole measured curve in hand. That is a measurement of an upper bound, not a prediction, so it
stays in `analysis/`. `predict_constrained_frequency.py` cross-checks itself against it on every
run, reproducing 28.5% and 4.9% at 1462 MHz before it reports anything of its own.

`curve_model.py`'s `specs` mode — predicting a never-measured chip from its spec sheet — is an
inactive extension point. It needs a specs database and enough distinct chips to fit against.
Two chips is not enough, and the file says so rather than printing a number.
