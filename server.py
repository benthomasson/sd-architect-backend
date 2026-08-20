import asyncio
import json
import os
import re
from pathlib import Path

import websockets

SKILL_REF = (Path(__file__).parent / "skill-reference.md").read_text()
REASONS_DB = os.environ.get(
    "REASONS_DB",
    os.path.expanduser("~/git/drawing-shell-expert/reasons.db"),
)
MAX_TOOL_ITERATIONS = 10

TOOL_INSTRUCTIONS = """\
You have access to a belief database (a truth maintenance system) via these tools.
To call a tool, output a fenced code block tagged `tool_call` with JSON inside:

```tool_call
{"tool": "reasons_search", "args": {"query": "your search query"}}
```

You can make multiple tool calls in one response. After each round of tool calls,
you will receive the results and can make more calls or produce your final answer.

### Available tools

| Tool | Args | Description |
|------|------|-------------|
| reasons_search | query, db? | Full-text search for beliefs |
| reasons_show | node_id, db? | Show node details and justifications |
| reasons_explain | node_id, db? | Trace why a node is IN or OUT |
| reasons_list | status?, premises?, by_impact?, db? | List beliefs with filters |
| reasons_trace | node_id, db? | Trace premises a belief rests on |
| reasons_topics | db? | List topic clusters |
| reasons_status | db? | Overview of all nodes with truth values |

All tools accept an optional `db` argument to target a specific database file.
Default database: """ + REASONS_DB + """

### When to use tools

- If the user asks you to build a diagram FROM beliefs or a knowledge base, use tools to explore the beliefs first
- If the user references a specific reasons database, use tools with that `db` path
- For simple diagram edits (add a component, change a connection), you usually don't need tools

### Final answer — Delta Edits

When modifying an existing diagram, output a delta edit list in a ```json fenced code block.
Do NOT regenerate the full architecture JSON. Instead, emit only the changes:

```json
{"edits": [
  {"op": "add_component", "component": {"name": "cache", "type": "cache", "position": [800, 300], "technology": "Redis"}},
  {"op": "add_connection", "connection": {"from": "api_out", "to": "cache_cache_in", "label": "get/set"}}
]}
```

#### Available edit operations

| op | Fields | Notes |
|----|--------|-------|
| add_component | component: {name, type, position, technology?, ...} | Full component object |
| remove_component | name | Connections to this component are removed automatically |
| update_component | name, plus any fields to change (position?, technology?, text?, description?, size?, font_size?, width?, icon_scale?, type?) | Only supplied fields change; omitted fields are preserved |
| add_connection | connection: {from, to, label?} | Full connection object |
| remove_connection | from, to | Identified by port pair |
| update_connection | from, to, label? | Only supplied fields change |
| rename_component | old_name, new_name | Port references in connections are updated automatically |

#### Rules

- Use delta edits for ALL modifications to existing diagrams
- Multiple ops in one edit list are applied in order
- Component names must be unique
- Port names follow the pattern `<component_name>_<port_suffix>` (see port table above)
- When adding a component AND connecting it, include both ops in the same edit list
- Only output a full architecture JSON (with `"components"`) when creating a brand new diagram from scratch (no existing architecture)"""

SYSTEM_INSTRUCTIONS = """\
You are editing a software architecture diagram. The user will ask you to modify it.
Respond with a brief explanation of what you changed, then output a delta edit list
in a ```json fenced code block with `{"edits": [...]}`.

Use delta edits for modifications. Only output a full architecture JSON with
`{"components": [...]}` when creating a brand new diagram from scratch."""


