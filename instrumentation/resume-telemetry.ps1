$ErrorActionPreference = 'Stop'
$tools = 'C:\ForensicTools'
$telemetry = 'C:\Telemetry'
if (-not (Test-Path (Join-Path $telemetry 'before\completed-utc.txt'))) { throw 'Pre-sample baseline incomplete' }
if (-not (Get-Service Sysmon64 -ErrorAction SilentlyContinue | Where-Object Status -eq Running)) { throw 'Sysmon not running' }
if (Get-Process Procmon64 -ErrorAction SilentlyContinue) { throw 'Procmon already running' }
if (-not (Get-CimInstance Win32_LogicalDisk | Where-Object VolumeName -eq 'CFXEXPORT')) { throw 'Telemetry export disk absent' }
Remove-Item (Join-Path $telemetry 'stop-watch.flag') -ErrorAction SilentlyContinue

& wevtutil.exe sl 'Microsoft-Windows-Sysmon/Operational' '/ms:1073741824'
& wevtutil.exe sl 'Microsoft-Windows-DNS-Client/Operational' '/e:true' '/ms:67108864'
& wevtutil.exe sl 'Microsoft-Windows-TaskScheduler/Operational' '/e:true' '/ms:67108864'
& wevtutil.exe sl 'Microsoft-Windows-WinHttp/Operational' '/e:true' '/ms:67108864'
& netsh.exe trace start scenario=NetConnection capture=yes report=no persistent=no maxsize=1024 "tracefile=C:\Telemetry\netsh-runtime.etl"
if ($LASTEXITCODE -ne 0) { throw "Network trace failed: $LASTEXITCODE" }
& (Join-Path $tools 'Procmon64.exe') /AcceptEula /Quiet /BackingFile (Join-Path $telemetry 'procmon-runtime.pml')
Start-Sleep -Seconds 4
if (-not (Get-Process Procmon64 -ErrorAction SilentlyContinue)) { throw 'Procmon did not start' }
[pscustomobject]@{
  Utc = [DateTime]::UtcNow.ToString('o')
  TimeZone = (Get-TimeZone).Id
  Sysmon = (Get-Service Sysmon64).Status.ToString()
  ProcmonPid = (Get-Process Procmon64 | Select-Object -First 1).Id
} | ConvertTo-Json | Out-File (Join-Path $telemetry 'runtime-ready.json') -Encoding utf8
