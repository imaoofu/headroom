<#
.SYNOPSIS
    Sweeps locked GPU core clocks and measures power at each one, to build a
    frequency-power-efficiency curve on real consumer hardware.

.DESCRIPTION
    This is the consumer-hardware equivalent of the public GPU-DVFS-Dataset: for each
    of N core frequencies, pin the clock, hold a load, and record what the card draws.

    Unlike Log-GpuStability.ps1 (which only observes), this script DOES change GPU state -
    it locks the core clock via nvidia-smi. That makes the reset path the most important
    code here, not the measurement:

      * The sweep body is wrapped in try/finally. The finally ALWAYS runs -rgc.
      * After resetting it READS BACK the clock state and shouts if the reset did not take.
      * Ctrl+C is intercepted rather than allowed to kill the process, so it unwinds
        through the same reset path instead of leaving the card pinned.
      * Clock locks do not survive a reboot, so a total loss of the process is recoverable
        by restarting the machine. Say so out loud if that ever happens.

    WORKLOAD: the GPU must be under sustained load or every measurement is an idle
    measurement. Two ways to supply it:

      -WorkloadCommand "<cmd>"   the script runs this at each frequency and times it.
                                 Duration becomes the performance metric (fixed work,
                                 varying clock), which is what makes efficiency computable.

      (nothing)                  the script assumes YOU started a load externally (OCCT,
                                 FurMark, a game) and just measures power. Gives the
                                 power curve but NOT performance, so efficiency cannot
                                 be computed from that run alone.

.PARAMETER SessionLabel
    Short name for this sweep. Becomes part of the output filename.

.PARAMETER WorkloadCommand
    Optional. Command run at each frequency; its wall-clock duration is recorded as the
    performance metric. Must be fixed-work (same amount of work every time), not fixed-time.

.PARAMETER FrequencyCount
    How many frequencies to test across the swept range. Default 13, matching the public
    V100 dataset's grid so the two are directly comparable.

.PARAMETER MinFrequencyPercent
    Floor of the sweep, as a percentage of the card's max clock. Default 40.

    Consumer cards report absurdly low clocks as "supported" - an RTX 5060 Ti offers 180 MHz,
    under 6% of its 3090 MHz max. Sweeping evenly from there wastes a third of the run on
    frequencies that will never be efficiency-optimal for real work, and makes any fixed-work
    benchmark crawl. The public V100 dataset only swept 757-1530 MHz, i.e. 49-100% of its max,
    and found its optimum at 62%. This default keeps the grid concentrated where the answer
    actually lives. Lower it if a card's optimum looks like it sits at the floor.

.PARAMETER SettleSeconds
    Wait after locking a clock before measuring, so the card reaches steady state. Default 8.

.PARAMETER MeasureSeconds
    How long to sample telemetry at each frequency. Default 20.

.PARAMETER DryRun
    Plan the sweep and print the frequencies WITHOUT touching GPU state. Always do this first.

.EXAMPLE
    .\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-baseline" -DryRun

.EXAMPLE
    .\Invoke-FrequencySweep.ps1 -SessionLabel "5060ti-baseline" -MeasureSeconds 25

.NOTES
    Requires an ELEVATED shell. nvidia-smi clock locking needs administrator rights;
    the script checks and refuses to start otherwise rather than failing halfway through.
#>

[CmdletBinding()]
param(
    [string]$SessionLabel = "sweep",
    [string]$WorkloadCommand = "",
    [int]$FrequencyCount = 13,
    [int]$MinFrequencyPercent = 40,
    [int]$SettleSeconds = 8,
    [int]$MeasureSeconds = 20,
    [int]$SampleIntervalSeconds = 1,
    [string]$OutputDirectory = "",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

function Resolve-NvidiaSmi {
    $candidates = @(
        "C:\Windows\System32\nvidia-smi.exe",
        "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe"
    )
    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) { return $candidate }
    }
    $onPath = Get-Command nvidia-smi -ErrorAction SilentlyContinue
    if ($null -ne $onPath) { return $onPath.Source }
    throw "nvidia-smi.exe not found. This tool requires an NVIDIA GPU with drivers installed."
}

