# Documentation Index

Welcome to the FastAPI Template documentation! This folder contains all the documentation for the project features.

## 📚 Documentation Files

### Code Context Feature

The Code Context feature allows users to add code repositories or upload zip files as context to their chat sessions.

| Document | Description | Audience |
|----------|-------------|----------|
| [**FEATURE_README.md**](FEATURE_README.md) | Complete overview and implementation guide | All users & developers |
| [**QUICK_START_GUIDE.md**](QUICK_START_GUIDE.md) | Step-by-step user guide with examples | End users |
| [**CODE_CONTEXT_FEATURE.md**](CODE_CONTEXT_FEATURE.md) | Technical documentation and API reference | Developers |
| [**CONTEXT_FEATURE_SUMMARY.md**](CONTEXT_FEATURE_SUMMARY.md) | Implementation summary and changes | Developers & reviewers |

## 🚀 Quick Navigation

### For End Users
**Want to add code context to your chats?**
→ Start with [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md)

### For Developers
**Want to understand the implementation?**
→ Start with [FEATURE_README.md](FEATURE_README.md)

**Need API documentation?**
→ Check [CODE_CONTEXT_FEATURE.md](CODE_CONTEXT_FEATURE.md)

**Want a quick summary?**
→ Read [CONTEXT_FEATURE_SUMMARY.md](CONTEXT_FEATURE_SUMMARY.md)

## 📖 Reading Order

### New Users
1. [QUICK_START_GUIDE.md](QUICK_START_GUIDE.md) - Learn how to use the feature
2. [FEATURE_README.md](FEATURE_README.md) - Understand what's possible

### New Developers
1. [FEATURE_README.md](FEATURE_README.md) - Get the big picture
2. [CONTEXT_FEATURE_SUMMARY.md](CONTEXT_FEATURE_SUMMARY.md) - See what changed
3. [CODE_CONTEXT_FEATURE.md](CODE_CONTEXT_FEATURE.md) - Deep dive into implementation

### Reviewers
1. [CONTEXT_FEATURE_SUMMARY.md](CONTEXT_FEATURE_SUMMARY.md) - Quick overview of changes
2. [CODE_CONTEXT_FEATURE.md](CODE_CONTEXT_FEATURE.md) - Technical details
3. Review code in `app/routers/chat_sessions.py`

## 🔗 Related Resources

### Code Files
- **Models:** `app/models/chat_sessions.py`
- **Schemas:** `app/schemas/chat_sessions.py`
- **Endpoints:** `app/routers/chat_sessions.py`
- **UI:** `app/static/chat_sessions.html`

### Tests
- **Automated Tests:** `tests/test_context_feature.py`
- See [tests/README.md](../tests/README.md) for testing guide

## 🤝 Contributing

When adding new features or documentation:

1. **Create comprehensive documentation** in this folder
2. **Follow the existing structure:**
   - Feature README (overview)
   - Quick Start Guide (user-facing)
   - Technical Documentation (developer-facing)
   - Summary (for reviewers)
3. **Update this index** with links to new docs
4. **Add tests** in the `tests/` folder

## 📝 Documentation Standards

### File Naming
- Use descriptive names with underscores
- Include feature name in filename
- Use `.md` extension for Markdown

### Content Structure
- Start with clear title and overview
- Include table of contents for long docs
- Use code examples and screenshots where helpful
- Add links to related documents
- Keep language clear and concise

### Formatting
- Use Markdown for all documentation
- Include emoji for visual appeal (sparingly)
- Use tables for comparisons
- Use code blocks with language tags
- Add clear section headers

## 🔍 Search Tips

Looking for something specific?

- **API Endpoints:** Check CODE_CONTEXT_FEATURE.md
- **User Guide:** Check QUICK_START_GUIDE.md
- **Code Changes:** Check CONTEXT_FEATURE_SUMMARY.md
- **Architecture:** Check FEATURE_README.md
- **Testing:** Check ../tests/README.md

## 📞 Need Help?

- Check the relevant documentation file above
- Review code examples in the docs
- Run the test suite in `tests/`
- Check the main project README

---

**Last Updated:** 2025-11-04
**Version:** 1.0.0
