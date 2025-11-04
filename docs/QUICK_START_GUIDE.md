# Quick Start Guide - Code Context Feature

## What is This Feature?

The Code Context feature allows you to add your codebase as context to chat sessions. This helps AI assistants understand your code and provide more relevant responses.

## Getting Started (3 Simple Steps)

### Step 1: Open Chat Sessions
Navigate to: `http://localhost:8000/static/chat_sessions.html`

### Step 2: Login
Use your credentials to login

### Step 3: Add Context
1. Select or create a chat session
2. Click the green **"+ Add Code Context"** button in the header
3. Choose one of two options:

## Option A: Add Repository URL

**Best for:** Public GitHub/GitLab repositories

1. Click "Repository URL" card
2. Enter your repository URL (e.g., `https://github.com/username/repo`)
3. Click "Add Repository"
4. Done! A green badge will appear next to your chat title

**Example URLs:**
- `https://github.com/fastapi/fastapi`
- `https://github.com/python/cpython`
- `https://gitlab.com/username/project`

## Option B: Upload Zip File

**Best for:** Private code or local projects

1. Click "Upload Zip File" card
2. Click "Choose File" and select your zip file
3. Click "Upload Zip"
4. Done! The system will automatically:
   - Extract code files
   - Filter out binary files
   - Store only relevant code
   - Show you how many files were processed

**Supported File Types:**
- Python (`.py`)
- JavaScript/TypeScript (`.js`, `.ts`, `.jsx`, `.tsx`)
- Java (`.java`)
- C/C++ (`.c`, `.cpp`, `.h`)
- And 20+ more languages!

## What Happens After Adding Context?

### You'll See:
1. **Green Badge** next to chat title showing "Repository" or "Zip"
2. **Context is Saved** with your session
3. **Ready to Use** - AI can reference your code in responses

### To View Context Details:
1. Click "+ Add Code Context" again
2. Scroll to bottom of modal
3. See "Current Context" section with:
   - Context type
   - Source (URL or filename)
   - Number of files extracted
   - "Remove Context" button

## Managing Context

### To Remove Context:
1. Click "+ Add Code Context"
2. Scroll down to "Current Context"
3. Click "Remove Context" button
4. Confirm removal

### To Replace Context:
1. Simply add new context (either URL or zip)
2. New context automatically replaces the old one

## Tips & Best Practices

### ✅ DO:
- Use zip files for private or local code
- Use repository URLs for public GitHub/GitLab repos
- Compress only relevant code folders (not node_modules, etc.)
- Keep individual files under 1MB

### ❌ DON'T:
- Don't include binary files (they'll be skipped anyway)
- Don't upload entire large projects (be selective)
- Don't include sensitive data in context

## Example Workflow

**Scenario:** You want to discuss your React project with an AI assistant

1. **Prepare Code:**
   ```bash
   cd my-react-project
   zip -r my-project.zip src/ public/ package.json README.md
   ```

2. **Upload:**
   - Open chat sessions UI
   - Create session named "React Project Discussion"
   - Click "+ Add Code Context"
   - Choose "Upload Zip File"
   - Select `my-project.zip`
   - Click "Upload Zip"

3. **Chat:**
   - See "Zip" badge appear
   - Start chatting about your code
   - AI can reference your uploaded files

## Troubleshooting

### "File must be a zip archive"
**Solution:** Make sure your file ends with `.zip`

### "Invalid repository URL"
**Solution:** URL must start with `http://` or `https://`

### "No files extracted from zip"
**Solution:** Your zip might not contain supported file types. Check the supported extensions list.

### Upload Takes Too Long
**Solution:**
- Your zip might be too large
- Try zipping only essential files
- Remove large dependencies (node_modules, etc.)

## Testing the Feature

### Quick Test with Sample Data:

1. **Create a test zip:**
   ```bash
   # Create a test directory
   mkdir test-code
   cd test-code

   # Create sample files
   echo "print('Hello, World!')" > main.py
   echo "console.log('Hello!');" > app.js
   echo "# Test Project" > README.md

   # Zip it
   cd ..
   zip -r test-code.zip test-code/
   ```

2. **Upload it:**
   - Open chat UI
   - Create test session
   - Upload the zip
   - Should see "3 files" extracted

### Automated Test:
```bash
python3 test_context_feature.py
```

## Video Tutorial (Steps)

1. **Login Screen** → Enter credentials → Click Login
2. **Sessions List** → Click "+ New Chat" → Enter title
3. **Chat View** → Click green "+ Add Code Context" button
4. **Modal Opens** → Two cards displayed
5. **Choose Option:**
   - **Repository**: Enter URL → Click "Add Repository"
   - **Zip**: Click "Choose File" → Select zip → Click "Upload Zip"
6. **Success** → Badge appears → Modal closes
7. **Verify** → Click "+ Add Code Context" again → See "Current Context"
8. **Chat** → Start sending messages with code context available

## FAQ

**Q: Can I add multiple contexts to one session?**
A: No, each session can have one context. Adding new context replaces the old one.

**Q: Is my code secure?**
A: Yes, context is stored in your database and only accessible to you.

**Q: What if my repository is private?**
A: For now, use the zip upload option. GitHub integration coming soon!

**Q: How large can my zip file be?**
A: Individual files are limited to 1MB. Total zip size should be reasonable (under 50MB recommended).

**Q: Can I see the extracted files?**
A: The UI shows file count. Full file browser coming in future update.

**Q: Does it work with GitLab/Bitbucket?**
A: Repository URL accepts any valid URL. Auto-fetching is not yet implemented but planned.

## Next Steps

- Try both methods (URL and zip)
- Experiment with different code projects
- Use context in your chats
- Provide feedback for improvements!

## Need Help?

- Check: `CODE_CONTEXT_FEATURE.md` for detailed documentation
- Run: `python3 test_context_feature.py` to verify setup
- Review: Backend code in `app/routers/chat_sessions.py`

---

**Happy Coding! 🚀**
