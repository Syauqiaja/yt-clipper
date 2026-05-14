"""Caption chunking service for intelligent text segmentation."""

from app.infrastructure.logging.logger import get_logger
from app.services.captions.models import CaptionChunk, WordTimestamp

logger = get_logger("captions.chunker")


class CaptionChunker:
    """
    Intelligent caption chunking engine.
    
    Splits word-level timestamps into readable caption chunks
    based on timing, punctuation, and pacing rules.
    """
    
    def __init__(
        self,
        max_words_per_chunk: int = 5,
        max_duration: float = 3.0,
        min_pause_duration: float = 0.3,
    ):
        """
        Initialize chunker.
        
        Args:
            max_words_per_chunk: Maximum words per caption
            max_duration: Maximum chunk duration in seconds
            min_pause_duration: Minimum pause to trigger chunk break
        """
        self.max_words_per_chunk = max_words_per_chunk
        self.max_duration = max_duration
        self.min_pause_duration = min_pause_duration
    
    def chunk_words(self, words: list[WordTimestamp]) -> list[CaptionChunk]:
        """
        Chunk words into caption segments.
        
        Args:
            words: List of word timestamps
            
        Returns:
            List of caption chunks
        """
        if not words:
            return []
        
        logger.info(f"Chunking {len(words)} words into captions")
        
        chunks: list[CaptionChunk] = []
        current_words: list[WordTimestamp] = []
        chunk_start: float = words[0].start
        
        for i, word in enumerate(words):
            current_words.append(word)
            
            should_break = self._should_break_chunk(
                current_words=current_words,
                chunk_start=chunk_start,
                current_word=word,
                next_word=words[i + 1] if i + 1 < len(words) else None,
            )
            
            if should_break:
                chunk = self._create_chunk(current_words, len(chunks))
                chunks.append(chunk)
                
                current_words = []
                if i + 1 < len(words):
                    chunk_start = words[i + 1].start
        
        if current_words:
            chunk = self._create_chunk(current_words, len(chunks))
            chunks.append(chunk)
        
        logger.info(f"Created {len(chunks)} caption chunks")
        
        return chunks
    
    def _should_break_chunk(
        self,
        current_words: list[WordTimestamp],
        chunk_start: float,
        current_word: WordTimestamp,
        next_word: WordTimestamp | None,
    ) -> bool:
        """
        Determine if chunk should break after current word.
        
        Args:
            current_words: Words in current chunk
            chunk_start: Chunk start time
            current_word: Current word
            next_word: Next word (if any)
            
        Returns:
            True if chunk should break
        """
        if len(current_words) >= self.max_words_per_chunk:
            return True
        
        chunk_duration = current_word.end - chunk_start
        if chunk_duration >= self.max_duration:
            return True
        
        if self._is_punctuation_break(current_word.word):
            return True
        
        if next_word:
            pause = next_word.start - current_word.end
            if pause >= self.min_pause_duration:
                return True
        
        return False
    
    def _is_punctuation_break(self, word: str) -> bool:
        """
        Check if word ends with punctuation that should trigger break.
        
        Args:
            word: Word text
            
        Returns:
            True if punctuation break
        """
        break_punctuation = {'.', '!', '?', ':', ';'}
        return any(word.endswith(p) for p in break_punctuation)
    
    def _create_chunk(
        self,
        words: list[WordTimestamp],
        index: int,
    ) -> CaptionChunk:
        """
        Create caption chunk from words.
        
        Args:
            words: Words in chunk
            index: Chunk index
            
        Returns:
            CaptionChunk instance
        """
        text = " ".join(w.word for w in words)
        start = words[0].start
        end = words[-1].end
        
        return CaptionChunk(
            text=text,
            start=start,
            end=end,
            words=words,
            index=index,
        )
