#!/bin/bash
# Simple FFmpeg subtitle syntax test script
# This tests different subtitle filter syntaxes to find which one works

set -e

echo "================================================================================"
echo "Phase 2 FFmpeg Subtitle Syntax Test"
echo "================================================================================"
echo ""

# Create test directory
TEST_DIR="temp/ffmpeg_test"
mkdir -p "$TEST_DIR"

echo "Step 1: Creating test video..."
ffmpeg -f lavfi -i testsrc=duration=5:size=1920x1080:rate=25 \
       -f lavfi -i sine=frequency=1000:duration=5 \
       -c:v libx264 -preset ultrafast -c:a aac \
       -y "$TEST_DIR/test_input.mp4" 2>&1 | grep -E "(Duration|Output)" || true

echo "✓ Test video created"
echo ""

echo "Step 2: Creating test ASS subtitle file..."
cat > "$TEST_DIR/test_captions.ass" << 'EOF'
[Script Info]
Title: Test Captions
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1080
PlayResY: 1920
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,48,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,3,2,2,50,50,50,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:00.00,0:00:02.00,Default,,0,0,0,,Test Caption 1
Dialogue: 0,0:00:02.00,0:00:04.00,Default,,0,0,0,,Test Caption 2
EOF

echo "✓ Test captions created"
echo ""

echo "Step 3: Testing composition without subtitles..."
ffmpeg -i "$TEST_DIR/test_input.mp4" \
  -filter_complex "[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15[bg];[0:v]scale=1080:607:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=0:656[out]" \
  -map "[out]" -map "0:a?" \
  -c:v libx264 -crf 23 -preset ultrafast -c:a aac -b:a 128k \
  -y "$TEST_DIR/output_no_subs.mp4" 2>&1 | grep -E "(Duration|Output|error|Error)" || true

if [ -f "$TEST_DIR/output_no_subs.mp4" ]; then
    echo "✓ Composition without subtitles WORKS"
else
    echo "✗ Composition without subtitles FAILED"
    exit 1
fi
echo ""

echo "Step 4: Testing different subtitle syntaxes..."
echo ""

# Array of subtitle filter syntaxes to test
declare -a SYNTAXES=(
    "subtitles=$TEST_DIR/test_captions.ass"
    "subtitles='$TEST_DIR/test_captions.ass'"
    "subtitles=filename=$TEST_DIR/test_captions.ass"
    "subtitles=filename='$TEST_DIR/test_captions.ass'"
    "ass=$TEST_DIR/test_captions.ass"
    "ass='$TEST_DIR/test_captions.ass'"
)

WORKING_SYNTAX=""

for i in "${!SYNTAXES[@]}"; do
    SYNTAX="${SYNTAXES[$i]}"
    NUM=$((i + 1))
    
    echo "Test $NUM: $SYNTAX"
    
    FILTER="[0:v]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=15[bg];[0:v]scale=1080:607:force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=0:656[out];[out]${SYNTAX}[final]"
    
    if ffmpeg -i "$TEST_DIR/test_input.mp4" \
        -filter_complex "$FILTER" \
        -map "[final]" -map "0:a?" \
        -c:v libx264 -crf 23 -preset ultrafast -c:a aac -b:a 128k \
        -y "$TEST_DIR/output_syntax${NUM}.mp4" 2>&1 | grep -q "error\|Error"; then
        echo "  ✗ Syntax $NUM FAILED"
    else
        if [ -f "$TEST_DIR/output_syntax${NUM}.mp4" ]; then
            echo "  ✓ Syntax $NUM WORKS!"
            WORKING_SYNTAX="$SYNTAX"
            break
        else
            echo "  ✗ Syntax $NUM FAILED (no output)"
        fi
    fi
    echo ""
done

echo ""
echo "================================================================================"
echo "Test Results"
echo "================================================================================"
echo ""

if [ -n "$WORKING_SYNTAX" ]; then
    echo "✓ FOUND WORKING SYNTAX:"
    echo ""
    echo "  $WORKING_SYNTAX"
    echo ""
    echo "Update app/services/renderer/service.py line 71-72 with:"
    echo ""
    echo "  filter_complex += f\";[out]${WORKING_SYNTAX}[final]\""
    echo ""
    echo "Replace 'test_captions.ass' with '{subtitle_path}' in the actual code."
else
    echo "✗ NO WORKING SYNTAX FOUND"
    echo ""
    echo "All tested syntaxes failed. This might be an FFmpeg version issue."
    echo "Try updating FFmpeg or using a different subtitle format."
fi

echo ""
echo "Test files location: $TEST_DIR"
echo ""
echo "================================================================================"
