<!-- dataset-grade: no -->

# Failed invocations — RTX 2060 Super, 2026-09-12

**Not measurements. The workload never ran.** Kept because the failure mode is worth recording and
because a directory of sweeps with no throughput column should say why, rather than be deleted and
leave a gap in the timestamps.

## `20260912-140822_rtx2060s-lowrange-gemm`

Thirteen points, all locked correctly (`lock_held` true, achieved = target), and all useless:
`bench_throughput` and `bench_ok` are **empty**, power reads **17–19 W** against 53–93 W on the
successful repeat, utilisation 1–2%, and `workload_seconds` is 0.58 where the real run takes 35–87.

**Cause: a drive letter.** The `workload_command` recorded in the JSON is

    D:\headroom-kit\python\python.exe  F:\headroom-kit\tools\frequency-sweep\gpu_workload.py

Two different drives. The kit is on one of them, so python started and immediately failed to open
the script. The sweeper timed a process that exited in half a second and recorded thirteen idle
points without complaint.

⚠️ **This is a hand-written invocation of `Invoke-FrequencySweep.ps1`, not a `Collect.ps1` run**, and
it skipped three things `Collect.ps1` does for you: it derives the kit root from `$PSScriptRoot`
rather than hardcoding a letter, it runs paths through `Get-SpaceFreePath` and refuses to start if a
space survives, and it disables console QuickEdit so a stray click cannot freeze the run. All three
bit during this session.

🔑 **The sweeper does not verify that the workload produced a result.** A sweep whose benchmark never
ran is indistinguishable, at the tool's exit code, from one that worked. That is worth fixing: a
run with `bench_ok` empty at every point should fail loudly rather than write a CSV.
