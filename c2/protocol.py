"""Conservative decoder/encoder for the recovered record-1118 native framing.

Only the arithmetic and XOR layer proven by disassembly/captures are implemented.
The optional per-field integrity mode is deliberately unsupported for generation.
"""
from __future__ import annotations

from dataclasses import dataclass
import struct
import time

K = 0x16DF3822A8
MASK = (1 << 64) - 1
HEADER = 120
DESCRIPTOR = 88
MAX_FRAME = 1 << 20
MAX_FIELDS = 1024


class FrameError(ValueError):
    pass


def _words(data: bytes, offset: int, count: int) -> tuple[int, ...]:
    return struct.unpack_from("<" + "Q" * count, data, offset)


def _pack(values) -> bytes:
    return struct.pack("<" + "Q" * len(values), *(v & MASK for v in values))


def _xor_key(raw_key: int) -> int:
    return (3 * raw_key + 7 if 4 <= raw_key <= 39 else raw_key) & 0xFF


@dataclass(frozen=True)
class Field:
    id: int
    parent: int
    tag: int
    data: bytes
    flag_a: bool = False
    byte_a: int = 0
    flag_xor: bool = True
    xor_key: int = 0x51
    flag_integrity: bool = False
    integrity_byte: int = 0
    seed: int = 0
    raw_data: bytes = b""


@dataclass(frozen=True)
class Frame:
    version: int
    status: int
    timestamp: int
    opaque_0: int
    opaque_1: int
    count: int
    total: int
    fields: tuple[Field, ...]
    raw: bytes


def frame_length(data: bytes) -> int | None:
    if len(data) < HEADER:
        return None
    q = _words(data, 0, 15)
    if q[1] != (7 * q[0] + 3 * K) & MASK:
        raise FrameError("header relation q1")
    if q[5] != (q[1] - 37 * (q[0] + K)) & MASK:
        raise FrameError("header relation q5")
    if q[6] != ((q[5] + 1) * (q[0] + K + 1)) & MASK:
        raise FrameError("header relation q6")
    n = (q[12] - K * q[11] - q[10]) & MASK
    n2 = (q[13] - K * q[10] + q[11]) & MASK
    if n > MAX_FIELDS or n2 > n:
        raise FrameError("field count")
    base = HEADER + DESCRIPTOR * n
    if base > MAX_FRAME:
        raise FrameError("descriptor table too large")
    if len(data) < base:
        return None
    total = base
    for i in range(n):
        d = _words(data, HEADER + DESCRIPTOR * i, 11)
        length = (d[4] - K - 7 * d[0]) & MASK
        total += length
        if total > MAX_FRAME:
            raise FrameError("frame too large")
    declared = (q[14] - K * (q[10] + q[11])) & MASK
    if declared != total:
        raise FrameError(f"declared length {declared} != {total}")
    return total


def parse_frame(data: bytes) -> Frame:
    size = frame_length(data)
    if size is None or len(data) != size:
        raise FrameError("incomplete frame or trailing bytes")
    q = _words(data, 0, 15)
    version = (q[2] - K + q[0] * q[1] - q[5]) & 0xFFFF
    status = (q[3] - K - q[0] * q[1] - q[5]) & 0xFFFF
    timestamp = (q[4] - K - q[0] * q[1] - q[5]) & MASK
    if version != 1:
        raise FrameError(f"unsupported version {version}")
    n = (q[12] - K * q[11] - q[10]) & MASK
    cursor = HEADER + DESCRIPTOR * n
    fields = []
    for i in range(n):
        d = _words(data, HEADER + DESCRIPTOR * i, 11)
        s = d[0]
        length = (d[4] - K - 7 * s) & MASK
        raw = data[cursor:cursor + length]
        cursor += length
        flag_xor = bool((d[7] - 3 * K + 3 * s) & MASK)
        key = (d[8] - K * s + 4 * s) & 0xFF
        decoded = bytes(b ^ _xor_key(key) for b in raw) if flag_xor else raw
        fields.append(Field(
            id=(d[1] - K * s - s) & MASK,
            parent=(d[2] - K + 3 * s) & MASK,
            tag=(d[3] - K * (s + 5) + 2 * s) & MASK,
            data=decoded,
            flag_a=bool((d[5] - 2 * K + 2 * s) & MASK),
            byte_a=(d[6] - K + 4 * s) & 0xFF,
            flag_xor=flag_xor,
            xor_key=key,
            flag_integrity=bool((d[9] - 5 * K + s) & MASK),
            integrity_byte=(d[10] - K + 5 * s) & 0xFF,
            seed=s,
            raw_data=raw,
        ))
    return Frame(version, status, timestamp, (q[8] - K * q[7]) & MASK,
                 q[9], n, size, tuple(fields), data)


def build_frame(fields: list[Field], *, timestamp: int | None = None,
                opaque_0: int = 0, opaque_1: int = 0, status: int = 0,
                seed: int = 0x12345678) -> bytes:
    if len(fields) > MAX_FIELDS:
        raise FrameError("too many fields")
    descriptors, values = [], []
    for i, field in enumerate(fields):
        if field.flag_integrity:
            raise FrameError("integrity-bearing fields cannot be generated")
        s = field.seed or (seed + i * 0x101)
        value = (bytes(b ^ _xor_key(field.xor_key) for b in field.data)
                 if field.flag_xor else field.data)
        d = [s, K * s + s + field.id, K - 3 * s + field.parent,
             K * (s + 5) - 2 * s + field.tag, K + 7 * s + len(value),
             2 * K - 2 * s + int(field.flag_a), K - 4 * s + field.byte_a,
             3 * K - 3 * s + int(field.flag_xor),
             K * s - 4 * s + field.xor_key, 5 * K - s,
             K - 5 * s + field.integrity_byte]
        descriptors.append(_pack(d))
        values.append(value)
    total = HEADER + DESCRIPTOR * len(fields) + sum(map(len, values))
    if total > MAX_FRAME:
        raise FrameError("frame too large")
    q0, q7, q10, q11 = seed, seed + 1, seed + 2, seed + 3
    q1 = 7 * q0 + 3 * K
    q5 = q1 - 37 * (q0 + K)
    q6 = (q5 + 1) * (q0 + K + 1)
    base = K + q0 * q1 + q5
    q = [q0, q1, K - q0 * q1 + q5 + 1, base + status,
         base + (int(time.time()) if timestamp is None else timestamp), q5, q6,
         q7, K * q7 + opaque_0, opaque_1, q10, q11,
         K * q11 + q10 + len(fields), K * q10 - q11 + len(fields),
         K * (q10 + q11) + total]
    return _pack(q) + b"".join(descriptors) + b"".join(values)


class StreamDecoder:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, chunk: bytes) -> list[Frame]:
        self.buffer.extend(chunk)
        if len(self.buffer) > MAX_FRAME:
            raise FrameError("receive buffer too large")
        out = []
        while True:
            length = frame_length(self.buffer)
            if length is None or len(self.buffer) < length:
                return out
            raw = bytes(self.buffer[:length])
            del self.buffer[:length]
            out.append(parse_frame(raw))
