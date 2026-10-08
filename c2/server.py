#!/usr/bin/env python3
"""Isolated, deliberately limited record-1118 interception server.

Run only on the emulator at 10.77.86.2. No proxy or upstream code exists.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import ipaddress
import json
from pathlib import Path
import socket
import struct

from protocol import Field, FrameError, StreamDecoder, build_frame

LAB_IP = "10.77.86.2"
LAB_NET = ipaddress.ip_network("10.77.86.0/24")
ALLOWED_RESPONSE_TAGS = {0x56BC}
TASKING_TAGS = {0x5B90, 0x5608, 0x5953, 0x5952, 0x5BD6, 0x5C4E}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bind", default=LAB_IP)
    ap.add_argument("--port", type=int, default=8443)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--response", choices=["observe", "accept", "flag0"], default="observe")
    args = ap.parse_args()
    if args.bind != LAB_IP:
        ap.error(f"bind must be {LAB_IP}")
    if not 1 <= args.port <= 65535:
        ap.error("invalid port")
    args.output.mkdir(parents=True, exist_ok=False)
    event_path = args.output / "events.jsonl"
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as listener, event_path.open("x") as log:
        listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listener.bind((args.bind, args.port))
        listener.listen(8)

        def emit(**event):
            record = {"utc": now(), **event}
            log.write(json.dumps(record, sort_keys=True) + "\n")
            log.flush()
            print(json.dumps(record, sort_keys=True), flush=True)

        emit(event="listen", bind=args.bind, port=args.port, mode=args.response)
        connection_no = 0
        while True:
            conn, peer = listener.accept()
            connection_no += 1
            if ipaddress.ip_address(peer[0]) not in LAB_NET:
                emit(event="reject_peer", peer=peer)
                conn.close()
                continue
            with conn:
                conn.settimeout(30)
                decoder = StreamDecoder()
                frame_no = 0
                replied = False
                emit(event="connect", connection=connection_no, peer=peer)
                while True:
                    try:
                        chunk = conn.recv(8192)
                    except socket.timeout:
                        emit(event="idle_timeout", connection=connection_no)
                        break
                    if not chunk:
                        emit(event="close", connection=connection_no,
                             residual_bytes=len(decoder.buffer))
                        break
                    try:
                        frames = decoder.feed(chunk)
                    except FrameError as exc:
                        invalid_name = f"conn{connection_no:04d}-invalid.bin"
                        (args.output / invalid_name).write_bytes(decoder.buffer)
                        emit(event="parse_error", connection=connection_no,
                             error=str(exc), buffered_bytes=len(decoder.buffer),
                             file=invalid_name)
                        break
                    for frame in frames:
                        frame_no += 1
                        name = f"conn{connection_no:04d}-rx{frame_no:04d}.bin"
                        (args.output / name).write_bytes(frame.raw)
                        fields = [{"id": f.id, "parent": f.parent,
                                   "tag": f"0x{f.tag:x}", "length": len(f.data),
                                   "sha256": hashlib.sha256(f.data).hexdigest(),
                                   "flag_a": f.flag_a, "flag_xor": f.flag_xor,
                                   "flag_integrity": f.flag_integrity,
                                   "decoded_hex": f.data.hex(),
                                   "preview_hex": f.data[:32].hex()}
                                  for f in frame.fields]
                        tags = {f.tag for f in frame.fields}
                        emit(event="frame_rx", connection=connection_no,
                             number=frame_no, file=name,
                             sha256=hashlib.sha256(frame.raw).hexdigest(),
                             version=frame.version, status=frame.status,
                             timestamp=frame.timestamp,
                             opaque_0=frame.opaque_0, opaque_1=frame.opaque_1,
                             fields=fields)
                        for tag in sorted(tags & TASKING_TAGS):
                            emit(event="unsupported_dangerous_tag", tag=f"0x{tag:x}",
                                 connection=connection_no)
                        if args.response in ("accept", "flag0") and not replied:
                            # Static candidate: ddeb8 sets connection state only when
                            # 0x56bc decodes true. No task container is transmitted.
                            flag = 1 if args.response == "accept" else 0
                            response_fields = [Field(1, 0, 0x56BC, bytes([flag]))]
                            assert {f.tag for f in response_fields} <= ALLOWED_RESPONSE_TAGS
                            response = build_frame(response_fields)
                            try:
                                conn.sendall(response)
                            except OSError as exc:
                                emit(event="send_error", connection=connection_no,
                                     error=str(exc))
                                break
                            tx_name = f"conn{connection_no:04d}-tx0001.bin"
                            (args.output / tx_name).write_bytes(response)
                            emit(event="candidate_flag_tx", flag=flag, connection=connection_no,
                                 file=tx_name, length=len(response),
                                 sha256=hashlib.sha256(response).hexdigest(),
                                 note="static candidate; client acceptance unproven")
                            replied = True


if __name__ == "__main__":
    main()
