# Login Issue Fix

## Problem

The login was failing with a 401 error when using a **username** in the login form, but working when using an **email**.

### Root Cause

The `authenticate_user` method in `app/controllers/users.py` only looked up users by email address:

```python
async def authenticate_user(self, email: str, password: str):
    user = await self.get_user_by_email(email)  # Only searches by email!
    # ...
```

However, the OAuth2PasswordRequestForm uses a field called `username`, which could be either:
- A username (e.g., "alice")
- An email (e.g., "alice@example.com")

## Solution

Updated the authentication logic to support **both username and email login**:

### Changes Made

1. **Updated `authenticate_user` method** (app/controllers/users.py:173-185)
   ```python
   async def authenticate_user(self, username_or_email: str, password: str):
       # Try to find user by email first, then by username
       user = await self.get_user_by_email(username_or_email)
       if not user:
           user = await self.get_user_by_username(username_or_email)
       # ...
   ```

2. **Added `get_user_by_username` method** (app/controllers/users.py:199-209)
   ```python
   async def get_user_by_username(self, username: str) -> Optional[UserModel]:
       try:
           user = await self.collection.find_one({"username": username})
           if user:
               return UserModel(**user)
           return None
       except Exception as e:
           raise HTTPException(
               status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
               detail=f"Error retrieving user: {str(e)}",
           )
   ```

## Testing

Both login methods now work:

### Login with Username
```bash
curl -X POST "http://localhost:8000/auths/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice&password=alicepass123"
```
✅ Returns 200 OK with access token

### Login with Email
```bash
curl -X POST "http://localhost:8000/auths/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=alice@example.com&password=alicepass123"
```
✅ Returns 200 OK with access token

## Impact

- ✅ Users can now login with either username or email
- ✅ Chat UI works with usernames
- ✅ More flexible authentication
- ✅ No breaking changes to existing functionality

## Test Accounts

You can now login to the chat UI with:

**User 1:**
- Username: `testuser` OR Email: `test@example.com`
- Password: `testpass123`

**User 2:**
- Username: `alice` OR Email: `alice@example.com`
- Password: `alicepass123`

## Next Steps

Visit http://localhost:8000/chat-ui and login with any of the test accounts using their **username** or **email**!
