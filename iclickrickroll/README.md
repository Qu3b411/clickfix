# iClickRickroll prepared lab

The release contains the infected Windows VM baseline, the isolated emulator,
two ISOs, and the harness used for the recorded demonstration. The Windows VM
retains its saved RAM state because the resident implant is already primed to
beacon to the local controller. Importing these VM folders repeats that
condition; rebuilding a victim from the samples would start a different run.

The encrypted archive is divided into twelve numbered GitHub Release assets
and is not tracked in Git. Read [SAFETY.md](../SAFETY.md) and
[MALWARE-WARNING.txt](MALWARE-WARNING.txt) before downloading or importing it.

This package starts where my tasking experiment started: with the implant
already alive inside the victim. The source samples in `malware/` let you
inspect how it got there. The prepared VM lets you test whether the controller
can speak to that resident process and make the fixed task run.

## Guided setup

On a dedicated Linux/VirtualBox host, read the warning and inspect the setup
script. Then run it from the repository root:

```sh
bash iclickrickroll/setup-lab.sh
```

The terminal guide asks before download, extraction, and VM import. It checks
the SHA-256 of each part and the assembled ZIP before asking you to type
`IAcknowledgeMaliciousContent`. That entry is both the required acknowledgement
and the archive password; the helper passes it to `unzip` through a private
terminal rather than a process argument. It then verifies the extracted files,
offers the optional Debian/Ubuntu package install described by `packages.json`,
and imports both baselines. Setup prints `make iclickrickroll` when it finishes.
It does not start either VM.

The default research directory is `iclickrickroll-research/` beside the clone.
Two optional arguments set the download directory and research directory, in
that order.

## Acquire and verify without importing

Once the repository is public, you can acquire the archive without importing a
VM. Read the warning, inspect [`acquire-lab.sh`](acquire-lab.sh), and run:

```sh
bash iclickrickroll/acquire-lab.sh
```

The script retrieves all twelve numbered assets from the
[`iclickrickroll-lab-v1` release](https://github.com/qu3b411/clickfix/releases/tag/iclickrickroll-lab-v1),
checks each against the committed SHA-256 manifest, joins them in order, and
checks the resulting ZIP's hash. An interrupted part download can resume. This
command only downloads and verifies; it does not extract the archive or start a
VM.

The default output is `iclickrickroll-download/` beside the cloned repo; the
script prints its absolute path. You may pass another directory as its first
argument. Allow about 45 GB for parts plus
assembled ZIP, and substantially more for extraction and disposable VM clones.

For manual acquisition, download every `iclickrickroll-lab-release.zip.partNN`
asset (`part00` through `part11`) from the release. Keep them together with
[ARCHIVE-SHA256SUMS](ARCHIVE-SHA256SUMS), then follow
[ARCHIVE-INSTRUCTIONS.txt](ARCHIVE-INSTRUCTIONS.txt). GitHub's per-asset limit
requires the 21.3 GiB archive to be split; the release page lists all twelve
parts, each below 2 GiB.

## Manual extraction, import, and run

The archive password is `IAcknowledgeMaliciousContent`. It marks a deliberate
extraction step and provides no confidentiality. After acquisition reports a
verified ZIP:

```sh
cd iclickrickroll-download
unzip iclickrickroll-lab-release.zip
cd iclickrickroll-lab
sha256sum -c SHA256SUMS
./import.sh
cd reproducible-lab
make iclickrickroll
```

After emulator preflight passes, type `send-rick` in the C2 pane and press
Enter. The next implant beacon carries the fixed task to start Edge on the
locally served Creative Commons video. `make clean` removes the disposable run
clones.

Typing the command does not make the implant connect immediately. Its beacon
cadence controls when the controller can deliver the task. Watch the controller
pane for the beacon and reply before treating a quiet Windows desktop as a
failure. If the preflight fails, fix the VM configuration; adding an external
adapter would invalidate the isolation on which the result depends.

The guide needs `curl`, `sha256sum`, `unzip`, and `python3`; the harness requires
Linux, X11, VirtualBox 7.1, `make`, and `xorriso`. Keep both VMs on the shipped
single VirtualBox internal network. The emulator has no uplink and forwarding
is disabled. Do not add NAT, bridged, or host-only adapters, and do not mount
the infected disk or live malware ISO on a general-purpose host.

## What is packaged

- A **prepared infected Windows VM folder** with its primed saved-RAM state,
  plus the isolated emulator VM folder. The original sealed forensic and golden
  VMs are not included.
- Two ISOs, local controller and licensed media, harness, warning, provenance,
  and internal file checksums.
- An encrypted ZIP of 22,887,509,030 bytes (~21.31 GiB). The twelve release
  assets are each under 2 GB. The extracted package is about 118.6 GB;
  running it creates disposable clones, so plan disk space accordingly.

I imported the exact packaged baselines into a clean VirtualBox home and ran
all 17 emulator preflight checks. The controller accepted `send-rick` on a
beacon from the resident implant, and Edge opened the local video fullscreen
with audio. The ZIP passed its password/CRC test, and joining the twelve
release parts reproduced its SHA-256.

For independent reconstruction of the analysis from samples and tooling, use
the [source-based reproducibility guide](../docs/reproducibility.md).
