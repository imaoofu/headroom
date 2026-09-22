<#
.SYNOPSIS
    Run one logged sweep start to finish, with no human and no GUI interaction by any agent.

.DESCRIPTION
    Reads a JOB FILE, validates every field, then does the whole boundary sequence itself:

        preflight -> HWiNFO log start -> frequency sweep -> HWiNFO log stop -> result file

    Designed to be the ONLY thing a scheduled task runs, so that an unelevated agent can trigger
    a bench run with `schtasks /run` and never touch an elevated window. See README.md for why
    that indirection is necessary rather than merely tidy (UIPI; the Codex MSIX cannot elevate).

.PARAMETER JobPath
    The job file. Defaults to the fixed location the scheduled task uses.

.PARAMETER WhatIfOnly
    Validate the job and print the plan. Changes no GPU state, starts no log.

.NOTES
    🛑 THE SECURITY RULE THIS SCRIPT ENFORCES, AND WHY IT IS NOT PARANOIA.
        The scheduled task runs ELEVATED. If the job file could name the command to run, or the
        path to write, then any process that can write a file would have arbitrary administrator
        execution. So:

          - The workload COMMAND is constructed here from a whitelisted workload NAME. The job
            file cannot supply a command line.
          - The output directory is DERIVED from the label. The job file cannot supply a path,
            so path traversal has nothing to traverse.
          - Every numeric field is range-checked, and the label is pattern-matched.
          - Anything unrecognised is a refusal, not a default.

        The job file is a REQUEST. It is never an instruction.
#>

