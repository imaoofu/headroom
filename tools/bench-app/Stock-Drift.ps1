# Same registered stock-return statistic as analysis/score_session_d.py.
function Measure-StockDrift([string]$firstDir,[string]$lastDir,[string[]]$workloads) {
    $per=@{}
    foreach ($name in $workloads) {
        $pattern='*-' + $name + '_sweep.csv'
        $a=@(Get-ChildItem $firstDir -Filter $pattern)
        $b=@(Get-ChildItem $lastDir -Filter $pattern)
        if ($a.Count -ne 1 -or $b.Count -ne 1) { throw "Missing stock return CSV for $name." }
        $rowsA=@(Import-Csv $a[0].FullName); $rowsB=@(Import-Csv $b[0].FullName)
        if ($rowsA.Count -ne 13 -or $rowsB.Count -ne 13) { throw "Stock return $name needs 13 points on each side." }
        $lookup=@{}
        foreach ($row in $rowsA) { $lookup[[string]$row.target_frequency_mhz]=$row }
        if ($lookup.Count -ne 13) { throw "Stock return $name has duplicate first-run targets." }
        $changes=@()
        $seenTargets=@{}
        foreach ($row in $rowsB) {
            $key=[string]$row.target_frequency_mhz
            if ($seenTargets.ContainsKey($key)) { throw "Stock return $name has duplicate last-run target $key." }
            $seenTargets[$key]=$true
            if (-not $lookup.ContainsKey($key)) { throw "Stock return $name has unmatched target $key." }
            $x=[double]::Parse($lookup[$key].bench_throughput,[Globalization.CultureInfo]::InvariantCulture)
            $y=[double]::Parse($row.bench_throughput,[Globalization.CultureInfo]::InvariantCulture)
            if ($x -le 0 -or $y -le 0) { throw "Stock return $name has nonpositive throughput." }
            $changes+=[math]::Abs(100*($y/$x-1))
        }
        $sorted=@($changes | Sort-Object)
        $per[$name]=[double]$sorted[6]
    }
    $worst=($per.Values | Measure-Object -Maximum).Maximum
    return @{ worstMedianAbsPct=$worst; perWorkload=$per }
}