function Test-Elevated {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-SupportedGraphicsClocks {
    param([string]$Smi)
    # Returns every graphics clock the card will accept, descending.
    $raw = @(& $Smi --query-supported-clocks=graphics --format=csv,noheader,nounits 2>$null)
    $clocks = @()
    foreach ($line in $raw) {
        $trimmed = ("$line").Trim()
        if ($trimmed -match '^\d+$') { $clocks += [int]$trimmed }
    }
    return ($clocks | Sort-Object -Unique -Descending)
}

function Select-SweepFrequencies {
    param([int[]]$Supported, [int]$Count)
    # Evenly spaced across the supported range, always including both endpoints.
    if ($Supported.Count -le $Count) { return ($Supported | Sort-Object) }
    $ascending = @($Supported | Sort-Object)
    $picked = @()
    for ($i = 0; $i -lt $Count; $i++) {
        $index = [int][math]::Round(($ascending.Count - 1) * $i / ($Count - 1))
        $picked += $ascending[$index]
    }
    return ($picked | Sort-Object -Unique)
}

function Read-Telemetry {
    param([string]$Smi)
    $fields = "clocks.current.sm,power.draw,temperature.gpu,utilization.gpu,clocks_throttle_reasons.active"
    $lines = @(& $Smi --query-gpu=$fields --format=csv,noheader,nounits -i 0 2>$null)
    if ($lines.Count -eq 0) { return $null }
    $parts = ("$($lines[0])") -split "\s*,\s*"
    if ($parts.Count -lt 5) { return $null }
    return [pscustomobject]@{
        SmClock      = [double]$parts[0]
        PowerDraw    = [double]$parts[1]
        Temperature  = [double]$parts[2]
        Utilization  = [double]$parts[3]
        ThrottleMask = $parts[4]
    }
}

function Reset-GpuClocks {
    param([string]$Smi)
    # The single most important function in this file.
    try {
        & $Smi -rgc 2>&1 | Out-Null
    } catch {
        Write-Host "[SWEEP] WARNING: -rgc threw: $($_.Exception.Message)"
    }
    Start-Sleep -Milliseconds 700
    $after = Read-Telemetry -Smi $Smi
    if ($null -ne $after) {
        Write-Host ("[SWEEP] Clocks reset. Card is now reporting {0} MHz at idle/load." -f $after.SmClock)
    } else {
        Write-Host "[SWEEP] Clocks reset issued, but telemetry did not respond - VERIFY MANUALLY with: nvidia-smi -q -d CLOCK"
    }
}

# --- Preflight -----------------------------------------------------------------------

$nvidiaSmi = Resolve-NvidiaSmi
$elevated = Test-Elevated

$identityRaw = & $nvidiaSmi --query-gpu=name,driver_version,clocks.max.sm,power.max_limit --format=csv,noheader,nounits -i 0
$identityParts = ("$identityRaw") -split "\s*,\s*"
$gpuName = $identityParts[0]
$driverVersion = $identityParts[1]
$maxClock = $identityParts[2]
$powerLimit = $identityParts[3]

$supported = Get-SupportedGraphicsClocks -Smi $nvidiaSmi
if ($supported.Count -eq 0) {
    throw "Could not read supported graphics clocks. This card may not support clock locking."
}

# Trim the pointless bottom end before picking the grid - see MinFrequencyPercent.
$floorMhz = [int][math]::Round(($supported[0] * $MinFrequencyPercent) / 100.0)
$inRange = @($supported | Where-Object { $_ -ge $floorMhz })
if ($inRange.Count -lt $FrequencyCount) {
    Write-Host "[SWEEP] NOTE: floor of $floorMhz MHz leaves only $($inRange.Count) clocks; using the full supported range instead."
    $inRange = $supported
}
$targets = Select-SweepFrequencies -Supported $inRange -Count $FrequencyCount

Write-Host ""
Write-Host "[SWEEP] GPU:        $gpuName (driver $driverVersion)"
Write-Host "[SWEEP] Max clock:  $maxClock MHz | power limit $powerLimit W"
Write-Host "[SWEEP] Supported:  $($supported.Count) discrete graphics clocks, $($supported[-1])-$($supported[0]) MHz"
Write-Host "[SWEEP] Sweep floor: $floorMhz MHz ($MinFrequencyPercent% of max) - lower clocks exist but are not swept"
Write-Host "[SWEEP] Testing:    $($targets.Count) frequencies -> $($targets -join ', ') MHz"
if ($WorkloadCommand -ne "") {
    Write-Host "[SWEEP] Workload:   $WorkloadCommand   (timed; duration is the performance metric)"
} else {
    Write-Host "[SWEEP] Workload:   NONE SUPPLIED - start a load yourself, or this measures idle."
}

$perPointSeconds = $SettleSeconds + $MeasureSeconds
Write-Host ("[SWEEP] Estimated:  ~{0:N1} min of measurement (plus workload time if any)" -f (($targets.Count * $perPointSeconds) / 60))
Write-Host ""

if ($DryRun) {
    Write-Host "[SWEEP] DRY RUN - no GPU state was changed. Re-run without -DryRun to sweep."
    exit 0
}

if (-not $elevated) {
    Write-Host "[SWEEP] REFUSING TO START: not running as Administrator."
    Write-Host "[SWEEP] nvidia-smi clock locking requires elevation. Right-click PowerShell -> Run as administrator."
    Write-Host "[SWEEP] Checking now rather than failing halfway through a sweep with the clock pinned."
    exit 3
}

if ($WorkloadCommand -eq "") {
    $idleCheck = Read-Telemetry -Smi $nvidiaSmi
    if ($null -ne $idleCheck -and $idleCheck.Utilization -lt 20) {
        Write-Host ("[SWEEP] WARNING: GPU utilisation is {0}% and no -WorkloadCommand was given." -f $idleCheck.Utilization)
        Write-Host "[SWEEP] An idle sweep measures nothing useful. Start your stress test, then re-run."
        Write-Host "[SWEEP] Continuing anyway in 5s - Ctrl+C to abort."
        Start-Sleep -Seconds 5
    }
}

# --- Output paths --------------------------------------------------------------------

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $PSScriptRoot "..\..\data\frequency-sweeps"
}
if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
}
$OutputDirectory = (Resolve-Path $OutputDirectory).Path

