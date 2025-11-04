"""
Object-based file storage utility for storing repository files and PDFs on filesystem
"""
import os
import json
import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from loguru import logger

# Base storage directory
STORAGE_BASE_DIR = Path("/app/storage")
ARTIFACTS_DIR = STORAGE_BASE_DIR / "artifacts"
REPOSITORIES_DIR = STORAGE_BASE_DIR / "repositories"
UPLOADS_DIR = STORAGE_BASE_DIR / "uploads"


def initialize_storage():
    """Initialize storage directories"""
    STORAGE_BASE_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    REPOSITORIES_DIR.mkdir(parents=True, exist_ok=True)
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Storage directories initialized at {STORAGE_BASE_DIR}")


def get_artifact_path(artifact_id: str) -> Path:
    """Get the base path for an artifact"""
    return ARTIFACTS_DIR / artifact_id


def get_repository_path(artifact_id: str) -> Path:
    """Get the path for a repository artifact"""
    return REPOSITORIES_DIR / artifact_id


def get_upload_path(artifact_id: str) -> Path:
    """Get the path for an uploaded file artifact"""
    return UPLOADS_DIR / artifact_id


async def save_repository_files(artifact_id: str, files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Save repository files to object storage

    Args:
        artifact_id: The artifact ID
        files: List of file dictionaries with path, content, and size

    Returns:
        Dictionary with storage statistics
    """
    try:
        repo_path = get_repository_path(artifact_id)
        repo_path.mkdir(parents=True, exist_ok=True)

        saved_files = []
        total_size = 0

        # Save metadata file
        metadata = {
            "artifact_id": artifact_id,
            "type": "repository",
            "file_count": len(files),
            "created_at": datetime.now().isoformat(),
            "files": []
        }

        for file_info in files:
            file_path = file_info['path']
            content = file_info['content']
            size = file_info['size']

            # Create full path
            full_path = repo_path / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Write file content
            with open(full_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(content)

            saved_files.append({
                "path": file_path,
                "size": size,
                "storage_path": str(full_path.relative_to(STORAGE_BASE_DIR))
            })

            total_size += size

            # Add to metadata (without content)
            metadata["files"].append({
                "path": file_path,
                "size": size
            })

        # Save metadata.json
        metadata_path = repo_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved {len(saved_files)} files for artifact {artifact_id}, total size: {total_size} bytes")

        return {
            "artifact_id": artifact_id,
            "files_saved": len(saved_files),
            "total_size": total_size,
            "storage_path": str(repo_path.relative_to(STORAGE_BASE_DIR))
        }

    except Exception as e:
        logger.error(f"Error saving repository files: {e}")
        raise


async def save_uploaded_file(artifact_id: str, filename: str, content: bytes) -> Dict[str, Any]:
    """
    Save an uploaded file (PDF, ZIP, etc.) to object storage

    Args:
        artifact_id: The artifact ID
        filename: Original filename
        content: File content as bytes

    Returns:
        Dictionary with storage information
    """
    try:
        upload_path = get_upload_path(artifact_id)
        upload_path.mkdir(parents=True, exist_ok=True)

        # Save the file
        file_path = upload_path / filename
        with open(file_path, 'wb') as f:
            f.write(content)

        file_size = len(content)

        # Save metadata
        metadata = {
            "artifact_id": artifact_id,
            "type": "upload",
            "filename": filename,
            "size": file_size,
            "created_at": datetime.now().isoformat(),
            "storage_path": str(file_path.relative_to(STORAGE_BASE_DIR))
        }

        metadata_path = upload_path / "metadata.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Saved uploaded file {filename} for artifact {artifact_id}, size: {file_size} bytes")

        return {
            "artifact_id": artifact_id,
            "filename": filename,
            "size": file_size,
            "storage_path": str(file_path.relative_to(STORAGE_BASE_DIR))
        }

    except Exception as e:
        logger.error(f"Error saving uploaded file: {e}")
        raise


async def get_repository_files(artifact_id: str, limit: int = 100, offset: int = 0) -> Dict[str, Any]:
    """
    Get list of files in a repository artifact

    Args:
        artifact_id: The artifact ID
        limit: Maximum number of files to return
        offset: Offset for pagination

    Returns:
        Dictionary with file list and metadata
    """
    try:
        repo_path = get_repository_path(artifact_id)
        metadata_path = repo_path / "metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found for artifact {artifact_id}")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        files = metadata.get("files", [])
        total_files = len(files)

        # Apply pagination
        paginated_files = files[offset:offset + limit]

        return {
            "artifact_id": artifact_id,
            "total_files": total_files,
            "offset": offset,
            "limit": limit,
            "files": paginated_files
        }

    except Exception as e:
        logger.error(f"Error getting repository files: {e}")
        raise


async def get_repository_file_content(artifact_id: str, file_path: str) -> Dict[str, Any]:
    """
    Get content of a specific file in a repository

    Args:
        artifact_id: The artifact ID
        file_path: Relative path to the file

    Returns:
        Dictionary with file content
    """
    try:
        repo_path = get_repository_path(artifact_id)
        full_path = repo_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Check if file is within the repository path (security check)
        if not full_path.resolve().is_relative_to(repo_path.resolve()):
            raise ValueError("Invalid file path")

        with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        size = full_path.stat().st_size

        return {
            "path": file_path,
            "content": content,
            "size": size
        }

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise


async def get_uploaded_file(artifact_id: str) -> Dict[str, Any]:
    """
    Get an uploaded file

    Args:
        artifact_id: The artifact ID

    Returns:
        Dictionary with file content and metadata
    """
    try:
        upload_path = get_upload_path(artifact_id)
        metadata_path = upload_path / "metadata.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f"Metadata not found for artifact {artifact_id}")

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        filename = metadata.get("filename")
        file_path = upload_path / filename

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")

        with open(file_path, 'rb') as f:
            content = f.read()

        return {
            "artifact_id": artifact_id,
            "filename": filename,
            "content": content,
            "size": len(content),
            "metadata": metadata
        }

    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise


async def delete_artifact_files(artifact_id: str) -> bool:
    """
    Delete all files for an artifact

    Args:
        artifact_id: The artifact ID

    Returns:
        True if successful
    """
    try:
        # Try repository path
        repo_path = get_repository_path(artifact_id)
        if repo_path.exists():
            shutil.rmtree(repo_path)
            logger.info(f"Deleted repository files for artifact {artifact_id}")
            return True

        # Try upload path
        upload_path = get_upload_path(artifact_id)
        if upload_path.exists():
            shutil.rmtree(upload_path)
            logger.info(f"Deleted uploaded files for artifact {artifact_id}")
            return True

        logger.warning(f"No files found for artifact {artifact_id}")
        return False

    except Exception as e:
        logger.error(f"Error deleting artifact files: {e}")
        raise


def get_storage_stats() -> Dict[str, Any]:
    """Get storage statistics"""
    try:
        stats = {
            "repositories": 0,
            "uploads": 0,
            "total_size": 0
        }

        if REPOSITORIES_DIR.exists():
            stats["repositories"] = len(list(REPOSITORIES_DIR.iterdir()))

        if UPLOADS_DIR.exists():
            stats["uploads"] = len(list(UPLOADS_DIR.iterdir()))

        # Calculate total size
        for path in [REPOSITORIES_DIR, UPLOADS_DIR]:
            if path.exists():
                for item in path.rglob("*"):
                    if item.is_file():
                        stats["total_size"] += item.stat().st_size

        return stats

    except Exception as e:
        logger.error(f"Error getting storage stats: {e}")
        return {"error": str(e)}
