#!/usr/bin/env python3
"""
Test script for Google Home MCP Server
This script tests the connection to Google Home devices on your local network
"""

import asyncio
import json
import sys

# Add the current directory to the path
sys.path.insert(0, '/app')

from mcp_google_home import GoogleHomeMCPServer

async def test_discovery():
    """Test device discovery"""
    print("=" * 60)
    print("🏠 Google Home Device Discovery Test")
    print("=" * 60)
    
    server = GoogleHomeMCPServer()
    
    # Test 1: Discover devices
    print("\n[Test 1] Discovering devices on the network...")
    print("⏳ This may take 10-15 seconds...")
    result = await server.discover_devices({"timeout": 15})
    print("\n📊 Discovery Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("success") and result.get("device_count", 0) > 0:
        print(f"\n✅ Found {result['device_count']} device(s)!")
        
        # Test 2: List devices
        print("\n[Test 2] Listing discovered devices...")
        list_result = await server.list_devices()
        print(json.dumps(list_result, indent=2, ensure_ascii=False))
        
        # Test 3: Get status of first device
        if result["devices"]:
            first_device = result["devices"][0]
            device_name = first_device["name"]
            
            print(f"\n[Test 3] Getting status of '{device_name}'...")
            status_result = await server.get_device_status({"device_name": device_name})
            print(json.dumps(status_result, indent=2, ensure_ascii=False))
            
            # Test 4: Test TTS (optional - uncomment to test)
            print(f"\n[Test 4] Testing text-to-speech on '{device_name}'...")
            print("🔊 This will play audio on your Google Home device!")
            
            # Uncomment the lines below to test TTS
            # tts_result = await server.speak_text({
            #     "device_name": device_name,
            #     "text": "Xin chào, đây là Google Home MCP Server",
            #     "language": "vi-VN"
            # })
            # print(json.dumps(tts_result, indent=2, ensure_ascii=False))
            
            print("ℹ️  TTS test skipped. Uncomment the code to test.")
    else:
        print("\n❌ No devices found on the network!")
        print("\n💡 Troubleshooting tips:")
        print("   1. Make sure your Google Home devices are powered on")
        print("   2. Ensure this container is on the same network as your devices")
        print("   3. Check that mDNS/Bonjour is enabled on your network")
        print("   4. Try using 'host' network mode in docker-compose.yml")
    
    print("\n" + "=" * 60)
    print("✅ Test completed!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        asyncio.run(test_discovery())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
