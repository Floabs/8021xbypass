from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from new8021x.appliance import run_observation_loop
from new8021x.config import AppConfig, load_config, write_example_config
from new8021x.eapol import analyze_eapol_pcap, observe_eapol, render_observation_report
from new8021x.env import (
    build_doctor_report,
    interface_by_name,
    list_interfaces,
    render_doctor_report,
    render_interfaces_table,
    render_layout_suggestion,
    suggest_layout,
)
from new8021x.report import write_report


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="new8021x",
        description="Lawful wired 802.1X research and awareness toolkit scaffold",
        epilog="Use 'new8021x <command> --help' for command-specific details.",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Optional TOML config path",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser(
        "doctor",
        help="Show environment readiness",
        description="Inspect the local host and report whether it looks suitable for a two-NIC 802.1X awareness/demo appliance.",
    )
    doctor.add_argument("--json", action="store_true", help="Emit JSON")
    doctor.set_defaults(func=cmd_doctor)

    interfaces = subparsers.add_parser(
        "interfaces",
        help="List local interfaces",
        description="List local interfaces with basic metadata such as link state, MAC address, and whether the NIC appears physical or virtual.",
    )
    interfaces.add_argument("--json", action="store_true", help="Emit JSON")
    interfaces.set_defaults(func=cmd_interfaces)

    init_config = subparsers.add_parser(
        "init-config",
        help="Write an example TOML config",
        description="Write a starter TOML config file that can be edited for a repeatable appliance setup.",
    )
    init_config.add_argument("--path", type=Path, default=Path("config.toml"))
    init_config.set_defaults(func=cmd_init_config)

    preflight = subparsers.add_parser(
        "preflight",
        help="Validate a two-NIC conference/demo layout",
        description="Validate that chosen upstream/downstream interfaces exist and make sense for a two-NIC conference or awareness appliance. This command does not modify networking.",
    )
    preflight.add_argument("--upstream", help="Upstream NIC")
    preflight.add_argument("--downstream", help="Downstream NIC")
    preflight.add_argument("--sidechannel", help="Optional management sidechannel NIC")
    preflight.add_argument("--json", action="store_true", help="Emit JSON")
    preflight.set_defaults(func=cmd_preflight)

    suggest = subparsers.add_parser(
        "suggest-layout",
        help="Suggest upstream/downstream/sidechannel interfaces",
        description="Suggest a likely upstream/downstream/sidechannel role layout using simple heuristics for a Raspberry Pi or demo appliance.",
    )
    suggest.add_argument("--json", action="store_true", help="Emit JSON")
    suggest.set_defaults(func=cmd_suggest_layout)

    observe = subparsers.add_parser(
        "observe",
        help="Passively summarize EAPOL traffic on one NIC",
        description="Passively listen for EAPOL / EAP frames on one interface and summarize what was observed. This command requires root and does not transmit packets.",
    )
    observe.add_argument("--iface", help="Interface to observe")
    observe.add_argument("--seconds", type=int, help="Observation window in seconds")
    observe.add_argument("--json", action="store_true", help="Emit JSON")
    observe.add_argument("--report", help="Optional Markdown report output path")
    observe.set_defaults(func=cmd_observe)

    observe_loop = subparsers.add_parser(
        "observe-loop",
        help="Run repeated passive observation windows",
        description="Run repeated passive observation windows and write timestamped Markdown and JSON reports. Designed for systemd or unattended appliance use.",
    )
    observe_loop.add_argument("--iface", help="Interface to observe")
    observe_loop.add_argument("--seconds", type=int, help="Length of each observation window")
    observe_loop.add_argument("--interval", type=int, help="Pause between windows in seconds")
    observe_loop.add_argument("--output-dir", help="Directory for Markdown and JSON reports")
    observe_loop.add_argument("--cycles", type=int, help="Optional number of windows before exiting")
    observe_loop.set_defaults(func=cmd_observe_loop)

    analyze_pcap = subparsers.add_parser(
        "analyze-pcap",
        help="Analyze a classic PCAP file offline",
        description="Analyze a classic Ethernet PCAP file offline and summarize any EAPOL / EAP frames found inside it.",
    )
    analyze_pcap.add_argument("--file", required=True, help="Path to a classic .pcap capture file")
    analyze_pcap.add_argument("--json", action="store_true", help="Emit JSON")
    analyze_pcap.add_argument("--report", help="Optional Markdown report output path")
    analyze_pcap.set_defaults(func=cmd_analyze_pcap)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        config = load_config(args.config)
        return args.func(args, config)
    except KeyboardInterrupt:
        print("interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


def cmd_doctor(args: argparse.Namespace, _: AppConfig) -> int:
    report = build_doctor_report()
    if args.json:
        print(json.dumps(report.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_doctor_report(report))
    return 0


def cmd_interfaces(args: argparse.Namespace, _: AppConfig) -> int:
    interfaces = list_interfaces()
    if args.json:
        print(json.dumps([iface.to_dict() for iface in interfaces], indent=2, sort_keys=True))
    else:
        print(render_interfaces_table(interfaces))
    return 0


def cmd_init_config(args: argparse.Namespace, _: AppConfig) -> int:
    path = write_example_config(args.path)
    print(f"wrote example config to {path}")
    return 0


def cmd_preflight(args: argparse.Namespace, config: AppConfig) -> int:
    upstream = args.upstream or config.interfaces.upstream
    downstream = args.downstream or config.interfaces.downstream
    sidechannel = args.sidechannel or config.interfaces.sidechannel

    if not upstream or not downstream:
        raise ValueError("preflight requires --upstream and --downstream, or those values in config")
    if upstream == downstream:
        raise ValueError("upstream and downstream must be different interfaces")

    result = {
        "upstream": _describe_selected_interface(upstream),
        "downstream": _describe_selected_interface(downstream),
        "sidechannel": _describe_selected_interface(sidechannel) if sidechannel else None,
        "warnings": [],
    }

    if result["upstream"]["exists"] and not result["upstream"]["is_physical"]:
        result["warnings"].append("upstream interface is not detected as physical hardware")
    if result["downstream"]["exists"] and not result["downstream"]["is_physical"]:
        result["warnings"].append("downstream interface is not detected as physical hardware")
    if sidechannel and result["sidechannel"] and not result["sidechannel"]["exists"]:
        result["warnings"].append("sidechannel interface does not exist")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("# Preflight")
        print("")
        print(f"- Upstream: `{upstream}`")
        print(f"- Downstream: `{downstream}`")
        if sidechannel:
            print(f"- Sidechannel: `{sidechannel}`")
        print("")
        for label in ("upstream", "downstream", "sidechannel"):
            data = result.get(label)
            if not data:
                continue
            print(f"## {label.capitalize()}")
            for key, value in data.items():
                print(f"- {key}: `{value}`")
            print("")
        if result["warnings"]:
            print("## Warnings")
            for warning in result["warnings"]:
                print(f"- {warning}")
        else:
            print("## Warnings")
            print("- None")
    return 0


def cmd_suggest_layout(args: argparse.Namespace, _: AppConfig) -> int:
    suggestion = suggest_layout()
    if args.json:
        print(json.dumps(suggestion.to_dict(), indent=2, sort_keys=True))
    else:
        print(render_layout_suggestion(suggestion))
    return 0


def cmd_observe(args: argparse.Namespace, config: AppConfig) -> int:
    iface = args.iface or config.observe.default_iface
    duration = args.seconds or config.observe.duration_seconds
    if not iface:
        raise ValueError("observe requires --iface or observe.default_iface in config")
    if duration <= 0:
        raise ValueError("observation duration must be positive")

    summary = observe_eapol(iface=iface, duration_seconds=duration)

    if args.json:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    else:
        text = render_observation_report(summary)
        print(text)

    if args.report:
        report_path = write_report(args.report, render_observation_report(summary))
        print(f"report written to {report_path}", file=sys.stderr)

    return 0


def cmd_observe_loop(args: argparse.Namespace, config: AppConfig) -> int:
    iface = args.iface or config.observe.default_iface
    duration = args.seconds or config.observe.duration_seconds
    interval = args.interval if args.interval is not None else config.observe.loop_interval_seconds
    output_dir = args.output_dir or config.reporting.report_dir

    if not iface:
        raise ValueError("observe-loop requires --iface or observe.default_iface in config")
    if args.cycles is not None and args.cycles <= 0:
        raise ValueError("cycles must be positive when provided")

    run_observation_loop(
        iface=iface,
        window_seconds=duration,
        interval_seconds=interval,
        output_dir=output_dir,
        cycles=args.cycles,
    )
    return 0


def cmd_analyze_pcap(args: argparse.Namespace, _: AppConfig) -> int:
    summary = analyze_eapol_pcap(args.file)

    if args.json:
        print(json.dumps(summary.to_dict(), indent=2, sort_keys=True))
    else:
        text = render_observation_report(summary)
        print(text)

    if args.report:
        report_path = write_report(args.report, render_observation_report(summary))
        print(f"report written to {report_path}", file=sys.stderr)

    return 0


def _describe_selected_interface(name: str | None) -> dict[str, object]:
    if not name:
        return {"exists": False}
    iface = interface_by_name(name)
    if iface is None:
        return {
            "exists": False,
            "name": name,
        }
    return {
        "exists": True,
        "name": iface.name,
        "is_physical": iface.is_physical,
        "is_wireless": iface.is_wireless,
        "operstate": iface.operstate,
        "carrier": iface.carrier,
        "mac_address": iface.mac_address,
        "addresses": iface.addresses,
    }
