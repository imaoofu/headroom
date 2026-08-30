<#
.SYNOPSIS
    Collect one complete replicate of the twelve-workload suite, at stock, in one sitting.

.DESCRIPTION
    Everything the consumer half of this paper rests on was measured once. Section 5.5's
    arithmetic-intensity table, 5.6.1.1's fixed-versus-per-workload comparison and 5.6.2.1's
    constrained-model retest all read from twelve curves collected a single time each, so nothing
    in them carries an interval. This script collects another complete set under identical
    conditions so they can.

    IT ALSO FIXES A PROVENANCE SPLIT
    The existing "twelve-workload suite" is really eight plus four. copy, bgemm128, bgemm1024 and
    conv came from the pilot batch collected earlier the same day under looser conditions, and
    stock-suite-20260829/README.md forbids leaning on sub-percent differences between the two
    batches. A replicate taken in one sitting has no such split, which is arguably worth more
    than the error bars.

    WHY THE ITERATION COUNTS ARE HARD-CODED HERE
    The methodology is fixed-work: duration is the performance metric, so a count must not vary
    within or between sweeps that will be compared. These are the counts from
    SUITE-ITERATIONS.md, calibrated 2026-08-28 on this card at stock for ~9 s of GPU work each.
    They are per card AND per configuration. Running this on a different card, or on this one
    with a different curve, needs its own calibration - the counts below would be measuring
    something else. gemm keeps its own long-standing default of 120, which is not re-set here
    because changing it would break comparability with 67 committed sweeps.

    THE STOCK CHECK IS NOT OPTIONAL, AND IT IS NOT nvidia-smi's max clock
    `clocks.max.memory` reports 14001 MHz whether or not an Afterburner memory offset is applied,
    so it CANNOT distinguish stock from tuned. That mistake was made on 2026-08-30: a run was
    labelled "memory untouched - verified 14001 MHz stock" while a +2500 offset was live, and the
    run's own telemetry later showed 16301 MHz. The only field that distinguishes them is the
    memory clock UNDER LOAD - 13801 stock, 16301 at +2500. This script measures it before
    collecting anything and refuses if it disagrees.

.PARAMETER Replicate
    Short tag distinguishing this set from the others, e.g. "r2". Becomes part of every label.

.PARAMETER AppliedSettings
    What is on the card, in your own words. Refused if empty - nothing can reconstruct it later.

.PARAMETER ExpectedMemoryClockMhz
    The memory clock this configuration should show under load. Default 13801, this card at
    stock. Set it deliberately if replicating a tuned configuration.

.EXAMPLE
    .\Invoke-SuiteReplicate.ps1 -Replicate r2 -AppliedSettings "STOCK - no Afterburner offsets"
#>

param(
    [Parameter(Mandatory = $true)][string]$Replicate,
    [string]$AppliedSettings = "",
    [int]$ExpectedMemoryClockMhz = 13801,
    [int]$MemoryClockToleranceMhz = 150,
    [switch]$SkipStockCheck
)

$ErrorActionPreference = "Stop"

$here = $PSScriptRoot
$repoRoot = Split-Path (Split-Path $here -Parent) -Parent
$workloadPy = "tools\frequency-sweep\gpu_workload.py"
$sweepPs1 = Join-Path $here "Invoke-FrequencySweep.ps1"

# Ascending declared arithmetic intensity. The order is fixed so that replicates are comparable
# to EACH OTHER; note it is not the order the original suite was collected in, which was split
# across two batches and not principled. Any thermal-ordering effect therefore sits between this
# set and the original, not between replicates - which is the comparison the intervals come from.
$SUITE = @(
    @{ Workload = "copy";      Iterations = 2660 },
    @{ Workload = "reduce";    Iterations = 2870 },
    @{ Workload = "softmax";   Iterations = 2600 },
    @{ Workload = "layernorm"; Iterations = 1597 },
    @{ Workload = "bgemm32";   Iterations = 2673 },
    @{ Workload = "bgemm64";   Iterations = 2661 },
    @{ Workload = "bgemm128";  Iterations = 2467 },
    @{ Workload = "bgemm256";  Iterations = 1579 },
    @{ Workload = "bgemm1024"; Iterations = 414  },
    @{ Workload = "attention"; Iterations = 147  },
    @{ Workload = "conv";      Iterations = 151  },
    @{ Workload = "gemm";      Iterations = 120  }
)

function Say([string]$text, [string]$colour = "White") { Write-Host $text -ForegroundColor $colour }

if ([string]::IsNullOrWhiteSpace($AppliedSettings)) {
    Say "REFUSING: -AppliedSettings is empty." "Red"
    Say "Nothing can reconstruct what was on the card later. A sweep without it is close to" "Yellow"
    Say "worthless, and a WRONG one is worse - see the 2026-08-30 memory-offset mislabelling." "Yellow"
    exit 1
}

