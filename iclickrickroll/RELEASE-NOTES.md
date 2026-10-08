# iClickRickroll prepared lab

**Live malware. Authorized research in a fully isolated VirtualBox lab only.**
Read `MALWARE-WARNING.txt` and the repository's `SAFETY.md` first.

I packaged the victim at the point where the ClickFix implant was already
resident and waiting for tasking. Its saved RAM state travels with the Windows
VM folder; the isolated emulator, local controller, harness, two ISOs,
provenance, and checksums travel with it. The result is a prepared lab for
repeating the specific tasking result shown in the demo.

Download `part00` through `part11` and the three small sidecars. Those parts
join into one password-protected ZIP of 22,887,509,030 bytes. Password:
`IAcknowledgeMaliciousContent`.

For guided setup, clone the repository and run `bash iclickrickroll/setup-lab.sh`.
It verifies the parts and joined ZIP, asks for the live-malware acknowledgement,
checks the extracted files, and imports both baselines. It prints the command
that starts the lab; setup itself does not start a VM. For manual assembly and
import, use `ARCHIVE-INSTRUCTIONS.txt`. After import, run `make iclickrickroll`.
Once its emulator preflight passes, type `send-rick` in the C2 pane. The task
is delivered on the implant's next beacon, so the video does not necessarily
open the moment you press Enter.

I tested these packaged baselines in a clean VirtualBox home. The full demo
acceptance run passed, the ZIP passed password/CRC testing, and the twelve-part
stream matched the archive SHA-256.

Release ZIP file dates, VM snapshot metadata, and acceptance receipt times
were normalized or redacted for operator privacy. Guest disk and saved RAM
bytes are unchanged; the original research evidence remains private.
