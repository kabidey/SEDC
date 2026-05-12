# SMIFS Enterprise Data Centre

A full-stack DCIM / IPAM / network-management platform (NetBox-style) for SMIFS.

## Stack

- **Frontend**: React 19, Tailwind, shadcn/ui (green enterprise theme)
- **Backend**: FastAPI, Motor (async MongoDB), JWT auth, Strawberry GraphQL
- **Database**: MongoDB

## Modules

Organization · Devices · Racks · Connections · IPAM · Circuits · Power ·
Virtualization · Wireless · VPN/Overlay · Customization · Discovery · Admin.

## Discovery / Autodiscovery

Built-in SNMP scanner (v1 / v2c / v3) plus integration with an external
Netdisco instance. Discovered devices can be one-click-imported as
SMIFS Devices, Interfaces, IP addresses and Cables (LLDP/CDP inferred).

## Default credentials

`admin / admin` (auto-seeded; replace before production).
