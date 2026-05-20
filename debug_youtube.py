#!/usr/bin/env python3
"""Debug script to test yt-dlp format selection."""

import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.youtube.service import YouTubeService
from app.config.settings import settings

print("=" * 60)
print("YouTube Service Debug")
print("=" * 60)
print()

# Create service
service = YouTubeService()

# Get options
opts = service._get_ydl_opts()

print("yt-dlp options:")
for key, value in opts.items():
    print(f"  {key}: {value}")

print()
print("=" * 60)
print("Checking format setting:")
print("=" * 60)

if "format" in opts:
    print(f"❌ Format is SET to: {opts['format']}")
    print("   This might cause issues!")
else:
    print("✅ Format is NOT set (yt-dlp will auto-select)")

print()
print("Cookies file:", settings.youtube_cookies_file)
print("Cookies exists:", Path(settings.youtube_cookies_file).exists() if settings.youtube_cookies_file else False)
