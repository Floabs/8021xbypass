# Lab Environment

Date: 2026-03-10

This repository is the appliance/runtime code for the AP2 lab. The VM inventory, bootstrap scripts, and host-specific infrastructure live in `/opt/8021x`.

## Current VM Roles

- `freeradius` at `192.168.55.40`
- `wpasupp01` at `192.168.55.41`
- `wpasupp02` at `192.168.55.42`
- `authenticator` at `192.168.55.45`
- `appliance` at `192.168.55.44`

## Interface Model

- `enp0s3`: management path on `192.168.55.0/24`
- `enp0s8`: authenticator-facing or appliance-upstream path on `ap2_access`
- `enp0s9`: appliance-downstream path on `ap2_access_downstream`

## Important Virtualization Rule

Do not attach both data-path sides of an inline test to the same Bridged Adapter network.

For the VM-first lab, use:

- one management network for SSH and package access
- one internal network for the authenticator-facing path
- one separate internal network for the downstream/client-facing path

## Current Practical State

- `new8021x` remains passive and validation-oriented.
- The external lab now includes a dedicated Linux authenticator VM.
- The appliance VM now has the `new8021x` runtime installed under `/opt/new8021x`.
- The direct authenticator-to-supplicant segment on `ap2_access` has been validated successfully.
- The inline VM topology has now been rewired so the direct authenticator-to-supplicant shortcut is removed.
- During the latest passive inline check, the appliance saw a real `EAPOL-Start` on `enp0s9` from `wpasupp01`.
- During that same test window, the appliance saw no `EAPOL` on `enp0s8`.
- The current lab breakpoint is therefore clear: downstream supplicant traffic reaches the appliance, but does not reach the authenticator-facing side through the appliance path.

## Why This Matters

This separation keeps the code in this repository honest about what it can do today:

- host checks
- interface inventory
- passive EAPOL observation
- report generation

It still does not yet create the active inline bridge or forwarding workflow automatically, and the current VM lab result matches that limitation exactly.
