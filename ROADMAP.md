# new8021x Roadmap

## Phase 1: Usable Awareness Appliance

- Keep the runtime Python 3 only.
- Keep the base install standard-library first.
- Treat passive observation and appliance preflight as the stable core.
- Add signed release artifacts for Raspberry Pi OS.
- Add a `systemd` service for one-command boot into observation mode.
- Add a small local web or TUI status view only if it improves field usability.

## Phase 2: Better Research Ergonomics

- Add offline PCAP ingestion for EAPOL-focused analysis.
- Add LLDP and DHCP metadata summaries for awareness demos.
- Improve interface role suggestions and optionally feed them into guided setup flows.
- Add Markdown and JSON report bundles for conference handouts and internal notes.
- Add network-namespace based integration tests.

## Phase 3: Lab-Only Extension Surface

- Add a plugin API so isolated testbed modules are separate from the appliance core.
- Require explicit `lab_only = true` enablement for any active mode.
- Keep all active or disruptive experiments behind separate modules, docs, and tests.
- Do not mix conference-awareness defaults with disruptive lab behavior.

## Design Rules

- No silent fallbacks.
- No hard-coded interface names.
- No legacy `ifconfig` or `route` dependency.
- No hidden state in shell scripts.
- No runtime behavior that depends on missing external wiki pages.
