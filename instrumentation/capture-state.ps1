param([Parameter(Mandatory=$true)][ValidateSet('before','after')][string]$Phase)
$ErrorActionPreference = 'Continue'
$root = Join-Path 'C:\Telemetry' $Phase
New-Item -ItemType Directory -Force $root | Out-Null
$times = [pscustomobject]@{ Phase=$Phase; Utc=[DateTime]::UtcNow.ToString('o'); Local=(Get-Date).ToString('o'); TimeZone=(Get-TimeZone).Id }
$times | ConvertTo-Json | Out-File (Join-Path $root 'clock.json') -Encoding utf8
Get-CimInstance Win32_Process | Select-Object Name,ProcessId,ParentProcessId,ExecutablePath,CommandLine,CreationDate |
  Export-Csv (Join-Path $root 'processes.csv') -NoTypeInformation
Get-CimInstance Win32_Service | Select-Object Name,DisplayName,State,StartMode,PathName,ProcessId |
  Export-Csv (Join-Path $root 'services.csv') -NoTypeInformation
Get-ScheduledTask | Select-Object TaskName,TaskPath,State,Author,Description,Actions,Triggers |
  Export-Clixml (Join-Path $root 'scheduled-tasks.xml')
Get-NetTCPConnection -ErrorAction SilentlyContinue | Export-Csv (Join-Path $root 'tcp.csv') -NoTypeInformation
Get-NetUDPEndpoint -ErrorAction SilentlyContinue | Export-Csv (Join-Path $root 'udp.csv') -NoTypeInformation
& 'C:\ForensicTools\autorunsc64.exe' -accepteula -a '*' -c -h -m > (Join-Path $root 'autoruns.csv')
& 'C:\ForensicTools\Listdlls64.exe' -accepteula -v > (Join-Path $root 'modules.txt')
& 'C:\ForensicTools\handle64.exe' -accepteula -a > (Join-Path $root 'handles.txt')
& reg.exe export 'HKCU' (Join-Path $root 'HKCU.reg') /y | Out-Null
& reg.exe export 'HKLM\SOFTWARE' (Join-Path $root 'HKLM-SOFTWARE.reg') /y | Out-Null
& reg.exe export 'HKLM\SYSTEM' (Join-Path $root 'HKLM-SYSTEM.reg') /y | Out-Null
& reg.exe save 'HKCU' (Join-Path $root 'HKCU.hiv') /y | Out-Null
& reg.exe save 'HKLM\SOFTWARE' (Join-Path $root 'HKLM-SOFTWARE.hiv') /y | Out-Null
& reg.exe save 'HKLM\SYSTEM' (Join-Path $root 'HKLM-SYSTEM.hiv') /y | Out-Null
& fsutil.exe usn queryjournal C: > (Join-Path $root 'usn-journal-state.txt')
Get-ChildItem -LiteralPath 'C:\' -Recurse -Force -File -ErrorAction SilentlyContinue |
  Select-Object FullName,Length,CreationTimeUtc,LastWriteTimeUtc,LastAccessTimeUtc |
  Export-Csv (Join-Path $root 'filesystem.csv') -NoTypeInformation
[DateTime]::UtcNow.ToString('o') | Out-File (Join-Path $root 'completed-utc.txt') -Encoding ascii
