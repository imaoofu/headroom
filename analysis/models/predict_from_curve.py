"""
Predict a workload's efficiency-optimal frequency by READING THE V/F CURVE, not by fitting.

WHAT THIS ASKS
    Every other model in this directory predicts the optimum from MEASUREMENTS of the workload -
    probe it at a few frequencies, fit something, pick a peak. All of them tie or lose to a
    constant, and `models/README.md` explains why: on the public V100 set 952 MHz is optimal for
    24 of 33 workloads, so there is almost no per-workload variance left to exploit.

    This module asks a different question. On the 5060 Ti the same twelve workloads were swept
    under four DIFFERENT applied V/F curves, and the optimum moves with the curve: a decomposition
    over 180 sweeps put 61.9% of the optimum's variance on the configuration and 19.0% on the
    workload. The V100 dataset contains exactly ONE configuration, so that 62% is invisible in it
    by construction - which is a structural property of that dataset, not a failure of modelling.

    So: can the optimum be predicted from the applied curve alone, with no measurement of the
    workload at all?

THE PREDICTOR, IN FULL
    The optimum is the last frequency the V/F curve reaches at the card's LOAD FLOOR voltage.

    That is the whole thing. One constant - the 0.720 V load floor, measured once by HWiNFO in
    data/frequency-sweeps/voltage-curve-20260908/ - plus the decoded curve, which is free: it is
    read out of the Afterburner profile store in milliseconds with no benchmark run at all.

    ⚠️ IT IS NOT "ZERO-PARAMETER" IN A FAIR COMPARISON. It uses the V/F curve, which the constant
    and the Ridge baselines never had. That is not cheating - the curve costs nothing to obtain -
    but it IS a different information set and saying otherwise would overstate the result. The
    honest claim is "there is a free feature nobody was using", not "fitting was done better".

WHAT IT SCORES, AND THE DEFLATION THAT COMES WITH IT
    Run this file to see the ladder. The summary, on 192 sweeps:

      - It beats the best single fixed frequency by ~2.9x on mean regret.
      - It TIES a best-constant-per-configuration fitted with full hindsight, to three decimals,
        because it picks the identical frequency every time. So it extracts everything the
        configuration axis has to offer, for free - and nothing more than that.
      - ⚠️ And the whole axis is worth about 1.3 points of regret, against a headroom of 30-57
        points. Predictor choice barely matters. This is the V100 null generalising, now with a
        mechanism attached rather than left as an observation.

    Reported honestly by main(), which prints a verdict against this module when it fails to beat
    a baseline - the same rule predict_optimal_frequency.py is held to. Do not "fix" a loss by
    tuning until it wins.

LIMITS
    One chip. Four configurations but only TWO distinct predicted values (1537 and 2002), so
    "configuration" is close to a binary variable here and the 61.9% should be read with that in
    mind.

⛔ THE FLOOR VOLTAGE DOES NOT TRANSFER BETWEEN CARDS. CORRECTED 2026-09-10.
    This docstring said the floor "was measured on this card and is assumed to transfer; whether it
    is a property of the silicon, the vendor, or this board is not established." It is now
    established, and the assumption was wrong.

    An RTX 3060 (Ampere, 8 nm) has a load floor of 0.756 V, not 0.720. Its floor ends at 1260 MHz
    and its efficiency optimum is 1260 MHz - the rule holds exactly, with a different constant.
    See data/frequency-sweeps/rtx3060-20260910/.

    🔑 THE RULE TRANSFERS; THE PARAMETER IS PER CARD. That is a better result than a shared
    constant would have been - a shared value would most likely have meant a driver policy, where a
    differing one means the floor is a property of the silicon and the relationship survives it
    anyway.

    ⚠️ SO FLOOR_VOLTAGE_MV BELOW IS A 5060 Ti CONSTANT, NOT A PROJECT CONSTANT. Applying this
    predictor to a new card REQUIRES measuring that card's floor first. Borrowing 0.720 V for the
    3060 would predict ~1530 MHz against a true optimum of 1260 - a 270 MHz error, worse than the
    best single constant. The evaluation below is 5060 Ti data only and is correct as it stands;
    nothing here is fitted across cards.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "analysis"))

from audit_claims import sweep  # noqa: E402

SWEEP_ROOT = REPO_ROOT / "data" / "frequency-sweeps"

# The one measured constant, FOR THIS CARD. data/frequency-sweeps/voltage-curve-20260908/ observed
# 70 loaded samples on the floor, every one of them exactly 0.720 V, across two configurations;
# voltage-curve-20260909 confirmed the same value on two more.
#
# ⛔ NOT A PROJECT CONSTANT. An RTX 3060 measures 0.756 V. Measure a new card's floor before
# applying this predictor to it - see the LIMITS section of the module docstring.
#
# ⚠️ It is a LOAD floor, not the card's minimum voltage - the same log shows 0.650 V at idle.
# "The card will not run loaded below 0.720 V" is what the data supports.
FLOOR_VOLTAGE_MV = 720.0

# Decoded curves come from the COMMITTED snapshot, not the live machine, so this is reproducible
# on any checkout. Profile 3 holds stock as of 2026-09-08.
PROFILE_SNAPSHOT = REPO_ROOT / "data" / "afterburner-profiles" / \
    "5060ti-profiles-20260908b-p4-plateau-3030.json"

CONFIGURATION_PROFILE = {
    "stock": "Profile3",
    "split": "Profile5",
    "repair": "Profile2",
    "fulltune": "Profile4",
}

# (directory, tag) per sweep set. Twelve workloads live under each.
#
# ⚠️ These are globbed by directory+tag rather than listed as 192 explicit paths, which is NOT the
# convention claims_*.py follows. The reason claims list paths explicitly is a real collision:
# suite-replicate-r2-20260830/ also holds bgemm64 sweeps tagged -r3 and -r4 from a separate early
# set. sweepPath() below asserts EXACTLY ONE match, which turns that collision into a loud error
# instead of a silent wrong file. A claim may not take that risk; a model that fails loudly may.
CONFIGURATION_RUNS = {
    "stock": [
        ("suite-replicate-r3-20260902", "r3"),
        ("suite-replicate-r4-20260904", "r4"),
        ("suite-replicate-r5-20260904", "r5"),
        ("suite-replicate-r6-20260905", "r6"),
        ("suite-replicate-r7-20260906", "r7"),
        ("suite-replicate-r8-20260908", "r8"),
        ("stock-bracket-20260909", "r9"),
    ],
    "fulltune": [
        ("abba-20260908", "a1"),
        ("abba-20260908", "a2"),
        ("stock-bracket-20260909", "p4t1"),
        ("stock-bracket-20260909", "p4t2"),
    ],
    "split": [
        ("abba-20260908", "b1"),
        ("abba-20260908", "b2"),
        ("splitcurve-suite-20260907", "s1"),
        ("splitcurve-suite-s2-20260908", "s2"),
    ],
    "repair": [
        ("repair-suite-p2-20260909", "p2t1"),
    ],
}

SUITE_WORKLOADS = ["copy", "reduce", "softmax", "layernorm", "bgemm32", "bgemm64",
                   "bgemm128", "bgemm256", "bgemm1024", "attention", "conv", "gemm"]


def decodeCurve(profileName, snapshotPath=PROFILE_SNAPSHOT):
    """(voltage_mV, applied_MHz) pairs for one profile, sorted by voltage, from the snapshot.

    ⚠️ A naive stride-3 read of the raw blob mispairs at the zero-offset boundary and yields an
    impossible ~6000 MHz point near 937 mV. The snapshot stores points as decoded INCLUDING that
    artifact, deliberately, so the capture stays lossless. Filtering is the reader's job, so it
    happens here: 3090 MHz is the top of this card's supported-clock table.
    """
    import json
    blob = json.loads(Path(snapshotPath).read_text(encoding="utf-8"))
    profiles = blob.get("profiles", blob)
    points = [(float(p["voltage_mv"]), float(p["applied_mhz"]))
              for p in profiles[profileName]["curve_points"]
              if 100.0 <= float(p["applied_mhz"]) <= 3090.0]
    if not points:
        raise ValueError(f"{profileName}: no curve points survived the 3090 MHz filter")
    return sorted(points)


def clockAtVoltage(curve, millivolts):
    """The clock the curve reaches at `millivolts`, linearly interpolated between its points."""
    below = [p for p in curve if p[0] <= millivolts]
    above = [p for p in curve if p[0] >= millivolts]
    if not below:
        return curve[0][1]
    if not above:
        return curve[-1][1]
    low, high = max(below), min(above)
    if low[0] == high[0]:
        return low[1]
    span = (millivolts - low[0]) / (high[0] - low[0])
    return low[1] + span * (high[1] - low[1])


def floorExtentMhz(configuration, snapshotPath=PROFILE_SNAPSHOT):
    """The frequency at which this configuration's V/F curve leaves the load floor.

    ⚠️ Profile 4's plateau was raised 3015 -> 3030 on 2026-09-08, between the `abba` legs and the
    later ones. This reads the POST-edit snapshot for both, which is correct here and would not be
    for a top-end quantity: the edit changed 49 points at 940 mV and above and left the
    low-voltage region byte-identical, and the floor sits at 720 mV.
    """
    if configuration not in CONFIGURATION_PROFILE:
        raise ValueError(
            f"no Afterburner profile is mapped to configuration {configuration!r}. "
            f"Known: {sorted(CONFIGURATION_PROFILE)}. The mechanism predictor cannot run on a "
            f"configuration whose applied curve is unknown - that is the whole input.")
    profileName = CONFIGURATION_PROFILE[configuration]
    return clockAtVoltage(decodeCurve(profileName, snapshotPath), FLOOR_VOLTAGE_MV)


def sweepPath(directory, workload, tag):
    """The one sweep CSV for this (directory, workload, tag). Raises unless exactly one matches."""
    matches = sorted((SWEEP_ROOT / directory).glob(f"*-{workload}-{tag}_sweep.csv"))
    if len(matches) != 1:
        raise ValueError(
            f"{directory}/{workload}-{tag}: expected exactly 1 sweep, found {len(matches)}")
    return matches[0].relative_to(SWEEP_ROOT).as_posix()


def loadEfficiencyCurves(runs=None, workloads=None):
    """[(configuration, workload, {commanded target MHz: efficiency})] for every sweep."""
    runs = CONFIGURATION_RUNS if runs is None else runs
    workloads = SUITE_WORKLOADS if workloads is None else workloads
    curves = []
    for configuration, sets in runs.items():
        for directory, tag in sets:
            for workload in workloads:
                rows = sweep(sweepPath(directory, workload, tag))
                curves.append((configuration, workload,
                               {target: row["efficiency"] for target, row in rows.items()}))
    return curves


def regretFor(curve, chosenTarget):
    """
    Efficiency given up by running at `chosenTarget` instead of this sweep's best, in percent.

    Relative to the sweep's own peak, so it is comparable across configurations that reach very
    different absolute efficiencies. Zero means the choice was exactly optimal.

    Regret is the honest metric and frequency error is not: near an optimum the efficiency curve
    is flat by construction, so a 150 MHz miss can cost nothing at all while looking dramatic in
    megahertz. An earlier version of this analysis reported mean absolute error in MHz and
    understated the result by a factor of about 1.3 as a consequence.
    """
    best = max(curve.values())
    return 100.0 * (1.0 - curve[chosenTarget] / best)


def nearestTarget(targets, mhz):
    """The grid target closest to `mhz`. Ties go to the lower target."""
    return min(sorted(targets), key=lambda t: (abs(t - mhz), t))


def evaluateStrategy(curves, chooseTarget):
    """Score one strategy. `chooseTarget(configuration, workload, curve) -> target`."""
    regrets, exact = [], []
    for configuration, workload, curve in curves:
        target = chooseTarget(configuration, workload, curve)
        regrets.append(regretFor(curve, target))
        exact.append(target == max(curve, key=lambda t: curve[t]))
    ordered = sorted(regrets)
    middle = len(ordered) // 2
    median = ordered[middle] if len(ordered) % 2 else (ordered[middle - 1] + ordered[middle]) / 2.0
    return {
        "mean_regret_pct": sum(regrets) / len(regrets),
        "median_regret_pct": median,
        "worst_regret_pct": max(regrets),
        "exact_match_rate": sum(exact) / len(exact),
        "n": len(regrets),
    }


def chooseByMechanism(curves):
    """THIS MODULE'S PREDICTOR - the grid point nearest where the curve leaves the load floor."""
    targets = set()
    for _, _, curve in curves:
        targets.update(curve)
    picks = {configuration: nearestTarget(targets, floorExtentMhz(configuration))
             for configuration in {c for c, _, _ in curves}}
    return lambda configuration, workload, curve: picks[configuration], picks


