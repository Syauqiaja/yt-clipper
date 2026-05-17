# Metadata Generation Feature

## Overview
Added automatic generation of bilingual titles and descriptions for exported clips using LLM.

## Changes Made

### 1. Schema Updates (`app/schemas/models.py`)
- Added fields to `ClipCandidate`:
  - `title_id`: Indonesian title
  - `title_en`: English title
  - `description_id`: Indonesian description with hashtags/emojis
  - `description_en`: English description with hashtags/emojis

### 2. AI Service Enhancement (`app/services/ai/`)
- Created `metadata_prompts.py` with prompts for generating viral titles/descriptions
- Added `generate_clip_metadata()` method to `AIAnalysisService`
- Batch processes all clips to generate bilingual metadata
- Extracts relevant transcript for each clip timeframe

### 3. Export Service Updates (`app/services/export/service.py`)
- Modified `export_clip()` and `export_all_clips()` to accept `verbose` parameter
- Updated `_save_clip_metadata()` to:
  - Always save: `title_id`, `title_en`, `description_id`, `description_en`
  - Only save detailed fields when `--verbose` flag is used:
    - Original title, hook, summary
    - Timestamps, duration, rank
    - Detailed scores breakdown

### 4. Workflow Integration (`app/workflows/clip_workflow.py`)
- Added `verbose` parameter to `run()` method
- Integrated metadata generation step after clip analysis
- Passes `verbose` flag through to export service

### 5. CLI Updates (`app/cli/commands.py`)
- Modified `clip_run()` to pass `verbose` flag to workflow
- Updated `_display_results()` to show:
  - Simple output (default): English title and path only
  - Verbose output (`--verbose`): Full details including scores

## Usage

### Default (Minimal Output)
```bash
python main.py clip run <youtube-url>
```
Output shows only:
- English title
- Video path

Metadata JSON contains only:
- `title_id`, `title_en`
- `description_id`, `description_en`
- File paths
- Export timestamp

### Verbose Mode
```bash
python main.py clip run <youtube-url> --verbose
```
Output shows:
- Full clip analysis table
- All scores and details

Metadata JSON contains everything:
- All fields from default mode
- Plus: original title, hook, summary, timestamps, scores

## Benefits
1. Clean, minimal output by default
2. Bilingual content ready for social media
3. Viral-optimized titles and descriptions
4. Detailed analysis available when needed
5. Metadata stored in organized JSON files
