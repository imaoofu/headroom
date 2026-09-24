# Read HWiNFO's latest complete CSV row without locking the writer.
# HWiNFO repeats some header names, so ConvertFrom-Csv is not usable here.
function Get-HwinfoCoreVoltage([string]$path) {
    if (-not (Test-Path $path)) { throw "HWiNFO CSV missing: $path" }
    $stream=New-Object IO.FileStream($path,[IO.FileMode]::Open,[IO.FileAccess]::Read,[IO.FileShare]::ReadWrite)
    try {
        $reader=New-Object IO.StreamReader($stream)
        $header=$reader.ReadLine()
        if (-not $header) { throw 'HWiNFO CSV has no header.' }
        $head=@([regex]::Split($header, ',(?=(?:[^"]*"[^"]*")*[^"]*$)'))
        $indices=@(for($i=0;$i -lt $head.Count;$i++) { if ($head[$i] -match '^"?GPU Core Voltage') { $i } })
        if ($indices.Count -ne 1) { throw 'Exactly one GPU Core Voltage column is required.' }
        [void]$stream.Seek([math]::Max(0,$stream.Length-65536),[IO.SeekOrigin]::Begin)
        $reader.DiscardBufferedData()
        $tail=$reader.ReadToEnd()
        $lines=@($tail -split "`n" | Where-Object { $_.Trim() })
        for($j=$lines.Count-1;$j -ge [math]::Max(0,$lines.Count-15);$j--) {
            $fields=@([regex]::Split($lines[$j].TrimEnd("`r"), ',(?=(?:[^"]*"[^"]*")*[^"]*$)'))
            if ($fields.Count -ne $head.Count) { continue }
            $value=$fields[$indices[0]].Trim('"')
            $number=0.0
            if ([double]::TryParse($value,[Globalization.NumberStyles]::Float,[Globalization.CultureInfo]::InvariantCulture,[ref]$number)) { return $number }
        }
        throw 'No complete core-voltage sample in HWiNFO CSV tail.'
    } finally { $stream.Dispose() }
}

function Assert-HwinfoLogGrowth([string]$path, [int]$FirstDelayMs=3000, [int]$SecondDelayMs=4000) {
    Start-Sleep -Milliseconds $FirstDelayMs
    if (-not (Test-Path $path)) { throw "HWiNFO log was not created: $path" }
    $first=(Get-Item $path).Length
    Start-Sleep -Milliseconds $SecondDelayMs
    $second=(Get-Item $path).Length
    if ($second -le $first) { throw "HWiNFO log is not growing: $path" }
    return @{ first=$first; second=$second }
}
