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

### Final answer

When you have enough information, output the complete architecture JSON in a ```json fenced code block.
Always output the COMPLETE architecture JSON, not a partial diff."""

SYSTEM_INSTRUCTIONS = """\
You are editing a software architecture diagram. The user will ask you to modify it.
Respond with a brief explanation of what you changed, then output the complete updated
architecture JSON in a ```json fenced code block.

Always output the COMPLETE architecture JSON, not a partial diff."""


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


def extract_architecture(text):
    blocks = re.findall(r"```json\s*\n(.*?)```", text, re.DOTALL)
    for block in blocks:
        try:
            data = json.loads(block.strip())
            if isinstance(data, dict) and "components" in data:
                return data
        except json.JSONDecodeError:
            continue
    return None


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


async def handle(ws):
    async for raw in ws:
        try:
            msg = json.loads(raw)
        except json.JSONDecodeError:
            await ws.send(json.dumps({"type": "error", "content": "Invalid JSON"}))
            continue

        if msg.get("type") != "chat":
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
            arch = extract_architecture(response)

            # Send text to frontend (strip tool_call blocks for readability)
            display = re.sub(r"```tool_call\s*\n.*?```", "", response, flags=re.DOTALL).strip()
            if display:
                await ws.send(json.dumps({"type": "text", "content": display}))

            # If architecture JSON found, send it to update the diagram
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
