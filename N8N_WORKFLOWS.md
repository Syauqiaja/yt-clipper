# n8n Workflow Quick Reference

## Workflow 1: Trigger Processing

**Name:** `YT-Clipper - Process Video`

### Node 1: Webhook Trigger
```
Type: Webhook
Method: POST
Path: clip-process
Authentication: Header Auth (optional)
  - Header Name: X-API-Key
  - Header Value: {{$env.API_KEY}}
Response Mode: Immediately
```

### Node 2: Validate Input (Code)
```javascript
const body = $input.item.json.body;

if (!body.url) {
  throw new Error('Missing required field: url');
}

return {
  url: body.url,
  format: body.format || 'shorts',
  template: body.template || 'shorts_fit',
  captions: body.captions !== false,
  caption_style: body.caption_style || 'tiktok',
  karaoke: body.karaoke || false,
  max_clips: body.max_clips || 5,
};
```

### Node 3: Respond Immediately
```
Type: Respond to Webhook
Status Code: 202
Body:
{
  "status": "processing",
  "url": "{{$json.url}}",
  "message": "Video processing started"
}
```

### Node 4: Execute Command
```
Type: Execute Command
Command:
cd /opt/yt-clipper && \
source .venv/bin/activate && \
python main.py clip run "{{$json.url}}" \
  --format {{$json.format}} \
  --template {{$json.template}} \
  {{$json.captions ? '--captions' : ''}} \
  --caption-style {{$json.caption_style}} \
  {{$json.karaoke ? '--karaoke' : ''}} \
  --max-clips {{$json.max_clips}} \
  --upload-to-drive \
  --webhook \
  --json

Timeout: 1800000 (30 minutes)
```

### Node 5: Error Handler (Error Trigger)
```javascript
// Connect to all nodes
return {
  success: false,
  error: $json.error.message,
  url: $json.url,
  timestamp: new Date().toISOString()
};
```

---

## Workflow 2: Results Handler

**Name:** `YT-Clipper - Results Handler`

### Node 1: Webhook Trigger
```
Type: Webhook
Method: POST
Path: clip-notification
Authentication: None
Response Mode: Immediately
```

### Node 2: Switch by Event
```
Type: Switch
Mode: Expression
Value: {{$json.body.event}}

Routes:
  - clip.completed → Success Flow
  - clip.failed → Error Flow
```

---

## Success Flow

### Node 3: Extract Data (Code)
```javascript
const data = $input.item.json.body;

return {
  video_title: data.video_title,
  video_url: data.video_url,
  clips_count: data.clips.length,
  processing_time: data.processing_time,
  clips: data.clips,
  drive_links: data.drive_uploads,
  timestamp: data.timestamp,
  video_metadata: data.video_metadata,
};
```

### Node 4: Format Notification (Code)
```javascript
const data = $input.item.json;

const clipsList = data.drive_links
  .map((link, i) => `${i + 1}. [${link.clip_title}](${link.view_link}) (Score: ${data.clips[i].final_score})`)
  .join('\n');

return {
  title: `✅ Clips Ready: ${data.video_title}`,
  description: `Generated ${data.clips_count} clips in ${data.processing_time.toFixed(1)}s`,
  message: `📹 **Video:** ${data.video_title}\n` +
           `🔗 **URL:** ${data.video_url}\n` +
           `🎬 **Clips:** ${data.clips_count}\n` +
           `⏱️ **Time:** ${data.processing_time.toFixed(1)}s\n\n` +
           `**Clips:**\n${clipsList}`,
  color: 3066993, // Green
};
```

### Node 5: Send Discord Notification
```
Type: Discord
Webhook URL: {{$env.DISCORD_WEBHOOK_URL}}
Content: {{$json.message}}
```

### Node 6: Send Slack Notification (Alternative)
```
Type: Slack
Webhook URL: {{$env.SLACK_WEBHOOK_URL}}
Text: {{$json.message}}
```

### Node 7: Log to Google Sheets (Optional)
```
Type: Google Sheets
Operation: Append
Spreadsheet: YT-Clipper History
Sheet: Processing Log

Columns:
  - Timestamp: {{$json.timestamp}}
  - Video Title: {{$json.video_title}}
  - Video URL: {{$json.video_url}}
  - Clips Count: {{$json.clips_count}}
  - Processing Time: {{$json.processing_time}}
  - Status: Success
```

### Node 8: Loop Over Clips (Split in Batches)
```
Type: Split in Batches
Batch Size: 1
Input: {{$json.clips}}
```

### Node 9: Store Clip Details (Google Sheets)
```
Type: Google Sheets
Operation: Append
Spreadsheet: YT-Clipper History
Sheet: Clips

Columns:
  - Timestamp: {{$json.timestamp}}
  - Video Title: {{$json.video_title}}
  - Clip Rank: {{$json.rank}}
  - Clip Title: {{$json.title}}
  - Score: {{$json.final_score}}
  - Start Time: {{$json.start_time}}
  - End Time: {{$json.end_time}}
  - Duration: {{$json.duration}}
  - Drive Link: {{$json.drive_links[0].view_link}}
```

