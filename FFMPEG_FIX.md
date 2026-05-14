# FFmpeg Rendering Fix

## Issue
FFmpeg command was failing with error code 234, likely due to:
1. Filter complex syntax issues
2. Subtitle path escaping problems
3. Missing error details in logs

## Fixes Applied

### 1. Enhanced Error Logging
**File:** `app/services/renderer/service.py`

Added detailed logging:
```python
logger.debug(f"FFmpeg filter_complex: {filter_complex}")
logger.debug(f"FFmpeg command: {' '.join(cmd)}")

if result.returncode != 0:
    logger.error(f"FFmpeg stderr: {result.stderr}")
    logger.error(f"FFmpeg stdout: {result.stdout}")
    logger.error(f"Filter complex was: {filter_complex}")
```

### 2. Subtitle Path Escaping
Fixed ASS subtitle path escaping:
```python
if subtitle_path:
    sub_path_escaped = str(subtitle_path).replace("\\", "/").replace(":", "\\:")
    filter_complex += f";[out]ass='{sub_path_escaped}'[final]"
```

### 3. Empty Filter Check
Added validation:
```python
if not filter_complex:
    raise FFmpegError("Failed to build filter graph - empty result")
```

## Testing

### Test Without Captions First
```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --format tiktok \
    --template shorts_fit \
    --max-clips 1
```

This will test the basic rendering without captions.

### Then Test With Captions
```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --format tiktok \
    --template shorts_fit \
    --captions \
    --caption-style tiktok \
    --max-clips 1
```

## Alternative: Use Legacy Rendering

If Phase 2 rendering continues to have issues, you can use the legacy Phase 1 rendering:

```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --template shorts_blur \
    --max-clips 1
```

Or disable Phase 2 rendering temporarily by commenting out the Phase 2 code in `app/workflows/clip_workflow.py` lines 189-220.

## Debug Steps

1. **Check FFmpeg version:**
   ```bash
   ffmpeg -version
   ```

2. **Test FFmpeg filter manually:**
   ```bash
   ffmpeg -i input.mp4 -filter_complex "[0:v]scale=1080:1920[out]" -map "[out]" test.mp4
   ```

3. **Check logs:**
   Look for "FFmpeg filter_complex:" in the output to see the exact filter being generated.

## Status

The fixes have been applied. The enhanced logging will help identify the exact issue if it persists.
