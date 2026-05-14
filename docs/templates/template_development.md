# Template Development Guide

## Overview

Templates encapsulate rendering strategies for specific output formats and styles. They generate composition plans that the renderer executes.

## Template Architecture

```
Template
    ↓
generate_composition()
    ↓
CompositionPlan
    ↓
Renderer
    ↓
Final Video
```

## Base Template Interface

All templates inherit from `RenderTemplate`:

```python
from abc import ABC, abstractmethod
from app.services.templates.base import RenderTemplate

class CustomTemplate(RenderTemplate):
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique template identifier."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description."""
        pass
    
    @abstractmethod
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate composition plan."""
        pass
    
    @abstractmethod
    def supports_format(self, format_name: str) -> bool:
        """Check format compatibility."""
        pass
```

## Built-in Templates

### ShortsFitTemplate (Default)

Fit-width layout with blurred background for vertical content.

```python
from app.services.templates import ShortsFitTemplate

template = ShortsFitTemplate(blur_strength=15)
```

**Behavior**:
- Scales video to canvas width
- Preserves full frame
- Adds blurred background top/bottom
- Centers video vertically

**Supported formats**: shorts, tiktok, instagram_reel, youtube_short, portrait_45

### ShortsBlurTemplate (Legacy)

Center crop with blur fallback.

```python
from app.services.templates import ShortsBlurTemplate

template = ShortsBlurTemplate(blur_strength=10)
```

**Behavior**:
- Center crops video to 9:16
- Aggressive crop (legacy Phase 1 behavior)

**Supported formats**: shorts, tiktok, instagram_reel, youtube_short

### SquareTemplate

Square format for Instagram posts.

```python
from app.services.templates import SquareTemplate

template = SquareTemplate()
```

**Behavior**:
- Automatically selects FIT_WIDTH or FIT_HEIGHT
- Minimizes cropping
- Blurred background

**Supported formats**: square

## Creating a Custom Template

### Example: Cinematic Template

```python
from app.services.composition import (
    CompositionPlanner,
    FitMode,
    BackgroundMode,
)
from app.services.formats import OutputFormat
from app.services.templates.base import RenderTemplate


class CinematicTemplate(RenderTemplate):
    """
    Cinematic template with letterbox bars.
    """
    
    def __init__(self, bar_height: int = 100):
        self.planner = CompositionPlanner()
        self.bar_height = bar_height
    
    @property
    def name(self) -> str:
        return "cinematic"
    
    @property
    def description(self) -> str:
        return "Cinematic letterbox with black bars"
    
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate cinematic composition with letterbox."""
        
        # Calculate video area (excluding bars)
        video_area_height = output_format.height - (2 * self.bar_height)
        
        # Use fit-width for video
        plan = self.planner.plan_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
            fit_mode=FitMode.FIT_WIDTH,
            background_mode=BackgroundMode.NONE,
        )
        
        # Adjust video position to account for top bar
        plan.video.y += self.bar_height
        
        # Add metadata
        plan.metadata["letterbox_bars"] = True
        plan.metadata["bar_height"] = self.bar_height
        
        return plan
    
    def supports_format(self, format_name: str) -> bool:
        """Supports all formats."""
        return True
```

### Register Custom Template

```python
from app.services.templates import TemplateRegistry

template = CinematicTemplate(bar_height=120)
TemplateRegistry.register(template)
```

### Use Custom Template

```python
from app.services.renderer import RenderService

renderer = RenderService()
renderer.render_with_template(
    input_path="video.mp4",
    output_path="output.mp4",
    template_name="cinematic",
    format_name="shorts",
    video_width=1920,
    video_height=1080,
)
```

## Advanced Template Examples

### Split-Screen Template

