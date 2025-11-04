# Repository Storage Feature

## Overview

The repository storage feature allows users to add Git repositories as artifacts to their chat sessions. When a repository URL is provided, the system automatically:

1. **Clones** the repository
2. **Extracts** code files
3. **Stores** the files in MongoDB (file-based database)
4. **Associates** the files with the chat session

## How It Works

### 1. Repository Cloning

When you add a repository URL, the system:
- Validates the URL
- Clones the repository using `git clone --depth=1` (shallow clone for speed)
- Extracts only code files (ignores binaries, large files, etc.)

### 2. File Filtering

The system intelligently filters files:

**Supported Extensions:**
- Python: `.py`
- JavaScript/TypeScript: `.js`, `.ts`, `.tsx`, `.jsx`
- Java: `.java`
- C/C++: `.c`, `.cpp`, `.h`, `.hpp`
- Web: `.html`, `.css`, `.vue`, `.svelte`
- Config: `.json`, `.yaml`, `.yml`, `.xml`
- Documentation: `.md`, `.txt`
- And many more...

**Ignored Directories:**
- `.git`, `node_modules`, `__pycache__`
- `venv`, `env`, `.env`
- `dist`, `build`, `target`
- IDE folders: `.idea`, `.vscode`
- And other common build/dependency directories

**File Size Limit:**
- Maximum file size: 5MB
- Maximum files: 500 files per repository

### 3. Storage in MongoDB

Files are stored directly in MongoDB as part of the artifact document:

```json
{
  "_id": ObjectId("..."),
  "session_id": ObjectId("..."),
  "user_id": ObjectId("..."),
  "type": "repository",
  "name": "my-repo",
  "source": "https://github.com/user/my-repo",
  "files": [
    {
      "path": "src/main.py",
      "content": "# Python code here...",
      "size": 1024
    },
    {
      "path": "README.md",
      "content": "# Documentation...",
      "size": 512
    }
  ],
  "metadata": {
    "repo_info": {
      "name": "my-repo",
      "host": "GitHub",
      "owner": "user"
    },
    "total_files": 25
  },
  "size": 153600,
  "created_at": ISODate("..."),
  "updated_at": ISODate("...")
}
```

## API Endpoints

### Add Repository

```http
POST /chat/sessions/{session_id}/context/repository
Authorization: Bearer <token>
Content-Type: application/json

{
  "url": "https://github.com/user/repo"
}
```

**Response:**
```json
{
  "id": "artifact_id",
  "session_id": "session_id",
  "type": "repository",
  "name": "repo",
  "source": "https://github.com/user/repo",
  "files": [...],
  "metadata": {...},
  "size": 153600,
  "created_at": "2025-11-04T10:00:00Z"
}
```

### Get Artifact Files (Paginated)

```http
GET /chat/sessions/{session_id}/artifacts/{artifact_id}/files?limit=100&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "artifact_id": "artifact_id",
  "artifact_name": "repo",
  "artifact_type": "repository",
  "total_files": 250,
  "offset": 0,
  "limit": 100,
  "files": [
    {
      "path": "src/main.py",
      "content": "...",
      "size": 1024
    }
  ]
}
```

### Get Specific File

```http
GET /chat/sessions/{session_id}/artifacts/{artifact_id}/files/{file_path}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "path": "src/main.py",
  "content": "# File content here",
  "size": 1024
}
```

## UI Usage

1. **Login** to the chat interface
2. **Select or create** a chat session
3. **Click** the "+ Add Code Context" button
4. **Choose** "📦 Repository URL"
5. **Enter** the repository URL (e.g., `github.com/user/repo` or `https://github.com/user/repo`)
6. **Click** "Add Repository"
7. Wait for the system to clone and process the repository
8. View the artifact in the modal with file count and details

## Benefits

### 1. **No External Storage Required**
- All files stored directly in MongoDB
- No need for separate file storage service
- Simple backup and restore with database backups

### 2. **Fast Access**
- Files available immediately through API
- No filesystem I/O required
- Efficient querying with MongoDB indexes

### 3. **Session Isolation**
- Each chat session has its own artifacts
- Easy to manage and delete
- Clean separation of concerns

### 4. **Rich Metadata**
- Repository information (host, owner, name)
- File statistics (count, total size)
- Creation and modification timestamps

### 5. **Scalability**
- MongoDB handles large documents efficiently
- Horizontal scaling with MongoDB sharding
- Automatic compression in MongoDB

## Limitations

1. **Private Repositories**: Currently only supports public repositories
2. **File Size**: Individual files limited to 5MB
3. **Total Files**: Maximum 500 files per repository
4. **Binary Files**: Not stored (only text-based code files)
5. **Large Repositories**: May take time to clone and process

## Future Enhancements

- [ ] Support for private repositories (SSH keys, tokens)
- [ ] Incremental updates (pull new changes)
- [ ] Code indexing and search
- [ ] Syntax highlighting in UI
- [ ] File tree visualization
- [ ] Repository branches support
- [ ] Git history access

## Technical Details

### Dependencies
- **GitPython**: For Git operations
- **Motor**: Async MongoDB driver
- **FastAPI**: REST API framework

### Performance
- **Shallow Clone**: Uses `--depth=1` for faster cloning
- **Async Operations**: Non-blocking I/O
- **File Filtering**: Only processes relevant files
- **Pagination**: Large file lists handled efficiently

### Security
- **URL Validation**: Checks for valid Git URLs
- **Size Limits**: Prevents storage abuse
- **User Isolation**: Artifacts tied to users and sessions
- **Soft Delete**: Artifacts marked as deleted, not immediately removed

## Example Use Cases

1. **Code Review**: Add a repository to discuss code changes
2. **Documentation**: Reference codebase while writing docs
3. **Bug Reports**: Include relevant code context
4. **Learning**: Analyze open-source projects
5. **Collaboration**: Share code context in team chats
