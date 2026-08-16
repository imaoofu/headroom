"""
Fixed-work GPU benchmarks, for measuring performance as a function of locked core clock.

WHY FIXED WORK
    Invoke-FrequencySweep.ps1 pins the core clock and needs a performance number at each
    frequency. A fixed-TIME stress test (OCCT, FurMark, gpu_stressor) cannot provide one -
    it runs for N seconds regardless of how fast the card is. A fixed-WORK benchmark does
    the identical amount of arithmetic every run, so wall-clock duration IS the performance
    metric, and efficiency = work / (duration x power) falls out directly.

TWO WORKLOADS, ON PURPOSE
    The V100 analysis found the efficiency-optimal frequency depends on whether a workload
    is compute-bound or memory-bound (correlation -0.666 between frequency sensitivity and
    optimal clock). Reproducing that on consumer hardware needs both kinds:

      gemm   - large matrix multiply through cuBLAS. Compute-bound; scales nearly linearly
               with core clock. Directly comparable to the "GeMM" workload in the published
               V100 dataset, which is why matmul was chosen over a homemade kernel.
      membw  - large elementwise stream over VRAM. Memory-bandwidth-bound; much LESS
               sensitive to core clock, which is the contrast that makes the comparison
               meaningful. Measured on this card: elasticity of throughput to core clock
               is ~0.35 for membw against ~1.09 for gemm over a 2.2x range. Sub-linear,
               but NOT flat - an earlier version of this comment claimed "largely
               insensitive" and the data does not support it. Below ~1200 MHz the SMs
               cannot issue requests fast enough to saturate DRAM, so the workload is
               issue-limited rather than bandwidth-limited there.

MEASUREMENT INTEGRITY
    Monitoring is not free and must not be counted as GPU work. An nvidia-smi call is a
    process spawn: measured at 42 ms each on this machine. The temperature check used to
    run every 5 iterations INSIDE the timed region, which cost 10% of gemm's reported
    duration and 50.5% of membw's - at 600 iterations that was 120 spawns, so over half
    of the "benchmark" was the GPU sitting idle waiting on a subprocess. Corrected,
    membw measures 414 GB/s against 205 GB/s before, i.e. 92% of this card's 448 GB/s
    rather than an implausible 46%.

    Worse than the absolute error: that cost was a fixed wall-clock offset, so it shrank
    as a fraction of the run when the sweep locked the clock lower. A frequency-dependent
    bias in the duration is a bias in the efficiency optimum, which is the one number this
    project exists to measure. Two rules follow, and both are load-bearing:

      * The check is TIME-based (--temp-check-seconds), not iteration-based, so its
        frequency does not depend on how fast the card happens to be running.
      * The wall time spent inside nvidia-smi is measured and SUBTRACTED. The preceding
        cuda.synchronize() is deliberately left inside the timed region - that is real
        queued work draining, and excluding it would undercount.

    duration_seconds is therefore work-only. wall_seconds and monitoring_overhead_seconds
    are both reported alongside it so the correction is auditable rather than assumed.

    The timed region is also stamped in Unix epoch time (timed_region_start_unix /
    _end_unix) so Invoke-FrequencySweep.ps1 can window its power samples to exactly the
    interval that produced the performance number. Without that, power was averaged over
    the whole process lifetime - including ~2.3 s of Python import and CUDA init at idle,
    which understated load power by 16% (124.77 W recorded against 148.52 W actual).

SAFETY
    This is ordinary arithmetic - the same work any game or training run does. It cannot
    damage hardware: a compute workload has no path to permanent damage, and the card
    enforces its own thermal and power limits underneath anything software asks for.
    Belt and braces anyway:

      * A temperature ceiling is checked periodically; it aborts cleanly if crossed.
      * Iteration count is bounded and finite. No infinite loops, no unattended running.
      * It allocates a fixed, modest fraction of VRAM and frees it on exit, including on
        error, so a failed run does not strand memory.
      * It never touches clocks, voltage, or power limits. Only the sweep script does that,
        and only via documented nvidia-smi calls.

    If this crashes the driver, that is a real finding about GPU stability at the applied
    settings - not damage. Clock locks and OC settings do not survive a reboot.

USAGE
    python gpu_workload.py --workload gemm  --json
    python gpu_workload.py --workload membw --json
    python gpu_workload.py --workload gemm --size 6144 --iterations 40 --max-temp 83
"""

import argparse
import json
import subprocess
import sys
import time


# A single matmul of size N does roughly 2*N^3 floating point operations.
FLOPS_PER_GEMM = lambda n: 2.0 * (n ** 3)

# How often to align the CPU with the GPU inside the timed loop. Measured to cost nothing
# (see the loop), and required for the temperature poll to see real progress rather than a
# CPU that has already raced to the end of the queue.
SYNC_EVERY_ITERATIONS = 5


def readGpuTemperature():
    """Read GPU temperature via nvidia-smi. Returns None if unavailable."""
    try:
        output = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits", "-i", "0"],
            capture_output=True, text=True, timeout=10,
        )
        if output.returncode != 0:
            return None
        return float(output.stdout.strip().splitlines()[0])
    except Exception:
        return None


