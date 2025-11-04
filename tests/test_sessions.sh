#!/bin/bash

echo "🧪 Testing Chat Sessions API..."
echo ""

# Login
echo "1️⃣  Logging in as alice..."
LOGIN_RESPONSE=$(curl -s -X POST "http://localhost:8000/auths/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=alicepass123")

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
echo "✅ Logged in! Token: ${TOKEN:0:20}..."
echo ""

# Create session
echo "2️⃣  Creating a new chat session..."
SESSION=$(curl -s -X POST "http://localhost:8000/chat/sessions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Test Chat"}')
echo $SESSION | python3 -m json.tool
SESSION_ID=$(echo $SESSION | python3 -c "import sys, json; print(json.load(sys.stdin)['_id'])")
echo "✅ Session created: $SESSION_ID"
echo ""

# Send message
echo "3️⃣  Sending a message..."
MESSAGE=$(curl -s -X POST "http://localhost:8000/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello, this is a test message!"}')
echo $MESSAGE | python3 -m json.tool
echo "✅ Message sent!"
echo ""

# Get messages
echo "4️⃣  Getting messages..."
curl -s -X GET "http://localhost:8000/chat/sessions/$SESSION_ID/messages" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
echo ""

# Get all sessions
echo "5️⃣  Getting all sessions..."
curl -s -X GET "http://localhost:8000/chat/sessions" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool

echo ""
echo "✅ All tests completed!"