async def run_reasons(args):
    try:
        proc = await asyncio.create_subprocess_exec(
            "reasons", *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode().strip()
        return f"Error: {stderr.decode().strip()}"
    except FileNotFoundError:
        return "Error: reasons CLI not found"


async def run_tool(tool_name, args):
    db = os.path.expanduser(args.get("db", REASONS_DB))
    base = ["--db", db]

    if tool_name == "reasons_search":
        return await run_reasons(base + ["search", args["query"]])
    elif tool_name == "reasons_show":
        return await run_reasons(base + ["show", args["node_id"]])
    elif tool_name == "reasons_explain":
        return await run_reasons(base + ["explain", args["node_id"]])
    elif tool_name == "reasons_trace":
        return await run_reasons(base + ["trace", args["node_id"]])
    elif tool_name == "reasons_topics":
        return await run_reasons(base + ["topics"])
    elif tool_name == "reasons_status":
        return await run_reasons(base + ["status"])
    elif tool_name == "reasons_list":
        cmd = base + ["list"]
        if args.get("status"):
            cmd += ["--status", args["status"]]
        if args.get("premises"):
            cmd += ["--premises"]
        if args.get("by_impact"):
            cmd += ["--by-impact"]
        return await run_reasons(cmd)
    else:
        return f"Error: unknown tool '{tool_name}'"


def parse_tool_calls(text):
    return [
        json.loads(block.strip())
        for block in re.findall(r"```tool_call\s*\n(.*?)```", text, re.DOTALL)
        if block.strip()
    ]


def extract_response(text):
    """Parse LLM response for either a full architecture or delta edits.

    Returns (architecture_dict, edits_list) — at most one is non-None.
    """
    blocks = re.findall(r"```json\s*\n(.*?)```", text, re.DOTALL)
    for block in blocks:
        try:
            data = json.loads(block.strip())
            if not isinstance(data, dict):
                continue
            if "edits" in data:
                return None, data["edits"]
            if "components" in data:
                return data, None
        except json.JSONDecodeError:
            continue
    return None, None


def apply_edits(arch, edits):
    """Apply a list of delta edit ops to an architecture dict. Returns the modified arch."""
    arch = json.loads(json.dumps(arch))  # deep copy
    components = arch.get("components", [])
    connections = arch.get("connections", [])

    for edit in edits:
        op = edit.get("op")

        if op == "add_component":
            components.append(edit["component"])

        elif op == "remove_component":
            name = edit["name"]
            components = [c for c in components if c.get("name") != name]
            prefix = f"{name}_"
            connections = [c for c in connections
                           if not c["from"].startswith(prefix) and not c["to"].startswith(prefix)]

        elif op == "update_component":
            name = edit["name"]
            for comp in components:
                if comp.get("name") == name:
                    for key, val in edit.items():
                        if key not in ("op", "name"):
                            comp[key] = val
                    break

        elif op == "add_connection":
            connections.append(edit["connection"])

        elif op == "remove_connection":
            fr, to = edit["from"], edit["to"]
            connections = [c for c in connections if not (c["from"] == fr and c["to"] == to)]

        elif op == "update_connection":
            fr, to = edit["from"], edit["to"]
            for conn in connections:
                if conn["from"] == fr and conn["to"] == to:
                    for key, val in edit.items():
                        if key not in ("op", "from", "to"):
                            conn[key] = val
                    break

        elif op == "rename_component":
            old_name, new_name = edit["old_name"], edit["new_name"]
            for comp in components:
                if comp.get("name") == old_name:
                    comp["name"] = new_name
                    break
            old_prefix = f"{old_name}_"
            new_prefix = f"{new_name}_"
            for conn in connections:
                if conn["from"].startswith(old_prefix):
                    conn["from"] = new_prefix + conn["from"][len(old_prefix):]
                if conn["to"].startswith(old_prefix):
                    conn["to"] = new_prefix + conn["to"][len(old_prefix):]

    arch["components"] = components
    arch["connections"] = connections
    return arch


# Per-connection undo history: list of architecture snapshots.
# Key = websocket id, value = {"undo": [arch, ...], "redo": [arch, ...], "current": arch}
undo_stacks = {}


def build_prompt(architecture, conversation):
    arch_json = json.dumps(architecture, indent=2)
    conv_text = "\n\n".join(conversation)
    return f"""{SKILL_REF}

{TOOL_INSTRUCTIONS}

## Current Architecture

```json
{arch_json}
```

## Instructions

{SYSTEM_INSTRUCTIONS}

## Conversation

{conv_text}"""


async def run_claude(prompt):
    proc = await asyncio.create_subprocess_exec(
        "claude", "-p", prompt,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await proc.communicate()
    if proc.returncode != 0:
        err = stderr.decode().strip()
        raise RuntimeError(f"claude exited {proc.returncode}: {err}")
    return stdout.decode()


def push_undo(ws_id, arch):
    """Save architecture state to undo stack before applying changes."""
    if ws_id not in undo_stacks:
        undo_stacks[ws_id] = {"undo": [], "redo": []}
    stack = undo_stacks[ws_id]
    stack["undo"].append(json.loads(json.dumps(arch)))
    stack["redo"].clear()
    if len(stack["undo"]) > 50:
        stack["undo"] = stack["undo"][-50:]


async def handle(ws):
    ws_id = id(ws)
    try:
        await _handle(ws, ws_id)
    finally:
        undo_stacks.pop(ws_id, None)


async def _handle(ws, ws_id):
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await ws.send(json.dumps({"type": "error", "content": "Invalid JSON"}))
            continue

        msg_type = msg.get("type")

        if msg_type == "undo":
            architecture = msg.get("architecture", {})
            stack = undo_stacks.get(ws_id, {"undo": [], "redo": []})
            if stack["undo"]:
                stack["redo"].append(json.loads(json.dumps(architecture)))
                prev = stack["undo"].pop()
                await ws.send(json.dumps({"type": "architecture", "data": prev}))
            continue

        if msg_type == "redo":
            architecture = msg.get("architecture", {})
            stack = undo_stacks.get(ws_id, {"undo": [], "redo": []})
            if stack["redo"]:
                stack["undo"].append(json.loads(json.dumps(architecture)))
                next_arch = stack["redo"].pop()
                await ws.send(json.dumps({"type": "architecture", "data": next_arch}))
            continue

        if msg_type != "chat":
            continue

        message = msg.get("message", "")
        architecture = msg.get("architecture", {})

        if not message.strip():
            await ws.send(json.dumps({"type": "error", "content": "Empty message"}))
            continue

        conversation = [f"**User:** {message}"]

        for iteration in range(MAX_TOOL_ITERATIONS):
            prompt = build_prompt(architecture, conversation)

            try:
                response = await run_claude(prompt)
            except RuntimeError as e:
                await ws.send(json.dumps({"type": "error", "content": str(e)}))
                break

            tool_calls = parse_tool_calls(response)
            arch, edits = extract_response(response)

            # Send text to frontend (strip tool_call and json blocks for readability)
            display = re.sub(r"```tool_call\s*\n.*?```", "", response, flags=re.DOTALL).strip()
            if display:
                await ws.send(json.dumps({"type": "text", "content": display}))

            # Handle delta edits — apply to current architecture
            if edits is not None:
                push_undo(ws_id, architecture)
                arch = apply_edits(architecture, edits)
                architecture = arch
                print(f"  Applied {len(edits)} delta edit(s)")

            # If architecture JSON found (full regen or applied deltas), send it
            if arch:
                await ws.send(json.dumps({"type": "architecture", "data": arch}))

            # If no tool calls, we're done
            if not tool_calls:
                break

            # Execute tool calls and continue the loop
            conversation.append(f"**Assistant:** {response}")

            tool_names = [tc.get("tool", "?") for tc in tool_calls]
            await ws.send(json.dumps({
                "type": "text",
                "content": f"\n\n_Querying knowledge base: {', '.join(tool_names)}_\n",
            }))

            results = []
            for tc in tool_calls:
                tool_name = tc.get("tool", "")
                tool_args = tc.get("args", {})
                print(f"  Tool call: {tool_name}({tool_args})")
                result = await run_tool(tool_name, tool_args)
                results.append(f"### Result of {tool_name}\n\n{result}")

            conversation.append("**Tool Results:**\n\n" + "\n\n".join(results))

            # If we already got architecture, stop even though there were tool calls
            if arch:
                break
        else:
            await ws.send(json.dumps({
                "type": "text",
                "content": "Reached maximum tool iterations. Returning last response.",
            }))

        await ws.send(json.dumps({"type": "done"}))


async def main():
    print("sd-architect-backend listening on ws://localhost:8765")
    print(f"  Default beliefs DB: {REASONS_DB}")
    async with websockets.serve(handle, "localhost", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
