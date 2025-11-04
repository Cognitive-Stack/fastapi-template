# FastAPI Chat Feature

A real-time chat application built with FastAPI WebSockets and MongoDB.

## Features

- **Real-time messaging** using WebSockets
- **User authentication** required to access chat
- **Message persistence** in MongoDB
- **Room-based chat** (currently "general" room)
- **Modern UI** with gradient design
- **Message history** loaded on login
- **Join/leave notifications**
- **Responsive design**

## Architecture

### Backend Components

1. **WebSocket Router** (`app/routers/chat.py`)
   - WebSocket endpoint: `/chat/ws/{room}`
   - REST endpoint for message history: `/chat/messages/{room}`
   - Message deletion: `/chat/messages/{message_id}`

2. **Models** (`app/models/messages.py`)
   - Message model with user info, content, room, and timestamps

3. **Schemas** (`app/schemas/messages.py`)
   - MessageCreate: For creating new messages
   - MessageResponse: For returning message data

### Frontend

- **Single-page application** (`app/static/chat.html`)
- Pure HTML/CSS/JavaScript (no frameworks)
- Gradient purple theme
- Real-time WebSocket connection

## Usage

### 1. Start the Application

```bash
docker-compose up -d
```

### 2. Access the Chat UI

Open your browser and navigate to:
```
http://localhost:8000/chat-ui
```

### 3. Login with Test Users

Two test users have been created:

**User 1:**
- Username: `testuser`
- Password: `testpass123`

**User 2:**
- Username: `alice`
- Password: `alicepass123`

### 4. Start Chatting

- Open the chat UI in two different browser windows
- Login with different users in each window
- Send messages and see them appear in real-time!

## API Endpoints

### WebSocket Connection

```
ws://localhost:8000/chat/ws/{room}?token={access_token}
```

**Message Format (Send):**
```json
{
  "content": "Hello, world!"
}
```

**Message Format (Receive):**
```json
{
  "type": "message",
  "_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "username": "testuser",
  "content": "Hello, world!",
  "room": "general",
  "created_at": "2025-11-04T10:00:00Z"
}
```

### REST Endpoints

**Get Message History:**
```bash
GET /chat/messages/{room}?limit=50
Authorization: Bearer {access_token}
```

**Delete Message:**
```bash
DELETE /chat/messages/{message_id}
Authorization: Bearer {access_token}
```

## Technology Stack

- **Backend:** FastAPI, Python 3.12
- **Database:** MongoDB (with Motor async driver)
- **Real-time:** WebSockets
- **Authentication:** JWT tokens
- **Frontend:** Vanilla JavaScript, HTML5, CSS3

## Features to Add

- [ ] Multiple chat rooms
- [ ] Direct messaging between users
- [ ] Typing indicators
- [ ] Read receipts
- [ ] File/image sharing
- [ ] Emoji support
- [ ] User presence (online/offline status)
- [ ] Message editing
- [ ] Search functionality
- [ ] Push notifications

## Security Notes

- All WebSocket connections require JWT authentication
- Messages are associated with authenticated users
- Users can only delete their own messages
- CORS is configured via middleware

## Development

The chat feature uses hot reload, so any changes to the backend will automatically restart the server. For frontend changes, simply refresh the browser.

### Project Structure

```
app/
├── routers/
│   └── chat.py          # WebSocket and REST endpoints
├── models/
│   └── messages.py      # MongoDB message model
├── schemas/
│   └── messages.py      # Pydantic schemas
└── static/
    └── chat.html        # Chat UI
```

## Troubleshooting

**WebSocket connection fails:**
- Ensure you're logged in and have a valid token
- Check that the API is running on port 8000
- Verify CORS settings if accessing from different origin

**Messages not persisting:**
- Ensure MongoDB container is running and healthy
- Check database connection in the logs

**Can't login:**
- Create a user via POST `/users/` endpoint
- Verify username and password are correct
- Check user is not disabled in the database
