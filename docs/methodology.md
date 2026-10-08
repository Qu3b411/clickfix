# How I established the result

Three records enter this investigation at different points: the original browser visit, a later capture of the payload chain, and execution of those saved payload bytes in an isolated lab. They answer different questions. The browser record establishes the route to the fake verification page; the supplementary samples expose the downstream code; the VM runs show what that code did under the lab's conditions. The companion article tells the story. This page records the conditions behind the technical claims.

## Evidence and derived files

I collected the original forensic set once, hashed it, and worked from copies. The supplied manifests were checked again at the major analysis boundaries: all six archives and all 26 case files passed. When a decoder or reconstruction changed, I kept the correction and the hash of its output so the derived bytes could be distinguished from the source.

The public samples came from a supplementary capture after the browser visit. I used them to reconstruct and execute the chain, but I do not have a manifest tying each of those bytes to the original page load. The separately retrieved MSI is the documented exception: its hash matched. That distinction is why the runtime findings in this repository are stated against the saved samples.

## Static analysis

I decoded the page's inline layers to reach the clipboard launcher, followed its PowerShell stages, parsed the MSI tables and CAB content, and mapped the PE side-load chain. That chain led into `Build.dat`, where an inserted region looked like data until the DLL's read length and callback path showed how it was used. My first decoder did not track all three changing registers in the XOR loop. Correcting that state produced valid x64 code; I kept the corrected bytes and their hash, then decoded and hashed the `.raw` task-script and stager records.

The static work did not execute the sample. Its only network retrievals were two explicitly authorized GETs to exact recovered URLs, one request each with redirects disabled.

## Dynamic runs and isolation

Each disposable VirtualBox VM had one NIC on the same private internal network. There was no NAT, bridged, or host-only adapter; no uplink; and no shared clipboard, drag-and-drop, or Guest Additions in the victim. The emulator had IP forwarding set to `0`. I checked these conditions before booting and again before introducing a sample. A clean, instrumented, powered-off snapshot preceded infection, and each run used a disposable clone.

Sysmon, Procmon, ETW for DNS, Task Scheduler, and WinHTTP, process and socket watchers, and timed memory dumps recorded guest behavior. I captured packets at the host NIC and inside the guest. Telemetry moved to a data disk and was read offline from a powered-off raw clone; the host never mounted a live infected disk.

INetSim and dnsmasq supplied simulated HTTP/HTTPS and wildcard DNS without an external route. The candidate C2 address was redirected inside the emulator to a local sink. No packet was sent to the live endpoint.

The prepared victim comes from the sealed run. Defender real-time protection was on, but its signatures were old and offline, and the specimen's install folder had a narrow exclusion. The specimen was not quarantined under those conditions. The run says nothing about detection on a fully updated Windows machine.

## Isolating the persistence condition

Several short runs ended before the delayed persistence writes appeared. I changed launch context, token, and network conditions one at a time across disposable clones and kept the failed boundaries. The deciding condition was the lifetime of a UI error dialog: it kept `DeElevate64.exe` alive while the task script's delayed Run-key and scheduled-task writes could fire. A later controlled run confirmed both writes. The effect was not explained by elevation or network reachability in those runs.

## Protocol reconstruction & confirmation

I first reconstructed the C2 frame format from code and passive traffic. To test whether the implant parsed the replies, I changed `0x56bc` between `1` and `0` and observed its connection timing change in both directions. I then sent a fixed type-1 shell task; the reply carried the known marker and echoed the shell PID. The published controller binds only to the lab network and implements those demonstrated frames.

## Limits

I did not execute the malware outside the isolated lab, contact the live C2, or receive a response from attacker infrastructure. The server frames in this repository were constructed locally. Other task types appear in the disassembly, but I did not drive them against the resident implant.
