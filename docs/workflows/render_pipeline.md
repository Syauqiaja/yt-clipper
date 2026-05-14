# Render Pipeline

## Overview

The render pipeline orchestrates the complete flow from video download to final export, integrating all Phase 2 systems.

## Complete Pipeline Flow

```
1. Download
   ↓
2. Transcribe (with word timestamps)
   ↓
3. AI Analysis
   ↓
4. Clip Selection
   ↓
5. Format Selection
   ↓
6. Template Selection
   ↓
7. Composition Planning
   ↓
8. Caption Generation (optional)
   ↓
9. FFmpeg Graph Build
   ↓
10. Render Execution
    ↓
11. Export
```

## Stage-by-Stage Breakdown

### Stage 1: Download

```python
from app.services.youtube import YouTubeService

yt_service = YouTubeService()
download_result = yt_service.download_video(url)

# Result contains:
# - video_path
# - audio_path
# - metadata (title, duration, etc.)
# - subtitle_path (if available)
```

### Stage 2: Transcribe

```python
from app.services.transcript import TranscriptService

transcript_service = TranscriptService()

# Option A: Standard transcript
transcript = transcript_service.transcribe_with_whisper(
    audio_path=download_result.audio_path
)

# Option B: Word-level timestamps (for captions)
words = transcript_service.transcribe_with_word_timestamps(
    audio_path=download_result.audio_path
)
```

### Stage 3: AI Analysis

```python
from app.services.ai import AIAnalysisService

ai_service = AIAnalysisService()
clips = ai_service.analyze_for_clips(
    video_metadata=download_result.metadata,
    transcript=transcript,
    max_clips=5,
)
```

### Stage 4: Clip Selection

```python
from app.services.scoring import ScoringService

scoring_service = ScoringService()
ranked_clips = scoring_service.rank_clips(clips)
top_clips = ranked_clips[:5]
```

### Stage 5: Format Selection

```python
from app.services.formats import FormatRegistry

output_format = FormatRegistry.get("shorts")
```

### Stage 6: Template Selection

```python
from app.services.templates import TemplateRegistry

template = TemplateRegistry.get("shorts_fit")
```

### Stage 7: Composition Planning

```python
from app.services.ffmpeg import FFmpegService

ffmpeg_service = FFmpegService()
video_info = ffmpeg_service.get_video_info(download_result.video_path)

video_width = video_info["streams"][0]["width"]
video_height = video_info["streams"][0]["height"]

composition_plan = template.generate_composition(
    video_width=video_width,
    video_height=video_height,
    output_format=output_format,
)
```

### Stage 8: Caption Generation (Optional)

```python
from app.services.captions import CaptionService, CaptionPresets

caption_service = CaptionService(
    style=CaptionPresets.tiktok(),
    max_words_per_chunk=5,
)

# Filter words for clip timeframe
clip_words = [
    w for w in words
    if clip.start_time <= w.start <= clip.end_time
]

# Adjust timestamps relative to clip start
for word in clip_words:
    word.start -= clip.start_time
    word.end -= clip.start_time

ass_path = caption_service.generate_captions(
    words=clip_words,
    output_path="captions.ass",
    video_width=output_format.width,
    video_height=output_format.height,
    karaoke=True,
)
```

### Stage 9: FFmpeg Graph Build

```python
from app.services.renderer import FFmpegGraphBuilder

builder = FFmpegGraphBuilder()
filter_complex = builder.build_composition_graph(composition_plan)

if ass_path:
    filter_complex += f";[out]ass={ass_path}[final]"
    map_label = "[final]"
else:
    map_label = "[out]"
```

### Stage 10: Render Execution

```python
from app.services.renderer import RenderService

renderer = RenderService()
rendered_path = renderer.render_composition(
    input_path=clip_video_path,
    output_path=output_path,
    plan=composition_plan,
    subtitle_path=ass_path,
)
```

### Stage 11: Export

