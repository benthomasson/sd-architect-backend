import asyncio
import json
import re
from pathlib import Path

import websockets

SKILL_REF = (Path(__file__).parent / "skill-reference.md").read_text()

SYSTEM_INSTRUCTIONS = """\
You are editing a software architecture diagram. The user will ask you to modify it.
Respond with a brief explanation of what you changed, then output the complete updated
architecture JSON in a ```json fenced code block.

Always output the COMPLETE architecture JSON, not a partial diff."""


def build_prompt(message, architecture):
    arch_json = json.dumps(architecture, indent=2)
    return f"""{SKILL_REF}

## Current Architecture

```json
{arch_json}
```

## Instructions

{SYSTEM_INSTRUCTIONS}

## User Request

{message}"""


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

        prompt = build_prompt(message, architecture)

        try:
            response = await run_claude(prompt)
        except RuntimeError as e:
            await ws.send(json.dumps({"type": "error", "content": str(e)}))
            await ws.send(json.dumps({"type": "done"}))
            continue

        await ws.send(json.dumps({"type": "text", "content": response}))

        arch = extract_architecture(response)
        if arch:
            await ws.send(json.dumps({"type": "architecture", "data": arch}))

        await ws.send(json.dumps({"type": "done"}))


async def main():
    print("sd-architect-backend listening on ws://localhost:8765")
    async with websockets.serve(handle, "localhost", 8765):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
