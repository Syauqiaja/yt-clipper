# Commit Message Template

## Title
feat: Add n8n integration with Google Drive upload and webhook notifications

## Description

### Features Added
- **Google Drive Integration**: OAuth2-based file upload with automatic public link generation
- **Webhook Notifications**: Async webhook system for success/error notifications to n8n
- **JSON Output Mode**: Machine-readable output for n8n workflow integration
- **CLI Enhancements**: New flags for upload, webhook control, and JSON output

### New Services
- `app/services/storage/`: Google Drive OAuth2 and upload service
- `app/services/webhooks/`: Webhook notification service with success/error payloads

### CLI Flags Added
- `--upload-to-drive`: Upload rendered clips to Google Drive
- `--webhook` / `--no-webhook`: Control webhook notifications (default: enabled)
- `--json`: Output results as JSON for n8n integration

### Configuration
- Added Google Drive settings (OAuth credentials, folder ID, token path)
- Added webhook settings (enabled flag, URL)
- Updated `.env.example` with new configuration options

### Dependencies
- google-auth>=2.28.0
- google-auth-oauthlib>=1.2.0
- google-auth-httplib2>=0.2.0
- google-api-python-client>=2.119.0

### Documentation
- N8N_INTEGRATION.md: Complete setup guide with troubleshooting
- N8N_WORKFLOWS.md: n8n workflow templates and examples
- IMPLEMENTATION_SUMMARY.md: Technical implementation details
- DEPLOYMENT_CHECKLIST.md: Step-by-step deployment guide
- QUICK_START.md: 5-step quick start guide

### Architecture
```
n8n Webhook (trigger) → Execute CLI Command
    ↓
CLI processes video (download → transcribe → analyze → render)
    ↓
CLI uploads to Google Drive (optional)
    ↓
CLI sends webhook to n8n with full metadata
    ↓
n8n handles notifications, history logging, auto-posting
```

### Webhook Payload
- Event type: `clip.completed` or `clip.failed`
- Full video metadata (title, duration, views, etc.)
- All clips with scores and timestamps
- Google Drive links (view, download, thumbnail)
- Processing time and error details (if failed)

### Files Changed
**New:**
- app/services/storage/__init__.py
- app/services/storage/models.py
- app/services/storage/google_drive_service.py
- app/services/webhooks/__init__.py
- app/services/webhooks/models.py
- app/services/webhooks/webhook_service.py
- N8N_INTEGRATION.md
- N8N_WORKFLOWS.md
- IMPLEMENTATION_SUMMARY.md
- DEPLOYMENT_CHECKLIST.md
- QUICK_START.md

**Modified:**
- pyproject.toml (added Google API dependencies)
- app/config/settings.py (added Google Drive and webhook settings)
- app/workflows/clip_workflow.py (added upload and webhook logic)
- app/cli/commands.py (added new CLI flags and JSON output)
- .env.example (added configuration examples)

### Testing
- ✅ All imports successful
- ✅ Syntax validation passed
- ✅ CLI help text verified
- ✅ Dependencies installed
- ⏳ Pending: OAuth setup and end-to-end testing

### Breaking Changes
None. All new features are opt-in via CLI flags.

### Migration Notes
1. Update `.env` with new Google Drive and webhook settings
2. Run `uv sync` to install new dependencies
3. Setup Google OAuth credentials (one-time)
4. Configure n8n workflows (see N8N_WORKFLOWS.md)

### Related Issues
Closes #[issue-number] (if applicable)

### References
- Google Drive API: https://developers.google.com/drive/api
- n8n Documentation: https://docs.n8n.io
- OAuth2 Flow: https://developers.google.com/identity/protocols/oauth2

---

**Commit Command:**
```bash
git add .
git commit -F COMMIT_MESSAGE.md
```

**Or short version:**
```bash
git add .
git commit -m "feat: Add n8n integration with Google Drive upload and webhook notifications"
```