```python
from app.services.export import ExportService

export_service = ExportService()
export_result = export_service.export_clip(
    clip=clip,
    video_path=rendered_path,
    subtitle_path=ass_path,
    project_name="my_project",
)
```

## Complete Example

### Basic Rendering

```python
from app.services.youtube import YouTubeService
from app.services.transcript import TranscriptService
from app.services.ffmpeg import FFmpegService
from app.services.formats import FormatRegistry
from app.services.templates import TemplateRegistry
from app.services.renderer import RenderService

# 1. Download
yt_service = YouTubeService()
download = yt_service.download_video("https://youtube.com/watch?v=...")

# 2. Get video info
ffmpeg = FFmpegService()
video_info = ffmpeg.get_video_info(download.video_path)
video_width = video_info["streams"][0]["width"]
video_height = video_info["streams"][0]["height"]

# 3. Select format and template
output_format = FormatRegistry.get("shorts")
template = TemplateRegistry.get("shorts_fit")

# 4. Generate composition
plan = template.generate_composition(
    video_width=video_width,
    video_height=video_height,
    output_format=output_format,
)

# 5. Render
renderer = RenderService()
output = renderer.render_composition(
    input_path=download.video_path,
    output_path="output.mp4",
    plan=plan,
)
```

### With Captions

```python
from app.services.captions import CaptionService, CaptionPresets

# 1-4: Same as above

# 5. Transcribe with word timestamps
transcript_service = TranscriptService()
words = transcript_service.transcribe_with_word_timestamps(
    download.audio_path
)

# 6. Generate captions
caption_service = CaptionService(
    style=CaptionPresets.tiktok(),
)

ass_path = caption_service.generate_captions(
    words=words,
    output_path="captions.ass",
    video_width=output_format.width,
    video_height=output_format.height,
    karaoke=True,
)

# 7. Render with captions
output = renderer.render_composition(
    input_path=download.video_path,
    output_path="output.mp4",
    plan=plan,
    subtitle_path=ass_path,
)
```

### Full Workflow with AI

```python
from app.workflows.clip_workflow import ClipWorkflow

workflow = ClipWorkflow()
result = workflow.run(
    url="https://youtube.com/watch?v=...",
    project_name="my_project",
    max_clips=5,
    output_format="shorts",
    template="shorts_fit",
    captions=True,
    caption_style="tiktok",
    karaoke=True,
)

# Result contains:
# - video_metadata
# - transcript
# - clips (ranked)
# - exports (with paths)
# - processing_time
```

## Pipeline Optimization

### Parallel Processing

```python
import concurrent.futures

def process_clip(clip, download, format, template):
    # Process single clip
    pass

with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(process_clip, clip, download, format, template)
        for clip in clips
    ]
    results = [f.result() for f in futures]
```

### Caching

```python
# Cache composition plans
cache_key = f"{video_width}x{video_height}_{format.name}_{template.name}"
plan = cache.get(cache_key)
if not plan:
    plan = template.generate_composition(...)
    cache.set(cache_key, plan)
```

### Incremental Processing

```python
# Save intermediate results
transcript_path = temp_dir / "transcript.json"
if transcript_path.exists():
    transcript = Transcript.parse_file(transcript_path)
else:
    transcript = transcript_service.transcribe_with_whisper(...)
    transcript_path.write_text(transcript.json())
```

## Error Handling

### Retry Logic

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10)
)
def render_with_retry(input_path, output_path, plan):
    return renderer.render_composition(input_path, output_path, plan)
```

### Graceful Degradation

```python
try:
    # Try with captions
    output = renderer.render_composition(
        input_path=input_path,
        output_path=output_path,
        plan=plan,
        subtitle_path=ass_path,
    )
except FFmpegError:
    # Fall back to no captions
    logger.warning("Caption rendering failed, rendering without captions")
    output = renderer.render_composition(
        input_path=input_path,
        output_path=output_path,
        plan=plan,
    )
