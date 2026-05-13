"""Transcript service: extract, normalize, and process video transcripts."""

import re
from pathlib import Path

from app.config.settings import settings
from app.core.exceptions import TranscriptError
from app.infrastructure.logging.logger import get_logger
from app.schemas.models import Transcript, TranscriptSegment

logger = get_logger("transcript")


class TranscriptService:
    def parse_subtitle_file(self, file_path: str | Path) -> Transcript:
        """Parse a subtitle file (SRT, VTT) into structured segments."""
        file_path = Path(file_path)

        if not file_path.exists():
            raise TranscriptError(f"Subtitle file not found: {file_path}")

        content = file_path.read_text(encoding="utf-8", errors="replace")

        if file_path.suffix.lower() == ".srt":
            return self._parse_srt(content, str(file_path))
        elif file_path.suffix.lower() == ".vtt":
            return self._parse_vtt(content, str(file_path))
        else:
            return self._parse_srt(content, str(file_path))

    def _parse_srt(self, content: str, source: str) -> Transcript:
        """Parse SRT format subtitles."""
        segments = []
        blocks = content.strip().split("\n\n")

        pattern = re.compile(
            r"(\d+)\n"
            r"(\d{2}:\d{2}:\d{2}[,\.]\d{3}) --> (\d{2}:\d{2}:\d{2}[,\.]\d{3})\n"
            r"((?:.+\n?)*)"
        )

        for block in blocks:
            match = pattern.match(block.strip())
            if match:
                start = self._timestamp_to_seconds(match.group(2))
                end = self._timestamp_to_seconds(match.group(3))
                text = match.group(4).strip()
                text = re.sub(r"<[^>]+>", "", text)
                text = re.sub(r"\n", " ", text)

                if text:
                    segments.append(
                        TranscriptSegment(
                            start=start, end=end, text=text
                        )
                    )

        full_text = " ".join(s.text for s in segments)
        return Transcript(segments=segments, source="youtube", full_text=full_text)

    def _parse_vtt(self, content: str, source: str) -> Transcript:
        """Parse WebVTT format subtitles."""
        segments = []

        lines = content.split("\n")
        cue_text = []
        cue_start = None
        cue_end = None

        for line in lines:
            line = line.strip()

            if line == "WEBVTT" or line.startswith("NOTE"):
                continue

            if "-->" in line:
                if cue_start is not None and cue_text:
                    segments.append(
                        TranscriptSegment(
                            start=cue_start,
                            end=cue_end,
                            text=" ".join(cue_text),
                        )
                    )
                    cue_text = []

                parts = line.split(" --> ")
                if len(parts) >= 2:
                    cue_start = self._timestamp_to_seconds(parts[0].strip())
                    cue_end = self._timestamp_to_seconds(parts[1].split()[0].strip())

            elif line and cue_start is not None:
                cleaned = re.sub(r"<[^>]+>", "", line).strip()
                if cleaned:
                    cue_text.append(cleaned)

        if cue_start is not None and cue_text:
            segments.append(
                TranscriptSegment(
                    start=cue_start,
                    end=cue_end,
                    text=" ".join(cue_text),
                )
            )

        full_text = " ".join(s.text for s in segments)
        return Transcript(segments=segments, source="youtube", full_text=full_text)

    def _timestamp_to_seconds(self, timestamp: str) -> float:
        """Convert timestamp string to seconds."""
        timestamp = timestamp.replace(",", ".")

        parts = timestamp.split(":")
        if len(parts) == 3:
            h, m, s = parts
            return int(h) * 3600 + int(m) * 60 + float(s)
        elif len(parts) == 2:
            m, s = parts
            return int(m) * 60 + float(s)
        else:
            return float(parts[0])

    def transcribe_with_whisper(
        self, audio_path: str | Path, language: str | None = None
    ) -> Transcript:
        """Transcribe audio using Faster-Whisper."""
        logger.info(f"Transcribing audio: {audio_path}")

        try:
            from faster_whisper import WhisperModel

            model = WhisperModel(
                model_size_or_path=settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )

            segments_raw, info = model.transcribe(
                str(audio_path),
                language=language,
                beam_size=5,
                vad_filter=True,
                vad_parameters=dict(
                    min_silence_duration_ms=500,
                ),
            )

            segments = []
            for seg in segments_raw:
                segments.append(
                    TranscriptSegment(
                        start=seg.start,
                        end=seg.end,
                        text=seg.text.strip(),
                        confidence=seg.avg_logprob if hasattr(seg, "avg_logprob") else None,
                    )
                )

            full_text = " ".join(s.text for s in segments)
            detected_language = info.language if info else language

            return Transcript(
                segments=segments,
                source="whisper",
                language=detected_language,
                full_text=full_text,
            )

        except ImportError:
            raise TranscriptError(
                "faster-whisper is not installed. Install with: pip install faster-whisper"
            )
        except Exception as e:
            raise TranscriptError(f"Failed to transcribe audio: {e}")

    def normalize_transcript(self, transcript: Transcript) -> Transcript:
        """Clean and normalize transcript text."""
        cleaned_segments = []
        filler_words = {
            "um", "uh", "uhh", "umm", "ah", "er", "hmm",
            "like", "you know", "actually", "basically", "literally",
            "sort of", "kind of", "i mean",
        }

        for segment in transcript.segments:
            text = segment.text
            text = re.sub(r"\[.*?\]", "", text)
            text = re.sub(r"\(.*?\)", "", text)
            text = re.sub(r"\s+", " ", text).strip()

            words = text.lower().split()
            if len(words) <= 2 and text.lower().strip() in filler_words:
                continue

            for filler in ("you know", "i mean", "sort of", "kind of"):
                text = re.sub(rf"\b{re.escape(filler)}\b,?\s*", "", text, flags=re.IGNORECASE)

            text = text.strip()
            if text:
                cleaned_segments.append(
                    TranscriptSegment(
                        start=segment.start,
                        end=segment.end,
                        text=text,
                        confidence=segment.confidence,
                    )
                )

        full_text = " ".join(s.text for s in cleaned_segments)
        return Transcript(
            segments=cleaned_segments,
            source=transcript.source,
            language=transcript.language,
            full_text=full_text,
        )

    def merge_segments(self, transcript: Transcript, max_gap: float = 2.0) -> Transcript:
        """Merge adjacent segments with small gaps."""
        if not transcript.segments:
            return transcript

        merged = [transcript.segments[0]]

        for segment in transcript.segments[1:]:
            last = merged[-1]
            gap = segment.start - last.end

            if gap < max_gap:
                merged[-1] = TranscriptSegment(
                    start=last.start,
                    end=segment.end,
                    text=f"{last.text} {segment.text}",
                    confidence=(last.confidence + segment.confidence) / 2
                    if last.confidence and segment.confidence
                    else None,
                )
            else:
                merged.append(segment)

        full_text = " ".join(s.text for s in merged)
        return Transcript(
            segments=merged,
            source=transcript.source,
            language=transcript.language,
            full_text=full_text,
        )

    def generate_semantic_chunks(
        self,
        transcript: Transcript,
        chunk_duration: float = 30.0,
        overlap: float = 5.0,
    ) -> list[Transcript]:
        """Split transcript into semantic chunks for AI analysis."""
        if not transcript.segments:
            return []

        chunks: list[Transcript] = []
        current_texts: list[str] = []
        current_segments: list[TranscriptSegment] = []
        chunk_start = 0.0

        for segment in transcript.segments:
            current_texts.append(segment.text)
            current_segments.append(segment)

            chunk_duration_actual = segment.end - chunk_start

            if chunk_duration_actual >= chunk_duration:
                chunk = Transcript(
                    segments=current_segments,
                    source=transcript.source,
                    language=transcript.language,
                    full_text=" ".join(current_texts),
                )
                chunks.append(chunk)

                overlap_start = max(
                    0, chunk_duration_actual - overlap
                )
                current_texts = []
                current_segments = []
                for seg in reversed(transcript.segments):
                    if seg.end >= segment.end - overlap_start:
                        current_texts.insert(0, seg.text)
                        current_segments.insert(0, seg)
                        chunk_start = current_segments[0].start
                    else:
                        break

        if current_segments:
            chunk = Transcript(
                segments=current_segments,
                source=transcript.source,
                language=transcript.language,
                full_text=" ".join(current_texts),
            )
            chunks.append(chunk)

        return chunks

    def get_text_between(
        self, transcript: Transcript, start_time: float, end_time: float
    ) -> str:
        """Get transcript text between two timestamps."""
        texts = []
        for segment in transcript.segments:
            if segment.start >= start_time and segment.end <= end_time:
                texts.append(segment.text)
        return " ".join(texts)
