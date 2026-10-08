# What the task probe and video each show

The browser window is the visible part of the demo, but it is not where I drew
the conclusion. In the first type-1 task probe, the controller sent a frame I
constructed; the resident implant started `cmd.exe`, returned
`CFX_RICKROLL_TASK_PROOF` with the shell PID, and opened a page served inside
the lab. The packet captures and Sysmon process tree gave me independent
places to check that path. The first page did not play the video. I later used
the same task path for the audio/video presentation, which the
[prepared lab](../iclickrickroll/README.md) lets a researcher repeat.

## Original task probe

In the isolated probe, the local controller sent four fixed frames: accept
(`0x56bc=1`), type-1 task start, `echo CFX_RICKROLL_TASK_PROOF`, and
`start "" msedge.exe http://10.77.86.2:8080/`. The observed process chain was
`DeElevate64.exe` PID 7568 → `cmd.exe` PID 3364 → `msedge.exe` PID 5304. The
implant's reply field `0x5975` contained 3364, matching the shell PID. Both
host NIC captures reconstructed 21 complete client frames and four server
frames; the local HTTP server observed `GET /` and returned 200. This first
probe displayed a local Rickroll-themed page; it did not play the video.

The preserved probe report has SHA-256
`c89d3a4c207d04b9f5856b32b2546a555c70ee788b16929fa653e799f5ef852f`;
its decoded transcript is
`c54d63a714cff58afe1f5691de3e5fd0efd004bbe14e8c81d04df541caa1dfaa`.
The raw probe PCAP, Sysmon export, screenshots, and transcript remain in the
private forensic set. The public [controller](../c2/README.md) and
[protocol reconstruction](../c2/protocol-spec.md) document the implemented
mechanism and its limits; the original captures are not repo files.

## Packaged demo acceptance

The prepared lab contains the primed infected VM, isolated emulator, controller,
media, and harness. I imported both baselines into a clean VirtualBox user home
to test the package rather than a working analysis VM. `make iclickrickroll`
passed all 17 emulator preflight checks; the controller accepted a beacon and
`send-rick`; Edge opened the locally served video fullscreen. The archive
contains `provenance/acceptance-preflight.txt`,
`provenance/acceptance-controller.png`, and
`provenance/acceptance-victim.png` for this check. Its internal `SHA256SUMS`
verifies the extracted files before import.
The release acceptance images and receipt have exact clock times redacted.

The [Release checksum manifest](../iclickrickroll/ARCHIVE-SHA256SUMS) covers all
twelve archive parts and their assembled ZIP. The
[guided setup](../iclickrickroll/setup-lab.sh) verifies those hashes, asks for
the live-malware acknowledgement, verifies extracted files, and imports the
VMs. The researcher runs `make iclickrickroll` and types `send-rick` to repeat
the demo. The VMs have only the shipped VirtualBox internal network; the
emulator has no uplink or forwarding route. The sample's hardcoded address is
redirected solely inside that emulator.

The companion article will link the YouTube recording after upload. The video
lets a reader see the result; the packaged VM lab supplies the bytes and saved
state needed to rerun it. Neither the probe nor the prepared demo contacts an
attacker server or the real C2 endpoint.
