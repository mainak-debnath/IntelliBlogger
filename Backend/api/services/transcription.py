from __future__ import annotations

import os
from typing import Optional

from .youtube import YouTubeUrl


class AssemblyAITranscriptionService:
    def __init__(self, api_key: Optional[str] = None):
        import assemblyai as aai

        self.api_key = api_key or os.getenv("ASSEMBLY_API_KEY")
        if not self.api_key:
            raise RuntimeError("ASSEMBLY_API_KEY is not configured.")
        aai.settings.api_key = self.api_key
        self._transcriber = aai.Transcriber()

    def transcribe_file(self, audio_path: str) -> str:
        transcript = self._transcriber.transcribe(audio_path)
        if not transcript or not getattr(transcript, "text", None):
            raise RuntimeError("Failed to transcribe audio.")
        return transcript.text


class YouTubeTranscriptApiTranscriptionService:
    def transcribe_youtube(self, link: str) -> str:
        from youtube_transcript_api import YouTubeTranscriptApi

        video_id = YouTubeUrl.video_id(link)
        if not video_id:
            raise RuntimeError("Invalid YouTube link.")

        transcript = YouTubeTranscriptApi().fetch(video_id)
        text = " ".join(
            segment.text.strip()
            for segment in transcript
            if getattr(segment, "text", "").strip()
        ).strip()
        if not text:
            raise RuntimeError("Failed to fetch transcript from YouTube.")
        return text


class TranscriptionService:
    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
    ):
        self.provider = (
            provider or os.getenv("TRANSCRIPTION_PROVIDER", "assemblyai")
        ).strip().lower()
        if self.provider not in {"assemblyai", "youtube_transcript_api"}:
            raise RuntimeError(
                "TRANSCRIPTION_PROVIDER must be either 'assemblyai' or "
                "'youtube_transcript_api'."
            )
        self._assemblyai_service = (
            AssemblyAITranscriptionService(api_key=api_key)
            if self.provider == "assemblyai"
            else None
        )
        self._youtube_transcript_service = (
            YouTubeTranscriptApiTranscriptionService()
            if self.provider == "youtube_transcript_api"
            else None
        )

    def uses_direct_youtube_transcripts(self) -> bool:
        return self.provider == "youtube_transcript_api"

    def transcribe_youtube(self, link: str) -> str:
        if not self.uses_direct_youtube_transcripts():
            raise RuntimeError(
                "Direct YouTube transcription is only supported when "
                "TRANSCRIPTION_PROVIDER=youtube_transcript_api."
            )
        assert self._youtube_transcript_service is not None
        return self._youtube_transcript_service.transcribe_youtube(link)

    def transcribe_file(self, audio_path: str) -> str:
        if self._assemblyai_service is None:
            raise RuntimeError(
                "Audio-file transcription is only supported when "
                "TRANSCRIPTION_PROVIDER=assemblyai."
            )
        return self._assemblyai_service.transcribe_file(audio_path)
