#!/usr/bin/env python3
"""
Test script for the code context feature.
This script tests the context endpoints.
"""

import requests
import zipfile
import io
import os

API_URL = "http://localhost:8000"

def login(username="admin", password="admin"):
    """Login and get access token"""
    response = requests.post(
        f"{API_URL}/auths/login",
        data={"username": username, "password": password},
        headers={"Content-Type": "application/x-www-form-urlencoded"}
    )
    if response.status_code == 200:
        return response.json()["access_token"]
    else:
        print(f"Login failed: {response.status_code}")
        print(response.text)
        return None

def create_session(token, title="Test Session"):
    """Create a new chat session"""
    response = requests.post(
        f"{API_URL}/chat/sessions",
        json={"title": title},
        headers={"Authorization": f"Bearer {token}"}
    )
    if response.status_code == 201:
        return response.json()["_id"]
    else:
        print(f"Create session failed: {response.status_code}")
        print(response.text)
        return None

def create_test_zip():
    """Create a test zip file with sample code"""
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Add a Python file
        zip_file.writestr("main.py", """
def hello_world():
    print("Hello, World!")

if __name__ == "__main__":
    hello_world()
""")
        # Add a JavaScript file
        zip_file.writestr("app.js", """
function greet(name) {
    console.log(`Hello, ${name}!`);
}

greet("World");
""")
        # Add a README
        zip_file.writestr("README.md", """
# Test Project

This is a test project for demonstrating code context.
""")

    zip_buffer.seek(0)
    return zip_buffer

def test_upload_zip(token, session_id):
    """Test uploading a zip file as context"""
    print("\n--- Testing Zip Upload ---")

    zip_file = create_test_zip()
    files = {"file": ("test_code.zip", zip_file, "application/zip")}

    response = requests.post(
        f"{API_URL}/chat/sessions/{session_id}/context/upload",
        files=files,
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        print("✓ Zip uploaded successfully!")
        if data.get("context"):
            ctx = data["context"]
            print(f"  Type: {ctx.get('type')}")
            print(f"  Source: {ctx.get('source')}")
            print(f"  Files: {len(ctx.get('files', []))} files extracted")
            return True
    else:
        print(f"✗ Upload failed: {response.status_code}")
        print(response.text)
        return False

def test_add_repository(token, session_id):
    """Test adding a repository URL as context"""
    print("\n--- Testing Repository URL ---")

    response = requests.post(
        f"{API_URL}/chat/sessions/{session_id}/context/repository",
        json={"repository_url": "https://github.com/test/repo"},
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        print("✓ Repository added successfully!")
        if data.get("context"):
            ctx = data["context"]
            print(f"  Type: {ctx.get('type')}")
            print(f"  Source: {ctx.get('source')}")
            return True
    else:
        print(f"✗ Add repository failed: {response.status_code}")
        print(response.text)
        return False

def test_remove_context(token, session_id):
    """Test removing context from session"""
    print("\n--- Testing Context Removal ---")

    response = requests.delete(
        f"{API_URL}/chat/sessions/{session_id}/context",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        print("✓ Context removed successfully!")
        return True
    else:
        print(f"✗ Remove context failed: {response.status_code}")
        print(response.text)
        return False

def test_get_session(token, session_id):
    """Get session details to verify context"""
    print("\n--- Getting Session Details ---")

    response = requests.get(
        f"{API_URL}/chat/sessions/{session_id}",
        headers={"Authorization": f"Bearer {token}"}
    )

    if response.status_code == 200:
        data = response.json()
        print("✓ Session retrieved successfully!")
        if data.get("context"):
            print("  Has context:")
            ctx = data["context"]
            print(f"    Type: {ctx.get('type')}")
            print(f"    Source: {ctx.get('source')}")
            if ctx.get('files'):
                print(f"    Files: {len(ctx.get('files', []))}")
        else:
            print("  No context attached")
        return True
    else:
        print(f"✗ Get session failed: {response.status_code}")
        print(response.text)
        return False

def main():
    """Run all tests"""
    print("=== Code Context Feature Test ===\n")

    # Login
    print("Logging in...")
    token = login()
    if not token:
        print("Failed to login. Make sure the server is running and credentials are correct.")
        return
    print("✓ Login successful!\n")

    # Create session
    print("Creating test session...")
    session_id = create_session(token, "Context Test Session")
    if not session_id:
        print("Failed to create session.")
        return
    print(f"✓ Session created: {session_id}\n")

    # Test 1: Upload zip file
    if test_upload_zip(token, session_id):
        test_get_session(token, session_id)

    # Test 2: Replace with repository URL
    if test_add_repository(token, session_id):
        test_get_session(token, session_id)

    # Test 3: Remove context
    if test_remove_context(token, session_id):
        test_get_session(token, session_id)

    print("\n=== Tests Complete ===")

if __name__ == "__main__":
    main()
