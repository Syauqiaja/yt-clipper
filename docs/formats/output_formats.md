# Output Formats

## Overview

Output formats define target specifications for video rendering including resolution, aspect ratio, safe areas, and caption zones.

## Format Model

```python
from app.services.formats.models import OutputFormat

format = OutputFormat(
    name="shorts",
    width=1080,
    height=1920,
    aspect_ratio="9:16",
    safe_margin=40,
    caption_zone_height=200,
)
```

### Properties

- **name**: Unique format identifier
- **width**: Canvas width in pixels
- **height**: Canvas height in pixels
- **aspect_ratio**: Human-readable ratio (e.g., "9:16")
- **safe_margin**: Safe area margin in pixels
- **caption_zone_height**: Height reserved for captions

### Computed Properties

```python
format.ratio          # 0.5625 (numeric aspect ratio)
format.is_vertical    # True
format.is_horizontal  # False
format.is_square      # False
```

## Built-in Formats

### shorts (Default)

```python
OutputFormat(
    name="shorts",
    width=1080,
    height=1920,
    aspect_ratio="9:16",
    safe_margin=40,
    caption_zone_height=200,
)
```

**Use case**: YouTube Shorts, general vertical content

### tiktok

```python
OutputFormat(
    name="tiktok",
    width=1080,
    height=1920,
    aspect_ratio="9:16",
    safe_margin=50,
    caption_zone_height=220,
)
```

**Use case**: TikTok-optimized with larger safe margins

### instagram_reel

```python
OutputFormat(
    name="instagram_reel",
    width=1080,
    height=1920,
    aspect_ratio="9:16",
    safe_margin=45,
    caption_zone_height=200,
)
```

**Use case**: Instagram Reels

### youtube_short

```python
OutputFormat(
    name="youtube_short",
    width=1080,
    height=1920,
    aspect_ratio="9:16",
    safe_margin=40,
    caption_zone_height=200,
)
```

**Use case**: YouTube Shorts (same as "shorts")

### square

```python
OutputFormat(
    name="square",
    width=1080,
    height=1080,
    aspect_ratio="1:1",
    safe_margin=30,
    caption_zone_height=150,
)
```

**Use case**: Instagram posts, Facebook posts

### landscape

```python
OutputFormat(
    name="landscape",
    width=1920,
    height=1080,
    aspect_ratio="16:9",
    safe_margin=40,
    caption_zone_height=120,
)
```

**Use case**: YouTube videos, horizontal content

### portrait_45

```python
OutputFormat(
    name="portrait_45",
    width=1080,
    height=1350,
    aspect_ratio="4:5",
    safe_margin=35,
    caption_zone_height=180,
)
```

**Use case**: Instagram feed posts (4:5 ratio)

## Format Registry

### Get Format

```python
from app.services.formats import FormatRegistry

format = FormatRegistry.get("shorts")
```

### List All Formats

```python
formats = FormatRegistry.list_formats()
# ['shorts', 'square', 'landscape', 'tiktok', ...]
```

### Get All Format Objects

```python
all_formats = FormatRegistry.get_all()
# {'shorts': OutputFormat(...), 'square': OutputFormat(...), ...}
```

## Creating Custom Formats

### Example: Custom Vertical Format

```python
from app.services.formats import OutputFormat, FormatRegistry

custom_format = OutputFormat(
    name="custom_vertical",
    width=1080,
    height=2400,
    aspect_ratio="9:20",
    safe_margin=60,
    caption_zone_height=250,
)

FormatRegistry.register(custom_format)
```

### Example: Ultra-Wide Format

```python
ultrawide = OutputFormat(
    name="ultrawide",
    width=2560,
    height=1080,
    aspect_ratio="21:9",
    safe_margin=50,
    caption_zone_height=100,
)

FormatRegistry.register(ultrawide)
```

## Safe Areas

Safe areas ensure content isn't obscured by platform UI elements.

### Platform UI Overlays

Different platforms have different UI overlays:

**TikTok**:
- Top: Profile icon, caption text
- Bottom: Action buttons, caption
- Recommended safe margin: 50px

**Instagram Reels**:
- Top: Username, audio info
- Bottom: Action buttons, caption
- Recommended safe margin: 45px

**YouTube Shorts**:
- Top: Channel info
- Bottom: Like/comment buttons
- Recommended safe margin: 40px

### Safe Area Calculation

