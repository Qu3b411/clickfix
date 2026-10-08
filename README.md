# ClickFix: samples, protocol, and an isolated replay lab

The saved ClickFix page put a PowerShell launcher on the clipboard and told the visitor to run it as a verification step. Analysis of the later captured stages led to a weaponized MSI and, inside an isolated lab, a resident implant. Reconstruction of its protocol allowed a fixed shell task to be sent and the implant's reply to be checked. This repository holds the saved samples, parser, controller, observation scripts, and a prepared VirtualBox lab that repeats the tasking result.

The original browser, mailbox, and packet-capture evidence remains private. The [article](https://blog.jacobmohrbutter.com/clickfix/) follows the incident, the payload, and the controlled tasking run. This repository holds the material a researcher can inspect or replay.

---

## Read this before opening anything

This repository contains **live malware** inside password-protected archives. Read [`SAFETY.md`](SAFETY.md) before opening `malware/` or importing the prepared lab. The infected VM must have no path to the internet, your LAN, or your host.

## What you can examine

The page and installer show how the infection starts. The controller and prepared VMs test a narrower question: will the resident implant accept a locally constructed type-1 task? The checkout contains:

- four password-protected samples, with hashes for both the original bytes and their archives;
- the reconstructed C2 protocol and a local controller that speaks the few messages tested against the resident implant;
- the Sysmon configuration and capture scripts used to observe the sample; and
- method notes that separate saved evidence, decoded code, and behavior confirmed in the lab.

The [`iclickrickroll/`](iclickrickroll/) release supplies the infected Windows VM, isolated emulator, two ISOs, and harness used for the [recorded demonstration](https://www.youtube.com/watch?v=VRApu5B4TR8). The victim includes saved RAM: the implant is already resident and primed to beacon. An OVA would discard that state and require another infection run. The encrypted VM archive travels as twelve release assets, outside Git history. [`setup-lab.sh`](iclickrickroll/setup-lab.sh) downloads and verifies the parts before importing the VM folders.

The [incident image](images/incident/) is a cropped copy of the fake verification prompt. The [demo-evidence guide](docs/demo-evidence.md) identifies what the first task probe established and what the later video demonstrates. Raw captures, original screenshots, mailbox records, and the video source file are not in this checkout.

## Layout

| Path | Contents |
|---|---|
| [`SAFETY.md`](SAFETY.md) | live-malware handling rules — read first |
| [`malware/`](malware/) | the samples, one password-protected ZIP each + register |
| [`c2/`](c2/) | local controller and recovered protocol specification |
| [`instrumentation/`](instrumentation/) | Sysmon config + telemetry/capture scripts used to observe detonations |
| [`docs/`](docs/) | methodology, reproducibility, and a demo-evidence guide |
| [`images/incident/`](images/incident/) | cropped, metadata-stripped incident screenshot |
| [`iclickrickroll/`](iclickrickroll/) | optional prepared lab: release checksums, import and run instructions |
| [`manifests/SHA256SUMS.txt`](manifests/SHA256SUMS.txt) | integrity hashes for the listed source files |
| [`LICENSE.pending.md`](LICENSE.pending.md) | licensing is not yet selected; samples/third-party excluded |

## Sample provenance

The four samples in `malware/samples/` came from a supplementary capture after the browser visit. The record does not establish that the page and PowerShell stages are byte-identical to what was served during that visit. An authorized live retrieval did return the same MSI bytes. The archive password is `IAcknowledgeTheRiskOfExecuting`; original and ZIP hashes are recorded in [`malware/README.md`](malware/README.md).

## The local C2 controller

The code in `c2/` constructs the implant's native frames: a 120-byte arithmetic header, 88-byte field descriptors, and XOR-transformed fields. Changing field `0x56bc` altered the live client's connection behavior; a subsequent type-1 task started a shell and returned a known marker. The listener binds only to the isolated lab network and has no upstream or forwarding path. The wire format is in [`c2/protocol-spec.md`](c2/protocol-spec.md); usage and isolation requirements are in [`c2/README.md`](c2/README.md).

## Instrumentation

The Sysmon configuration and PowerShell scripts in [`instrumentation/`](instrumentation/) record process, network, registry, and persistence activity in a disposable Windows guest. Microsoft's `Sysmon64.exe` is not redistributed here; [`instrumentation/README.md`](instrumentation/README.md) explains the setup.

## Reproduce it

[`docs/reproducibility.md`](docs/reproducibility.md) lists the static and dynamic checks. [`docs/methodology.md`](docs/methodology.md) records the evidence collection and limits of each conclusion. To run the prepared demonstration, read [`iclickrickroll/README.md`](iclickrickroll/README.md) and run `bash iclickrickroll/setup-lab.sh`. The guide verifies and imports the archive, then prints the command to start the isolated lab.

## Integrity & privacy

Run `sha256sum -c manifests/SHA256SUMS.txt` from the repository root to verify the source files. The release parts have a separate manifest in `iclickrickroll/`; the extracted lab has another manifest for its own files. The public screenshot is cropped to the attacker-controlled prompt and stripped of metadata. Addresses, hostnames, and usernames shown in the released lab (`10.77.86.0/24`, `analyst`, `cfx-*`) are lab values.
