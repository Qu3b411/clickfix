$ErrorActionPreference = 'Continue'
'stop' | Out-File 'C:\Telemetry\stop-watch.flag' -Encoding ascii
& 'C:\ForensicTools\Procmon64.exe' /Terminate
& netsh.exe trace stop
Start-Sleep -Seconds 4
$channels = @('Microsoft-Windows-Sysmon/Operational','Microsoft-Windows-DNS-Client/Operational',
  'Microsoft-Windows-TaskScheduler/Operational','Microsoft-Windows-WinHttp/Operational',
  'System','Application','Security')
foreach ($channel in $channels) {
  $safe = $channel -replace '[\\/]','-'
  & wevtutil.exe epl $channel ("C:\Telemetry\" + $safe + '.evtx')
}
Get-ChildItem 'C:\Telemetry' -Recurse -File -ErrorAction SilentlyContinue |
  ForEach-Object { [pscustomobject]@{Path=$_.FullName;Bytes=$_.Length;SHA256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash} } |
  Export-Csv 'C:\Telemetry\artifact-hashes.csv' -NoTypeInformation
[DateTime]::UtcNow.ToString('o') | Out-File 'C:\Telemetry\completed-utc.txt' -Encoding ascii