```python
format = FormatRegistry.get("shorts")

# Safe area bounds
safe_x = format.safe_margin
safe_y = format.safe_margin
safe_width = format.width - (2 * format.safe_margin)
safe_height = format.height - (2 * format.safe_margin)

# For 1080x1920 with 40px margin:
# safe_x = 40
# safe_y = 40
# safe_width = 1000
# safe_height = 1840
```

### Visual Representation

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

## Caption Zones

Caption zones reserve space for text overlays.

### Zone Calculation

```python
format = FormatRegistry.get("shorts")

caption_zone_top = format.height - format.caption_zone_height - format.safe_margin
caption_zone_height = format.caption_zone_height

# For shorts (1080x1920, 200px caption zone, 40px margin):
# caption_zone_top = 1680
# caption_zone_height = 200
```

### Visual Representation

```
┌─────────────────────┐
│                     │
│   Video Content     │
│                     │
├─────────────────────┤ ← caption_zone_top (1680px)
│                     │
│   Caption Zone      │ ← 200px height
│   (Text Safe)       │
│                     │
└─────────────────────┘
```

## Format Selection Guide

### By Platform

| Platform | Format | Aspect Ratio |
|----------|--------|--------------|
| TikTok | tiktok | 9:16 |
| Instagram Reels | instagram_reel | 9:16 |
| Instagram Feed | portrait_45 | 4:5 |
| Instagram Post | square | 1:1 |
| YouTube Shorts | youtube_short | 9:16 |
| YouTube Video | landscape | 16:9 |

### By Content Type

| Content Type | Recommended Format |
|--------------|-------------------|
| Talking head | shorts (9:16) |
| Landscape video | landscape (16:9) |
| Product showcase | square (1:1) |
| Tutorial | landscape (16:9) |
| Meme/Quote | square (1:1) |
| Podcast clip | shorts (9:16) |

### By Source Aspect Ratio

| Source | Target | Recommended Format |
|--------|--------|-------------------|
| 16:9 → Vertical | shorts | 9:16 |
| 16:9 → Square | square | 1:1 |
| 4:3 → Vertical | shorts | 9:16 |
| 9:16 → Horizontal | landscape | 16:9 |

## CLI Usage

### List Formats

```bash
python main.py formats list
```

Output:
```
Available Output Formats

Name              Resolution    Aspect Ratio  Type
shorts            1080x1920     9:16          Vertical
square            1080x1080     1:1           Square
landscape         1920x1080     16:9          Horizontal
tiktok            1080x1920     9:16          Vertical
instagram_reel    1080x1920     9:16          Vertical
portrait_45       1080x1350     4:5           Vertical
```

### Use Format

```bash
python main.py clip run "https://youtube.com/watch?v=..." \
    --format shorts
```

## Format Validation

### Validate Format

```python
from app.services.formats import FormatRegistry
from app.core.exceptions import ValidationError

try:
    format = FormatRegistry.get("invalid_format")
except ValidationError as e:
    print(f"Error: {e}")
    # Error: Format 'invalid_format' not found. Available: shorts, square, ...
```

### Check Format Properties

```python
format = FormatRegistry.get("shorts")

assert format.width > 0
assert format.height > 0
assert format.safe_margin >= 0
assert format.caption_zone_height >= 0
```

## Best Practices

### 1. Use Named Formats

❌ **Don't**: Hardcode dimensions
```python
width = 1080
height = 1920
```

✅ **Do**: Use format registry
```python
format = FormatRegistry.get("shorts")
width = format.width
height = format.height
```

### 2. Respect Safe Areas

Always position important content within safe areas:

```python
format = FormatRegistry.get("shorts")
text_y = format.height - format.caption_zone_height - format.safe_margin
```

### 3. Use Appropriate Margins

Different platforms need different margins:

- TikTok: 50px (more UI elements)
- Instagram: 45px
- YouTube: 40px

### 4. Test on Target Platform

Always preview rendered videos on the target platform to verify safe areas and caption positioning.

## Troubleshooting

### Content Cut Off

**Cause**: Content positioned outside safe area

**Solution**: Use safe margins
```python
x = format.safe_margin
y = format.safe_margin
```

### Captions Obscured

**Cause**: Captions positioned in platform UI area

**Solution**: Use caption zone
```python
caption_y = format.height - format.caption_zone_height - format.safe_margin
```

### Wrong Aspect Ratio

**Cause**: Using wrong format for platform

**Solution**: Check platform requirements and use correct format

## Summary

Output formats provide:

✅ Platform-specific specifications  
✅ Safe area definitions  
✅ Caption zone management  
✅ Aspect ratio handling  
✅ Extensible format system  

Use the format registry for all rendering operations to ensure platform compatibility and proper content positioning.