$startTime = Get-Date
$stamp = $startTime.ToString("yyyyMMdd-HHmmss")
$safeLabel = ($SessionLabel -replace "[^\w\-\.]", "_")
$csvPath = Join-Path $OutputDirectory "$stamp`_$safeLabel`_sweep.csv"
$jsonPath = Join-Path $OutputDirectory "$stamp`_$safeLabel`_sweep.json"

# Same Ctrl+C handling as the stability logger: intercept rather than terminate, so the
# finally block's clock reset is guaranteed to run. Degrades if no console is attached.
$consoleControlAvailable = $true
try {
    [Console]::TreatControlCAsInput = $true
} catch {
    $consoleControlAvailable = $false
    Write-Host "[SWEEP] No interactive console - Ctrl+C interception unavailable. The finally block still resets clocks."
}

$results = New-Object System.Collections.ArrayList
$abortedByUser = $false

# --- Sweep ---------------------------------------------------------------------------

try {
    foreach ($target in $targets) {

        if ($consoleControlAvailable -and [Console]::KeyAvailable) {
            $key = [Console]::ReadKey($true)
            if ($key.Key -eq "C" -and ($key.Modifiers -band [ConsoleModifiers]::Control)) {
                Write-Host ""
                Write-Host "[SWEEP] Ctrl+C received - stopping sweep and resetting clocks."
                $abortedByUser = $true
                break
            }
        }

        Write-Host ("[SWEEP] --> locking {0} MHz" -f $target)
        $lockOutput = & $nvidiaSmi -lgc $target 2>&1
        $lockFailed = ($LASTEXITCODE -ne 0)
        if ($lockFailed) {
            Write-Host "[SWEEP] LOCK FAILED at $target MHz: $lockOutput"
            Write-Host "[SWEEP] Aborting rather than recording measurements at an unknown clock."
            break
        }

        Start-Sleep -Seconds $SettleSeconds

        $workloadSeconds = $null
        if ($WorkloadCommand -ne "") {
            $workloadStart = Get-Date
            try {
                cmd.exe /c $WorkloadCommand 2>&1 | Out-Null
            } catch {
                Write-Host "[SWEEP] Workload command errored at $target MHz: $($_.Exception.Message)"
            }
            $workloadSeconds = [math]::Round(((Get-Date) - $workloadStart).TotalSeconds, 3)
        }

        $samples = New-Object System.Collections.ArrayList
        $throttleSeen = @{}
        $deadline = (Get-Date).AddSeconds($MeasureSeconds)
        while ((Get-Date) -lt $deadline) {
            $reading = Read-Telemetry -Smi $nvidiaSmi
            if ($null -ne $reading) {
                [void]$samples.Add($reading)
                $throttleSeen[$reading.ThrottleMask] = $true
            }
            Start-Sleep -Seconds $SampleIntervalSeconds
        }

        if ($samples.Count -eq 0) {
            Write-Host "[SWEEP] No telemetry collected at $target MHz - skipping this point."
            continue
        }

        $clockStats = $samples | Select-Object -ExpandProperty SmClock | Measure-Object -Average -Minimum -Maximum
        $powerStats = $samples | Select-Object -ExpandProperty PowerDraw | Measure-Object -Average -Minimum -Maximum
        $tempStats = $samples | Select-Object -ExpandProperty Temperature | Measure-Object -Average -Maximum
        $utilStats = $samples | Select-Object -ExpandProperty Utilization | Measure-Object -Average

        $row = [pscustomobject]@{
            target_frequency_mhz   = $target
            achieved_frequency_avg = [math]::Round($clockStats.Average, 1)
            achieved_frequency_min = $clockStats.Minimum
            achieved_frequency_max = $clockStats.Maximum
            lock_held              = ([math]::Abs($clockStats.Average - $target) -le 30)
            power_avg_w            = [math]::Round($powerStats.Average, 2)
            power_min_w            = $powerStats.Minimum
            power_max_w            = $powerStats.Maximum
            temperature_avg_c      = [math]::Round($tempStats.Average, 1)
            temperature_max_c      = $tempStats.Maximum
            utilization_avg_pct    = [math]::Round($utilStats.Average, 1)
            workload_seconds       = $workloadSeconds
            samples                = $samples.Count
            throttle_masks_seen    = ($throttleSeen.Keys -join ";")
        }
        [void]$results.Add($row)

        $heldNote = "held"
        if (-not $row.lock_held) { $heldNote = "DRIFTED" }
        Write-Host ("[SWEEP]     {0,5} MHz -> achieved {1,6} MHz ({2}), {3,6} W, {4,3} C, util {5,3}%" -f `
            $target, $row.achieved_frequency_avg, $heldNote, $row.power_avg_w, $row.temperature_avg_c, $row.utilization_avg_pct)
    }
} finally {
    Write-Host ""
    Write-Host "[SWEEP] Resetting GPU clocks..."
    Reset-GpuClocks -Smi $nvidiaSmi
    if ($consoleControlAvailable) {
        try { [Console]::TreatControlCAsInput = $false } catch { }
    }
}

# --- Output --------------------------------------------------------------------------

if ($results.Count -eq 0) {
    Write-Host "[SWEEP] No results collected. Nothing written."
    exit 2
}

$results | Export-Csv -Path $csvPath -NoTypeInformation -Encoding UTF8

$driftedPoints = @($results | Where-Object { -not $_.lock_held })

$session = [ordered]@{
    session_label        = $SessionLabel
    gpu_name             = $gpuName
    driver_version       = $driverVersion
    max_clock_mhz        = $maxClock
    power_limit_w        = $powerLimit
    workload_command     = $WorkloadCommand
    started_at           = $startTime.ToString("o")
    ended_at             = (Get-Date).ToString("o")
    aborted_by_user      = $abortedByUser
    frequencies_planned  = $targets.Count
    frequencies_measured = $results.Count
    settle_seconds       = $SettleSeconds
    measure_seconds      = $MeasureSeconds
    drifted_points       = $driftedPoints.Count
    supported_clock_count = $supported.Count
    samples_file         = Split-Path $csvPath -Leaf
    schema_version       = "0.1.0"
}
$session | ConvertTo-Json -Depth 4 | Out-File -FilePath $jsonPath -Encoding utf8

Write-Host ""
Write-Host "[SWEEP] ===================== RESULT ====================="
Write-Host ("[SWEEP] Measured {0} of {1} planned frequencies." -f $results.Count, $targets.Count)
if ($abortedByUser) { Write-Host "[SWEEP] Sweep was stopped early by the user - partial curve." }
if ($driftedPoints.Count -gt 0) {
    Write-Host ("[SWEEP] WARNING: {0} point(s) drifted more than 30 MHz from their target." -f $driftedPoints.Count)
    Write-Host "[SWEEP] The card overrode the lock - usually power or thermal limits. Those rows are suspect."
}
if ($WorkloadCommand -eq "") {
    Write-Host "[SWEEP] No workload command was given, so there is NO performance metric in this data."
    Write-Host "[SWEEP] You have a power-vs-frequency curve. Efficiency needs performance too - re-run with -WorkloadCommand."
}
Write-Host "[SWEEP] CSV:  $csvPath"
Write-Host "[SWEEP] JSON: $jsonPath"
Write-Host "[SWEEP] =================================================="
Write-Host ""
Write-Host "[SWEEP] Clock locks do NOT survive a reboot. If anything looks wrong with the card's"
Write-Host "[SWEEP] clocks after this, reboot and it returns to stock."

exit 0
