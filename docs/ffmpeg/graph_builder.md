# FFmpeg Graph Builder

## Overview

The FFmpeg Graph Builder abstracts complex FFmpeg filter chains into modular, testable, and maintainable Python code. It eliminates hardcoded filter strings and enables composition-based rendering.

## Problem Statement

### Before (Phase 1)

```python
filter_str = (
    f"[0:v]split[fg][bg];"
    f"[bg]scale={width}:{height}:force_original_aspect_ratio=increase,"
    f"crop={width}:{height},boxblur={blur_strength}[bgblurred];"
    f"[fg]scale=-1:{height}[fgscaled];"
    f"[bgblurred][fgscaled]overlay=(W-w)/2:(H-h)/2"
)
```

**Issues**:
- Hardcoded, monolithic strings
- Difficult to test
- Error-prone
- Not reusable
- Hard to debug

### After (Phase 2)

```python
builder = FFmpegGraphBuilder()
bg_label = builder.add_background_blur(plan, "0:v")
fg_label = builder.add_scaled_video(plan, "0:v")
final_label = builder.add_overlay(bg_label, fg_label, x, y)
filter_complex = builder.build()
```

**Benefits**:
- Modular, composable
- Unit testable
- Reusable methods
- Clear intent
- Easy to debug

## Architecture

```
CompositionPlan
      ↓
FFmpegGraphBuilder
      ↓
  Filter Chain
      ↓
FFmpeg Execution
```

## Core Concepts

### Filter Labels

FFmpeg filters use labels to connect streams:

```
[input] → filter → [output]
```

**Example**:
```
[0:v]scale=1920:1080[scaled]
[scaled]blur=5[blurred]
```

The graph builder manages labels automatically.

### Filter Chains

Filters are chained using semicolons:

```
filter1;filter2;filter3
```

**Example**:
```
[0:v]scale=1080:1920[a];[a]blur=10[b];[b]overlay=0:0[out]
```

## FFmpegGraphBuilder API

### Initialization

```python
from app.services.renderer import FFmpegGraphBuilder

builder = FFmpegGraphBuilder()
```

### add_input()

Add input file (returns input label).

```python
input_label = builder.add_input("video.mp4")
# Returns: "0:v"
```

### add_background_blur()

Add blurred background layer.

```python
bg_label = builder.add_background_blur(
    plan=composition_plan,
    input_label="0:v",
)
```

**Generated filter**:
```
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,
     crop=1080:1920,
     boxblur=15[bgblur0]
```

### add_scaled_video()

Add scaled video layer based on fit mode.

```python
fg_label = builder.add_scaled_video(
    plan=composition_plan,
    input_label="0:v",
)
```

**Generated filter (FIT_WIDTH)**:
```
[0:v]scale=1080:607:force_original_aspect_ratio=decrease[scaled0]
```

### add_overlay()

Overlay foreground on background.

```python
final_label = builder.add_overlay(
    background_label="bgblur0",
    foreground_label="scaled0",
    x=0,
    y=656,
)
```

**Generated filter**:
```
[bgblur0][scaled0]overlay=0:656[overlay0]
```

### add_ass_subtitles()

Add ASS subtitle overlay.

```python
subs_label = builder.add_ass_subtitles(
    input_label="overlay0",
    subtitle_path="captions.ass",
)
```

**Generated filter**:
```
[overlay0]ass=captions.ass[subs0]
```

### add_pad()

Add padding/border.

```python
padded_label = builder.add_pad(
    input_label="scaled0",
    width=1080,
    height=1920,
    x=0,
    y=656,
    color="black",
)
```

**Generated filter**:
```
[scaled0]pad=1080:1920:0:656:color=black[pad0]
```

### build()

Build complete filter_complex string.

```python
filter_complex = builder.build()
```

**Returns**:
```
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15[bgblur0];[0:v]scale=1080:607:force_original_aspect_ratio=decrease[scaled0];[bgblur0][scaled0]overlay=0:656[out]
```

### build_composition_graph()

Convenience method to build complete graph from composition plan.

```python
filter_complex = builder.build_composition_graph(plan)
```

This method:
1. Adds background layer (if needed)
2. Adds scaled video layer
3. Overlays video on background
4. Returns complete filter string

## Complete Example

### Fit-Width with Blur Background

```python
from app.services.composition import CompositionPlanner, FitMode, BackgroundMode
from app.services.formats import FormatRegistry
from app.services.renderer import FFmpegGraphBuilder

# 1. Create composition plan
planner = CompositionPlanner()
output_format = FormatRegistry.get("shorts")

plan = planner.plan_composition(
    video_width=1920,
    video_height=1080,
    output_format=output_format,
    fit_mode=FitMode.FIT_WIDTH,
    background_mode=BackgroundMode.BLUR,
    blur_strength=15,
)

# 2. Build FFmpeg graph
builder = FFmpegGraphBuilder()
filter_complex = builder.build_composition_graph(plan)

# 3. Execute FFmpeg
cmd = [
    "ffmpeg",
    "-i", "input.mp4",
    "-filter_complex", filter_complex,
    "-map", "[out]",
    "-map", "0:a?",
    "output.mp4",
]
```

### With Subtitles

```python
builder = FFmpegGraphBuilder()

# Build base composition
filter_complex = builder.build_composition_graph(plan)

# Add subtitles
filter_complex += ";[out]ass=captions.ass[final]"

cmd = [
    "ffmpeg",
    "-i", "input.mp4",
    "-filter_complex", filter_complex,
    "-map", "[final]",
    "-map", "0:a?",
    "output.mp4",
]
```

