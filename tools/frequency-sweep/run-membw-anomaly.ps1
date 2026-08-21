<#
  One focused membw sweep over the plateau band, with a caller-supplied label.

  BACKGROUND
      The 2026-08-19 tuned run sat flat at ~295 GB/s across 1545-1852 MHz while the stock run
      rose 312 -> 332 -> 342. A clean re-run with no stability logger reproduced the plateau to
      within 1%, and memory clock telemetry (added to the sweep tool for that run) showed a
      rock-steady 16301 MHz at every point. Throttle masks are clean in all three runs. So the
      plateau is not the logger, not a memory downclock, and not throttling.

      The remaining hypothesis is the core V/F curve: the tuned profile pins it flat near
      3000 MHz at and above ~925 mV, so locking the SM clock into the plateau band forces a
      voltage selection BELOW the flattened region, where the custom and stock curves diverge
      most. Separating the memory overclock from the core curve settles it.

  USAGE
      -Label memonly    memory overclock only, core V/F curve reverted to stock
      -Label oc         both applied (the original tuned configuration)
      -Label stock      neither

  WHAT IS DELIBERATELY NOT RUNNING
      No stability logger. The first tuned run had one spawning nvidia-smi once per second and
      the stock run did not, which made them methodologically different. Nothing else may touch
      the GPU during this.
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$Label
)

$ErrorActionPreference = "Stop"

$sweepDir = $PSScriptRoot
$repoRoot = Split-Path (Split-Path $sweepDir -Parent) -Parent
$python = "C:\Users\Raymond\AppData\Local\Programs\Python\Python312\python.exe"
$workload = Join-Path $sweepDir "gpu_workload.py"
$outputDir = Join-Path $repoRoot "data\frequency-sweeps\membw-anomaly-20260819"

Write-Host "[RUN] label:    $Label" -ForegroundColor Cyan
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
    -SessionLabel "5060ti-$Label-membw-anomaly" `
    -WorkloadCommand $command `
    -MinFrequencyMhz 1400 `
    -MaxFrequencyMhz 2100 `
    -FrequencyCount 10 `
    -SettleSeconds 8 `
    -MeasureSeconds 20 `
    -OutputDirectory $outputDir

Write-Host ""
Write-Host "[RUN] Done. Leave this window open and tell Claude." -ForegroundColor Green
