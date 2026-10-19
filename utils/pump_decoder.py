"""
Better pump.fun Create / CreateEvent decoder.

Program: 6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P

Supports create, create_v2, and CreateEvent discriminators.
Parses name, symbol, uri, mint, bonding_curve, creator from Program data logs.
"""

from __future__ import annotations
import base64
import struct
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from solders.pubkey import Pubkey

CREATE_DISC = bytes([24, 30, 200, 40, 5, 28, 7, 119])
CREATE_V2_DISC = bytes([214, 144, 76, 236, 95, 139, 49, 180])
CREATE_EVENT_DISC = bytes([27, 114, 169, 77, 222, 235, 99, 118])

PUMP_PROGRAM = "6EF8rrecthR5Dkzon8Nwu78hRvfCKubJ14M5uBEwF6P"


@dataclass
class PumpCreate:
    name: str = ""
    symbol: str = ""
    uri: str = ""
    mint: Optional[str] = None
    bonding_curve: Optional[str] = None
    creator: Optional[str] = None
    signature: Optional[str] = None
    raw_logs: List[str] = field(default_factory=list)
    source: str = "unknown"


def _read_borsh_string(data: bytes, offset: int) -> Tuple[str, int]:
    if offset + 4 > len(data):
        return "", offset
    length = struct.unpack_from("<I", data, offset)[0]
    offset += 4
    if length > 1024 or offset + length > len(data):
        return "", offset
    s = data[offset : offset + length].decode("utf-8", errors="replace")
    return s, offset + length


def _read_pubkey(data: bytes, offset: int) -> Tuple[Optional[str], int]:
    if offset + 32 > len(data):
        return None, offset
    try:
        pk = str(Pubkey.from_bytes(data[offset : offset + 32]))
        return pk, offset + 32
    except Exception:
        return None, offset + 32


def decode_create_args(data: bytes) -> Optional[PumpCreate]:
    if len(data) < 8:
        return None
    disc = data[:8]
    if disc not in (CREATE_DISC, CREATE_V2_DISC):
        return None
    offset = 8
    name, offset = _read_borsh_string(data, offset)
    symbol, offset = _read_borsh_string(data, offset)
    uri, offset = _read_borsh_string(data, offset)
    creator, offset = _read_pubkey(data, offset)
    return PumpCreate(name=name, symbol=symbol, uri=uri, creator=creator, source="instruction")


def decode_create_event(data: bytes) -> Optional[PumpCreate]:
    if len(data) < 8:
        return None
    if data[:8] == CREATE_EVENT_DISC:
        data = data[8:]
    elif len(data) > 8 and data[8:16] == CREATE_EVENT_DISC:
        data = data[16:]
    offset = 0
    name, offset = _read_borsh_string(data, offset)
    symbol, offset = _read_borsh_string(data, offset)
    uri, offset = _read_borsh_string(data, offset)
    mint, offset = _read_pubkey(data, offset)
    bonding_curve, offset = _read_pubkey(data, offset)
    creator, offset = _read_pubkey(data, offset)
    if not name and not symbol and not mint:
        return None
    return PumpCreate(
        name=name, symbol=symbol, uri=uri, mint=mint,
        bonding_curve=bonding_curve, creator=creator, source="event",
    )


def extract_program_data_from_logs(logs: List[str]) -> List[bytes]:
    payloads = []
    for line in logs:
        if "Program data:" in line:
            try:
                b64 = line.split("Program data:")[-1].strip()
                payloads.append(base64.b64decode(b64))
            except Exception:
                continue
    return payloads


def decode_from_logs(logs: List[str], signature: Optional[str] = None) -> Optional[PumpCreate]:
    for payload in extract_program_data_from_logs(logs):
        evt = decode_create_event(payload)
        if evt and (evt.name or evt.mint):
            evt.signature = signature
            evt.raw_logs = logs
            return evt
        ix = decode_create_args(payload)
        if ix and (ix.name or ix.symbol):
            ix.signature = signature
            ix.raw_logs = logs
            return ix
    text = " ".join(logs)
    if "Instruction: Create" in text or "Create" in text:
        return PumpCreate(signature=signature, raw_logs=logs, source="heuristic")
    return None


def is_create_log(logs: List[str]) -> bool:
    text = " ".join(logs)
    return "Instruction: Create" in text or any("Program data:" in l for l in logs)