```python
class SplitScreenTemplate(RenderTemplate):
    """Split screen with two videos side-by-side."""
    
    def __init__(self, split_ratio: float = 0.5):
        self.planner = CompositionPlanner()
        self.split_ratio = split_ratio
    
    @property
    def name(self) -> str:
        return "split_screen"
    
    @property
    def description(self) -> str:
        return "Split screen layout"
    
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate split-screen composition."""
        
        # Calculate split widths
        left_width = int(output_format.width * self.split_ratio)
        right_width = output_format.width - left_width
        
        # Create base plan
        plan = self.planner.plan_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
            fit_mode=FitMode.FIT_HEIGHT,
            background_mode=BackgroundMode.NONE,
        )
        
        # Adjust for left side
        plan.video.width = left_width
        plan.video.x = 0
        
        # Store split info in metadata
        plan.metadata["split_screen"] = True
        plan.metadata["left_width"] = left_width
        plan.metadata["right_width"] = right_width
        
        return plan
    
    def supports_format(self, format_name: str) -> bool:
        return format_name in ["landscape", "square"]
```

### Picture-in-Picture Template

```python
class PictureInPictureTemplate(RenderTemplate):
    """Picture-in-picture layout."""
    
    def __init__(self, pip_size: float = 0.25, pip_position: str = "bottom_right"):
        self.planner = CompositionPlanner()
        self.pip_size = pip_size
        self.pip_position = pip_position
    
    @property
    def name(self) -> str:
        return "pip"
    
    @property
    def description(self) -> str:
        return "Picture-in-picture layout"
    
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate PIP composition."""
        from app.services.composition import OverlayLayer, OverlayPosition
        
        # Main video fills canvas
        plan = self.planner.plan_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
            fit_mode=FitMode.FIT_WIDTH,
            background_mode=BackgroundMode.BLUR,
        )
        
        # Calculate PIP dimensions
        pip_width = int(output_format.width * self.pip_size)
        pip_height = int(output_format.height * self.pip_size)
        
        # Position PIP
        if self.pip_position == "bottom_right":
            pip_x = output_format.width - pip_width - 20
            pip_y = output_format.height - pip_height - 20
        # ... other positions
        
        # Add PIP overlay
        pip_overlay = OverlayLayer(
            type="video",
            x=pip_x,
            y=pip_y,
            width=pip_width,
            height=pip_height,
            content="pip_source",
        )
        
        plan.overlays.append(pip_overlay)
        plan.metadata["pip"] = True
        
        return plan
    
    def supports_format(self, format_name: str) -> bool:
        return True
```

### Ken Burns Template

```python
class KenBurnsTemplate(RenderTemplate):
    """Ken Burns zoom effect template."""
    
    def __init__(self, zoom_factor: float = 1.1, duration: float = 5.0):
        self.planner = CompositionPlanner()
        self.zoom_factor = zoom_factor
        self.duration = duration
    
    @property
    def name(self) -> str:
        return "ken_burns"
    
    @property
    def description(self) -> str:
        return "Ken Burns zoom effect"
    
    def generate_composition(
        self,
        video_width: int,
        video_height: int,
        output_format: OutputFormat,
    ) -> CompositionPlan:
        """Generate Ken Burns composition."""
        
        plan = self.planner.plan_composition(
            video_width=video_width,
            video_height=video_height,
            output_format=output_format,
            fit_mode=FitMode.FIT_WIDTH,
            background_mode=BackgroundMode.BLUR,
        )
        
        # Store zoom parameters in metadata
        plan.metadata["ken_burns"] = True
        plan.metadata["zoom_factor"] = self.zoom_factor
        plan.metadata["zoom_duration"] = self.duration
        
        return plan
    
    def supports_format(self, format_name: str) -> bool:
        return True
```

## Template Best Practices

### 1. Use CompositionPlanner

Always use `CompositionPlanner` for layout calculations:

```python
self.planner = CompositionPlanner()
plan = self.planner.plan_composition(...)
```

### 2. Store Configuration in Metadata

```python
plan.metadata["template_name"] = self.name
plan.metadata["custom_param"] = self.custom_value
```

### 3. Validate Format Compatibility

```python
def supports_format(self, format_name: str) -> bool:
    # Only support vertical formats
    return format_name in ["shorts", "tiktok", "instagram_reel"]
```

### 4. Make Templates Configurable

