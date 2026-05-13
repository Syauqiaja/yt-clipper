# YT-Clipper Project Summary

## Overview

A production-grade AI-powered YouTube video clipper built with Python 3.12+. The system automatically generates viral short-form clips optimized for TikTok, Instagram Reels, and YouTube Shorts using semantic AI analysis.

## Architecture

### Service-Oriented Design

The project follows a **scalable service-oriented architecture** designed for future FastAPI migration:

```
CLI Layer (Thin)
    ↓
Workflow Orchestration
    ↓
Service Layer (Business Logic)
    ↓
Infrastructure Layer
```

### Directory Structure

```
app/
├── cli/                    # Typer CLI commands
├── core/                   # Exceptions, enums, base classes
├── config/                 # Pydantic settings with .env support
├── schemas/                # Pydantic domain models
├── services/               # Business logic services
│   ├── youtube/           # yt-dlp video download
│   ├── transcript/        # Whisper + subtitle parsing
│   ├── ai/                # 9router AI client + prompts
│   ├── ffmpeg/            # Video processing
│   ├── subtitles/         # SRT/ASS generation
│   ├── scoring/           # Weighted clip ranking
│   ├── reframing/         # Vertical conversion
│   └── export/            # File organization
├── workflows/              # Orchestrated pipelines
├── infrastructure/         # Logging, storage, subprocess, cache
└── utils/                  # Shared utilities
```

## Core Components

### 1. YouTube Service (`services/youtube/`)
- Downloads videos using yt-dlp
- Extracts metadata, subtitles, chapters
- Supports cookies for private videos
- Resumable downloads

### 2. Transcript Service (`services/transcript/`)
- Parses SRT/VTT subtitle files
- Transcribes audio with Faster-Whisper
- Normalizes and cleans transcript text
- Merges segments and removes filler words
- Generates semantic chunks for AI analysis

### 3. AI Analysis Service (`services/ai/`)
- 9router OpenAI-compatible API client
- Semantic clip identification prompts
- Scores clips on 6 dimensions:
  - Hook strength
  - Retention potential
  - Information density
  - Storytelling quality
  - Emotional engagement
  - Viral potential

### 4. Scoring Service (`services/scoring/`)
- Weighted clip ranking algorithm
- Configurable scoring weights
- Filters clips by minimum score
- Validates clip quality

### 5. FFmpeg Service (`services/ffmpeg/`)
- Precise clip cutting
- Audio normalization
- Silence trimming
- Fade effects
- Thumbnail generation
- Video concatenation

### 6. Subtitles Service (`services/subtitles/`)
- SRT subtitle generation
- WebVTT format support
- ASS subtitles with styling
- TikTok-style animated captions

### 7. Reframing Service (`services/reframing/`)
- Vertical 9:16 conversion
- Center crop
- Blur background fallback
- Smart crop with face tracking (planned)
- Ken Burns zoom effects

### 8. Export Service (`services/export/`)
- Organized file structure
- Metadata JSON generation
- Project summaries
- Clip artifacts management

### 9. Workflow Orchestration (`workflows/`)
- End-to-end pipeline
- Progress tracking with Rich
- Error handling and recovery
- Stage-based processing

### 10. Infrastructure Layer (`infrastructure/`)
- **Logging**: Structured logging with Rich
- **Storage**: Temp file management
- **Subprocess**: Safe command execution
- **Cache**: Video metadata caching

## Key Features

### AI Semantic Analysis

The AI doesn't just summarize—it identifies:
- Strong hooks that grab attention
- High-retention moments
- Valuable informational segments
- Emotional peaks
- Story arcs with setup/payoff
- Semantic completeness

### Weighted Scoring

```python
final_score = (
    hook_strength * 0.30 +
    retention_potential * 0.25 +
    information_density * 0.20 +
    storytelling * 0.15 +
    emotional_engagement * 0.10
)
```

Weights are configurable via `.env`.

### Production Engineering

- **Type Safety**: Pydantic models everywhere
- **Error Handling**: Structured exceptions
- **Retry Logic**: Tenacity for AI API calls
- **Logging**: Rich terminal output + structured logs
- **Configuration**: Environment-based settings
- **Testing**: Pytest test suite
- **Docker**: Containerized deployment

## CLI Commands

### Generate Clips
```bash
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID" \
  --project "my-project" \
  --max-clips 5 \
  --verbose
```

### Analyze Only
```bash
python main.py analyze run "https://youtube.com/watch?v=VIDEO_ID"
```

### Download Only
```bash
python main.py download run "https://youtube.com/watch?v=VIDEO_ID"
```

### Transcribe Only
```bash
python main.py transcribe run "https://youtube.com/watch?v=VIDEO_ID"
```

### Configuration
```bash
python main.py config show
python main.py config validate
```

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
```

## Installation

```bash
# Clone repo
git clone <repo-url>
cd yt-clipper

# Install dependencies
pip install uv
uv sync

# Configure
cp .env.example .env
# Edit .env with your API key

# Run
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID"
```

## Dependencies

- **typer**: CLI framework
- **rich**: Terminal UI
- **yt-dlp**: YouTube download
- **faster-whisper**: Transcription
- **httpx**: HTTP client
- **pydantic**: Data validation
- **tenacity**: Retry logic
- **FFmpeg**: Video processing (external)

## Testing

```bash
# Run tests
pytest tests/ -v --cov=app/

# Lint
ruff check app/ tests/

# Type check
mypy app/
```

## Docker

```bash
# Build
docker build -t yt-clipper .

# Run
docker run -it --rm \
  -v $(pwd)/exports:/app/exports \
  -v $(pwd)/.env:/app/.env \
  yt-clipper clip run "https://youtube.com/watch?v=VIDEO_ID"
```

## Future Enhancements

### Phase 2: Enhanced Processing
- Face tracking for smart crop
- Background music detection
- Scene change detection
- Multi-language support
- Batch processing

### Phase 3: FastAPI Backend
- REST API endpoints
- Background job queue (Celery/RQ)
- Webhook notifications
- User authentication
- Project management API

### Phase 4: SaaS Platform
- Web dashboard
- Cloud storage integration
- Direct social media upload
- Analytics and insights
- Team collaboration

## Design Principles

1. **CLI is thin** — All logic in services
2. **Services are reusable** — Can be called from CLI, API, or workers
3. **Typed everywhere** — Pydantic models for all data
4. **Dependency injection ready** — Easy to test and extend
5. **FastAPI-ready** — Add API routes without refactoring

## File Counts

- **42 Python files** across app/
- **8 service modules** with full implementations
- **5 test files** with unit tests
- **Comprehensive README** with examples
- **Docker support** with multi-stage build
- **Makefile** with common commands

## Status

✅ **Complete and production-ready**

All core functionality implemented:
- YouTube download ✅
- Transcript extraction ✅
- AI semantic analysis ✅
- Clip scoring ✅
- Video processing ✅
- Subtitle generation ✅
- Vertical conversion ✅
- Export organization ✅
- CLI interface ✅
- Configuration system ✅
- Infrastructure layer ✅
- Test suite ✅
- Documentation ✅

## Next Steps

1. Install dependencies: `uv sync`
2. Configure API key in `.env`
3. Validate setup: `python main.py config validate`
4. Run first clip: `python main.py clip run <youtube-url>`

---

**Built with production-grade architecture for scalability and maintainability.**
