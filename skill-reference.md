# sd-architect Format Reference

Full skill: https://github.com/benthomasson/sd-architect-skill

## architecture.json

```json
{
  "components": [...],
  "connections": [...],
  "view": {"translate_x": 960, "translate_y": 540, "scale": 1.0, "theme": "dark"}
}
```

### Component Fields

- `name` (required) — unique identifier, shown in the title bar
- `type` (required) — one of the types below
- `position` (required) — `[x, y]` center of the box
- `technology` (optional) — picks a logo if one exists
- `icon_scale` (optional) — override the logo's default scale
- `description` (optional)
- `size` (groups only) — `[w, h]` of the group container

### Connection Fields

- `from` (required) — source port name
- `to` (required) — destination port name
- `label` (optional) — text rendered at the wire midpoint

### View Fields

- `translate_x`, `translate_y` — viewport offset
- `scale` — zoom level (1.0 = 100%)
- `theme` — `"dark"` or `"light"`
- `name` — diagram name

## Component Types and Ports

Port names are `<component_name>_<port_suffix>`.

| type            | input ports          | output ports                | default icon |
|-----------------|----------------------|-----------------------------|--------------|
| client          |                      | `_request`                  | —            |
| load_balancer   | `_lb_in`             | `_lb_out`                   | nginx        |
| service         | `_in`                | `_out`, `_event`            | FastAPI      |
| database        | `_query`             | `_replication`              | PostgreSQL   |
| cache           | `_cache_in`          |                             | Redis        |
| queue           | `_publish`           | `_consume`                  | RabbitMQ     |
| external        | `_ext_in`            | `_ext_out`                  | —            |
| script          | `_in`                | `_out`                      | Terminal     |
| message_broker  | `_topic_in`          | `_topic_out`                | Kafka        |
| group           | (none — visual only) | (none)                      | —            |
| label           | (none)               | (none)                      | —            |
| textarea        | (none)               | (none)                      | —            |

### Labels

```json
{"name": "title", "type": "label", "text": "Production", "font_size": 36, "position": [0, -500]}
```

### Textareas

```json
{"name": "rationale", "type": "textarea", "text": "Cache is sized for 90% hit rate.", "width": 300, "font_size": 14, "position": [400, 0]}
```

### Groups

```json
{"name": "backend", "type": "group", "position": [0, 0], "size": [800, 600]}
```

## Available Logos

nginx, FastAPI, PostgreSQL, SQLite, Redis, RabbitMQ, Kafka, LangChain, Langfuse, Snowflake, Firefox, Vertex AI, MCP, Ollama, Terminal, S3, Red Hat, filesystem, Prometheus, Segment, Amplitude, LiteLLM

Unknown technologies still render — the title shows the name and the subtitle shows the technology text (without an icon).

## Layout Conventions

- Positive x is right, positive y is **down** (screen convention)
- Components are roughly 330x225 — leave ~400px between centers horizontally, ~250px vertically
- Request flow reads left-to-right
- Data stores (db, cache) sit to the right of the services that use them
- Groups sit behind their member components (earlier in array)
