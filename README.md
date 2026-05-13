# YT-Clipper

**AI-powered YouTube video clipper** — Automatically generate viral short-form clips optimized for TikTok, Instagram Reels, and YouTube Shorts.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## Features

- **AI Semantic Analysis**: Identifies high-retention moments, strong hooks, and valuable content segments
- **Automated Clip Generation**: Generates multiple short-form clips from a single YouTube video
- **Vertical Video Conversion**: Converts clips to 9:16 format optimized for mobile platforms
- **Subtitle Generation**: Creates SRT/ASS subtitles with TikTok-style formatting
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
# Generate clips from a YouTube video
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID"

# Analyze video without rendering
python main.py analyze run "https://youtube.com/watch?v=VIDEO_ID"

# Download video only
python main.py download run "https://youtube.com/watch?v=VIDEO_ID"

# Transcribe video
python main.py transcribe run "https://youtube.com/watch?v=VIDEO_ID"

# Show configuration
python main.py config show

# Validate setup
python main.py config validate
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

### Design Principles

1. **CLI is thin** — All logic lives in services
2. **Services are reusable** — Can be called from CLI, API, or workers
3. **Typed everywhere** — Pydantic models for all data
4. **Dependency injection ready** — Easy to test and extend
5. **FastAPI-ready** — Add API routes without refactoring services

---

## How It Works

### 1. Download & Extract

- Downloads video using `yt-dlp`
- Extracts metadata, subtitles, and audio
- Supports cookies for private videos

### 2. Transcription

- Uses existing YouTube subtitles if available
- Falls back to Faster-Whisper for transcription
- Normalizes and cleans transcript text

### 3. AI Semantic Analysis

The AI analyzes the transcript and identifies clips based on:

- **Hook Strength**: Does it grab attention immediately?
- **Retention Potential**: Will viewers watch until the end?
- **Information Density**: How much value is packed in?
- **Storytelling**: Is there a narrative arc?
- **Emotional Engagement**: Does it evoke emotion?
- **Viral Potential**: Would people share this?

### 4. Scoring & Ranking

Clips are scored using weighted criteria:

```python
final_score = (
    hook_strength * 0.30 +
    retention_potential * 0.25 +
    information_density * 0.20 +
    storytelling * 0.15 +
    emotional_engagement * 0.10
)
```

### 5. Video Processing

- Cuts clips at precise timestamps
- Converts to vertical 9:16 format
- Generates subtitles
- Creates thumbnails
- Applies audio normalization

### 6. Export

Organizes exports into structured directories:

```
exports/
└── project_name/
    ├── clips/
    ├── subtitles/
    ├── thumbnails/
    └── metadata/
```

---

## Configuration

All settings are configurable via `.env` file:

```bash
# AI Configuration
NINEROUTER_API_KEY=sk-your-key-here
NINEROUTER_BASE_URL=https://api.9router.com/v1
NINEROUTER_MODEL=gpt-4o

# Video Settings
OUTPUT_QUALITY=23              # CRF (lower = better)
MAX_CLIP_DURATION=60           # seconds
MIN_CLIP_DURATION=15           # seconds

# Whisper
WHISPER_MODEL_SIZE=base        # tiny, base, small, medium, large-v3
WHISPER_DEVICE=cpu             # cpu or cuda

# Scoring Weights (must sum to 1.0)
SCORING_HOOK_WEIGHT=0.30
SCORING_RETENTION_WEIGHT=0.25
SCORING_INFO_WEIGHT=0.20
SCORING_STORY_WEIGHT=0.15
SCORING_EMOTION_WEIGHT=0.10

# Paths
EXPORT_DIR=exports
TEMP_DIR=temp

# Debug
DEBUG=false
LOG_LEVEL=INFO
```

---

## CLI Commands

### `clip run`

Generate clips from a YouTube video.

```bash
python main.py clip run "https://youtube.com/watch?v=VIDEO_ID" \
  --project "my-project" \
  --max-clips 5 \
  --verbose
```

### `analyze run`

Analyze video and show clip opportunities without rendering.

```bash
python main.py analyze run "https://youtube.com/watch?v=VIDEO_ID" \
  --max-clips 10
```

### `download run`

Download video only.

```bash
python main.py download run "https://youtube.com/watch?v=VIDEO_ID" \
  --output ./downloads
```

### `transcribe run`

Transcribe video to text.

```bash
python main.py transcribe run "https://youtube.com/watch?v=VIDEO_ID" \
  --whisper
```

### `config show`

Display current configuration.

```bash
python main.py config show
```

### `config validate`

Validate configuration and dependencies.

```bash
python main.py config validate
```

---

## Development

### Setup Development Environment

```bash
# Install dev dependencies
make dev

# Run tests
make test

# Lint code
make lint

# Format code
make format

# Type check
make typecheck
```

### Project Structure

```bash
# Create project structure
make scaffold

# Clean temp files
make clean

# Setup pre-commit hooks
make pre-commit
```

### Running Tests

```bash
pytest tests/ -v --cov=app/
```

---

## Docker

### Build Image

```bash
docker build -t yt-clipper .
```

### Run Container

```bash
docker run -it --rm \
  -v $(pwd)/exports:/app/exports \
  -v $(pwd)/.env:/app/.env \
  yt-clipper clip run "https://youtube.com/watch?v=VIDEO_ID"
```

---

## Roadmap

### Phase 1: Core CLI (Current)
- [x] YouTube download
- [x] Transcript extraction
- [x] AI semantic analysis
- [x] Clip generation
- [x] Vertical conversion
- [x] Subtitle generation

### Phase 2: Enhanced Processing
- [ ] Face tracking for smart crop
- [ ] Background music detection
- [ ] Scene change detection
- [ ] Multi-language support
- [ ] Batch processing

### Phase 3: FastAPI Backend
- [ ] REST API endpoints
- [ ] Background job queue
- [ ] Webhook notifications
- [ ] User authentication
- [ ] Project management

### Phase 4: SaaS Platform
- [ ] Web dashboard
- [ ] Cloud storage integration
- [ ] Direct social media upload
- [ ] Analytics and insights
- [ ] Team collaboration

---

## Contributing

Contributions are welcome! Please follow these guidelines:

1. Fork the repository
2. Create a feature branch
3. Write tests for new features
4. Ensure all tests pass
5. Submit a pull request

---

## License

MIT License - see [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube downloading
- [Faster-Whisper](https://github.com/guillaumekln/faster-whisper) for transcription
- [FFmpeg](https://ffmpeg.org/) for video processing
- [Typer](https://typer.tiangolo.com/) for CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output

---

## Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/yt-clipper/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/yt-clipper/discussions)
- **Email**: support@example.com

---

## FAQ

### How accurate is the AI analysis?

The AI uses semantic understanding to identify high-value moments. Accuracy depends on transcript quality and video content type. Educational and storytelling content typically yields better results.

### Can I use my own AI model?

Yes! The AI client is abstracted. You can modify `app/services/ai/client.py` to use any OpenAI-compatible API.

### Does it work with private videos?

Yes, if you provide cookies. Use `yt-dlp --cookies-from-browser chrome` to extract cookies.

### Can I customize scoring weights?

Yes, adjust the `SCORING_*_WEIGHT` values in `.env`. They must sum to 1.0.

### What video formats are supported?

Any format supported by yt-dlp and FFmpeg (MP4, MKV, WebM, etc.).

### How long does processing take?

Depends on video length and hardware. A 10-minute video typically takes 2-5 minutes on modern hardware.

---

**Built with ❤️ for content creators**
