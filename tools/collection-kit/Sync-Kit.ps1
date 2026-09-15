<#
.SYNOPSIS
    Copy the current tooling into an already-built collection kit, and prove it landed.

.DESCRIPTION
    The kit is not committed to the repository - it carries a ~4.65 GB copy of Python and
    PyTorch. So the kit on the USB drive is a SNAPSHOT, and it silently rots every time the
    tooling in the repository changes.

    It had rotted badly by 2026-08-23, three days before a build. The kit was carrying:

      - Invoke-FrequencySweep.ps1 at schema 0.1.0 against the repository's 0.3.0, so it had
        neither -AppliedSettings nor the video-engine guard - the two things added specifically
        to stop the contamination that cost this project two days of re-measurement.
      - A Collect.ps1 that hardcoded "-stock" into the session label, so an overclocked run
        wrote files named  <label>-oc-gemm-stock_sweep.csv  and read as stock data to anyone
        scanning the directory later.
      - A stability logger without the BOM fix, whose session.json broke every standard JSON
        parser.

    None of those announce themselves. Each one produces a run that looks completely successful
    and is quietly worth less than it should be. This script exists so that "is the kit current?"
    is one command with a verifiable answer, rather than a thing to remember.

    It copies TOOLING ONLY. Python, PyTorch and collected results are never touched, so running
    this on a kit with data in it is safe.

.PARAMETER KitPath
    The existing kit folder, e.g. F:\headroom-kit.

.PARAMETER WhatIfOnly
    Report what differs and change nothing.

.EXAMPLE
    .\Sync-Kit.ps1 -KitPath F:\headroom-kit -WhatIfOnly
    .\Sync-Kit.ps1 -KitPath F:\headroom-kit
#>

param(
    [Parameter(Mandatory = $true)]
    [string]$KitPath,
    [switch]$WhatIfOnly
)

$ErrorActionPreference = "Stop"

# This file lives in tools\collection-kit, so the repository root is two levels up.
$repoRoot = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent

# Source in the repository -> destination relative to the kit root.
$files = @(
    @{ From = "tools\frequency-sweep\Invoke-FrequencySweep.ps1"; To = "tools\frequency-sweep\Invoke-FrequencySweep.ps1" },
    # ⛔ MISSING FROM THIS LIST UNTIL 2026-09-14, AND ITS ABSENCE WAS SILENT BY DESIGN.
    # Invoke-FrequencySweep.ps1 dot-sources this helper to check that the benchmark actually
    # produced numbers. When it is not found the sweep prints a NOTE and carries on WITHOUT the
    # check - which is the right behaviour for an old kit, and exactly wrong for a freshly synced
    # one. So syncing would have installed the guard's caller and not the guard, leaving the kit
    # in the one state that looks current and is not.
    # 🔑 The guard exists because of a failure on the RTX 2060 Super on 2026-09-12: a hand-written
    # invocation with the interpreter on D: and the script on F: timed a process that exited in
    # half a second and wrote thirteen clean-looking idle points. See
    # data/frequency-sweeps/rtx2060s-20260912/failed-invocations/README.md.
    @{ From = "tools\frequency-sweep\WorkloadResultVerdict.ps1"; To = "tools\frequency-sweep\WorkloadResultVerdict.ps1" },
    @{ From = "tools\frequency-sweep\gpu_workload.py";           To = "tools\frequency-sweep\gpu_workload.py" },
    @{ From = "tools\Disable-QuickEdit.ps1";                     To = "tools\Disable-QuickEdit.ps1" },
    @{ From = "tools\stability-logger\Log-GpuStability.ps1";     To = "tools\stability-logger\Log-GpuStability.ps1" },
    @{ From = "tools\collection-kit\Collect.ps1";                To = "Collect.ps1" },
    @{ From = "tools\collection-kit\Calibrate-Suite.ps1";        To = "Calibrate-Suite.ps1" },
    @{ From = "tools\collection-kit\RUN-ME.bat";                 To = "RUN-ME.bat" },
    @{ From = "tools\collection-kit\preflight.py";               To = "preflight.py" },
    @{ From = "tools\collection-kit\CHECKLIST.txt";              To = "CHECKLIST.txt" },
    # HWiNFO's own config, which sets SensorInterval and therefore the sampling rate of every
    # voltage measurement taken through the kit. It lived only on the USB drive until 2026-09-11,
    # so a rate change on one machine could not be seen from the repository. Synced like any other
    # tool for exactly that reason.
    @{ From = "tools\collection-kit\HWiNFO64.INI";               To = "HWiNFO64.INI" }
)

