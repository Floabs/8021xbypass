from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import os
import shutil
import subprocess


CORE_TOOLS = ("ip", "bridge", "ethtool")
OPTIONAL_TOOLS = ("tcpdump", "nmcli", "wpa_supplicant", "macchanger", "iptables", "ebtables")


@dataclass(slots=True)
class InterfaceInfo:
    name: str
    mac_address: str
    mtu: int | None
    operstate: str
    carrier: int | None
    is_up: bool
    is_loopback: bool
    is_physical: bool
    is_wireless: bool
    addresses: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class ToolStatus:
    name: str
    available: bool
    path: str | None

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class DoctorReport:
    root: bool
    interfaces: list[InterfaceInfo]
    core_tools: list[ToolStatus]
    optional_tools: list[ToolStatus]
    warnings: list[str]

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "interfaces": [iface.to_dict() for iface in self.interfaces],
            "core_tools": [tool.to_dict() for tool in self.core_tools],
            "optional_tools": [tool.to_dict() for tool in self.optional_tools],
            "warnings": self.warnings,
        }


@dataclass(slots=True)
class LayoutSuggestion:
    upstream: str | None
    downstream: str | None
    sidechannel: str | None
    confidence: str
    notes: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def build_doctor_report() -> DoctorReport:
    interfaces = list_interfaces()
    core_tools = [tool_status(name) for name in CORE_TOOLS]
    optional_tools = [tool_status(name) for name in OPTIONAL_TOOLS]

    warnings: list[str] = []
    physical = [iface for iface in interfaces if iface.is_physical and not iface.is_loopback]
    if len(physical) < 2:
        warnings.append("fewer than two physical NICs detected; a two-port demo appliance will need more hardware")
    if not all(tool.available for tool in core_tools):
        warnings.append("one or more core tooling prerequisites are missing")
    if os.geteuid() != 0:
        warnings.append("not running as root; live packet observation will not work")

    return DoctorReport(
        root=os.geteuid() == 0,
        interfaces=interfaces,
        core_tools=core_tools,
        optional_tools=optional_tools,
        warnings=warnings,
    )


def list_interfaces() -> list[InterfaceInfo]:
    ip_map = _ip_address_map()
    result: list[InterfaceInfo] = []
    for name in sorted(os.listdir("/sys/class/net")):
        base = Path("/sys/class/net") / name
        result.append(
            InterfaceInfo(
                name=name,
                mac_address=_read_text(base / "address", "00:00:00:00:00:00"),
                mtu=_read_int(base / "mtu"),
                operstate=_read_text(base / "operstate", "unknown"),
                carrier=_read_int(base / "carrier"),
                is_up=_read_text(base / "operstate", "unknown") == "up",
                is_loopback=name == "lo",
                is_physical=(base / "device").exists(),
                is_wireless=(base / "wireless").exists(),
                addresses=ip_map.get(name, []),
            )
        )
    return result


def interface_by_name(name: str) -> InterfaceInfo | None:
    for iface in list_interfaces():
        if iface.name == name:
            return iface
    return None


def suggest_layout() -> LayoutSuggestion:
    return suggest_layout_from_interfaces(list_interfaces())


def suggest_layout_from_interfaces(interfaces: list[InterfaceInfo]) -> LayoutSuggestion:
    notes: list[str] = []
    wired = [iface for iface in interfaces if iface.is_physical and not iface.is_wireless and not iface.is_loopback]
    wireless = [iface for iface in interfaces if iface.is_wireless]

    upstream = _pick_upstream(wired)
    downstream = _pick_downstream(wired, upstream)
    sidechannel = wireless[0].name if wireless else None

    if upstream:
        notes.append(f"selected `{upstream}` as upstream because it is the best wired candidate with current link heuristics")
    else:
        notes.append("no wired upstream candidate was found")

    if downstream:
        notes.append(f"selected `{downstream}` as downstream as the remaining wired candidate")
    else:
        notes.append("no second wired candidate was found for downstream")

    if sidechannel:
        notes.append(f"selected `{sidechannel}` as sidechannel because it appears to be a wireless interface")
    else:
        notes.append("no wireless sidechannel candidate was found")

    upstream_iface = next((iface for iface in interfaces if iface.name == upstream), None)

    if upstream and downstream:
        confidence = "medium"
        if upstream_iface and upstream_iface.carrier == 1:
            confidence = "medium-high"
    else:
        confidence = "low"

    return LayoutSuggestion(
        upstream=upstream,
        downstream=downstream,
        sidechannel=sidechannel,
        confidence=confidence,
        notes=notes,
    )


