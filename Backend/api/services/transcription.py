from __future__ import annotations

import os
from typing import Optional


class TranscriptionService:
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