```python
def __init__(self, blur_strength: int = 15, margin: int = 40):
    self.blur_strength = blur_strength
    self.margin = margin
```

### 5. Document Template Behavior

```python
class MyTemplate(RenderTemplate):
    """
    Custom template description.
    
    Behavior:
        - Scales video to fit width
        - Adds gradient background
        - Positions logo in top-right
    
    Supported formats:
        - shorts
        - square
    
    Parameters:
        gradient_start: Start color (hex)
        gradient_end: End color (hex)
    """
```

## Testing Templates

### Unit Test Example

```python
def test_cinematic_template():
    template = CinematicTemplate(bar_height=100)
    output_format = FormatRegistry.get("shorts")
    
    plan = template.generate_composition(
        video_width=1920,
        video_height=1080,
        output_format=output_format,
    )
    
    # Verify letterbox bars
    assert plan.metadata["letterbox_bars"] is True
    assert plan.metadata["bar_height"] == 100
    
    # Verify video position adjusted for top bar
    assert plan.video.y >= 100
```

### Integration Test Example

```python
def test_template_rendering():
    template = ShortsFitTemplate()
    renderer = RenderService()
    
    output_path = renderer.render_with_template(
        input_path="test_video.mp4",
        output_path="output.mp4",
        template_name="shorts_fit",
        format_name="shorts",
        video_width=1920,
        video_height=1080,
    )
    
    assert output_path.exists()
```

## Template Registry

### List Templates

```python
from app.services.templates import TemplateRegistry

templates = TemplateRegistry.list_templates()
# ['shorts_fit', 'shorts_blur', 'square']
```

### Get Template

```python
template = TemplateRegistry.get("shorts_fit")
```

### Get Templates for Format

```python
compatible = TemplateRegistry.get_for_format("shorts")
# [ShortsFitTemplate, ShortsBlurTemplate]
```

## CLI Usage

### List Available Templates

```bash
python main.py templates list
```

### Use Template

```bash
python main.py clip run "https://youtube.com/watch?v=..." \
    --template shorts_fit \
    --format shorts
```

## Common Patterns

### Pattern: Conditional Layout

```python
def generate_composition(self, video_width, video_height, output_format):
    video_aspect = video_width / video_height
    canvas_aspect = output_format.width / output_format.height
    
    if video_aspect > canvas_aspect:
        # Video is wider than canvas
        fit_mode = FitMode.FIT_HEIGHT
    else:
        # Video is taller than canvas
        fit_mode = FitMode.FIT_WIDTH
    
    return self.planner.plan_composition(
        video_width, video_height, output_format, fit_mode
    )
```

### Pattern: Multi-Layer Composition

```python
def generate_composition(self, video_width, video_height, output_format):
    plan = self.planner.plan_composition(...)
    
    # Add logo overlay
    logo = OverlayLayer(
        type="image",
        position=OverlayPosition.TOP_RIGHT,
        width=200,
        height=200,
        content="logo.png",
    )
    plan.overlays.append(logo)
    
    # Add watermark
    watermark = OverlayLayer(
        type="text",
        position=OverlayPosition.BOTTOM_LEFT,
        content="@username",
    )
    plan.overlays.append(watermark)
    
    return plan
```

## Troubleshooting

### Template Not Found

**Cause**: Template not registered

**Solution**: Register template
```python
TemplateRegistry.register(my_template)
```

### Format Not Supported

**Cause**: `supports_format()` returns False

**Solution**: Update format compatibility
```python
def supports_format(self, format_name: str) -> bool:
    return format_name in ["shorts", "square", "landscape"]
```

### Composition Plan Invalid

**Cause**: Invalid dimensions or positions

**Solution**: Validate plan before returning
```python
assert plan.video.width <= plan.canvas_width
assert plan.video.height <= plan.canvas_height
```

## Summary

Templates provide:

✅ Reusable rendering strategies  
✅ Format-specific optimizations  
✅ Extensible architecture  
✅ Clean separation from rendering  
✅ Easy testing and validation  

Create custom templates to encapsulate your unique rendering styles and layouts.
