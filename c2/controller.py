#!/usr/bin/env python3
"""Fixed-command tasking probe for the isolated record-1118 client."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import socket
import struct
import time

from protocol import Field, FrameError, StreamDecoder, build_frame, parse_frame

LAB_IP = "10.77.86.2"
LAB_NET = ipaddress.ip_network("10.77.86.0/24")
TASK_ID = 0x5249434B
COMMANDS = (
    "echo CFX_RICKROLL_TASK_PROOF",
    'start "" msedge.exe http://10.77.86.2:8080/',
)


def stamp() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def qword(value: int) -> bytes:
    return struct.pack("<Q", value)


def candidate_frames() -> tuple[tuple[str, bytes], ...]:
    common = [Field(1, 0, 0x5601, qword(TASK_ID), byte_a=0xF9),
              Field(2, 0, 0x5952, b"", flag_a=True, byte_a=0x95),
              Field(3, 2, 0x5974, qword(1), byte_a=0xF9)]
    responses = [("accept", build_frame([Field(1, 0, 0x56BC, b"\x01")]))]
    responses.append(("task_start", build_frame(common +
                       [Field(4, 2, 0x597E, b"\x01")])))
    for index, command in enumerate(COMMANDS, 1):
        responses.append((f"command_{index}", build_frame(common +
                           [Field(4, 2, 0x5980, command.encode("utf-16le"),
                                  byte_a=0x3F)])))
    for _, raw in responses:
        assert parse_frame(raw).raw == raw
    return tuple(responses)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    frames = candidate_frames()
    with (args.output / "events.jsonl").open("x") as log:
        def emit(**data):
            record = {"utc": stamp(), **data}
            log.write(json.dumps(record, sort_keys=True) + "\n")
            log.flush()
            print(json.dumps(record, sort_keys=True), flush=True)

        for label, raw in frames:
            name = label + ".bin"
            (args.output / name).write_bytes(raw)
            emit(event="candidate", label=label, file=name, size=len(raw),
                 sha256=hashlib.sha256(raw).hexdigest())
        if args.dry_run:
            emit(event="dry_run_complete")
            return

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener:
            listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind((LAB_IP, 8443))
            listener.listen(4)
            emit(event="listening", bind=LAB_IP, port=8443)
            conn, peer = listener.accept()
            if ipaddress.ip_address(peer[0]) not in LAB_NET:
                emit(event="rejected_peer", peer=peer)
                conn.close()
                return
            with conn:
                emit(event="connected", peer=peer)
                conn.settimeout(60)
                decoder = StreamDecoder()
                sent = False
                rx_no = 0
                deadline = time.monotonic() + 90
                while time.monotonic() < deadline:
                    try:
                        data = conn.recv(8192)
                    except socket.timeout:
                        emit(event="timeout")
                        break
                    if not data:
                        emit(event="closed", residual=len(decoder.buffer))
                        break
                    try:
                        parsed = decoder.feed(data)
                    except FrameError as exc:
                        emit(event="parse_error", error=str(exc))
                        break
                    for frame in parsed:
                        rx_no += 1
                        name = f"rx{rx_no:04d}.bin"
                        (args.output / name).write_bytes(frame.raw)
                        tags = [f"0x{field.tag:x}" for field in frame.fields]
                        emit(event="frame_rx", file=name, tags=tags,
                             sha256=hashlib.sha256(frame.raw).hexdigest())
                        if sent or 0x56B8 not in [field.tag for field in frame.fields]:
                            continue
                        for index, (label, raw) in enumerate(frames):
                            if index:
                                time.sleep(3)
                            conn.sendall(raw)
                            emit(event="frame_tx", label=label, size=len(raw),
                                 sha256=hashlib.sha256(raw).hexdigest())
                        sent = True
                emit(event="complete", sent=sent, rx_frames=rx_no)


if __name__ == "__main__":
    main()