def chooseByBestFixedFrequency(curves):
    """Baseline - ONE frequency for everything, chosen with full hindsight over these sweeps.

    Hindsight is deliberate. A baseline this module has to clear should be as strong as it can
    possibly be made, not as weak as a fair split would leave it.
    """
    targets = sorted({t for _, _, curve in curves for t in curve})
    best = min(targets, key=lambda t: sum(regretFor(curve, t) for _, _, curve in curves))
    return (lambda configuration, workload, curve: best), best


def chooseByBestPerConfiguration(curves):
    """Baseline - one frequency PER CONFIGURATION, again chosen with full hindsight.

    🔑 This is the baseline that matters. It is what the mechanism predictor would have to be
    measured against if you were willing to sweep every configuration first, and the mechanism
    needs no sweeps at all. If the two tie, the mechanism has extracted everything the
    configuration axis holds - and nothing beyond it.
    """
    targets = sorted({t for _, _, curve in curves for t in curve})
    picks = {}
    for configuration in {c for c, _, _ in curves}:
        subset = [curve for c, _, curve in curves if c == configuration]
        picks[configuration] = min(targets,
                                   key=lambda t: sum(regretFor(curve, t) for curve in subset))
    return (lambda configuration, workload, curve: picks[configuration]), picks


def chooseByOracle():
    """Upper bound - the true optimum of every sweep. Regret zero by construction."""
    return lambda configuration, workload, curve: max(curve, key=lambda t: curve[t])


