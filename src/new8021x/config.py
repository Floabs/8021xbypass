from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import tomllib


@dataclass(slots=True)
class InterfaceRoles:
    upstream: str | None = None
    downstream: str | None = None
    sidechannel: str | None = None


@dataclass(slots=True)
class ObserveSettings:
    default_iface: str | None = None
    duration_seconds: int = 15
    loop_interval_seconds: int = 5


@dataclass(slots=True)
class ReportingSettings:
    report_dir: str = "reports"


@dataclass(slots=True)
class AppConfig:
    profile_name: str = "default"
    interfaces: InterfaceRoles = field(default_factory=InterfaceRoles)
    observe: ObserveSettings = field(default_factory=ObserveSettings)
    reporting: ReportingSettings = field(default_factory=ReportingSettings)


def load_config(path: str | Path | None) -> AppConfig:
    if path is None:
        return AppConfig()

    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"config file not found: {config_path}")

    with config_path.open("rb") as handle:
        raw = tomllib.load(handle)

    interfaces = raw.get("interfaces", {})
    observe = raw.get("observe", {})
    reporting = raw.get("reporting", {})

    return AppConfig(
        profile_name=raw.get("profile_name", "default"),
        interfaces=InterfaceRoles(
            upstream=_clean_text(interfaces.get("upstream")),
            downstream=_clean_text(interfaces.get("downstream")),
            sidechannel=_clean_text(interfaces.get("sidechannel")),
        ),
        observe=ObserveSettings(
            default_iface=_clean_text(observe.get("default_iface")),
            duration_seconds=int(observe.get("duration_seconds", 15)),
            loop_interval_seconds=int(observe.get("loop_interval_seconds", 5)),
        ),
        reporting=ReportingSettings(
            report_dir=str(reporting.get("report_dir", "reports")),
        ),
    )


def write_example_config(path: str | Path) -> Path:
    output_path = Path(path)
    output_path.write_text(
        """profile_name = "conference-kit"

[interfaces]
upstream = "eth0"
downstream = "eth1"
sidechannel = ""

[observe]
default_iface = "eth0"
duration_seconds = 15
loop_interval_seconds = 5

[reporting]
report_dir = "reports"
""",
        encoding="utf-8",
    )
    return output_path


def _clean_text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None
