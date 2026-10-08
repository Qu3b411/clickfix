# How the result was established

Three kinds of records support the result: the browser visit, a later capture of the payload chain, and runs of those saved payload bytes inside an isolated lab. The browser record reaches the fake verification page. The later samples expose the code beyond it. The VM runs show what those saved bytes did under the lab conditions described below. The [article](https://blog.jacobmohrbutter.com/clickfix/) follows the investigation; this page records the conditions behind its technical claims.

## Evidence and derived files

The original forensic set was collected once, hashed, and analyzed from copies. The supplied manifests were checked again at the major analysis boundaries: all six archives and all 26 case files passed. Decoder corrections and their output hashes were retained so derived bytes could be distinguished from the source.

The public samples came from a supplementary capture after the browser visit. They support reconstruction and execution of the chain, but no manifest ties each of those bytes to the original page load. The separately retrieved MSI is the documented exception: its hash matched. That distinction is why the runtime findings in this repository are stated against the saved samples.

## Static analysis

The page's inline layers led to the clipboard launcher and its PowerShell stages. MSI tables and CAB content exposed the PE side-load chain. That chain led into `Build.dat`, where an inserted region looked like data until the DLL's read length and callback path showed how it was used. The first decoder did not track all three changing registers in the XOR loop. Correcting that state produced valid x64 code. The corrected bytes and their hash were retained. The `.raw` task-script and stager records were then decoded and hashed.

The static work did not execute the sample. Its only network retrievals were two explicitly authorized GETs to exact recovered URLs, one request each with redirects disabled.

## Dynamic runs and isolation

Each disposable VirtualBox VM had one NIC on the same private internal network. There was no NAT, bridged, or host-only adapter; no uplink; and no shared clipboard, drag-and-drop, or Guest Additions in the victim. The emulator had IP forwarding set to `0`. Isolation checks preceded both boot and sample introduction. A clean, instrumented, powered-off snapshot preceded infection, and each run used a disposable clone.

Sysmon, Procmon, ETW for DNS, Task Scheduler, and WinHTTP, process and socket watchers, and timed memory dumps recorded guest behavior. Packet captures covered the host NIC and guest. Telemetry moved to a data disk and was read offline from a powered-off raw clone; the host never mounted a live infected disk.

INetSim and dnsmasq supplied simulated HTTP/HTTPS and wildcard DNS without an external route. The candidate C2 address was redirected inside the emulator to a local sink. No packet was sent to the live endpoint.

The prepared victim comes from the sealed run. Defender real-time protection was on, but its signatures were old and offline, and the specimen's install folder had a narrow exclusion. The specimen was not quarantined under those conditions. The run says nothing about detection on a fully updated Windows machine.

## Isolating the persistence condition

Several short runs ended before the delayed persistence writes appeared. Launch context, token, and network conditions were changed one at a time across disposable clones, and the failed boundaries were retained. The deciding condition was the lifetime of a UI error dialog: it kept `DeElevate64.exe` alive while the task script's delayed Run-key and scheduled-task writes could fire. A later controlled run confirmed both writes. Elevation and network reachability did not explain the difference in those runs.

## Protocol reconstruction & confirmation

The C2 frame format was reconstructed from code and passive traffic. Changing `0x56bc` between `1` and `0` tested whether the implant parsed locally generated replies; its connection timing changed in both directions. A subsequent fixed type-1 shell task returned the known marker and echoed the shell PID. The published controller binds only to the lab network and implements those demonstrated frames.

## Limits

The malware was not executed outside the isolated lab. The live C2 was not contacted, and no response was received from attacker infrastructure. The server frames in this repository were constructed locally. Other task types appear in the disassembly but were not driven against the resident implant.
