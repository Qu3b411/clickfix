$ErrorActionPreference = 'Stop'
$volume = Get-CimInstance Win32_LogicalDisk | Where-Object { $_.VolumeName -eq 'CFXEXPORT' } | Select-Object -First 1
if (-not $volume) { throw 'CFXEXPORT telemetry disk not mounted' }
$root = 'C:\Telemetry'
$dest = $volume.DeviceID + '\Telemetry'
New-Item -ItemType Directory -Force $dest | Out-Null
$manifest = New-Object System.Collections.Generic.List[object]
$chunkSize = [long](1024 * 1024 * 1024)
foreach ($file in Get-ChildItem -LiteralPath $root -File -Recurse -ErrorAction SilentlyContinue) {
  $relative = $file.FullName.Substring($root.Length).TrimStart('\')
  $target = Join-Path $dest $relative
  New-Item -ItemType Directory -Force (Split-Path $target -Parent) | Out-Null
  $sourceHash = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
  if ($file.Length -lt $chunkSize) {
    Copy-Item -LiteralPath $file.FullName -Destination $target -Force
    $copyHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash
    $manifest.Add([pscustomobject]@{Source=$relative; SourceBytes=$file.Length; SourceSHA256=$sourceHash;
      Part=(Split-Path $target -Leaf); PartBytes=$file.Length; PartSHA256=$copyHash})
  } else {
    $inputStream = [System.IO.File]::OpenRead($file.FullName)
    try {
      $partNumber = 0
      $buffer = New-Object byte[] (4 * 1024 * 1024)
      while ($inputStream.Position -lt $inputStream.Length) {
        $partPath = $target + ('.part{0:D4}' -f $partNumber)
        $outputStream = [System.IO.File]::Create($partPath)
        try {
          $written = [long]0
          while ($written -lt $chunkSize -and $inputStream.Position -lt $inputStream.Length) {
            $readCount = [int][Math]::Min($buffer.Length, [Math]::Min($chunkSize-$written,$inputStream.Length-$inputStream.Position))
            $n = $inputStream.Read($buffer,0,$readCount)
            if ($n -le 0) { break }
            $outputStream.Write($buffer,0,$n)
            $written += $n
          }
        } finally { $outputStream.Dispose() }
        $partHash = (Get-FileHash -LiteralPath $partPath -Algorithm SHA256).Hash
        $manifest.Add([pscustomobject]@{Source=$relative; SourceBytes=$file.Length; SourceSHA256=$sourceHash;
          Part=(Split-Path $partPath -Leaf); PartBytes=$written; PartSHA256=$partHash})
        $partNumber++
      }
    } finally { $inputStream.Dispose() }
  }
}
$manifest | Export-Csv (Join-Path $dest 'export-manifest.csv') -NoTypeInformation
[DateTime]::UtcNow.ToString('o') | Out-File (Join-Path $dest 'export-completed-utc.txt') -Encoding ascii
