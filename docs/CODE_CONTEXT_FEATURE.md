# Code Context Feature for Chat Sessions

This document describes the new code context feature that allows users to add code repositories or zip files as context to their chat sessions.

## Overview

Users can now enhance their chat sessions by adding code context in two ways:
1. **Repository URL**: Add a link to a code repository (GitHub, GitLab, etc.)
2. **Zip File Upload**: Upload a zip file containing code files

This context can be used by AI assistants or other services to provide more relevant responses based on the user's codebase.

## Features

### 1. Backend API Endpoints

#### Upload Zip File
- **Endpoint**: `POST /chat/sessions/{session_id}/context/upload`
- **Description**: Upload a zip file containing code
- **Request**: Multipart form data with a file field
- **Features**:
  - Validates zip file format
  - Extracts and filters code files only (supports common extensions)
  - Limits file size to 1MB per file
  - Stores file content in the database
  - Returns updated session with context information

#### Add Repository URL
- **Endpoint**: `POST /chat/sessions/{session_id}/context/repository`
- **Description**: Add a repository URL as context
- **Request**: JSON body with `repository_url` field
- **Features**:
  - Validates URL format
  - Stores repository URL in the database
  - Can be extended to fetch repository contents

#### Remove Context
- **Endpoint**: `DELETE /chat/sessions/{session_id}/context`
- **Description**: Remove context from a chat session
- **Features**:
  - Removes all context data from the session
  - Updates session timestamp

### 2. Database Schema Changes

#### ChatSession Model
Added `context` field to store code context information:

```python
class CodeContext(Base):
    type: str  # 'repository' or 'zip'
    source: Optional[str]  # Repository URL or filename
    files: Optional[List[Dict[str, Any]]]  # List of files with content
    added_at: datetime

class ChatSession(Base):
    # ... existing fields
    context: Optional[CodeContext]
```

### 3. User Interface

#### Features
- **"+ Add Code Context" button** in the chat header (visible when a session is selected)
- **Modal dialog** with two options:
  - Upload Zip File
  - Add Repository URL
- **Context badge** displayed in chat title when context is present
- **Context information display** showing:
  - Context type (Repository/Zip)
  - Source (URL or filename)
  - Number of files extracted
- **Remove context button** to delete context from session

#### User Workflow

1. **Select or create a chat session**
2. **Click "+ Add Code Context" button** in the chat header
3. **Choose context type**:
   - **For Repository**: Enter the repository URL and click "Add Repository"
   - **For Zip File**: Select a zip file and click "Upload Zip"
4. **View context**: A badge appears next to the chat title
5. **Remove context**: Click "+ Add Code Context" again and use "Remove Context" button

## Supported File Extensions

The system automatically filters and processes only code files with these extensions:
- Python: `.py`
- JavaScript/TypeScript: `.js`, `.ts`, `.tsx`, `.jsx`
- Java: `.java`
- C/C++: `.cpp`, `.c`, `.h`
- C#: `.cs`
- Go: `.go`
- Rust: `.rs`
- Ruby: `.rb`
- PHP: `.php`
- Swift: `.swift`
- Kotlin: `.kt`
- Scala: `.scala`
- SQL: `.sql`
- Markup/Config: `.html`, `.css`, `.json`, `.xml`, `.yaml`, `.yml`
- Documentation: `.md`, `.txt`
- Scripts: `.sh`, `.bash`

## Limitations

- **File size limit**: Individual files larger than 1MB are skipped
- **File type filtering**: Only text-based code files are processed
- **Binary files**: Automatically skipped
- **Storage**: Context data is stored in MongoDB, consider storage limits for large codebases

## Security Considerations

- Authentication required for all context operations
- Users can only add context to their own sessions
- File content is sanitized (UTF-8 decoding with error handling)
- Repository URLs are validated for proper format

## Future Enhancements

Possible improvements for this feature:
1. **Repository fetching**: Automatically clone and extract files from public repositories
2. **Context search**: Allow searching through context files
3. **Context usage tracking**: Track which files are referenced in chat
4. **Selective file upload**: Allow users to choose specific files from zip
5. **GitHub integration**: Direct integration with GitHub API
6. **Context preview**: Show file tree before uploading
7. **Code highlighting**: Display code with syntax highlighting
8. **Context limits**: Add configurable limits per user or plan

## Example Usage

### Using cURL

#### Add Repository URL
```bash
curl -X POST "http://localhost:8000/chat/sessions/{session_id}/context/repository" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"repository_url": "https://github.com/username/repo"}'
```

#### Upload Zip File
```bash
curl -X POST "http://localhost:8000/chat/sessions/{session_id}/context/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/code.zip"
```

#### Remove Context
```bash
curl -X DELETE "http://localhost:8000/chat/sessions/{session_id}/context" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Testing

To test the feature:

1. Start the application:
   ```bash
   docker-compose up
   ```

2. Open the chat sessions interface: `http://localhost:8000/static/chat_sessions.html`

3. Login with test credentials

4. Create or select a chat session

5. Click "+ Add Code Context" and try both methods:
   - Upload a zip file with code
   - Add a repository URL

6. Verify the context badge appears

7. Open the modal again to see context details

8. Remove the context and verify it's gone

## Files Modified

- `app/models/chat_sessions.py` - Added CodeContext model
- `app/schemas/chat_sessions.py` - Added context schemas
- `app/routers/chat_sessions.py` - Added context endpoints
- `app/static/chat_sessions.html` - Added UI components and JavaScript

## Dependencies

No new dependencies required. Uses existing packages:
- `zipfile` (Python standard library)
- `io` (Python standard library)
- `pathlib` (Python standard library)
