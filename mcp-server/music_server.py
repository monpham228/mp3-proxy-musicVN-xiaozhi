#!/usr/bin/env python3
"""
Xiaozhi Music MCP Server
Provides music search, streaming, lyrics, financial data and weather functionality via MCP protocol
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Optional
from datetime import datetime
import httpx
from mcp.server import Server
from mcp.types import Tool, TextContent, CallToolResult
from mcp.server.stdio import stdio_server

# Configure logging to stderr (MCP uses stdout for protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('xiaozhi-music')

# Adapter URL from environment variable (default to localhost for local development)
ADAPTER_URL = os.getenv("ADAPTER_URL", "https://xiaozhi_music.monpham.work")

# SSL verification - disable for self-signed certificates in development
VERIFY_SSL = os.getenv("VERIFY_SSL", "true").lower() in ("true", "1", "yes")

class XiaozhiMusicServer:
    def __init__(self):
        self.server = Server("xiaozhi-music-mcp-server")
        self.http_client: Optional[httpx.AsyncClient] = None
        self._setup_handlers()
        logger.info(f"📍 Adapter URL: {ADAPTER_URL}")
        logger.info(f"🔒 SSL Verification: {VERIFY_SSL}")

    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available music tools"""
            return [
                # Tool(
                #     name="search_music",
                #     description="Search for music using song name and optional artist",
                #     inputSchema={
                #         "type": "object",
                #         "properties": {
                #             "song": {
                #                 "type": "string",
                #                 "description": "Name of the song to search for"
                #             },
                #             "artist": {
                #                 "type": "string",
                #                 "description": "Artist name (optional)"
                #             }
                #         },
                #         "required": ["song"]
                #     }
                # ),
                # Tool(
                #     name="get_music_stream",
                #     description="Get streaming URL for a specific song",
                #     inputSchema={
                #         "type": "object",
                #         "properties": {
                #             "song": {
                #                 "type": "string",
                #                 "description": "Name of the song"
                #             },
                #             "artist": {
                #                 "type": "string",
                #                 "description": "Artist name (optional)"
                #             }
                #         },
                #         "required": ["song"]
                #     }
                # ),
                # Tool(
                #     name="get_lyrics",
                #     description="Get lyrics for a song",
                #     inputSchema={
                #         "type": "object",
                #         "properties": {
                #             "song": {
                #                 "type": "string",
                #                 "description": "Name of the song"
                #             },
                #             "artist": {
                #                 "type": "string",
                #                 "description": "Artist name (optional)"
                #             }
                #         },
                #         "required": ["song"]
                #     }
                # ),
                Tool(
                    name="get_gold_price",
                    description="Lấy giá vàng trong nước (SJC, PNJ, DOJI, etc.)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_usd_rate",
                    description="Lấy tỷ giá USD/VND (Vietcombank, giá chợ đen)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_bitcoin_price",
                    description="Lấy giá Bitcoin hiện tại (USD và VND)",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
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
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool calls"""
            try:
                if name == "search_music":
                    result = await self.search_music(arguments)
                elif name == "play_music":
                    result = await self.get_audio(arguments)
                elif name == "get_music_stream":
                    result = await self.get_music_stream(arguments)
                elif name == "get_lyrics":
                    result = await self.get_lyrics(arguments)
                elif name == "get_gold_price":
                    result = await self.get_gold_price()
                elif name == "get_usd_rate":
                    result = await self.get_usd_rate()
                elif name == "get_bitcoin_price":
                    result = await self.get_bitcoin_price()
                elif name == "get_weather":
                    result = await self.get_weather(arguments)
                elif name == "adapter_status":
                    result = await self.get_adapter_status()
                else:
                    result = {
                        "success": False,
                        "error": f"Unknown tool: {name}"
                    }
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2, ensure_ascii=False)
                )]
            except Exception as e:
                logger.error(f"Error calling tool {name}: {e}", exc_info=True)
                return [TextContent(
                    type="text",
                    text=json.dumps({
                        "success": False,
                        "error": str(e)
                    }, indent=2)
                )]

    async def search_music(self, args: dict) -> dict:
        """Search for music"""
        song = args.get("song", "")
        artist = args.get("artist", "")
        
        try:
            logger.info(f"🔍 Searching music: '{song}' by '{artist}'")
            
            url = f"{ADAPTER_URL}/stream_pcm"
            params = {"song": song, "artist": artist}
            
            async with httpx.AsyncClient(timeout=30.0, verify=VERIFY_SSL) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                return {
                    "success": True,
                    "result": data,
                    "message": f"Found music: {data.get('title', 'Unknown')} by {data.get('artist', 'Unknown')}"
                }
        except Exception as e:
            logger.error(f"Search music error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to search for music: {song}"
            }

    async def get_audio(self, args: dict) -> dict:
        """Get direct audio stream URL"""
        song = args.get("song", "")
        artist = args.get("artist", "")
        
        try:
            logger.info(f"🎶 Getting audio for: '{song}' by '{artist}'")
            
            url = f"{ADAPTER_URL}/audio"
            params = {"song": song, "artist": artist}
            
            async with httpx.AsyncClient(timeout=30.0, verify=VERIFY_SSL) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("audio_url"):
                    return {
                        "success": True,
                        "title": data.get("title"),
                        "artist": data.get("artist"),
                        "audio_url": data.get("audio_url"),
                        "message": f"Audio URL ready for: {data.get('title')}"
                    }
                else:
                    raise Exception("No audio URL in response")
        except Exception as e:
            logger.error(f"Get audio error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get audio for: {song}"
            }

    async def get_music_stream(self, args: dict) -> dict:
        """Get music streaming URL"""
        song = args.get("song", "")
        artist = args.get("artist", "")
        
        try:
            logger.info(f"🎵 Getting stream for: '{song}' by '{artist}'")
            
            url = f"{ADAPTER_URL}/stream_pcm"
            params = {"song": song, "artist": artist}
            
            async with httpx.AsyncClient(timeout=30.0, verify=VERIFY_SSL) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
                
                if data.get("audio_url"):
                    full_audio_url = f"{ADAPTER_URL}{data['audio_url']}"
                    
                    return {
                        "success": True,
                        "title": data.get("title"),
                        "artist": data.get("artist"),
                        "audio_url": full_audio_url,
                        "duration": data.get("duration"),
                        "thumbnail": data.get("thumbnail"),
                        "message": f"Stream URL ready for: {data.get('title')}"
                    }
                else:
                    raise Exception("No audio URL in response")
        except Exception as e:
            logger.error(f"Get stream error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get stream for: {song}"
            }

    async def get_lyrics(self, args: dict) -> dict:
        """Get song lyrics"""
        song = args.get("song", "")
        artist = args.get("artist", "")
        
        try:
            logger.info(f"📝 Getting lyrics for: '{song}' by '{artist}'")
            
            # First get song info
            search_url = f"{ADAPTER_URL}/stream_pcm"
            params = {"song": song, "artist": artist}
            
            async with httpx.AsyncClient(timeout=30.0, verify=VERIFY_SSL) as client:
                search_response = await client.get(search_url, params=params)
                search_response.raise_for_status()
                search_data = search_response.json()
                
                if search_data.get("lyric_url"):
                    full_lyric_url = f"{ADAPTER_URL}{search_data['lyric_url']}"
                    
                    # Get lyrics content
                    lyric_response = await client.get(full_lyric_url, timeout=15.0)
                    lyric_response.raise_for_status()
                    lyrics_data = lyric_response.json()
                    
                    return {
                        "success": True,
                        "title": search_data.get("title"),
                        "artist": search_data.get("artist"),
                        "lyrics": lyrics_data,
                        "message": f"Lyrics found for: {search_data.get('title')}"
                    }
                else:
                    raise Exception("No lyric URL in response")
        except Exception as e:
            logger.error(f"Get lyrics error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to get lyrics for: {song}"
            }

    async def get_gold_price(self) -> dict:
        """Lấy giá vàng trong nước từ API BTMC"""
        try:
            logger.info("💰 Getting gold prices from BTMC...")
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # API giá vàng BTMC (Bảo Tín Minh Châu)
                response = await client.get(
                    "http://api.btmc.vn/api/BTMCAPI/getpricebtmc",
                    params={"key": "3kd8ub1llcg9t45hnoh8hmn7t5kc2v"}
                )
                response.raise_for_status()
                data = response.json()
                
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Parse BTMC response - structure is DataList.Data array
                if data and isinstance(data, dict) and "DataList" in data:
                    data_list = data["DataList"].get("Data", [])
                    
                    if not data_list or not isinstance(data_list, list):
                        raise Exception("No data in BTMC response")
                    
                    # Get the latest entries (first occurrence of each type)
                    sjc_data = None
                    nhan_tron_data = None
                    seen_types = set()
                    
                    for item in data_list:
                        # Each item has numbered attributes like @n_1, @n_2, etc.
                        # We need to find the correct attribute number for this row
                        row = item.get("@row", "1")
                        
                        # Get the name, buy price, and sell price using the row number
                        name_key = f"@n_{row}"
                        buy_key = f"@pb_{row}"
                        sell_key = f"@ps_{row}"
                        date_key = f"@d_{row}"
                        purity_key = f"@h_{row}"
                        
                        name = item.get(name_key, "")
                        buy_price = item.get(buy_key, "0")
                        sell_price = item.get(sell_key, "0")
                        update_date = item.get(date_key, "")
                        purity = item.get(purity_key, "")
                        
                        # Look for VÀNG MIẾNG SJC (most recent one)
                        if "SJC" in name.upper() and "VÀNG MIẾNG" in name.upper():
                            if "SJC" not in seen_types:
                                sjc_data = {
                                    "type": "VÀNG MIẾNG SJC",
                                    "purity": purity,
                                    "buy": f"{int(buy_price):,}",
                                    "sell": f"{int(sell_price):,}",
                                    "updated": update_date
                                }
                                seen_types.add("SJC")
                        
                        # Look for NHẪN TRÒN TRƠN (most recent one)
                        if "NHẪN TRÒN TRƠN" in name.upper():
                            if "NHAN_TRON" not in seen_types:
                                nhan_tron_data = {
                                    "type": "NHẪN TRÒN TRƠN",
                                    "purity": purity,
                                    "buy": f"{int(buy_price):,}",
                                    "sell": f"{int(sell_price):,}",
                                    "updated": update_date
                                }
                                seen_types.add("NHAN_TRON")
                    
                    # Build result with the important items
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
                            "note": "Đơn vị: VNĐ/lượng",
                            "url": "https://www.btmc.vn/gia-vang"
                        }
                    else:
                        raise Exception("SJC or NHẪN TRÒN TRƠN not found in response")
                else:
                    raise Exception("Invalid response structure from BTMC API")
                    
        except Exception as e:
            logger.error(f"Get gold price error: {e}")
            # Fallback to static data with sources
            current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
            return {
                "success": False,
                "error": str(e),
                "timestamp": current_time,
                "message": "Không thể lấy giá vàng từ API. Vui lòng kiểm tra trực tiếp tại các nguồn sau:",
                "sources": {
                    "sjc": "https://sjc.com.vn/giavang",
                    "pnj": "https://www.pnj.com.vn/blog/gia-vang/",
                    "doji": "https://doji.vn/gia-vang-hom-nay",
                    "btmc": "https://www.btmc.vn/gia-vang"
                }
            }

    async def get_usd_rate(self) -> dict:
        """Lấy tỷ giá USD/VND"""
        try:
            logger.info("💵 Getting USD/VND rate...")
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # API tỷ giá Vietcombank
                response = await client.get("https://portal.vietcombank.com.vn/Usercontrols/TVPortal.TyGia/pXML.aspx?b=10")
                response.raise_for_status()
                
                # Parse XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.text)
                
                usd_data = None
                for exrate in root.findall('.//Exrate'):
                    if exrate.get('CurrencyCode') == 'USD':
                        usd_data = {
                            "currency": "USD",
                            "buy_cash": exrate.get('Buy'),
                            "buy_transfer": exrate.get('Transfer'),
                            "sell": exrate.get('Sell')
                        }
                        break
                
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                if usd_data:
                    return {
                        "success": True,
                        "timestamp": current_time,
                        "bank": "Vietcombank",
                        "data": usd_data,
                        "message": f"Tỷ giá USD/VND - Vietcombank lúc {current_time}"
                    }
                else:
                    raise Exception("USD rate not found")
        except Exception as e:
            logger.error(f"Get USD rate error: {e}")
            # Fallback to exchange rate API
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get("https://api.exchangerate-api.com/v4/latest/USD")
                    response.raise_for_status()
                    data = response.json()
                    
                    vnd_rate = data.get("rates", {}).get("VND")
                    current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
                    
                    if vnd_rate:
                        return {
                            "success": True,
                            "timestamp": current_time,
                            "source": "Exchange Rate API",
                            "rate": vnd_rate,
                            "message": f"Tỷ giá USD/VND: {vnd_rate:,.0f} VND"
                        }
            except:
                pass
            
            return {
                "success": False,
                "error": str(e),
                "message": "Không thể lấy tỷ giá USD/VND"
            }

    async def get_bitcoin_price(self) -> dict:
        """Lấy giá Bitcoin hiện tại"""
        try:
            logger.info("₿ Getting Bitcoin price...")
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # CoinGecko API (free, no API key required)
                response = await client.get(
                    "https://api.coingecko.com/api/v3/simple/price",
                    params={
                        "ids": "bitcoin",
                        "vs_currencies": "usd,vnd",
                        "include_24hr_change": "true",
                        "include_market_cap": "true"
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                btc_data = data.get("bitcoin", {})
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                return {
                    "success": True,
                    "timestamp": current_time,
                    "price_usd": btc_data.get("usd"),
                    "price_vnd": btc_data.get("vnd"),
                    "change_24h": btc_data.get("usd_24h_change"),
                    "market_cap_usd": btc_data.get("usd_market_cap"),
                    "message": f"Bitcoin: ${btc_data.get('usd'):,.2f} USD ({btc_data.get('vnd'):,.0f} VND)"
                }
        except Exception as e:
            logger.error(f"Get Bitcoin price error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Không thể lấy giá Bitcoin"
            }

    async def get_weather(self, args: dict) -> dict:
        """Lấy thông tin thời tiết"""
        city = args.get("city", "Ho Chi Minh")
        
        # Normalize city name
        if city.lower() in ["cao lanh", "cao lãnh"]:
            city_name = "Cao Lanh"
            lat, lon = 10.4606, 105.6328  # Cao Lãnh coordinates
        else:  # Default to Ho Chi Minh
            city_name = "Ho Chi Minh City"
            lat, lon = 10.8231, 106.6297  # HCM coordinates
        
        try:
            logger.info(f"🌤️ Getting weather for {city_name}...")
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                # Open-Meteo API (free, no API key required)
                response = await client.get(
                    "https://api.open-meteo.com/v1/forecast",
                    params={
                        "latitude": lat,
                        "longitude": lon,
                        "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
                        "timezone": "Asia/Bangkok",
                        "forecast_days": 1
                    }
                )
                response.raise_for_status()
                data = response.json()
                
                current = data.get("current", {})
                current_time = datetime.now().strftime("%d/%m/%Y %H:%M")
                
                # Weather code descriptions
                weather_codes = {
                    0: "Quang đãng",
                    1: "Chủ yếu quang đãng",
                    2: "Một phần có mây",
                    3: "U ám",
                    45: "Sương mù",
                    48: "Sương mù kết tủa",
                    51: "Mưa phùn nhẹ",
                    53: "Mưa phùn vừa",
                    55: "Mưa phùn dày đặc",
                    61: "Mưa nhỏ",
                    63: "Mưa vừa",
                    65: "Mưa to",
                    80: "Mưa rào nhẹ",
                    81: "Mưa rào vừa",
                    82: "Mưa rào to",
                    95: "Dông",
                    96: "Dông có mưa đá"
                }
                
                weather_code = current.get("weather_code", 0)
                weather_desc = weather_codes.get(weather_code, "Không xác định")
                
                return {
                    "success": True,
                    "city": city_name,
                    "timestamp": current_time,
                    "temperature": current.get("temperature_2m"),
                    "feels_like": current.get("apparent_temperature"),
                    "humidity": current.get("relative_humidity_2m"),
                    "precipitation": current.get("precipitation"),
                    "wind_speed": current.get("wind_speed_10m"),
                    "weather": weather_desc,
                    "message": f"{city_name}: {current.get('temperature_2m')}°C, {weather_desc}"
                }
        except Exception as e:
            logger.error(f"Get weather error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"Không thể lấy thông tin thời tiết cho {city_name}"
            }

    async def get_adapter_status(self) -> dict:
        """Check adapter service status"""
        try:
            async with httpx.AsyncClient(timeout=5.0, verify=VERIFY_SSL) as client:
                response = await client.get(f"{ADAPTER_URL}/health")
                response.raise_for_status()
                
                return {
                    "success": True,
                    "adapter_url": ADAPTER_URL,
                    "status": "connected",
                    "message": "Adapter service is running"
                }
        except Exception as e:
            return {
                "success": False,
                "adapter_url": ADAPTER_URL,
                "status": "disconnected",
                "error": str(e),
                "message": "Failed to connect to adapter service"
            }

    async def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting Xiaozhi Music MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point"""
    server = XiaozhiMusicServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)