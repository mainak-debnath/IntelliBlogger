from __future__ import annotations

import json
import os
import subprocess
import uuid
from dataclasses import dataclass
from typing import Optional
from urllib.parse import parse_qs, urlparse

import requests
from django.conf import settings


class YouTubeUrl:
    """Normalizes YouTube URLs to https://www.youtube.com/watch?v=<id>."""

    @staticmethod
    def video_id(link: str) -> str:
        normalized = YouTubeUrl.normalize(link)
        parsed = urlparse(normalized)
        query = parse_qs(parsed.query)
        return query.get("v", [""])[0]

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


class LocalYtDlpAudioDownloader:
    """Downloads audio with yt-dlp as MP3 into MEDIA_ROOT and returns the file path."""

    def __init__(self, media_root: Optional[str] = None):
        self.media_root = media_root or settings.MEDIA_ROOT

    def download_mp3(self, link: str) -> str:
        os.makedirs(self.media_root, exist_ok=True)
        output_file = os.path.join(self.media_root, f"{uuid.uuid4().hex}.mp3")
        ffmpeg_location = getattr(settings, "FFMPEG_LOCATION", None)
        command = [
            "yt-dlp",
            "-x",
            "--audio-format",
            "mp3",
        ]

        if ffmpeg_location:
            command.extend(["--ffmpeg-location", ffmpeg_location])

        command.extend(["-o", output_file, YouTubeUrl.normalize(link)])

        try:
            subprocess.run(
                command,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )
        except subprocess.CalledProcessError as e:
            raise AudioDownloadError(
                f"yt-dlp failed (code {e.returncode}): {e.stderr[:400]}"
            )

        if not os.path.exists(output_file):
            raise AudioDownloadError("Audio file was not created by yt-dlp.")
        return output_file


class RapidApiAudioDownloader:
    def __init__(
        self,
        media_root: Optional[str] = None,
        api_key: Optional[str] = None,
        api_host: Optional[str] = None,
        base_url: Optional[str] = None,
        download_path: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
    ):
        self.media_root = media_root or settings.MEDIA_ROOT
        self.api_key = api_key or getattr(settings, "RAPIDAPI_KEY", "")
        self.api_host = api_host or getattr(settings, "RAPIDAPI_HOST", "")
        self.base_url = (
            base_url
            or getattr(settings, "RAPIDAPI_BASE_URL", "")
            or (
                f"https://{self.api_host}"
                if (api_host or getattr(settings, "RAPIDAPI_HOST", ""))
                else ""
            )
        ).rstrip("/")
        self.download_path = download_path or getattr(
            settings, "RAPIDAPI_DOWNLOAD_PATH", "/download/mp3"
        )
        self.timeout_seconds = timeout_seconds or int(
            getattr(settings, "RAPIDAPI_TIMEOUT_SECONDS", 60)
        )

        if not self.api_key:
            raise RuntimeError("RAPIDAPI_KEY is not configured.")
        if not self.api_host:
            raise RuntimeError("RAPIDAPI_HOST is not configured.")
        if not self.base_url:
            raise RuntimeError("RAPIDAPI_BASE_URL is not configured.")

    def download_mp3(self, link: str) -> str:
        os.makedirs(self.media_root, exist_ok=True)
        normalized_link = YouTubeUrl.normalize(link)
        output_file = os.path.join(self.media_root, f"{uuid.uuid4().hex}.mp3")

        conversion_response = requests.get(
            f"{self.base_url}{self.download_path}",
            headers={
                "x-rapidapi-key": self.api_key,
                "x-rapidapi-host": self.api_host,
            },
            params={"url": normalized_link},
            timeout=self.timeout_seconds,
        )
        conversion_response.raise_for_status()

        download_url = self._extract_download_url(conversion_response)
        if not download_url:
            raise AudioDownloadError("RapidAPI response did not contain an MP3 URL.")

        download_response = requests.get(
            download_url,
            stream=True,
            timeout=self.timeout_seconds,
        )
        download_response.raise_for_status()

        with open(output_file, "wb") as audio_file:
            for chunk in download_response.iter_content(chunk_size=8192):
                if chunk:
                    audio_file.write(chunk)

        if not os.path.exists(output_file):
            raise AudioDownloadError("Audio file was not downloaded from RapidAPI.")
        return output_file

    def _extract_download_url(self, response: requests.Response) -> str:
        content_type = (response.headers.get("content-type") or "").lower()
        text = response.text.strip()

        if text.startswith("http://") or text.startswith("https://"):
            return text

        if (
            "application/json" in content_type
            or text.startswith("{")
            or text.startswith("[")
        ):
            try:
                payload = response.json()
            except json.JSONDecodeError as exc:
                raise AudioDownloadError(
                    f"RapidAPI returned invalid JSON: {text[:300]}"
                ) from exc
            print()
            return self._extract_download_url_from_payload(payload)

        raise AudioDownloadError(f"Unexpected RapidAPI response: {text[:300]}")

    def _extract_download_url_from_payload(self, payload: object) -> str:
        if isinstance(payload, dict):
            for key in ("download", "url", "response", "dlurl", "downloadUrl"):
                value = payload.get(key)
                if isinstance(value, str) and value.startswith(("http://", "https://")):
                    return value

            result = payload.get("result")
            if isinstance(result, list):
                for item in result:
                    if not isinstance(item, dict):
                        continue
                    for key in ("dlurl", "download", "url", "response"):
                        value = item.get(key)
                        if isinstance(value, str) and value.startswith(
                            ("http://", "https://")
                        ):
                            return value

        return ""


class YouTubeAudioDownloader:
    """Facade that chooses the configured audio download provider."""

    def __init__(self, media_root: Optional[str] = None):
        self.media_root = media_root or settings.MEDIA_ROOT
        provider = getattr(settings, "AUDIO_DOWNLOAD_PROVIDER", "local").strip().lower()

        if provider == "rapidapi":
            self._provider = RapidApiAudioDownloader(media_root=self.media_root)
        elif provider == "local":
            self._provider = LocalYtDlpAudioDownloader(media_root=self.media_root)
        else:
            raise RuntimeError(
                "AUDIO_DOWNLOAD_PROVIDER must be either 'local' or 'rapidapi'."
            )

    def download_mp3(self, link: str) -> str:
        return self._provider.download_mp3(link)
