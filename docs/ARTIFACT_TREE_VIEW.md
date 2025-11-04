# Artifact Tree View UI

## Overview

The chat sessions UI now includes an **interactive tree view** that displays all artifacts for the current chat session. This provides users with a visual representation of uploaded repositories, PDFs, and other files.

## Features

### 📁 Artifact Panel

- **Auto-displays** when artifacts are present in the session
- **Collapsible** panel with +/− button
- **Smooth animations** for expand/collapse
- **Persistent across sessions** - shows artifacts for each chat

### 🌳 Tree Structure

Each artifact displays:
- **Icon** based on type (📦 repository, 📄 PDF, 📁 ZIP, etc.)
- **Name** of the artifact
- **Metadata** (type, size, file count)
- **Action buttons** (Download, Delete)
- **Expandable file list** (for repositories)

### 📂 File Tree

When expanded, repositories show:
- **File paths** in a hierarchical structure
- **File icons** based on extension (🐍 Python, 📜 JavaScript, etc.)
- **File sizes** in KB
- **Clickable files** (view file content - coming soon)
- **Pagination** (shows first 50 files with stats)

## UI Components

### 1. Artifacts Panel

```html
<div class="artifacts-panel" id="artifactsPanel">
    <div class="artifacts-header">
        <h3>📁 Artifacts</h3>
        <button class="collapse-btn">−</button>
    </div>
    <div class="artifacts-tree">
        <!-- Artifact items here -->
    </div>
</div>
```

**Location:** Between chat header and messages container

### 2. Artifact Item Structure

```
┌─ Artifact Item ────────────────────────────┐
│ 📦 my-repo                          [⬇][🗑]│
│ repository • 2.5 MB • 45 files          [▶]│
├────────────────────────────────────────────┤
│ 🐍 src/main.py              2.3 KB        │
│ 📜 src/utils.js             1.8 KB        │
│ 📝 README.md                0.9 KB        │
│ ...                                        │
│ Showing 50 of 45 files                     │
└────────────────────────────────────────────┘
```

### 3. Artifact Types & Icons

| Type       | Icon | Description           |
|------------|------|-----------------------|
| repository | 📦   | Git repository        |
| pdf        | 📄   | PDF document          |
| doc        | 📝   | Word document         |
| zip        | 📁   | ZIP archive           |
| text       | 📃   | Text file             |
| file       | 📎   | Generic file          |

### 4. File Extension Icons

| Extension | Icon | Language/Type    |
|-----------|------|------------------|
| .py       | 🐍   | Python           |
| .js       | 📜   | JavaScript       |
| .ts       | 📘   | TypeScript       |
| .tsx/.jsx | ⚛️   | React            |
| .html     | 🌐   | HTML             |
| .css      | 🎨   | CSS              |
| .json     | 📋   | JSON             |
| .md       | 📝   | Markdown         |
| .yml      | ⚙️   | YAML             |
| .sql      | 🗄️   | SQL              |
| .sh       | ⚡   | Shell script     |
| .go       | 🔵   | Go               |
| .rs       | 🦀   | Rust             |
| .java     | ☕   | Java             |
| .rb       | 💎   | Ruby             |
| .php      | 🐘   | PHP              |

## Functionality

### Collapse/Expand Panel

```javascript
// Click the −/+ button
collapseArtifactsBtn.addEventListener('click', () => {
    panel.classList.toggle('collapsed');
    button.textContent = panel.classList.contains('collapsed') ? '+' : '−';
});
```

### Toggle File List

```javascript
// Click on artifact header to expand/collapse files
async function toggleArtifact(artifactId) {
    // Toggle expanded state
    // Load files if not already loaded
    await loadArtifactFiles(artifactId);
}
```

### Load Files

```javascript
// Lazy load files when artifact is expanded
async function loadArtifactFiles(artifactId) {
    const response = await fetch(
        `${API_URL}/chat/sessions/${sessionId}/artifacts/${artifactId}/files?limit=50`
    );
    const data = await response.json();
    renderFileTree(data.files);
}
```

### Download Artifact

```javascript
// Download PDF/DOC files
async function downloadArtifact(artifactId) {
    const response = await fetch(
        `${API_URL}/chat/sessions/${sessionId}/artifacts/${artifactId}/download`
    );
    const blob = await response.blob();
    // Trigger download
}
```

### Delete Artifact

```javascript
// Remove artifact from session
async function removeArtifact(artifactId) {
    if (confirm('Are you sure?')) {
        await fetch(
            `${API_URL}/chat/sessions/${sessionId}/artifacts/${artifactId}`,
            { method: 'DELETE' }
        );
        await loadArtifacts(); // Refresh list
    }
}
```

## Styling

### Colors & Theme

- **Background**: `#f8f9fa` (light gray)
- **Border**: `#dee2e6` (gray)
- **Text**: `#495057` (dark gray)
- **Hover**: `#e9ecef` (lighter gray)
- **Download**: `#007bff` (blue)
- **Delete**: `#dc3545` (red)

