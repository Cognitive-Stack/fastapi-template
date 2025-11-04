"""
Repository cloning and file extraction utilities
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
from git import Repo, GitCommandError
from loguru import logger


# Code file extensions to extract
CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.tsx', '.jsx', '.java', '.cpp', '.c', '.h', '.hpp',
    '.cs', '.go', '.rs', '.rb', '.php', '.swift', '.kt', '.scala',
    '.sql', '.html', '.css', '.json', '.xml', '.yaml', '.yml',
    '.md', '.txt', '.sh', '.bash', '.r', '.m', '.vue', '.svelte',
    '.dart', '.lua', '.pl', '.pm', '.gradle', '.proto', '.thrift'
}

# Directories to ignore
IGNORE_DIRS = {
    '.git', '.svn', '.hg', 'node_modules', '__pycache__', '.pytest_cache',
    'venv', 'env', '.env', 'virtualenv', '.venv', 'dist', 'build',
    '.idea', '.vscode', '.vs', 'target', 'bin', 'obj', 'out',
    'coverage', '.nyc_output', '.next', '.nuxt', 'vendor'
}

# Maximum file size to process (5MB)
MAX_FILE_SIZE = 5 * 1024 * 1024


async def clone_and_extract_repository(repo_url: str, max_files: int = 500, artifact_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Clone a Git repository and extract code files.

    Args:
        repo_url: URL of the Git repository
        max_files: Maximum number of files to extract
        artifact_id: If provided, files will be saved directly to object storage

    Returns:
        Dictionary containing:
        - files: List of file dictionaries with path and size (no content if artifact_id provided)
        - total_files: Total number of files extracted
        - repo_name: Name of the repository
        - error: Error message if any
        - temp_dir: Temporary directory path (for later processing)
    """
    temp_dir = None
    result = {
        'files': [],
        'total_files': 0,
        'repo_name': '',
        'error': None,
        'temp_dir': None
    }

    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='repo_')
        logger.info(f"Cloning repository {repo_url} to {temp_dir}")

        # Clone repository with depth=1 for faster cloning
        try:
            repo = Repo.clone_from(
                repo_url,
                temp_dir,
                depth=1,
                single_branch=True
            )

            # Extract repository name from URL
            repo_name = repo_url.rstrip('/').split('/')[-1]
            if repo_name.endswith('.git'):
                repo_name = repo_name[:-4]
            result['repo_name'] = repo_name

        except GitCommandError as e:
            logger.error(f"Failed to clone repository: {e}")
            result['error'] = f"Failed to clone repository: {str(e)}"
            return result

        # Extract code files
        files = []
        file_count = 0

        for root, dirs, filenames in os.walk(temp_dir):
            # Remove ignored directories from traversal
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

            # Calculate relative path
            rel_root = os.path.relpath(root, temp_dir)

            for filename in filenames:
                # Check file extension
                file_ext = Path(filename).suffix.lower()
                if file_ext not in CODE_EXTENSIONS:
                    continue

                # Check max files limit
                if file_count >= max_files:
                    logger.warning(f"Reached max files limit ({max_files})")
                    break

                file_path = os.path.join(root, filename)

                # Check file size
                try:
                    file_size = os.path.getsize(file_path)
                    if file_size > MAX_FILE_SIZE:
                        logger.debug(f"Skipping large file: {filename} ({file_size} bytes)")
                        continue
                except OSError:
                    continue

                # Calculate relative path for storage
                try:
                    if rel_root == '.':
                        relative_path = filename
                    else:
                        relative_path = os.path.join(rel_root, filename)

                    # Only read content if no artifact_id (legacy mode)
                    if artifact_id is None:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                        files.append({
                            'path': relative_path,
                            'content': content,
                            'size': file_size
                        })
                    else:
                        # Just store metadata, files will be processed later
                        files.append({
                            'path': relative_path,
                            'size': file_size,
                            'full_path': file_path  # Keep track of file location for later
                        })

                    file_count += 1

                except Exception as e:
                    logger.warning(f"Failed to process file {file_path}: {e}")
                    continue

            # Break outer loop if max files reached
            if file_count >= max_files:
                break

        result['files'] = files
        result['total_files'] = file_count
        result['temp_dir'] = temp_dir  # Return temp_dir for later cleanup

        logger.info(f"Extracted {file_count} files from repository {repo_name}")

    except Exception as e:
        logger.error(f"Error processing repository: {e}")
        result['error'] = str(e)
        # Cleanup on error
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup temp directory: {cleanup_error}")

    # Note: If artifact_id is provided, don't cleanup temp_dir yet
    # It will be cleaned up after files are saved to object storage
    if artifact_id is None and temp_dir and os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
            logger.debug(f"Cleaned up temporary directory: {temp_dir}")
        except Exception as e:
            logger.error(f"Failed to cleanup temp directory: {e}")

    return result


def validate_repository_url(url: str) -> bool:
    """
    Validate if the URL is a valid Git repository URL.

    Args:
        url: Repository URL to validate

    Returns:
        True if valid, False otherwise
    """
    if not url:
        return False

    # Check for common Git hosting services
    git_hosts = [
        'github.com',
        'gitlab.com',
        'bitbucket.org',
        'git.sr.ht',
        'codeberg.org',
        'gitea.io'
    ]

    # Check if URL contains any of the known Git hosts
    url_lower = url.lower()
    if any(host in url_lower for host in git_hosts):
        return True

    # Check if URL ends with .git
    if url_lower.endswith('.git'):
        return True

    # Basic URL validation
    if url.startswith(('http://', 'https://', 'git://', 'ssh://', 'git@')):
        return True

    return False


def get_repository_info(repo_url: str) -> Dict[str, str]:
    """
    Extract basic information from repository URL.

    Args:
        repo_url: Repository URL

    Returns:
        Dictionary with repository name and host
    """
    info = {
        'name': '',
        'host': '',
        'owner': ''
    }

    try:
        # Clean URL
        url = repo_url.rstrip('/')

        # Extract repository name
        name = url.split('/')[-1]
        if name.endswith('.git'):
            name = name[:-4]
        info['name'] = name

        # Extract owner/organization
        parts = url.split('/')
        if len(parts) >= 2:
            info['owner'] = parts[-2]

        # Extract host
        if 'github.com' in url:
            info['host'] = 'GitHub'
        elif 'gitlab.com' in url:
            info['host'] = 'GitLab'
        elif 'bitbucket.org' in url:
            info['host'] = 'Bitbucket'
        else:
            info['host'] = 'Git'

    except Exception as e:
        logger.error(f"Failed to extract repository info: {e}")

    return info
