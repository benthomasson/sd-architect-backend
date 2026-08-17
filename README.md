# sd-architect-backend

WebSocket backend that connects the [sd-architect](https://sd.ftl2.com) diagram editor's chat panel to Claude. Type natural language in the chat and Claude modifies the architecture diagram directly.

## Prerequisites

- Python 3.10+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-code) installed and authenticated (`claude` must be on your PATH)

## Install

```bash
git clone https://github.com/benthomasson/sd-architect-backend.git
cd sd-architect-backend
pip install .
```

Or with uv:

```bash
uv pip install .
```

## Start

```bash
python server.py
```

The server listens on `ws://localhost:8765`. Open [sd.ftl2.com](https://sd.ftl2.com), click **Chat**, and the panel connects automatically.

## How it works

1. You type a message in the chat panel (e.g. "add a Redis cache connected to the API")
2. The frontend sends the message + current architecture JSON over WebSocket
3. The backend builds a prompt with the architecture schema reference and calls `claude -p`
4. Claude returns the updated architecture JSON
5. The backend sends it back and the diagram updates live

Claude also has access to a belief/knowledge database via tool calls, so you can ask it to build diagrams from a knowledge base (e.g. "build a diagram from the beliefs about the deployment stack").

## Configuration

The WebSocket URL defaults to `ws://localhost:8765`. To use a different host, set `chat-ws` in the browser's localStorage:

```js
localStorage.setItem('chat-ws', 'ws://your-host:8765');
```

The beliefs database path defaults to `~/git/drawing-shell-expert/reasons.db`. Override with the `REASONS_DB` environment variable:

```bash
REASONS_DB=/path/to/reasons.db python server.py
```
