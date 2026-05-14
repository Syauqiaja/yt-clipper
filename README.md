# YT-Clipper

**AI-powered Multi-Format Content Engine** — Automatically generate viral short-form clips with production-grade rendering, auto-captions, and multi-format support for TikTok, Instagram Reels, and YouTube Shorts.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

### Phase 2 (Current)

- **Multi-Format Rendering**: Shorts (9:16), Square (1:1), Landscape (16:9), and custom formats
- **Auto-Caption System**: Production-grade captions with word-level timing and karaoke highlighting
- **Composition Engine**: Fit-width rendering with blurred backgrounds (no aggressive cropping)
- **Template System**: Reusable rendering strategies for different styles
- **Caption Presets**: TikTok, Hormozi, Documentary, Gaming, Podcast styles
- **FFmpeg Abstraction**: Modular filter graph builder for maintainable rendering
- **ASS Subtitles**: Advanced styling with animations, positioning, and effects

### Core Features

- **AI Semantic Analysis**: Identifies high-retention moments, strong hooks, and valuable content segments
- **Automated Clip Generation**: Generates multiple short-form clips from a single YouTube video
- **Smart Scoring**: Ranks clips by hook strength, retention potential, and viral potential
- **Production Architecture**: Service-oriented design ready for FastAPI migration
- **Beautiful CLI**: Rich terminal UI with progress bars and tables

---

## Quick Start

### Prerequisites