### Node 10: Auto-Post Filter (Optional)
```
Type: Filter
Condition: {{$json.final_score}} > 8.0
```

### Node 11: Download from Drive (Optional)
```
Type: Google Drive
Operation: Download
File ID: {{$json.drive_links[0].file_id}}
```

### Node 12: Post to TikTok (Optional)
```
Type: HTTP Request
Method: POST
URL: https://open-api.tiktok.com/share/video/upload/
Headers:
  - Authorization: Bearer {{$env.TIKTOK_ACCESS_TOKEN}}
Body:
  - video: {{$binary.data}}
  - caption: {{$json.title}}
```

---

## Error Flow

### Node 13: Format Error (Code)
```javascript
const data = $input.item.json.body;

return {
  title: `❌ Processing Failed`,
  message: `📹 **Video:** ${data.video_url}\n` +
           `⚠️ **Error:** ${data.error}\n` +
           `🕐 **Time:** ${data.timestamp}`,
  color: 15158332, // Red
};
```

### Node 14: Send Error Notification
```
Type: Discord
Webhook URL: {{$env.DISCORD_WEBHOOK_URL}}
Content: {{$json.message}}
```

### Node 15: Log Error (Google Sheets)
```
Type: Google Sheets
Operation: Append
Spreadsheet: YT-Clipper History
Sheet: Errors

Columns:
  - Timestamp: {{$json.timestamp}}
  - Video URL: {{$json.video_url}}
  - Error: {{$json.error}}
```

---

## Workflow 3: Cleanup

**Name:** `YT-Clipper - Cleanup`

### Node 1: Schedule Trigger
```
Type: Schedule Trigger
Cron: 0 2 * * * (Daily at 2 AM)
```

### Node 2: Execute Cleanup
```
Type: Execute Command
Command:
cd /opt/yt-clipper/temp && \
find . -type f ! -name '.gitkeep' -mtime +1 -delete && \
echo "Cleanup completed"
```

### Node 3: Send Summary (Optional)
```
Type: Discord
Webhook URL: {{$env.DISCORD_WEBHOOK_URL}}
Content: 🧹 Temp files cleaned up successfully
```

---

## Testing Commands

### Trigger Processing
```bash
curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-process \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
    "format": "shorts",
    "captions": true,
    "max_clips": 2
  }'
```

### Test Webhook Manually
```bash
curl -X POST https://n8n.fajrsyauqi.com/webhook/clip-notification \
  -H "Content-Type: application/json" \
  -d '{
    "event": "clip.completed",
    "video_url": "https://youtube.com/watch?v=test",
    "video_title": "Test Video",
    "video_metadata": {},
    "clips": [{"rank": 1, "title": "Test Clip", "final_score": 8.5}],
    "drive_uploads": [{"clip_title": "Test", "view_link": "https://drive.google.com/test"}],
    "processing_time": 120.5,
    "timestamp": "2026-05-19T14:00:00.000Z"
  }'
```

---

## Environment Variables for n8n

Add these to your n8n environment:

```bash
# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK

# Slack (alternative)
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR_WEBHOOK

# TikTok (optional)
TIKTOK_ACCESS_TOKEN=your_access_token

# API Key (optional)
API_KEY=your_secure_api_key
```

---

## Google Sheets Setup

### Sheet 1: Processing Log
Columns:
- Timestamp
- Video Title
- Video URL
- Clips Count
- Processing Time
- Status

### Sheet 2: Clips
Columns:
- Timestamp
- Video Title
- Clip Rank
- Clip Title
- Score
- Start Time
- End Time
- Duration
- Drive Link

### Sheet 3: Errors
Columns:
- Timestamp
- Video URL
- Error

---

## Tips

1. **Test Each Node:** Use n8n's "Execute Node" feature to test individually
2. **Check Logs:** View execution logs in n8n for debugging
3. **Start Simple:** Begin with just notification, add features incrementally
4. **Use Filters:** Only auto-post high-scoring clips (score > 8.0)
5. **Monitor Quotas:** Check Google Drive API quotas if uploads fail
6. **Backup Webhooks:** Have both Discord and Slack for redundancy

---

## Common Issues

**Webhook not received:**
- Check n8n workflow is activated
- Verify webhook URL in `.env`
- Test webhook URL manually with curl

**Command timeout:**
- Increase timeout to 30 minutes (1800000ms)
- Check VPS resources (CPU, memory)
- Monitor processing with `htop`

**Upload fails:**
- Verify Google Drive folder ID
- Check OAuth token is valid
- Ensure folder permissions are correct

**Auto-post fails:**
- Verify API credentials
- Check file format compatibility
- Test API endpoints manually

---

**Quick Start:** Import these workflows into n8n, configure webhooks, and test!
