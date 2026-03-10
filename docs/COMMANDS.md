# Command Reference

This file explains every currently implemented command in `new8021x`.

Important: the current commands are for validation, inventory, and passive observation. They do not perform active 802.1X bypass.

## Global CLI Structure

```bash
new8021x [--config CONFIG] <command> [options]
```

Global options:

- `--config CONFIG`
  - Optional path to a TOML config file.
  - Useful if you want to avoid repeating interface names.

## `doctor`

Purpose:

- Inspect the host and tell you whether the machine looks suitable for a two-NIC awareness/demo appliance.

What it checks:

- whether the process is running as root
- which interfaces exist
- whether at least two physical NICs appear to be present
- whether core tools such as `ip`, `bridge`, and `ethtool` are available
- whether optional tools such as `tcpdump` are available

What it does not do:

- does not modify the system
- does not bring interfaces up or down
- does not capture packets

Example:

```bash
new8021x doctor
new8021x doctor --json
```

When to use it:

- first run on a Raspberry Pi or demo laptop
- after changing adapters or NIC names
- before a conference or workshop

## `interfaces`

Purpose:

- Print a simple interface inventory.

What it shows:

- interface name
- whether the interface looks physical, virtual, or loopback
- operstate
- carrier state if available
- MAC address
- IP addresses currently assigned

What it does not do:

- no packet capture
- no interface changes

Example:

```bash
new8021x interfaces
new8021x interfaces --json
```

When to use it:

- to identify the correct upstream and downstream NIC names
- to confirm a USB Ethernet adapter is visible to the OS

## `init-config`

Purpose:

- Write a starter TOML config file.

What it writes:

- interface role placeholders
- default observation settings
- default reporting directory

Example:

```bash
new8021x init-config
new8021x init-config --path demo-config.toml
```

When to use it:

- once per appliance build
- if you want repeatable command behavior without long flag lists

## `preflight`

Purpose:

- Validate that a selected pair of interfaces makes sense for a two-NIC appliance layout.

What it checks:

- whether the named interfaces exist
- whether upstream and downstream are different
- whether the selected NICs appear to be physical hardware
- optional sidechannel presence

What it does not do:

- does not create a bridge
- does not modify routes
- does not modify firewall state
- does not start packet forwarding

Examples:

```bash
new8021x preflight --upstream eth0 --downstream eth1
new8021x --config config.toml preflight
new8021x preflight --upstream eth0 --downstream eth1 --sidechannel wlan0 --json
```

When to use it:

- right before a live demo
- after swapping USB adapters
- before packaging a Pi image for someone else to use

## `suggest-layout`

Purpose:

- Suggest likely upstream, downstream, and optional sidechannel interfaces for a demo appliance.

What it does:

- looks at currently visible interfaces
- prefers wired physical NICs for upstream/downstream
- prefers a wireless interface for sidechannel if one exists
- returns notes explaining the choice

What it does not do:

- does not claim to be authoritative
- does not modify the system

Examples:

```bash
new8021x suggest-layout
new8021x suggest-layout --json
```

When to use it:

- on a Raspberry Pi with multiple adapters attached
- before writing a config file
- when a non-specialist operator needs a likely starting point

## `observe`

Purpose:

- Passively observe EAPOL / EAP frames on one interface and summarize what was seen.

What it captures:

- EAPOL start/logoff/key packet counts
- EAP request/response/success/failure counts
- observed EAP type names where parsing is possible
- source MAC addresses
- response identities when an EAP Identity response is visible

What it requires:

- root privileges
- a Linux interface that can receive the relevant traffic

What it does not do:

- does not transmit anything
- does not trigger reauthentication
- does not modify bridge state
- does not alter the target environment

Examples:

```bash
sudo new8021x observe --iface eth0 --seconds 15
sudo new8021x observe --iface eth0 --seconds 30 --report reports/session.md
sudo new8021x observe --iface eth0 --seconds 15 --json
```

When to use it:

- in a lab to understand what a client and switch are doing
- in awareness sessions to explain what 802.1X traffic looks like
- during authorized testbed development before adding more advanced lab-only modules

## Current Command Summary

If you need the short version:

- `doctor`: Is this host ready?
- `interfaces`: What NICs do I have?
- `init-config`: Write a starter config.
- `preflight`: Does this NIC selection make sense?
- `suggest-layout`: What role should each NIC probably have?
- `observe`: What 802.1X/EAP traffic is visible right now?
- `observe-loop`: Repeated passive observation for unattended appliance use.
- `analyze-pcap`: Offline EAPOL analysis from a saved classic PCAP file.

## Current Limitations

The CLI is intentionally conservative right now.

It does not yet include:

- automatic role assignment into live commands
- packet forwarding
- TUI or web UI
- active lab-only modules

## `observe-loop`

Purpose:

- Run repeated passive observation windows and save the results.

What it does:

- repeatedly runs the same passive capture logic as `observe`
- writes timestamped Markdown and JSON reports
- is suitable for `systemd`

What it does not do:

- does not transmit packets
- does not create a bridge
- does not perform active 802.1X actions

Examples:

```bash
sudo new8021x observe-loop --iface eth0 --seconds 30 --interval 5 --output-dir reports
sudo new8021x observe-loop --iface eth0 --seconds 15 --interval 0 --output-dir reports --cycles 3
```

## `analyze-pcap`

Purpose:

- Analyze a saved classic Ethernet `.pcap` file offline.

What it does:

- parses classic `pcap`
- extracts EAPOL/EAP frames
- renders the same summary style used by live observation

Current limitation:

- only classic `pcap` is supported
- `pcapng` is not yet supported

Examples:

```bash
new8021x analyze-pcap --file capture.pcap
new8021x analyze-pcap --file capture.pcap --report reports/offline.md
new8021x analyze-pcap --file capture.pcap --json
```