### Animations

```css
.artifact-files {
    max-height: 0;
    overflow: hidden;
    transition: max-height 0.3s ease;
}

.artifact-files.expanded {
    max-height: 400px;
    overflow-y: auto;
}

.expand-icon {
    transition: transform 0.2s;
}

.expand-icon.expanded {
    transform: rotate(90deg);
}
```

### Responsive Design

- **Max height**: 300px with scroll
- **Sticky header**: Stays visible while scrolling
- **Flexible layout**: Adapts to content
- **Overflow handling**: Scrollable file lists

## User Interactions

### 1. View Artifacts

1. Select a chat session
2. Artifacts panel appears automatically if artifacts exist
3. See list of all artifacts with metadata

### 2. Expand Repository

1. Click on artifact header
2. File list expands with animation
3. Files load from API (lazy loading)
4. See file tree with icons and sizes

### 3. Download PDF/DOC

1. Click "Download" button on PDF/DOC artifact
2. File downloads to browser
3. Original filename preserved

### 4. Delete Artifact

1. Click "Delete" button
2. Confirm deletion
3. Artifact removed from database and filesystem
4. Tree view refreshes automatically

### 5. Collapse Panel

1. Click "−" button to collapse
2. Panel minimizes to header only
3. Click "+" to expand again

## API Integration

### Get Artifacts

```http
GET /chat/sessions/{session_id}/artifacts
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": "artifact_id",
    "name": "my-repo",
    "type": "repository",
    "size": 2621440,
    "metadata": {
      "total_files": 45,
      "storage_type": "object"
    }
  }
]
```

### Get Artifact Files

```http
GET /chat/sessions/{session_id}/artifacts/{artifact_id}/files?limit=50&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
{
  "artifact_id": "artifact_id",
  "total_files": 45,
  "files": [
    {
      "path": "src/main.py",
      "size": 2348
    }
  ]
}
```

### Download Artifact

```http
GET /chat/sessions/{session_id}/artifacts/{artifact_id}/download
Authorization: Bearer <token>
```

**Response:** Binary file with content-disposition header

## Future Enhancements

- [ ] **File content viewer** - View file content in modal
- [ ] **Search files** - Filter files by name
- [ ] **Folder structure** - Hierarchical tree view
- [ ] **File syntax highlighting** - Code preview
- [ ] **Download repository** - Download entire repository as ZIP
- [ ] **Diff viewer** - Compare files
- [ ] **File editor** - Edit files directly
- [ ] **Drag & drop** - Reorder artifacts
- [ ] **Bulk actions** - Delete multiple artifacts

## Performance Considerations

### Lazy Loading

- Files loaded only when artifact is expanded
- Reduces initial page load time
- API calls made on-demand

### Pagination

- Only first 50 files shown by default
- Stats show total file count
- Can be extended with "Load More" button

### Caching

- Loaded files cached in DOM
- No re-fetch on collapse/expand
- Refresh on artifact changes

### Animations

- CSS transitions for smooth UX
- Hardware-accelerated transforms
- Debounced events

## Testing

### Manual Testing

1. **Add repository** → Verify tree appears
2. **Click expand** → Verify files load
3. **Click file** → Verify placeholder alert
4. **Download PDF** → Verify download works
5. **Delete artifact** → Verify removal
6. **Collapse panel** → Verify animation
7. **Switch sessions** → Verify artifacts update

### Browser Compatibility

- ✅ Chrome/Edge (Chromium)
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

## Accessibility

- **Keyboard navigation** - Tab through items
- **ARIA labels** - Screen reader support (to be added)
- **Focus indicators** - Visible focus states
- **Color contrast** - WCAG AA compliant

## Code Structure

### JavaScript Functions

```
updateArtifactsDisplay()      // Main render function
├── createArtifactTreeItem()  // Create artifact UI
├── getArtifactIcon()         // Get icon by type
└── toggleArtifact()          // Expand/collapse
    └── loadArtifactFiles()   // Fetch files
        └── renderFileTree()  // Render file list
            └── getFileIcon() // Get icon by extension
```

### Event Handlers

- `collapseArtifactsBtn.click` - Toggle panel
- `artifact-header.click` - Toggle files
- `downloadArtifact()` - Download file
- `removeArtifact()` - Delete artifact
- `viewFile()` - View file (coming soon)

## Summary

The artifact tree view provides a **comprehensive, interactive interface** for managing and exploring uploaded artifacts in chat sessions. It features:

- 🎨 **Beautiful design** with icons and animations
- ⚡ **Fast performance** with lazy loading
- 📦 **Rich metadata** display
- 🔄 **Automatic updates** on artifact changes
- 📱 **Responsive** across devices
- ♿ **Accessible** keyboard navigation

This enhancement significantly improves the user experience for working with code repositories and documents in the chat interface.
