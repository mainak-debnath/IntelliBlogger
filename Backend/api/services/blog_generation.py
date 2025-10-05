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

    def from_transcript(self, transcription: str, tone: str, length: str) -> str:
        length_map = {
            "short": "approximately 300 words",
            "medium": "approximately 600 words",
            "long": "over 1000 words",
        }
        target_length = length_map.get(length, "approximately 600 words")
        tone_instructions = {
            "professional": "a formal, professional, and informative tone. Use clear and structured language.",
            "casual": "a casual, friendly, and engaging tone. Feel free to use contractions and a conversational style.",
            "witty": "a witty, humorous, and clever tone. Use clever wordplay and lighthearted humor where appropriate.",
            "technical": "a technical, detailed, and precise tone. Focus on accuracy and provide in-depth explanations.",
        }
        target_tone = tone_instructions.get(tone, "a professional tone")
        prompt = (
            "Based on the following transcript from a YouTube video, write a comprehensive "
            "blog article. Write it based on the transcript, but do not make it sound like "
            "a YouTube video. Make it read as a polished, structured blog article with an "
            "engaging intro, clear sections, and a concise conclusion.\n\n"
            f"Transcript:\n{transcription}\n\nArticle:"
        )
        # response = self.model.generate_content(prompt)
        # html = markdown.markdown(response.text or "")
        html = f"<h1>Generated Blog Post</h1><p>This is a sample blog post generated with a <strong>{tone}</strong> tone and targeting a <strong>{length}</strong> length. The AI would process the transcript and generate the full article here.</p>"
        if not html:
            raise RuntimeError("Failed to generate blog content from transcript.")
        return html
