from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
import os
import socket
import struct
import time


ETH_P_ALL = 0x0003
EAPOL_ETHERTYPE = 0x888E

EAPOL_TYPES = {
    0: "eap-packet",
    1: "start",
    2: "logoff",
    3: "key",
    4: "encapsulated-asf-alert",
}

EAP_CODES = {
    1: "request",
    2: "response",
    3: "success",
    4: "failure",
}

EAP_TYPES = {
    1: "identity",
    4: "md5-challenge",
    13: "tls",
    17: "leap",
    21: "ttls",
    25: "peap",
    43: "fast",
    47: "psk",
}

PCAP_MAGIC_TO_ENDIAN = {
    b"\xd4\xc3\xb2\xa1": "<",
    b"\xa1\xb2\xc3\xd4": ">",
    b"\x4d\x3c\xb2\xa1": "<",
    b"\xa1\xb2\x3c\x4d": ">",
}


@dataclass(slots=True)
class ParsedEAPOLFrame:
    src_mac: str
    dst_mac: str
    version: int
    eapol_type: int
    eapol_type_name: str
    eap_code: int | None = None
    eap_code_name: str | None = None
    eap_identifier: int | None = None
    eap_type: int | None = None
    eap_type_name: str | None = None
    identity: str | None = None


@dataclass(slots=True)
class ObservationSummary:
    source_name: str
    duration_seconds: int | None
    source_kind: str = "live-interface"
    frames_total: int = 0
    eapol_types: Counter[str] = field(default_factory=Counter)
    eap_codes: Counter[str] = field(default_factory=Counter)
    eap_types: Counter[str] = field(default_factory=Counter)
    source_macs: set[str] = field(default_factory=set)
    identities: set[str] = field(default_factory=set)

    def add(self, frame: ParsedEAPOLFrame) -> None:
        self.frames_total += 1
        self.eapol_types[frame.eapol_type_name] += 1
        self.source_macs.add(frame.src_mac)
        if frame.eap_code_name is not None:
            self.eap_codes[frame.eap_code_name] += 1
        if frame.eap_type_name is not None:
            self.eap_types[frame.eap_type_name] += 1
        if frame.identity:
            self.identities.add(frame.identity)

    def to_dict(self) -> dict[str, object]:
        return {
            "source_name": self.source_name,
            "source_kind": self.source_kind,
            "iface": self.source_name,
            "duration_seconds": self.duration_seconds,
            "frames_total": self.frames_total,
            "eapol_types": dict(self.eapol_types),
            "eap_codes": dict(self.eap_codes),
            "eap_types": dict(self.eap_types),
            "source_macs": sorted(self.source_macs),
            "identities": sorted(self.identities),
        }


def observe_eapol(iface: str, duration_seconds: int) -> ObservationSummary:
    if os.geteuid() != 0:
        raise PermissionError("live observation requires root privileges")

    summary = ObservationSummary(
        source_name=iface,
        duration_seconds=duration_seconds,
        source_kind="live-interface",
    )
    deadline = time.monotonic() + duration_seconds

    with socket.socket(socket.AF_PACKET, socket.SOCK_RAW, socket.htons(ETH_P_ALL)) as handle:
        handle.bind((iface, 0))
        handle.settimeout(0.5)

        while time.monotonic() < deadline:
            try:
                packet = handle.recv(65535)
            except TimeoutError:
                continue

            frame = parse_eapol_frame(packet)
            if frame is not None:
                summary.add(frame)

    return summary


def analyze_eapol_pcap(path: str | Path) -> ObservationSummary:
    pcap_path = Path(path)
    with pcap_path.open("rb") as handle:
        data = handle.read()

    summary = ObservationSummary(
        source_name=str(pcap_path),
        duration_seconds=None,
        source_kind="pcap-file",
    )
    for packet in iter_pcap_packets(data):
        frame = parse_eapol_frame(packet)
        if frame is not None:
            summary.add(frame)
    return summary


