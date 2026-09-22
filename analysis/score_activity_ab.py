"""Score the activity A/B test. Written and committed BEFORE collection, 2026-09-22.

The design and every threshold below are registered in docs/REGISTERED-PREDICTIONS.md section 5.
Changing a threshold after the data exists turns a registered test into a fitted one - if a rule
here turns out to be wrong, say so in the write-up and report BOTH the registered verdict and any
revised one, never only the revised one.

    python analysis/score_activity_ab.py C:\\headroom-bench\\results\\activity-ab-<stamp>

What it measures. Every scored run sweeps the same 13 targets. For each target the ENVELOPE is the
best throughput any scored run reached there. A point is DEGRADED if it falls more than
DEGRADE_PCT below that envelope. The 2026-09-22 losses were 8-11 pct; a quiet three-run set agreed
to better than 0.1 pct, so 2 pct sits far above the noise and far below the effect.

What it cannot do. The active condition is a scripted PROXY for agent activity. A null result
weakens the activity hypothesis for that proxy only.
"""
import glob
import json
import os
import sys

import pandas as pd

DEGRADE_PCT = 2.0          # registered
SUPPORT_MARGIN = 4         # registered: active must exceed silent by at least this many points
SUPPORT_MIN_ACTIVE_RUNS = 3  # registered: ...and the losses must appear in at least this many active runs
NULL_MARGIN = 1            # registered: active exceeding silent by at most this is "not supported"
SILENT_LOSSES_MEAN_OTHER_CAUSE = 3  # registered


def findSweepCsv(label, roots):
    for root in roots:
        hits = glob.glob(os.path.join(root, "**", f"*_{label}_sweep.csv"), recursive=True)
        if len(hits) == 1:
            return hits[0]
        if len(hits) > 1:
            raise SystemExit(f"Ambiguous: {len(hits)} sweep CSVs for {label} under {root}.")
    return None


def loadRuns(experimentDir, extraRoots=()):
    with open(os.path.join(experimentDir, "experiment.json"), encoding="utf-8-sig") as f:
        records = json.load(f)
    if isinstance(records, dict):
        records = [records]
    roots = [os.path.dirname(os.path.abspath(experimentDir)), *extraRoots]
    runs, excluded = [], []
    for r in records:
        if r["condition"] == "warmup":
            excluded.append((r["label"], "warm-up, excluded by registration"))
            continue
        if r.get("wrapper_exit") != 0:
            excluded.append((r["label"], f"wrapper exit {r.get('wrapper_exit')}"))
            continue
        if r["condition"] == "active" and not r.get("load_seen"):
            excluded.append((r["label"], "active run whose generator never started"))
            continue
        path = findSweepCsv(r["label"], roots)
        if path is None:
            excluded.append((r["label"], "sweep CSV not found"))
            continue
        sweep = pd.read_csv(path, encoding="utf-8-sig")
        runs.append({**r, "sweep": sweep, "path": path})
    return runs, excluded


def eventsInWindow(eventLog, start, end):
    if not eventLog or not os.path.exists(eventLog):
        return {}
    events = pd.read_csv(eventLog)
    inside = events[(events.end_unix >= start) & (events.start_unix <= end)]
    return inside.event.value_counts().to_dict()


def score(runs):
    table = pd.concat(
        [run["sweep"][["target_frequency_mhz", "bench_throughput"]].assign(order=run["order"]) for run in runs])
    envelope = table.groupby("target_frequency_mhz").bench_throughput.max()
    perRun = []
    for run in runs:
        sweep = run["sweep"]
        loss = 100 * (1 - sweep.bench_throughput.values / envelope.loc[sweep.target_frequency_mhz].values)
        degraded = [(int(t), round(float(l), 2)) for t, l in zip(sweep.target_frequency_mhz, loss) if l > DEGRADE_PCT]
        eventsAtDegraded = [
            eventsInWindow(run.get("event_log"), sweep.window_start_unix[i], sweep.window_end_unix[i])
            for i in range(len(sweep)) if loss[i] > DEGRADE_PCT]
        perRun.append({"order": run["order"], "tag": run["tag"], "condition": run["condition"],
                       "uptime": run.get("uptime_min_at_start"), "degraded": degraded,
                       "events_at_degraded": eventsAtDegraded,
                       "temp_range": (sweep.temperature_avg_c.min(), sweep.temperature_avg_c.max())})
    return perRun


def verdict(perRun):
    active = [r for r in perRun if r["condition"] == "active"]
    silent = [r for r in perRun if r["condition"] == "silent"]
    dA = sum(len(r["degraded"]) for r in active)
    dS = sum(len(r["degraded"]) for r in silent)
    activeRunsHit = sum(1 for r in active if r["degraded"])
    lines = [f"Degraded points (> {DEGRADE_PCT} pct below the per-target envelope): "
             f"ACTIVE {dA} across {len(active)} runs ({activeRunsHit} runs hit), SILENT {dS} across {len(silent)} runs."]
    if len(active) < 6 or len(silent) < 6:
        lines.append(f"INCOMPLETE: the registration requires 6 scored runs per condition; have "
                     f"{len(active)} active and {len(silent)} silent. The verdict below is NOT the registered one.")
    if dA >= dS + SUPPORT_MARGIN and activeRunsHit >= SUPPORT_MIN_ACTIVE_RUNS:
        lines.append("VERDICT: ACTIVITY SUPPORTED - the scripted activity produces isolated losses that "
                     "silence does not, on a warm card, with run order balanced.")
    elif dA <= dS + NULL_MARGIN:
        lines.append("VERDICT: NOT SUPPORTED FOR THIS PROXY - the scripted activity does not add losses. "
                     "It does not rule out the parts of real agent activity the proxy does not imitate.")
    else:
        lines.append("VERDICT: INCONCLUSIVE - between the registered thresholds.")
    if dS >= SILENT_LOSSES_MEAN_OTHER_CAUSE:
        lines.append(f"ALSO: {dS} losses in SILENT runs on a warm card - something other than this activity "
                     "produces them.")
    if dA + dS == 0:
        lines.append("ALSO: no losses at all. The 2026-09-22 losses happened on a cold card and/or under real "
                     "agent activity; this run removed the first and imitated the second, so they are still "
                     "not separated.")
    return lines


def main():
    if len(sys.argv) < 2:
        raise SystemExit("Usage: python analysis/score_activity_ab.py <experiment directory> [extra search root ...]")
    runs, excluded = loadRuns(sys.argv[1], sys.argv[2:])
    for label, why in excluded:
        print(f"Excluded {label}: {why}.")
    if not runs:
        raise SystemExit("No scorable runs.")
    perRun = score(runs)
    print("Per run, in collection order:")
    for r in perRun:
        print(f"  {r['order']:>2} {r['tag']:<12} {r['condition']:<7} uptime {r['uptime']} min, "
              f"temp {r['temp_range'][0]:.1f}-{r['temp_range'][1]:.1f} C, degraded {r['degraded']}")
        for e in r["events_at_degraded"]:
            print(f"       events inside a degraded window: {e}")
    blocks = {}
    for i, r in enumerate(perRun):   # index among SCORED runs, so the warm-ups do not shift blocks
        blocks.setdefault(i // 4 + 1, 0)
        blocks[i // 4 + 1] += len(r["degraded"])
    print(f"Degraded points by block of four (a time trend shows here, not in the verdict): {blocks}")
    for line in verdict(perRun):
        print(line)
    print("This is one chip, one session, and a scripted proxy for agent activity. "
          "Event overlap is descriptive: the generator cycles every 5 s, so most windows overlap some event.")


if __name__ == "__main__":
    main()
