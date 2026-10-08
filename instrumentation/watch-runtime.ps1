$ErrorActionPreference = 'Continue'
$out = 'C:\Telemetry\watch-runtime.jsonl'
$seen = @{}
while (-not (Test-Path 'C:\Telemetry\stop-watch.flag')) {
  $now = [DateTime]::UtcNow.ToString('o')
  $processes = @(Get-CimInstance Win32_Process | Select-Object Name,ProcessId,ParentProcessId,ExecutablePath,CommandLine,CreationDate)
  $tcp = @(Get-NetTCPConnection -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,RemoteAddress,RemotePort,State,OwningProcess)
  $udp = @(Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Select-Object LocalAddress,LocalPort,OwningProcess)
  [pscustomobject]@{Utc=$now;Processes=$processes;Tcp=$tcp;Udp=$udp} | ConvertTo-Json -Depth 8 -Compress | Add-Content $out
  foreach ($p in $processes) {
    if ($p.Name -match '^(DeElevate64|waifu2x-converter|msiexec)\.exe$' -and -not $seen.ContainsKey($p.ProcessId)) {
      $seen[$p.ProcessId] = $true
      $dump = "C:\Telemetry\memory-$($p.Name)-$($p.ProcessId)-$([DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')).dmp"
      & 'C:\ForensicTools\procdump64.exe' -accepteula -ma $p.ProcessId $dump > "$dump.log" 2>&1
    }
  }
  Start-Sleep -Seconds 2
}