def parse_eapol_frame(packet: bytes) -> ParsedEAPOLFrame | None:
    if len(packet) < 18:
        return None

    ethertype = struct.unpack("!H", packet[12:14])[0]
    if ethertype != EAPOL_ETHERTYPE:
        return None

    src_mac = _format_mac(packet[6:12])
    dst_mac = _format_mac(packet[0:6])
    version = packet[14]
    eapol_type = packet[15]
    payload_len = struct.unpack("!H", packet[16:18])[0]
    payload = packet[18 : 18 + payload_len]

    frame = ParsedEAPOLFrame(
        src_mac=src_mac,
        dst_mac=dst_mac,
        version=version,
        eapol_type=eapol_type,
        eapol_type_name=EAPOL_TYPES.get(eapol_type, f"unknown-{eapol_type}"),
    )

    if eapol_type != 0 or len(payload) < 4:
        return frame

    frame.eap_code = payload[0]
    frame.eap_code_name = EAP_CODES.get(frame.eap_code, f"unknown-{frame.eap_code}")
    frame.eap_identifier = payload[1]
    eap_length = struct.unpack("!H", payload[2:4])[0]

    if frame.eap_code in (1, 2) and len(payload) >= 5:
        frame.eap_type = payload[4]
        frame.eap_type_name = EAP_TYPES.get(frame.eap_type, f"unknown-{frame.eap_type}")

        if frame.eap_code == 2 and frame.eap_type == 1:
            identity_bytes = payload[5:eap_length]
            if identity_bytes:
                frame.identity = identity_bytes.decode("utf-8", errors="replace").strip() or None

    return frame


def render_observation_report(summary: ObservationSummary) -> str:
    lines = [
        "# EAPOL Observation Report",
        "",
        f"- Source kind: `{summary.source_kind}`",
        f"- Source: `{summary.source_name}`",
    ]
    if summary.duration_seconds is not None:
        lines.append(f"- Duration: `{summary.duration_seconds}` seconds")
    lines.extend([
        f"- Frames seen: `{summary.frames_total}`",
        "",
        "## EAPOL Types",
    ])
    if summary.eapol_types:
        for key, value in summary.eapol_types.most_common():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- No EAPOL frames observed")

    lines.extend(["", "## EAP Codes"])
    if summary.eap_codes:
        for key, value in summary.eap_codes.most_common():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- No EAP packet codes observed")

    lines.extend(["", "## EAP Types"])
    if summary.eap_types:
        for key, value in summary.eap_types.most_common():
            lines.append(f"- `{key}`: `{value}`")
    else:
        lines.append("- No typed EAP payloads observed")

    lines.extend(["", "## Source MACs"])
    if summary.source_macs:
        for mac in sorted(summary.source_macs):
            lines.append(f"- `{mac}`")
    else:
        lines.append("- None")

    lines.extend(["", "## Identities"])
    if summary.identities:
        for identity in sorted(summary.identities):
            lines.append(f"- `{identity}`")
    else:
        lines.append("- None")

    return "\n".join(lines)


def _format_mac(value: bytes) -> str:
    return ":".join(f"{octet:02x}" for octet in value)


def iter_pcap_packets(data: bytes) -> list[bytes]:
    if len(data) < 24:
        raise ValueError("pcap file is too small")

    endian = PCAP_MAGIC_TO_ENDIAN.get(data[:4])
    if endian is None:
        raise ValueError("unsupported capture format: only classic pcap is supported")

    _version_major, _version_minor, _thiszone, _sigfigs, _snaplen, network = struct.unpack(
        f"{endian}HHIIII",
        data[4:24],
    )
    if network != 1:
        raise ValueError(f"unsupported datalink type in pcap: {network} (expected Ethernet/1)")

    packets: list[bytes] = []
    offset = 24
    while offset + 16 <= len(data):
        _ts_sec, _ts_usec, incl_len, _orig_len = struct.unpack(
            f"{endian}IIII",
            data[offset : offset + 16],
        )
        offset += 16
        frame_end = offset + incl_len
        if frame_end > len(data):
            raise ValueError("pcap record length exceeds file size")
        packets.append(data[offset:frame_end])
        offset = frame_end
    return packets
