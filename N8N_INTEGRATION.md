# YT-Clipper + n8n + Google Drive Integration

## Overview

This integration enables YT-Clipper to:
1. Upload generated clips to Google Drive
2. Send webhook notifications to n8n with full metadata
3. Enable n8n to orchestrate processing, notifications, and auto-posting

## Architecture

```
n8n Webhook (trigger) → Execute CLI Command
    ↓
CLI processes video (download → transcribe → analyze → render)
    ↓
CLI uploads to Google Drive (optional)
    ↓
CLI sends webhook to n8n with results
    ↓
n8n handles notifications, history logging, auto-posting
```

## Setup Instructions

### 1. Google Drive OAuth2 Setup

#### Step 1: Enable Google Drive API
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select your project
3. Navigate to **APIs & Services → Library**
4. Search for "Google Drive API" and click **Enable**

#### Step 2: Create OAuth2 Credentials
1. Go to **APIs & Services → Credentials**
2. Click **Create Credentials → OAuth 2.0 Client ID**
3. Application type: **Desktop app**
4. Name: `YT-Clipper`
5. Click **Create**
6. Download the JSON file and save as `google_oauth_credentials.json` in the project root

#### Step 3: Create Google Drive Folder
1. Go to [Google Drive](https://drive.google.com)
2. Create a new folder: `YT-Clipper-Exports`
3. Open the folder and copy the folder ID from the URL:
   ```
   https://drive.google.com/drive/folders/FOLDER_ID_HERE
   ```

### 2. Environment Configuration

Update your `.env` file:

```bash
# Google Drive
GOOGLE_OAUTH_CREDENTIALS_PATH=google_oauth_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
GOOGLE_DRIVE_TOKEN_PATH=google_drive_token.json

# Webhooks
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://n8n.fajrsyauqi.com/webhook/clip-notification
```

### 3. First-Time OAuth Authentication

Run this command to authenticate with Google (one-time setup):

```bash
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
```

This will:
1. Open your browser for Google OAuth consent
2. Save the token to `google_drive_token.json`
3. Token will be automatically refreshed when needed

### 4. Test the Integration

#### Test without upload:
```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 2 \
  --json
```

#### Test with Google Drive upload:
```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 2 \
  --upload-to-drive \
  --json
```

#### Test with webhook (requires n8n running):
```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 2 \
  --upload-to-drive \
  --webhook \
  --json
```

## CLI Usage

### New Flags

- `--upload-to-drive`: Upload clips to Google Drive
- `--webhook` / `--no-webhook`: Enable/disable webhook notifications (default: enabled)
- `--json`: Output results as JSON (for n8n integration)

### Examples

**Basic usage with all features:**
```bash
python main.py clip run "YOUTUBE_URL" \
  --format shorts \
  --captions \
  --upload-to-drive \
  --webhook
```

**JSON output for n8n:**
```bash
python main.py clip run "YOUTUBE_URL" \
  --upload-to-drive \
  --json
```

**Disable webhook:**
```bash
python main.py clip run "YOUTUBE_URL" \
  --no-webhook
```

## Webhook Payload

### Success Webhook

```json
{
  "event": "clip.completed",
  "video_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
  "video_title": "Rick Astley - Never Gonna Give You Up",
  "video_metadata": {
    "video_id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up",
    "duration": 212.0,
    "uploader": "Rick Astley",
    "view_count": 1400000000
  },
  "clips": [
    {
      "rank": 1,
      "title": "Epic Hook Moment",
      "start_time": 15.5,
      "end_time": 45.2,
      "duration": 29.7,
      "final_score": 8.75,
      "scores": {
        "hook_strength": 9.5,
        "retention_potential": 8.8,
        "information_density": 7.5,
        "storytelling": 8.0,
        "emotional_engagement": 9.2,
        "viral_potential": 8.2
      }
    }
  ],
  "drive_uploads": [
    {
      "clip_rank": 1,
      "clip_title": "Epic Hook Moment",
      "file_id": "1abc123xyz",
      "file_name": "raw_1.mp4",
      "view_link": "https://drive.google.com/file/d/1abc123xyz/view",
      "download_link": "https://drive.google.com/uc?id=1abc123xyz",
      "thumbnail_link": "https://lh3.googleusercontent.com/..."
    }
  ],
  "processing_time": 127.5,
  "timestamp": "2026-05-19T14:00:21.335Z"
}
```

### Error Webhook

```json
{
  "event": "clip.failed",
  "video_url": "https://youtube.com/watch?v=invalid",
  "video_title": "",
  "video_metadata": {},
  "clips": [],
  "drive_uploads": null,
  "processing_time": 0.0,
  "timestamp": "2026-05-19T14:00:21.335Z",
  "error": "ERROR: Video unavailable"
}
```

## n8n Workflow Setup

### Workflow 1: Process Video (Trigger)

**Webhook Trigger:**
- Method: POST
- Path: `clip-process`
- Body: `{ "url": "youtube_url", "format": "shorts", "captions": true }`

**Execute Command Node:**
```bash
cd /opt/yt-clipper && \
source .venv/bin/activate && \
python main.py clip run "{{$json.body.url}}" \
  --format {{$json.body.format || 'shorts'}} \
  --captions \
  --max-clips {{$json.body.max_clips || 5}} \
  --upload-to-drive \
  --webhook \
  --json
```

### Workflow 2: Results Handler (Receive Webhook)

**Webhook Trigger:**
- Method: POST
- Path: `clip-notification`

**Switch Node:** Route by `event` field
- `clip.completed` → Success flow
- `clip.failed` → Error flow

**Success Flow:**
- Log to Google Sheets
- Send Discord/Slack notification
- Auto-post to social media (optional)

**Error Flow:**
- Log error
- Send error notification

## VPS Deployment

### 1. Install Dependencies

```bash
cd /opt/yt-clipper
source .venv/bin/activate
uv sync
```

### 2. Setup Google OAuth

```bash
# Copy credentials to server
scp google_oauth_credentials.json user@your-vps:/opt/yt-clipper/

# Run OAuth flow (one-time)
cd /opt/yt-clipper
source .venv/bin/activate
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
```

### 3. Configure Environment

```bash
# Edit .env
nano .env

# Add:
GOOGLE_OAUTH_CREDENTIALS_PATH=google_oauth_credentials.json
GOOGLE_DRIVE_FOLDER_ID=your_folder_id
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://n8n.fajrsyauqi.com/webhook/clip-notification
```

### 4. Test End-to-End

```bash
# Trigger from n8n
curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-process \
  -H "Content-Type: application/json" \
  -d '{"url": "https://youtube.com/watch?v=dQw4w9WgXcQ", "max_clips": 2}'
```

## Troubleshooting

### Google Drive Authentication Issues

**Problem:** Token expired or invalid

**Solution:**
```bash
# Delete old token and re-authenticate
rm google_drive_token.json
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
```

### Webhook Not Sending

**Problem:** Webhook fails silently

**Solution:**
1. Check `.env` has `WEBHOOK_ENABLED=true`
2. Verify `WEBHOOK_URL` is correct
3. Check logs: `tail -f logs/yt-clipper.log`
4. Test webhook URL manually:
   ```bash
   curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-notification \
     -H "Content-Type: application/json" \
     -d '{"event": "test"}'
   ```

### Upload Fails

**Problem:** Google Drive upload fails

**Solution:**
1. Verify folder ID is correct
2. Check folder permissions (should be owned by authenticated account)
3. Re-authenticate if needed
4. Check quota limits in Google Drive

## Security Notes

1. **OAuth Token:** `google_drive_token.json` contains sensitive credentials. Add to `.gitignore`
2. **Credentials File:** `google_oauth_credentials.json` should not be committed to git
3. **Webhook URL:** Keep webhook URLs private to prevent unauthorized access
4. **n8n Authentication:** Use API keys or basic auth for n8n webhooks in production

## Files Added/Modified

### New Files:
- `app/services/storage/__init__.py`
- `app/services/storage/models.py`
- `app/services/storage/google_drive_service.py`
- `app/services/webhooks/__init__.py`
- `app/services/webhooks/models.py`
- `app/services/webhooks/webhook_service.py`
- `N8N_INTEGRATION.md` (this file)

### Modified Files:
- `pyproject.toml` - Added Google API dependencies
- `app/config/settings.py` - Added Google Drive and webhook settings
- `app/workflows/clip_workflow.py` - Added upload and webhook logic
- `app/cli/commands.py` - Added new CLI flags
- `.env.example` - Added new environment variables

## Next Steps

1. ✅ Setup Google OAuth credentials
2. ✅ Configure `.env` file
3. ✅ Run first-time authentication
4. ✅ Test local processing with upload
5. ⏳ Deploy to VPS
6. ⏳ Create n8n workflows
7. ⏳ Test end-to-end integration
8. ⏳ Setup notifications (Discord/Slack)
9. ⏳ Configure auto-posting (optional)

## Support

For issues or questions:
- Check logs in `logs/` directory
- Review n8n execution logs
- Verify Google Drive API quotas
- Test webhook endpoints manually
