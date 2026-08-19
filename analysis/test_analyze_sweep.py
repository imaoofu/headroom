"""
Known-answer checks for loadSweep in analyze_sweep.py.

WHY THIS FUNCTION NEEDS TESTS AT ALL
    loadSweep decides which rows of a sweep CSV enter the analysis and which are silently
    dropped. It filters on three separate conditions - a missing throughput, a bench_ok that
    is not True, and a clock lock that overshot - and a mistake in any of them changes every
    downstream number without producing an error. It gated every published sweep result in
    this project while having no test coverage.

    The subtle case is a CSV with no bench_ok column at all. The condition reads
    `raw.get("bench_ok") not in ("True", "true", None)`, and an absent column makes .get()
    return None, which IS in that tuple - so the row is KEPT. Reading that backwards would
    silently discard an entire file.

PROVENANCE
    Drafted by a local model (qwen3-coder:30b via Ollama) from a specification, then verified
    here rather than trusted. Five deliberate mutations were introduced into loadSweep -
    inverting EXCLUDE_DIRECTIONS, removing the sort, turning the efficiency division into a
    multiplication, accepting bench_ok=False, and making windowed accept any value - and all
    five were caught. Tests that pass against a broken function are worse than no tests, so
    that check is the reason this file is committed.

    Note when repeating that exercise: delete analysis/__pycache__ between mutations. Swapping
    `/` for `*` leaves the file the same size, and stale bytecode ran the mutated version while
    inspect.getsource showed the restored source - which produced a confidently wrong result
    until the cache was cleared.

Run: python analysis/test_analyze_sweep.py
"""

import sys
from pathlib import Path
import tempfile
import os

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_sweep import loadSweep

failures = []

def check(description, condition, detail=""):
    if not condition:
        print(f"[FAIL] {description}")
        if detail:
            print(f"  Detail: {detail}")
        failures.append(description)
    else:
        print(f"[PASS] {description}")

# Test 1: A row whose `bench_throughput` is empty is dropped.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w,bench_ok\n")
    f.write("1000,,100,True\n")
    f.write("1000,1000,100,True\n")
    temp_path1 = f.name

try:
    result1 = loadSweep(temp_path1)
    check("Empty bench_throughput dropped", len(result1) == 1)
    check("Non-empty bench_throughput kept", result1[0]["throughput"] == 1000.0)
finally:
    os.unlink(temp_path1)

# Test 2: A row whose `bench_ok` is `False` is dropped.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w,bench_ok\n")
    f.write("1000,1000,100,False\n")
    f.write("1000,1000,100,True\n")
    temp_path2 = f.name

try:
    result2 = loadSweep(temp_path2)
    check("False bench_ok dropped", len(result2) == 1)
    check("True bench_ok kept", result2[0]["throughput"] == 1000.0)
finally:
    os.unlink(temp_path2)

# Test 3: Rows whose `bench_ok` is `True` or `true` are both kept.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w,bench_ok\n")
    f.write("1000,1000,100,True\n")
    f.write("1000,1000,100,true\n")
    temp_path3 = f.name

try:
    result3 = loadSweep(temp_path3)
    check("True bench_ok kept", len(result3) == 2)
    check("true bench_ok kept", result3[0]["throughput"] == 1000.0 and result3[1]["throughput"] == 1000.0)
finally:
    os.unlink(temp_path3)

# Test 4: A row whose `lock_miss_direction` is `above` is dropped.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w,lock_miss_direction\n")
    f.write("1000,1000,100,above\n")
    f.write("1000,1000,100,below\n")
    temp_path4 = f.name

try:
    result4 = loadSweep(temp_path4)
    check("above lock_miss_direction dropped", len(result4) == 1)
    check("below lock_miss_direction kept", result4[0]["mhz"] == 1000.0)
finally:
    os.unlink(temp_path4)

# Test 5: Rows whose `lock_miss_direction` is `below` or `none` are both KEPT.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w,lock_miss_direction\n")
    f.write("1000,1000,100,below\n")
    f.write("1000,1000,100,none\n")
    temp_path5 = f.name

try:
    result5 = loadSweep(temp_path5)
    check("below lock_miss_direction kept", len(result5) == 2)
    check("none lock_miss_direction kept", result5[0]["mhz"] == 1000.0 and result5[1]["mhz"] == 1000.0)
finally:
    os.unlink(temp_path5)

# Test 6: Output is sorted by `mhz` ascending even when the input rows are shuffled.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w\n")
    f.write("2000,2000,200\n")
    f.write("1000,1000,100\n")
    temp_path6 = f.name

try:
    result6 = loadSweep(temp_path6)
    check("Output sorted by mhz ascending", result6[0]["mhz"] == 1000.0 and result6[1]["mhz"] == 2000.0)
finally:
    os.unlink(temp_path6)

# Test 7: `efficiency` equals `throughput / power` exactly, for a case you compute by hand.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w\n")
    f.write("1000,1000,100\n")
    temp_path7 = f.name

try:
    result7 = loadSweep(temp_path7)
    check("Efficiency computed correctly", result7[0]["efficiency"] == 10.0)
finally:
    os.unlink(temp_path7)

# Test 8: `windowed` is True for `True` and `true`, and False for `False` or an empty value.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w,power_window_applied\n")
    f.write("1000,1000,100,True\n")
    f.write("1000,1000,100,true\n")
    f.write("1000,1000,100,False\n")
    f.write("1000,1000,100,\n")
    temp_path8 = f.name

try:
    result8 = loadSweep(temp_path8)
    check("windowed=True for True", result8[0]["windowed"] == True)
    check("windowed=True for true", result8[1]["windowed"] == True)
    check("windowed=False for False", result8[2]["windowed"] == False)
    check("windowed=False for empty", result8[3]["windowed"] == False)
finally:
    os.unlink(temp_path8)

# Test 9: A file written with a UTF-8 BOM still parses (the function opens with `utf-8-sig`).
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8-sig") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w\n")
    f.write("1000,1000,100\n")
    temp_path9 = f.name

try:
    result9 = loadSweep(temp_path9)
    check("UTF-8 BOM file parsed", len(result9) == 1)
finally:
    os.unlink(temp_path9)

# Test 10: A CSV with NO `bench_ok` column at all keeps its rows.
with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False, encoding="utf-8") as f:
    f.write("achieved_frequency_avg,bench_throughput,power_avg_w\n")
    f.write("1000,1000,100\n")
    temp_path10 = f.name

try:
    result10 = loadSweep(temp_path10)
    check("No bench_ok column keeps row", len(result10) == 1)
finally:
    os.unlink(temp_path10)

if failures:
    print(f"FAILED: {', '.join(failures)}")
    raise SystemExit(1)
else:
    print("ALL CHECKS PASSED")