- Python 3.12+
- FFmpeg installed and in PATH
- 9Router API key ([get one here](https://9router.com))

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/yt-clipper.git
cd yt-clipper

# Install dependencies with uv (recommended)
pip install uv
uv sync

# Or with pip
pip install -e .

# Create .env file
cp .env.example .env
# Edit .env and add your NINEROUTER_API_KEY
```

### Basic Usage

```bash
# Generate clips with auto-captions (Phase 2)
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID" \
    --format shorts \
    --template shorts_fit \
    --captions \
    --caption-style tiktok \
    --karaoke

# Generate clips (simple)
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID"

# Analyze video without rendering
python main.py analyze run "https://youtube.com/watch?v=VIDEO_ID"

# List available formats
python main.py formats list

# List available templates
python main.py templates list

# List caption presets
python main.py captions list

# Show configuration
python main.py config show

# Validate setup
python main.py config validate
```

---

## Phase 2 Architecture

YT-Clipper Phase 2 transforms the system into a **Multi-Format AI Content Engine** with production-grade rendering capabilities.

### New Systems

```
app/services/
├── formats/          # Output format registry (shorts, square, landscape)
├── composition/      # Layout planning engine (fit-width, fit-height, crop)
├── templates/        # Render template system (reusable strategies)
├── renderer/         # FFmpeg graph builder (modular filter chains)
└── captions/         # Auto caption system (word-level timing, ASS generation)
```

### Rendering Pipeline

```
Download → Transcribe (word-level) → AI Analysis → Clip Selection
    → Format Selection → Template Selection → Composition Planning
    → Caption Generation → FFmpeg Graph Build → Render → Export
```

### Key Improvements

**Fit-Width Rendering (Default)**

Phase 1: Aggressive center crop to 9:16
```
┌─────────────────────┐
│ [CROPPED VIDEO]     │
│ (loses content)     │
└─────────────────────┘
```

Phase 2: Fit by width, preserve full frame
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

**Production-Grade Captions**

- Word-level timestamps from Whisper
- Intelligent chunking (punctuation-aware, pause-aware)
- ASS subtitle generation with styling
- Multiple presets (TikTok, Hormozi, Documentary, Gaming, Podcast)
- Karaoke-style word highlighting
- Animation effects (fade, scale, bounce)

---

## CLI Reference

### Clip Generation

```bash
# Basic clip generation
python main.py clip run "URL"

# With all Phase 2 features
python main.py clip run "URL" \
    --project "my-project" \
    --max-clips 5 \
    --format shorts \
    --template shorts_fit \
    --captions \
    --caption-style tiktok \
    --karaoke \
    --verbose
```

**Options:**
- `--project, -p`: Project name for organization
- `--max-clips, -n`: Maximum clips to generate (default: 5)
- `--format, -f`: Output format (shorts, square, landscape, etc.)
- `--template, -t`: Render template (shorts_fit, shorts_blur, square)
- `--captions, -c`: Generate auto-captions
- `--caption-style`: Caption preset (tiktok, hormozi, documentary, gaming, podcast)
- `--karaoke`: Enable karaoke-style highlighting
- `--verbose, -v`: Verbose output

### Format Management

```bash
# List all available formats
python main.py formats list

# Output:
# Name              Resolution    Aspect Ratio  Type
# shorts            1080x1920     9:16          Vertical
# square            1080x1080     1:1           Square
# landscape         1920x1080     16:9          Horizontal
# tiktok            1080x1920     9:16          Vertical
# instagram_reel    1080x1920     9:16          Vertical
# portrait_45       1080x1350     4:5           Vertical
```

### Template Management

```bash
# List all available templates
python main.py templates list

# Output:
# Name          Description
# shorts_fit    Fit video by width with blurred background for shorts
# shorts_blur   Center crop with blur background (legacy)
# square        Square 1:1 format for Instagram posts
```

### Caption Management

```bash
# List caption presets
python main.py captions list

# Output:
# Name          Font          Size  Style
# tiktok        Arial Black   52    Bold
# hormozi       Impact        60    Bold
# documentary   Helvetica     44    Regular
# gaming        Arial Black   56    Bold
# podcast       Open Sans     48    Bold
# minimal       Arial         42    Regular
```

### Transcription

```bash
# Transcribe with word-level timestamps
python main.py transcribe run video.mp4 \
    --words \
    --output words.json

# Standard transcription
python main.py transcribe run video.mp4 \
    --output transcript.txt
```

---

## Architecture

YT-Clipper uses a **service-oriented architecture** designed for scalability and future FastAPI migration.

```
app/
├── cli/                    # Typer CLI commands (thin orchestration layer)
├── core/                   # Exceptions, enums, base classes
├── config/                 # Pydantic settings with .env support
├── schemas/                # Pydantic domain models
├── services/               # Business logic services
│   ├── youtube/           # yt-dlp abstraction
│   ├── transcript/        # Whisper + word timestamps
│   ├── ai/                # 9router AI client + prompts
│   ├── ffmpeg/            # Video processing
│   ├── subtitles/         # SRT/ASS generation
│   ├── scoring/           # Weighted clip ranking
│   ├── reframing/         # Vertical conversion (legacy)
│   ├── export/            # File organization
│   ├── formats/           # Output format registry (Phase 2)
│   ├── composition/       # Layout planning (Phase 2)
│   ├── templates/         # Render templates (Phase 2)
│   ├── renderer/          # FFmpeg graph builder (Phase 2)
│   └── captions/          # Auto caption system (Phase 2)
├── workflows/              # Orchestrated pipelines
├── infrastructure/         # Logging, storage, subprocess, cache
└── utils/                  # Shared utilities
```

### Design Principles

1. **CLI is thin** — All logic lives in services
2. **Services are reusable** — Can be called from CLI, API, or workers
3. **Typed everywhere** — Pydantic models for all data
4. **Dependency injection ready** — Easy to test and extend
5. **FastAPI-ready** — Add API routes without refactoring
6. **Composition over inheritance** — Modular, testable components

---

## Configuration

All settings in `.env`:

```bash
# AI
NINEROUTER_API_KEY=sk-your-key
NINEROUTER_MODEL=gpt-4o

# Video
OUTPUT_QUALITY=23
MAX_CLIP_DURATION=60
MIN_CLIP_DURATION=15

# Whisper
WHISPER_MODEL_SIZE=base
WHISPER_DEVICE=cpu

# Scoring
SCORING_HOOK_WEIGHT=0.30
SCORING_RETENTION_WEIGHT=0.25
SCORING_INFO_WEIGHT=0.20
SCORING_STORY_WEIGHT=0.15
SCORING_EMOTION_WEIGHT=0.10

# Phase 2 (Optional)
DEFAULT_OUTPUT_FORMAT=shorts
DEFAULT_TEMPLATE=shorts_fit
ENABLE_CAPTIONS=false
DEFAULT_CAPTION_STYLE=tiktok
```

---

## Examples

### Example 1: TikTok-Style Shorts

```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --format tiktok \
    --template shorts_fit \
    --captions \
    --caption-style tiktok \
    --karaoke \
    --max-clips 3
```

### Example 2: Instagram Square Posts

```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --format square \
    --template square \
    --captions \
    --caption-style minimal
```

### Example 3: YouTube Landscape Clips

```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --format landscape \
    --max-clips 5
```

### Example 4: Hormozi-Style Captions

```bash
python main.py clip run "https://youtube.com/watch?v=dQw4w9WgXcQ" \
    --format shorts \
    --captions \
    --caption-style hormozi \
    --karaoke
```

---

## Documentation

Comprehensive documentation is available in the `docs/` directory:

### Architecture
- [Phase 2 Overview](docs/architecture/phase2_overview.md) - System architecture and design
- [Migration Guide](docs/migration/phase1_to_phase2.md) - Upgrading from Phase 1

### Rendering
- [Composition Engine](docs/rendering/composition_engine.md) - Layout planning system
- [Render Pipeline](docs/workflows/render_pipeline.md) - Complete rendering workflow

### Captions
- [Caption Engine](docs/captions/caption_engine.md) - Auto-caption system guide

### Templates
- [Template Development](docs/templates/template_development.md) - Creating custom templates

### Formats
- [Output Formats](docs/formats/output_formats.md) - Format specifications and usage

### FFmpeg
- [Graph Builder](docs/ffmpeg/graph_builder.md) - FFmpeg abstraction layer

---

## Testing

```bash
# Run all tests
pytest tests/ -v --cov=app/

# Run specific test modules
pytest tests/test_captions.py -v
pytest tests/test_composition.py -v
pytest tests/test_templates.py -v
pytest tests/test_renderer.py -v
pytest tests/test_formats.py -v

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

---

## Docker

```bash
# Build
docker build -t yt-clipper .

# Run
docker run -it --rm \
  -v $(pwd)/exports:/app/exports \
  -v $(pwd)/.env:/app/.env \
  yt-clipper clip run "https://youtube.com/watch?v=VIDEO_ID" \
    --format shorts \
    --captions \
    --caption-style tiktok
```

---

## Roadmap

### Phase 3: Advanced Features
- Face tracking for smart crop
- Scene change detection
- Background music detection
- Multi-language captions
- Batch processing
- Real-time preview generation

### Phase 4: FastAPI Backend
- REST API endpoints
- Background job queue (Celery/RQ)
- Webhook notifications
- User authentication
- Project management API

### Phase 5: SaaS Platform
- Web dashboard
- Cloud storage integration
- Direct social media upload
- Analytics and insights
- Team collaboration

---

## Contributing

Contributions are welcome! Please read our contributing guidelines before submitting PRs.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- **9Router** - AI analysis API
- **Faster-Whisper** - Speech-to-text transcription
- **yt-dlp** - YouTube video download
- **FFmpeg** - Video processing
- **Typer** - CLI framework
- **Rich** - Terminal UI

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/yt-clipper/issues)
- **Documentation**: [docs/](docs/)
- **Examples**: [examples/](examples/)

---

**Built with production-grade architecture for scalability and maintainability.**

**Phase 2 transforms YT-Clipper into a multi-format AI content engine comparable to OpusClip, Captions.ai, and Vidyo.ai.**
