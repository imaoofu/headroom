# Grid-aware achieved-clock count, 2026-09-22

This answers Job 6 in `docs/agents/GPT-PROMPT-NEXT.md`. No sweep was run and no GPU state was changed. All committed CSV and JSON files under `data/` were read only.

## Corrected example and reproduction

⛔ **The prompt's run date was wrong.** It attributed “10 against 13 genuinely distinct clocks” to the 2026-09-18 fine-floor run. I recomputed the existing 25 MHz grouping from both [09-18 fine-floor CSVs](../../data/frequency-sweeps/5060ti-finefloor-20260918/README.md): each gives **13 of 13**, exactly as its committed JSON reports. The source of **10 against 13** is the [RTX 2060 Super run from 2026-09-15](../../data/frequency-sweeps/rtx2060s-finefloor-20260915/README.md). Its 13 achieved clocks are distinct and all `lock_held=True`; the fixed 25 MHz grouping merges 945/960, 1020/1035 and 1065/1080 MHz. The mistaken prompt copied the count from the 09-15 run and attached the later run's date. The prompt now carries a dated correction; the original claim remains quoted there.

Another clear example is the [2026-09-22 4h floor-end pair](../../data/frequency-sweeps/5060ti-finefloor-20260922/README.md): both 13-point runs have 7–8 MHz target spacing and all locks held, but the old field reports **4**. The new grouping reports **13** for each. These are read-only recomputations, not new measurements. Historical JSON remains unchanged and must be interpreted under the old rule.

## Change and verification

[`ClockBuckets.ps1`](../../tools/frequency-sweep/ClockBuckets.ps1) calculates bucket width as the smaller of 25 MHz and half the smallest positive requested target gap. [`Invoke-FrequencySweep.ps1`](../../tools/frequency-sweep/Invoke-FrequencySweep.ps1) uses it only when grouping achieved clocks for the JSON count and the duplicate-clock message. It does not participate in applying clocks or accepting measurement points. A 15 MHz grid gets 7.5 MHz buckets; the 7 MHz grid gets 3.5 MHz buckets; any grid whose smallest gap is at least 50 MHz keeps the original 25 MHz calculation.

The read-only [regression suite](../../tools/frequency-sweep/test_clock_buckets.py) invokes the actual PowerShell helper. It verified **10→13** on the 09-15 run; **13→13** on each of two 09-18 runs; **4→13** on each of two 09-22 runs; and **unchanged historical counts in all 404 committed sweep CSVs whose smallest target gap is at least 50 MHz**. It also checks a synthetic clipped pair remains one achieved-clock group. The 404 count was recomputed by enumerating committed CSV files in the test; it is not a project-wide count of all sweeps. No live hardware behavior was tested.

The corrected field is a grouping heuristic on per-point average clocks. It does not prove frequency stability within a point, and a clipped run whose achieved averages straddle a bucket boundary can still require manual CSV inspection. Per-point lock checks remain the more direct evidence that a requested cap held.

After the edits, `python run_tests.py --quiet` passed **913 checks in 27 suites**; `audit_claims.py`, `build_data_manifest.py --check` and `verify_citations.py --check` also passed. These are repository checks, not a live sweep validation.

## Review by Claude, 2026-09-22 — accepted, plus one kit fix

**Checked:**
- the change is reporting-only: grouping for the count, never locking or measurement
- `$targets` is defined (line 451) before the new call uses it
- the helper is ASCII-only, as PowerShell 5.1 requires
- GPT's regression tests pass, including 404 coarse sweeps with unchanged counts
- a 50 MHz grid keeps the old 25 MHz bucket, so the 4c run is unaffected

**GPT's correction of the prompt is right**: the 10-versus-13 case is the 2026-09-15 RTX 2060 Super
run. The prompt, written by Claude, had the wrong date.

**Added: `ClockBuckets.ps1` to `tools/collection-kit/Sync-Kit.ps1`.** The sweep now dot-sources it,
and the kit sync did not copy it. So on a shop machine the kit's sweep would have failed at the end
of a run, after every measurement. That is the worst place to fail.
