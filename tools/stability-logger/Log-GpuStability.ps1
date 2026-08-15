<#
.SYNOPSIS
    Records GPU telemetry during a stress test and reports whether the run looked stable.

.DESCRIPTION
    This script OBSERVES. It does not apply overclock or undervolt settings, and that is
    a deliberate choice rather than a missing feature - see NON-GOALS below.

    Workflow:
      1. Apply whatever clock/voltage settings you want to test, by hand, in MSI Afterburner.
      2. Start this logger, telling it what you applied via -AppliedSettings.
      3. Start your stress test (OCCT, FurMark, 3DMark, a real game - your choice).
      4. The logger samples nvidia-smi until the duration elapses, then writes a verdict.

    Every sample is flushed to disk immediately. If the machine hard-locks, the truncated
    log is itself the evidence: the last timestamp is roughly when it died.

.PARAMETER SessionLabel
    Short name for this run. Becomes part of the output filename. Use something you will
    recognise later, like "5060ti-build07-uv900mv".

.PARAMETER AppliedSettings
    What you actually set before starting, in your own words - "core +150, mem +500, 900mV @ 2700MHz".
    This is the single most important field in the whole log and nothing can infer it for you.

.PARAMETER TestMethod
    What stress test is running alongside this. "OCCT 3D Adaptive", "FurMark 1080p", "Cyberpunk 30min".

.PARAMETER DurationSeconds
    How long to sample for. Default 600 (10 minutes).

.PARAMETER IntervalSeconds
    Seconds between samples. Default 1.

.PARAMETER OutputDirectory
    Where logs are written. Defaults to ..\..\data\stability-runs relative to this script.

.EXAMPLE
    .\Log-GpuStability.ps1 -SessionLabel "build07-stock" -AppliedSettings "stock, no changes" -TestMethod "OCCT 3D" -DurationSeconds 300

.NOTES
    NON-GOALS for this version, on purpose:
      * It does not change any GPU setting. A script that sweeps voltage unattended can
        hard-lock or destabilise a machine mid-build, and on a customer's machine that is
        not an acceptable failure mode. Automating the sweep is a later decision, made
        deliberately, not something to inherit by accident from a logging tool.
      * It cannot see a crash that takes the whole machine down instantly. It infers one
        from a truncated log, which is weaker evidence than a recorded event, and the
        verdict says so when it happens.
#>

[CmdletBinding()]
param(
    [string]$SessionLabel = "unlabeled",
    [string]$AppliedSettings = "UNRECORDED - fill this in",
    [string]$TestMethod = "UNRECORDED - fill this in",
    [int]$DurationSeconds = 600,
    [int]$IntervalSeconds = 1,
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"

# --- Throttle reason bits, per NVML documentation -------------------------------------
# The bitmask nvidia-smi reports is a OR of these. Idle and power-cap are normal; the
# hardware slowdown bits are the ones that mean the card is protecting itself.
#
# This MUST stay a plain hashtable. Indexing an [ordered] dictionary with an integer does
# a POSITIONAL lookup, not a key lookup, so every reason came back shifted by one - 0x1
# decoded as "ApplicationsClocksSetting" instead of "GpuIdle". Caught by smoke test.
$ThrottleReasonBits = @{
    1   = "GpuIdle"
    2   = "ApplicationsClocksSetting"
    4   = "SwPowerCap"
    8   = "HwSlowdown"
    16  = "SyncBoost"
    32  = "SwThermalSlowdown"
    64  = "HwThermalSlowdown"
    128 = "HwPowerBrakeSlowdown"
    256 = "DisplayClockSetting"
}

# Bits that indicate the card is in trouble rather than merely idle or power-limited.
$ConcerningReasons = @("HwSlowdown", "SwThermalSlowdown", "HwThermalSlowdown", "HwPowerBrakeSlowdown")

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

function ConvertTo-ThrottleReasonList {
    param([string]$HexMask)

    if ([string]::IsNullOrWhiteSpace($HexMask)) { return "unknown" }
    try {
        $value = [Convert]::ToInt64($HexMask.Replace("0x", ""), 16)
    } catch {
        return "unparsed:$HexMask"
    }
    if ($value -eq 0) { return "None" }

    $active = @()
    foreach ($bit in ($ThrottleReasonBits.Keys | Sort-Object)) {
        if (($value -band $bit) -ne 0) { $active += $ThrottleReasonBits[$bit] }
    }
    if ($active.Count -eq 0) { return "Unrecognised:$HexMask" }
    return ($active -join ";")
}

function Get-DisplayDriverCrashEvents {
    param([datetime]$Since)

    # Event ID 4101 from the "Display" provider is the classic TDR: "Display driver
    # stopped responding and has recovered". A crash that survives long enough to be
    # logged shows up here.
    try {
        $events = Get-WinEvent -FilterHashtable @{
            LogName   = "System"
            StartTime = $Since
        } -ErrorAction Stop | Where-Object {
            $_.Id -eq 4101 -or ($_.ProviderName -like "*nvlddmkm*")
        }
        return @($events)
    } catch {
        return @()
    }
}

# --- Preflight ------------------------------------------------------------------------

$nvidiaSmi = Resolve-NvidiaSmi

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $PSScriptRoot "..\..\data\stability-runs"
}
if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
}
$OutputDirectory = (Resolve-Path $OutputDirectory).Path

