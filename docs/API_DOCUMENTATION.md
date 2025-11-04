# Backend API Documentation

## Base URL
```
http://localhost:8000
```

## Table of Contents
1. [Authentication](#authentication)
2. [User Management](#user-management)
3. [Chat Sessions](#chat-sessions)
4. [Messages](#messages)
5. [Artifacts](#artifacts)
6. [WebSocket](#websocket)

---

## Authentication

### 1. Login
**POST** `/auths/login`

Login with email and password to receive access and refresh tokens.

**Request Body (form-data):**
```
username: string (email)
password: string
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "tier": "free",
  "verified": true,
  "active": true,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:00:00Z",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2025-11-04T11:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid credentials
- `403 Forbidden` - Account not verified or inactive

---

### 2. Refresh Token
**POST** `/auths/refresh`

Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_at": "2025-11-04T11:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or expired refresh token

---

### 3. Reset Password Request
**POST** `/auths/reset-password-request`

Request password reset email (sends reset token to email).

**Query Parameters:**
```
email: string
```

**Response:** `200 OK`
```json
{
  "message": "Password reset email sent"
}
```

**Error Responses:**
- `404 Not Found` - User not found

---

### 4. Reset Password
**POST** `/auths/reset-password`

Reset password using reset token.

**Query Parameters:**
```
token: string
new_password: string
```

**Response:** `200 OK`
```json
{
  "message": "Password reset successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired token

---

### 5. Verify Email
**POST** `/auths/verify-email`

Verify email address using verification token.

**Query Parameters:**
```
token: string
```

**Response:** `200 OK`
```json
{
  "message": "Email verified successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid or expired token

---

## User Management

### 1. Create User (Register)
**POST** `/users/`

Register a new user account.

**Request Body:**
```json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "SecurePass123!",
  "role": "user",
  "tier": "free"
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "tier": "free",
  "verified": false,
  "active": true,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Email already exists or invalid data

---

### 2. Get Current User
**GET** `/users/me`

Get currently authenticated user information.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "tier": "free",
  "verified": true,
  "active": true,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

### 3. Get User by ID
**GET** `/users/{id}`

Get user information by user ID. (Admin or own account only)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "johndoe",
  "email": "john@example.com",
  "role": "user",
  "tier": "free",
  "verified": true,
  "active": true,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:00:00Z"
}
```

**Error Responses:**
- `403 Forbidden` - Access denied (not admin or own account)
- `404 Not Found` - User not found

---

### 4. Update User by ID
**PUT** `/users/{id}`

Update user information. (Admin or own account only)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "username": "johndoe_updated",
  "tier": "premium"
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "johndoe_updated",
  "email": "john@example.com",
  "role": "user",
  "tier": "premium",
  "verified": true,
  "active": true,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T11:00:00Z"
}
```

**Error Responses:**
- `403 Forbidden` - Access denied (not admin or own account, or trying to update tier without admin role)
- `404 Not Found` - User not found

---

### 5. Update User by Email
**PUT** `/users/email/{email}`

Update user information by email. (Admin or own account only)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "username": "johndoe_updated"
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439011",
  "username": "johndoe_updated",
  "email": "john@example.com",
  "role": "user",
  "tier": "free",
  "verified": true,
  "active": true,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T11:00:00Z"
}
```

**Error Responses:**
- `403 Forbidden` - Access denied
- `404 Not Found` - User not found

---

### 6. Delete User
**DELETE** `/users/{id}`

Delete user account. (Admin or own account only)

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "message": "User deleted successfully"
}
```

**Error Responses:**
- `403 Forbidden` - Access denied
- `404 Not Found` - User not found

---

## Chat Sessions

### 1. Create Chat Session
**POST** `/chat/sessions`

Create a new chat session.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "title": "My Chat Session"
}
```

**Response:** `201 Created`
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "title": "My Chat Session",
  "message_count": 0,
  "last_message_at": null,
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:00:00Z"
}
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

### 2. Get All Chat Sessions
**GET** `/chat/sessions`

Get all chat sessions for the current user.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
```
limit: integer (default: 50) - Maximum number of sessions to return
```

**Response:** `200 OK`
```json
[
  {
    "_id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439012",
    "title": "My Chat Session",
    "message_count": 5,
    "last_message_at": "2025-11-04T10:30:00Z",
    "created_at": "2025-11-04T10:00:00Z",
    "updated_at": "2025-11-04T10:30:00Z"
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

### 3. Get Chat Session by ID
**GET** `/chat/sessions/{session_id}`

Get a specific chat session by ID.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "title": "My Chat Session",
  "message_count": 5,
  "last_message_at": "2025-11-04T10:30:00Z",
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T10:30:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid session ID format
- `404 Not Found` - Session not found

---

### 4. Update Chat Session
**PUT** `/chat/sessions/{session_id}`

Update chat session (e.g., rename).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "title": "Updated Session Title"
}
```

**Response:** `200 OK`
```json
{
  "_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "title": "Updated Session Title",
  "message_count": 5,
  "last_message_at": "2025-11-04T10:30:00Z",
  "created_at": "2025-11-04T10:00:00Z",
  "updated_at": "2025-11-04T11:00:00Z"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid session ID or no fields to update
- `404 Not Found` - Session not found

---

### 5. Delete Chat Session
**DELETE** `/chat/sessions/{session_id}`

Delete a chat session (soft delete) and disable all related artifacts.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "message": "Session deleted successfully",
  "artifacts_disabled": 2
}
```

**Error Responses:**
- `400 Bad Request` - Invalid session ID
- `404 Not Found` - Session not found

---

## Messages

### 1. Send Message
**POST** `/chat/sessions/{session_id}/messages`

Send a message in a chat session.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Request Body:**
```json
{
  "content": "Hello, this is my message!"
}
```

**Response:** `201 Created`
```json
{
  "_id": "507f1f77bcf86cd799439013",
  "session_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "content": "Hello, this is my message!",
  "role": "user",
  "created_at": "2025-11-04T10:15:00Z",
  "updated_at": "2025-11-04T10:15:00Z",
  "deleted": false,
  "deleted_at": null
}
```

**Error Responses:**
- `400 Bad Request` - Invalid session ID
- `404 Not Found` - Session not found

---

### 2. Get Messages
**GET** `/chat/sessions/{session_id}/messages`

Get all messages in a chat session.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
```
limit: integer (default: 100) - Maximum number of messages to return
```

**Response:** `200 OK`
```json
[
  {
    "_id": "507f1f77bcf86cd799439013",
    "session_id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439012",
    "content": "Hello, this is my message!",
    "role": "user",
    "created_at": "2025-11-04T10:15:00Z",
    "updated_at": "2025-11-04T10:15:00Z",
    "deleted": false,
    "deleted_at": null
  }
]
```

**Error Responses:**
- `400 Bad Request` - Invalid session ID
- `404 Not Found` - Session not found

---

### 3. Delete Message
**DELETE** `/chat/sessions/{session_id}/messages/{message_id}`

Delete a message (soft delete).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "message": "Message deleted successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid ID format
- `404 Not Found` - Session or message not found

---

### 4. Get Room Messages (WebSocket Chat)
**GET** `/chat/messages/{room}`

Get chat message history for a room (for WebSocket chat).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
```
limit: integer (default: 50, min: 1, max: 100) - Maximum number of messages to return
```

**Response:** `200 OK`
```json
[
  {
    "_id": "507f1f77bcf86cd799439013",
    "user_id": "507f1f77bcf86cd799439012",
    "username": "johndoe",
    "content": "Hello everyone!",
    "room": "general",
    "created_at": "2025-11-04T10:15:00Z",
    "updated_at": "2025-11-04T10:15:00Z",
    "deleted": false,
    "deleted_at": null
  }
]
```

**Error Responses:**
- `401 Unauthorized` - Invalid or missing token

---

### 5. Delete Room Message
**DELETE** `/chat/messages/{message_id}`

Delete a message from room (soft delete). User must own the message.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "message": "Message deleted successfully"
}
```

**Error Responses:**
- `403 Forbidden` - Not authorized to delete this message
- `404 Not Found` - Message not found

---

## Artifacts

### 1. Create Artifact
**POST** `/chat/sessions/{session_id}/artifacts`

Create a new artifact (repository, document, etc.) for a chat session.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "type": "repository",
  "name": "My Project",
  "source": "https://github.com/user/repo"
}
```

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439014",
  "session_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "type": "repository",
  "name": "My Project",
  "source": "https://github.com/user/repo",
  "files": [],
  "content": null,
  "metadata": {
    "storage_type": "object",
    "files_count": 0
  },
  "size": null,
  "created_at": "2025-11-04T10:20:00Z",
  "updated_at": "2025-11-04T10:20:00Z",
  "deleted": false,
  "deleted_at": null
}
```

**Artifact Types:**
- `repository` - Git repository
- `zip` - ZIP file
- `pdf` - PDF document
- `doc` - DOC/DOCX document
- `text` - Text file

**Error Responses:**
- `400 Bad Request` - Invalid session ID or artifact data
- `404 Not Found` - Session not found

---

### 2. Add Repository Context (Legacy Endpoint)
**POST** `/chat/sessions/{session_id}/context/repository`

Legacy endpoint for adding repository as artifact. Redirects to artifact creation.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body (Flexible):**
```json
{
  "url": "https://github.com/user/repo",
  "name": "My Project"
}
```

Or:
```json
{
  "source": "https://github.com/user/repo",
  "name": "My Project"
}
```

Or:
```json
{
  "repo_url": "https://github.com/user/repo"
}
```

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439014",
  "session_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "type": "repository",
  "name": "My Project",
  "source": "https://github.com/user/repo",
  "files": [],
  "content": null,
  "metadata": {},
  "size": null,
  "created_at": "2025-11-04T10:20:00Z",
  "updated_at": "2025-11-04T10:20:00Z",
  "deleted": false,
  "deleted_at": null
}
```

**Error Responses:**
- `400 Bad Request` - Invalid repository URL
- `404 Not Found` - Session not found

---

### 3. Upload File as Artifact
**POST** `/chat/sessions/{session_id}/artifacts/upload`

Upload a file (PDF, DOC, ZIP, etc.) as an artifact.

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: multipart/form-data
```

**Request Body (form-data):**
```
file: File (required)
name: string (optional) - Display name for the artifact
```

**Response:** `201 Created`
```json
{
  "id": "507f1f77bcf86cd799439015",
  "session_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "type": "pdf",
  "name": "document.pdf",
  "source": "document.pdf",
  "files": null,
  "content": null,
  "metadata": {
    "storage_type": "object",
    "filename": "document.pdf",
    "content_type": "application/pdf"
  },
  "size": 102400,
  "created_at": "2025-11-04T10:25:00Z",
  "updated_at": "2025-11-04T10:25:00Z",
  "deleted": false,
  "deleted_at": null
}
```

**Supported File Types:**
- PDF (`.pdf`)
- DOC/DOCX (`.doc`, `.docx`)
- ZIP (`.zip`)
- Text (`.txt`)

**Error Responses:**
- `400 Bad Request` - Invalid session ID or unsupported file type
- `404 Not Found` - Session not found
- `413 Payload Too Large` - File too large

---

### 4. Get Session Artifacts
**GET** `/chat/sessions/{session_id}/artifacts`

Get all artifacts for a chat session.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
[
  {
    "id": "507f1f77bcf86cd799439014",
    "session_id": "507f1f77bcf86cd799439011",
    "user_id": "507f1f77bcf86cd799439012",
    "type": "repository",
    "name": "My Project",
    "source": "https://github.com/user/repo",
    "files": [],
    "content": null,
    "metadata": {
      "storage_type": "object",
      "files_count": 25
    },
    "size": null,
    "created_at": "2025-11-04T10:20:00Z",
    "updated_at": "2025-11-04T10:20:00Z",
    "deleted": false,
    "deleted_at": null
  }
]
```

**Error Responses:**
- `400 Bad Request` - Invalid session ID
- `404 Not Found` - Session not found

---

### 5. Get Artifact by ID
**GET** `/chat/sessions/{session_id}/artifacts/{artifact_id}`

Get a specific artifact by ID.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439014",
  "session_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "type": "repository",
  "name": "My Project",
  "source": "https://github.com/user/repo",
  "files": [],
  "content": null,
  "metadata": {
    "storage_type": "object"
  },
  "size": null,
  "created_at": "2025-11-04T10:20:00Z",
  "updated_at": "2025-11-04T10:20:00Z",
  "deleted": false,
  "deleted_at": null
}
```

**Error Responses:**
- `400 Bad Request` - Invalid session or artifact ID
- `404 Not Found` - Session or artifact not found

---

### 6. Get Artifact Files
**GET** `/chat/sessions/{session_id}/artifacts/{artifact_id}/files`

Get list of files in an artifact (for repositories and archives).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Query Parameters:**
```
limit: integer (default: 50) - Maximum number of files to return
offset: integer (default: 0) - Number of files to skip
```

**Response:** `200 OK`
```json
{
  "files": [
    {
      "path": "src/main.py",
      "size": 1024,
      "type": "file"
    },
    {
      "path": "src/utils/helper.py",
      "size": 512,
      "type": "file"
    }
  ],
  "total": 25,
  "limit": 50,
  "offset": 0
}
```

**Error Responses:**
- `400 Bad Request` - Invalid session or artifact ID
- `404 Not Found` - Session or artifact not found

---

### 7. Get Artifact File Content
**GET** `/chat/sessions/{session_id}/artifacts/{artifact_id}/files/{file_path:path}`

Get content of a specific file in an artifact.

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "content": "def main():\n    print('Hello, World!')\n\nif __name__ == '__main__':\n    main()",
  "path": "src/main.py",
  "size": 78,
  "encoding": "utf-8"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid IDs
- `404 Not Found` - Artifact or file not found

---

### 8. Download Artifact File
**GET** `/chat/sessions/{session_id}/artifacts/{artifact_id}/download`

Download artifact file (for PDFs, DOCs, etc.).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```
Content-Type: application/pdf (or appropriate mime type)
Content-Disposition: attachment; filename="document.pdf"

[Binary file content]
```

**Error Responses:**
- `400 Bad Request` - Invalid IDs
- `404 Not Found` - Artifact not found
- `500 Internal Server Error` - File not found on storage

---

### 9. Update Artifact
**PUT** `/chat/sessions/{session_id}/artifacts/{artifact_id}`

Update artifact metadata (name, etc.).

**Headers:**
```
Authorization: Bearer {access_token}
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "Updated Artifact Name"
}
```

**Response:** `200 OK`
```json
{
  "id": "507f1f77bcf86cd799439014",
  "session_id": "507f1f77bcf86cd799439011",
  "user_id": "507f1f77bcf86cd799439012",
  "type": "repository",
  "name": "Updated Artifact Name",
  "source": "https://github.com/user/repo",
  "files": [],
  "content": null,
  "metadata": {},
  "size": null,
  "created_at": "2025-11-04T10:20:00Z",
  "updated_at": "2025-11-04T10:40:00Z",
  "deleted": false,
  "deleted_at": null
}
```

**Error Responses:**
- `400 Bad Request` - Invalid IDs or no fields to update
- `404 Not Found` - Artifact not found

---

### 10. Delete Artifact
**DELETE** `/chat/sessions/{session_id}/artifacts/{artifact_id}`

Delete an artifact (soft delete).

**Headers:**
```
Authorization: Bearer {access_token}
```

**Response:** `200 OK`
```json
{
  "message": "Artifact deleted successfully"
}
```

**Error Responses:**
- `400 Bad Request` - Invalid IDs
- `404 Not Found` - Artifact not found

---

## WebSocket

### WebSocket Connection
**WS** `/chat/ws/{room}`

Connect to a chat room via WebSocket for real-time messaging.

**Query Parameters:**
```
token: string (required) - JWT access token for authentication
```

**Connection URL Example:**
```
ws://localhost:8000/chat/ws/general?token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Events:**

#### Client → Server Messages:
```json
{
  "content": "Hello everyone!"
}
```

#### Server → Client Messages:

**User Message:**
```json
{
  "type": "message",
  "_id": "507f1f77bcf86cd799439013",
  "user_id": "507f1f77bcf86cd799439012",
  "username": "johndoe",
  "content": "Hello everyone!",
  "room": "general",
  "created_at": "2025-11-04T10:15:00.000Z"
}
```

**System Message (Join):**
```json
{
  "type": "system",
  "content": "johndoe joined the room",
  "room": "general",
  "timestamp": "2025-11-04T10:15:00.000Z"
}
```

**System Message (Leave):**
```json
{
  "type": "system",
  "content": "johndoe left the room",
  "room": "general",
  "timestamp": "2025-11-04T10:20:00.000Z"
}
```

**Error Handling:**
- Invalid token: Connection closed with code `1008` (Policy Violation)
- Internal error: Connection closed with code `1011` (Internal Error)

---

## Error Response Format

All API endpoints return errors in the following format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

Common HTTP status codes:
- `200 OK` - Request successful
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required or invalid token
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `413 Payload Too Large` - Request body too large
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

---

## Authentication

Most endpoints require authentication using JWT Bearer tokens. Include the access token in the Authorization header:

```
Authorization: Bearer {access_token}
```

Tokens are obtained from the `/auths/login` endpoint and can be refreshed using `/auths/refresh`.

---

## Rate Limiting

Currently, no rate limiting is implemented. This should be added in production environments.

---

## WebSocket Connection Example (JavaScript)

```javascript
const token = "your_access_token_here";
const room = "general";
const ws = new WebSocket(`ws://localhost:8000/chat/ws/${room}?token=${token}`);

ws.onopen = () => {
  console.log("Connected to chat room");

  // Send a message
  ws.send(JSON.stringify({
    content: "Hello everyone!"
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Received:", data);

  if (data.type === "message") {
    console.log(`${data.username}: ${data.content}`);
  } else if (data.type === "system") {
    console.log(`[System] ${data.content}`);
  }
};

ws.onerror = (error) => {
  console.error("WebSocket error:", error);
};

ws.onclose = () => {
  console.log("Disconnected from chat room");
};
```

---

## Notes

- All timestamps are in ISO 8601 format (UTC)
- MongoDB ObjectIds are returned as strings
- Soft deletes are used throughout - deleted items are marked with `deleted: true` but not removed from the database
- When a chat session is deleted, all related artifacts are automatically soft-deleted (cascade delete)
- File uploads support PDF, DOC/DOCX, ZIP, and TXT formats
- Repository cloning supports GitHub, GitLab, and Bitbucket repositories
- Object storage is used for file artifacts (stored in `/app/storage/`)

---

**Last Updated:** 2025-11-04
**API Version:** 0.1.0
