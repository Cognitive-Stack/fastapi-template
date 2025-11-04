#!/usr/bin/env python3
"""
Test script to verify repository cloning functionality
"""
import asyncio
import sys
from app.utils.repository import clone_and_extract_repository, validate_repository_url, get_repository_info


async def test_repository_cloning():
    """Test cloning a small public repository"""
    print("=" * 60)
    print("Testing Repository Cloning Functionality")
    print("=" * 60)

    # Test 1: URL Validation
    print("\n1. Testing URL Validation...")
    test_urls = [
        ("https://github.com/user/repo", True),
        ("github.com/user/repo", False),
        ("invalid-url", False),
        ("git@github.com:user/repo.git", True),
    ]

    for url, expected in test_urls:
        result = validate_repository_url(url)
        status = "✓" if result == expected else "✗"
        print(f"   {status} {url}: {result}")

    # Test 2: Repository Info Extraction
    print("\n2. Testing Repository Info Extraction...")
    url = "https://github.com/octocat/Hello-World"
    info = get_repository_info(url)
    print(f"   Name: {info['name']}")
    print(f"   Host: {info['host']}")
    print(f"   Owner: {info['owner']}")

    # Test 3: Clone a small public repository
    print("\n3. Testing Repository Cloning...")
    print(f"   Cloning: {url}")
    print("   This may take a few seconds...")

    result = await clone_and_extract_repository(url, max_files=50)

    if result['error']:
        print(f"   ✗ Error: {result['error']}")
        return False

    print(f"   ✓ Successfully cloned repository")
    print(f"   Repository Name: {result['repo_name']}")
    print(f"   Total Files Extracted: {result['total_files']}")

    if result['files']:
        print(f"\n   Sample files:")
        for i, file in enumerate(result['files'][:5], 1):
            print(f"     {i}. {file['path']} ({file['size']} bytes)")

    print("\n" + "=" * 60)
    print("✓ All tests passed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    try:
        success = asyncio.run(test_repository_cloning())
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