## Filter Breakdown

### Background Blur Filter

```
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,
     crop=1080:1920,
     boxblur=15[bg]
```

**Steps**:
1. Scale video to fill canvas (may exceed)
2. Crop to exact canvas size
3. Apply box blur

### Fit-Width Video Filter

```
[0:v]scale=1080:607:force_original_aspect_ratio=decrease[fg]
```

**Steps**:
1. Scale to canvas width (1080px)
2. Maintain aspect ratio (height becomes 607px)

### Overlay Filter

```
[bg][fg]overlay=0:656[out]
```

**Steps**:
1. Take background layer
2. Overlay foreground at position (0, 656)
3. Output as [out]

## Advanced Usage

### Multiple Overlays

```python
builder = FFmpegGraphBuilder()

bg = builder.add_background_blur(plan, "0:v")
video = builder.add_scaled_video(plan, "0:v")
composed = builder.add_overlay(bg, video, 0, 656)

# Add logo overlay
logo_input = builder.add_input("logo.png")
final = builder.add_overlay(composed, logo_input, 50, 50)

filter_complex = builder.build()
```

### Custom Filters

```python
builder = FFmpegGraphBuilder()

# Add custom filter manually
builder.filters.append("[0:v]hue=s=0[grayscale]")

# Continue with standard methods
scaled = builder.add_scaled_video(plan, "grayscale")
```

## Debugging

### Print Filter Graph

```python
filter_complex = builder.build()
print(filter_complex)
```

### Visualize with FFmpeg

```bash
ffmpeg -i input.mp4 -filter_complex "$FILTER" -map "[out]" -f null -
```

This runs the filter without encoding to verify it works.

### Test Individual Filters

```python
builder = FFmpegGraphBuilder()
builder.filters.append("[0:v]scale=1080:1920[test]")
assert builder.build() == "[0:v]scale=1080:1920[test]"
```

## Common Patterns

### Pattern: Background + Video + Subtitles

```python
def render_with_captions(input_path, output_path, plan, subtitle_path):
    builder = FFmpegGraphBuilder()
    
    bg = builder.add_background_blur(plan, "0:v")
    fg = builder.add_scaled_video(plan, "0:v")
    composed = builder.add_overlay(bg, fg, plan.video.x, plan.video.y, "composed")
    final = builder.add_ass_subtitles(composed, subtitle_path, "final")
    
    filter_complex = builder.build()
    
    # Execute FFmpeg...
```

### Pattern: Multi-Input Composition

```python
builder = FFmpegGraphBuilder()

video1 = builder.add_input("video1.mp4")  # 0:v
video2 = builder.add_input("video2.mp4")  # 1:v

scaled1 = builder.add_scaled_video(plan, video1)
scaled2 = builder.add_scaled_video(plan, video2)

# Side-by-side
final = builder.add_overlay(scaled1, scaled2, 540, 0)
```

## Performance

- **Graph building**: < 1ms (pure Python)
- **FFmpeg execution**: Same as manual filter strings
- **Memory**: Minimal (small string concatenation)

## Testing

### Unit Test Example

```python
def test_background_blur():
    builder = FFmpegGraphBuilder()
    plan = create_test_plan(blur_strength=10)
    
    bg_label = builder.add_background_blur(plan, "0:v")
    
    assert "boxblur=10" in builder.build()
    assert bg_label == "bgblur0"
```

### Integration Test Example

```python
def test_full_composition():
    builder = FFmpegGraphBuilder()
    plan = create_shorts_plan()
    
    filter_complex = builder.build_composition_graph(plan)
    
    # Verify filter contains expected components
    assert "scale=" in filter_complex
    assert "overlay=" in filter_complex
    assert "[out]" in filter_complex
```

## Troubleshooting

### Filter Fails to Execute

**Symptom**: FFmpeg error about invalid filter

**Solution**: Print filter and test manually
```python
print(builder.build())
```

### Labels Conflict

**Symptom**: FFmpeg error about duplicate labels

**Solution**: Use unique output labels
```python
builder.add_overlay(bg, fg, 0, 0, output_label="unique_label")
```

### Filter Order Wrong

**Symptom**: Unexpected visual result

**Solution**: Verify filter order matches intent
```python
for i, filter_str in enumerate(builder.filters):
    print(f"{i}: {filter_str}")
```

## Best Practices

### 1. Use Builder Methods

❌ **Don't**: Manually construct filter strings
```python
filter_str = f"[0:v]scale={width}:{height}[out]"
```

✅ **Do**: Use builder methods
```python
builder.add_scaled_video(plan, "0:v")
```

### 2. Let Builder Manage Labels

❌ **Don't**: Hardcode labels
```python
builder.filters.append("[0:v]scale=1080:1920[myLabel]")
```

✅ **Do**: Use returned labels
```python
label = builder.add_scaled_video(plan, "0:v")
```

### 3. Build Once, Execute Once

```python
builder = FFmpegGraphBuilder()
# ... add filters ...
filter_complex = builder.build()  # Build once
# Use filter_complex in FFmpeg command
```

### 4. Test Filter Graphs

Always test generated filters before production use.

## Summary

The FFmpeg Graph Builder provides:

✅ Modular filter generation  
✅ Automatic label management  
✅ Testable architecture  
✅ Reusable filter methods  
✅ Clear, readable code  
✅ Easy debugging  

Use the graph builder for all FFmpeg filter generation to maintain code quality and enable future enhancements.