$identityFields = "name,driver_version,vbios_version,clocks.max.sm,power.max_limit,memory.total"
$identityRaw = & $nvidiaSmi --query-gpu=$identityFields --format=csv,noheader,nounits -i 0
$identityParts = $identityRaw -split "\s*,\s*"

$gpuName = $identityParts[0]
$driverVersion = $identityParts[1]
$vbiosVersion = $identityParts[2]
$maxSmClock = $identityParts[3]
$powerLimit = $identityParts[4]

$startTime = Get-Date
$stamp = $startTime.ToString("yyyyMMdd-HHmmss")
$safeLabel = ($SessionLabel -replace "[^\w\-\.]", "_")
$logPath = Join-Path $OutputDirectory "$stamp`_$safeLabel`_samples.csv"
$metaPath = Join-Path $OutputDirectory "$stamp`_$safeLabel`_session.json"

Write-Host ""
Write-Host "[LOGGER] GPU:      $gpuName (driver $driverVersion, VBIOS $vbiosVersion)"
Write-Host "[LOGGER] Limits:   max SM clock $maxSmClock MHz, power limit $powerLimit W"
Write-Host "[LOGGER] Settings: $AppliedSettings"
Write-Host "[LOGGER] Test:     $TestMethod"
Write-Host "[LOGGER] Sampling every $IntervalSeconds s for $DurationSeconds s. Ctrl+C stops early."
Write-Host "[LOGGER] Writing:  $logPath"
Write-Host ""

if ($AppliedSettings -like "UNRECORDED*") {
    Write-Warning "No -AppliedSettings given. The log will record what the card DID but not what you ASKED it to do, which makes the run much less useful later."
}

# --- Sample loop ----------------------------------------------------------------------

$queryFields = "clocks.current.sm,clocks.current.memory,power.draw,temperature.gpu,utilization.gpu,utilization.memory,fan.speed,memory.used,clocks_throttle_reasons.active"

$writer = New-Object System.IO.StreamWriter($logPath, $false, [System.Text.Encoding]::UTF8)
$writer.AutoFlush = $true    # never buffer: a hard lock must not take the last samples with it
$writer.WriteLine("timestamp_iso,elapsed_seconds,sm_clock_mhz,memory_clock_mhz,power_draw_w,temperature_c,gpu_utilization_pct,memory_utilization_pct,fan_speed_pct,memory_used_mb,throttle_bitmask,throttle_reasons")

$sampleCount = 0
$queryFailureCount = 0
$concerningSampleCount = 0
$samples = New-Object System.Collections.ArrayList
$completedFullDuration = $false

