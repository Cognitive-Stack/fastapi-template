# Chat Sessions Feature

A multi-session chat system where users can create, manage, and chat in multiple independent chat sessions.

## What Changed

### Removed
- ❌ P2P WebSocket chat functionality
- ❌ Real-time message broadcasting
- ❌ Room-based chat
- ❌ Old `app/routers/chat.py`

### Added
- ✅ Session-based chat system
- ✅ Create multiple chat sessions
- ✅ REST API for messages (no WebSockets)
- ✅ Session management (create, rename, delete)
- ✅ New modern UI with sidebar

## Architecture

### Models

**ChatSession** (`app/models/chat_sessions.py`):
```python
- user_id: PyObjectId          # Owner of the session
- title: str                    # Session name
- message_count: int            # Number of messages
- last_message_at: datetime     # Last activity
```

**Message** (`app/models/messages.py`):
```python
- session_id: PyObjectId        # Parent session
- user_id: PyObjectId           # Message author
- content: str                  # Message text
- role: str                     # "user" or "assistant"
```

### API Endpoints

All endpoints require JWT authentication via `Authorization: Bearer <token>` header.

#### Sessions

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/sessions` | Create a new chat session |
| GET | `/chat/sessions` | Get all user's sessions |
| GET | `/chat/sessions/{id}` | Get specific session |
| PUT | `/chat/sessions/{id}` | Update session (rename) |
| DELETE | `/chat/sessions/{id}` | Delete session |

#### Messages

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/sessions/{id}/messages` | Send a message |
| GET | `/chat/sessions/{id}/messages` | Get session messages |
| DELETE | `/chat/sessions/{id}/messages/{msg_id}` | Delete a message |

## Frontend

Access at: **http://localhost:8000/chat-ui**

### Features

1. **Sidebar**:
   - List of all chat sessions
   - Create new session button
   - Rename/delete session actions
   - User info and logout

2. **Main Chat Area**:
   - Messages displayed in conversation format
   - User messages on the right (purple)
   - Assistant messages on the left (white)
   - Send message input with textarea

3. **Session Management**:
   - Click session to view messages
   - Create new chat with custom title
   - Rename sessions inline
   - Delete with confirmation

## Usage Example

### 1. Login

```bash
curl -X POST "http://localhost:8000/auths/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=alicepass123"
```

### 2. Create Session

```bash
curl -X POST "http://localhost:8000/chat/sessions" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"title": "My First Chat"}'
```

Response:
```json
{
  "_id": "6909...",
  "user_id": "6909...",
  "title": "My First Chat",
  "message_count": 0,
  "last_message_at": null,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:00:00Z"
}
```

### 3. Send Message

```bash
curl -X POST "http://localhost:8000/chat/sessions/{session_id}/messages" \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"content": "Hello!"}'
```

### 4. Get Messages

```bash
curl -X GET "http://localhost:8000/chat/sessions/{session_id}/messages" \
  -H "Authorization: Bearer <token>"
```

### 5. Get All Sessions

```bash
curl -X GET "http://localhost:8000/chat/sessions" \
  -H "Authorization: Bearer <token>"
```

## Database Collections

### `chat_sessions`
```javascript
{
  _id: ObjectId,
  user_id: ObjectId,
  title: String,
  message_count: Number,
  last_message_at: Date,
  created_at: Date,
  updated_at: Date,
  deleted: Boolean,
  deleted_at: Date
}
```

### `messages`
```javascript
{
  _id: ObjectId,
  session_id: ObjectId,
  user_id: ObjectId,
  content: String,
  role: String,  // "user" or "assistant"
  created_at: Date,
  deleted: Boolean,
  deleted_at: Date
}
```

## Testing with UI

1. **Open**: http://localhost:8000/chat-ui

2. **Login** with:
   - Username: `alice` or `testuser`
   - Password: `alicepass123` or `testpass123`

3. **Create a session**:
   - Click "+ New Chat" button
   - Enter a title (e.g., "My Test Chat")

4. **Send messages**:
   - Type in the input area
   - Press Enter or click "Send"
   - Messages appear immediately

5. **Manage sessions**:
   - Click any session in sidebar to switch
   - Click "Rename" to change title
   - Click "Delete" to remove session

## Features

✅ **Multiple sessions**: Create unlimited chat sessions
✅ **Session management**: Create, rename, delete
✅ **Message history**: Persistent storage in MongoDB
✅ **User isolation**: Each user sees only their sessions
✅ **Soft deletes**: Sessions and messages can be recovered
✅ **Message count tracking**: Auto-updated on send/delete
✅ **Last activity tracking**: Shows when session was last used
✅ **Modern UI**: Clean sidebar layout with session list
✅ **Responsive design**: Works on all screen sizes

## Future Enhancements

Potential features to add:

- [ ] AI integration (OpenAI, Claude, etc.)
- [ ] Message editing
- [ ] Search within messages
- [ ] Export session to PDF/TXT
- [ ] Share session with other users
- [ ] Session folders/organization
- [ ] Message reactions
- [ ] File attachments
- [ ] Markdown rendering in messages
- [ ] Code syntax highlighting

## Differences from P2P Chat

| Feature | P2P Chat (Old) | Sessions (New) |
|---------|---------------|----------------|
| **Communication** | Real-time WebSocket | REST API |
| **Users** | Multiple users in room | Single user per session |
| **Sessions** | One room ("general") | Unlimited sessions |
| **Messages** | Broadcast to all | Stored per session |
| **UI** | Single chat window | Sidebar + chat area |
| **Use Case** | Group chat | Personal conversations |

## Notes

- Sessions are user-specific (no sharing between users yet)
- Messages are ordered by `created_at` timestamp
- All operations support soft delete for recovery
- Session `message_count` is automatically maintained
- The `role` field in messages allows for future AI integration

## Next Steps

To add AI functionality:

1. Add AI service integration (OpenAI, Claude API)
2. When user sends message, also send to AI
3. Save AI response with `role: "assistant"`
4. Display both user and AI messages in UI

The architecture is already prepared for this with the `role` field!
