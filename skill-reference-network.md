# sd-architect Format Reference (Network Mode)

Full skill: https://github.com/benthomasson/sd-architect-skill

## network.json

```json
{
  "components": [...],
  "connections": [...],
  "view": {"translate_x": 960, "translate_y": 540, "scale": 1.0, "theme": "dark", "mode": "network"}
}
```

### Component Fields

- `name` (required) — unique identifier, shown in the title bar
- `type` (required) — one of the types below
- `position` (required) — `[x, y]` center of the box
- `technology` (optional) — displayed as subtitle
- `description` (optional)
- `size` (groups only) — `[w, h]` of the group container
- `members` (groups only) — list of component names to auto-size around

### Connection Fields

- `from` (required) — source port name
- `to` (required) — destination port name
- `label` (optional) — text rendered at the wire midpoint

### View Fields

- `translate_x`, `translate_y` — viewport offset
- `scale` — zoom level (1.0 = 100%)
- `theme` — `"dark"` or `"light"`
- `mode` — `"network"` (required for network diagrams)
- `name` — diagram name

## Network Component Types and Ports

Port names are `<component_name>_<port_suffix>`.

| type         | input ports  | output ports | technology |
|--------------|--------------|--------------|------------|
| server       | `_eth0`      | `_eth1`      | Linux      |
| switch       | `_p1`, `_p2` | `_p3`, `_p4` | L2         |
| router       | `_wan`       | `_lan`       | L3         |
| firewall     | `_ext`       | `_int`       | iptables   |
| workstation  |              | `_net`       | —          |
| access_point | `_uplink`    | `_wifi`      | WiFi 6     |
| internet     |              | `_conn`      | —          |
| dns          | `_query`     | `_resolve`   | BIND       |
| vpn          | `_public`    | `_tunnel`    | WireGuard  |
| group        | (none)       | (none)       | —          |
| label        | (none)       | (none)       | —          |
| textarea     | (none)       | (none)       | —          |

### Labels

```json
{"name": "title", "type": "label", "text": "Office Network", "font_size": 36, "position": [0, -500]}
```

### Groups

```json
{"name": "dmz", "type": "group", "members": ["web_server", "mail_server"], "position": [0, 0]}
```

## Layout Conventions

- Positive x is right, positive y is **down** (screen convention)
- Components are roughly 330x225 — leave ~400px between centers horizontally, ~250px vertically
- Internet/WAN on the left, internal network on the right
- Firewalls sit between network zones
- Groups represent subnets or VLANs
