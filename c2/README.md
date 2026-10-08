# Local controller and reconstructed C2 protocol

The passive capture contains registration messages from the implant and no reply from the attacker's server. Those messages and the client code supplied the frame arithmetic and field descriptors. A lab test then checked whether the client would accept a locally constructed frame. This directory contains the parser, listener, and controller used for that test. The listener and controller emit only frames exercised against the resident implant. No attacker server code or operator response was recovered.

> **Run only inside the isolated lab.** The implant contains a hardcoded C2 address, `45.140.205.28:443` (**LIVE IOC — DO NOT NAVIGATE**). The emulator redirects that address to `10.77.86.2:8443` with `ip_forward=0` and no external route. The tools bind to the lab network and have no upstream or forwarding code. Confirm the network boundary before starting the victim.

## Files

| File | What it is |
|---|---|
| `protocol.py` | the recovered wire protocol: 120-byte arithmetic header (constant `K=0x16df3822a8`), 88-byte field descriptors, XOR field transform, stream framing/validation. Parser + conservative encoder. |
| `server.py` | the interception listener. Binds `10.77.86.2:8443`, rejects peers outside `10.77.86.0/24`, logs every parsed client frame, and can emit only the frames tested in the isolated lab. Modes: `observe` (send nothing), `accept` (one `0x56bc=1` frame), `flag0` (`0x56bc=0`). **No** tasking/payload/endpoint-update response can be selected. |
| `controller.py` | the task controller used for the type-1 shell probe. Sends only fixed, documented frames (accept, task_start, and two fixed benign commands). It does not accept arbitrary commands or URLs. |
| `replay_capture.py` | validates captured client frames against the parser and round-trips the candidate response offline. |
| `verify_probe.py` | reproduces the probe's packet/guest-frame parity and state-transition timing from captures. |
| `protocol-spec.md` | the recovered protocol, documented field by field, with confidence limits. |
| `capability-map.tsv`, `opcode-handler-map.tsv` | the reconstructed capability/handler maps (what each tag/branch does, and how confident we are). |

`replay_capture.py` requires a capture file and `--helper-dir` pointing to a
local directory containing `summarize_tcp_payloads.py`. `verify_probe.py`
expects the first controlled probe's capture and export directory layout. Those raw
captures and the private helper are not part of this source checkout; these
scripts document how the original checks were made.

## What the frames established

Changing `0x56bc` from `01` to `00` changed the live client's close and reconnect timing; changing it back restored the earlier timing. A socket that stays open once can be an accident. The same client changing behavior in both directions after a generated frame was stronger evidence that it had parsed the field. A fixed type-1 task then spawned `cmd.exe` and returned the expected marker and shell PID.

Task types 2–4 and several handler branches are visible in the disassembly. They were not exercised and remain reconstructed behavior. The published controller has no arbitrary-command mode, payload-delivery path, or external endpoint.

## Usage (isolated lab only)

```sh
# observe only (log client frames, send nothing)
python3 server.py --output /path/to/new-unique-dir --response observe

# send one proven acceptance frame per connection
python3 server.py --output /path/to/another-new-dir --response accept
```

`controller.py` drives the fixed type-1 shell probe against an already-resident implant in the isolated guest. It logs each generated frame and client reply. Read [`protocol-spec.md`](protocol-spec.md) before interpreting those logs. The parser's confidence limits and the untested branches matter when extending this code.
