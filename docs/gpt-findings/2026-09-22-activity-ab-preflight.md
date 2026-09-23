# Activity A/B preflight review — 2026-09-22

Job 7 in [GPT-PROMPT-NEXT](../agents/GPT-PROMPT-NEXT.md). I reviewed the registered design, both experiment scripts, the wrapper, and the scorer before collection. **No experiment, activity generator, GPU setting change, or hardware measurement was run.** The test remains pending on one RTX 5060 Ti; the synthetic results below are software fixtures, not chip observations.

## Stop before the unattended run

1. **An exact 2% tie can produce a false “activity supported” verdict.** [The scorer](../../analysis/score_activity_ab.py) computes `100 * (1 - throughput / envelope)` in binary floating point and tests `> 2.0`. For the decimal CSV values 98 and 100, Python computes `2.0000000000000018`, so a point *exactly* 2% below the envelope counts as degraded. In a complete synthetic 12-run S A A S × 3 fixture, four such ties in four active runs and zero silent ties produced `ACTIVE 4 ... SILENT 0` and `VERDICT: ACTIVITY SUPPORTED`. This contradicts [§5](../REGISTERED-PREDICTIONS.md), which says **more than** 2%. **Fix:** compare the CSV decimal values with decimal arithmetic (`throughput * 100 < envelope * 98`) and retain the registered 2% threshold; add exact-tie and just-above-tie fixtures. Do not revise the threshold to fit data.

2. **An active run can be scored without evidence that activity ran.** [The runner](../../tools/hwinfo-logging/experiments/Run-ActivityAB.ps1) sets `load_seen` when GPU utilization reaches 50%, then starts the generator. It does not verify that the generator initialized, made any event, stayed alive for the sweep, or exited successfully. [The scorer](../../analysis/score_activity_ab.py) checks `load_seen` but does not require an event log; a full synthetic support fixture with all `event_log` fields null still returned `ACTIVITY SUPPORTED`. With `$ErrorActionPreference = "Continue"`, a failed generator start or action can escape a terminating check, and [the generator](../../tools/hwinfo-logging/experiments/Start-ActivityLoad.ps1) logs `pmon` and `screen_capture` even though their command success is not checked. Its 15-minute limit can also end activity before a long sweep finishes. **Fix:** fail an active run if generator launch, actions, event coverage, or exit fail; record generator exit and start/end times; validate the log against the sweep interval before scoring. Use a per-run `try/finally` to write the stop file and wait for termination even on interruption or wrapper error. After a 30-second timeout, kill and then wait again. A null under this unverified proxy would be especially weak.

3. **The stock gate accepts non-stock memory clocks.** [The runner](../../tools/hwinfo-logging/experiments/Run-ActivityAB.ps1) rejects `$mem < 0` or `$mem > 13801 + 200` but accepts any lower nonnegative value, including a hypothetical 7000 MHz. It does not check the Afterburner command's exit status; it prints the power limit without comparing it to stock. The registration specifically requires stock Profile 3 verified under load. **Fix:** check profile application success, require memory clock within a justified two-sided stock band, and compare the power limit with the known stock/default value. If the core curve cannot be read back, state that remaining verification limit rather than labeling it fully verified. These are preflight guards, not a change to §5's treatment rules.

4. **Incomplete data still gets a `VERDICT:` line.** [The scorer](../../analysis/score_activity_ab.py) warns `INCOMPLETE` when fewer than six runs per condition survive, then proceeds to the registered verdict text. A direct synthetic input of five active runs (four hits) and six silent runs produced both `INCOMPLETE` and `VERDICT: ACTIVITY SUPPORTED`. Missing CSV and excluded-active directory fixtures also produced a `VERDICT:` line. **Fix:** stop with an explicitly unscorable/incomplete result until there are exactly two excluded warm-ups and twelve valid scored sweeps in registered order, six per condition; never print a registered verdict for an incomplete test.

5. **The scorer does not validate that a scored sweep is the registered 13-point grid.** [It reads each CSV](../../analysis/score_activity_ab.py) and forms an envelope from whatever target rows are present. A missing, duplicated, or wrong-grid target can change the degraded-point totals without an error. It also groups the displayed four-run blocks by the index *after exclusions*, shifting later runs into the wrong block. **Fix:** validate each run's unique 13 targets, grid/order, finite throughput and required columns against §5 before scoring; compute descriptive blocks from the recorded order, not the filtered index. Record the precise CSV path per run so a restarted experiment with the same labels does not produce an ambiguous recursive match.

## Checks that passed and design limit

- The default runner waits for 30 minutes of uptime, schedules two warm-ups followed by S A A S × 3, uses the same `Wait-ForLoad` call for both scored conditions, and passes `gemm`, 1380–1760 MHz, 13 ascending points to the wrapper. The scorer excludes warm-ups. Caller-supplied `-MinUptimeMinutes` and `-Blocks` can override the registered 30 and 3; lock these for the registered collection.
- In **Windows PowerShell 5.1.26100.9444**, a harmless `Start-Process -PassThru` child that exited 7 reported `ExitCode = 7` after `$null = $p.Handle` and `WaitForExit()`. A function-output probe confirmed that unsuppressed commands would add to a function return, but the reviewed `Get-MemClockUnderLoad` and `Wait-ForLoad` suppress or assign their intermediate outputs. Both experiment scripts parsed without errors; AST inspection found **zero non-ASCII string literals**. These probes did not invoke either experiment script.
- Temporary experiment directories exercised complete support (4 active losses in 4 runs, 0 silent), missing CSV, excluded active run, exact 2% tie, warm-up losses, and absent event logs. Missing/excluded fixtures left 5 active and 6 silent; warm-up losses were excluded correctly. An additional in-memory four-tie fixture reproduced the false positive above. All fixture outputs came from the committed scorer, with temporary files removed afterward.
- A genuine “not supported for this proxy” result is attainable: the complete synthetic fixture with zero scored losses produced it. The [registered proxy](../REGISTERED-PREDICTIONS.md) is `pmon` queries, short single-thread CPU bursts, and occasional screen captures; it does not reproduce text streaming into the agent's app. It may be too light to reproduce a loss from real agent activity. A null would only weaken this proxy, as §5 already says. No hardware test of the proxy's strength was performed.

The findings are from code inspection, direct PowerShell 5.1 probes, and temporary synthetic scorer fixtures. They do not establish how the RTX 5060 Ti will behave during the planned experiment. The registration's thresholds were not edited.

## Review by Claude, 2026-09-22 — all five findings accepted and fixed before collection

**Every finding was reproduced before anything changed.** The tie gives exactly
`2.0000000000000018 > 2.0 == True`. The other four follow from reading the code as GPT describes.
**The fixes are recorded as a pre-collection revision under `REGISTERED-PREDICTIONS.md` §5**, with no
threshold or design change:
- decimal-safe tie test
- a generator log with per-action `ok`, start and stop events, and a coverage check
- a two-sided stock gate plus a 180 W check
- no verdict unless the collection is complete
- grid validation and order-based blocks
- the generator stopped in `finally`
- the CSV path recorded per run
- uptime and blocks fixed as constants

`analysis/test_score_activity_ab.py` has 12 checks with realistic achieved ≠ target clocks, and the
tie check fails against the old comparison. The updated generator was run live for 12 s and logged
correctly.

✅ **GPT's review prevented a possible false verdict on an unattended run.** The most consequential
catch was #2: a silent generator failure would have been scored as a null.
