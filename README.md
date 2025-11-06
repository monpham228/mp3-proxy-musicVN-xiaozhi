# Xiaozhi Music MCP Server System

Complete MCP (Model Context Protocol) server system for music search, streaming, and lyrics via Xiaozhi WebSocket API.

## 🏗️ Architecture

```
┌─────────────────┐
│ Xiaozhi Client  │ (WebSocket)
│   (AI Agent)    │
└────────┬────────┘
         │ WSS
         ▼
┌─────────────────┐
│   mcp_pipe.py   │ (WebSocket ↔ stdio bridge)
└────────┬────────┘
         │ stdio
         ▼
┌─────────────────┐
│ music_server.py │ (MCP Server)
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│ xiaozhi-adapter │ (Format converter)
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│    mp3-api      │ (Zing MP3 API)
└─────────────────┘
```

## 🚀 Quick Start

### Initial Setup

**IMPORTANT: Before running, configure your environment variables:**

1. **Copy the example environment file:**
```bash
cp .env.example .env
```

2. **Edit `.env` and add your actual tokens:**
```bash
# Replace YOUR_MCP_TOKEN_HERE with your actual Xiaozhi MCP token
# Replace YOUR_SECRET_KEY_HERE with your actual secret key
nano .env  # or use your preferred editor
```

3. **Never commit the `.env` file to git** - it's already in `.gitignore`

### Using Docker (Recommended)

```bash
# Build and start all services
./manage.sh build
./manage.sh start

# View logs
./manage.sh logs mcp-server

# Check status
./manage.sh status
```

### Manual Setup

1. **Start adapter service:**
```bash
cd adapter
npm install
# Make sure .env file exists in project root
node xiaozhi-adapter.js
```

2. **Start MCP server:**
```bash
cd mcp-server
pip install -r requirements.txt
# Load environment variables from .env file
export $(cat ../.env | xargs)
python mcp_pipe.py
```

## 📦 Services

### 1. mp3-api (Port 5555)
- Zing MP3 API wrapper
- Internal service (not exposed)

### 2. xiaozhi-adapter (Port 5005)
- Converts MP3 API to Xiaozhi format
- Provides PCM streaming for ESP32
- Health check: `http://localhost:5005/health`

### 3. mcp-server
- Python-based MCP server
- Connects to Xiaozhi via WebSocket
- Provides 4 tools: search_music, get_music_stream, get_lyrics, adapter_status

## 🛠️ Management Script

The `manage.sh` script provides easy Docker management:

```bash
./manage.sh build          # Build images
./manage.sh start          # Start services
./manage.sh stop           # Stop services
./manage.sh restart        # Restart services
./manage.sh logs [service] # View logs
./manage.sh status         # Show status
./manage.sh shell [service]# Open shell
./manage.sh rebuild        # Rebuild MCP server
./manage.sh clean          # Remove all
./manage.sh test           # Test dependencies
```

## 🔧 Configuration

### Environment Variables

**Step 1: Copy the example file**
```bash
cp .env.example .env
```

**Step 2: Edit `.env` with your credentials**

Required variables:
```env
# MCP Server Configuration
MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=YOUR_ACTUAL_TOKEN_HERE

# Xiaozhi Adapter Configuration
SECRET_KEY=YOUR_ACTUAL_SECRET_KEY_HERE
```

**Important:** 
- ✅ The `.env` file is gitignored and will NOT be committed
- ✅ The `.env.example` file is tracked and shows the required format
- ⚠️ Never hardcode tokens directly in docker-compose.yml or source code

### MCP Configuration (`mcp-server/mcp_config.json`)

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

## 📡 Available MCP Tools

### Music Tools

#### 1. search_music
Search for music by song name and artist
```json
{
  "song": "Nơi này có anh",
  "artist": "Sơn Tùng MTP"
}
```

#### 2. get_music_stream
Get streaming URL for a song
```json
{
  "song": "Nơi này có anh",
  "artist": "Sơn Tùng MTP"
}
```

#### 3. get_lyrics
Get lyrics for a song
```json
{
  "song": "Nơi này có anh"
}
```

### Financial & Market Tools

#### 4. get_gold_price
Lấy giá vàng trong nước (SJC, PNJ, DOJI, v.v.)
```json
{}
```

**Response includes:**
- Giá vàng các thương hiệu: SJC, PNJ, DOJI, Bảo Tín Minh Châu
- Giá mua vào / bán ra
- Loại vàng: nhẫn, miếng 1 lượng, 5 chỉ, v.v.
- Cập nhật theo thời gian thực

**API Source:** https://api.vietqr.io/v1/gold-price

