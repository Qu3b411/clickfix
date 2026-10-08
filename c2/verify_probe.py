#!/usr/bin/env python3
"""Verify the saved isolated probe against its VirtualBox NIC capture."""
from collections import defaultdict
from datetime import datetime
import hashlib
import ipaddress
import json
from pathlib import Path
import statistics
import struct
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "server"))
from protocol import parse_frame

SOURCE = ipaddress.IPv4Address("10.77.86.116").packed
REMOTE = ipaddress.IPv4Address("45.140.205.28").packed


def packets(path):
    with path.open("rb") as file:
        header = file.read(24)
        if header[:4] != b"\xd4\xc3\xb2\xa1":
            raise ValueError("expected little-endian classic PCAP")
        while block := file.read(16):
            sec, usec, length, _ = struct.unpack("<IIII", block)
            payload = file.read(length)
            if len(payload) != length:
                raise ValueError("truncated PCAP record")
            yield sec + usec / 1e6, payload


def tcp_payload(packet):
    if len(packet) < 54 or packet[12:14] != b"\x08\x00":
        return None
    ip = packet[14:]
    h = (ip[0] & 15) * 4
    if ip[9] != 6:
        return None
    ip = ip[:struct.unpack_from("!H", ip, 2)[0]]
    tcp = ip[h:]
    if len(tcp) < 20:
        return None
    source_port, dest_port, seq = struct.unpack_from("!HHI", tcp)
    th = (tcp[12] >> 4) * 4
    body = tcp[th:]
    if not body:
        return None
    if ip[12:16] == SOURCE and ip[16:20] == REMOTE and dest_port == 443:
        return "rx", source_port, seq, body
    if ip[12:16] == REMOTE and ip[16:20] == SOURCE and source_port == 443:
        return "tx", dest_port, seq, body
    return None


def reassemble(segments):
    pieces = sorted(segments)
    cursor = pieces[0][0]
    chunks = []
    gaps = 0
    for seq, body in pieces:
        if seq > cursor:
            gaps += seq - cursor
            cursor = seq
        overlap = max(0, cursor - seq)
        if overlap < len(body):
            chunks.append(body[overlap:])
            cursor = seq + len(body)
    return b"".join(chunks), gaps


def main(run):
    candidates = sorted((run / "emulator-export").glob("cfx-protocol-*"))
    if len(candidates) != 1:
        raise ValueError("expected one captured protocol export under emulator-export")
    evidence = candidates[0]
    flows = defaultdict(list)
    for timestamp, packet in packets(run / "vbox-emulator.pcap"):
        item = tcp_payload(packet)
        if item:
            direction, port, seq, body = item
            flows[(direction, port)].append((seq, body))
    wire_hashes = {"rx": set(), "tx": set()}
    for (direction, port), parts in flows.items():
        body, gaps = reassemble(parts)
        assert gaps == 0, (direction, port, gaps)
        if direction == "rx" and len(body) == 1:
            continue  # saved-state residual byte before the new probe
        parse_frame(body)
        wire_hashes[direction].add(hashlib.sha256(body).hexdigest())
    guest_hashes = {}
    for direction in ("rx", "tx"):
        files = list(evidence.glob(f"server*/conn*-{direction}*.bin"))
        guest_hashes[direction] = {hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
        assert wire_hashes[direction] == guest_hashes[direction], direction
    rows = []
    for name, folder in (("flag1-initial", "server"), ("observe", "server-observe"),
                         ("flag0", "server-flag0"), ("flag1-confirm", "server-flag1-confirm")):
        events = [json.loads(line) for line in (evidence / folder / "events.jsonl").read_text().splitlines()]
        by_connection = defaultdict(dict)
        for event in events:
            if "connection" in event:
                by_connection[event["connection"]][event["event"]] = event
        for number, event_set in sorted(by_connection.items()):
            if "frame_rx" not in event_set:
                continue
            final = event_set.get("close", event_set.get("idle_timeout"))
            duration = ((datetime.fromisoformat(final["utc"]) -
                         datetime.fromisoformat(event_set["frame_rx"]["utc"])).total_seconds()
                        if final else None)
            rows.append((name, number, event_set["frame_rx"]["utc"],
                         event_set["frame_rx"]["sha256"],
                         event_set.get("candidate_flag_tx", event_set.get("candidate_accept_tx", {})).get("flag", 1 if name.startswith("flag1") else ""),
                         final["event"] if final else "incomplete", duration))
    out = run / "state-transitions.tsv"
    lines = ["phase\tconnection\trequest_utc_emulator\trequest_sha256\tresponse_flag\tend_event\tseconds_from_request"]
    lines += ["\t".join("" if x is None else str(x) for x in row) for row in rows]
    expected = "\n".join(lines) + "\n"
    if out.exists():
        assert out.read_text() == expected, "existing transition table differs"
    else:
        out.write_text(expected)
    print(f"PCAP/guest byte parity: {len(wire_hashes['rx'])} requests, {len(wire_hashes['tx'])} responses")
    for phase in ("flag1-initial", "observe", "flag0", "flag1-confirm"):
        durations = [r[-1] for r in rows if r[0] == phase and r[-1] is not None]
        print(phase, len(durations), "median_seconds", statistics.median(durations))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
