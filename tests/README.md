# Tests Directory

This folder contains all test files for the FastAPI Template project.

## 📋 Test Files

### Code Context Feature Tests

| File | Description | Type |
|------|-------------|------|
| [**test_context_feature.py**](test_context_feature.py) | Automated tests for code context feature | Integration |

### Chat Feature Tests

| File | Description | Type |
|------|-------------|------|
| **test_websocket.py** | WebSocket connection tests | Integration |
| **test_create_session.py** | Session creation tests | Integration |
| **test_sessions.sh** | Shell script for session testing | Integration |

## 🚀 Running Tests

### Code Context Feature Tests

```bash
# From project root
python3 tests/test_context_feature.py
```

**Prerequisites:**
- Server must be running (`docker-compose up`)
- Valid user credentials (default: admin/admin)
- MongoDB accessible

**What it tests:**
- ✅ User authentication
- ✅ Session creation
- ✅ Zip file upload with sample code
- ✅ Repository URL addition
- ✅ Context information retrieval
- ✅ Context removal

**Expected Output:**
```
=== Code Context Feature Test ===

Logging in...
✓ Login successful!

Creating test session...
✓ Session created: 507f1f77bcf86cd799439011

--- Testing Zip Upload ---
✓ Zip uploaded successfully!
  Type: zip
  Source: test_code.zip
  Files: 3 files extracted

--- Testing Repository URL ---
✓ Repository added successfully!
  Type: repository
  Source: https://github.com/test/repo

--- Testing Context Removal ---
✓ Context removed successfully!

=== Tests Complete ===
```

### WebSocket Tests

```bash
python3 tests/test_websocket.py
```

### Session Tests

```bash
# Shell script
bash tests/test_sessions.sh

# Python script
python3 tests/test_create_session.py
```

## 📝 Test Structure

### test_context_feature.py

```python
# Main test functions
- login()                    # Authenticate user
- create_session()           # Create test session
- create_test_zip()          # Generate sample zip file
- test_upload_zip()          # Test zip upload
- test_add_repository()      # Test repository URL
- test_remove_context()      # Test context removal
- test_get_session()         # Verify context data
```

## 🔧 Configuration

### Environment Variables

Tests use these default values:
```python
API_URL = "http://localhost:8000"
USERNAME = "admin"
PASSWORD = "admin"
```

To customize:
```bash
# Set environment variables
export API_URL="http://your-server:8000"
export TEST_USERNAME="your-username"
export TEST_PASSWORD="your-password"

# Run tests
python3 tests/test_context_feature.py
```

## ✅ Test Checklist

Before running tests, ensure:
- [ ] Server is running
- [ ] MongoDB is accessible
- [ ] Test user exists (admin/admin)
- [ ] No port conflicts (8000)
- [ ] Dependencies installed

## 🐛 Debugging Tests

### Common Issues

#### Test fails with "Connection refused"
**Solution:** Start the server first
```bash
docker-compose up
```

#### Test fails with "Login failed"
**Solution:** Check credentials or create test user
```bash
# Create admin user if needed
python3 -c "from app.controllers.users import create_admin_user; create_admin_user()"
```

#### Test fails with "Session not found"
**Solution:** Check MongoDB connection and database name

#### Zip upload fails
**Solution:** Check file size limits and supported extensions

### Enable Debug Output

Modify test file:
```python
# Add at top of test file
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📊 Test Coverage

### Current Coverage

| Feature | Coverage | Tests |
|---------|----------|-------|
| Code Context - Zip Upload | ✅ | test_context_feature.py |
| Code Context - Repository | ✅ | test_context_feature.py |
| Code Context - Removal | ✅ | test_context_feature.py |
| WebSocket Connection | ✅ | test_websocket.py |
| Session Creation | ✅ | test_create_session.py |
| User Authentication | ✅ | All tests |

### Areas for Additional Tests
- [ ] File size limit enforcement
- [ ] Invalid file type handling
- [ ] Concurrent context updates
- [ ] Context with large files
- [ ] Malformed zip files
- [ ] Invalid repository URLs
- [ ] Context persistence after server restart

## 🔄 CI/CD Integration

### GitHub Actions Example

```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Start services
        run: docker-compose up -d
      - name: Wait for services
        run: sleep 10
      - name: Run tests
        run: python3 tests/test_context_feature.py
      - name: Stop services
        run: docker-compose down
```

## 📝 Writing New Tests

### Template for New Test File

```python
#!/usr/bin/env python3
"""
Test script for [Feature Name]
"""

import requests
import sys

API_URL = "http://localhost:8000"

def login(username="admin", password="admin"):
    """Login and get access token"""
    response = requests.post(
        f"{API_URL}/auths/login",
        data={"username": username, "password": password}
    )
    return response.json()["access_token"] if response.status_code == 200 else None

def test_feature(token):
    """Test your feature"""
    print("\n--- Testing [Feature] ---")
    # Your test code here
    pass

def main():
    """Run all tests"""
    print("=== [Feature] Tests ===\n")

    token = login()
    if not token:
        print("Failed to login")
        sys.exit(1)

    test_feature(token)

    print("\n=== Tests Complete ===")

if __name__ == "__main__":
    main()
```

### Best Practices

1. **Isolate tests** - Each test should be independent
2. **Clean up** - Remove test data after tests
3. **Use assertions** - Validate expected outcomes
4. **Handle errors** - Catch and report exceptions
5. **Document tests** - Explain what each test does
6. **Use realistic data** - Test with real-world scenarios

## 🎯 Test Scenarios

### Manual Test Scenarios

#### Scenario 1: Basic Workflow
1. Login with valid credentials
2. Create new chat session
3. Upload zip file with code
4. Verify context badge appears
5. Send message in chat
6. Remove context
7. Verify badge removed

#### Scenario 2: Repository URL
1. Login and create session
2. Add repository URL
3. Verify URL is stored
4. Replace with different URL
5. Remove context

#### Scenario 3: Error Handling
1. Try to upload non-zip file
2. Try to add invalid URL
3. Try to access other user's session
4. Try to upload oversized file

## 📈 Performance Testing

### Load Testing Example

```python
import concurrent.futures
import time

def load_test_upload():
    """Test concurrent uploads"""
    tokens = [login() for _ in range(10)]
    sessions = [create_session(t) for t in tokens]

    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(test_upload_zip, tokens[i], sessions[i])
            for i in range(10)
        ]
        results = [f.result() for f in futures]

    duration = time.time() - start
    print(f"10 uploads completed in {duration:.2f}s")
```

## 🤝 Contributing Tests

When adding new features:

1. **Write tests first** (TDD approach)
2. **Cover happy path** - Normal usage
3. **Cover edge cases** - Boundary conditions
4. **Cover error cases** - Invalid inputs
5. **Update this README** - Document new tests
6. **Run all tests** - Ensure nothing breaks

## 📞 Support

- **Test failures:** Check debugging section above
- **Adding tests:** Follow template and best practices
- **CI/CD setup:** See integration examples
- **Questions:** Review existing test files

---

**Happy Testing! 🧪**