#### 5. get_usd_rate
Lấy tỷ giá USD/VND từ Vietcombank
```json
{}
```

**Response includes:**
- Giá mua tiền mặt (Buy Cash)
- Giá mua chuyển khoản (Buy Transfer)
- Giá bán (Sell)
- Thời gian cập nhật

**API Source:** Vietcombank Portal (với fallback đến Exchange Rate API)

#### 6. get_bitcoin_price
Lấy giá Bitcoin hiện tại (USD và VND)
```json
{}
```

**Response includes:**
- Giá Bitcoin (USD)
- Giá Bitcoin (VND)
- Thay đổi 24h (%)
- Market cap (USD)

**API Source:** CoinGecko API

### Weather Tools

#### 7. get_weather
Lấy thông tin thời tiết cho Cao Lãnh hoặc TP. Hồ Chí Minh
```json
{
  "city": "Ho Chi Minh"
}
```

**Supported cities:**
- `"Cao Lãnh"` hoặc `"Cao Lanh"` - Cao Lãnh, Đồng Tháp
- `"Ho Chi Minh"`, `"HCM"`, `"Saigon"` - TP. Hồ Chí Minh

**Response includes:**
- Nhiệt độ hiện tại (°C)
- Nhiệt độ cảm nhận
- Độ ẩm (%)
- Lượng mưa (mm)
- Tốc độ gió (km/h)
- Tình trạng thời tiết (bằng tiếng Việt)

**API Source:** Open-Meteo API (free, no API key required)

### System Tools

#### 8. adapter_status
Check adapter service health
```json
{}
```

## 🔄 Reconnection Strategy

The WebSocket pipe automatically reconnects:
- Initial backoff: 1 second
- Maximum backoff: 600 seconds
- Exponential backoff
- Infinite retry attempts

## 📊 Health Checks

All services include health checks:
- **mp3-api**: 30s interval, HTTP check
- **xiaozhi-adapter**: 30s interval, HTTP check
- **mcp-server**: 30s interval, process check

## 🐛 Debugging

### View logs for specific service
```bash
./manage.sh logs mcp-server
./manage.sh logs xiaozhi-adapter
./manage.sh logs mp3-api
```

### Access container shell
```bash
./manage.sh shell mcp-server
```

### Test MCP server directly
```bash
cd mcp-server
python music_server.py
# In another terminal:
echo '{"jsonrpc":"2.0","method":"tools/list","id":1}' | python music_server.py
```

## 📝 Development

### File Structure
```
.
├── docker-compose.yml          # Main Docker configuration
├── docker-compose.override.yml # Development overrides
├── manage.sh                   # Management script
├── README.md                   # This file
├── adapter/                    # Xiaozhi adapter service
│   ├── package.json
│   └── xiaozhi-adapter.js
├── mcp-server/                 # MCP server
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── mcp_config.json
│   ├── mcp_pipe.py            # WebSocket bridge
│   ├── music_server.py        # MCP server
│   └── README.md
└── mp3-api/                    # MP3 API service
    ├── package.json
    └── server.js
```

### Local Development
```bash
# Start dependencies only
docker-compose up -d mp3-api xiaozhi-adapter

# Run MCP server locally
cd mcp-server
export MCP_ENDPOINT="wss://api.xiaozhi.me/mcp/?token=YOUR_TOKEN"
export ADAPTER_URL="http://localhost:5005"
python mcp_pipe.py
```

## 🔐 Security Notes

### Token Management
- ✅ **DO**: Use `.env` file for tokens (gitignored)
- ✅ **DO**: Use `.env.example` as a template (tracked in git)
- ✅ **DO**: Keep your MCP_ENDPOINT token secure
- ❌ **DON'T**: Commit `.env` files with real tokens
- ❌ **DON'T**: Hardcode tokens in source code
- ❌ **DON'T**: Share tokens publicly

### Before Publishing to GitHub
1. Ensure `.env` is in `.gitignore` ✓
2. Remove any hardcoded tokens from all files ✓
3. Provide `.env.example` with placeholder values ✓
4. Update README with setup instructions ✓
5. Run `git status` to verify `.env` is not tracked

### Rotating Tokens
If your token is compromised:
1. Generate a new token from Xiaozhi API
2. Update your `.env` file
3. Restart services: `./manage.sh restart`

## 📚 References

- [MCP Protocol](https://modelcontextprotocol.io/)
- [MCP Calculator Example](https://github.com/78/mcp-calculator)
- [Xiaozhi API Documentation](https://api.xiaozhi.me/)

## 🤝 Contributing

Feel free to submit issues and enhancement requests!

## 📄 License

MIT