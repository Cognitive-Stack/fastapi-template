# UI Update Guide - Context to Artifacts

## Overview

This guide shows exactly what needs to change in `app/static/chat_sessions.html` to support the new artifacts system.

## Key Changes Required

### 1. Update Button Text

**Find:**
```html
<button class="add-context-btn" id="addContextBtn" style="display: none;">+ Add Code Context</button>
```

**Replace with:**
```html
<button class="add-context-btn" id="addArtifactsBtn" style="display: none;">📎 Manage Artifacts</button>
```

### 2. Update Modal Title

**Find:**
```html
<h3>Add Code Context</h3>
```

**Replace with:**
```html
<h3>Manage Artifacts</h3>
```

### 3. Update CSS Class Names (Optional but recommended)

**Find:** `.add-context-btn`, `.context-badge`, etc.

**Replace with:** `.add-artifacts-btn`, `.artifacts-badge`, etc.

### 4. Add Artifacts List Display

**Add this HTML after the modal header:**
```html
<!-- Artifacts List -->
<div id="artifactsList" style="margin-bottom: 20px;">
    <h4>Current Artifacts</h4>
    <div id="artifactsContainer"></div>
</div>
```

### 5. Update JavaScript Variables

**Find:**
```javascript
const addContextBtn = document.getElementById('addContextBtn');
let currentContext = null;
```

**Replace with:**
```javascript
const addArtifactsBtn = document.getElementById('addArtifactsBtn');
let artifacts = [];
```

### 6. Update API Endpoints in JavaScript

#### Load Artifacts
**Find:**
```javascript
// Old - no code existed for loading context
```

**Add:**
```javascript
async function loadArtifacts() {
    if (!currentSessionId) return;

    try {
        const response = await fetch(`${API_URL}/chat/sessions/${currentSessionId}/artifacts`, {
            headers: {'Authorization': `Bearer ${accessToken}`}
        });

        if (response.ok) {
            artifacts = await response.json();
            renderArtifacts();
            updateArtifactsBadge();
        }
    } catch (error) {
        console.error('Failed to load artifacts:', error);
    }
}
```

#### Render Artifacts List
**Add this new function:**
```javascript
function renderArtifacts() {
    const container = document.getElementById('artifactsContainer');
    if (!artifacts || artifacts.length === 0) {
        container.innerHTML = '<p style="color: #999;">No artifacts attached</p>';
        return;
    }

    container.innerHTML = artifacts.map(artifact => `
        <div class="artifact-item" style="padding: 10px; margin: 5px 0; background: #f0f0f0; border-radius: 6px; display: flex; justify-content: space-between; align-items: center;">
            <div>
                <strong>${escapeHtml(artifact.name)}</strong>
                <span style="margin-left: 10px; padding: 2px 8px; background: #667eea; color: white; border-radius: 12px; font-size: 11px;">
                    ${artifact.type}
                </span>
                ${artifact.files ? `<br><small>${artifact.files.length} files</small>` : ''}
            </div>
            <button class="session-action-btn delete" onclick="deleteArtifact('${artifact._id}')" style="margin: 0;">
                Delete
            </button>
        </div>
    `).join('');
}
```

#### Create Repository Artifact
**Find:**
```javascript
// Submit repository URL (old code around line 1002)
const response = await fetch(`${API_URL}/chat/sessions/${currentSessionId}/context/repository`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({ repository_url: url })
});
```

