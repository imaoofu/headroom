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

.PARAMETER MinFrequencyMhz
.PARAMETER MaxFrequencyMhz
    Absolute bounds on the swept band, in MHz. Both default to 0, meaning "unset" - the grid then
    runs from the MinFrequencyPercent floor to the card's maximum, as before.

    These exist for FINE sweeps: once a coarse sweep has bracketed the efficiency optimum, the
    useful next run concentrates all N points into the neighbourhood of the peak rather than
    re-measuring a range whose shape is already known. MinFrequencyPercent cannot express that,
    since it only moves the floor.

    A fine sweep needs enough span to be worth fitting. Near its optimum an efficiency curve is
    flat by construction, so a band tight around the peak buys resolution in frequency and pays
    for it in signal: if the curve only falls a percent or two across the whole band, per-point
    noise decides which point wins. Choose a band across which efficiency visibly falls.

.PARAMETER SettleSeconds
    Wait after locking a clock before measuring, so the card reaches steady state. Default 8.

.PARAMETER MeasureSeconds
    How long to sample telemetry at each frequency. Default 20. Applies only when NO
    -WorkloadCommand is given; with a workload, sampling runs for as long as it runs.

.PARAMETER SampleIntervalSeconds
    Telemetry sampling period, in seconds. Default 0.5.

    When a workload is supplied, power is averaged over only the benchmark's timed region
    (see below), which is a window of roughly 8-10 seconds. At the old 1 s period that left
    under ten samples to average; 0.5 s doubles the resolution for a cost of ~42 ms per
    nvidia-smi call, on a thread that is otherwise sleeping.

.PARAMETER MaxBaselineUtilization
    Refuse to start if the GPU is already busier than this percentage before our workload
    runs. Default 10.

    This guard protects the whole dataset. A sweep run while a game, a video, a local LLM
    server or an animated wallpaper is on the card measures that load mixed with ours at
    every frequency, inseparably. The output looks like ordinary data and is worthless.

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
    [int]$MinFrequencyMhz = 0,
    [int]$MaxFrequencyMhz = 0,
    [int]$SettleSeconds = 8,
    [int]$MeasureSeconds = 20,
    [double]$SampleIntervalSeconds = 0.5,
    [double]$MaxBaselineUtilization = 10,
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
    # Memory clock is appended LAST so the existing positional offsets are untouched. It is
    # here because a bandwidth-bound workload tracks memory clock, not SM clock, and sweeps
    # that recorded only the SM clock could not explain why membw capped at ~295 GB/s across
    # 1545-1852 MHz on a tuned card while stock rose 312 -> 342. That question is unanswerable
    # from telemetry that never looked at the relevant clock.
    $fields = "clocks.current.sm,power.draw,temperature.gpu,utilization.gpu,clocks_throttle_reasons.active,clocks.current.memory"
    $lines = @(& $Smi --query-gpu=$fields --format=csv,noheader,nounits -i 0 2>$null)
    if ($lines.Count -eq 0) { return $null }
    $parts = ("$($lines[0])") -split "\s*,\s*"
    if ($parts.Count -lt 6) { return $null }
    return [pscustomobject]@{
        # Unix epoch seconds, same clock the benchmark stamps its timed region with, so
        # samples can be matched to the interval that actually produced the performance number.
        Timestamp    = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
        SmClock      = [double]$parts[0]
        PowerDraw    = [double]$parts[1]
        Temperature  = [double]$parts[2]
        Utilization  = [double]$parts[3]
        ThrottleMask = $parts[4]
        MemClock     = [double]$parts[5]
    }
}

function Get-BaselineUtilization {
    param([string]$Smi, [int]$Samples = 5)
    # Measures what the GPU is doing BEFORE our workload starts. Anything materially above
    # zero means something else is competing for the card.
    $values = @()
    for ($i = 0; $i -lt $Samples; $i++) {
        $reading = Read-Telemetry -Smi $Smi
        if ($null -ne $reading) { $values += $reading.Utilization }
        Start-Sleep -Milliseconds 600
    }
    if ($values.Count -eq 0) { return $null }
    return [math]::Round((($values | Measure-Object -Average).Average), 1)
}