def tool_status(name: str) -> ToolStatus:
    path = shutil.which(name)
    return ToolStatus(name=name, available=path is not None, path=path)


def render_interfaces_table(interfaces: list[InterfaceInfo]) -> str:
    rows = [
        ("name", "kind", "state", "carrier", "mac", "addresses"),
    ]
    for iface in interfaces:
        kind = "loopback" if iface.is_loopback else "physical" if iface.is_physical else "virtual"
        carrier = "-" if iface.carrier is None else str(iface.carrier)
        addresses = ",".join(iface.addresses) if iface.addresses else "-"
        rows.append((iface.name, kind, iface.operstate, carrier, iface.mac_address, addresses))

    widths = [max(len(row[idx]) for row in rows) for idx in range(len(rows[0]))]
    lines = []
    for index, row in enumerate(rows):
        line = "  ".join(value.ljust(widths[col]) for col, value in enumerate(row))
        lines.append(line)
        if index == 0:
            lines.append("  ".join("-" * width for width in widths))
    return "\n".join(lines)


def render_doctor_report(report: DoctorReport) -> str:
    lines = [
        f"root: {'yes' if report.root else 'no'}",
        "",
        "interfaces:",
        render_interfaces_table(report.interfaces),
        "",
        "core tools:",
    ]
    for tool in report.core_tools:
        lines.append(f"- {tool.name}: {'ok' if tool.available else 'missing'}{_tool_suffix(tool.path)}")
    lines.append("")
    lines.append("optional tools:")
    for tool in report.optional_tools:
        lines.append(f"- {tool.name}: {'ok' if tool.available else 'missing'}{_tool_suffix(tool.path)}")
    if report.warnings:
        lines.append("")
        lines.append("warnings:")
        for warning in report.warnings:
            lines.append(f"- {warning}")
    return "\n".join(lines)


def render_layout_suggestion(suggestion: LayoutSuggestion) -> str:
    lines = [
        "# Suggested Layout",
        "",
        f"- Upstream: `{suggestion.upstream or ''}`",
        f"- Downstream: `{suggestion.downstream or ''}`",
        f"- Sidechannel: `{suggestion.sidechannel or ''}`",
        f"- Confidence: `{suggestion.confidence}`",
        "",
        "## Notes",
    ]
    for note in suggestion.notes:
        lines.append(f"- {note}")
    return "\n".join(lines)


def to_json(data: object) -> str:
    return json.dumps(data, indent=2, sort_keys=True)


def _tool_suffix(path: str | None) -> str:
    return f" ({path})" if path else ""


def _read_text(path: Path, default: str) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return default


def _read_int(path: Path) -> int | None:
    try:
        return int(path.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None


def _ip_address_map() -> dict[str, list[str]]:
    if shutil.which("ip") is None:
        return {}

    completed = subprocess.run(
        ["ip", "-j", "addr", "show"],
        check=False,
        capture_output=True,
        text=True,
    )
    if completed.returncode != 0:
        return {}

    try:
        raw = json.loads(completed.stdout)
    except json.JSONDecodeError:
        return {}

    mapping: dict[str, list[str]] = {}
    for item in raw:
        addresses: list[str] = []
        for address in item.get("addr_info", []):
            local = address.get("local")
            prefix = address.get("prefixlen")
            if local is not None and prefix is not None:
                addresses.append(f"{local}/{prefix}")
        mapping[item["ifname"]] = addresses
    return mapping


def _pick_upstream(wired: list[InterfaceInfo]) -> str | None:
    if not wired:
        return None

    ranked = sorted(
        wired,
        key=lambda iface: (
            0 if iface.carrier == 1 else 1,
            0 if iface.is_up else 1,
            0 if iface.name.startswith("eth") else 1,
            0 if iface.name.startswith("enp") else 1,
            iface.name,
        ),
    )
    return ranked[0].name


def _pick_downstream(wired: list[InterfaceInfo], upstream: str | None) -> str | None:
    remaining = [iface for iface in wired if iface.name != upstream]
    if not remaining:
        return None

    ranked = sorted(
        remaining,
        key=lambda iface: (
            0 if iface.carrier == 0 else 1,
            0 if iface.name.startswith("enx") else 1,
            0 if iface.name.startswith("usb") else 1,
            iface.name,
        ),
    )
    return ranked[0].name
