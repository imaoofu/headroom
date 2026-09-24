"""Acceptance check for the local model's compare-fine-pair.md output.

Written by Claude on 2026-09-23 BEFORE the model saw the task. The expected values were computed
that evening by an independent script (in the session transcript), comparing the 3070 Ti's C8
descending fine sweep (b) against the 2026-08-27 ascending sweep (a).

    python tools/local-model/specs/accept_compare_fine_pair.py CANDIDATE.py

C8 is not committed yet, so it is read from the local results backup. Exit 0 = all checks passed.
"""

import csv
import importlib.util
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
A = ROOT / "data/frequency-sweeps/rtx3070ti-20260825/hwinfo-silent/20260827-172904_rtx3070ti-silent-gemm-fine_sweep.csv"
B_CANDIDATES = [
    Path(r"C:\Users\Raymond\Documents\headroom-results-backup\kit-results-20260923\finefloor-desc\20260923-220950_rtx3070ti-sessiond-finefloor-desc_sweep.csv"),
    Path(r"F:\headroom-kit\results\finefloor-desc\20260923-220950_rtx3070ti-sessiond-finefloor-desc_sweep.csv"),
]
# target -> delta_pct, b relative to a, 2 decimals, computed 2026-09-23.
EXPECTED_DELTA = {1200: -1.14, 1245: -1.22, 1290: -1.27, 1335: -1.23, 1380: -1.16,
                  1410: -1.18, 1455: -1.14, 1500: -1.09, 1545: -1.09, 1590: -1.13}


def main():
    candidate = Path(sys.argv[1]).resolve()
    b_path = next((p for p in B_CANDIDATES if p.is_file()), None)
    if b_path is None:
        print("C8 sweep not found in the backup or on the USB; cannot run the check.")
        return 3
    spec = importlib.util.spec_from_file_location("candidate_compare", candidate)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    results = []

    def check(name, condition, detail=""):
        results.append((name, bool(condition), detail))

    try:
        a, b = module.load_sweep(A), module.load_sweep(b_path)
        result = module.compare(a, b)
    except Exception as exc:
        print(f"FAIL  load/compare raised {type(exc).__name__}: {exc}")
        return 1
    check("ten shared targets, none unmatched",
          [p["target"] for p in result["points"]] == sorted(EXPECTED_DELTA) and not result["only_a"] and not result["only_b"])
    wrong = [(p["target"], round(p["delta_pct"], 3), EXPECTED_DELTA.get(p["target"]))
             for p in result["points"] if abs(p["delta_pct"] - EXPECTED_DELTA.get(p["target"], 1e9)) > 0.006]
    check("per-point delta_pct matches the independent computation", not wrong, str(wrong))
    check("all ten points clean", all(p["clean"] for p in result["points"]))
    mean = sum(EXPECTED_DELTA.values()) / len(EXPECTED_DELTA)
    check("mean delta over clean points", abs(result["mean_delta_pct"] - mean) < 0.01, str(result["mean_delta_pct"]))
    check("min and max delta", abs(result["min_delta_pct"] + 1.27) < 0.006 and abs(result["max_delta_pct"] + 1.09) < 0.006,
          f'{result["min_delta_pct"]} {result["max_delta_pct"]}')
    check("argmax efficiency: a at 1500, b at 1455",
          (result["argmax_eff_a"], result["argmax_eff_b"]) == (1500, 1455),
          f'{result["argmax_eff_a"]} {result["argmax_eff_b"]}')
    first = result["points"][0]
    check("efficiency is throughput / power, unrounded",
          abs(first["eff_a"] - first["throughput_a"] / first["power_a"]) < 1e-6)
    check("load_sweep keys exactly as specified",
          set(a[1200]) == {"achieved", "throughput", "power", "temp", "lock_held", "bench_ok"} and a[1200]["lock_held"] is True)

    run = subprocess.run([sys.executable, str(candidate), str(A), str(b_path), "--json"],
                         capture_output=True, text=True, timeout=60)
    try:
        parsed = json.loads(run.stdout)
        check("--json prints compare() as JSON", run.returncode == 0 and len(parsed["points"]) == 10)
    except Exception as exc:
        check("--json prints compare() as JSON", False, f"{exc}; stderr {run.stderr[-200:]}")
    run = subprocess.run([sys.executable, str(candidate), str(A), str(b_path)], capture_output=True, text=True, timeout=60)
    check("text output states it attributes nothing",
          run.returncode == 0 and "not attributed to anything by this tool" in run.stdout, run.stderr[-200:])

    # A duplicated target must be refused, with exit 2 on the command line.
    with tempfile.TemporaryDirectory() as tmp:
        dup = Path(tmp) / "dup.csv"
        with A.open(encoding="utf-8-sig", newline="") as src:
            rows = list(csv.reader(src))
        with dup.open("w", encoding="utf-8-sig", newline="") as out:
            writer = csv.writer(out, quoting=csv.QUOTE_ALL)
            writer.writerows(rows + [rows[1]])
        try:
            module.load_sweep(dup)
            check("duplicate target raises ValueError", False, "no error")
        except ValueError:
            check("duplicate target raises ValueError", True)
        except Exception as exc:
            check("duplicate target raises ValueError", False, type(exc).__name__)
        run = subprocess.run([sys.executable, str(candidate), str(dup), str(b_path)], capture_output=True, text=True, timeout=60)
        check("duplicate target exits 2 on the command line", run.returncode == 2)

    failed = [r for r in results if not r[1]]
    for name, passed, detail in results:
        print(f"{'PASS' if passed else 'FAIL'}  {name}" + (f"   [{detail}]" if not passed and detail else ""))
    print(f"\n{len(results) - len(failed)} of {len(results)} checks passed.")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