try {
    $deadline = $startTime.AddSeconds($DurationSeconds)
    while ((Get-Date) -lt $deadline) {
        $now = Get-Date
        $elapsed = [math]::Round(($now - $startTime).TotalSeconds, 1)

        # No "| Select-Object -First 1" here. Select-Object stops the pipeline early, which
        # kills nvidia-smi mid-write and leaves it reporting exit 255 on an otherwise fine
        # query. With -i 0 the command returns exactly one line anyway.
        $raw = $null
        try {
            $rawLines = @(& $nvidiaSmi --query-gpu=$queryFields --format=csv,noheader,nounits -i 0 2>$null)
            if ($rawLines.Count -gt 0) { $raw = $rawLines[0] }
        } catch {
            $raw = $null
        }

        if ([string]::IsNullOrWhiteSpace($raw)) {
            $queryFailureCount++
            $writer.WriteLine("$($now.ToString('o')),$elapsed,,,,,,,,,,QUERY_FAILED")
            Start-Sleep -Seconds $IntervalSeconds
            continue
        }

        $parts = $raw -split "\s*,\s*"
        $throttleMask = $parts[8]
        $throttleReasons = ConvertTo-ThrottleReasonList -HexMask $throttleMask

        $isConcerning = $false
        foreach ($reason in $ConcerningReasons) {
            if ($throttleReasons -like "*$reason*") { $isConcerning = $true }
        }
        if ($isConcerning) { $concerningSampleCount++ }

        $writer.WriteLine("$($now.ToString('o')),$elapsed,$($parts[0]),$($parts[1]),$($parts[2]),$($parts[3]),$($parts[4]),$($parts[5]),$($parts[6]),$($parts[7]),$throttleMask,$throttleReasons")

        [void]$samples.Add([pscustomobject]@{
            SmClock     = [double]$parts[0]
            PowerDraw   = [double]$parts[2]
            Temperature = [double]$parts[3]
            Utilization = [double]$parts[4]
        })

        $sampleCount++
        if ($sampleCount % 15 -eq 0) {
            Write-Host ("[LOGGER] {0,5}s  {1,5} MHz  {2,6} W  {3,3} C  {4,3}% util  {5}" -f `
                [int]$elapsed, $parts[0], $parts[2], $parts[3], $parts[4], $throttleReasons)
        }

        Start-Sleep -Seconds $IntervalSeconds
    }
    $completedFullDuration = $true
} finally {
    $writer.Close()
    $writer.Dispose()
}

# --- Verdict --------------------------------------------------------------------------

$endTime = Get-Date
$crashEvents = Get-DisplayDriverCrashEvents -Since $startTime

$flags = New-Object System.Collections.ArrayList
if ($crashEvents.Count -gt 0) {
    [void]$flags.Add("$($crashEvents.Count) display-driver crash/reset event(s) in the Windows System log during this run")
}
if ($queryFailureCount -gt 0) {
    [void]$flags.Add("$queryFailureCount telemetry query failure(s) - the driver may have been unresponsive")
}
if ($concerningSampleCount -gt 0) {
    [void]$flags.Add("$concerningSampleCount sample(s) showed hardware slowdown or thermal throttling")
}
if (-not $completedFullDuration) {
    [void]$flags.Add("run did not reach its full duration - stopped early or interrupted")
}
if ($sampleCount -eq 0) {
    [void]$flags.Add("no samples were collected at all")
}

if ($flags.Count -eq 0) {
    $verdict = "CLEAN"
} elseif ($crashEvents.Count -gt 0 -or $queryFailureCount -gt 0) {
    $verdict = "UNSTABLE"
} else {
    $verdict = "FLAGGED"
}

$clockValues = @($samples | Select-Object -ExpandProperty SmClock)
$powerValues = @($samples | Select-Object -ExpandProperty PowerDraw)
$tempValues = @($samples | Select-Object -ExpandProperty Temperature)
$utilValues = @($samples | Select-Object -ExpandProperty Utilization)

function Get-Stat {
    param([double[]]$Values, [string]$Kind)
    if ($Values.Count -eq 0) { return $null }
    $measured = $Values | Measure-Object -Average -Maximum -Minimum
    if ($Kind -eq "avg") { return [math]::Round($measured.Average, 2) }
    if ($Kind -eq "max") { return [math]::Round($measured.Maximum, 2) }
    if ($Kind -eq "min") { return [math]::Round($measured.Minimum, 2) }
    return $null
}

$session = [ordered]@{
    session_label            = $SessionLabel
    applied_settings         = $AppliedSettings
    test_method              = $TestMethod
    verdict                  = $verdict
    flags                    = @($flags)
    gpu_name                 = $gpuName
    driver_version           = $driverVersion
    vbios_version            = $vbiosVersion
    max_sm_clock_mhz         = $maxSmClock
    power_limit_w            = $powerLimit
    started_at               = $startTime.ToString("o")
    ended_at                 = $endTime.ToString("o")
    requested_duration_s     = $DurationSeconds
    actual_duration_s        = [math]::Round(($endTime - $startTime).TotalSeconds, 1)
    sample_interval_s        = $IntervalSeconds
    samples_collected        = $sampleCount
    telemetry_failures       = $queryFailureCount
    throttled_samples        = $concerningSampleCount
    driver_crash_events      = $crashEvents.Count
    sm_clock_avg_mhz         = Get-Stat -Values $clockValues -Kind "avg"
    sm_clock_max_mhz         = Get-Stat -Values $clockValues -Kind "max"
    sm_clock_min_mhz         = Get-Stat -Values $clockValues -Kind "min"
    power_avg_w              = Get-Stat -Values $powerValues -Kind "avg"
    power_max_w              = Get-Stat -Values $powerValues -Kind "max"
    temperature_avg_c        = Get-Stat -Values $tempValues -Kind "avg"
    temperature_max_c        = Get-Stat -Values $tempValues -Kind "max"
    gpu_utilization_avg_pct  = Get-Stat -Values $utilValues -Kind "avg"
    samples_file             = Split-Path $logPath -Leaf
    schema_version           = "0.1.0"
}

$session | ConvertTo-Json -Depth 4 | Out-File -FilePath $metaPath -Encoding utf8

Write-Host ""
Write-Host "[LOGGER] ===================== RESULT ====================="
Write-Host "[LOGGER] Verdict: $verdict"
foreach ($flag in $flags) { Write-Host "[LOGGER]   - $flag" }
if ($sampleCount -gt 0) {
    Write-Host ("[LOGGER] Collected {0} samples over {1}s." -f $sampleCount, $session.actual_duration_s)
    Write-Host ("[LOGGER] SM clock: avg {0} MHz, range {1}-{2} MHz." -f $session.sm_clock_avg_mhz, $session.sm_clock_min_mhz, $session.sm_clock_max_mhz)
    Write-Host ("[LOGGER] Power:    avg {0} W, peak {1} W (limit {2} W)." -f $session.power_avg_w, $session.power_max_w, $powerLimit)
    Write-Host ("[LOGGER] Temp:     avg {0} C, peak {1} C." -f $session.temperature_avg_c, $session.temperature_max_c)
    Write-Host ("[LOGGER] GPU util: avg {0}%." -f $session.gpu_utilization_avg_pct)
    if ($session.gpu_utilization_avg_pct -lt 50) {
        Write-Host "[LOGGER] NOTE: average utilisation is low. If a stress test was meant to be running, it probably was not - this run says little about stability."
    }
}
Write-Host "[LOGGER] Samples: $logPath"
Write-Host "[LOGGER] Session: $metaPath"
Write-Host "[LOGGER] =================================================="
Write-Host ""
Write-Host "[LOGGER] A CLEAN verdict means nothing went visibly wrong during this window. It is"
Write-Host "[LOGGER] not proof of stability - undervolt failures often need hours to show up, and"
Write-Host "[LOGGER] a single clean 10-minute run is weak evidence. Say so when reporting it."

# Exit code carries the verdict so this can be driven from a batch script later:
#   0 = CLEAN, 1 = FLAGGED, 2 = UNSTABLE
if ($verdict -eq "CLEAN") { exit 0 }
if ($verdict -eq "FLAGGED") { exit 1 }
exit 2
