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
