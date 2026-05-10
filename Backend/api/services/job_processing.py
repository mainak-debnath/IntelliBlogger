from __future__ import annotations

import logging
import os

from django.core.cache import cache
from django.utils import timezone

from api.models import BlogGenerationJob

from .blog_generation import BlogGenerator
from .job_notifications import BlogGenerationJobNotifier
from .transcription import TranscriptionService
from .youtube import AudioDownloadError, YouTubeAudioDownloader, YouTubeMetadataFetcher

logger = logging.getLogger(__name__)


class BlogGenerationJobProcessor:
    def __init__(self) -> None:
        self.notifier = BlogGenerationJobNotifier()

    def process(self, job: BlogGenerationJob) -> BlogGenerationJob:
        if job.status not in {
            BlogGenerationJob.Status.QUEUED,
            BlogGenerationJob.Status.FAILED,
        }:
            return job

        audio_path = None
        job.status = BlogGenerationJob.Status.PROCESSING
        job.started_at = timezone.now()
        job.error_message = ""
        job.save(update_fields=["status", "started_at", "error_message", "updated_at"])
        self.notifier.notify(job)

        parsed_link = job.normalized_youtube_link
        video_id = parsed_link.split("v=")[-1]
        transcript_cache_key = f"youtube_transcript:{video_id}"
        blog_cache_key = (
            f"generated_blog:{job.user_id}:{video_id}:{job.tone}:{job.length}"
        )

        try:
            cached_blog = cache.get(blog_cache_key)
            if cached_blog:
                job.title = cached_blog["title"]
                job.generated_content = cached_blog["content"]
                job.status = BlogGenerationJob.Status.COMPLETED
                job.completed_at = timezone.now()
                job.save(
                    update_fields=[
                        "title",
                        "generated_content",
                        "status",
                        "completed_at",
                        "updated_at",
                    ]
                )
                self.notifier.notify(job)
                return job

            transcription = cache.get(transcript_cache_key)
            if not transcription:
                audio_path = YouTubeAudioDownloader().download_mp3(parsed_link)
                transcription = TranscriptionService().transcribe_file(audio_path)
                cache.set(transcript_cache_key, transcription, timeout=60 * 60 * 24)

            title = YouTubeMetadataFetcher().get_title(parsed_link).title
            generated_content = BlogGenerator().from_transcript(
                transcription=transcription,
                tone=job.tone,
                length=job.length,
            )

            payload = {
                "title": title,
                "content": generated_content,
                "tone": job.tone,
                "length": job.length,
            }
            cache.set(blog_cache_key, payload, timeout=60 * 60 * 24)

            job.title = title
            job.generated_content = generated_content
            job.status = BlogGenerationJob.Status.COMPLETED
            job.completed_at = timezone.now()
            job.save(
                update_fields=[
                    "title",
                    "generated_content",
                    "status",
                    "completed_at",
                    "updated_at",
                ]
            )
            self.notifier.notify(job)
            return job
        except AudioDownloadError:
            message = "Unable to download audio for this YouTube link."
            logger.warning("Job %s failed during audio download", job.id)
            job.status = BlogGenerationJob.Status.FAILED
            job.error_message = message
            job.completed_at = timezone.now()
            job.save(
                update_fields=["status", "error_message", "completed_at", "updated_at"]
            )
            self.notifier.notify(job)
            return job
        except Exception:
            logger.exception("Job %s failed during generation", job.id)
            job.status = BlogGenerationJob.Status.FAILED
            job.error_message = "Generation failed. Please try again later."
            job.completed_at = timezone.now()
            job.save(
                update_fields=["status", "error_message", "completed_at", "updated_at"]
            )
            self.notifier.notify(job)
            return job
        finally:
            if audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    logger.warning("Failed to remove temporary audio file: %s", audio_path)