Say ""
Say "=======================================================" "Cyan"
Say ("  Suite replicate {0} - {1} workloads" -f $Replicate, $SUITE.Count) "Cyan"
Say "=======================================================" "Cyan"
Say ("  configuration : {0}" -f $AppliedSettings)
Say ("  estimated     : ~{0} min at ~4.5 min per sweep" -f ([int]($SUITE.Count * 4.5)))

# ---- the check that distinguishes stock from tuned --------------------------------------
if (-not $SkipStockCheck) {
    Say ""
    Say "Verifying the memory clock UNDER LOAD before collecting anything..." "Cyan"
    Say "  (clocks.max.memory reads 14001 either way and cannot tell them apart)" "Gray"

    $probe = Start-Process -FilePath "python" -WorkingDirectory $repoRoot `
        -ArgumentList $workloadPy, "--workload", "membw", "--iterations", "1200", "--json" `
        -PassThru -WindowStyle Hidden

    $observed = 0
    for ($i = 0; $i -lt 25; $i++) {
        Start-Sleep -Milliseconds 400
        $raw = & nvidia-smi --query-gpu=clocks.current.memory --format=csv,noheader,nounits 2>$null
        $value = 0
        if ([int]::TryParse(("$raw").Trim(), [ref]$value)) {
            if ($value -gt $observed) { $observed = $value }
        }
        if ($probe.HasExited) { break }
    }
    if (-not $probe.HasExited) { $probe.WaitForExit() }

    Say ("  peak memory clock under load: {0} MHz (expected {1})" -f $observed, $ExpectedMemoryClockMhz)
    $delta = [math]::Abs($observed - $ExpectedMemoryClockMhz)
    if ($observed -eq 0) {
        Say "REFUSING: could not read a memory clock under load at all." "Red"
        exit 1
    }
    if ($delta -gt $MemoryClockToleranceMhz) {
        Say "" "Red"
        Say ("REFUSING: memory clock under load is {0} MHz, not {1} +/- {2}." -f `
             $observed, $ExpectedMemoryClockMhz, $MemoryClockToleranceMhz) "Red"
        Say "The card is not in the configuration this run claims. 13801 is stock on this card;" "Yellow"
        Say "16301 is the +2500 offset. Fix the card, or pass -ExpectedMemoryClockMhz if you are" "Yellow"
        Say "deliberately replicating a tuned configuration." "Yellow"
        exit 1
    }
    Say "  [ok] configuration matches what this run claims" "Green"
}

# ---- collect ----------------------------------------------------------------------------
$started = Get-Date
$failed = @()

for ($i = 0; $i -lt $SUITE.Count; $i++) {
    $item = $SUITE[$i]
    $label = "5060ti-stock-suite-{0}-{1}" -f $item.Workload, $Replicate
    $command = "python {0} --workload {1} --iterations {2} --json" -f `
               $workloadPy, $item.Workload, $item.Iterations

    Say ""
    Say "-------------------------------------------------------" "Cyan"
    Say ("  [{0}/{1}] {2}  ({3} iterations)" -f ($i + 1), $SUITE.Count, $item.Workload, $item.Iterations) "Cyan"
    Say "-------------------------------------------------------" "Cyan"

    & powershell.exe -ExecutionPolicy Bypass -File $sweepPs1 `
        -SessionLabel $label `
        -WorkloadCommand $command `
        -FrequencyCount 13 `
        -MinFrequencyPercent 40 `
        -AppliedSettings $AppliedSettings

    if ($LASTEXITCODE -ne 0) {
        # Not fatal on its own: one refused sweep (a busy GPU, a video engine waking up) should
        # not discard the eleven that would have succeeded. Recorded and reported at the end so
        # it cannot be missed, because a replicate missing a workload is not a replicate.
        Say ("  [!] {0} exited {1}" -f $item.Workload, $LASTEXITCODE) "Red"
        $failed += $item.Workload
    }
}

$minutes = ((Get-Date) - $started).TotalMinutes
Say ""
Say "=======================================================" "Cyan"
Say ("  Replicate {0} finished in {1:N0} min" -f $Replicate, $minutes) "Cyan"
Say "=======================================================" "Cyan"

if ($failed.Count -gt 0) {
    Say ("  {0} of {1} sweeps FAILED: {2}" -f $failed.Count, $SUITE.Count, ($failed -join ", ")) "Red"
    Say "  A replicate missing a workload cannot be compared to a complete one. Re-run those" "Yellow"
    Say "  workloads in this same session, or discard the set." "Yellow"
    exit 1
}

Say ("  all {0} sweeps completed" -f $SUITE.Count) "Green"
Say ""
Say "  Next: check every sweep reached 13 of 13 planned frequencies and that its locks held," "Gray"
Say "  then write a README recording the configuration, the baseline and this replicate's tag." "Gray"
exit 0
