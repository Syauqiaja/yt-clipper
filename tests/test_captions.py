"""Tests for caption system."""

import pytest

from app.services.captions.chunker import CaptionChunker
from app.services.captions.models import CaptionStyle, WordTimestamp
from app.services.captions.presets import CaptionPresets


class TestWordTimestamp:
    def test_word_timestamp_creation(self):
        """Test creating word timestamp."""
        word = WordTimestamp(
            word="hello",
            start=1.0,
            end=1.5,
            confidence=0.95,
        )
        
        assert word.word == "hello"
        assert word.start == 1.0
        assert word.end == 1.5
        assert word.confidence == 0.95
    
    def test_word_duration(self):
        """Test word duration calculation."""
        word = WordTimestamp(
            word="test",
            start=2.0,
            end=2.8,
        )
        
        assert word.duration == pytest.approx(0.8)


class TestCaptionChunker:
    @pytest.fixture
    def chunker(self):
        """Create caption chunker."""
        return CaptionChunker(
            max_words_per_chunk=5,
            max_duration=3.0,
            min_pause_duration=0.3,
        )
    
    @pytest.fixture
    def sample_words(self):
        """Create sample word timestamps."""
        return [
            WordTimestamp(word="This", start=0.0, end=0.2),
            WordTimestamp(word="is", start=0.2, end=0.4),
            WordTimestamp(word="a", start=0.4, end=0.5),
            WordTimestamp(word="test", start=0.5, end=0.8),
            WordTimestamp(word="sentence.", start=0.8, end=1.2),
            WordTimestamp(word="Another", start=1.5, end=1.9),
            WordTimestamp(word="sentence", start=1.9, end=2.3),
            WordTimestamp(word="here.", start=2.3, end=2.6),
        ]
    
    def test_basic_chunking(self, chunker, sample_words):
        """Test basic word chunking."""
        chunks = chunker.chunk_words(sample_words)
        
        assert len(chunks) > 0
        assert all(chunk.word_count <= 5 for chunk in chunks)
        assert all(chunk.duration <= 3.0 for chunk in chunks)
    
    def test_chunk_word_limit(self, chunker):
        """Test chunking respects word limit."""
        words = [
            WordTimestamp(word=f"word{i}", start=i*0.2, end=(i+1)*0.2)
            for i in range(10)
        ]
        
        chunks = chunker.chunk_words(words)
        
        assert all(chunk.word_count <= 5 for chunk in chunks)
    
    def test_chunk_duration_limit(self, chunker):
        """Test chunking respects duration limit."""
        words = [
            WordTimestamp(word=f"word{i}", start=i*0.5, end=(i+1)*0.5)
            for i in range(10)
        ]
        
        chunks = chunker.chunk_words(words)
        
        assert all(chunk.duration <= 3.5 for chunk in chunks)
    
    def test_punctuation_break(self, chunker):
        """Test chunking breaks at punctuation."""
        words = [
            WordTimestamp(word="Hello", start=0.0, end=0.3),
            WordTimestamp(word="world.", start=0.3, end=0.7),
            WordTimestamp(word="How", start=0.8, end=1.0),
            WordTimestamp(word="are", start=1.0, end=1.2),
            WordTimestamp(word="you?", start=1.2, end=1.5),
        ]
        
        chunks = chunker.chunk_words(words)
        
        # Should break at punctuation
        assert len(chunks) >= 2
    
    def test_pause_break(self, chunker):
        """Test chunking breaks at pauses."""
        words = [
            WordTimestamp(word="First", start=0.0, end=0.3),
            WordTimestamp(word="part", start=0.3, end=0.6),
            # 0.5s pause
            WordTimestamp(word="Second", start=1.1, end=1.4),
            WordTimestamp(word="part", start=1.4, end=1.7),
        ]
        
        chunks = chunker.chunk_words(words)
        
        # Should break at pause
        assert len(chunks) == 2
    
    def test_empty_words(self, chunker):
        """Test chunking with empty word list."""
        chunks = chunker.chunk_words([])
        
        assert len(chunks) == 0


class TestCaptionStyle:
    def test_style_creation(self):
        """Test creating caption style."""
        style = CaptionStyle(
            font_name="Arial",
            font_size=48,
            primary_color="&H00FFFFFF",
            outline_color="&H00000000",
            outline_width=3,
        )
        
        assert style.font_name == "Arial"
        assert style.font_size == 48
        assert style.outline_width == 3
    
    def test_ass_style_generation(self):
        """Test ASS style string generation."""
        style = CaptionStyle(
            font_name="Arial",
            font_size=48,
            bold=True,
        )
        
        ass_style = style.to_ass_style("TestStyle")
        
        assert "TestStyle" in ass_style
        assert "Arial" in ass_style
        assert "48" in ass_style


class TestCaptionPresets:
    def test_tiktok_preset(self):
        """Test TikTok caption preset."""
        style = CaptionPresets.tiktok()
        
        assert style.font_name == "Arial Black"
        assert style.font_size == 52
        assert style.bold is True
    
    def test_hormozi_preset(self):
        """Test Hormozi caption preset."""
        style = CaptionPresets.hormozi()
        
        assert style.font_name == "Impact"
        assert style.font_size == 60
        assert style.primary_color == "&H0000FFFF"
    
    def test_documentary_preset(self):
        """Test documentary caption preset."""
        style = CaptionPresets.documentary()
        
        assert style.font_name == "Helvetica"
        assert style.bold is False
    
    def test_list_presets(self):
        """Test listing all presets."""
        presets = CaptionPresets.list_presets()
        
        assert "tiktok" in presets
        assert "hormozi" in presets
        assert "documentary" in presets
        assert len(presets) >= 3
    
    def test_get_preset(self):
        """Test getting preset by name."""
        style = CaptionPresets.get_preset("tiktok")
        
        assert isinstance(style, CaptionStyle)
        assert style.font_name == "Arial Black"
    
    def test_get_invalid_preset(self):
        """Test getting invalid preset."""
        with pytest.raises(ValueError, match="Preset 'invalid' not found"):
            CaptionPresets.get_preset("invalid")
