# Quickstart

This guide is written for users who are comfortable using a terminal but are not already experts in 802.1X tooling.

## 1. Install

From the project directory:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

You can also run directly without installation:

```bash
PYTHONPATH=src python3 -m new8021x doctor
```

## 2. Check the Host

Run:

```bash
new8021x doctor
```

What you want to see:

- the expected NICs are listed
- at least two physical NICs are present if you want a two-port appliance
- core tools are available

If `doctor` says you have fewer than two physical NICs, your system is not ready for a two-port conference/demo layout yet.

## 3. Identify Interface Names

Run:

```bash
new8021x interfaces
```

Find the names of:

- the upstream NIC
- the downstream NIC
- an optional management sidechannel NIC

Common examples:

- onboard Ethernet: `eth0`
- USB Ethernet adapters: names such as `enx...`
- Wi-Fi sidechannel: `wlan0`

## 4. Validate the Intended Layout

Run:

```bash
new8021x preflight --upstream eth0 --downstream eth1
```

This does not change the machine. It only checks whether your selected layout is plausible.

If you are not sure which NIC should be upstream or downstream, try:

```bash
new8021x suggest-layout
```

## 5. Observe EAPOL Traffic

Run as root:

```bash
sudo new8021x observe --iface eth0 --seconds 15
```

This command passively listens and prints a summary.

If you want a saved report:

```bash
sudo new8021x observe --iface eth0 --seconds 15 --report reports/observe.md
```

## 6. Save a Config

Write an example config:

```bash
new8021x init-config
```

Then edit `config.toml` and set the interface names for your appliance.

After that you can use:

```bash
new8021x --config config.toml preflight
sudo new8021x --config config.toml observe
```

## 7. Unattended Passive Appliance Mode

To keep writing timestamped reports in a loop:

```bash
sudo new8021x --config config.toml observe-loop --iface eth0 --seconds 30 --interval 5 --output-dir reports
```

To analyze a saved capture later:

```bash
new8021x analyze-pcap --file capture.pcap
```

## Important Current Limitation

This project is not yet a full Raspberry Pi 802.1X demo appliance.

Right now it is:

- a documented project skeleton
- a host readiness checker
- a passive 802.1X observer

It is not yet:

- an active bridge
- a forwarding appliance
- an authenticator emulator
- an active bypass tool
