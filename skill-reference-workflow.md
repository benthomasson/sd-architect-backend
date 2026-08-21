# sd-architect Format Reference (Workflow Mode)

Full skill: https://github.com/benthomasson/sd-architect-skill

## workflow.json

```json
{
  "components": [...],
  "connections": [...],
  "view": {"translate_x": 960, "translate_y": 540, "scale": 1.0, "theme": "dark", "mode": "workflow"}
}
```

### Component Fields

- `name` (required) — unique identifier, shown in the title bar
- `type` (required) — one of the types below
- `position` (required) — `[x, y]` center of the box
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
- `mode` — `"workflow"` (required for workflow diagrams)
- `name` — diagram name

## Workflow Step Types and Ports

Port names are `<component_name>_<port_suffix>`. Connections represent directed flow — "happens after", not "talks to".

| type     | input ports          | output ports                | color  |
|----------|----------------------|-----------------------------|--------|
| start    |                      | `_out`                      | green  |
| step     | `_in`                | `_out`                      | teal   |
| decision | `_in`                | `_yes`, `_no`               | amber  |
| fork     | `_in`                | `_out_a`, `_out_b`          | blue   |
| join     | `_in_a`, `_in_b`     | `_out`                      | blue   |
| end      | `_in`                |                             | red    |
| group    | (none — visual only) | (none)                      | —      |
| label    | (none)               | (none)                      | —      |
| textarea | (none)               | (none)                      | —      |

### Labels

```json
{"name": "title", "type": "label", "text": "Deploy Pipeline", "font_size": 36, "position": [0, -500]}
```

### Textareas

```json
{"name": "notes", "type": "textarea", "text": "Rollback if health check fails.", "width": 300, "font_size": 14, "position": [400, 0]}
```

### Groups

```json
{"name": "testing", "type": "group", "members": ["unit_tests", "integration_tests"], "position": [0, 0]}
```

## Layout Conventions

- Positive x is right, positive y is **down** (screen convention)
- Flow reads top-to-bottom by default
- Steps are roughly 330x225 — leave ~400px between centers horizontally, ~300px vertically
- Use Start at the top, End at the bottom
- Fork/Join pairs should be vertically aligned with parallel steps between them
- Decision branches: `_yes` goes left or down, `_no` goes right
- Groups can surround related steps (use `members` for auto-sizing)
