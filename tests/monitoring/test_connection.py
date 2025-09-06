#!/usr/bin/env python3
"""
Quick connection test for the bridge component.
Tests WebSocket connection to Bun server and basic functionality.
"""

import asyncio
import json
import websockets
from datetime import datetime

async def test_websocket_connection():
    """Test WebSocket connection to Bun server."""
    url = "ws://localhost:4000/stream"
    
    try:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Connecting to {url}...")
        
        async with websockets.connect(url, timeout=5) as websocket:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WebSocket connected successfully!")
            
            # Wait for initial message
            try:
                message = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(message)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] 📨 Received initial data:")
                print(f"  Type: {data.get('type')}")
                if data.get('data'):
                    events = data['data'].get('events', [])
                    metrics = data['data'].get('sessionMetrics', [])
                    insights = data['data'].get('insights', [])
                    print(f"  Events: {len(events)}")
                    print(f"  Session Metrics: {len(metrics)}")
                    print(f"  Insights: {len(insights)}")
                
            except asyncio.TimeoutError:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ⏰ No initial message received (timeout)")
                
            # Send test message
            test_message = {
                "type": "test",
                "timestamp": datetime.now().isoformat()
            }
            await websocket.send(json.dumps(test_message))
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 📤 Sent test message")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ WebSocket test completed successfully!")
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ WebSocket connection failed: {e}")
        return False
        
    return True

async def test_usage_monitor():
    """Test Usage Monitor CLI availability."""
    import subprocess
    import sys
    from pathlib import Path
    
    usage_monitor_path = Path("../Claude-Code-Usage-Monitor").resolve()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Testing Usage Monitor at: {usage_monitor_path}")
    
    if not usage_monitor_path.exists():
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Usage Monitor directory not found")
        return False
        
    try:
        # Test if we can run the CLI
        cmd = [sys.executable, "-c", "import os; print(f'Python path: {os.getcwd()}')"]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=usage_monitor_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=5)
        
        if process.returncode == 0:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ Usage Monitor directory accessible")
            print(f"  Output: {stdout.decode().strip()}")
            return True
        else:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Usage Monitor test failed")
            print(f"  Error: {stderr.decode()}")
            return False
            
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ Usage Monitor test error: {e}")
        return False

async def test_http_endpoints():
    """Test Bun server HTTP endpoints."""
    import httpx
    
    endpoints = [
        "http://localhost:4000",
        "http://localhost:4000/analytics/dashboard",
        "http://localhost:4000/events/recent"
    ]
    
    async with httpx.AsyncClient(timeout=5) as client:
        for endpoint in endpoints:
            try:
                response = await client.get(endpoint)
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ✅ {endpoint} - Status: {response.status_code}")
                
                if endpoint.endswith("/dashboard"):
                    data = response.json()
                    if data.get('success'):
                        summary = data['data']['summary']
                        print(f"  Active Sessions: {summary['activeSessions']}")
                        print(f"  Total Insights: {summary['totalInsights']}")
                        
            except Exception as e:
                print(f"[{datetime.now().strftime('%H:%M:%S')}] ❌ {endpoint} - Error: {e}")

async def main():
    """Run all connection tests."""
    print("🔍 Claude Monitoring Bridge - Connection Tests")
    print("=" * 50)
    
    # Test 1: WebSocket Connection
    print("\n1️⃣ Testing WebSocket Connection to Bun Server...")
    ws_success = await test_websocket_connection()
    
    # Test 2: Usage Monitor
    print("\n2️⃣ Testing Usage Monitor Integration...")
    um_success = await test_usage_monitor()
    
    # Test 3: HTTP Endpoints
    print("\n3️⃣ Testing HTTP Endpoints...")
    await test_http_endpoints()
    
    # Summary
    print("\n📊 Test Summary:")
    print(f"  WebSocket Connection: {'✅ PASS' if ws_success else '❌ FAIL'}")
    print(f"  Usage Monitor Access: {'✅ PASS' if um_success else '❌ FAIL'}")
    
    if ws_success and um_success:
        print("\n🎉 All core integration points are working!")
        print("   Ready to start the bridge component.")
    else:
        print("\n⚠️  Some integration points need attention before starting the bridge.")

if __name__ == "__main__":
    asyncio.run(main())