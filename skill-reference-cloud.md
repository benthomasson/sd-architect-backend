# sd-architect Format Reference (Cloud Mode)

Full skill: https://github.com/benthomasson/sd-architect-skill

## cloud.json

```json
{
  "components": [...],
  "connections": [...],
  "view": {"translate_x": 960, "translate_y": 540, "scale": 1.0, "theme": "dark", "mode": "cloud"}
}
```

### Component Fields

- `name` (required) — unique identifier, shown in the title bar
- `type` (required) — one of the types below
- `position` (required) — `[x, y]` center of the box
- `technology` (optional) — picks a logo if one exists
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
- `mode` — `"cloud"` (required for cloud diagrams)
- `name` — diagram name

## Cloud Component Types and Ports

Port names are `<component_name>_<port_suffix>`.

| type           | input ports   | output ports   | default tech | logo       |
|----------------|---------------|----------------|--------------|------------|
| vpc            | `_ingress`    | `_egress`      | —            | —          |
| app_gateway    | `_frontend`   | `_backend`     | —            | —          |
| vm             | `_eth0`       | `_eth1`        | Linux        | —          |
| container      | `_ingress`    | `_egress`      | Docker       | —          |
| serverless     | `_trigger`    | `_output`      | —            | —          |
| object_storage | `_read_write` |                | S3           | S3         |
| block_storage  | `_attach`     |                | —            | —          |
| cloud_lb       | `_frontend`   | `_backend`     | —            | —          |
| cdn            | `_origin`     | `_edge`        | Cloudflare   | Cloudflare |
| cloud_dns      | `_query`      | `_resolve`     | —            | —          |
| cloud_vpn      | `_public`     | `_private`     | WireGuard    | —          |
| relational_db  | `_query`      | `_replication` | PostgreSQL   | PostgreSQL |
| nosql_db       | `_read_write` | `_stream`      | —            | —          |
| data_warehouse | `_ingest`     | `_query`       | Snowflake    | Snowflake  |
| cloud_cache    | `_get_set`    |                | Redis        | Redis      |
| iam            | `_auth`       | `_policy`      | —            | —          |
| key_vault      | `_encrypt`    | `_decrypt`     | —            | —          |
| waf            | `_ingress`    | `_filtered`    | —            | —          |
| group          | (none)        | (none)         | —            | —          |
| label          | (none)        | (none)         | —            | —          |
| textarea       | (none)        | (none)         | —            | —          |

### Labels

```json
{"name": "title", "type": "label", "text": "AWS Production", "font_size": 36, "position": [0, -500]}
```

### Groups

```json
{"name": "prod_vpc", "type": "group", "members": ["web_server", "app_server", "rds"], "position": [0, 0]}
```

## Available Logos

S3, Cloudflare, PostgreSQL, Redis, Snowflake — set via `technology` field.

## Layout Conventions

- Positive x is right, positive y is **down** (screen convention)
- Components are roughly 330x225 — leave ~400px between centers horizontally, ~250px vertically
- Internet/users on the left, data stores on the right
- WAF and load balancers sit at the ingress edge
- Groups represent VPCs, subnets, or availability zones
- Security components (IAM, key vault) typically sit outside the main data flow
