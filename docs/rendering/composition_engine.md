# Composition Engine

## Overview

The Composition Engine is responsible for calculating video layout, positioning, and scaling for multi-format rendering. It generates **CompositionPlan** objects that describe how to render a video without executing any FFmpeg commands.

## Core Concept

**Separation of Planning and Rendering**

- **Planning**: Calculate dimensions, positions, layouts (pure Python)
- **Rendering**: Execute FFmpeg with the plan (FFmpeg execution)

This separation enables:
- Unit testing of layout logic
- Caching of composition plans
- Format-agnostic rendering
- Template reusability

## Architecture

```
┌──────────────────┐
│  Video Metadata  │
│  Output Format   │
│  Fit Mode        │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ CompositionPlanner│
│  (Calculator)    │
└────────┬─────────┘
         ↓
┌──────────────────┐
│ CompositionPlan  │
│  (Data Model)    │
└──────────────────┘
```

## CompositionPlan Model

A `CompositionPlan` is a Pydantic model containing:

```python
class CompositionPlan(BaseModel):
    canvas_width: int           # Output canvas width
    canvas_height: int          # Output canvas height
    background: BackgroundLayer # Background configuration
    video: VideoLayer           # Main video layer
    fit_mode: FitMode          # How video fits in canvas
    overlays: list[OverlayLayer] # Additional overlays
    safe_area_margin: int      # Safe area margin
    metadata: dict             # Additional metadata
```

### VideoLayer

Describes the main video positioning:

```python
class VideoLayer(BaseModel):
    width: int      # Scaled video width
    height: int     # Scaled video height
    x: int          # X position in canvas
    y: int          # Y position in canvas
    scale: float    # Scale factor
    opacity: float  # Opacity (0.0 to 1.0)
```

### BackgroundLayer

Describes background rendering:

```python
class BackgroundLayer(BaseModel):
    mode: BackgroundMode        # blur, color, gradient, image, none
    blur_strength: int          # Blur intensity (for blur mode)
    color: str | None          # Hex color (for color mode)
    gradient_start: str | None # Gradient start color
    gradient_end: str | None   # Gradient end color
    image_path: str | None     # Background image path
```

## Fit Modes

### FIT_WIDTH (Default)

Scales video to match canvas width, preserves aspect ratio, centers vertically.

**Use case**: Horizontal videos → Vertical output

```
Canvas: 1080x1920
Video:  1920x1080

Result:
  Video width:  1080px (matches canvas)
  Video height: 607px  (maintains 16:9)
  Position:     (0, 656) (centered vertically)
```

**Visual**:
```
┌─────────────────────┐
│   Blurred BG        │ ← Top padding
├─────────────────────┤
│                     │
│   Source Video      │ ← Full width
│   (1080x607)        │
│                     │
├─────────────────────┤
│   Blurred BG        │ ← Bottom padding
└─────────────────────┘
```

### FIT_HEIGHT

Scales video to match canvas height, preserves aspect ratio, centers horizontally.

**Use case**: Vertical videos → Horizontal output

### CENTER_CROP (Legacy)

Scales video to fill canvas, crops excess.

**Use case**: Backward compatibility with Phase 1

### STRETCH

Stretches video to fill canvas (may distort).

**Use case**: Rare, when distortion is acceptable

## CompositionPlanner Service

### Basic Usage

```python
from app.services.composition import CompositionPlanner, FitMode
from app.services.formats import FormatRegistry

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
```

### Calculation Logic

#### Fit-Width Calculation

```python
def _fit_width(video_width, video_height, canvas_width, canvas_height):
    # Calculate aspect ratio
    video_aspect = video_width / video_height
    
    # Scale to canvas width
    scaled_width = canvas_width
    scaled_height = int(canvas_width / video_aspect)
    
    # Center vertically
    x = 0
    y = (canvas_height - scaled_height) // 2
    
    return VideoLayer(
        width=scaled_width,
        height=scaled_height,
        x=x,
        y=y,
    )
```

#### Fit-Height Calculation

```python
def _fit_height(video_width, video_height, canvas_width, canvas_height):
    video_aspect = video_width / video_height
    
    scaled_height = canvas_height
    scaled_width = int(canvas_height * video_aspect)
    
    x = (canvas_width - scaled_width) // 2
    y = 0
    
    return VideoLayer(
        width=scaled_width,
        height=scaled_height,
        x=x,
        y=y,
    )
```

## Safe Areas

Safe areas ensure content isn't cut off by platform UI elements.

```python
safe_x, safe_y, safe_width, safe_height = plan.get_safe_area()
```

**Example** (shorts format with 40px margin):
```
Canvas: 1080x1920
Safe area: (40, 40, 1000, 1840)
```