[CmdletBinding()]
param(
    [string]$JobPath = "C:\headroom-bench\job.json",
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$sweep    = Join-Path $repoRoot "tools\frequency-sweep\Invoke-FrequencySweep.ps1"
$workload = Join-Path $repoRoot "tools\frequency-sweep\gpu_workload.py"
$logTool  = Join-Path $PSScriptRoot "Invoke-HwinfoLogging.ps1"

# Output always lands under here, one directory per label. Never taken from the job.
$resultsRoot = "C:\headroom-bench\results"

# The only workloads this wrapper will ever run.
$allowedWorkloads = @("gemm", "membw", "copy", "reduce", "softmax", "layernorm",
                      "bgemm32", "bgemm64", "bgemm128", "bgemm256", "bgemm1024",
                      "attention", "conv")

function Say([string]$t, [string]$c = "White") { Write-Host $t -ForegroundColor $c }
function Die([string]$t, [int]$code) { Say $t "Red"; exit $code }

# ---- read and validate the job ---------------------------------------------------------------

if (-not (Test-Path $JobPath)) { Die "No job file at $JobPath." 2 }

try { $job = Get-Content $JobPath -Raw | ConvertFrom-Json }
catch { Die "Job file is not valid JSON: $($_.Exception.Message)" 2 }

$label = [string]$job.label
if ($label -notmatch '^[a-z0-9][a-z0-9-]{2,63}$') {
    Die "label must be 3-64 chars of lowercase letters, digits and hyphens. Got '$label'." 2
}

$work = [string]$job.workload
if ($allowedWorkloads -notcontains $work) {
    Die ("workload '{0}' is not in the allowed list: {1}" -f $work, ($allowedWorkloads -join ", ")) 2
}

function Need-Int($value, $name, $lo, $hi) {
    $n = 0
    if (-not [int]::TryParse([string]$value, [ref]$n)) { Die "$name must be an integer. Got '$value'." 2 }
    if ($n -lt $lo -or $n -gt $hi) { Die "$name must be between $lo and $hi. Got $n." 2 }
    return $n
}

$minMhz = Need-Int $job.minMhz "minMhz" 200 4000
$maxMhz = Need-Int $job.maxMhz "maxMhz" 200 4000
$count  = Need-Int $job.frequencyCount "frequencyCount" 3 40
if ($maxMhz -le $minMhz) { Die "maxMhz ($maxMhz) must exceed minMhz ($minMhz)." 2 }

$applied = [string]$job.appliedSettings
if ($applied.Trim().Length -lt 20) {
    Die "appliedSettings is required and must actually describe the configuration. It is the one field nothing can reconstruct afterwards." 2
}
if ($applied.Length -gt 600) { Die "appliedSettings is implausibly long ($($applied.Length) chars)." 2 }

$iterations = ""
if ($job.PSObject.Properties.Name -contains "iterations" -and $job.iterations) {
    $iterations = [string]$job.iterations
    if ($iterations -notmatch '^\d+(,\d+)*$') { Die "iterations must be digits separated by commas. Got '$iterations'." 2 }
}

$descending = $false
if ($job.PSObject.Properties.Name -contains "descending") { $descending = [bool]$job.descending }

$expectMinutes = Need-Int $job.expectedMinutes "expectedMinutes" 1 240

# ---- derived paths ---------------------------------------------------------------------------

$stamp   = Get-Date -Format "yyyyMMdd-HHmmss"
$outDir  = Join-Path $resultsRoot ("{0}_{1}" -f $stamp, $label)
$logPath = Join-Path $outDir ("{0}-hwinfo.csv" -f $label)
$result  = Join-Path $outDir "wrapper-result.json"

Say ""
Say "================ PLAN ================" "Cyan"
Say ("  label        : {0}" -f $label)
Say ("  workload     : {0}" -f $work)
Say ("  band         : {0}-{1} MHz, {2} points{3}" -f $minMhz, $maxMhz, $count, $(if ($descending) { ", DESCENDING" } else { "" }))
Say ("  iterations   : {0}" -f $(if ($iterations) { $iterations } else { "(tool default)" }))
Say ("  output dir   : {0}" -f $outDir)
Say ("  hwinfo log   : {0}" -f $logPath)
Say ("  expected     : ~{0} min" -f $expectMinutes)
Say ("  applied      : {0}" -f $applied)
Say ""

if ($WhatIfOnly) { Say "WhatIfOnly - validated, nothing run, no GPU state touched." "Yellow"; exit 0 }

foreach ($needed in @($sweep, $workload, $logTool)) {
    if (-not (Test-Path $needed)) { Die "Missing required script: $needed" 3 }
}
New-Item -ItemType Directory -Force -Path $outDir | Out-Null

# ---- preflight -------------------------------------------------------------------------------
# ⛔ This is a gate, not a formality. A run that begins on a contaminated machine produces data
# that looks fine and is worth nothing - measured at 9.38% on 2026-09-18, and a point-to-point
# residual cannot find it afterwards because it is blind to a uniform offset.

Say "---- preflight ----" "Cyan"
$power = (& nvidia-smi --query-gpu=power.limit,power.default_limit --format=csv,noheader) -join " | "
Say ("  power limit : {0}" -f $power)

$pmon = & nvidia-smi pmon -c 3 -s u 2>&1
$busy = $false
foreach ($line in $pmon) {
    if ($line -match '^\s*#') { continue }
    $cols = ($line -split '\s+') | Where-Object { $_ -ne "" }
    if ($cols.Count -lt 5) { continue }
    foreach ($idx in 3, 4) {
        $v = 0
        if ([int]::TryParse($cols[$idx], [ref]$v)) { if ($v -gt 10) { $busy = $true } }
    }
}
if ($busy) {
    Say "  pmon shows a busy GPU. REFUSING to start." "Red"
    $pmon | ForEach-Object { Say ("    " + $_) "Gray" }
    Die "Preflight failed: the card is not idle." 4
}
Say "  pmon        : idle enough" "Green"

# ---- log start -------------------------------------------------------------------------------

Say ""
Say "---- HWiNFO log start ----" "Cyan"
& $logTool -Start -LogPath $logPath
if ($LASTEXITCODE -ne 0) { Die "Could not start HWiNFO logging (exit $LASTEXITCODE). Nothing was swept." 5 }

# ---- the sweep -------------------------------------------------------------------------------
# From here on, always stop the log - a sweep that dies must not leave logging running, or the
# next run's log would span two configurations and the join bins by core clock.

$sweepExit = -1
$startedAt = Get-Date
try {
    Say ""
    Say "---- sweep ----" "Cyan"
    $cmd = '"{0}" "{1}" --workload {2} --json' -f (Join-Path $env:SystemRoot "..\..\Python312\python.exe"), $workload, $work
    # Prefer whatever python is actually on PATH; the line above is only a fallback shape.
    $py = (Get-Command python -ErrorAction SilentlyContinue)
    if ($py) { $cmd = '"{0}" "{1}" --workload {2} --json' -f $py.Source, $workload, $work }

    $args = @(
        "-SessionLabel",    $label,
        "-WorkloadCommand", $cmd,
        "-MinFrequencyMhz", $minMhz,
        "-MaxFrequencyMhz", $maxMhz,
        "-FrequencyCount",  $count,
        "-OutputDirectory", $outDir,
        "-AppliedSettings", $applied
    )
    if ($descending) { $args += "-Descending" }
    if ($iterations) { $args += @("-Iterations", $iterations) }

    & $sweep @args
    $sweepExit = $LASTEXITCODE
}
finally {
    Say ""
    Say "---- HWiNFO log stop ----" "Cyan"
    & $logTool -Stop -LogPath $logPath
    $stopExit = $LASTEXITCODE
}

$elapsed = [math]::Round(((Get-Date) - $startedAt).TotalMinutes, 1)

# ---- result file the agent can read unelevated ------------------------------------------------

$logBytes = 0
$logRows = 0
if (Test-Path $logPath) {
    $logBytes = (Get-Item $logPath).Length
    $logRows = (Get-Content $logPath | Measure-Object -Line).Lines
}

[pscustomobject]@{
    label           = $label
    startedAt       = $startedAt.ToString("o")
    finishedAt      = (Get-Date).ToString("o")
    elapsedMinutes  = $elapsed
    sweepExitCode   = $sweepExit
    logStopExitCode = $stopExit
    outputDirectory = $outDir
    hwinfoLog       = $logPath
    hwinfoLogBytes  = $logBytes
    hwinfoLogRows   = $logRows
    appliedSettings = $applied
} | ConvertTo-Json | Set-Content -Path $result -Encoding UTF8

Say ""
Say "================ RESULT ================" "Cyan"
Say ("  sweep exit    : {0}" -f $sweepExit)
Say ("  elapsed       : {0} min (expected ~{1})" -f $elapsed, $expectMinutes)
Say ("  hwinfo log    : {0} bytes, {1} rows" -f $logBytes, $logRows)
Say ("  result file   : {0}" -f $result)

if ($sweepExit -ne 0) { Say "  THE SWEEP FAILED. Treat this run as invalid." "Red"; exit 6 }
if ($logRows -lt 5)   { Say "  The HWiNFO log is nearly empty. There is no voltage evidence for this run." "Red"; exit 7 }

Say ""
Say "Run complete and both halves verified." "Green"
exit 0
