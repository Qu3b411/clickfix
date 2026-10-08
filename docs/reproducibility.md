# Reproduce the saved chain and isolated task

The sample archives let you check the page, MSI, loader, and protocol findings against saved bytes. The prepared VM release begins later, with the implant already resident; it lets you test the fixed controller task against that saved state. Read [`SAFETY.md`](../SAFETY.md) before opening either. Any execution requires a disposable lab with no path to the internet, LAN, or host.

## Before starting

- An isolated analysis environment with a private internal network, no route to the internet, LAN, or host, and no shared clipboard, folders, or Guest Additions in the victim.
- Static analysis tools suitable for HTML, PowerShell, MSI, PE, and binary records. Choose the tools you trust; the hashes below define the bytes being examined.
- The sample archive password, `IAcknowledgeTheRiskOfExecuting`. It requires a deliberate extraction step and provides no containment.

## 1. Verify the checkout

```sh
# from the repository root
sha256sum -c manifests/SHA256SUMS.txt
```

[`malware/README.md`](../malware/README.md) records both the ZIP hashes and the hashes of the extracted sample bytes. Check both before comparing a decoded result.

## 2. Follow the saved chain without executing it

1. Decode the page's inline layers to recover the clipboard launcher and its three-stage retrieval path.
2. Parse the MSI tables, streams, and CAB content. The `DeElevate64.exe` auto-launch action, `.rsrc` import directory, and side-load chain give the next links in the execution path.
3. Reproduce the `Build.dat` transform with all three changing XOR state registers. The corrected output is valid x64 position-independent code.
4. Decode the `.raw` container using its record-length arithmetic. Record 4 contains the task script; record 1118 contains the stager.

The reconstruction rows in [`malware/README.md`](../malware/README.md) give the expected hashes for decoded outputs. A plausible disassembly is not enough here: if a decoded byte stream differs, the later offsets and behavioral claims may be describing a different program. Resolve the mismatch before going on.

## 3. Dynamic reproduction (isolated lab only)

Build and instrument a disposable Windows guest, verify the network boundary, and take a clean powered-off snapshot before introducing the sample. A local emulator supplies wildcard DNS and simulated HTTP/HTTPS with forwarding disabled and no uplink. Replaying the full chain also requires a local server that returns the exact saved stage bodies.

Detonate from a clone. Leave the de-elevation wrapper's error dialog open if you want to observe persistence; it keeps the process alive for delayed writes at roughly 150 and 875 seconds. Capture packets at both the host and guest, along with Sysmon, Procmon, ETW, and memory dumps. Saved-state resume can shift the guest clock, so join network events by source port and packet order.

## 4. C2 / protocol reproduction (isolated lab only)

The resident implant attempts to reach a live C2 address (**LIVE IOC — DO NOT NAVIGATE**). Redirect that destination inside the emulator to a local sink or controller; do not provide a route to the real endpoint. Parse your own captures using [`c2/protocol-spec.md`](../c2/protocol-spec.md) and the tools in [`c2/`](../c2/). The `server.py` `accept` and `flag0` modes test whether `0x56bc` changes the client's timing in both directions. The fixed task in `controller.py` tests the type-1 shell path by requesting a known marker and checking the reply.

The capture-verification scripts document the first controlled task probe. Their input captures remain private, so that historical check cannot be rerun from this checkout alone.

## 5. Optional prepared lab

The [`iclickrickroll` release](../iclickrickroll/README.md) contains the prepared infected VirtualBox baseline used for the demo, including the victim's primed saved RAM state. The emulator VM, controller, two ISOs, and isolation-checking harness travel with it. The archive is split into encrypted release assets and retains the VM folder format required for saved-state resume.

Download all twelve numbered parts, verify their checksums, reconstruct the ZIP, and follow its `README.md` and `MALWARE-WARNING.txt`. The import registers two baselines; `make iclickrickroll` checks the emulator, creates disposable run clones, and resumes the saved victim. After the controller is ready, type `send-rick` in its pane. The task waits for the implant's next beacon, so the Edge window need not appear immediately. When that beacon arrives, the fixed task opens the locally served Creative Commons video. The lab has no route to the real C2.

## What should match

Decoded-stage hashes should match exactly. Runtime PIDs and timestamps will vary. A rebuilt ZIP can have different archive bytes even when its contained files match; compare its structure and contained-file hashes. The prepared release has a fixed assembled-ZIP hash, and a download of that release must match it exactly.