def buildArgumentParser():
    parser = argparse.ArgumentParser(
        description="Fixed-work GPU benchmark for frequency sweeps.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--workload", choices=["gemm", "membw"], default="gemm",
                        help="gemm = compute-bound matmul; membw = memory-bandwidth-bound stream")
    parser.add_argument("--size", type=int, default=0,
                        help="Matrix dimension for gemm, or element count for membw. 0 picks a sensible default.")
    parser.add_argument("--iterations", type=int, default=0,
                        help="Timed iterations. 0 picks a per-workload default sized for ~8-9s of GPU "
                             "work at full clock. MUST be held constant across every frequency in a sweep - "
                             "varying it breaks the fixed-work property that makes duration a valid "
                             "performance metric.")
    parser.add_argument("--warmup", type=int, default=5,
                        help="Untimed iterations first, so clocks and caches settle before measurement.")
    parser.add_argument("--max-temp", type=float, default=88.0,
                        help="Abort if GPU temperature reaches this (Celsius).")
    parser.add_argument("--temp-check-seconds", type=float, default=2.0,
                        help="How often to poll temperature during the run. Time-based on purpose: "
                             "an iteration-based cadence polls more often on a fast card than a slow "
                             "one, which puts a frequency-dependent bias in the measured duration.")
    parser.add_argument("--dtype", choices=["fp32", "fp16"], default="fp32",
                        help="fp32 is the conservative default and stresses the general pipeline.")
    parser.add_argument("--json", action="store_true",
                        help="Emit a single JSON object on stdout (for the sweep script to parse).")
    return parser


def emit(payload, asJson, humanLines):
    if asJson:
        print(json.dumps(payload))
    else:
        for line in humanLines:
            print(line)


