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
    throw 'Unknown child job.'
} catch {
    Write-Host "CHILD FAILED: $($_.Exception.Message)"
    exit 1
}
