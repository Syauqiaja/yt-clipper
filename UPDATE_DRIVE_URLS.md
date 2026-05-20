# Update Summary - Drive URLs in Webhook

**Date:** 2026-05-19T15:57:36Z  
**Status:** ✅ Complete

---

## Changes Made

### 1. Updated `app/schemas/models.py`
Added `drive_uploads` field to `ProcessingResult`:
```python
drive_uploads: list[dict] | None = Field(default=None, description="Google Drive upload results")
```

### 2. Updated `app/workflows/clip_workflow.py`
- Store `drive_uploads` in `ProcessingResult`
- Merge drive URLs into each clip object before sending webhook
- Each clip now includes: `drive_file_id`, `drive_file_name`, `drive_view_link`, `drive_download_link`, `drive_thumbnail_link`

### 3. Updated `app/cli/commands.py`
- Include drive URLs in each clip's JSON output
- Match drive uploads to clips by rank
- Add `drive_uploads` to top-level output

---

## Webhook Payload Structure

```json
{
  "event": "clip.completed",
  "video_url": "https://youtube.com/watch?v=...",
  "video_title": "Video Title",
  "video_metadata": { ... },
  "clips": [
    {
      "rank": 1,
      "title": "Clip Title",
      "title_id": "Judul Indonesia",
      "title_en": "English Title",
      "description_id": "Deskripsi Indonesia",
      "description_en": "English Description",
      "start_time": 10.0,
      "end_time": 40.0,
      "duration": 30.0,
      "final_score": 8.5,
      "scores": {
        "hook_strength": 9.5,
        "retention_potential": 8.8,
        "information_density": 7.5,
        "storytelling": 8.0,
        "emotional_engagement": 9.2,
        "viral_potential": 8.2
      },
      "hook": "Hook description",
      "summary": "Clip summary",
      "drive_file_id": "1abc123xyz",
      "drive_file_name": "raw_1.mp4",
      "drive_view_link": "https://drive.google.com/file/d/1abc123xyz/view",
      "drive_download_link": "https://drive.google.com/uc?id=1abc123xyz",
      "drive_thumbnail_link": "https://lh3.googleusercontent.com/..."
    }
  ],
  "drive_uploads": [
    {
      "clip_rank": 1,
      "clip_title": "Clip Title",
      "file_id": "1abc123xyz",
      "file_name": "raw_1.mp4",
      "view_link": "https://drive.google.com/file/d/1abc123xyz/view",
      "download_link": "https://drive.google.com/uc?id=1abc123xyz",
      "thumbnail_link": "https://lh3.googleusercontent.com/..."
    }
  ],
  "processing_time": 127.5,
  "timestamp": "2026-05-19T15:57:36.270Z"
}
```

---

## Fields Available Per Clip

### Clip Information
- `rank` - Clip ranking (1, 2, 3, etc.)
- `title` - Original clip title
- `start_time` - Start time in seconds
- `end_time` - End time in seconds
- `duration` - Duration in seconds
- `final_score` - Overall score (0-10)
- `scores` - Detailed scores object
- `hook` - Hook description
- `summary` - Clip summary

### Multilingual Metadata
- `title_id` - Indonesian title
- `title_en` - English title
- `description_id` - Indonesian description
- `description_en` - English description

### Google Drive URLs
- `drive_file_id` - Google Drive file ID
- `drive_file_name` - File name (e.g., raw_1.mp4)
- `drive_view_link` - Shareable view link
- `drive_download_link` - Direct download link
- `drive_thumbnail_link` - Thumbnail URL (if available)

---

## Usage in n8n

### Access Drive URLs in n8n Workflow

```javascript
// In n8n Code node or expressions
const clips = $json.body.clips;

// Loop through clips
for (const clip of clips) {
  console.log(`Clip ${clip.rank}: ${clip.title}`);
  console.log(`View: ${clip.drive_view_link}`);
  console.log(`Download: ${clip.drive_download_link}`);
  console.log(`Indonesian: ${clip.title_id}`);
  console.log(`English: ${clip.title_en}`);
}

// Access specific clip
const firstClip = clips[0];
const viewUrl = firstClip.drive_view_link;
const downloadUrl = firstClip.drive_download_link;
```

### Example: Post to Social Media

```javascript
// Filter high-scoring clips
const topClips = $json.body.clips.filter(c => c.final_score > 8.0);

// Post each to TikTok/Instagram
for (const clip of topClips) {
  // Download from Google Drive
  const videoUrl = clip.drive_download_link;
  
  // Use multilingual titles
  const caption = clip.title_en || clip.title;
  const description = clip.description_en || clip.description_id;
  
  // Post to social media...
}
```

---

## Testing

### Test Command
```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
  --max-clips 1 \
  --upload-to-drive \
  --webhook \
  --json
```

### Expected Output
- CLI JSON includes drive URLs per clip
- Webhook sent to n8n includes drive URLs per clip
- Both include title_id, title_en, description_id, description_en

---

## Files Modified

1. `app/schemas/models.py` - Added drive_uploads field
2. `app/workflows/clip_workflow.py` - Merge drive URLs into clips
3. `app/cli/commands.py` - Include drive URLs in JSON output

---

## Benefits

✅ **Single Source of Truth**: Each clip object contains all its information  
✅ **Easy n8n Integration**: No need to match clips with separate drive_uploads array  
✅ **Multilingual Support**: Indonesian and English titles/descriptions  
✅ **Direct Access**: View, download, and thumbnail links readily available  
✅ **Automation Ready**: Perfect for auto-posting workflows  

---

**Status:** Ready for production use! 🚀
