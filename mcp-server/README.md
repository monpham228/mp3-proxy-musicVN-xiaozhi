# Xiaozhi Music MCP Server

MCP (Model Context Protocol) server that connects to Xiaozhi via WebSocket and provides music functionality.

Based on the [mcp-calculator](https://github.com/78/mcp-calculator) implementation pattern.

## Features

- 🔗 WebSocket connection to Xiaozhi API via pipe transport
- 🎵 Music search and streaming
- 📝 Lyrics retrieval
- 🔄 Automatic reconnection with exponential backoff
- 🎯 MCP protocol compliance
- 🐍 Python-based implementation

## Available Tools

1. **search_music** - Search for music by song name and optional artist
2. **get_music_stream** - Get streaming URL for a specific song
3. **get_lyrics** - Get lyrics for a song
4. **adapter_status** - Check adapter service connection status

## Setup

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create or update `.env` file:

```env
MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=YOUR_TOKEN
ADAPTER_URL=http://localhost:5005
```

Or export directly:

```bash
export MCP_ENDPOINT="wss://api.xiaozhi.me/mcp/?token=YOUR_TOKEN"
```

### 3. Ensure Adapter Service is Running

Make sure your xiaozhi-adapter service is running on port 5005.

## Usage

### Start MCP Server with WebSocket Pipe

Run all configured servers (from `mcp_config.json`):

```bash
python mcp_pipe.py
```

Run a specific server:

```bash
python mcp_pipe.py music_server.py
```

### Direct Server Mode (without WebSocket)

For testing without Xiaozhi WebSocket:

```bash
python music_server.py
```

## Configuration

The `mcp_config.json` file defines available MCP servers:

```json
{
  "mcpServers": {
    "xiaozhi-music": {
      "type": "stdio",
      "command": "python3",
      "args": ["-u", "music_server.py"],
      "env": {
        "ADAPTER_URL": "http://localhost:5005"
      }
    }
  }
}
```

### Configuration Options

- **type**: Transport type (`stdio`)
- **command**: Python interpreter
- **args**: Script and arguments
- **env**: Environment variables for the server process
- **disabled**: Set to `true` to disable a server

## Architecture

```
Xiaozhi Client (WSS) ↔ mcp_pipe.py ↔ music_server.py (stdio) ↔ Adapter Service (HTTP)
```

The system uses:
- **mcp_pipe.py**: WebSocket ↔ stdio pipe with auto-reconnection
- **music_server.py**: MCP server implementing music tools
- **Adapter service**: HTTP API for music operations

## Reconnection

The pipe automatically reconnects to Xiaozhi WebSocket if connection is lost:
- Initial backoff: 1 second
- Maximum backoff: 600 seconds (10 minutes)
- Exponential backoff strategy
- Infinite retry attempts

## Logs

Logs are written to stderr to keep stdout clean for MCP protocol communication.

## Docker Support

The server can also run in Docker (see docker-compose.yml in parent directory).

## Development

### Test the MCP Server Directly

```bash
# Test stdio communication
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python music_server.py
```

### Debug Mode

Set logging level in the scripts for more verbose output.