function Get-HeavyGpuProcesses {
    param([string]$Smi)
    # Windows always has a dozen shell/compositor processes touching the GPU; those are
    # unavoidable and near-free. These are the ones that render CONTINUOUSLY and will
    # contaminate a measurement.
    $known = @(
        "wallpaper64", "wallpaper32", "wallpaperservice32",   # Wallpaper Engine - animated wallpapers render nonstop
        "opera", "chrome", "msedge", "firefox", "brave",      # browsers composite and play video
        "Discord", "Spotify", "steamwebhelper",
        "obs64", "obs32",
        "ollama", "ollama_llama_server",                      # local LLM inference will saturate the card
        "python", "pythonw"                                   # another sweep or training run already going
    )
    $found = @()
    try {
        $lines = @(& $Smi --query-compute-apps=process_name --format=csv,noheader 2>$null)
        foreach ($line in $lines) {
            $name = [System.IO.Path]::GetFileNameWithoutExtension(("$line").Trim())
            foreach ($candidate in $known) {
                if ($name -like "*$candidate*" -and ($found -notcontains $name)) { $found += $name }
            }
        }
    } catch { }
    return $found
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

# Pick the band. Explicit MHz bounds win over the percentage floor when given.
$explicitBand = ($MinFrequencyMhz -gt 0 -or $MaxFrequencyMhz -gt 0)
if ($explicitBand) {
    $floorMhz = if ($MinFrequencyMhz -gt 0) { $MinFrequencyMhz } else { $supported[-1] }
    $ceilMhz = if ($MaxFrequencyMhz -gt 0) { $MaxFrequencyMhz } else { $supported[0] }
    if ($floorMhz -gt $ceilMhz) {
        throw "MinFrequencyMhz ($floorMhz) is above MaxFrequencyMhz ($ceilMhz). Nothing to sweep."
    }
    $inRange = @($supported | Where-Object { $_ -ge $floorMhz -and $_ -le $ceilMhz })
    if ($inRange.Count -eq 0) {
        throw "No supported graphics clock falls in $floorMhz-$ceilMhz MHz. Supported range is $($supported[-1])-$($supported[0]) MHz."
    }
    # Do NOT silently widen an explicitly-requested band the way the percentage floor does.
    # Asking for a fine sweep and receiving a coarse one over the whole range would produce a
    # file that answers a different question than the one it was run to answer.
    if ($inRange.Count -lt $FrequencyCount) {
        Write-Host "[SWEEP] NOTE: $floorMhz-$ceilMhz MHz contains only $($inRange.Count) supported clocks; sweeping all of them instead of $FrequencyCount."
    }
} else {
    # Trim the pointless bottom end before picking the grid - see MinFrequencyPercent.
    $floorMhz = [int][math]::Round(($supported[0] * $MinFrequencyPercent) / 100.0)
    $ceilMhz = $supported[0]
    $inRange = @($supported | Where-Object { $_ -ge $floorMhz })
    if ($inRange.Count -lt $FrequencyCount) {
        Write-Host "[SWEEP] NOTE: floor of $floorMhz MHz leaves only $($inRange.Count) clocks; using the full supported range instead."
        $inRange = $supported
    }
}
$targets = Select-SweepFrequencies -Supported $inRange -Count $FrequencyCount

Write-Host ""
Write-Host "[SWEEP] GPU:        $gpuName (driver $driverVersion)"
Write-Host "[SWEEP] Max clock:  $maxClock MHz | power limit $powerLimit W"
Write-Host "[SWEEP] Supported:  $($supported.Count) discrete graphics clocks, $($supported[-1])-$($supported[0]) MHz"
if ($explicitBand) {
    $stepMhz = if ($targets.Count -gt 1) { [int][math]::Round(($targets[-1] - $targets[0]) / ($targets.Count - 1)) } else { 0 }
    Write-Host "[SWEEP] Sweep band:  $floorMhz-$ceilMhz MHz (explicit) - FINE sweep, ~$stepMhz MHz apart. Not a full-range curve."
} else {
    Write-Host "[SWEEP] Sweep floor: $floorMhz MHz ($MinFrequencyPercent% of max) - lower clocks exist but are not swept"
}
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

# --- Is anything else using the GPU? -------------------------------------------------
#
# This is the guard that protects the entire dataset. A sweep run while a game, a browser
# playing video, a local LLM, or an animated wallpaper is on the card measures THAT load
# mixed with ours, at every frequency, with no way to separate them afterwards. The result
# looks like perfectly ordinary data and is silently worthless.
#
# Utilisation is the robust signal - it catches anything, including processes not on any
# known-offenders list. Process names are only a hint for what to go close.

if ($WorkloadCommand -ne "") {
    Write-Host "[SWEEP] Checking the GPU is quiet before starting..."
    $baseline = Get-BaselineUtilization -Smi $nvidiaSmi
    $heavy = Get-HeavyGpuProcesses -Smi $nvidiaSmi

    if ($null -ne $baseline -and $baseline -gt $MaxBaselineUtilization) {
        Write-Host ""
        Write-Host ("[SWEEP] REFUSING TO START: GPU is already {0}% busy before any workload of ours." -f $baseline)
        if ($heavy.Count -gt 0) {
            Write-Host ("[SWEEP] Likely culprits on the GPU right now: {0}" -f ($heavy -join ", "))
        }
        Write-Host "[SWEEP] Close games, browsers playing video, animated wallpapers, and local LLM"
        Write-Host "[SWEEP] servers, then re-run. Competing load contaminates EVERY frequency point"
        Write-Host "[SWEEP] and cannot be separated out afterwards - the data would look fine and be wrong."
        Write-Host ("[SWEEP] Override with -MaxBaselineUtilization <pct> if you know what you are doing.")
        exit 4
    }

    Write-Host ("[SWEEP] Baseline utilisation {0}% - clear to start." -f $baseline)

} else {
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

# A click in the console window freezes this script mid-sweep with the clock still locked. See
# tools/Disable-QuickEdit.ps1 - it has happened, it cost six minutes and two corrupted points.
$quickEditGuard = Join-Path $PSScriptRoot "..\Disable-QuickEdit.ps1"
if (Test-Path $quickEditGuard) {
    . $quickEditGuard
    [void](Disable-ConsoleQuickEdit -Tag "SWEEP")
} else {
    Write-Host "[SWEEP] NOTE: tools\Disable-QuickEdit.ps1 not found - DO NOT CLICK IN THIS WINDOW while the sweep runs."
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

        $samples = New-Object System.Collections.ArrayList
        $throttleSeen = @{}
        $workloadSeconds = $null
        $workloadJson = $null

        if ($WorkloadCommand -ne "") {
            # Telemetry MUST be sampled while the workload is running. Running the workload
            # first and sampling afterwards measures the card at IDLE, which would produce a
            # power curve that says nothing about power under load - a silently worthless
            # dataset. So: launch the workload as a separate process, sample power for as
            # long as it runs, then collect its output.
            $stdoutPath = [System.IO.Path]::GetTempFileName()
            $stderrPath = [System.IO.Path]::GetTempFileName()
            $workloadStart = Get-Date

            $process = Start-Process -FilePath "cmd.exe" `
                -ArgumentList "/c", $WorkloadCommand `
                -PassThru -NoNewWindow `
                -RedirectStandardOutput $stdoutPath `
                -RedirectStandardError $stderrPath

            # Touching .Handle caches the process handle while the process is still alive.
            # Without it, Start-Process -PassThru returns an object whose ExitCode reads back
            # as $null after exit - and "$null -ne 0" is TRUE, so every successful point
            # printed a failure message with a blank code. That made a real crash and a clean
            # run produce identical output, i.e. no failure detection at all.
            $processHandle = $process.Handle

            while (-not $process.HasExited) {
                $reading = Read-Telemetry -Smi $nvidiaSmi
                if ($null -ne $reading) {
                    [void]$samples.Add($reading)
                    $throttleSeen[$reading.ThrottleMask] = $true
                }
                Start-Sleep -Milliseconds ([int]($SampleIntervalSeconds * 1000))
            }
            $process.WaitForExit()
            $workloadSeconds = [math]::Round(((Get-Date) - $workloadStart).TotalSeconds, 3)

            $stdoutText = ""
            if (Test-Path $stdoutPath) { $stdoutText = (Get-Content $stdoutPath -Raw) }
            $exitCode = $process.ExitCode
            if ($null -eq $exitCode) {
                Write-Host "[SWEEP] WARNING: could not read the workload's exit code at $target MHz - relying on bench_ok from its JSON."
            } elseif ($exitCode -ne 0) {
                $errText = ""
                if (Test-Path $stderrPath) { $errText = (Get-Content $stderrPath -Raw) }
                Write-Host "[SWEEP] Workload exited $exitCode at $target MHz. stderr: $(($errText -split "`n" | Select-Object -First 2) -join ' ')"
            }

            # The benchmark's own --json output carries its internal timing, which is more
            # precise than our wall-clock wrapper (it excludes process startup and CUDA init).
            foreach ($line in ($stdoutText -split "`r?`n")) {
                $trimmed = $line.Trim()
                if ($trimmed.StartsWith("{") -and $trimmed.EndsWith("}")) {
                    try { $workloadJson = $trimmed | ConvertFrom-Json } catch { }
                }
            }

            Remove-Item $stdoutPath, $stderrPath -ErrorAction SilentlyContinue
        } else {
            # No workload supplied: assume an external load is already running and just
            # sample for the configured window.
            $deadline = (Get-Date).AddSeconds($MeasureSeconds)
            while ((Get-Date) -lt $deadline) {
                $reading = Read-Telemetry -Smi $nvidiaSmi
                if ($null -ne $reading) {
                    [void]$samples.Add($reading)
                    $throttleSeen[$reading.ThrottleMask] = $true
                }
                Start-Sleep -Milliseconds ([int]($SampleIntervalSeconds * 1000))
            }
        }

        if ($samples.Count -eq 0) {
            Write-Host "[SWEEP] No telemetry collected at $target MHz - skipping this point."
            continue
        }

        # Window the samples to the benchmark's timed region.
        #
        # Sampling necessarily spans the whole workload PROCESS, but performance is measured
        # over a strictly smaller interval inside it. Averaging power across the difference
        # mixes in ~2.3 s of Python import and CUDA init at idle - measured on this machine as
        # 124.77 W recorded against 148.52 W actually drawn under load, a 16% understatement.
        # Efficiency is throughput / power, so an efficiency curve built from the process-wide
        # average is dividing a load number by a partly-idle one.
        #
        # The dilution also shrinks as the clock drops (the run lengthens while init stays
        # ~2.3 s), so it is a frequency-dependent bias, not a constant offset that would
        # cancel out of the comparison.
        $statSamples = @($samples)
        $windowApplied = $false
        if ($null -ne $workloadJson -and
            $null -ne $workloadJson.timed_region_start_unix -and
            $null -ne $workloadJson.timed_region_end_unix) {

            $windowStart = [double]$workloadJson.timed_region_start_unix
            $windowEnd = [double]$workloadJson.timed_region_end_unix
            $inWindow = @($samples | Where-Object { $_.Timestamp -ge $windowStart -and $_.Timestamp -le $windowEnd })

            # Two samples is the floor for an average worth reporting. Below that, fall back to
            # the whole process and say so - a loudly-flagged diluted number beats a silent one
            # computed from a single reading.
            if ($inWindow.Count -ge 2) {
                $statSamples = $inWindow
                $windowApplied = $true
            } else {
                Write-Host ("[SWEEP] WARNING: only {0} sample(s) fell inside the benchmark's timed region at {1} MHz." -f $inWindow.Count, $target)
                Write-Host "[SWEEP] Falling back to whole-process averages for this point - its power figure is diluted by CUDA init."
            }
        } elseif ($WorkloadCommand -ne "") {
            Write-Host "[SWEEP] WARNING: workload emitted no timed-region stamps at $target MHz - power averaged over the whole process."
        }

        $clockStats = $statSamples | Select-Object -ExpandProperty SmClock | Measure-Object -Average -Minimum -Maximum
        $memClockStats = $statSamples | Select-Object -ExpandProperty MemClock | Measure-Object -Average -Minimum -Maximum
        $powerStats = $statSamples | Select-Object -ExpandProperty PowerDraw | Measure-Object -Average -Minimum -Maximum
        $tempStats = $statSamples | Select-Object -ExpandProperty Temperature | Measure-Object -Average -Maximum
        $utilStats = $statSamples | Select-Object -ExpandProperty Utilization | Measure-Object -Average
        $processPowerStats = $samples | Select-Object -ExpandProperty PowerDraw | Measure-Object -Average

        $row = [pscustomobject]@{
            target_frequency_mhz   = $target
            achieved_frequency_avg = [math]::Round($clockStats.Average, 1)
            achieved_frequency_min = $clockStats.Minimum
            achieved_frequency_max = $clockStats.Maximum
            memory_clock_avg_mhz   = [math]::Round($memClockStats.Average, 1)
            memory_clock_min_mhz   = $memClockStats.Minimum
            memory_clock_max_mhz   = $memClockStats.Maximum
            lock_held              = ([math]::Abs($clockStats.Average - $target) -le 30)
            # Direction matters, and conflating the two hides the more dangerous failure.
            # BELOW target = the card could not sustain the request (power/thermal limits) -
            # ordinary, and expected at the top of the range where max boost is a bin the card
            # never actually holds. ABOVE target = the cap was not applied at all, which
            # nvidia-smi cannot do on its own. That means something outside nvidia-smi owns the
            # V/F curve - typically an MSI Afterburner profile with a flattened curve, which
            # pins a clock the card then refuses to drop below. That case is corrosive: several
            # grid points collapse onto the SAME clock, and a sweep that looks like N points is
            # really N-k, with duplicate rows that quietly overweight one frequency.
            lock_miss_mhz          = [math]::Round($clockStats.Average - $target, 1)
            lock_miss_direction    = if ([math]::Abs($clockStats.Average - $target) -le 30) { "none" }
                                     elseif ($clockStats.Average -gt $target) { "above" }
                                     else { "below" }
            power_avg_w            = [math]::Round($powerStats.Average, 2)
            power_min_w            = $powerStats.Minimum
            power_max_w            = $powerStats.Maximum
            temperature_avg_c      = [math]::Round($tempStats.Average, 1)
            temperature_max_c      = $tempStats.Maximum
            utilization_avg_pct    = [math]::Round($utilStats.Average, 1)
            power_avg_process_w    = [math]::Round($processPowerStats.Average, 2)
            power_window_applied   = $windowApplied
            workload_seconds       = $workloadSeconds
            bench_seconds          = if ($null -ne $workloadJson) { $workloadJson.duration_seconds } else { $null }
            bench_wall_seconds     = if ($null -ne $workloadJson) { $workloadJson.wall_seconds } else { $null }
            bench_monitoring_s     = if ($null -ne $workloadJson) { $workloadJson.monitoring_overhead_seconds } else { $null }
            bench_throughput       = if ($null -ne $workloadJson) { $workloadJson.throughput } else { $null }
            bench_throughput_unit  = if ($null -ne $workloadJson) { $workloadJson.throughput_unit } else { $null }
            bench_ok               = if ($null -ne $workloadJson) { $workloadJson.ok } else { $null }
            samples                = $statSamples.Count
            samples_process        = $samples.Count
            throttle_masks_seen    = ($throttleSeen.Keys -join ";")
        }
        [void]$results.Add($row)

        $heldNote = "held"
        if ($row.lock_miss_direction -eq "above") { $heldNote = "OVERSHOT +$($row.lock_miss_mhz)" }
        elseif ($row.lock_miss_direction -eq "below") { $heldNote = "UNDERSHOT $($row.lock_miss_mhz)" }
        $powerNote = "whole process"
        if ($windowApplied) { $powerNote = "{0} in-window of {1}" -f $statSamples.Count, $samples.Count }
        Write-Host ("[SWEEP]     {0,5} MHz -> achieved {1,6} MHz ({2}), {3,6} W [{4}], {5,3} C, util {6,3}%" -f `
            $target, $row.achieved_frequency_avg, $heldNote, $row.power_avg_w, $powerNote, $row.temperature_avg_c, $row.utilization_avg_pct)
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
$undilutedPoints = @($results | Where-Object { -not $_.power_window_applied })
$overshotPoints = @($results | Where-Object { $_.lock_miss_direction -eq "above" })
$undershotPoints = @($results | Where-Object { $_.lock_miss_direction -eq "below" })

# Grid points that landed on the same achieved clock. Bucketed at 25 MHz because a lock that
# holds still wanders a few MHz; two targets inside one bucket are one measurement, not two.
$clockGroups = @($results | Group-Object { [math]::Round($_.achieved_frequency_avg / 25) })
$collapsedGroups = @($clockGroups | Where-Object { $_.Count -gt 1 })

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
    # Band provenance. A fine sweep and a full-range sweep produce structurally identical CSVs
    # and must never be pooled or compared as if they covered the same thing.
    sweep_band_min_mhz   = $floorMhz
    sweep_band_max_mhz   = $ceilMhz
    sweep_band_explicit  = $explicitBand
    settle_seconds       = $SettleSeconds
    measure_seconds      = $MeasureSeconds
    drifted_points       = $driftedPoints.Count
    overshot_points      = $overshotPoints.Count
    undershot_points     = $undershotPoints.Count
    distinct_clocks_measured = $clockGroups.Count
    sample_interval_s    = $SampleIntervalSeconds
    power_windowed_points = ($results.Count - $undilutedPoints.Count)
    supported_clock_count = $supported.Count
    samples_file         = Split-Path $csvPath -Leaf
    schema_version       = "0.1.0"
}
$session | ConvertTo-Json -Depth 4 | Out-File -FilePath $jsonPath -Encoding utf8

Write-Host ""
Write-Host "[SWEEP] ===================== RESULT ====================="
Write-Host ("[SWEEP] Measured {0} of {1} planned frequencies." -f $results.Count, $targets.Count)
if ($abortedByUser) { Write-Host "[SWEEP] Sweep was stopped early by the user - partial curve." }
if ($undershotPoints.Count -gt 0) {
    Write-Host ("[SWEEP] NOTE: {0} point(s) ran BELOW their target by more than 30 MHz." -f $undershotPoints.Count)
    Write-Host "[SWEEP] The card could not sustain the requested clock - power or thermal limits. Expected"
    Write-Host "[SWEEP] at the top of the range, where max boost is a bin the card never actually holds."
}

if ($overshotPoints.Count -gt 0) {
    Write-Host ""
    Write-Host ("[SWEEP] *** {0} point(s) ran ABOVE their target - THE CLOCK CAP DID NOT APPLY. ***" -f $overshotPoints.Count)
    Write-Host "[SWEEP] nvidia-smi cannot exceed its own cap, so something else owns the V/F curve -"
    Write-Host "[SWEEP] typically an MSI Afterburner profile with a flattened curve pinning a high clock."
    Write-Host "[SWEEP] Close it / reset to stock and re-run before trusting this data."
    Write-Host "[SWEEP] Why this matters more than it looks: overshooting points collapse onto the SAME"
    Write-Host "[SWEEP] achieved clock, so the run yields fewer distinct frequencies than it claims and"
    Write-Host "[SWEEP] silently duplicates one. Check achieved_frequency_avg for repeats:"
    foreach ($group in $collapsedGroups) {
        Write-Host ("[SWEEP]   targets {0} MHz all ran at ~{1} MHz" -f `
            (($group.Group | ForEach-Object { $_.target_frequency_mhz }) -join ", "), $group.Group[0].achieved_frequency_avg)
    }
    Write-Host ("[SWEEP] Distinct frequencies actually measured: {0} of {1} planned." -f $clockGroups.Count, $targets.Count)
}
if ($WorkloadCommand -ne "" -and $undilutedPoints.Count -gt 0) {
    Write-Host ("[SWEEP] WARNING: {0} point(s) could not be windowed to the benchmark's timed region." -f $undilutedPoints.Count)
    Write-Host "[SWEEP] Their power_avg_w is averaged over the whole workload process, so it includes"
    Write-Host "[SWEEP] CUDA init at idle and understates load power. Check power_window_applied in the CSV."
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
