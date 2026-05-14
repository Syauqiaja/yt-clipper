# Phase 2 Rendering Test Script

## Usage

Run the test script to identify the correct FFmpeg subtitle syntax:

```bash
cd /Users/mac/Documents/Works/python/yt-clipper
python3 test_phase2_rendering.py
```

## What It Does

The test script will:

1. **Create dummy test files** (no need for real video download)
   - Dummy video: 1920x1080, 10 seconds
   - Dummy captions: ASS file with test text

2. **Test composition planning**
   - Verify layout calculations
   - Check fit-width positioning

3. **Test FFmpeg graph builder**
   - Generate filter complex
   - Verify filter chain syntax

4. **Test rendering without captions**
   - Verify basic composition works
   - Test blur background + overlay

5. **Test multiple subtitle syntaxes**
   - Try 6 different FFmpeg subtitle filter syntaxes
   - Identify which one works
   - Report the working syntax

6. **Test rendering with captions**
   - Use the working syntax
   - Generate final output

## Expected Output

The script will test these subtitle syntaxes:
1. `subtitles=temp/captions_1.ass`
2. `subtitles='temp/captions_1.ass'`
3. `subtitles=filename=temp/captions_1.ass`
4. `subtitles=filename='temp/captions_1.ass'`
5. `ass=temp/captions_1.ass`
6. `ass='temp/captions_1.ass'`

It will report which syntax works and automatically update the code.

## Output Files

All test files will be in `temp/test_rendering/`:
- `dummy_input.mp4` - Test video
- `dummy_captions.ass` - Test captions
- `output_no_subs.mp4` - Rendered without captions
- `output_with_subs.mp4` - Rendered with captions
- `output_syntax1.mp4` through `output_syntax6.mp4` - Test outputs

## Quick Test

If you want to quickly test just the FFmpeg command manually:

```bash
# Create test video
ffmpeg -f lavfi -i testsrc=duration=10:size=1920x1080:rate=25 \
       -f lavfi -i sine=frequency=1000:duration=10 \
       -c:v libx264 -preset ultrafast -c:a aac -y temp/test.mp4

# Test composition only (should work)
ffmpeg -i temp/test.mp4 \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15[bg];[0:v]scale=1080:607:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=0:656[out]" \
  -map "[out]" -map "0:a?" \
  -c:v libx264 -crf 23 -preset fast -c:a aac -b:a 128k \
  -y temp/test_no_subs.mp4

# Test with subtitles (try different syntaxes)
ffmpeg -i temp/test.mp4 \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15[bg];[0:v]scale=1080:607:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=0:656[out];[out]subtitles=temp/captions_1.ass[final]" \
  -map "[final]" -map "0:a?" \
  -c:v libx264 -crf 23 -preset fast -c:a aac -b:a 128k \
  -y temp/test_with_subs.mp4
```

## Alternative: Test Without Captions First

To verify Phase 2 rendering works without captions:

```bash
python3 main.py clip run "https://youtu.be/XDT2N2_8kTU" \
    --format tiktok \
    --template shorts_fit \
    --max-clips 1
    # Note: No --captions flag
```

This should work and produce a rendered clip with fit-width layout and blur background.

## Status

Run the test script to identify the correct subtitle syntax, then we can update the renderer service with the working syntax.
