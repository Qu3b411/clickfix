$ErrorActionPreference = 'Stop'
$volume = Get-CimInstance Win32_LogicalDisk | Where-Object { $_.VolumeName -eq 'CFXTOOLS' } | Select-Object -First 1
if (-not $volume) { throw 'CFXTOOLS read-only ISO not mounted' }
$source = $volume.DeviceID + '\'
$tools = 'C:\ForensicTools'
$telemetry = 'C:\Telemetry'
New-Item -ItemType Directory -Force $tools,$telemetry | Out-Null
Copy-Item (Join-Path $source '*') $tools -Recurse -Force
Start-Transcript -Path (Join-Path $telemetry 'setup-transcript.txt') -Force
try {
  Get-Date -Format o
  [DateTime]::UtcNow.ToString('o')
  Get-CimInstance Win32_TimeZone | Format-List *
  Get-ChildItem $tools -File | ForEach-Object {
    [pscustomobject]@{Name=$_.Name; Length=$_.Length; SHA256=(Get-FileHash $_.FullName -Algorithm SHA256).Hash;
      Signature=(Get-AuthenticodeSignature $_.FullName).Status.ToString()}
  } | Export-Csv (Join-Path $telemetry 'tool-verification.csv') -NoTypeInformation

  & (Join-Path $tools 'Sysmon64.exe') -accepteula -i (Join-Path $tools 'sysmon-full.xml')
  if ($LASTEXITCODE -ne 0) { throw "Sysmon install failed: $LASTEXITCODE" }
  & wevtutil.exe sl 'Microsoft-Windows-Sysmon/Operational' '/ms:1073741824'
  & wevtutil.exe sl 'Microsoft-Windows-DNS-Client/Operational' '/e:true' '/ms:67108864'
  & wevtutil.exe sl 'Microsoft-Windows-TaskScheduler/Operational' '/e:true' '/ms:67108864'
  & wevtutil.exe sl 'Microsoft-Windows-WinHttp/Operational' '/e:true' '/ms:67108864'
  & netsh.exe trace start scenario=NetConnection capture=yes report=no persistent=no maxsize=1024 "tracefile=C:\Telemetry\netsh-netconnection.etl"
  if ($LASTEXITCODE -ne 0) { throw "netsh trace failed: $LASTEXITCODE" }
  & (Join-Path $tools 'Sysmon64.exe') -c | Out-File (Join-Path $telemetry 'sysmon-active-config.txt') -Encoding utf8
  & (Join-Path $tools 'Sysmon64.exe') -s | Out-File (Join-Path $telemetry 'sysmon-schema.txt') -Encoding utf8
  Get-Service Sysmon64 -ErrorAction SilentlyContinue | Format-List * | Out-File (Join-Path $telemetry 'sysmon-service.txt')

  & (Join-Path $tools 'Procmon64.exe') /AcceptEula /Quiet /Minimized /BackingFile (Join-Path $telemetry 'procmon.pml')
  Start-Sleep -Seconds 3
  if (-not (Get-Process -Name Procmon64 -ErrorAction SilentlyContinue)) { throw 'Procmon did not remain running' }
  & (Join-Path $tools 'procexp64.exe') /AcceptEula /t
  Get-Process Procmon64,procexp64 -ErrorAction SilentlyContinue |
    Select-Object Name,Id,StartTime,Path | Export-Csv (Join-Path $telemetry 'instrumentation-processes.csv') -NoTypeInformation
  'READY ' + [DateTime]::UtcNow.ToString('o') | Out-File (Join-Path $telemetry 'instrumentation-ready.txt') -Encoding ascii
}
finally { Stop-Transcript }
