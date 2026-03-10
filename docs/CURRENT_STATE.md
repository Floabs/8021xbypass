# Current State

Date: 2026-03-10

This file answers the practical question: what can `new8021x` do today, and what can it not do yet?

## What Works Today

Implemented and verified:

- Python 3 packaging and CLI entrypoint
- host readiness checks
- interface inventory
- two-NIC preflight validation
- interface-role suggestion heuristics
- passive EAPOL / EAP observation on a live interface
- repeated passive observation windows for unattended use
- offline classic PCAP analysis
- Markdown report output
- JSON report output
- basic automated tests

Verified in the current environment:

- code compiles under Python 3
- unit tests pass
- `doctor` works
- `preflight` works
- a one-second live `observe` smoke test works
- the surrounding AP2 VM lab now includes a Linux authenticator node and a prepared appliance VM; see `docs/LAB_ENVIRONMENT.md`
- the current inline lab breakpoint is now documented: downstream `EAPOL-Start` is visible on the appliance, but no corresponding upstream `EAPOL` reaches the authenticator-facing side

## What Does Not Exist Yet

Not implemented:

- bridge creation
- packet forwarding
- route management
- firewall orchestration
- Raspberry Pi service packaging
- TUI or web UI
- offline PCAP import
- active lab-only modules

## Direct Answer: Is It a Deployable Bypass Appliance Yet?

No.

If you deployed it to a Raspberry Pi today, it would be useful for:

- checking the appliance hardware and interfaces
- validating interface selections
- passively observing 802.1X traffic in a lawful lab or demo environment

It would not yet be able to:

- automatically set up a full two-NIC inline appliance workflow
- perform an active 802.1X bypass demonstration
- replace the older offensive proof-of-concept tools end to end

In the current VM lab, that means:

- the appliance can prove it is physically inline on the downstream side by observing `EAPOL-Start`
- the appliance does not currently provide a path that carries that traffic onward to the authenticator side
- a successful end-to-end inline 802.1X exchange should therefore not be expected from this codebase today

## Why It Was Built This Way

The first step was to create a modern, stable, well-documented core that is safe to run and easy for non-specialists to understand.

That gives us:

- a maintainable codebase
- a Raspberry Pi friendly packaging model
- a place to add future modules cleanly

It avoids repeating the main problems from the older repos:

- Python 2 dependency
- hard-coded interface names
- hidden shell state
- fragile legacy tool assumptions
- incomplete documentation

## Most Useful Next Steps

If the goal remains a serious conference or awareness appliance, the next safe engineering steps are:

1. Add richer passive reporting and optional offline PCAP analysis.
2. Add Raspberry Pi installation and `systemd` docs/scripts.
3. Improve interface role heuristics and optionally connect them to guided setup flows.
4. Add deterministic network-namespace integration tests.
5. Decide how any future isolated-lab-only active modules will be separated from the default conference/demo runtime.
