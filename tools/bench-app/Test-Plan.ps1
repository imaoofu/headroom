param([Parameter(Mandatory=$true)][string]$PlanPath)
$ErrorActionPreference = 'Stop'

function Require($condition, [string]$message) {
    if (-not $condition) { throw $message }
}
function Is-KitPath([string]$value) {
    return ($value -match '^kit:/[^.]' -and $value -notmatch '(^|[\\/])\.\.([\\/]|$)')
}
function Is-Absolute([string]$value) {
    return ([System.IO.Path]::IsPathRooted($value) -or $value -match '^[A-Za-z]:[\\/]' -or (Is-KitPath $value))
}
function Validate-Plan($plan) {
    Require ($null -ne $plan) 'Plan is empty.'
    Require ($plan.schemaVersion -eq 1) 'schemaVersion must be 1.'
    Require ($plan.volumeLabel -match '^[A-Za-z0-9 _-]{1,32}$' -and $plan.card.name) 'Plan needs a USB volume label and GPU name.'
    Require ($plan.card.minClockMhz -gt 0 -and $plan.card.maxClockMhz -gt $plan.card.minClockMhz) 'Invalid card clock range.'
    Require ($plan.runs.Count -gt 0) 'Select at least one run.'
    $runIds = @{}
    $allowedWorkloads=@('gemm','membw','copy','reduce','softmax','layernorm','bgemm32','bgemm64','bgemm128','bgemm256','bgemm1024','attention','conv')
    $seenRuns = @{}
    $logPaths = @{}
    $runIndex=0
    $closedGroups=@{}
    $activeGroup=''
    foreach ($run in $plan.runs) {
        $group=[string]$run.group
        if ($group -ne $activeGroup) {
            if ($activeGroup) { $closedGroups[$activeGroup]=$true }
            Require (-not ($group -and $closedGroups.ContainsKey($group))) "Locked group $group was split."
            $activeGroup=$group
        }
        if ($run.finalRun) { Require ($runIndex -eq ($plan.runs.Count - 1)) "Run $($run.id) must be last." }
        $runIndex++
        Require ($run.id -match '^[a-z0-9][a-z0-9-]{1,63}$') 'Invalid run id.'
        Require (-not $runIds.ContainsKey($run.id)) "Duplicate run id: $($run.id)"
        $runIds[$run.id] = $true
        foreach ($needed in @($run.requires)) { if ($needed) { Require ($seenRuns.ContainsKey([string]$needed)) "Run $($run.id) requires earlier run $needed." } }
        $seenRuns[$run.id]=$true
        Require ($run.steps.Count -gt 0) "Run $($run.id) has no steps."
        $logging = $false
        $usedLog = $false
        $needsWitness = $false
        foreach ($step in $run.steps) {
            Require ($step.id -match '^[a-z0-9][a-z0-9-]{1,63}$') 'Invalid step id.'
            $type = [string]$step.type
            Require (@('gate-power','gate-quiet','gate-hash','gate-drift','apply-profile','witness','hwinfo-start','hwinfo-stop','suite','sweep','human') -contains $type) "Unknown step type: $type"
            switch ($type) {
                'gate-power' { Require ($step.limit -gt 0 -and $step.default -gt 0 -and $step.max -gt 0) 'gate-power needs limit/default/max.' }
                'gate-quiet' { Require ($step.maxUtil -gt 0 -and $step.maxUtil -le 100) 'gate-quiet needs maxUtil 1..100.' }
                'gate-hash' {
                    Require ($step.path -and (Is-Absolute $step.path)) 'gate-hash needs an absolute path.'
                    Require ($step.prefix -match '^[0-9a-fA-F]{8,64}$') 'gate-hash needs a SHA-256 prefix.'
                }
                'gate-drift' {
                    Require ($step.firstRun -and $step.lastRun -and $step.workloads.Count -gt 0 -and $step.maxMedianAbsPct -gt 0) 'gate-drift needs firstRun, lastRun, workloads and maxMedianAbsPct.'
                    Require ($seenRuns.ContainsKey([string]$step.firstRun) -and $seenRuns.ContainsKey([string]$step.lastRun) -and $step.firstRun -ne $step.lastRun) 'gate-drift references missing or identical runs.'
                }
                'apply-profile' { Require (-not $logging) 'A profile cannot change while HWiNFO is logging.'; Require ($step.slot -ge 1 -and $step.slot -le 5) 'apply-profile slot must be 1..5.'; $needsWitness=$true }
                'witness' {
                    Require ($step.iterations -gt 0 -and $allowedWorkloads -contains $step.workload) 'witness needs a supported workload and iterations.'
                    Require ($step.coreMin -gt 0 -and $step.coreMax -ge $step.coreMin -and $step.memoryMin -gt 0 -and $step.memoryMax -ge $step.memoryMin) 'witness needs core and memory bounds.'
                    Require ($step.coreMin -ge $plan.card.minClockMhz -and $step.coreMax -le $plan.card.maxClockMhz) 'Witness core bounds outside card range.'
                    if ($step.lockMhz) { Require ($step.lockMhz -ge $plan.card.minClockMhz -and $step.lockMhz -le $plan.card.maxClockMhz) 'Witness lock outside card range.' }
                    if ($step.voltageMin -or $step.voltageMax) { Require ($logging) 'Voltage witness needs an active HWiNFO log.'; Require ($step.voltageMin -gt 0 -and $step.voltageMax -ge $step.voltageMin) 'Invalid voltage range.' }
                    $needsWitness=$false
                }
                'hwinfo-start' {
                    Require (-not $logging) 'A log is already active.'
                    Require ($step.path -and $step.path -match '^kit:/results/' -and (Is-KitPath $step.path)) 'hwinfo-start needs a kit:/results/ path.'
                    Require (-not $logPaths.ContainsKey($step.path.ToLowerInvariant())) 'Two runs share one HWiNFO log.'
                    $logPaths[$step.path.ToLowerInvariant()] = $true
                    $logging = $true
                    $usedLog = $true
                }
                'hwinfo-stop' { Require ($logging) 'hwinfo-stop without hwinfo-start.'; $logging = $false }
                'suite' {
                    Require ($logging) 'A suite needs hwinfo-start before it.'
                    Require (-not $needsWitness) 'Applied profile needs a witness before a suite.'
                    Require ($step.label -match '^[a-z0-9][a-z0-9-]{2,63}$' -and $step.settings) 'suite needs label and settings.'
                    Require ($step.workloads.Count -gt 0 -and $step.workloads.Count -eq $step.iterations.Count) 'suite workloads and iterations must match.'
                    Require ($step.expectedMemoryClockMhz -gt 0) 'suite needs expectedMemoryClockMhz.'
                    foreach ($name in $step.workloads) { Require ($allowedWorkloads -contains $name) "Unsupported suite workload: $name" }
                    foreach ($n in $step.iterations) { Require ($n -gt 0) 'Iterations must be positive.' }
                }
                'sweep' {
                    Require ($logging) 'A sweep needs hwinfo-start before it.'
                    Require (-not $needsWitness) 'Applied profile needs a witness before a sweep.'
                    Require ($step.label -match '^[a-z0-9][a-z0-9-]{2,63}$' -and $step.settings) 'sweep needs label and settings.'
                    $iterationsValue=0
                    Require ($allowedWorkloads -contains $step.workload -and -not ($step.iterations -is [array]) -and [int]::TryParse([string]$step.iterations,[ref]$iterationsValue) -and $iterationsValue -gt 0) 'sweep needs a supported workload and one fixed iteration count.'
                    Require ($step.minMhz -ge $plan.card.minClockMhz -and $step.maxMhz -le $plan.card.maxClockMhz -and $step.maxMhz -gt $step.minMhz) 'Sweep outside card supported clocks.'
                    Require ($step.points -ge 3 -and $step.points -le 40 -and @('ascending','descending') -contains $step.direction) 'Invalid sweep grid.'
                    Require ($step.output -and $step.output -match '^kit:/results/' -and (Is-KitPath $step.output)) 'sweep output must be under kit:/results/.'
                }
                'human' { Require (-not [string]::IsNullOrWhiteSpace($step.instruction)) 'human needs instruction.' }
            }
        }
        Require (-not $logging) "Run $($run.id) leaves its HWiNFO log open."
        Require (-not $needsWitness) "Run $($run.id) applies a profile without a witness."
        if ($run.requiresLog) { Require ($usedLog) "Run $($run.id) requires a log." }
    }
    if ($plan.revert) {
        Require ($plan.revert.slot -ge 1 -and $plan.revert.slot -le 5) 'Invalid revert slot.'
        Require ($null -ne $plan.revert.witness) 'Revert needs a witness.'
        $w=$plan.revert.witness
        Require ($allowedWorkloads -contains $w.workload -and $w.iterations -gt 0) 'Revert witness needs a supported workload and iterations.'
        Require ($w.coreMin -ge $plan.card.minClockMhz -and $w.coreMax -le $plan.card.maxClockMhz -and $w.coreMax -ge $w.coreMin) 'Invalid revert core bounds.'
        Require ($w.memoryMin -gt 0 -and $w.memoryMax -ge $w.memoryMin) 'Invalid revert memory bounds.'
    }
    return $true
}

try {
    Require ([System.IO.Path]::IsPathRooted($PlanPath)) 'PlanPath must be absolute.'
    $plan = Get-Content -LiteralPath $PlanPath -Raw -Encoding UTF8 | ConvertFrom-Json
    [void](Validate-Plan $plan)
    Write-Host 'VALID PLAN'
    exit 0
} catch {
    Write-Host ("INVALID PLAN: {0}" -f $_.Exception.Message)
    exit 2
}
