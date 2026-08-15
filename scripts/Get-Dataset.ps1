<#
.SYNOPSIS
    Downloads the public GPU-DVFS-Dataset CSVs into data/raw/.

.DESCRIPTION
    The dataset is not redistributed in this repository - its license has not been checked,
    and re-hosting someone else's data without that check is not a thing to do casually.
    This script fetches it from the source instead.

    Source: https://github.com/zyjopensource/GPU-DVFS-Dataset
    Contents: a single NVIDIA V100, 33 workloads, 13 core frequencies (757-1530 MHz).
#>

[CmdletBinding()]
param(
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"

if ([string]::IsNullOrWhiteSpace($OutputDirectory)) {
    $OutputDirectory = Join-Path $PSScriptRoot "..\data\raw"
}
if (-not (Test-Path $OutputDirectory)) {
    New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
}
$OutputDirectory = (Resolve-Path $OutputDirectory).Path

$baseUrl = "https://raw.githubusercontent.com/zyjopensource/GPU-DVFS-Dataset/main/"
$files = @("dataset_performance.csv", "dataset_power.csv", "dataset_efficiency.csv")

Write-Host "[DATASET] Downloading GPU-DVFS-Dataset into $OutputDirectory"

foreach ($file in $files) {
    $destination = Join-Path $OutputDirectory $file
    try {
        Invoke-WebRequest -Uri ($baseUrl + $file) -OutFile $destination -UseBasicParsing
        $size = (Get-Item $destination).Length
        Write-Host "[DATASET]   OK   $file ($size bytes)"
    } catch {
        Write-Host "[DATASET]   FAIL $file - $($_.Exception.Message)"
    }
}

Write-Host "[DATASET] Done. Check the dataset's license before quoting its numbers in a write-up."