**Replace with:**
```javascript
const response = await fetch(`${API_URL}/chat/sessions/${currentSessionId}/artifacts`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`,
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        type: 'repository',
        name: url.split('/').pop() || 'Repository',
        source: url
    })
});
```

#### Upload Zip Artifact
**Find:**
```javascript
// Submit zip file (old code around line 1057)
const response = await fetch(`${API_URL}/chat/sessions/${currentSessionId}/context/upload`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: formData
});
```

**Replace with:**
```javascript
const response = await fetch(`${API_URL}/chat/sessions/${currentSessionId}/artifacts/upload`, {
    method: 'POST',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    },
    body: formData
});
```

#### Delete Artifact
**Find:**
```javascript
// Remove context (old code around line 1089)
const response = await fetch(`${API_URL}/chat/sessions/${currentSessionId}/context`, {
    method: 'DELETE',
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});
```

**Replace with:**
```javascript
async function deleteArtifact(artifactId) {
    if (!confirm('Are you sure you want to delete this artifact?')) return;

    try {
        const response = await fetch(`${API_URL}/chat/sessions/${currentSessionId}/artifacts/${artifactId}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${accessToken}`
            }
        });

        if (response.ok) {
            await loadArtifacts(); // Reload list
            alert('Artifact deleted successfully');
        } else {
            alert('Failed to delete artifact');
        }
    } catch (error) {
        console.error('Failed to delete artifact:', error);
        alert('Failed to delete artifact');
    }
}
```

### 7. Update Badge Display

**Find:**
```javascript
// Update context badge in chat title (around line 1121)
function updateContextBadge() {
    const session = sessions.find(s => s._id === currentSessionId);
    const existingBadge = document.querySelector('.context-badge');
    if (existingBadge) existingBadge.remove();

    if (session && session.context) {
        const badge = document.createElement('span');
        badge.className = 'context-badge';
        badge.textContent = session.context.type === 'repository' ? 'Repository' : 'Zip';
        chatTitle.appendChild(badge);
    }
}
```

**Replace with:**
```javascript
function updateArtifactsBadge() {
    const existingBadge = document.querySelector('.artifacts-badge');
    if (existingBadge) existingBadge.remove();

    if (artifacts && artifacts.length > 0) {
        const badge = document.createElement('span');
        badge.className = 'artifacts-badge context-badge'; // Reuse context-badge CSS
        badge.textContent = `${artifacts.length} Artifact${artifacts.length > 1 ? 's' : ''}`;
        chatTitle.appendChild(badge);
    }
}
```

### 8. Update Session Selection

**Find:**
```javascript
// Update selectSession (around line 1156)
selectSession = async function(sessionId) {
    await originalSelectSession(sessionId);
    addContextBtn.style.display = 'inline-block';
    updateContextBadge();
};
```

**Replace with:**
```javascript
selectSession = async function(sessionId) {
    await originalSelectSession(sessionId);
    addArtifactsBtn.style.display = 'inline-block';
    await loadArtifacts(); // Load artifacts for the session
    updateArtifactsBadge();
};
```

### 9. Update Modal Open Handler

**Find:**
```javascript
// Open modal (around line 949)
addContextBtn.addEventListener('click', () => {
    contextModal.classList.add('active');
    resetContextModal();
    updateContextDisplay();
});
```

**Replace with:**
```javascript
addArtifactsBtn.addEventListener('click', () => {
    artifactsModal.classList.add('active');
    resetArtifactsModal();
    renderArtifacts(); // Show current artifacts
});
```

### 10. Update Success Handlers

**After successful repository add or zip upload:**

**Find:**
```javascript
if (response.ok) {
    const session = await response.json();
    updateSessionContext(session);
    contextModal.classList.remove('active');
    alert('Repository added successfully!');
}
```

**Replace with:**
```javascript
if (response.ok) {
    await loadArtifacts(); // Reload artifacts list
    artifactsModal.classList.remove('active');
    alert('Artifact added successfully!');
}
```

## Complete Flow Example

### When User Clicks "Manage Artifacts":
1. Modal opens
2. Current artifacts list is displayed
3. User sees options to add new artifact
4. User can delete existing artifacts

### When User Adds Artifact:
1. Choose type (Repository or Zip)
2. Fill in details
3. Submit
4. Artifact is created
5. List refreshes showing new artifact
6. Badge updates with count

### When User Deletes Artifact:
1. Click delete on specific artifact
2. Confirm deletion
3. Artifact is removed
4. List refreshes
5. Badge updates with new count

## Quick Reference: API Endpoint Mapping

| Old Endpoint | New Endpoint | Method |
|--------------|--------------|--------|
| `/chat/sessions/{id}/context/repository` | `/chat/sessions/{id}/artifacts` | POST |
| `/chat/sessions/{id}/context/upload` | `/chat/sessions/{id}/artifacts/upload` | POST |
| N/A | `/chat/sessions/{id}/artifacts` | GET |
| `/chat/sessions/{id}/context` | `/chat/sessions/{id}/artifacts/{artifact_id}` | DELETE |

## Testing Checklist

After making changes:
- [ ] Button shows "Manage Artifacts"
- [ ] Clicking button opens modal with artifacts list
- [ ] Can add repository URL artifact
- [ ] Can upload zip file artifact
- [ ] Multiple artifacts show in list
- [ ] Badge shows correct count
- [ ] Can delete individual artifacts
- [ ] List updates after add/delete
- [ ] Badge updates after changes

## Rollback Plan

If issues occur:
1. Restore from backup: `cp app/static/chat_sessions_backup.html app/static/chat_sessions.html`
2. Restart server
3. Test with old context endpoints (if backend hasn't been deployed)

## Notes

- The CSS classes can stay the same (just rename IDs)
- The modal structure remains mostly the same
- Main changes are API endpoints and displaying multiple artifacts
- Badge logic changes from showing type to showing count
- Session management is cleaner without embedded context
