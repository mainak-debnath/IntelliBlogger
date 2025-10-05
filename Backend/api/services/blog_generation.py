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
            "You are an expert blog writer.\n\n"
            "Based on the following transcript from a YouTube video, generate a polished blog article. "
            "It should not read like a transcript or a YouTube script, but like a structured article. "
            "The blog should have:\n"
            "- An engaging introduction\n"
            "- Well-structured sections with headers\n"
            "- A concise conclusion\n\n"
            f"Please write the article in {target_length}, and {target_tone}\n\n"
            f"Transcript:\n{transcription}\n\n"
            "Blog Article:"
        )
        response = self.model.generate_content(prompt)
        html = markdown.markdown(response.text or "")
        if not html:
            raise RuntimeError("Failed to generate blog content from transcript.")
        return html
