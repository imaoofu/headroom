param([Parameter(Mandatory=$true)][string]$JobPath)
$ErrorActionPreference='Stop'
try {
    $job=Get-Content $JobPath -Raw -Encoding UTF8 | ConvertFrom-Json
    if ($job.type -eq 'suite') {
        & $job.script -Label $job.label -AppliedSettings $job.settings -Workloads $job.workloads -Iterations $job.iterations -ExpectedMemoryClockMhz $job.expectedMemoryClockMhz -NoPause | Out-Host
        exit 0
    }
    if ($job.type -eq 'sweep') {
        $args=@{ SessionLabel=$job.label; WorkloadCommand=$job.command; MinFrequencyMhz=$job.minMhz; MaxFrequencyMhz=$job.maxMhz; FrequencyCount=$job.points; OutputDirectory=$job.output; AppliedSettings=$job.settings }
        if ($job.direction -eq 'descending') { $args.Descending=$true }
        & $job.script @args | Out-Host
        if ($LASTEXITCODE -ne 0) { exit 1 }
        exit 0
    }
    if ($job.type -eq 'calibrate') {
        # gpu_workload.py --calibrate times the card and prints the count as "--iterations N", the
        # same parse Calibrate-Suite.ps1 uses. Any workload without a count fails the whole step.
        $counts=@()
        foreach ($workload in @($job.workloads)) {
            Write-Host "Calibrating $workload"
            $output=& $job.python $job.workloadScript --workload $workload --calibrate --target-seconds $job.targetSeconds 2>&1
            $text=($output | Out-String)
            Write-Host $text
            $found=[regex]::Match($text, '--iterations\s+(\d+)')
            if (-not $found.Success) { throw "Calibration gave no count for $workload." }
            $counts+=[int]$found.Groups[1].Value
        }
        [IO.File]::WriteAllText($job.resultPath, (@{ workloads=@($job.workloads); iterations=$counts } | ConvertTo-Json), (New-Object Text.UTF8Encoding($false)))
        exit 0
    }
    throw 'Unknown child job.'
} catch {
    Write-Host "CHILD FAILED: $($_.Exception.Message)"
    exit 1
}