**Visual**:
```
┌─────────────────────┐
│ ← 40px margin       │
│  ┌───────────────┐  │
│  │               │  │
│  │  Safe Area    │  │
│  │  1000x1840    │  │
│  │               │  │
│  └───────────────┘  │
│       40px margin → │
└─────────────────────┘
```

## Background Modes

### BLUR (Default)

Blurs and scales source video as background.

**FFmpeg equivalent**:
```
[0:v]scale=1080:1920:force_original_aspect_ratio=increase,
     crop=1080:1920,
     boxblur=15[bg]
```

### COLOR

Solid color background.

**Use case**: Clean, minimal aesthetic

### GRADIENT

Gradient background (future enhancement).

### IMAGE

Custom image background (future enhancement).

### NONE

Black canvas, no background.

## Layout Rules

### Vertical Formats (9:16, 4:5)

**Default**: FIT_WIDTH
- Preserves full horizontal frame
- Adds blurred padding top/bottom
- Ideal for landscape → portrait conversion

### Square Formats (1:1)

**Default**: FIT_WIDTH or FIT_HEIGHT (whichever fits better)
- Automatically selects best fit
- Minimizes cropping

### Horizontal Formats (16:9)

**Default**: FIT_HEIGHT
- Preserves full vertical frame
- Adds blurred padding left/right

## Adding Custom Layouts

### Example: Corner Positioning

```python
class CornerPositionPlanner(CompositionPlanner):
    def plan_corner_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
        corner: str = "top_right",
    ) -> CompositionPlan:
        # Scale video to 1/4 canvas size
        scaled_width = output_format.width // 2
        scaled_height = output_format.height // 2
        
        # Position in corner
        if corner == "top_right":
            x = output_format.width - scaled_width
            y = 0
        # ... other corners
        
        video_layer = VideoLayer(
            width=scaled_width,
            height=scaled_height,
            x=x,
            y=y,
        )
        
        # Generate plan
        return CompositionPlan(...)
```

## Overlay Support

Overlays are additional layers (text, logos, images).

```python
from app.services.composition import OverlayLayer, OverlayPosition

overlay = OverlayLayer(
    type="logo",
    position=OverlayPosition.TOP_RIGHT,
    width=200,
    height=200,
    content="/path/to/logo.png",
    opacity=0.8,
)

plan.overlays.append(overlay)
```

## Best Practices

### 1. Always Use Composition Plans

❌ **Don't**: Generate FFmpeg filters directly
```python
filter_str = f"scale={width}:{height},crop=..."
```

✅ **Do**: Generate composition plan
```python
plan = planner.plan_composition(...)
renderer.render_composition(input_path, output_path, plan)
```

### 2. Cache Plans When Possible

Plans are deterministic and cacheable:
```python
cache_key = f"{video_width}x{video_height}_{format_name}_{fit_mode}"
plan = cache.get(cache_key) or planner.plan_composition(...)
```

### 3. Validate Plans Before Rendering

```python
assert plan.video.width <= plan.canvas_width
assert plan.video.height <= plan.canvas_height
assert plan.video.x >= 0 and plan.video.y >= 0
```

### 4. Use Safe Areas for Text/Overlays

```python
safe_x, safe_y, safe_w, safe_h = plan.get_safe_area()
text_y = safe_y + safe_h - 100  # 100px from bottom of safe area
```

## Troubleshooting

### Video Appears Stretched

**Cause**: Using STRETCH fit mode or incorrect aspect ratio calculation

**Solution**: Use FIT_WIDTH or FIT_HEIGHT

### Video Too Small

**Cause**: Using wrong fit mode for aspect ratio

**Solution**: 
- Horizontal → Vertical: Use FIT_WIDTH
- Vertical → Horizontal: Use FIT_HEIGHT

### Background Not Blurred

**Cause**: Background mode not set to BLUR

**Solution**:
```python
plan = planner.plan_composition(
    ...,
    background_mode=BackgroundMode.BLUR,
    blur_strength=15,
)
```

### Video Off-Center

**Cause**: Manual positioning override

**Solution**: Let planner calculate positions automatically

## Performance

- **Planning time**: < 1ms (pure Python math)
- **Memory**: Minimal (small Pydantic models)
- **Cacheable**: Yes (plans are deterministic)

## Summary

The Composition Engine provides:

✅ Clean separation of planning and rendering  
✅ Reusable composition logic  
✅ Format-agnostic layouts  
✅ Unit-testable calculations  
✅ Extensible for custom layouts  

Use composition plans for all rendering operations to maintain architectural consistency and enable future enhancements.
