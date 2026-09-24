"""Acceptance check for the local model's decoder-3slot-next-pairing.md output.

Written by Claude on 2026-09-23 BEFORE the model saw the task, from a table verified the same
evening: next-record pairing reproduces all 14 rows of the hand-decoded 3070 Ti table
(data/afterburner-profiles/3070ti-profiles-20260923/README.md) for all three slots.

    python tools/local-model/specs/accept_decoder_3slot.py CANDIDATE.py

Exit 0 means every check passed. It does NOT run analysis/test_decode_profiles.py against the
candidate; do that at review by copying the candidate over the real file in a clean tree.
"""

import importlib.util
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STORE = ROOT / "data/afterburner-profiles/3070ti-profiles-20260923"
FIVE_SLOT = ROOT / "data/afterburner-profiles"

# mV -> (P1 stock, P2 Edit 1, P3 Edit 2), from the committed README table.
TABLE = {
    700.0: (1125, 1125, 1125), 718.75: (1185, 1200, 1185), 725.0: (1215, 1200, 1215),
    812.5: (1485, 1200, 1485), 818.75: (1500, 1200, 1500), 825.0: (1515, 1200, 1500),
    831.25: (1530, 1215, 1500), 837.5: (1545, 1275, 1500), 868.75: (1620, 1575, 1500),
    875.0: (1635, 1635, 1500), 900.0: (1695, 1695, 1500), 1000.0: (1875, 1875, 1500),
    1100.0: (1965, 1965, 1500), 1200.0: (1995, 1995, 1500),
}


def load(candidate):
    spec = importlib.util.spec_from_file_location("candidate_decoder", candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main():
    candidate = Path(sys.argv[1]).resolve()
    module = load(candidate)
    results = []

    def check(name, condition, detail=""):
        results.append((name, bool(condition), detail))

    try:
        module.load_profiles(STORE)
        check("default refuses the 3-slot store (unchanged behaviour)", False, "no error raised")
    except ValueError as exc:
        check("default refuses the 3-slot store (unchanged behaviour)", "missing profiles" in str(exc), str(exc))

    try:
        _, profiles = module.load_profiles(STORE, allow_partial=True, allow_tail=True)
    except Exception as exc:  # report, do not crash: the point is a list of what failed
        profiles = {}
        check("lenient load works", False, f"{type(exc).__name__}: {exc}")
    check("lenient load returns exactly Profile1-3", list(profiles) == ["Profile1", "Profile2", "Profile3"],
          str(list(profiles)))

    names = [name for name in ["Profile1", "Profile2", "Profile3"] if name in profiles]
    for slot, name in enumerate(names):
        points = profiles[name].points
        try:
            paired = module.next_record_pairing(points)
        except Exception as exc:
            check(f"{name}: next_record_pairing exists and runs", False, f"{type(exc).__name__}: {exc}")
            continue
        check(f"{name}: one value per point, last is None", len(paired) == len(points) and paired[-1] is None)
        by_voltage = {round(point.voltage_mv, 2): paired[i] for i, point in enumerate(points)}
        wrong = [(mv, by_voltage.get(mv), row[slot]) for mv, row in TABLE.items()
                 if by_voltage.get(mv) is None or abs(by_voltage[mv] - row[slot]) > 0.01]
        check(f"{name}: next-record pairing matches the 14-row table", not wrong, str(wrong))

    try:
        module.load_profiles(STORE, allow_partial=True)
        check("tail check still on unless allow_tail", False, "no error raised")
    except ValueError as exc:
        check("tail check still on unless allow_tail", "tail" in str(exc), str(exc))
    except Exception as exc:
        check("tail check still on unless allow_tail", False, f"{type(exc).__name__}: {exc}")

    run = subprocess.run([sys.executable, str(candidate), str(STORE), "--lenient", "--pairing", "next"],
                         capture_output=True, text=True, timeout=60)
    check("CLI --lenient --pairing next exits 0", run.returncode == 0, run.stderr[-300:])
    check("CLI prints P2 at 825 mV as 1200", "825 mV: 1200 MHz (next-record pairing)" in run.stdout)
    check("CLI labels the reading as not the default", "NOT the committed default reading" in run.stdout)

    run = subprocess.run([sys.executable, str(candidate), str(STORE), "--lenient", "--verify-rung"],
                         capture_output=True, text=True, timeout=60)
    check("--verify-rung with --lenient is refused", run.returncode == 2)

    # The committed 5060 Ti snapshots must still decode by default, as before.
    five = sorted(p for p in FIVE_SLOT.glob("5060ti-profiles-*") if p.is_dir() and list(p.glob("VEN_10DE*.cfg")))
    for snapshot in five:
        try:
            _, loaded = module.load_profiles(snapshot)
            check(f"default still decodes {snapshot.name}", len(loaded) == 5)
        except ValueError as exc:
            check(f"default still decodes {snapshot.name}", False, str(exc))

    failed = [r for r in results if not r[1]]
    for name, passed, detail in results:
        print(f"{'PASS' if passed else 'FAIL'}  {name}" + (f"   [{detail}]" if not passed and detail else ""))
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
