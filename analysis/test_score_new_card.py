"""Checks for score_new_card.py (REGISTERED-PREDICTIONS 11); no measurement files are written.

The floor classifier is first run on committed sweeps from three cards whose floors are already
known, so its definitions are checked against real readings, not only against fixtures.
"""

import csv
import json
import tempfile
from pathlib import Path

from score_new_card import WORKLOADS, classify_floor, score
from score_session_d import read_voltage

ROOT = Path(__file__).resolve().parents[1] / "data" / "frequency-sweeps"


def check(condition, message):
    if not condition:
        print(f"[FAIL] {message}")
        raise AssertionError(message)
    print(f"[PASS] {message}")


def real(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as handle:
        targets = [int(float(row["target"])) for row in csv.DictReader(handle)]
    return {t: r["voltage"] for t, r in read_voltage(ROOT / path, targets).items()}


DENSE = list(range(1236, 2500, 52))[:25]   # 25 points, like 40-80% of a 3090 MHz table
SUITE = [round(1236 + i * 154.5) for i in range(13)]


def dense_volts(floor_end, floor_v=0.720, dip_at=None):
    volts = {t: floor_v if t <= floor_end else round(floor_v + 0.005 * (1 + (t - floor_end) // 52), 3)
             for t in DENSE}
    if dip_at is not None:
        volts[DENSE[0]] = floor_v + 0.013   # voltage falls INTO the floor, as on the 2060 Super
    return volts


def write(root, label, targets, peak, volts=None, order=None, gpu="NVIDIA GeForce RTX 4060",
          power=("115.00", "115.00")):
    csv_path = root / f"20990101-000000_{label}_sweep.csv"
    meta = {"session_label": label, "gpu_name": gpu, "driver_version": "synthetic",
            "power_limit_enforced_w": power[0], "power_limit_default_w": power[1]}
    if order:
        meta["sweep_order"] = order
    csv_path.with_suffix(".json").write_text(json.dumps(meta), encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=(
            "target_frequency_mhz", "achieved_frequency_avg", "bench_throughput", "power_avg_w",
            "temperature_avg_c", "bench_ok", "lock_miss_direction", "power_window_applied"))
        writer.writeheader()
        for t in (sorted(targets, reverse=True) if order == "descending" else targets):
            writer.writerow({"target_frequency_mhz": t, "achieved_frequency_avg": t,
                             "bench_throughput": 200 if t == peak else 100, "power_avg_w": 100,
                             "temperature_avg_c": 60, "bench_ok": "True",
                             "lock_miss_direction": "none", "power_window_applied": "True"})
    with csv_path.with_name(csv_path.stem + "_voltage.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=("target", "achieved", "voltage", "sampleCount"))
        writer.writeheader()
        for t in targets:
            writer.writerow({"target": t, "achieved": t, "voltage": (volts or {}).get(t, 0.8),
                             "sampleCount": 40})


def evaluate(asc_end=1652, desc_end=1652, peak=1700, peaks=None, dip=False, gpu="NVIDIA GeForce RTX 4060",
             power=("115.00", "115.00")):
    with tempfile.TemporaryDirectory() as temporary:
        root = Path(temporary)
        write(root, "newcard-dense-asc", DENSE, 0, dense_volts(asc_end, dip_at=dip or None), "ascending", gpu, power)
        write(root, "newcard-dense-desc", DENSE, 0, dense_volts(desc_end), "descending", gpu, power)
        for name in WORKLOADS:
            write(root, f"newcard-suite-{name}", SUITE, (peaks or {}).get(name, peak), gpu=gpu, power=power)
        return score(root)


def raises(**kwargs):
    try:
        evaluate(**kwargs)
    except ValueError:
        return True
    return False


def main():
    # ------------------------------------------------ the classifier on committed real sweeps
    ti = classify_floor(real("5060ti-finefloor-20260918/20260918-202543_5060ti-finefloor-gemm-r2_sweep_voltage.csv"))
    check(ti[0] == "FLAT_FLOOR" and ti[1] == 1567 and ti[2] == 0.720,
          "the 5060 Ti's quiet fine sweep is a flat 0.720 V floor ending at 1567 MHz")
    s = classify_floor(real("rtx2060s-finefloor-20260915/20260915-160921_rtx2060s-finefloor-gemm_sweep_voltage.csv"))
    check(s[0] == "NON_MONOTONIC", "the 2060 Super's fine sweep is non-monotonic: the rule is undecidable")
    asc = classify_floor(real("rtx3070ti-sessiond-20260924/fine/finefloor-asc2-resume-20260924-202335/20260924-213132_rtx3070ti-sessiond-finefloor-asc2_sweep_voltage.csv"))
    desc = classify_floor(real("rtx3070ti-sessiond-20260924/fine/finefloor-desc2-resume-20260924-202335/20260924-213543_rtx3070ti-sessiond-finefloor-desc2_sweep_voltage.csv"))
    check(asc[:2] == ("FLAT_FLOOR", 1500) and desc[:2] == ("FLAT_FLOOR", 1500),
          "the 3070 Ti's up and down fine sweeps both end the floor at 1500 MHz")
    check((asc[2], desc[2]) == (0.812, 0.819), "... one voltage code apart, which 11b reports but does not score")

    # Edge cases the first mutation pass showed were unpinned (2026-09-25).
    check(classify_floor({1: 0.720, 2: 0.720, 3: 0.730, 4: 0.720, 5: 0.740})[0] == "NON_MONOTONIC",
          "a floor with a bump in the middle is not one floor")
    check(classify_floor({1: 0.720, 2: 0.730, 3: 0.740})[0] == "NOT_LOCATED",
          "a floor touching only the lowest point ends at or below the range and is not located")
    check(classify_floor({1: 0.720, 2: 0.722, 3: 0.720, 4: 0.730})[:2] == ("FLAT_FLOOR", 3),
          "a 0.722 V median between two codes still sits on the 0.720 V floor")

    # ------------------------------------------------ 11a and 11b on synthetic cards
    passed = evaluate()
    check(passed["rule"] == "PASS" and passed["direction"] == "AGREE",
          "optimum one grid point above a 1652 MHz floor end, inside half a step, passes")
    check(passed["regrets"] is not None and max(passed["regrets"].values()) == 0,
          "regret at the nearest grid point is reported and is zero when every optimum is there")
    below = evaluate(peak=1390)
    check(below["rule"] == "FAIL_BELOW" and max(below["regrets"].values()) == 50,
          "an optimum two steps below fails BELOW, with its regret reported beside it")
    check(evaluate(peak=2008)["rule"] == "FAIL_ABOVE", "an optimum well above fails ABOVE")
    check(evaluate(peak=1545)["rule"] == "FAIL_BELOW",
          "107 MHz below the floor end is more than half a 154.5 MHz step, and fails")
    split = evaluate(peaks={n: (1545 if i < 6 else 1700) for i, n in enumerate(WORKLOADS)})
    check(split["median"] == 1622.5 and split["rule"] == "PASS",
          "a 1545/1700 split has median 1622.5, 29.5 MHz from the floor end, and passes")
    check(evaluate(dip=True)["rule"] == "UNDECIDABLE",
          "voltage falling into the floor, as on the 2060 Super, is undecidable, not a failure")
    far = evaluate(asc_end=1652, desc_end=1860)
    check(far["direction"] == "DIFFER" and far["rule"] == "NOT_SCOREABLE",
          "floor ends four dense steps apart differ, and the rule is not scored")
    check(evaluate(asc_end=1652, desc_end=1704)["direction"] == "AGREE",
          "floor ends one dense step apart agree")
    check(evaluate(asc_end=2600, desc_end=2600)["rule"] == "NOT_SCOREABLE",
          "a floor running past 80% of the table top is not located")
    check(raises(power=("125.00", "115.00")), "a power limit above the card default is refused as not stock")
    ti_card = evaluate(gpu="NVIDIA GeForce RTX 5060 Ti")
    check(ti_card["comparison"] is not None and ti_card["comparison"]["borrowed_grid_point"] == 1545,
          "an 8 GB 5060 Ti gets the 11c comparison, borrowing the 16 GB unit's 1571 MHz floor end")
    check(evaluate()["comparison"] is None, "any other card gets no 5060 Ti comparison")


if __name__ == "__main__":
    main()
