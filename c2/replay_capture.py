#!/usr/bin/env python3
"""Read-only offline capture check; writes no malware-sample data."""
import argparse
import collections
import ipaddress
from pathlib import Path
import sys

from protocol import Field, build_frame, frame_length, parse_frame


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("capture", type=Path)
    parser.add_argument("--helper-dir", type=Path, required=True,
                        help="directory containing summarize_tcp_payloads.py")
    args = parser.parse_args()
    sys.path.insert(0, str(args.helper_dir.resolve()))
    from summarize_tcp_payloads import outbound_tcp, reassemble, records

    capture = args.capture
    flows = collections.defaultdict(list)
    for packet in records(capture):
        item = outbound_tcp(packet, ipaddress.IPv4Address("10.77.86.116"),
                            ipaddress.IPv4Address("45.140.205.28"))
        if item and item[2]:
            flows[item[0]].append((item[1], item[2]))
    checked = 0
    for port, pieces in sorted(flows.items()):
        body, gaps = reassemble(pieces)
        size = frame_length(body)
        frame = parse_frame(body[:size])
        assert not gaps and frame.count == 26
        checked += 1
        print(f"{port}\t{size}\t{len(body)-size}\t{frame.timestamp}"
              f"\t{','.join(hex(f.tag) for f in frame.fields)}")
    assert checked == 26, checked
    candidate = build_frame([Field(1, 0, 0x56BC, b"\x01")])
    parsed = parse_frame(candidate)
    assert [(f.tag, f.data) for f in parsed.fields] == [(0x56BC, b"\x01")]
    print("offline_capture_frames=26 candidate_roundtrip=pass")


if __name__ == "__main__":
    main()
