"""AI emphasis service for intelligent caption highlighting."""

from app.infrastructure.logging.logger import get_logger
from app.services.captions.models import CaptionChunk, WordTimestamp

logger = get_logger("captions.emphasis")


class EmphasisAnalyzer:
    """
    AI-powered emphasis analyzer for caption enhancement.
    
    Identifies words and phrases that should be emphasized
    based on semantic importance, emotional weight, and hooks.
    
    Future enhancement: Can integrate with LLM for advanced analysis.
    """
    
    def __init__(self):
        self.emphasis_keywords = self._load_emphasis_keywords()
    
    def _load_emphasis_keywords(self) -> set[str]:
        """
        Load keywords that typically warrant emphasis.
        
        Returns:
            Set of emphasis keywords
        """
        return {
            "amazing", "incredible", "shocking", "unbelievable",
            "never", "always", "must", "need", "important",
            "critical", "essential", "key", "secret", "truth",
            "proven", "guaranteed", "results", "breakthrough",
            "discover", "reveal", "expose", "warning", "danger",
            "urgent", "now", "today", "immediately", "fast",
            "easy", "simple", "powerful", "effective", "best",
            "worst", "first", "last", "only", "exclusive",
            "free", "bonus", "limited", "special", "new",
        }
    
    def analyze_chunks(
        self,
        chunks: list[CaptionChunk],
    ) -> list[CaptionChunk]:
        """
        Analyze chunks and mark words for emphasis.
        
        Args:
            chunks: Caption chunks
            
        Returns:
            Chunks with emphasis markers
        """
        logger.info(f"Analyzing {len(chunks)} chunks for emphasis")
        
        emphasized_chunks = []
        
        for chunk in chunks:
            emphasized_words = self._analyze_words(chunk.words)
            
            emphasized_chunk = chunk.model_copy()
            emphasized_chunk.words = emphasized_words
            
            emphasized_chunks.append(emphasized_chunk)
        
        return emphasized_chunks
    
    def _analyze_words(
        self,
        words: list[WordTimestamp],
    ) -> list[WordTimestamp]:
        """
        Analyze words and mark for emphasis.
        
        Args:
            words: Word timestamps
            
        Returns:
            Words with emphasis markers (future: add emphasis field)
        """
        emphasized = []
        
        for word in words:
            word_lower = word.word.lower().strip(".,!?;:")
            
            if word_lower in self.emphasis_keywords:
                logger.debug(f"Emphasis keyword detected: {word.word}")
            
            emphasized.append(word)
        
        return emphasized
    
    def get_emphasis_score(self, word: str) -> float:
        """
        Calculate emphasis score for a word.
        
        Args:
            word: Word text
            
        Returns:
            Emphasis score (0.0 to 1.0)
        """
        word_lower = word.lower().strip(".,!?;:")
        
        if word_lower in self.emphasis_keywords:
            return 1.0
        
        if word.isupper() and len(word) > 1:
            return 0.8
        
        if word.endswith("!"):
            return 0.7
        
        return 0.0
    
    def suggest_emphasis_words(
        self,
        chunks: list[CaptionChunk],
        max_per_chunk: int = 2,
    ) -> dict[int, list[str]]:
        """
        Suggest words to emphasize per chunk.
        
        Args:
            chunks: Caption chunks
            max_per_chunk: Maximum words to emphasize per chunk
            
        Returns:
            Dictionary mapping chunk index to emphasized words
        """
        suggestions = {}
        
        for chunk in chunks:
            emphasized_words = []
            
            for word in chunk.words:
                score = self.get_emphasis_score(word.word)
                if score > 0.5:
                    emphasized_words.append(word.word)
            
            if emphasized_words:
                suggestions[chunk.index] = emphasized_words[:max_per_chunk]
        
        return suggestions
