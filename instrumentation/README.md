# Instrumenting the Windows guest

I used these Sysmon rules and PowerShell scripts in a disposable Windows guest. They record the state before infection, watch the sample run, and export telemetry afterward. The paths and volume names are lab values; check them against your guest before running a script.

> **Microsoft `Sysmon64.exe` is not redistributed here.** Download it from the official [Sysinternals Sysmon](https://learn.microsoft.com/sysinternals/downloads/sysmon) page and apply `sysmon-full.xml`.

## Files

| File | What it does |
|---|---|
| `sysmon-full.xml` | Sysmon config enabling process create/terminate, network, image load, process access, remote thread, file create/delete, registry, DNS, named-pipe, WMI, executable creation, and process-tampering events, with SHA-256 hashing. |
| `setup-telemetry.ps1` | installs Sysmon with the config, enables DNS Client / Task Scheduler / WinHTTP operational channels, starts a network ETW trace, and launches Procmon. |
| `capture-state.ps1` | records filesystem/registry plus process/service/task/autorun/socket/module/handle baselines (before/after snapshots). |
| `watch-runtime.ps1` | samples process + socket state on an interval and dumps named suspect processes. |
| `finish-telemetry.ps1` | stops Procmon and the ETW trace and exports the EVTX logs. |
| `export-telemetry.ps1` | copies and hashes the raw records to a guest-writable disk for read-only host extraction after shutdown. |
| `resume-telemetry.ps1` | restarts Procmon + ETW after a saved-state resume. |

The before/after capture tells me which persistent objects changed. Sysmon and
Procmon supply the process and file sequence that led to those changes, while
the network trace ties a socket to the emulator capture. None of those logs
alone establishes the full execution path; the useful result comes from
matching the same process, port, and event order across them.

## How to use (isolated guest only)

1. Configure the clean guest and verify its isolation. Apply `sysmon-full.xml`, run `setup-telemetry.ps1`, and use `capture-state.ps1` to record the before-state.
2. Power off and snapshot that instrumented, pre-sample guest. Start a disposable clone from the snapshot; use `resume-telemetry.ps1` to restart Procmon and ETW before introducing the sample.
3. Detonate from the clone while `watch-runtime.ps1` records process and socket changes.
4. Capture the after-state, run `finish-telemetry.ps1` to export EVTX, then use `export-telemetry.ps1` to move records to the lab data disk.
5. Power off the guest and read the records from a powered-off clone. Do not mount a live infected disk on the host.

## Correlation note

Guest and emulator clocks can drift after a saved-state resume. A source port and the order of packets give a better join between guest events and captures than wall-clock time alone. The procedure is described in [`docs/reproducibility.md`](../docs/reproducibility.md).

The scripts use lab paths such as `C:\Telemetry` and a dedicated export disk. Check each path against your guest before running them.