def regretByWorkload(curves, chooseTarget):
    """Mean regret per workload, worst first. Shows where a strategy's residual actually lives."""
    grouped = {}
    for configuration, workload, curve in curves:
        target = chooseTarget(configuration, workload, curve)
        grouped.setdefault(workload, []).append(regretFor(curve, target))
    return sorted(((w, sum(v) / len(v), max(v), len(v)) for w, v in grouped.items()),
                  key=lambda row: -row[1])


def main():
    curves = loadEfficiencyCurves()
    mechanism, mechanismPicks = chooseByMechanism(curves)
    perConfig, perConfigPicks = chooseByBestPerConfiguration(curves)
    fixed, fixedPick = chooseByBestFixedFrequency(curves)

    ladder = [
        ("oracle (true optimum per sweep)", chooseByOracle()),
        ("MECHANISM - curve read at the load floor", mechanism),
        ("best constant per configuration (hindsight)", perConfig),
        ("best single constant (hindsight)", fixed),
    ]

    print(f"Predicting the efficiency optimum from the applied V/F curve")
    print(f"{len(curves)} sweeps, {len(CONFIGURATION_RUNS)} configurations, one RTX 5060 Ti.")
    print(f"Load floor {FLOOR_VOLTAGE_MV:.0f} mV, measured in voltage-curve-20260908.\n")

    print(f"  {'strategy':<44}{'mean':>9}{'median':>9}{'worst':>9}{'exact':>9}")
    print("  " + "-" * 80)
    scores = {}
    for label, chooser in ladder:
        score = evaluateStrategy(curves, chooser)
        scores[label] = score
        print(f"  {label:<44}{score['mean_regret_pct']:>9.3f}"
              f"{score['median_regret_pct']:>9.3f}{score['worst_regret_pct']:>9.3f}"
              f"{score['exact_match_rate'] * 100:>8.1f}%")
    print("  " + "-" * 80)
    print("  Regret is efficiency given up, in percent. Lower is better.\n")

    print("  Where each strategy looks:")
    for configuration in sorted(mechanismPicks):
        print(f"    {configuration:<10} curve leaves the floor at "
              f"{floorExtentMhz(configuration):>7.0f} MHz  ->  mechanism picks "
              f"{mechanismPicks[configuration]:>5d}, "
              f"hindsight picks {perConfigPicks[configuration]:>5d}")
    print(f"    best single constant across everything: {fixedPick} MHz\n")

    mechanismScore = scores["MECHANISM - curve read at the load floor"]["mean_regret_pct"]
    perConfigScore = scores["best constant per configuration (hindsight)"]["mean_regret_pct"]
    fixedScore = scores["best single constant (hindsight)"]["mean_regret_pct"]

    print("  VERDICT")
    if mechanismScore > fixedScore:
        print("    The mechanism predictor LOSES to a single fixed frequency. Report that as the")
        print("    result. Do not tune it until it wins.")
    else:
        print(f"    Against the best single constant: {mechanismScore:.3f} vs {fixedScore:.3f} "
              f"({fixedScore / mechanismScore:.2f}x better).")

    if abs(mechanismScore - perConfigScore) < 0.001:
        print("    It TIES the hindsight-fitted per-configuration constant exactly - it picks the")
        print("    same frequency every time. So it extracts everything the configuration axis")
        print("    holds and nothing more; its value is needing no measurement, not being smarter.")
    elif mechanismScore > perConfigScore:
        print(f"    It LOSES to a hindsight per-configuration constant "
              f"({mechanismScore:.3f} vs {perConfigScore:.3f}), so reading the curve is worse than")
        print("    sweeping each configuration once. Report that.")
    else:
        print(f"    It BEATS a hindsight per-configuration constant "
              f"({mechanismScore:.3f} vs {perConfigScore:.3f}), which needs explaining before it")
        print("    is believed - a free predictor should not beat one fitted on the answers.")

    # ASCII only in PRINTED output. Windows consoles default to cp1252, which cannot encode the
    # warning emoji this repository uses in Markdown, and print() raises UnicodeEncodeError rather
    # than degrading. Docstrings and comments are never printed, so they keep theirs.
    print(f"\n    !! SCALE. The whole configuration axis is worth "
          f"{fixedScore - mechanismScore:.2f} points of regret,")
    print("    against a headroom of roughly 30-57 points. Predictor choice barely matters -")
    print("    which is the V100 null generalising, now with a mechanism rather than a shrug.\n")

    print("  Where the mechanism's residual lives:")
    print(f"    {'workload':<12}{'mean':>9}{'worst':>9}{'sweeps':>9}")
    rows = regretByWorkload(curves, mechanism)
    for workload, meanRegret, worst, count in rows:
        print(f"    {workload:<12}{meanRegret:>9.3f}{worst:>9.3f}{count:>9d}")
    worstTwo = [row[0] for row in rows[:2]]
    total = sum(row[1] * row[3] for row in rows)
    share = sum(row[1] * row[3] for row in rows if row[0] in worstTwo) / total
    print(f"\n    {', '.join(worstTwo)} carry {share * 100:.0f}% of the residual. "
          f"That is structure, not noise,")
    print("    and it is a mechanism question rather than a modelling one.")


if __name__ == "__main__":
    main()
