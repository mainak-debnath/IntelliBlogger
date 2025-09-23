from __future__ import annotations

import os
from typing import Optional

import google.generativeai as genai
import markdown
from dotenv import load_dotenv

load_dotenv()


class BlogGenerator:
    def __init__(
        self, api_key: Optional[str] = None, model_name: str = "gemini-2.5-flash"
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY is not configured.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name)

    def from_transcript(self, transcription: str) -> str:
        prompt = (
            "Based on the following transcript from a YouTube video, write a comprehensive "
            "blog article. Write it based on the transcript, but do not make it sound like "
            "a YouTube video. Make it read as a polished, structured blog article with an "
            "engaging intro, clear sections, and a concise conclusion.\n\n"
            f"Transcript:\n{transcription}\n\nArticle:"
        )
        response = self.model.generate_content(prompt)
        html = markdown.markdown(response.text or "")
        if not html:
            raise RuntimeError("Failed to generate blog content from transcript.")
        return html