```

### Cleanup

```python
import tempfile
from pathlib import Path

temp_dir = Path(tempfile.mkdtemp())

try:
    # Processing...
    pass
finally:
    # Cleanup temp files
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
```

## Performance Metrics

### Typical Processing Times

| Stage | Duration | Notes |
|-------|----------|-------|
| Download | 30-120s | Depends on video length |
| Transcribe | 10-30s | Depends on audio length |
| AI Analysis | 5-15s | Depends on transcript length |
| Composition Planning | <1ms | Pure Python calculation |
| Caption Generation | <1s | For typical video |
| FFmpeg Rendering | 10-60s | Depends on video length |
| Export | <1s | File operations |

### Total Pipeline Time

- **Short video (30s)**: ~1-2 minutes
- **Medium video (5min)**: ~3-5 minutes
- **Long video (30min)**: ~10-20 minutes

## Monitoring

### Progress Tracking

```python
from rich.progress import Progress

with Progress() as progress:
    task = progress.add_task("Processing...", total=100)
    
    # Download (20%)
    download = yt_service.download_video(url)
    progress.update(task, advance=20)
    
    # Transcribe (30%)
    transcript = transcript_service.transcribe_with_whisper(...)
    progress.update(task, advance=30)
    
    # AI Analysis (20%)
    clips = ai_service.analyze_for_clips(...)
    progress.update(task, advance=20)
    
    # Render (30%)
    output = renderer.render_composition(...)
    progress.update(task, advance=30)
```

### Logging

```python
from app.infrastructure.logging import get_logger

logger = get_logger("pipeline")

logger.info("Starting pipeline", extra={
    "url": url,
    "format": format_name,
    "template": template_name,
})

logger.info("Download complete", extra={
    "video_path": str(download.video_path),
    "duration": download.metadata.duration,
})

logger.info("Rendering complete", extra={
    "output_path": str(output_path),
    "processing_time": processing_time,
})
```

## Troubleshooting

### Pipeline Hangs

**Cause**: FFmpeg process stuck

**Solution**: Add timeout
```python
result = runner.run(cmd, timeout=300)  # 5 minute timeout
```

### Out of Memory

**Cause**: Processing large video

**Solution**: Process in chunks or reduce quality
```python
# Reduce quality
plan.metadata["quality"] = 28  # Lower quality = less memory
```

### Slow Transcription

**Cause**: Large Whisper model on CPU

**Solution**: Use smaller model or GPU
```python
# In .env
WHISPER_MODEL_SIZE=base  # Instead of large
WHISPER_DEVICE=cuda      # If GPU available
```

## Best Practices

### 1. Validate Inputs

```python
assert Path(video_path).exists()
assert video_width > 0 and video_height > 0
assert output_format in FormatRegistry.list_formats()
```

### 2. Use Workflows

Use `ClipWorkflow` instead of manually orchestrating stages:

```python
workflow = ClipWorkflow()
result = workflow.run(...)
```

### 3. Save Intermediate Results

Save transcripts, composition plans, and captions for reuse:

```python
transcript_path.write_text(transcript.json())
plan_path.write_text(plan.json())
```

### 4. Monitor Resource Usage

```python
import psutil

memory_percent = psutil.virtual_memory().percent
if memory_percent > 80:
    logger.warning(f"High memory usage: {memory_percent}%")
```

### 5. Test Each Stage

Test stages independently before running full pipeline:

```python
# Test composition planning
plan = template.generate_composition(...)
assert plan.canvas_width == output_format.width

# Test caption generation
chunks = chunker.chunk_words(words)
assert len(chunks) > 0
```

## Summary

The render pipeline provides:

✅ End-to-end video processing  
✅ Modular stage architecture  
✅ Error handling and retry logic  
✅ Progress tracking  
✅ Performance optimization  
✅ Extensible workflow system  

Use the pipeline to transform raw YouTube videos into production-ready short-form content with minimal manual intervention.
