<#
  One focused membw sweep to resolve the 1545-1852 MHz anomaly.

  BACKGROUND
      The 2026-08-19 tuned run sat flat at ~295 GB/s across 1545-1852 MHz while the stock run
      rose 312 -> 332 -> 342. Throttle reasons were decoded for both runs afterwards and show
      no power cap, no thermal slowdown and no hardware slowdown at any frequency, so the cap
      is none of those. Power was flat too - ~53 W across all three points against stock's
      53 -> 57 -> 60 - which is a capped signature rather than contention: CPU contention
      costs throughput while power holds or rises.

      That leaves memory clock, which the sweep tool did not record. It does now.

  WHAT IS DELIBERATELY NOT RUNNING
      No stability logger. The previous tuned run had one spawning nvidia-smi once per second
      and the stock run did not, which made the two methodologically different and is the
      reason that comparison was marked unusable. Nothing else may touch the GPU during this.
#>

$ErrorActionPreference = "Stop"

$sweepDir = $PSScriptRoot
$repoRoot = Split-Path (Split-Path $sweepDir -Parent) -Parent
$python = "C:\Users\Raymond\AppData\Local\Programs\Python\Python312\python.exe"
$workload = Join-Path $sweepDir "gpu_workload.py"
$outputDir = Join-Path $repoRoot "data\frequency-sweeps\membw-anomaly-20260819"

Write-Host "[RUN] repo:     $repoRoot" -ForegroundColor Gray
Write-Host "[RUN] output:   $outputDir" -ForegroundColor Gray
Write-Host ""

# Both paths are space-free, so no quoting or 8.3 shortening is needed here. Check rather than
# assume - this command is handed to cmd /c, where an unquoted space silently truncates it.
foreach ($path in @($python, $workload)) {
    if ($path -match '\s') { throw "Path contains a space and would break under cmd /c: $path" }
    if (-not (Test-Path $path)) { throw "Not found: $path" }
}

$command = "$python $workload --workload membw --json"

& (Join-Path $sweepDir "Invoke-FrequencySweep.ps1") `
    -SessionLabel "5060ti-oc-membw-anomaly" `
    -WorkloadCommand $command `
    -MinFrequencyMhz 1400 `
    -MaxFrequencyMhz 2100 `
    -FrequencyCount 10 `
    -SettleSeconds 8 `
    -MeasureSeconds 20 `
    -OutputDirectory $outputDir

Write-Host ""
Write-Host "[RUN] Done. Leave this window open and tell Claude." -ForegroundColor Green
