#!/usr/bin/env python3
"""
Unified MCP Server
Provides music, weather, financial data, and Google Home control via MCP protocol
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Optional, List
from datetime import datetime
import httpx
import pychromecast
import time
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server

# Configure logging to stderr (MCP uses stdout for protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('unified-mcp')

# Adapter URL from environment variable
ADAPTER_URL = os.getenv("ADAPTER_URL", "https://xiaozhi_music.monpham.work")
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() in ("true", "1", "yes")

class UnifiedMCPServer:
    def __init__(self):
        self.server = Server("unified-mcp-server")
        self.chromecasts: List[pychromecast.Chromecast] = []
        self.last_discovery_time: Optional[float] = None
        self._setup_handlers()
        logger.info(f"📍 Adapter URL: {ADAPTER_URL}")
        logger.info(f"🔒 SSL Verification: {VERIFY_SSL}")

    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List all available tools"""
            return [
                # Financial & Weather Tools
                Tool(
                    name="get_gold_price",
                    description="Lấy giá vàng trong nước (SJC, PNJ, DOJI, etc.)",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_usd_rate",
                    description="Lấy tỷ giá USD/VND (Vietcombank, giá chợ đen)",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_bitcoin_price",
                    description="Lấy giá Bitcoin hiện tại (USD và VND)",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="get_weather",
                    description="Lấy thông tin thời tiết cho khu vực Cao Lãnh hoặc TP. Hồ Chí Minh",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "Tên thành phố: 'Cao Lãnh' hoặc 'Ho Chi Minh'",
                                "enum": ["Cao Lãnh", "Ho Chi Minh", "Cao Lanh", "HCM", "Saigon"]
                            }
                        },
                        "required": ["city"]
                    }
                ),
                Tool(
                    name="adapter_status",
                    description="Check adapter service connection status",
                    inputSchema={"type": "object", "properties": {}}
                ),
                # Google Home Tools
                Tool(
                    name="discover_google_home",
                    description="Khám phá thiết bị Google Home/Chromecast trên mạng",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timeout": {
                                "type": "number",
                                "description": "Thời gian chờ (giây, mặc định: 10)",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="list_google_home",
                    description="Liệt kê các thiết bị Google Home đã tìm thấy",
                    inputSchema={"type": "object", "properties": {}}
                ),
                Tool(
                    name="google_home_status",
                    description="Kiểm tra trạng thái thiết bị Google Home",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Tên thiết bị Google Home"
                            }
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="play_on_google_home",
                    description="Phát nhạc/audio trên Google Home",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Tên thiết bị Google Home"
                            },
                            "media_url": {
                                "type": "string",
                                "description": "URL của file nhạc/audio (mp3, mp4, etc.)"
                            },
                            "content_type": {
                                "type": "string",
                                "description": "MIME type (e.g., 'audio/mp3')",
                                "default": "audio/mp3"
                            },
                            "title": {
                                "type": "string",
                                "description": "Tiêu đề hiển thị"
                            }
                        },
                        "required": ["device_name", "media_url"]
                    }
                ),
                Tool(
                    name="google_home_pause",
                    description="Tạm dừng phát nhạc trên Google Home",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "Tên thiết bị"}
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="google_home_resume",
                    description="Tiếp tục phát nhạc trên Google Home",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "Tên thiết bị"}
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="google_home_stop",
                    description="Dừng phát nhạc trên Google Home",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "Tên thiết bị"}
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="google_home_volume",
                    description="Điều chỉnh âm lượng Google Home",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "Tên thiết bị"},
                            "volume": {
                                "type": "number",
                                "description": "Mức âm lượng (0.0 - 1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["device_name", "volume"]
                    }
                ),
                Tool(
                    name="google_home_speak",
                    description="Dùng Google TTS để nói văn bản trên Google Home",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {"type": "string", "description": "Tên thiết bị"},
                            "text": {"type": "string", "description": "Văn bản cần nói"},
                            "language": {
                                "type": "string",
                                "description": "Mã ngôn ngữ (vi-VN, en-US, etc.)",
                                "default": "vi-VN"
                            }
                        },
                        "required": ["device_name", "text"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls"""
            try:
                # Financial & Weather
                if name == "get_gold_price":
                    result = await self.get_gold_price()
                elif name == "get_usd_rate":
                    result = await self.get_usd_rate()
                elif name == "get_bitcoin_price":
                    result = await self.get_bitcoin_price()
                elif name == "get_weather":
                    result = await self.get_weather(arguments)
                elif name == "adapter_status":
                    result = await self.get_adapter_status()
                # Google Home
                elif name == "discover_google_home":
                    result = await self.discover_devices(arguments)
                elif name == "list_google_home":
                    result = await self.list_devices()
                elif name == "google_home_status":
                    result = await self.get_device_status(arguments)
                elif name == "play_on_google_home":
                    result = await self.play_media(arguments)
                elif name == "google_home_pause":
                    result = await self.pause_media(arguments)
                elif name == "google_home_resume":
                    result = await self.resume_media(arguments)
                elif name == "google_home_stop":
                    result = await self.stop_media(arguments)
                elif name == "google_home_volume":
                    result = await self.set_volume(arguments)
                elif name == "google_home_speak":
                    result = await self.speak_text(arguments)
                else:
                    result = {"success": False, "error": f"Unknown tool: {name}"}
                
                return [TextContent(type="text", text=json.dumps(result, indent=2, ensure_ascii=False))]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}", exc_info=True)
                return [TextContent(type="text", text=json.dumps({"success": False, "error": str(e)}, indent=2))]

    # ========== Financial & Weather Methods ==========
    
    async def get_gold_price(self) -> dict:
        """Lấy giá vàng trong nước từ API BTMC"""
        try:
            logger.info("💰 Getting gold prices from BTMC...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "http://api.btmc.vn/api/BTMCAPI/getpricebtmc",
                    params={"key": "3kd8ub1llcg9t45hnoh8hmn7t5kc2v"}
                )
                response.raise_for_status()
                data = response.json()
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                if data and isinstance(data, dict) and "DataList" in data:
                    data_list = data["DataList"].get("Data", [])
                    if not data_list:
                        raise Exception("No data in BTMC response")
                    
                    sjc_data = None
                    nhan_tron_data = None
                    seen_types = set()
                    
                    for item in data_list:
                        row = item.get("@row", "1")
                        name = item.get(f"@n_{row}", "")
                        buy_price = item.get(f"@pb_{row}", "0")
                        sell_price = item.get(f"@ps_{row}", "0")
                        update_date = item.get(f"@d_{row}", "")
                        purity = item.get(f"@h_{row}", "")
                        
                        if "SJC" in name.upper() and "VÀNG MIẾNG" in name.upper() and "SJC" not in seen_types:
                            sjc_data = {
                                "type": "VÀNG MIẾNG SJC",
                                "purity": purity,
                                "buy": f"{int(buy_price):,}",
                                "sell": f"{int(sell_price):,}",
                                "updated": update_date
                            }
                            seen_types.add("SJC")
                        
                        if "NHẪN TRÒN TRƠN" in name.upper() and "NHAN_TRON" not in seen_types:
                            nhan_tron_data = {
                                "type": "NHẪN TRÒN TRƠN",
                                "purity": purity,
                                "buy": f"{int(buy_price):,}",
                                "sell": f"{int(sell_price):,}",
                                "updated": update_date
                            }
                            seen_types.add("NHAN_TRON")
                    
                    gold_data = []
                    if sjc_data:
                        gold_data.append(sjc_data)
                    if nhan_tron_data:
                        gold_data.append(nhan_tron_data)
                    
                    if gold_data:
                        return {
                            "success": True,
                            "timestamp": current_time,
                            "source": "Bảo Tín Minh Châu (BTMC)",
                            "data": gold_data,
                            "message": f"Cập nhật giá vàng BTMC lúc {current_time}",
                            "note": "Đơn vị: VNĐ/lượng"
                        }
                raise Exception("SJC or NHẪN TRÒN TRƠN not found")
        except Exception as e:
            logger.error(f"Get gold price error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Không thể lấy giá vàng từ API"
            }

    async def get_usd_rate(self) -> dict:
        """Lấy tỷ giá USD/VND"""
        try:
            logger.info("💵 Getting USD/VND rate...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10")
                response.raise_for_status()
                
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                for exrate in root.findall('.//Exrate'):
                    if exrate.get('CurrencyCode') == 'USD':
                        return {
                            "success": True,
                            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
                            "bank": "Vietcombank",
                            "data": {
                                "currency": "USD",
                                "buy_cash": exrate.get('Buy'),
                                "buy_transfer": exrate.get('Transfer'),
                                "sell": exrate.get('Sell')
                            }
                        }
                raise Exception("USD rate not found")
        except Exception as e:
            logger.error(f"Get USD rate error: {e}")
            return {"success": False, "error": str(e)}

    async def get_bitcoin_price(self) -> dict:
        """Lấy giá Bitcoin hiện tại"""
        try:
            logger.info("₿ Getting Bitcoin price...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={"ids": "bitcoin", "vs_currencies": "usd,vnd", "include_24hr_change": "true"}
                )
                response.raise_for_status()
                data = response.json()
                btc_data = data.get("bitcoin", {})
                
                return {
                    "success": True,
                    "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M"),
                    "price_usd": btc_data.get("usd"),
                    "price_vnd": btc_data.get("vnd"),
                    "change_24h": btc_data.get("usd_24h_change"),
                    "message": f"Bitcoin: ${btc_data.get('usd'):,.2f} USD"
                }
        except Exception as e:
            logger.error(f"Get Bitcoin price error: {e}")
            return {"success": False, "error": str(e)}

    async def get_weather(self, args: dict) -> dict:
        """Lấy thông tin thời tiết"""
        city = args.get("city", "Ho Chi Minh")
        
        if city.lower() in ["cao lanh", "cao lãnh"]:
            city_name, lat, lon = "Cao Lanh", 10.4606, 105.6328
        else:
            city_name, lat, lon = "Ho Chi Minh City", 10.8231, 106.6297
        
        try:
            logger.info(f"🌤️ Getting weather for {city_name}...")
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat, "longitude": lon,
                        "current": "temperature_2m,relative_humidity_2m,weather_code",
                        "timezone": "Asia/Bangkok", "forecast_days": 1
                    }
                )
                response.raise_for_status()
                data = response.json()
                current = data.get("current", {})
                
                weather_codes = {
                    0: "Quang đãng", 1: "Chủ yếu quang đãng", 2: "Một phần có mây",
                    3: "U ám", 61: "Mưa nhỏ", 63: "Mưa vừa", 65: "Mưa to", 95: "Dông"
                }
                
                return {
                    "success": True,
                    "city": city_name,
                    "temperature": current.get("temperature_2m"),
                    "humidity": current.get("relative_humidity_2m"),
                    "weather": weather_codes.get(current.get("weather_code", 0), "Không xác định"),
                    "message": f"{city_name}: {current.get('temperature_2m')}°C"
                }
        except Exception as e:
            logger.error(f"Get weather error: {e}")
            return {"success": False, "error": str(e)}

    async def get_adapter_status(self) -> dict:
        """Check adapter service status"""
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=VERIFY_SSL) as client:
                response = await client.get(f"{ADAPTER_URL}/health")
                response.raise_for_status()
                return {"success": True, "adapter_url": ADAPTER_URL, "status": "connected"}
        except Exception as e:
            return {"success": False, "adapter_url": ADAPTER_URL, "status": "disconnected", "error": str(e)}

    # ========== Google Home Methods ==========
    
    async def discover_devices(self, args: dict) -> dict:
        """Khám phá thiết bị Google Home/Chromecast"""
        timeout = args.get("timeout", 10)
        try:
            logger.info(f"🔍 Discovering Google Home devices (timeout: {timeout}s)...")
            loop = asyncio.get_event_loop()
            chromecasts, browser = await loop.run_in_executor(
                None, lambda: pychromecast.get_chromecasts(timeout=timeout)
            )
            
            self.chromecasts = list(chromecasts)
            self.last_discovery_time = time.time()
            
            if browser:
                browser.stop_discovery()
            
            devices = []
            for cast in self.chromecasts:
                try:
                    cast.wait()
                    devices.append({
                        "name": cast.name,
                        "friendly_name": cast.device.friendly_name,
                        "model": cast.model_name,
                        "host": cast.host,
                        "uuid": str(cast.uuid)
                    })
                except Exception as e:
                    logger.warning(f"Error getting device info: {e}")
            
            logger.info(f"✅ Found {len(devices)} device(s)")
            return {
                "success": True,
                "device_count": len(devices),
                "devices": devices,
                "message": f"Tìm thấy {len(devices)} thiết bị Google Home/Chromecast"
            }
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            return {"success": False, "error": str(e), "message": "Không thể khám phá thiết bị"}

    async def list_devices(self) -> dict:
        """Liệt kê thiết bị đã tìm thấy"""
        if not self.chromecasts:
            return {"success": False, "message": "Chưa có thiết bị. Hãy chạy discover_google_home trước.", "devices": []}
        
        devices = []
        for cast in self.chromecasts:
            try:
                devices.append({"name": cast.name, "model": cast.model_name, "host": cast.host})
            except:
                continue
        
        return {
            "success": True,
            "device_count": len(devices),
            "devices": devices,
            "last_discovery": datetime.fromtimestamp(self.last_discovery_time).strftime("%Y-%m-%d %H:%M:%S") if self.last_discovery_time else "Never"
        }

    def _find_device(self, device_name: str) -> Optional[pychromecast.Chromecast]:
        """Tìm thiết bị theo tên"""
        for cast in self.chromecasts:
            if cast.name.lower() == device_name.lower() or cast.device.friendly_name.lower() == device_name.lower():
                return cast
        return None

    async def get_device_status(self, args: dict) -> dict:
        """Lấy trạng thái thiết bị"""
        device_name = args.get("device_name", "")
        cast = self._find_device(device_name)
        if not cast:
            return {"success": False, "error": f"Không tìm thấy thiết bị '{device_name}'"}
        
        try:
            cast.wait()
            status = {
                "name": cast.name,
                "model": cast.model_name,
                "is_idle": cast.is_idle,
                "app": cast.app_display_name,
                "volume_level": cast.status.volume_level,
                "volume_muted": cast.status.volume_muted
            }
            
            if cast.media_controller and cast.media_controller.status:
                ms = cast.media_controller.status
                status["media"] = {
                    "title": ms.title,
                    "artist": ms.artist,
                    "player_state": ms.player_state,
                    "duration": ms.duration,
                    "current_time": ms.current_time
                }
            
            return {"success": True, "status": status}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def play_media(self, args: dict) -> dict:
        """Phát media trên Google Home"""
        device_name = args.get("device_name", "")
        media_url = args.get("media_url", "")
        content_type = args.get("content_type", "audio/mp3")
        title = args.get("title", "")
        
        cast = self._find_device(device_name)
        if not cast:
            return {"success": False, "error": f"Không tìm thấy thiết bị '{device_name}'"}
        
        try:
            cast.wait()
            logger.info(f"🎵 Playing {media_url} on {device_name}")
            cast.media_controller.play_media(media_url, content_type, title=title)
            cast.media_controller.block_until_active()
            return {"success": True, "message": f"Đang phát trên {device_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def pause_media(self, args: dict) -> dict:
        """Tạm dừng phát"""
        cast = self._find_device(args.get("device_name", ""))
        if not cast:
            return {"success": False, "error": "Không tìm thấy thiết bị"}
        try:
            cast.wait()
            cast.media_controller.pause()
            return {"success": True, "message": "Đã tạm dừng"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def resume_media(self, args: dict) -> dict:
        """Tiếp tục phát"""
        cast = self._find_device(args.get("device_name", ""))
        if not cast:
            return {"success": False, "error": "Không tìm thấy thiết bị"}
        try:
            cast.wait()
            cast.media_controller.play()
            return {"success": True, "message": "Đã tiếp tục phát"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def stop_media(self, args: dict) -> dict:
        """Dừng phát"""
        cast = self._find_device(args.get("device_name", ""))
        if not cast:
            return {"success": False, "error": "Không tìm thấy thiết bị"}
        try:
            cast.wait()
            cast.media_controller.stop()
            return {"success": True, "message": "Đã dừng phát"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def set_volume(self, args: dict) -> dict:
        """Điều chỉnh âm lượng"""
        cast = self._find_device(args.get("device_name", ""))
        volume = args.get("volume", 0.5)
        if not cast:
            return {"success": False, "error": "Không tìm thấy thiết bị"}
        try:
            cast.wait()
            cast.set_volume(volume)
            return {"success": True, "volume": volume, "message": f"Đã đặt âm lượng {int(volume * 100)}%"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def speak_text(self, args: dict) -> dict:
        """Dùng Google TTS để nói văn bản"""
        device_name = args.get("device_name", "")
        text = args.get("text", "")
        language = args.get("language", "vi-VN")
        
        cast = self._find_device(device_name)
        if not cast:
            return {"success": False, "error": f"Không tìm thấy thiết bị '{device_name}'"}
        
        try:
            from urllib.parse import quote
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={language}&q={quote(text)}"
            
            cast.wait()
            logger.info(f"🗣️ Speaking on {device_name}: {text}")
            cast.media_controller.play_media(tts_url, "audio/mp3")
            cast.media_controller.block_until_active()
            return {"success": True, "message": f"Đang nói trên {device_name}"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting Unified MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(read_stream, write_stream, self.server.create_initialization_options())

async def main():
    """Main entry point"""
    server = UnifiedMCPServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
