<#
.SYNOPSIS
    One-command Headroom data collection for a machine that has nothing installed.

.DESCRIPTION
    Runs a stock frequency sweep for both workloads and writes everything into results\.
    Uses the portable Python bundled in this kit, so NOTHING is installed on the target
    machine and nothing is left behind when the folder is deleted.

    Designed to be run without anyone available to debug it. Every step that can fail is
    checked up front, and the script refuses to start rather than failing halfway and
    leaving the GPU clock-locked.

.NOTES
    Launch via RUN-ME.bat, which handles elevation. Running this directly needs an
    already-elevated PowerShell.
#>

param(
    [string]$Label = "",
    [switch]$SkipMembw,
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"
$kit = $PSScriptRoot

# Log everything. On build day nobody will be watching the whole run, and a failure that
# scrolled past is a failure nobody can diagnose afterwards.
$logDir = Join-Path $kit "results"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null
$transcript = Join-Path $logDir ("run-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
try { Start-Transcript -Path $transcript -Force | Out-Null } catch { }
$pythonExe = Join-Path $kit "python\python.exe"
$workloadPy = Join-Path $kit "tools\frequency-sweep\gpu_workload.py"
$sweepPs1 = Join-Path $kit "tools\frequency-sweep\Invoke-FrequencySweep.ps1"

function Say([string]$text, [string]$colour = "White") {
    Write-Host $text -ForegroundColor $colour
}
function Fail([string]$text) {
    Say ""
    Say "STOPPED: $text" "Red"
    Say ""
    Say "Nothing was changed. Fix the above and run RUN-ME.bat again." "Yellow"
    try { Stop-Transcript | Out-Null } catch { }
    if (-not $NoPause) { Read-Host "Press Enter to close" }
    exit 1
}

Say ""
Say "=======================================================" "Cyan"
Say "  Headroom collection kit" "Cyan"
Say "=======================================================" "Cyan"
Say ""

# ---- preflight: everything that could fail, checked BEFORE touching the GPU ----

Say "Checking this machine..." "Gray"

$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Fail "Not running as Administrator. Use RUN-ME.bat, and click Yes on the prompt."
}
Say "  [ok] running as Administrator" "Green"

$smi = Get-Command nvidia-smi -ErrorAction SilentlyContinue
if (-not $smi) {
    foreach ($candidate in @("C:\Windows\System32\nvidia-smi.exe",
                             "C:\Program Files\NVIDIA Corporation\NVSMI\nvidia-smi.exe")) {
        if (Test-Path $candidate) { $smi = @{ Source = $candidate }; break }
    }
}
if (-not $smi) { Fail "nvidia-smi not found. This machine needs an NVIDIA GPU with drivers installed." }
Say "  [ok] nvidia-smi found" "Green"

foreach ($required in @($pythonExe, $workloadPy, $sweepPs1)) {
    if (-not (Test-Path $required)) { Fail "Missing file in the kit: $required`n`nThe kit did not copy fully. Copy the whole folder again." }
}
Say "  [ok] kit files present" "Green"

# The sweep hands its workload string to `cmd /c` through Start-Process, which mangles
# embedded quotes - so a path containing a space cannot be quoted its way out of trouble.
# Measured directly: the quoted form fails with "The filename, directory name, or volume
# label syntax is incorrect" while the unquoted form runs fine. Short (8.3) names never
# contain spaces, so prefer those; if the volume has 8.3 generation disabled, refuse with
# an instruction rather than discovering this halfway through a clock-locked sweep.
function Get-SpaceFreePath([string]$path) {
    try {
        $fso = New-Object -ComObject Scripting.FileSystemObject
        $short = $fso.GetFile($path).ShortPath
        if ($short -and $short -notmatch '\s') { return $short }
    } catch { }
    return $path
}

$pythonForCmd = Get-SpaceFreePath $pythonExe
$workloadForCmd = Get-SpaceFreePath $workloadPy
if ($pythonForCmd -match '\s' -or $workloadForCmd -match '\s') {
    Fail ("This kit is in a folder whose path contains a space:`n`n  $kit`n`n" +
          "The sweep cannot pass a quoted path through to the benchmark. Move the whole " +
          "kit folder somewhere without spaces - for example E:\headroom-kit or " +
          "C:\headroom-kit - and run RUN-ME.bat again.")
}
Say "  [ok] kit path is usable" "Green"

# torch.cuda.is_available() is NOT sufficient: it says True on a card whose compute
# capability this build has no compiled kernels for, then fails on the first real operation
# with "no kernel image is available". preflight.py runs the actual benchmark kernels and
# synchronises, so that failure surfaces here rather than mid-sweep with clocks locked.
Say "  ... testing the GPU (first run can take a minute)" "Gray"
$preflightPy = Join-Path $kit "preflight.py"
if (-not (Test-Path $preflightPy)) { Fail "Missing file in the kit: $preflightPy" }
$pre = & $pythonExe $preflightPy 2>&1
$preExit = $LASTEXITCODE

$gpuName = ""
$vramFree = ""
foreach ($line in $pre) {
    $text = [string]$line
    if ($text -match '^INFO\|device=(.+)$')        { $gpuName = $matches[1] }
    if ($text -match '^INFO\|capability=(.+)$')    { Say "  [ok] compute capability: $($matches[1])" "Green" }
    if ($text -match '^INFO\|vram_free_gb=(.+)$')  { $vramFree = $matches[1] }
    if ($text -match '^WARN\|(.+)$')               { Say "  [warn] $($matches[1])" "Yellow" }
}
if ($preExit -ne 0) {
    $reason = ($pre | Where-Object { $_ -match '^FAIL\|' } | Select-Object -First 1) -replace '^FAIL\|', ''
    if (-not $reason) { $reason = ($pre -join "`n") }
    Fail "This GPU cannot run the benchmark.`n`n$reason"
}
Say "  [ok] GPU ran the benchmark kernels: $gpuName" "Green"
if ($vramFree) { Say "  [ok] VRAM free: $vramFree GB" "Green" }

# A busy GPU makes every number wrong. The sweep refuses above 10% anyway; say so early.
$util = (& $smi.Source --query-gpu=utilization.gpu --format=csv,noheader,nounits -i 0 2>$null | Select-Object -First 1)
if ($util -and [int]$util -gt 10) {
    Fail "GPU is already $util% busy. Close games, browsers with video, mining, or any AI app, then re-run.`n`nA loaded GPU makes every measurement wrong."
}
Say "  [ok] GPU is idle ($util% used)" "Green"

if ($Label -eq "") {
    Say ""
    Say "Name this machine. Use the GPU model, no spaces." "Yellow"
    Say "Examples:  rtx4070-super   rx7800xt   rtx3060ti-build12" "Gray"
    $Label = Read-Host "Machine label"
}
$Label = ($Label -replace '[^A-Za-z0-9\-_]', '-').Trim('-')
if ($Label -eq "") { $Label = "unlabelled" }

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir = Join-Path $kit "results\$stamp`_$Label"
New-Item -ItemType Directory -Path $outDir -Force | Out-Null

# ---- record what this machine IS, before measuring anything ----
# Nothing downstream can reconstruct this later, and a sweep without it is close to worthless.

Say ""
Say "Recording machine details..." "Gray"
$infoPath = Join-Path $outDir "machine-info.txt"
$sysinfo = @()
$sysinfo += "label            : $Label"
$sysinfo += "collected_at     : $(Get-Date -Format o)"
$sysinfo += "collected_by     : kit v1"
$sysinfo += "tuning_state_claimed : STOCK - ASSERTED BY THE OPERATOR, NOT VERIFIED."
$sysinfo += "                       Nothing in nvidia-smi reports whether an Afterburner or"
$sysinfo += "                       vendor profile is applied, so this kit cannot check it."
$sysinfo += "                       See measured_peak_sm_clock_mhz at the end of this file -"
$sysinfo += "                       that IS measured, and is the field to trust."
$sysinfo += ""
$sysinfo += "--- GPU (nvidia-smi) ---"
$sysinfo += (& $smi.Source --query-gpu=name,driver_version,vbios_version,memory.total,power.limit,power.max_limit,pcie.link.gen.max,pcie.link.width.max --format=csv -i 0 2>&1)
$sysinfo += ""
$sysinfo += "--- CPU / RAM / OS ---"
$cpu = Get-CimInstance Win32_Processor | Select-Object -First 1
$os = Get-CimInstance Win32_OperatingSystem
$ramGB = [math]::Round((Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory / 1GB, 1)
$sysinfo += "cpu              : $($cpu.Name.Trim())"
$sysinfo += "cpu_cores        : $($cpu.NumberOfCores) cores / $($cpu.NumberOfLogicalProcessors) threads"
$sysinfo += "ram_gb           : $ramGB"
$sysinfo += "os               : $($os.Caption) $($os.Version)"
$sysinfo += ""
$sysinfo += "--- NOTE ---"
$sysinfo += "The tuning_state_claimed line above is what the operator was SUPPOSED to do, not"
$sysinfo += "something this kit confirmed. If a profile was applied and nobody noticed, that"
$sysinfo += "line is wrong and nothing in it would reveal the mistake."
$sysinfo += "The measured peak clock appended below is the actual evidence. On a known GPU"
$sysinfo += "model, stock and tuned sustained clocks differ far more than run-to-run noise -"
$sysinfo += "measured on an RTX 5060 Ti: 2588 MHz stock against ~2950 MHz tuned, a 360 MHz"
$sysinfo += "gap. Classify the run from that number, not from the claim."
$sysinfo | Out-File -FilePath $infoPath -Encoding utf8
Say "  [ok] saved machine-info.txt" "Green"

# ---- the sweeps ----

$workloads = @("gemm")
if (-not $SkipMembw) { $workloads += "membw" }

$results = @()
foreach ($workload in $workloads) {
    Say ""
    Say "-------------------------------------------------------" "Cyan"
    Say "  Sweep $($workloads.IndexOf($workload) + 1) of $($workloads.Count): $workload" "Cyan"
    Say "  Takes about 6-12 minutes. Leave the machine alone." "Gray"
    Say "  Do NOT click inside this window - it pauses the run." "Yellow"
    Say "-------------------------------------------------------" "Cyan"
    Say ""

    $command = '{0} {1} --workload {2} --json' -f $pythonForCmd, $workloadForCmd, $workload

    try {
        # No hardcoded "-stock" here. It produced filenames like
        # `5060ti-oc-gemm-stock_sweep.csv` on an overclocked run, which reads as stock data
        # to anyone scanning the directory. $Label already carries the tuning state.
        & $sweepPs1 -SessionLabel "$Label-$workload" `
                    -WorkloadCommand $command `
                    -OutputDirectory $outDir
        $results += [pscustomobject]@{ Workload = $workload; Ok = ($LASTEXITCODE -eq 0 -or $null -eq $LASTEXITCODE) }
    } catch {
        Say "  Sweep for $workload failed: $_" "Red"
        $results += [pscustomobject]@{ Workload = $workload; Ok = $false }
    }
}

# ---- verify we actually got data, rather than assuming ----

Say ""
Say "=======================================================" "Cyan"
Say "  Checking what was collected" "Cyan"
Say "=======================================================" "Cyan"

$csvFiles = @(Get-ChildItem -Path $outDir -Filter "*_sweep.csv" -ErrorAction SilentlyContinue)
$allGood = $true

if ($csvFiles.Count -eq 0) {
    Say "  [BAD] No sweep CSV files were written." "Red"
    $allGood = $false
} else {
    foreach ($file in $csvFiles) {
        $rows = @(Import-Csv $file.FullName)
        $withThroughput = @($rows | Where-Object { $_.bench_throughput -and $_.bench_throughput -ne "" })
        $locksHeld = @($rows | Where-Object { $_.lock_held -eq "True" })
        if ($withThroughput.Count -ge 10) {
            Say ("  [ok] {0}: {1} points, {2} with performance data, {3} locks held" -f `
                 $file.Name, $rows.Count, $withThroughput.Count, $locksHeld.Count) "Green"
        } else {
            Say ("  [BAD] {0}: only {1} of {2} points have performance data" -f `
                 $file.Name, $withThroughput.Count, $rows.Count) "Red"
            $allGood = $false
        }
    }
}

# The provenance line above is an assertion. This is the measurement that can check it, and
# it costs nothing extra - the sweep already recorded the achieved clock at every point.
# Peak clock is recorded PER WORKLOAD, never pooled. The two workloads draw different power
# and therefore reach different clocks on the same card at the same settings - measured here
# at stock: gemm 2588 MHz, membw 2753 MHz, a 165 MHz spread from workload alone. A single
# pooled figure would report membw's 2753 and invite a comparison against gemm's 2597 stock
# reference, which looks like an overclock and is not one.
$evidence = @()
$evidence += ""
$evidence += "--- MEASURED (this is evidence, unlike tuning_state_claimed) ---"
foreach ($file in $csvFiles) {
    $peak = 0.0
    foreach ($row in @(Import-Csv $file.FullName)) {
        $achieved = 0.0
        if ([double]::TryParse($row.achieved_frequency_avg, [ref]$achieved)) {
            if ($achieved -gt $peak) { $peak = $achieved }
        }
    }
    $which = if ($file.Name -match "-(gemm|membw)-") { $matches[1] } else { $file.BaseName }
    if ($peak -gt 0) {
        $evidence += ("peak_sm_clock_mhz[{0}] : {1:N0}" -f $which, $peak)
        Say ("  [ok] peak SM clock, {0}: {1:N0} MHz (provenance evidence)" -f $which, $peak) "Green"
    }
}
$evidence += "  Highest sustained SM clock reached in each sweep. Compare EACH against the same"
$evidence += "  workload's known stock figure for this GPU model - never against the other"
$evidence += "  workload's. Materially above stock means a profile was applied and this is NOT a"
$evidence += "  stock baseline, whatever tuning_state_claimed says."
$evidence += "  RTX 5060 Ti reference, measured: gemm 2588 stock / ~2950 tuned;"
$evidence += "  membw 2753 stock. Other models need their own reference before comparing."
$evidence | Out-File -FilePath $infoPath -Encoding utf8 -Append

Say ""
if ($allGood -and $csvFiles.Count -eq $workloads.Count) {
    Say "  COLLECTION SUCCEEDED" "Green"
    Say ""
    Say "  Results are in:" "White"
    Say "    $outDir" "White"
    Say ""
    Say "  Copy that whole folder off this machine, then delete the kit." "Yellow"
} else {
    Say "  COLLECTION INCOMPLETE - do not delete anything yet" "Red"
    Say ""
    Say "  Copy this folder anyway so the failure can be diagnosed:" "White"
    Say "    $outDir" "White"
}

Say ""
Say "  GPU clocks have been reset to normal automatically." "Gray"
Say "  Verify with:  nvidia-smi -q -d CLOCK" "Gray"
Say ""
try { Stop-Transcript | Out-Null } catch { }
if (-not $NoPause) { Read-Host "Press Enter to close" }
