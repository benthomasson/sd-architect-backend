# sd-architect Format Reference (CI/CD Mode)

Full skill: https://github.com/benthomasson/sd-architect-skill

## cicd.json

```json
{
  "components": [...],
  "connections": [...],
  "view": {"translate_x": 960, "translate_y": 540, "scale": 1.0, "theme": "dark", "mode": "cicd"}
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
- `mode` — `"cicd"` (required for CI/CD diagrams)
- `name` — diagram name

## CI/CD Component Types and Ports

Port names are `<component_name>_<port_suffix>`. Connections represent pipeline flow — artifacts and triggers moving through stages.

| type       | input ports | output ports  | description              |
|------------|-------------|---------------|--------------------------|
| code_repo  | `_push`     | `_trigger`    | Source code repository   |
| build_step | `_source`   | `_artifact`   | Build / compile stage    |
| test_step  | `_input`    | `_result`     | Test / validation stage  |
| staging    | `_deploy`   | `_promote`    | Staging environment      |
| production | `_deploy`   | `_monitor`    | Production environment   |
| group      | (none)      | (none)        | Pipeline grouping        |
| label      | (none)      | (none)        | —                        |
| textarea   | (none)      | (none)        | —                        |

### Labels

```json
{"name": "title", "type": "label", "text": "Deploy Pipeline", "font_size": 36, "position": [0, -500]}
```

### Groups

```json
{"name": "testing", "type": "group", "members": ["unit_tests", "integration_tests"], "position": [0, 0]}
```

## Layout Conventions

- Positive x is right, positive y is **down** (screen convention)
- Pipeline flow reads left-to-right: repo → build → test → staging → production
- Components are roughly 330x225 — leave ~400px between centers horizontally, ~250px vertically
- Groups can wrap related stages (e.g., all test steps)
- Parallel pipelines stack vertically
