from __future__ import annotations

import os
import subprocess

# import sys
import uuid
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings


class YouTubeUrl:
    """Normalizes YouTube URLs to https://www.youtube.com/watch?v=<id>."""

    @staticmethod
    def normalize(link: str) -> str:
        parsed = urlparse(link)
        host = parsed.netloc.lower()

        if "youtu.be" in host:
            video_id = parsed.path.lstrip("/")
            return f"https://www.youtube.com/watch?v={video_id}"

        if "youtube.com" in host:
            query = parse_qs(parsed.query)
            if "v" in query:
                return f"https://www.youtube.com/watch?v={query['v'][0]}"

        return link


@dataclass
class YouTubeMetadata:
    title: str


class YouTubeMetadataFetcher:
    """Fetches video metadata via YouTube oEmbed (no API key required)."""

    OEMBED_URL = "https://www.youtube.com/oembed"

    def get_title(self, link: str) -> YouTubeMetadata:
        url = YouTubeUrl.normalize(link)
        resp = requests.get(
            self.OEMBED_URL, params={"url": url, "format": "json"}, timeout=20
        )
        resp.raise_for_status()
        data = resp.json()
        return YouTubeMetadata(title=data.get("title", "Unknown Title"))


class AudioDownloadError(RuntimeError):
    pass


class YouTubeAudioDownloader:
    """Downloads audio with yt-dlp as MP3 into MEDIA_ROOT and returns the file path."""

    def __init__(self, media_root: Optional[str] = None):
        self.media_root = media_root or settings.MEDIA_ROOT

    def download_mp3(self, link: str) -> str:
        os.makedirs(self.media_root, exist_ok=True)
        output_file = os.path.join(self.media_root, f"{uuid.uuid4().hex}.mp3")
        try:
            # -x extract audio; --audio-format mp3 ensures MP3 output
            # -o <path> to write exactly to output_file
            subprocess.run(
                [
                    "yt-dlp",
                    "-x",
                    "--audio-format",
                    "mp3",
                    "--ffmpeg-location",
                    "C:/ffmpeg/bin",
                    "-o",
                    output_file,
                    YouTubeUrl.normalize(link),
                ],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except subprocess.CalledProcessError as e:
            print(f"yt-dlp error: {e.stderr}")
            raise AudioDownloadError(
                f"yt-dlp failed (code {e.returncode}): {e.stderr[:400]}"
            )

        if not os.path.exists(output_file):
            raise AudioDownloadError("Audio file was not created by yt-dlp.")
        return output_file