function Say([string]$text, [string]$colour = "White") {
    Write-Host $text -ForegroundColor $colour
}

if (-not (Test-Path $KitPath)) {
    Say "No kit at $KitPath." "Red"
    Say "This script updates an EXISTING kit. To build one from scratch see the README." "Yellow"
    exit 1
}

# A folder with a python\ subdirectory and a RUN-ME.bat is a kit. Anything else is probably a
# mistyped path, and this script writes files - so refuse rather than scatter them somewhere.
if (-not (Test-Path (Join-Path $KitPath "python\python.exe"))) {
    Say "$KitPath has no python\python.exe, so it is not a built kit." "Red"
    Say "Refusing to write into it in case the path is wrong." "Yellow"
    exit 1
}

Say ""
Say "Syncing tooling into $KitPath" "Cyan"
Say "  (Python, PyTorch and results are not touched.)" "Gray"
Say ""

$changed = @()
$same = @()
$missing = @()

foreach ($f in $files) {
    $src = Join-Path $repoRoot $f.From
    $dst = Join-Path $KitPath $f.To

    if (-not (Test-Path $src)) {
        $missing += $f.From
        Say ("  [MISSING IN REPO] {0}" -f $f.From) "Red"
        continue
    }

    $identical = $false
    if (Test-Path $dst) {
        $hSrc = (Get-FileHash $src -Algorithm SHA256).Hash
        $hDst = (Get-FileHash $dst -Algorithm SHA256).Hash
        $identical = ($hSrc -eq $hDst)
    }

    if ($identical) {
        $same += $f.To
        Say ("  [same]    {0}" -f $f.To) "DarkGray"
    } else {
        $changed += $f.To
        if ($WhatIfOnly) {
            Say ("  [WOULD UPDATE] {0}" -f $f.To) "Yellow"
        } else {
            $dstDir = Split-Path $dst -Parent
            if (-not (Test-Path $dstDir)) { New-Item -ItemType Directory -Path $dstDir -Force | Out-Null }
            Copy-Item $src $dst -Force
            Say ("  [updated] {0}" -f $f.To) "Green"
        }
    }
}

if ($missing.Count -gt 0) {
    Say ""
    Say "Files are missing from the repository itself. The kit was NOT fully synced." "Red"
    exit 1
}

Say ""

if ($WhatIfOnly) {
    Say ("$($changed.Count) file(s) would change, $($same.Count) already current.") "Cyan"
    Say "Re-run without -WhatIfOnly to apply." "Gray"
    exit 0
}

# ---- verify, rather than assume the copies landed ----
# Copy-Item to a USB drive can fail silently enough (write cache, full volume, read-only media)
# that a hash check afterwards is worth the two seconds it costs.

Say "Verifying..." "Gray"
$bad = 0
foreach ($f in $files) {
    $src = Join-Path $repoRoot $f.From
    $dst = Join-Path $KitPath $f.To
    if (-not (Test-Path $dst)) { Say ("  [BAD] not present: {0}" -f $f.To) "Red"; $bad++; continue }
    if ((Get-FileHash $src -Algorithm SHA256).Hash -ne (Get-FileHash $dst -Algorithm SHA256).Hash) {
        Say ("  [BAD] hash mismatch after copy: {0}" -f $f.To) "Red"
        $bad++
    }
}

if ($bad -gt 0) {
    Say ""
    Say "$bad file(s) did not copy correctly. Do not use this kit." "Red"
    exit 1
}
Say "  [ok] all $($files.Count) files match the repository" "Green"

# The sweep's schema version is the one field that says at a glance which generation of the
# tooling a kit is carrying, and it is stamped into every session JSON the kit produces.
$sweep = Join-Path $KitPath "tools\frequency-sweep\Invoke-FrequencySweep.ps1"
$schema = (Select-String -Path $sweep -Pattern 'schema_version\s*=\s*"([^"]+)"' | Select-Object -First 1)
if ($schema) {
    Say ("  [ok] sweep schema version: {0}" -f $schema.Matches[0].Groups[1].Value) "Green"
}

Say ""
Say "Kit is current. $($changed.Count) file(s) updated, $($same.Count) already matched." "Cyan"
Say ""
Say "Before build day, run RUN-ME.bat once on a machine you already understand." "Yellow"
Say "A synced kit is not a tested kit." "Yellow"
Say ""
exit 0
