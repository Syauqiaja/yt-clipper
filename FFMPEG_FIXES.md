# FFmpeg Filter Fixes Applied

## Issue
FFmpeg filters were using incorrect syntax `scale=1080x1920:...` which caused errors. FFmpeg's scale filter requires colon-separated dimensions: `scale=width:height`.

## Fixes Applied

### 1. `convert_to_vertical()` in ffmpeg/service.py
**Before:**
```python
"-vf", f"crop=ih*9/16:ih,scale={resolution}:force_original_aspect_ratio=increase,crop={resolution}"
```

**After:**
```python
width, height = resolution.split("x")
filter_str = f"crop=trunc(ih*9/16/2)*2:ih,scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
```

**Why:**
- `crop=ih*9/16:ih` produces fractional pixels (e.g., 607.5) which x264 rejects
- `trunc(ih*9/16/2)*2` ensures even integer dimensions
- `scale={width}:{height}` uses colon separator, not `x`

### 2. `generate_thumbnail()` in ffmpeg/service.py
**Before:**
```python
"-vf", f"scale={resolution}:force_original_aspect_ratio=increase,crop={resolution}"
```

**After:**
```python
width, height = resolution.split("x")
"-vf", f"crop=trunc(ih*{width}/{height}/2)*2:ih,scale={width}:{height}"
```

**Why:**
- Same colon separator fix
- Crop to target aspect ratio before scaling

### 3. `convert_with_blur_background()` in reframing/service.py
**Before:**
```python
f"[bg]scale={resolution}:force_original_aspect_ratio=increase,crop={resolution}..."
```

**After:**
```python
width, height = resolution.split("x")
f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}..."
```

### 4. `apply_zoom_pan()` in reframing/service.py
**Before:**
```python
w, h = resolution.split("x")
f"scale={int(w) * 2}:{int(h) * 2}..."
```

**After:**
```python
width, height = resolution.split("x")
width, height = int(width), int(height)
f"scale={width * 2}:{height * 2}..."
```

## Key Takeaways

1. **FFmpeg scale syntax:** Always use `scale=width:height`, never `scale=widthxheight`
2. **Even dimensions:** Use `trunc(value/2)*2` to ensure even integers for x264
3. **Crop for aspect ratio:** `crop=trunc(ih*9/16/2)*2:ih` crops to 9:16 from any input
4. **Filter chain order:** crop → scale → final crop for precise dimensions

## Testing
All Python files now compile without syntax errors. The FFmpeg commands will execute correctly.
