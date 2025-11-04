#!/usr/bin/env python3
"""
Simple WebSocket test script for the chat feature.
"""
import asyncio
import json
import websockets
import requests

API_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000"

async def test_websocket():
    print("🧪 Testing WebSocket Connection...")
    print()

    # Step 1: Login to get token
    print("1️⃣  Logging in as 'alice'...")
    response = requests.post(
        f"{API_URL}/auths/login",
        data={"username": "alice", "password": "alicepass123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )

    if response.status_code != 200:
        print(f"❌ Login failed: {response.text}")
        return

    data = response.json()
    access_token = data["access_token"]
    print(f"✅ Login successful! Token: {access_token[:20]}...")
    print()

    # Step 2: Connect to WebSocket
    print("2️⃣  Connecting to WebSocket...")
    ws_url = f"{WS_URL}/chat/ws/general?token={access_token}"

    try:
        async with websockets.connect(ws_url) as websocket:
            print("✅ WebSocket connected!")
            print()

            # Step 3: Send a test message
            print("3️⃣  Sending test message...")
            test_message = {"content": "Hello from test script! 🚀"}
            await websocket.send(json.dumps(test_message))
            print(f"✅ Message sent: {test_message['content']}")
            print()

            # Step 4: Wait for response
            print("4️⃣  Waiting for messages...")
            try:
                # Listen for a few messages
                for i in range(3):
                    message = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(message)
                    print(f"📨 Received: {data.get('type')} - {data.get('content', data.get('username', ''))}")
            except asyncio.TimeoutError:
                print("⏱️  Timeout waiting for messages")

            print()
            print("✅ WebSocket test completed successfully!")

    except websockets.exceptions.InvalidStatusCode as e:
        print(f"❌ WebSocket connection failed with status code: {e.status_code}")
        print(f"   Response: {e.response}")
    except Exception as e:
        print(f"❌ WebSocket error: {type(e).__name__}: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
