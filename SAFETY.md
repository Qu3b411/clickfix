# Handling the live samples and prepared lab

The sample archives contain live malware, and the controller in `c2/` can task the resident implant. Read this before extracting a sample or importing the prepared VM.

---

## Isolation is the condition for running it

**Extract individual sample payloads only inside a disposable, isolated guest. Never execute them on the host.** The prepared VM archive is assembled and extracted on a dedicated research host so VirtualBox can import its folders; do not mount the infected virtual disk there. Keep the infected guest on its single VirtualBox internal network, with no route to the internet, your LAN, or your host. Do not add NAT, bridged, or host-only adapters, shared folders, clipboard sharing, drag-and-drop, or Guest Additions.

If you cannot verify those conditions yourself, stop before extraction. The isolation model is recorded in [`docs/methodology.md`](docs/methodology.md); [`docs/reproducibility.md`](docs/reproducibility.md) describes the lab procedure.

## Live malware

> **WARNING — LIVE MALWARE**
>
> Files in `malware/samples/` contain live malicious software preserved for security research and reproducibility. Do not extract or execute them on a production system. Use an isolated analysis environment. Archives use the password `IAcknowledgeTheRiskOfExecuting`.
>
> The password requires a deliberate extraction step. It does not make the files safe.

Each sample has its own password-protected ZIP. No executable, MSI, DLL, or PowerShell payload is loose in this checkout. Git hooks and CI do not extract the archives. The prepared lab runs an infected disposable clone only after a researcher imports it and invokes `make iclickrickroll`; the harness checks its VirtualBox network configuration before starting Windows.

Both archive passwords are public. They make extraction an intentional act and can prevent casual handling, but they provide no confidentiality or containment.

## The C2 interception tooling (`c2/`)

The controller speaks the implant's reconstructed protocol. Its listener binds to the lab address and has no upstream. The implant still contains a hardcoded C2 address, `45.140.205.28:443` (**LIVE IOC — DO NOT NAVIGATE**). Inside the emulator, DNAT sends that traffic to the local controller while IP forwarding remains disabled. Check that redirect and the lack of an external route before starting the victim.

The published controller sends only the fixed frames tested in this lab. Do not extend it with arbitrary commands or an uplink and then treat the existing isolation checks as proof that the new behavior is safe.

## Prepared lab archive

The release has twelve numbered chunks of one password-protected ZIP. Assembly and extraction produce the infected VM folders, including the victim's saved RAM state. Follow [`iclickrickroll/README.md`](iclickrickroll/README.md) and [`iclickrickroll/MALWARE-WARNING.txt`](iclickrickroll/MALWARE-WARNING.txt) before importing either VM. The original evidentiary and golden VMs are not included.

## IOC safety

Prose defangs indicators such as `hxxp://86[.]109[.]75[.]7` and `sites[.]google[.]com/view/antibot172881`. An exact indicator required to explain the network redirect is marked **LIVE IOC — DO NOT NAVIGATE**. Quoted evidence and decoded payloads retain their original bytes unless the text explicitly says otherwise.

## Before you run the harness

Cloning the repository does not execute the sample. Importing the lab registers infected VMs, and `make iclickrickroll` resumes a disposable infected clone. The Windows desktop may look ordinary; its saved state already contains a resident implant. Check the adapters and host integration yourself before that command. If the preflight reports a mismatch, stop and correct the lab rather than bypassing the check.

If a file, VM setting, or network path differs from the instructions, stop and inspect it before continuing.
