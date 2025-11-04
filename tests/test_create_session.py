#!/usr/bin/env python3
import requests
import json

API_URL = "http://localhost:8000"

# Login
print("1. Logging in as alice...")
response = requests.post(
    f"{API_URL}/auths/login",
    data={"username": "alice", "password": "alicepass123"},
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code != 200:
    print(f"❌ Login failed: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
token = data["access_token"]
print(f"✅ Login successful! Token: {token[:20]}...")
print()

# Create session
print("2. Creating a chat session...")
response = requests.post(
    f"{API_URL}/chat/sessions",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={"title": "My Test Chat"}
)

print(f"Status Code: {response.status_code}")
print("Response:")
print(json.dumps(response.json(), indent=2))
print()

if response.status_code == 201:
    session_id = response.json()["_id"]
    print(f"✅ Session created successfully!")
    print(f"Session ID: {session_id}")

    # Send a message
    print()
    print("3. Sending a message...")
    response = requests.post(
        f"{API_URL}/chat/sessions/{session_id}/messages",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        json={"content": "Hello, this is my first message!"}
    )

    print(f"Status Code: {response.status_code}")
    print("Response:")
    print(json.dumps(response.json(), indent=2))

    if response.status_code == 201:
        print()
        print("✅ Message sent successfully!")
        print()
        print("🎉 All tests passed! The chat sessions feature is working!")
else:
    print(f"❌ Session creation failed")
