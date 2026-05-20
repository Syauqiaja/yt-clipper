# Quick Start Guide

## 🚀 Get Started in 5 Steps

### Step 1: Setup Google OAuth (10 minutes)

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Enable **Google Drive API**
3. Create **OAuth 2.0 Client ID** (Desktop app)
4. Download credentials → save as `google_oauth_credentials.json`
5. Create folder in Google Drive → copy folder ID from URL

### Step 2: Configure Environment (2 minutes)

Edit `.env`:
```bash
GOOGLE_DRIVE_FOLDER_ID=your_folder_id_here
WEBHOOK_ENABLED=true
WEBHOOK_URL=https://n8n.fajrsyauqi.com/webhook/clip-notification
```

### Step 3: Authenticate (1 minute)

```bash
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
```

This opens browser for OAuth consent and saves token.

### Step 4: Test Locally (5 minutes)

```bash
# Test basic processing
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 2 \
  --json

# Test with upload
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 2 \
  --upload-to-drive \
  --json
```

### Step 5: Setup n8n Workflows (15 minutes)

See `N8N_WORKFLOWS.md` for complete workflow templates.

**Minimal setup:**
1. Create webhook trigger: `/webhook/clip-process`
2. Add execute command node
3. Create webhook receiver: `/webhook/clip-notification`
4. Add Discord/Slack notification

---

## 📝 Example Commands

### Process video with all features:
```bash
python main.py clip run "YOUTUBE_URL" \
  --format shorts \
  --captions \
  --upload-to-drive \
  --webhook \
  --json
```

### Trigger from n8n:
```bash
curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-process \
  -H "Content-Type: application/json" \
  -d '{"url": "YOUTUBE_URL", "max_clips": 3}'
```

---

## 📚 Documentation

- **N8N_INTEGRATION.md** - Complete setup guide
- **N8N_WORKFLOWS.md** - Workflow templates
- **DEPLOYMENT_CHECKLIST.md** - Deployment steps
- **IMPLEMENTATION_SUMMARY.md** - Technical details

---

## 🆘 Troubleshooting

**OAuth fails:**
```bash
rm google_drive_token.json
python -c "from app.services.storage import GoogleDriveService; GoogleDriveService()"
```

**Webhook not sending:**
- Check `.env` has `WEBHOOK_ENABLED=true`
- Verify `WEBHOOK_URL` is correct
- Test manually: `curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-notification -d '{"event":"test"}'`

**Upload fails:**
- Verify folder ID is correct
- Check folder permissions
- Re-authenticate if needed

---

**Ready to start? Begin with Step 1!**
