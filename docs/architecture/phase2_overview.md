# Phase 2 Architecture Overview

## Introduction

YT-Clipper Phase 2 transforms the system from a YouTube clipper into a **Multi-Format AI Content Engine** with production-grade rendering capabilities, auto-caption generation, and extensible composition architecture.

## System Evolution

### Phase 1 (Original)
- YouTube download → Transcribe → AI Analysis → Clip → Center Crop → Export

### Phase 2 (Enhanced)
- YouTube download → Transcribe (word-level) → AI Analysis → Clip Selection → **Composition Planning** → **Caption Generation** → **Render Graph Build** → Export

## Core Architectural Changes

### 1. Separation of Concerns

Phase 2 introduces clear boundaries between:

- **Planning**: Composition planning, layout calculation
- **Rendering**: FFmpeg execution, filter graph generation
- **Captioning**: Word timestamps, chunking, ASS generation
- **Formatting**: Output format definitions, aspect ratios

### 2. New Service Modules

```
app/services/
├── formats/          # Output format registry
├── composition/      # Layout planning engine
├── templates/        # Render template system
├── renderer/         # FFmpeg graph builder
└── captions/         # Auto caption system
```

### 3. Key Design Principles

1. **Composition Plans are Data**: Plans are Pydantic models, not code
2. **Templates Generate Plans**: Templates create reusable compositions
3. **Renderer Executes Plans**: Renderer consumes plans, doesn't create them
4. **FFmpeg is Abstracted**: Graph builder creates modular filter chains
5. **Captions are Separate**: Caption system is independent of rendering

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     CLI / API Layer                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Workflow Orchestration                     │
│  (Download → Transcribe → Analyze → Plan → Render → Export) │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│  Format Registry │ Template Registry│  Caption Presets     │
│  (Output Specs)  │ (Layout Rules)   │  (Style Definitions) │
└──────────────────┴──────────────────┴──────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                   Composition Planner                        │
│         (Calculates layout, positioning, scaling)            │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    CompositionPlan (Data)
                              ↓
┌──────────────────┬──────────────────┬──────────────────────┐
│  Caption Service │  Render Service  │  FFmpeg Graph Builder│
│  (ASS Generation)│  (Orchestration) │  (Filter Chains)     │
└──────────────────┴──────────────────┴──────────────────────┘
                              ↓
                         Final Video
```

## Service Responsibilities

### Format Registry
- Defines output specifications (resolution, aspect ratio, safe areas)
- Provides built-in formats (shorts, square, landscape, portrait)
- Supports custom format registration

### Composition Planner
- Calculates video positioning and scaling
- Determines background layer strategy
- Ensures safe area compliance
- Generates CompositionPlan data structures

### Template System
- Encapsulates rendering strategies
- Generates composition plans for specific styles
- Supports format compatibility checking
- Extensible for custom templates

### Renderer Service
- Orchestrates final rendering
- Consumes composition plans
- Coordinates subtitle overlays
- Manages temporary artifacts

### FFmpeg Graph Builder
- Generates modular filter chains
- Abstracts complex FFmpeg syntax
- Supports background blur, scaling, overlays
- Enables unit testing of filter logic

### Caption Service
- Extracts word-level timestamps
- Performs intelligent chunking
- Generates ASS subtitle files
- Applies style presets
- Supports karaoke highlighting

## Data Flow

### Rendering Pipeline

```
1. User Request
   ↓
2. Format Selection (e.g., "shorts")
   ↓
3. Template Selection (e.g., "shorts_fit")
   ↓
4. Template generates CompositionPlan
   ↓
5. Renderer builds FFmpeg graph from plan
   ↓
6. FFmpeg executes rendering
   ↓
7. Output video
```

### Caption Pipeline

```
1. Audio file
   ↓
2. Whisper transcription (word_timestamps=True)
   ↓
3. Word-level timestamps extracted
   ↓
4. Caption chunker segments words
   ↓
5. Style preset applied
   ↓
6. ASS generator creates subtitle file
   ↓
7. Renderer burns subtitles into video
```

## Key Behavioral Changes

### Default Rendering: Fit-Width

**Phase 1**: Center crop to 9:16 (aggressive crop)

**Phase 2**: Fit by width, preserve full frame

```
┌─────────────────────┐
│   Blurred BG        │
├─────────────────────┤
│                     │
│   Source Video      │
│   (Full Frame)      │
│                     │
├─────────────────────┤
│   Blurred BG        │
└─────────────────────┘
```

### Caption System

**Phase 1**: Basic SRT subtitles

**Phase 2**: Production-grade ASS captions with:
- Word-level timing
- Intelligent chunking
- Custom styling
- Animation effects
- Karaoke highlighting

## Extensibility Points

### Adding a New Format

```python
from app.services.formats import OutputFormat, FormatRegistry

custom_format = OutputFormat(
    name="custom_916",
    width=1080,
    height=1920,
    aspect_ratio="9:16",
    safe_margin=50,
    caption_zone_height=250,
)

FormatRegistry.register(custom_format)
```

### Adding a New Template

```python
from app.services.templates import RenderTemplate

class CustomTemplate(RenderTemplate):
    @property
    def name(self) -> str:
        return "custom"
    
    def generate_composition(self, video_width, video_height, output_format):
        # Generate composition plan
        pass
```

### Adding a New Caption Preset

```python
from app.services.captions import CaptionStyle

custom_style = CaptionStyle(
    font_name="Custom Font",
    font_size=50,
    primary_color="&H00FF00FF",
    outline_width=4,
    animation_preset="custom_animation",
)
```

## Migration from Phase 1

### Backward Compatibility

Phase 2 maintains backward compatibility:

- Existing workflows continue to work
- Default behavior uses new fit-width rendering
- Legacy center-crop available via `shorts_blur` template
- Existing APIs unchanged

### Breaking Changes

None. Phase 2 is additive.

### Deprecated Features

- Direct FFmpeg filter string generation (use graph builder)
- Hardcoded resolution strings (use format registry)

## Performance Considerations

### Composition Planning
- Planning is fast (pure Python calculations)
- Plans are cacheable
- No FFmpeg execution during planning

### FFmpeg Graph Generation
- Modular filter chains
- Optimized for readability and maintainability
- No performance regression vs Phase 1

### Caption Generation
- Word timestamp extraction adds ~10% to transcription time
- ASS generation is fast (< 1s for typical video)
- Chunking is O(n) where n = word count

## Testing Strategy

### Unit Tests
- Format registry
- Composition calculations
- Caption chunking logic
- ASS generation
- FFmpeg graph building

### Integration Tests
- End-to-end rendering
- Caption + video rendering
- Multi-format output

### Manual Testing
- Visual quality verification
- Caption timing accuracy
- Cross-platform compatibility

## Future Enhancements

### Phase 3 Candidates
- Face tracking for smart crop
- Scene detection
- Background music integration
- Multi-language captions
- Real-time preview generation

### API Readiness
Phase 2 architecture is FastAPI-ready:
- All services are dependency-injectable
- Pydantic models everywhere
- Stateless service design
- Background job compatible

## Summary

Phase 2 transforms YT-Clipper into a production-grade content engine with:

✅ Multi-format rendering  
✅ Extensible composition system  
✅ Production-grade captions  
✅ Modular FFmpeg abstraction  
✅ Backward compatibility  
✅ FastAPI-ready architecture  

The system is now comparable to commercial tools like OpusClip, Captions.ai, and Vidyo.ai in terms of architectural sophistication and rendering capabilities.
