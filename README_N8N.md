# n8n Integration for YT-Clipper

**Status:** ✅ Ready for Testing  
**Version:** 1.0.0  
**Date:** 2026-05-19

---

## What This Integration Does

Enables YT-Clipper to work seamlessly with n8n for:
- **Automated Processing**: Trigger video processing from n8n workflows
- **Cloud Storage**: Upload clips to Google Drive with shareable links
- **Notifications**: Send webhook notifications with full metadata
- **Automation**: Enable n8n to handle notifications, logging, and auto-posting

---

## Quick Overview

### Before Integration
```
User → CLI → Process Video → Save Locally
```

### After Integration
```
n8n → CLI → Process → Upload to Drive → Webhook → n8n
                                                    ↓
                                    Notifications, Logging, Auto-posting
```

---

## Getting Started

### 1. Read the Documentation
- **QUICK_START.md** - Start here (5 steps, ~30 minutes)
- **N8N_INTEGRATION.md** - Complete setup guide
- **N8N_WORKFLOWS.md** - Workflow templates
- **DEPLOYMENT_CHECKLIST.md** - Deployment steps

### 2. Setup Requirements
- Google Cloud project with Drive API enabled
- OAuth2 credentials (Desktop app)
- Google Drive folder for uploads
- n8n instance at: https://n8n.fajrsyauqi.com

### 3. Quick Test
```bash
# Configure .env
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://n8n.fajrsyauqi.com/webhook/clip-notification

# Authenticate
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"

# Test
python main.py clip run "YOUTUBE_URL" --upload-to-drive --json
```

---

## New CLI Flags

### `--upload-to-drive`
Upload rendered clips to Google Drive with public links.

```bash
python main.py clip run "URL" --upload-to-drive
```

### `--webhook` / `--no-webhook`
Control webhook notifications (default: enabled).

```bash
python main.py clip run "URL" --webhook
python main.py clip run "URL" --no-webhook
```

### `--json`
Output results as JSON for n8n integration.

```bash
python main.py clip run "URL" --json
```

---

## Example Usage

### Basic Processing
```bash
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID" \
  --format shorts \
  --captions
```

### With Google Drive Upload
```bash
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID" \
  --format shorts \
  --captions \
  --upload-to-drive
```

### Full Integration (for n8n)
```bash
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID" \
  --format shorts \
  --captions \
  --upload-to-drive \
  --webhook \
  --json
```

---

## Webhook Payload Example

```json
{
  "event": "clip.completed",
  "video_url": "https://youtube.com/watch?v=VIDEO_ID",
  "video_title": "Video Title",
  "clips": [
    {
      "rank": 1,
      "title": "Clip Title",
      "final_score": 8.75,
      "start_time": 15.5,
      "end_time": 45.2
    }
  ],
  "drive_uploads": [
    {
      "clip_rank": 1,
      "clip_title": "Clip Title",
      "view_link": "https://drive.google.com/file/d/...",
      "download_link": "https://drive.google.com/uc?id=..."
    }
  ],
  "processing_time": 127.5,
  "timestamp": "2026-05-19T14:00:00.000Z"
}
```

---

## n8n Workflow Templates

### Minimal Setup (2 workflows)

**Workflow 1: Trigger Processing**
- Webhook trigger: `/webhook/clip-process`
- Execute command node
- Respond immediately

**Workflow 2: Handle Results**
- Webhook trigger: `/webhook/clip-notification`
- Send Discord/Slack notification
- Log to Google Sheets (optional)

See **N8N_WORKFLOWS.md** for complete templates.

---

## Configuration

### Environment Variables

```bash
# Google Drive
GOOGLE_OAUTH_CREDENTIALS_PATH=google_oauth_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_DRIVE_TOKEN_PATH=google_drive_token.json

# Webhooks
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://n8n.fajrsyauqi.com/webhook/clip-notification
```

### Files Needed
- `google_oauth_credentials.json` - OAuth2 credentials from Google Cloud
- `google_drive_token.json` - Generated during first-time auth (auto-created)
- `.env` - Configuration file

---

## Architecture

### Components
1. **Google Drive Service** - OAuth2 authentication and file upload
2. **Webhook Service** - Async notifications to n8n
3. **CLI Integration** - New flags and JSON output
4. **Workflow Integration** - Upload and webhook logic

### Data Flow
```
1. n8n triggers CLI via webhook
2. CLI processes video (download, transcribe, analyze, render)
3. CLI uploads clips to Google Drive
4. CLI sends webhook to n8n with results
5. n8n handles notifications and automation
```

---

## Troubleshooting

### OAuth Issues
```bash
# Delete token and re-authenticate
rm google_drive_token.json
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
```

### Webhook Not Sending
- Check `WEBHOOK_ENABLED=true` in `.env`
- Verify `WEBHOOK_URL` is correct
- Test manually: `curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-notification -d '{"event":"test"}'`

### Upload Fails
- Verify folder ID is correct
- Check folder permissions
- Ensure OAuth token is valid

---

## Security Notes

1. **Never commit credentials:**
   - `google_oauth_credentials.json`
   - `google_drive_token.json`
   - `.env`

2. **Use HTTPS for webhooks**

3. **Limit OAuth scope to `drive.file` only**

4. **Keep webhook URLs private**

---

## Support

### Documentation
- **QUICK_START.md** - Quick setup guide
- **N8N_INTEGRATION.md** - Complete integration guide
- **N8N_WORKFLOWS.md** - Workflow templates
- **DEPLOYMENT_CHECKLIST.md** - Deployment steps
- **IMPLEMENTATION_SUMMARY.md** - Technical details

### Logs
```bash
# Check application logs
tail -f logs/yt-clipper.log

# Check n8n execution logs
# View in n8n UI → Executions
```

---

## What's Next?

1. ✅ Implementation complete
2. ⏳ Setup Google OAuth
3. ⏳ Test locally
4. ⏳ Deploy to VPS
5. ⏳ Create n8n workflows
6. ⏳ Test end-to-end
7. ⏳ Setup notifications
8. ⏳ Configure auto-posting (optional)

---

**Ready to start? Open QUICK_START.md**
