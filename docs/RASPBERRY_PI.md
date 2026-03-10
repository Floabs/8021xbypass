# Raspberry Pi Deployment

This guide explains the current, safe deployment path for `new8021x` on Raspberry Pi OS.

## Current Goal

The current Raspberry Pi deployment target is a passive observation appliance, not an active bypass appliance.

That means a Pi deployment can currently do the following well:

- boot into a known software environment
- validate attached NICs
- suggest interface roles
- run repeated EAPOL observation windows
- write timestamped reports for later review
- analyze saved PCAP files offline

## Raspberry Pi OS Notes

Two current Raspberry Pi OS details matter here:

- Raspberry Pi OS Bookworm requires Python packages installed with `pip` to go into a virtual environment.
- Raspberry Pi OS Bookworm uses NetworkManager as the default network configuration stack.

Those points come from the official Raspberry Pi documentation and are the reason this project uses a per-project `venv` and modern `ip`/`bridge` tooling instead of older `ifconfig` habits.

## Recommended Hardware

- Raspberry Pi 4 or Raspberry Pi 5
- Raspberry Pi OS Lite
- one onboard Ethernet port if available
- one USB Ethernet adapter for the second wired interface
- optional Wi-Fi sidechannel
- stable power supply
- quality SD card or SSD boot

## Software Install

From the project root on the Raspberry Pi:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e .
```

Quick checks:

```bash
new8021x doctor
new8021x interfaces
new8021x suggest-layout
```

## Recommended First-Run Sequence

1. Boot the Pi and connect all NICs.
2. Run `new8021x doctor`.
3. Run `new8021x interfaces`.
4. Run `new8021x suggest-layout`.
5. Create a config with `new8021x init-config`.
6. Edit the config and set the correct interface names.
7. Run `new8021x --config config.toml preflight`.
8. Run a short live check:

```bash
sudo new8021x --config config.toml observe --seconds 15
```

## Continuous Appliance Mode

The project includes:

- a service template at `deploy/systemd/new8021x-observe.service`
- an example environment file at `deploy/systemd/new8021x-observe.env.example`
- an install helper at `scripts/install_pi_observer.sh`

The service runs `observe-loop`, which repeatedly performs passive observation windows and writes timestamped Markdown and JSON files.

### Manual service setup

Copy the service and environment file:

```bash
sudo cp deploy/systemd/new8021x-observe.service /etc/systemd/system/
sudo cp deploy/systemd/new8021x-observe.env.example /etc/default/new8021x-observe
```

Edit `/etc/default/new8021x-observe` and set:

- `NEW8021X_IFACE`
- `NEW8021X_SECONDS`
- `NEW8021X_INTERVAL`
- `NEW8021X_OUTPUT_DIR`

Then enable the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now new8021x-observe.service
```

Check logs:

```bash
sudo journalctl -u new8021x-observe.service -f
```

## Offline Analysis Workflow

If you captured traffic with another tool, you can analyze a classic Ethernet `.pcap` file offline:

```bash
new8021x analyze-pcap --file capture.pcap
new8021x analyze-pcap --file capture.pcap --report reports/offline.md
```

Current limitation:

- only classic Ethernet `pcap` is supported
- `pcapng` is not yet supported

## Operator-Friendly Commands

For non-specialist operators, the safest useful sequence is:

```bash
new8021x doctor
new8021x interfaces
new8021x suggest-layout
new8021x --config config.toml preflight
sudo new8021x --config config.toml observe --seconds 15
```

For unattended passive monitoring:

```bash
sudo new8021x --config config.toml observe-loop --seconds 30 --interval 5 --output-dir reports
```

## References

- Raspberry Pi documentation on Python package installation and Bookworm `venv` behavior:
  - <https://www.raspberrypi.com/documentation/computers/os.html>
- Raspberry Pi documentation noting NetworkManager as the default on Bookworm:
  - <https://www.raspberrypi.com/documentation/computers/configuration.html>
- Raspberry Pi Bookworm release note background:
  - <https://www.raspberrypi.com/news/bookworm-the-new-version-of-raspberry-pi-os/>
