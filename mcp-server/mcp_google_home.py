#!/usr/bin/env python3
"""
Google Home MCP Server
Provides Google Home/Chromecast device discovery and control via MCP protocol
"""

import asyncio
import json
import logging
import sys
import os
from typing import Any, Optional, List
from datetime import datetime
import pychromecast
from pychromecast.controllers.media import MediaController
from mcp.server import Server
from mcp.types import Tool, TextContent
from mcp.server.stdio import stdio_server
import time

# Configure logging to stderr (MCP uses stdout for protocol)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('google-home-mcp')

class GoogleHomeMCPServer:
    def __init__(self):
        self.server = Server("google-home-mcp-server")
        self.chromecasts: List[pychromecast.Chromecast] = []
        self.last_discovery_time: Optional[float] = None
        self.discovery_timeout = 10  # seconds
        self._setup_handlers()
        logger.info("🏠 Google Home MCP Server initialized")

    def _setup_handlers(self):
        """Setup MCP request handlers"""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available Google Home tools"""
            return [
                Tool(
                    name="discover_devices",
                    description="Discover all Google Home/Chromecast devices on the local network",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "timeout": {
                                "type": "number",
                                "description": "Discovery timeout in seconds (default: 10)",
                                "default": 10
                            }
                        }
                    }
                ),
                Tool(
                    name="list_devices",
                    description="List all previously discovered Google Home/Chromecast devices",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="get_device_status",
                    description="Get current status of a specific Google Home device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the Google Home device"
                            }
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="play_media",
                    description="Play media (audio/video URL) on a Google Home device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the Google Home device"
                            },
                            "media_url": {
                                "type": "string",
                                "description": "URL of the media to play (mp3, mp4, etc.)"
                            },
                            "content_type": {
                                "type": "string",
                                "description": "MIME type of the media (e.g., 'audio/mp3', 'video/mp4')",
                                "default": "audio/mp3"
                            },
                            "title": {
                                "type": "string",
                                "description": "Title to display (optional)"
                            }
                        },
                        "required": ["device_name", "media_url"]
                    }
                ),
                Tool(
                    name="pause_media",
                    description="Pause playback on a Google Home device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the Google Home device"
                            }
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="resume_media",
                    description="Resume playback on a Google Home device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the Google Home device"
                            }
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="stop_media",
                    description="Stop playback on a Google Home device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the Google Home device"
                            }
                        },
                        "required": ["device_name"]
                    }
                ),
                Tool(
                    name="set_volume",
                    description="Set volume level on a Google Home device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the Google Home device"
                            },
                            "volume": {
                                "type": "number",
                                "description": "Volume level (0.0 to 1.0)",
                                "minimum": 0.0,
                                "maximum": 1.0
                            }
                        },
                        "required": ["device_name", "volume"]
                    }
                ),
                Tool(
                    name="speak_text",
                    description="Use Google TTS to speak text on a Google Home device",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "device_name": {
                                "type": "string",
                                "description": "Name of the Google Home device"
                            },
                            "text": {
                                "type": "string",
                                "description": "Text to speak"
                            },
                            "language": {
                                "type": "string",
                                "description": "Language code (e.g., 'en', 'vi', 'en-US', 'vi-VN')",
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
                if name == "discover_devices":
                    result = await self.discover_devices(arguments)
                elif name == "list_devices":
                    result = await self.list_devices()
                elif name == "get_device_status":
                    result = await self.get_device_status(arguments)
                elif name == "play_media":
                    result = await self.play_media(arguments)
                elif name == "pause_media":
                    result = await self.pause_media(arguments)
                elif name == "resume_media":
                    result = await self.resume_media(arguments)
                elif name == "stop_media":
                    result = await self.stop_media(arguments)
                elif name == "set_volume":
                    result = await self.set_volume(arguments)
                elif name == "speak_text":
                    result = await self.speak_text(arguments)
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

    async def discover_devices(self, args: dict) -> dict:
        """Discover Google Home/Chromecast devices on the network"""
        timeout = args.get("timeout", 10)
        
        try:
            logger.info(f"🔍 Discovering Google Home devices (timeout: {timeout}s)...")
            
            # Run discovery in a thread to avoid blocking
            loop = asyncio.get_event_loop()
            chromecasts, browser = await loop.run_in_executor(
                None,
                lambda: pychromecast.get_chromecasts(timeout=timeout)
            )
            
            self.chromecasts = list(chromecasts)
            self.last_discovery_time = time.time()
            
            # Stop the browser
            if browser:
                browser.stop_discovery()
            
            devices = []
            for cast in self.chromecasts:
                try:
                    cast.wait()
                    device_info = {
                        "name": cast.name,
                        "friendly_name": cast.device.friendly_name,
                        "model": cast.model_name,
                        "manufacturer": cast.device.manufacturer,
                        "uuid": str(cast.uuid),
                        "host": cast.host,
                        "port": cast.port,
                        "cast_type": cast.cast_type
                    }
                    devices.append(device_info)
                except Exception as e:
                    logger.warning(f"Error getting info for device: {e}")
                    continue
            
            logger.info(f"✅ Found {len(devices)} device(s)")
            
            return {
                "success": True,
                "device_count": len(devices),
                "devices": devices,
                "message": f"Discovered {len(devices)} Google Home/Chromecast device(s)"
            }
            
        except Exception as e:
            logger.error(f"Discovery error: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Failed to discover devices"
            }

    async def list_devices(self) -> dict:
        """List previously discovered devices"""
        try:
            if not self.chromecasts:
                return {
                    "success": False,
                    "message": "No devices found. Please run discover_devices first.",
                    "devices": []
                }
            
            devices = []
            for cast in self.chromecasts:
                try:
                    devices.append({
                        "name": cast.name,
                        "model": cast.model_name,
                        "host": cast.host,
                        "uuid": str(cast.uuid)
                    })
                except:
                    continue
            
            discovery_time = datetime.fromtimestamp(self.last_discovery_time).strftime("%Y-%m-%d %H:%M:%S") if self.last_discovery_time else "Never"
            
            return {
                "success": True,
                "device_count": len(devices),
                "devices": devices,
                "last_discovery": discovery_time,
                "message": f"Found {len(devices)} cached device(s)"
            }
            
        except Exception as e:
            logger.error(f"List devices error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _find_device(self, device_name: str) -> Optional[pychromecast.Chromecast]:
        """Find a device by name"""
        for cast in self.chromecasts:
            if cast.name.lower() == device_name.lower() or cast.device.friendly_name.lower() == device_name.lower():
                return cast
        return None

    async def get_device_status(self, args: dict) -> dict:
        """Get status of a specific device"""
        device_name = args.get("device_name", "")
        
        try:
            cast = self._find_device(device_name)
            if not cast:
                return {
                    "success": False,
                    "error": f"Device '{device_name}' not found. Please run discover_devices first."
                }
            
            cast.wait()
            
            status = {
                "name": cast.name,
                "model": cast.model_name,
                "is_idle": cast.is_idle,
                "app_id": cast.app_id,
                "app_display_name": cast.app_display_name,
                "volume_level": cast.status.volume_level,
                "volume_muted": cast.status.volume_muted
            }
            
            # Get media status if available
            if cast.media_controller and cast.media_controller.status:
                media_status = cast.media_controller.status
                status["media"] = {
                    "content_id": media_status.content_id,
                    "content_type": media_status.content_type,
                    "title": media_status.title,
                    "artist": media_status.artist,
                    "album": media_status.album_name,
                    "player_state": media_status.player_state,
                    "duration": media_status.duration,
                    "current_time": media_status.current_time
                }
            
            return {
                "success": True,
                "status": status,
                "message": f"Status retrieved for {device_name}"
            }
            
        except Exception as e:
            logger.error(f"Get status error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def play_media(self, args: dict) -> dict:
        """Play media on a device"""
        device_name = args.get("device_name", "")
        media_url = args.get("media_url", "")
        content_type = args.get("content_type", "audio/mp3")
        title = args.get("title", "")
        
        try:
            cast = self._find_device(device_name)
            if not cast:
                return {
                    "success": False,
                    "error": f"Device '{device_name}' not found"
                }
            
            cast.wait()
            mc = cast.media_controller
            
            logger.info(f"🎵 Playing {media_url} on {device_name}")
            
            # Play the media
            mc.play_media(media_url, content_type, title=title)
            mc.block_until_active()
            
            return {
                "success": True,
                "device": device_name,
                "media_url": media_url,
                "message": f"Playing media on {device_name}"
            }
            
        except Exception as e:
            logger.error(f"Play media error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def pause_media(self, args: dict) -> dict:
        """Pause media playback"""
        device_name = args.get("device_name", "")
        
        try:
            cast = self._find_device(device_name)
            if not cast:
                return {
                    "success": False,
                    "error": f"Device '{device_name}' not found"
                }
            
            cast.wait()
            cast.media_controller.pause()
            
            return {
                "success": True,
                "message": f"Paused playback on {device_name}"
            }
            
        except Exception as e:
            logger.error(f"Pause error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def resume_media(self, args: dict) -> dict:
        """Resume media playback"""
        device_name = args.get("device_name", "")
        
        try:
            cast = self._find_device(device_name)
            if not cast:
                return {
                    "success": False,
                    "error": f"Device '{device_name}' not found"
                }
            
            cast.wait()
            cast.media_controller.play()
            
            return {
                "success": True,
                "message": f"Resumed playback on {device_name}"
            }
            
        except Exception as e:
            logger.error(f"Resume error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def stop_media(self, args: dict) -> dict:
        """Stop media playback"""
        device_name = args.get("device_name", "")
        
        try:
            cast = self._find_device(device_name)
            if not cast:
                return {
                    "success": False,
                    "error": f"Device '{device_name}' not found"
                }
            
            cast.wait()
            cast.media_controller.stop()
            
            return {
                "success": True,
                "message": f"Stopped playback on {device_name}"
            }
            
        except Exception as e:
            logger.error(f"Stop error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def set_volume(self, args: dict) -> dict:
        """Set volume level"""
        device_name = args.get("device_name", "")
        volume = args.get("volume", 0.5)
        
        try:
            cast = self._find_device(device_name)
            if not cast:
                return {
                    "success": False,
                    "error": f"Device '{device_name}' not found"
                }
            
            cast.wait()
            cast.set_volume(volume)
            
            return {
                "success": True,
                "device": device_name,
                "volume": volume,
                "message": f"Set volume to {int(volume * 100)}% on {device_name}"
            }
            
        except Exception as e:
            logger.error(f"Set volume error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def speak_text(self, args: dict) -> dict:
        """Use Google TTS to speak text"""
        device_name = args.get("device_name", "")
        text = args.get("text", "")
        language = args.get("language", "vi-VN")
        
        try:
            cast = self._find_device(device_name)
            if not cast:
                return {
                    "success": False,
                    "error": f"Device '{device_name}' not found"
                }
            
            # Use Google TTS API
            from urllib.parse import quote
            tts_url = f"https://translate.google.com/translate_tts?ie=UTF-8&client=tw-ob&tl={language}&q={quote(text)}"
            
            cast.wait()
            mc = cast.media_controller
            
            logger.info(f"🗣️ Speaking on {device_name}: {text}")
            
            mc.play_media(tts_url, "audio/mp3")
            mc.block_until_active()
            
            return {
                "success": True,
                "device": device_name,
                "text": text,
                "language": language,
                "message": f"Speaking text on {device_name}"
            }
            
        except Exception as e:
            logger.error(f"Speak text error: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def run(self):
        """Run the MCP server"""
        logger.info("🚀 Starting Google Home MCP Server...")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )

async def main():
    """Main entry point"""
    server = GoogleHomeMCPServer()
    await server.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server interrupted by user")
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        sys.exit(1)
