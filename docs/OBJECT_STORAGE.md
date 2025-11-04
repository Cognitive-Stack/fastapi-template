# Object Storage Implementation

## Overview

The system now uses **object-based file storage** (filesystem) instead of storing files in MongoDB. This approach provides:

- ✅ **Better performance** for large files
- ✅ **Support for binary files** (PDF, DOC, etc.)
- ✅ **Reduced database load**
- ✅ **Easier file management**
- ✅ **Persistent storage** with Docker volumes

## Architecture

### Storage Structure

```
/app/storage/
├── artifacts/          # General artifact storage
├── repositories/       # Cloned repository files
│   └── {artifact_id}/
│       ├── metadata.json
│       └── {file_path}
└── uploads/           # Uploaded files (PDF, DOC, etc.)
    └── {artifact_id}/
        ├── metadata.json
        └── {filename}
```

### MongoDB Storage

MongoDB now stores **only metadata**:

```json
{
  "_id": "artifact_id",
  "session_id": "session_id",
  "user_id": "user_id",
  "type": "repository",
  "name": "repo-name",
  "source": "https://github.com/user/repo",
  "files": null,  // Files NOT stored in MongoDB
  "metadata": {
    "storage_type": "object",
    "storage_path": "repositories/artifact_id",
    "total_files": 250,
    "repo_info": {...}
  },
  "size": 1024000
}
```

## Implementation Details

### 1. Object Storage Utility (`app/utils/object_storage.py`)

**Key Functions:**

- `initialize_storage()` - Creates storage directories
- `save_repository_files()` - Saves repository files to disk
- `save_uploaded_file()` - Saves uploaded files (PDF, DOC)
- `get_repository_files()` - Lists files with pagination
- `get_repository_file_content()` - Gets file content
- `get_uploaded_file()` - Gets uploaded file
- `delete_artifact_files()` - Deletes artifact files

### 2. Repository Storage

When a repository is cloned:

1. **Clone** repository using GitPython
2. **Extract** code files (40+ extensions)
3. **Create artifact** in MongoDB (gets ID)
4. **Save files** to `/app/storage/repositories/{artifact_id}/`
5. **Create metadata.json** with file list
6. **Update MongoDB** with storage path

**Example:**
```bash
/app/storage/repositories/673456789abcdef/
├── metadata.json
├── README.md
├── src/
│   ├── main.py
│   └── utils.py
└── tests/
    └── test_main.py
```

### 3. PDF/Document Storage

When a PDF or DOC is uploaded:

1. **Read file** content
2. **Create artifact** in MongoDB (gets ID)
3. **Save file** to `/app/storage/uploads/{artifact_id}/{filename}`
4. **Create metadata.json** with file info
5. **Update MongoDB** with storage path

**Example:**
```bash
/app/storage/uploads/673456789abcdef/
├── metadata.json
└── document.pdf
```

## API Endpoints

### Upload PDF/Document

```http
POST /chat/sessions/{session_id}/artifacts/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: document.pdf
```

**Response:**
```json
{
  "id": "artifact_id",
  "type": "pdf",
  "name": "document.pdf",
  "size": 1024000,
  "metadata": {
    "storage_type": "object",
    "storage_path": "uploads/artifact_id"
  }
}
```

### Download PDF/Document

```http
GET /chat/sessions/{session_id}/artifacts/{artifact_id}/download
Authorization: Bearer <token>
```

**Response:** Binary file download

### Get Repository Files

```http
GET /chat/sessions/{session_id}/artifacts/{artifact_id}/files?limit=100&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "artifact_id": "artifact_id",
  "total_files": 250,
  "files": [
    {
      "path": "src/main.py",
      "size": 1024
    }
  ]
}
```

### Get File Content

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

## Docker Configuration

### Volume Mount

```yaml
volumes:
  - artifact_storage:/app/storage  # Persistent storage
```

### Storage Persistence

- Files survive container restarts
- Files persist across deployments
- Can be backed up separately from database

### Backup Strategy

```bash
# Backup artifact storage
docker run --rm -v fastapi-template_artifact_storage:/data \
  -v $(pwd):/backup busybox tar czf /backup/artifacts-backup.tar.gz /data

# Restore artifact storage
docker run --rm -v fastapi-template_artifact_storage:/data \
  -v $(pwd):/backup busybox tar xzf /backup/artifacts-backup.tar.gz -C /
```

## Migration from MongoDB Storage

For existing artifacts stored in MongoDB:

1. **Keep MongoDB files** for backward compatibility
2. **New artifacts** automatically use object storage
3. **API handles both** storage types transparently

The system checks `metadata.storage_type`:
- `"object"` → Read from filesystem
- `null/undefined` → Read from MongoDB (legacy)

## Performance Comparison

### MongoDB Storage (Old)

- ❌ 16MB document size limit
- ❌ Slow for large files
- ❌ High memory usage
- ❌ Complex binary handling

### Object Storage (New)

- ✅ No file size limits
- ✅ Fast file access
- ✅ Low memory footprint
- ✅ Native binary support
- ✅ Easy file management

## File Type Support

### Repositories

- All text-based code files
- 40+ file extensions
- Maximum 500 files per repo
- Maximum 5MB per file

### Uploads

- **PDF** - Full support with download
- **DOC/DOCX** - Full support with download
- **ZIP** - Extracted to repository structure
- **TXT/MD** - Stored as text files

## Security Considerations

### Path Traversal Protection

```python
# Check if file is within artifact directory
if not full_path.resolve().is_relative_to(repo_path.resolve()):
    raise ValueError("Invalid file path")
```

### User Isolation

- Files stored per artifact ID
- MongoDB enforces user access
- Filesystem organized by artifact

### File Size Limits

- Individual files: 5MB (repositories)
- Total upload size: Configurable
- Prevents storage abuse

## Monitoring & Maintenance

### Storage Statistics

```python
from app.utils.object_storage import get_storage_stats

stats = get_storage_stats()
# {
#   "repositories": 50,
#   "uploads": 25,
#   "total_size": 1073741824  # bytes
# }
```

### Cleanup

Deleted artifacts automatically remove:
1. MongoDB metadata (soft delete)
2. Filesystem files (hard delete)

### Disk Space Management

Monitor Docker volume:
```bash
docker system df -v
```

Clean up old artifacts:
```bash
# MongoDB soft-deleted artifacts can be purged
# Filesystem files auto-deleted on artifact removal
```

## Troubleshooting

### Storage Not Initialized

```
ERROR: Storage directory not found
```

**Solution:** Storage auto-initializes on startup. If missing:
```bash
docker-compose exec api python3 -c "from app.utils.object_storage import initialize_storage; initialize_storage()"
```

### Permission Issues

```
ERROR: Permission denied writing to /app/storage
```

**Solution:** Check volume permissions:
```bash
docker-compose exec api ls -la /app/storage
docker-compose exec api chmod -R 755 /app/storage
```

### Files Not Found

```
ERROR: File not found in artifact
```

**Solution:** Verify artifact storage type and path in MongoDB:
```javascript
db.artifacts.findOne({_id: ObjectId("artifact_id")})
```

## Best Practices

1. **Always use object storage** for new artifacts
2. **Regular backups** of artifact volume
3. **Monitor disk space** usage
4. **Set appropriate limits** for file sizes
5. **Clean up deleted artifacts** periodically

## Future Enhancements

- [ ] Cloud storage integration (S3, Azure Blob)
- [ ] File compression for repositories
- [ ] CDN integration for file serving
- [ ] Deduplication for similar files
- [ ] Virus scanning for uploads
- [ ] Thumbnail generation for PDFs
- [ ] Full-text search in documents