def main():
    args = buildArgumentParser().parse_args()

    try:
        import torch
    except ImportError:
        emit({"ok": False, "error": "torch_not_installed"}, args.json,
             ["[WORKLOAD] PyTorch is not installed.",
              "[WORKLOAD] Install with: pip install torch --index-url https://download.pytorch.org/whl/cu128"])
        return 4

    if not torch.cuda.is_available():
        emit({"ok": False, "error": "cuda_unavailable"}, args.json,
             ["[WORKLOAD] PyTorch is installed but reports no CUDA device.",
              "[WORKLOAD] A CPU-only build cannot benchmark the GPU. Reinstall with the cu128 index URL."])
        return 5

    device = torch.device("cuda:0")
    deviceName = torch.cuda.get_device_name(0)
    torchDtype = torch.float32 if args.dtype == "fp32" else torch.float16

    startTemp = readGpuTemperature()
    if startTemp is not None and startTemp >= args.max_temp:
        emit({"ok": False, "error": "already_too_hot", "temperature_c": startTemp}, args.json,
             [f"[WORKLOAD] GPU is already at {startTemp} C, at or above the {args.max_temp} C ceiling. Refusing to start."])
        return 6

    # Defaults chosen to be heavy enough to saturate the GPU but well inside VRAM on any
    # modern card. gemm at 8192 fp32 is ~768 MB of tensors; membw at 256M floats is ~3 GB.
    size = args.size
    if size <= 0:
        size = 8192 if args.workload == "gemm" else 256 * 1024 * 1024

    # Iteration defaults target roughly 8-9 seconds of ACTUAL GPU WORK at full boost clock,
    # measured on an RTX 5060 Ti: gemm at 120 iterations takes 7.5-8.4 s, membw at 1200
    # takes ~9.3 s. Short runs are actively misleading here - the card needs time to reach a
    # steady clock and thermal state, and launch overhead stays visible in the throughput
    # figure otherwise.
    #
    # membw's default was 600 while monitoring overhead was still inside the timer, which
    # made it look like a 9.4 s run when only 4.7 s of it was memory traffic. Excluding the
    # overhead exposed that, so the count is doubled to put real work back at ~9 s.
    #
    # A sweep locks the clock LOW as well as high, so the same iteration count takes 2-3x
    # longer at the bottom of the range - that is expected and correct.
    iterations = args.iterations
    if iterations <= 0:
        iterations = 120 if args.workload == "gemm" else 1200

    aborted = False
    abortReason = None
    peakTemp = startTemp if startTemp is not None else 0.0

    try:
        if args.workload == "gemm":
            left = torch.randn((size, size), device=device, dtype=torchDtype)
            right = torch.randn((size, size), device=device, dtype=torchDtype)
            workPerIteration = FLOPS_PER_GEMM(size)

            def step():
                torch.matmul(left, right)

        else:
            # Memory-bound: a scaled add over a large buffer. Every element is read twice
            # and written once, so this is bandwidth-limited rather than arithmetic-limited.
            source = torch.randn(size, device=device, dtype=torchDtype)
            other = torch.randn(size, device=device, dtype=torchDtype)
            destination = torch.empty(size, device=device, dtype=torchDtype)
            bytesPerElement = 4 if args.dtype == "fp32" else 2
            workPerIteration = float(size) * bytesPerElement * 3.0

            def step():
                torch.add(source, other, alpha=2.0, out=destination)

        for _ in range(max(0, args.warmup)):
            step()
        torch.cuda.synchronize()

        started = time.perf_counter()
        startedUnix = time.time()
        completedIterations = 0
        monitoringSeconds = 0.0
        lastTempCheck = started
        checkInterval = max(0.1, args.temp_check_seconds)

        for _ in range(iterations):
            step()
            completedIterations += 1

            # Two separate cadences, and the distinction is the whole point.
            #
            # The SYNC is iteration-based. It has to be: CUDA launches are asynchronous, so
            # the CPU queues every kernel in milliseconds and then blocks at the final
            # synchronize(). A purely time-based gate on perf_counter() therefore never fires
            # at all - the loop is over before wall time advances - which silently disables
            # the temperature ceiling. That regression was caught only by running it and
            # noticing monitoring_overhead_seconds come back as exactly 0.000.
            #
            # Syncing this often is free: measured against a no-sync control, gemm ran 7.49 s
            # both ways and membw 4.67 s both ways. The GPU is the bottleneck, so this waits
            # on work that had to finish anyway.
            if completedIterations % SYNC_EVERY_ITERATIONS == 0:
                torch.cuda.synchronize()

                # The nvidia-smi POLL is time-based, because that cost is real (42 ms per
                # spawn) and an iteration cadence would poll a fast card more often than a
                # slow one - putting a frequency-dependent bias in the measured duration.
                now = time.perf_counter()
                if now - lastTempCheck < checkInterval:
                    continue

                monitorStart = time.perf_counter()
                currentTemp = readGpuTemperature()
                monitoringSeconds += time.perf_counter() - monitorStart
                lastTempCheck = time.perf_counter()

                if currentTemp is not None:
                    peakTemp = max(peakTemp, currentTemp)
                    if currentTemp >= args.max_temp:
                        aborted = True
                        abortReason = f"temperature {currentTemp} C reached ceiling {args.max_temp} C"
                        break

        torch.cuda.synchronize()
        endedUnix = time.time()
        wallSeconds = time.perf_counter() - started
        elapsed = wallSeconds - monitoringSeconds

    except RuntimeError as error:
        message = str(error)
        errorKind = "out_of_memory" if "out of memory" in message.lower() else "runtime_error"
        emit({"ok": False, "error": errorKind, "detail": message[:300]}, args.json,
             [f"[WORKLOAD] {errorKind}: {message[:300]}"])
        return 7
    finally:
        # Always hand VRAM back, including on abort, so repeated sweep points do not
        # accumulate allocations across runs.
        try:
            torch.cuda.synchronize()
        except Exception:
            pass
        torch.cuda.empty_cache()

    endTemp = readGpuTemperature()
    if endTemp is not None:
        peakTemp = max(peakTemp, endTemp)

    throughput = None
    if elapsed > 0 and completedIterations > 0:
        totalWork = workPerIteration * completedIterations
        throughput = totalWork / elapsed  # FLOP/s for gemm, byte/s for membw

    payload = {
        "ok": (not aborted) and completedIterations == iterations,
        "workload": args.workload,
        "device": deviceName,
        "dtype": args.dtype,
        "size": size,
        "iterations_requested": iterations,
        "iterations_completed": completedIterations,
        # duration_seconds is work-only: monitoring subprocess time is subtracted. The raw
        # figures are kept alongside it so the correction can be checked, not taken on faith.
        "duration_seconds": round(elapsed, 4),
        "wall_seconds": round(wallSeconds, 4),
        "monitoring_overhead_seconds": round(monitoringSeconds, 4),
        "seconds_per_iteration": round(elapsed / completedIterations, 6) if completedIterations else None,
        "throughput": throughput,
        "throughput_unit": "FLOP/s" if args.workload == "gemm" else "byte/s",
        # Epoch bounds of the timed region, so the sweep can window its power samples to
        # exactly the interval that produced the throughput above.
        "timed_region_start_unix": round(startedUnix, 4),
        "timed_region_end_unix": round(endedUnix, 4),
        "temperature_start_c": startTemp,
        "temperature_peak_c": peakTemp,
        "aborted": aborted,
        "abort_reason": abortReason,
    }

    humanUnit = "TFLOP/s" if args.workload == "gemm" else "GB/s"
    humanValue = (throughput / 1e12) if args.workload == "gemm" else (throughput / 1e9) if throughput else 0.0

    lines = [
        f"[WORKLOAD] {args.workload} on {deviceName} ({args.dtype}, size {size})",
        f"[WORKLOAD] {completedIterations}/{iterations} iterations in {elapsed:.3f} s of GPU work "
        f"({wallSeconds:.3f} s wall, {monitoringSeconds:.3f} s monitoring excluded)",
        f"[WORKLOAD] Throughput: {humanValue:.2f} {humanUnit}",
        f"[WORKLOAD] Temperature: start {startTemp} C, peak {peakTemp} C",
    ]
    if aborted:
        lines.append(f"[WORKLOAD] ABORTED: {abortReason}")
        lines.append("[WORKLOAD] This run is NOT comparable to complete runs - discard it.")

    emit(payload, args.json, lines)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
