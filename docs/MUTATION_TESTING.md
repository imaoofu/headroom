# Measuring the test suites, 2026-08-30

The suites and the claim auditor are the two mechanical checks this project's credibility rests
on. Both are self-reporting: they say they passed. Neither can say whether it was looking.

This is the measurement that answers that. 155 single-line bugs were injected into the thirteen
source files that have a dedicated suite, one at a time, and the full battery was run against
each. A mutant the suites catch is **killed**; one they miss **survived**.

Method and harness: `tools/mutation/`. Mutants proposed by the local Qwen3.8-27B (UD-IQ4_XS via
llama.cpp), applied and graded mechanically.

## Headline

**69 killed, 86 survived, 0 invalid — a mutation score of 45%.**

| file | killed | survived | score |
|---|---:|---:|---:|
| `analysis/audit_claims.py` | 11 | 1 | **92%** |
| `analysis/analyze_constrained.py` | 9 | 3 | 75% |
| `analysis/characterize.py` | 7 | 5 | 58% |
| `tools/frequency-sweep/join_hwinfo_voltage.py` | 7 | 5 | 58% |
| `tools/local-model/ask_local.py` | 6 | 6 | 50% |
| `analysis/models/predict_constrained_frequency.py` | 5 | 6 | 45% |
| `analysis/compare_consumer.py` | 5 | 7 | 42% |
| `analysis/load_data.py` | 5 | 7 | 42% |
| `analysis/models/curve_model.py` | 5 | 7 | 42% |
| `analysis/models/predict_optimal_frequency.py` | 4 | 8 | 33% |
| `analysis/analyze_sweep.py` | 2 | 10 | 17% |
| `tools/frequency-sweep/gpu_workload.py` | 2 | 10 | 17% |
| `analysis/analyze_fine_sweep.py` | 1 | 11 | **8%** |
| **total** | **69** | **86** | **45%** |

**Zero of 155 mutants were invalid** — none landed on the wrong line, none failed to parse, none
were no-ops. That matters for reading the score: it is not diluted by junk.

## 🔑 The finding is structural, not a list of oversights

**68 of the 86 survivors sit in functions their owning suite never calls.**

The suites are not weak on what they cover. On `curve_model.py`, every one of the three mutants
inside the three functions `test_curve_model.py` calls was killed, and six of seven survivors
landed in functions it never calls at all. That pattern holds across the thirteen files.

So 45% does not mean "the tests are half broken". It means the suites test the pure helpers and
not the code that produces the output. The distinction changes what to do about it: "the tests
are weak" invites rewriting them, "the tests do not reach `evaluate()`" names the function to
write a test for.

## Blast radius: most survivors cannot reach the paper

The score alone overstates the risk, because the paper's numbers do not come from these display
paths. `claims_*.py` recomputes every pinned figure from the CSVs through `audit_claims`, so a
bug in a reporting function misleads whoever is reading terminal output without touching a
number in `PAPER_DRAFT.md`.

**`analyze_sweep.py` is the clearest case, and its 17% is misleading.** `audit_claims` imports
`loadSweep` from it, so that one function is on the path of every claim in the project. Both
mutants that landed in `loadSweep` were **killed**. All eight survivors are in `describe()`,
which the auditor bypasses entirely.

That is defence in depth working as intended, and it should be stated rather than assumed. It is
not a reason to leave the gaps: `describe()` is what the operator reads while deciding whether a
sweep is worth keeping, and three of its survivors invert a printed ratio —

```python
# analysis/analyze_sweep.py:101, survived
print(f"  efficiency gain  : {100*(peak['efficiency']/fastest['efficiency'] - 1):.1f}%")
#                                   ^^^^ swapping these two survives every check
```

An inverted efficiency gain on screen is exactly the kind of thing that gets a good run thrown
away or a bad one kept.

## The 18 survivors inside functions the suites do call

These are assertion gaps rather than coverage holes. Six are probably **equivalent mutants** —
five of the form `>=` → `>` on a floor comparison that already subtracts a tolerance, which can
only flip for a value sitting exactly at `floor - 1e-9`, plus a bootstrap that resamples
`fitted - residuals` instead of `fitted + residuals`, distributionally near-identical for
symmetric residuals.

The remaining twelve are real. The ones worth fixing first:

| where | mutation | what it breaks |
|---|---|---|
| `gpu_workload.py:685` | `wall - monitoring` → `wall + monitoring` | the performance metric itself |
| `gpu_workload.py:592` | `bytesPerElement * 3.0` → `* 2.0` | `membw` work per iteration |
| `ask_local.py:388` | `stopReason == "length"` → `== "stop"` | the truncation detector |
| `characterize.py:117` | `len(insensitive) > 0` → `>= 0` | a warning that always fires |
| `characterize.py:123` | `len(sensitive) > 0` → `< 0` | a warning that never fires |

The `ask_local.py` one is pointed: that check is what caught truncated replies during this very
run, and its suite's 48 checks never verify it works.

One was chased and could not be resolved. `evaluateStrategy()` computes `worst_regret_pct` as
`np.max(regrets)`; mutated to `np.min` it survives. The field is computed in three modules and
printed, but no paper number could be traced to it — so it is a genuine assertion gap of
**unconfirmed** consequence, not a live error in §5.6.

## Caveats

- **n = 1 per mutant**, and each is one model's guess at a meaningful change. Where the mutant is
  weak the kill is weak, and a kill only proves *something* noticed, not that the right thing did.
- **"Called" is not "covered".** The 18 above are in functions the suite invokes; that does not
  prove the mutated *branch* was reached. Some may be unreachable paths rather than missing
  assertions.
- **Twelve mutants per file is a sample, not an audit.** A second run at a different seed would
  find different ones. The score is a floor on test quality, not a grade.
- Equivalent-mutant classification above is **judgement, not measurement**. The six were reasoned
  about, not proven equivalent.

## What the harness itself is worth

`run_mutants.py` edits tracked source in place, so it was gated before its verdicts were trusted:
`gate_harness.py` injects ten deliberate bugs into the harness and checks `test_mutation.py`
notices. **10/10 caught.**

Two of its checks were found weak on the first gate run and fixed — a line-0 check that passed
for the wrong reason, and a bracket-in-string check whose bracket was balanced, so the scan
landed correctly even with string tracking disabled. Both would have made the harness look
better than it was, which is the failure this whole exercise exists to catch, one level up.

A third bug was found by running it rather than gating it. `gpu_workload.py` carries a UTF-8 BOM;
`compile()` on text held in memory rejects the stray U+FEFF, so all twelve of that file's mutants
were refused as "does not parse" and the fault looked like the model's. The BOM is now stripped
for the compile check only — `readLines`/`writeLines` keep it, or restoring would drop byte zero
of a tracked source.

## What was done with it

Two things, then a deliberate stop.

**`analyze_sweep.describe()` now has coverage, 17% to 80%.** All eight survivors killed; the two
left are in `main()`. The checks were drafted by the local model from a specification naming the
mutants they had to kill, and **two of nine were wrong**. One asserted a substring a padded format
never produces, and failed on unmutated source. The other asserted the peak row draws a full
40-character bar — the one row where inverting the ratio changes nothing, since the peak row's
efficiency IS the divisor — so it passed against the very mutant it was written for. Both were
caught mechanically by re-running the mutants, which is the property that makes delegating this
kind of work safe.

**The declared arithmetic-intensity column is now pinned** by `5.5-intensity-*` in
`claims_consumer.py`. That began as a test task and became a claim, because the gap was not where
it looked. `test_gpu_workload.py` compares `suiteDeclaredIntensity()` against a longhand
`builderIntensity()` written out in the test file, and `buildSuiteWorkload()` — the code that runs
on the card — is in neither side of that comparison. Six of its coefficients survived mutation.
Fixing it properly means extracting the builder's arithmetic so the runtime path is the tested
path, which is a change to the collection tool with 3070 Ti runs still outstanding on it, so it is
deferred. The claims bound the damage rather than closing the gap: a drift in the builder alone
still goes unnoticed. Gated by changing four shape constants, all four caught — the conv case
renders ``| `conv` | 144 |``, exactly the wrong value the original hand-written table carried.

## Not done, on purpose

The remaining 34 functions and 60 survivors were left. Seven are `main()`, roughly twelve are
`report()`/`describe()` shaped, and the blast-radius section above says why those are second tier:
the auditor recomputes every pinned figure from the CSVs, so a bug there misleads an operator
rather than the paper. Driving 45% toward 70% would improve a number without improving the
finding, and the collection gaps — the 3070 Ti's remaining priorities, replicates for a dataset
that is n=1 throughout, a failure detector that has never seen a failure — are what a reader will
name first.
