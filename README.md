# new8021x

`new8021x` is a clean-room Python 3 scaffold for lawful wired 802.1X research, conference demos, and security awareness labs.

It is intentionally not a bypass tool. The current implementation focuses on:

- two-NIC appliance preflight checks
- passive EAPOL / EAP observation
- interface inventory
- reproducible configuration
- report generation

The architecture is inspired by the operational shape of older projects such as FENRIR and silentbridge, but the runtime here is designed to be modern, explicit, and safe to extend in authorized lab environments.

## Current Status

As of 2026-03-10, this project is a documented, working foundation for:

- host and interface readiness checks
- two-NIC appliance preflight validation
- interface role suggestions
- passive EAPOL / EAP observation
- continuous passive observation loops for unattended use
- offline classic PCAP analysis
- report generation

It is not currently an active 802.1X bypass appliance.

If you are evaluating it for a Raspberry Pi build, read:

- [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md)
- [docs/COMMANDS.md](docs/COMMANDS.md)
- [docs/QUICKSTART.md](docs/QUICKSTART.md)

## Current Commands

- `new8021x doctor`
  - Show host readiness, interface inventory, and optional tooling status.
- `new8021x interfaces`
  - List interfaces with basic role-relevant metadata.
- `new8021x preflight --upstream eth0 --downstream eth1`
  - Validate a two-NIC conference or demo appliance layout without modifying networking.
- `new8021x suggest-layout`
  - Suggest likely upstream, downstream, and sidechannel interfaces.
- `new8021x observe --iface eth0 --seconds 15`
  - Passively observe EAPOL traffic on one interface and summarize what is seen.
- `new8021x observe-loop --iface eth0 --seconds 30 --interval 5 --output-dir reports`
  - Repeatedly observe and write timestamped Markdown and JSON reports.
- `new8021x analyze-pcap --file capture.pcap`
  - Analyze saved classic Ethernet PCAP files offline.
- `new8021x init-config`
  - Write an example `config.toml`.

These commands are implemented now and do work, but they are passive/validation-oriented commands. None of them currently alter network topology, impersonate an authenticator, or perform bypass actions.

## Example

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .

new8021x doctor
new8021x interfaces
new8021x preflight --upstream eth0 --downstream eth1
sudo new8021x observe --iface eth0 --seconds 20 --report reports/observe.md
```

## Documentation

- [docs/COMMANDS.md](docs/COMMANDS.md): command-by-command reference
- [docs/QUICKSTART.md](docs/QUICKSTART.md): first-run guide
- [docs/CURRENT_STATE.md](docs/CURRENT_STATE.md): what is and is not implemented
- [docs/RASPBERRY_PI.md](docs/RASPBERRY_PI.md): Pi deployment and `systemd` guidance
- [ROADMAP.md](ROADMAP.md): build direction and next steps

## Design Notes

- Runtime dependencies are standard library only.
- Live observation uses raw sockets and therefore requires root.
- Interface metadata is read from `/sys/class/net` and `ip -j addr show`.
- EAPOL parsing is implemented locally to avoid fragile runtime dependencies.

## Non-Goals

The scaffold does not implement:

- active 802.1X bypass
- rogue authenticator workflows
- credential harvesting
- packet rewriting to gain unauthorized access

If you need future lab-only modules for an isolated testbed, add them behind explicit profiles and keep them separate from the conference/demo core.
