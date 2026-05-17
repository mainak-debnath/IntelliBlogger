import tempfile
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.management import call_command
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import BlogGenerationJob, BlogPost
from api.tasks import process_blog_generation_job
from api.services.youtube import RapidApiAudioDownloader, YouTubeAudioDownloader


class BaseAuthenticatedAPITestCase(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(
            username="mainak", email="mainak@example.com", password="strongpass123"
        )
        refresh = RefreshToken.for_user(self.user)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}"
        )


class HealthCheckTests(APITestCase):
    def test_health_check_returns_ok(self):
        response = self.client.get(reverse("health"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "ok")


class SignupTests(APITestCase):
    def test_signup_creates_user_and_returns_tokens(self):
        payload = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "repeat_password": "securepass123",
        }

        response = self.client.post(reverse("signup"), payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)


class GenerateBlogTests(BaseAuthenticatedAPITestCase):
    @patch("api.views.BlogGenerator")
    @patch("api.views.YouTubeMetadataFetcher")
    @patch("api.views.TranscriptionService")
    @patch("api.views.YouTubeAudioDownloader")
    def test_generate_blog_returns_payload_and_cleans_up_audio(
        self,
        mock_downloader,
        mock_transcription_service,
        mock_metadata_fetcher,
        mock_blog_generator,
    ):
        mock_downloader.return_value.download_mp3.return_value = "temp-audio.mp3"
        mock_transcription_service.return_value.transcribe_file.return_value = (
            "sample transcript"
        )
        mock_transcription_service.return_value.uses_direct_youtube_transcripts.return_value = (
            False
        )
        mock_metadata_fetcher.return_value.get_title.return_value.title = "Demo title"
        mock_blog_generator.return_value.from_transcript.return_value = "<h1>Blog</h1>"

        with patch("api.views.os.path.exists", return_value=True), patch(
            "api.views.os.remove"
        ) as mock_remove:
            response = self.client.post(
                reverse("generate_blog"),
                {
                    "link": "https://youtu.be/abc123xyz99",
                    "tone": "professional",
                    "length": "medium",
                },
                format="json",
            )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["title"], "Demo title")
        self.assertEqual(response.data["content"], "<h1>Blog</h1>")
        mock_remove.assert_called_once_with("temp-audio.mp3")

    def test_generate_blog_rejects_invalid_tone(self):
        response = self.client.post(
            reverse("generate_blog"),
            {
                "link": "https://www.youtube.com/watch?v=abc123xyz99",
                "tone": "dramatic",
                "length": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("tone", response.data)

    @patch("api.views.settings.TRANSCRIPTION_PROVIDER", "youtube_transcript_api")
    @patch("api.views.BlogGenerator")
    @patch("api.views.YouTubeMetadataFetcher")
    @patch("api.views.TranscriptionService")
    @patch("api.views.YouTubeAudioDownloader")
    def test_generate_blog_uses_youtube_transcript_provider_without_audio_download(
        self,
        mock_downloader,
        mock_transcription_service,
        mock_metadata_fetcher,
        mock_blog_generator,
    ):
        mock_transcription_service.return_value.uses_direct_youtube_transcripts.return_value = (
            True
        )
        mock_transcription_service.return_value.transcribe_youtube.return_value = (
            "sample transcript"
        )
        mock_metadata_fetcher.return_value.get_title.return_value.title = "Demo title"
        mock_blog_generator.return_value.from_transcript.return_value = "<h1>Blog</h1>"

        response = self.client.post(
            reverse("generate_blog"),
            {
                "link": "https://youtu.be/abc123xyz99",
                "tone": "professional",
                "length": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        mock_downloader.return_value.download_mp3.assert_not_called()
        mock_transcription_service.return_value.transcribe_youtube.assert_called_once()


class SaveBlogTests(BaseAuthenticatedAPITestCase):
    def test_save_blog_creates_record(self):
        response = self.client.post(
            reverse("save-blog"),
            {
                "title": "Generated title",
                "content": "<p>Blog content</p>",
                "link": "https://youtu.be/abc123xyz99",
                "tone": "professional",
                "length": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], "created")
        self.assertEqual(BlogPost.objects.count(), 1)

    def test_save_blog_returns_exists_for_duplicate_without_force_update(self):
        BlogPost.objects.create(
            user=self.user,
            youtube_title="Existing",
            youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            generated_content="<p>old</p>",
            tone="professional",
            length="medium",
        )

        response = self.client.post(
            reverse("save-blog"),
            {
                "title": "Existing",
                "content": "<p>new</p>",
                "link": "https://youtu.be/abc123xyz99",
                "tone": "professional",
                "length": "medium",
                "force_update": False,
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "exists")

    def test_save_blog_updates_existing_record_when_force_update_is_true(self):
        post = BlogPost.objects.create(
            user=self.user,
            youtube_title="Existing",
            youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            generated_content="<p>old</p>",
            tone="professional",
            length="medium",
        )

        response = self.client.post(
            reverse("save-blog"),
            {
                "title": "Existing",
                "content": "<p>updated</p>",
                "link": "https://youtu.be/abc123xyz99",
                "tone": "professional",
                "length": "medium",
                "force_update": True,
            },
            format="json",
        )

        post.refresh_from_db()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "updated")
        self.assertEqual(post.generated_content, "<p>updated</p>")


class BlogGenerationJobTests(BaseAuthenticatedAPITestCase):
    def test_list_jobs_returns_user_jobs_in_descending_order(self):
        older = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/oldjob",
            normalized_youtube_link="https://www.youtube.com/watch?v=oldjob",
            tone="professional",
            length="medium",
        )
        newer = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/newjob",
            normalized_youtube_link="https://www.youtube.com/watch?v=newjob",
            tone="casual",
            length="short",
        )

        response = self.client.get(reverse("generation-job-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([job["id"] for job in response.data[:2]], [newer.id, older.id])

    def test_create_job_returns_accepted(self):
        response = self.client.post(
            reverse("generation-job-create"),
            {
                "link": "https://youtu.be/abc123xyz99",
                "tone": "professional",
                "length": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], BlogGenerationJob.Status.QUEUED)
        self.assertEqual(BlogGenerationJob.objects.count(), 1)

    def test_create_job_returns_existing_active_duplicate(self):
        existing = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/abc123xyz99",
            normalized_youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            tone="professional",
            length="medium",
            status=BlogGenerationJob.Status.QUEUED,
        )

        response = self.client.post(
            reverse("generation-job-create"),
            {
                "link": "https://www.youtube.com/watch?v=abc123xyz99",
                "tone": "professional",
                "length": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], existing.id)
        self.assertEqual(BlogGenerationJob.objects.count(), 1)

    def test_create_job_reuses_recent_completed_match(self):
        existing = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/abc123xyz99",
            normalized_youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            tone="professional",
            length="medium",
            status=BlogGenerationJob.Status.COMPLETED,
            title="Existing title",
            generated_content="<h1>Existing</h1>",
        )

        response = self.client.post(
            reverse("generation-job-create"),
            {
                "link": "https://www.youtube.com/watch?v=abc123xyz99",
                "tone": "professional",
                "length": "medium",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], existing.id)
        self.assertEqual(BlogGenerationJob.objects.count(), 1)

    @patch("api.views.settings.MAX_ACTIVE_GENERATION_JOBS_PER_USER", 1)
    def test_create_job_enforces_active_job_limit(self):
        BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/firstjob",
            normalized_youtube_link="https://www.youtube.com/watch?v=firstjob",
            tone="professional",
            length="medium",
            status=BlogGenerationJob.Status.PROCESSING,
        )

        response = self.client.post(
            reverse("generation-job-create"),
            {
                "link": "https://youtu.be/secondjob",
                "tone": "technical",
                "length": "long",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
        self.assertIn("active generation jobs", response.data["detail"])

    @patch("api.views.settings.JOB_EXECUTION_MODE", "celery")
    @patch("api.views.process_blog_generation_job.delay")
    def test_process_job_enqueues_background_task(
        self,
        mock_delay,
    ):
        job = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/abc123xyz99",
            normalized_youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            tone="professional",
            length="medium",
        )
        response = self.client.post(
            reverse("generation-job-process", kwargs={"pk": job.id}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        mock_delay.assert_called_once_with(job.id)

    @patch("api.views.settings.JOB_EXECUTION_MODE", "sync")
    @patch("api.views.BlogGenerationJobProcessor.process")
    def test_process_job_runs_inline_when_sync_mode_is_enabled(self, mock_process):
        job = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/abc123xyz99",
            normalized_youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            tone="professional",
            length="medium",
        )
        completed_job = BlogGenerationJob.objects.get(pk=job.id)
        completed_job.status = BlogGenerationJob.Status.COMPLETED
        mock_process.return_value = completed_job

        response = self.client.post(
            reverse("generation-job-process", kwargs={"pk": job.id}),
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_process.assert_called_once()

    @patch("api.services.job_processing.BlogGenerator")
    @patch("api.services.job_processing.YouTubeMetadataFetcher")
    @patch("api.services.job_processing.TranscriptionService")
    @patch("api.services.job_processing.YouTubeAudioDownloader")
    def test_celery_task_processes_job_to_completion(
        self,
        mock_downloader,
        mock_transcription_service,
        mock_metadata_fetcher,
        mock_blog_generator,
    ):
        job = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/abc123xyz99",
            normalized_youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            tone="professional",
            length="medium",
        )
        mock_downloader.return_value.download_mp3.return_value = "temp-audio.mp3"
        mock_transcription_service.return_value.transcribe_file.return_value = (
            "sample transcript"
        )
        mock_transcription_service.return_value.uses_direct_youtube_transcripts.return_value = (
            False
        )
        mock_metadata_fetcher.return_value.get_title.return_value.title = "Demo title"
        mock_blog_generator.return_value.from_transcript.return_value = "<h1>Blog</h1>"

        with patch(
            "api.services.job_processing.os.path.exists", return_value=True
        ), patch("api.services.job_processing.os.remove"):
            result = process_blog_generation_job(job.id)

        job.refresh_from_db()
        self.assertEqual(result["status"], BlogGenerationJob.Status.COMPLETED)
        self.assertEqual(job.status, BlogGenerationJob.Status.COMPLETED)
        self.assertEqual(job.generated_content, "<h1>Blog</h1>")

    @patch("api.services.job_processing.BlogGenerator")
    @patch("api.services.job_processing.YouTubeMetadataFetcher")
    @patch("api.services.job_processing.TranscriptionService")
    @patch("api.services.job_processing.YouTubeAudioDownloader")
    def test_job_processor_uses_youtube_transcript_provider_without_audio_download(
        self,
        mock_downloader,
        mock_transcription_service,
        mock_metadata_fetcher,
        mock_blog_generator,
    ):
        job = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/abc123xyz99",
            normalized_youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            tone="professional",
            length="medium",
        )
        mock_transcription_service.return_value.uses_direct_youtube_transcripts.return_value = (
            True
        )
        mock_transcription_service.return_value.transcribe_youtube.return_value = (
            "sample transcript"
        )
        mock_metadata_fetcher.return_value.get_title.return_value.title = "Demo title"
        mock_blog_generator.return_value.from_transcript.return_value = "<h1>Blog</h1>"

        result = process_blog_generation_job(job.id)

        job.refresh_from_db()
        self.assertEqual(result["status"], BlogGenerationJob.Status.COMPLETED)
        self.assertEqual(job.status, BlogGenerationJob.Status.COMPLETED)
        mock_downloader.return_value.download_mp3.assert_not_called()
        mock_transcription_service.return_value.transcribe_youtube.assert_called_once()

    @patch("api.services.job_processing.BlogGenerationJobProcessor.process")
    def test_management_command_processes_queued_jobs(self, mock_process):
        job = BlogGenerationJob.objects.create(
            user=self.user,
            youtube_link="https://youtu.be/abc123xyz99",
            normalized_youtube_link="https://www.youtube.com/watch?v=abc123xyz99",
            tone="professional",
            length="medium",
        )

        call_command("process_blog_generation_jobs", limit=5)

        mock_process.assert_called_once()
        processed_job = mock_process.call_args.args[0]
        self.assertEqual(processed_job.id, job.id)


class AudioDownloadProviderTests(APITestCase):
    @patch("api.services.youtube.requests.get")
    def test_rapidapi_downloader_handles_plain_text_download_url(self, mock_get):
        conversion_response = self._build_response(
            text="https://cdn.example.com/audio.mp3",
            headers={"content-type": "text/plain"},
        )
        download_response = self._build_response(
            headers={"content-type": "audio/mpeg"},
            chunks=[b"abc", b"123"],
        )
        mock_get.side_effect = [conversion_response, download_response]

        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = RapidApiAudioDownloader(
                media_root=temp_dir,
                api_key="test-key",
                api_host="youtube-mp310.p.rapidapi.com",
                base_url="https://youtube-mp310.p.rapidapi.com",
                download_path="/download/mp3",
                timeout_seconds=5,
            )
            output_path = downloader.download_mp3("https://youtu.be/abc123xyz99")

        self.assertEqual(mock_get.call_count, 2)
        self.assertTrue(output_path.endswith(".mp3"))

    @patch("api.services.youtube.requests.get")
    def test_rapidapi_downloader_handles_json_download_url(self, mock_get):
        conversion_response = self._build_response(
            json_payload={
                "status": "success",
                "result": [{"dlurl": "https://cdn.example.com/audio.mp3"}],
            },
            headers={"content-type": "application/json"},
        )
        download_response = self._build_response(
            headers={"content-type": "audio/mpeg"},
            chunks=[b"abc"],
        )
        mock_get.side_effect = [conversion_response, download_response]

        with tempfile.TemporaryDirectory() as temp_dir:
            downloader = RapidApiAudioDownloader(
                media_root=temp_dir,
                api_key="test-key",
                api_host="youtube-mp310.p.rapidapi.com",
                base_url="https://youtube-mp310.p.rapidapi.com",
                download_path="/download/mp3",
                timeout_seconds=5,
            )
            output_path = downloader.download_mp3("https://youtu.be/abc123xyz99")

        self.assertEqual(mock_get.call_count, 2)
        self.assertTrue(output_path.endswith(".mp3"))

    @patch("api.services.youtube.RapidApiAudioDownloader")
    @patch("api.services.youtube.LocalYtDlpAudioDownloader")
    @patch("api.services.youtube.settings.AUDIO_DOWNLOAD_PROVIDER", "rapidapi")
    def test_facade_selects_rapidapi_provider(
        self, mock_local_downloader, mock_rapidapi_downloader
    ):
        provider = mock_rapidapi_downloader.return_value
        provider.download_mp3.return_value = "rapid.mp3"

        downloader = YouTubeAudioDownloader(media_root="test-media")
        result = downloader.download_mp3("https://youtu.be/abc123xyz99")

        mock_rapidapi_downloader.assert_called_once_with(media_root="test-media")
        mock_local_downloader.assert_not_called()
        self.assertEqual(result, "rapid.mp3")

    @staticmethod
    def _build_response(
        *,
        text: str = "",
        headers: dict | None = None,
        json_payload: dict | None = None,
        chunks: list[bytes] | None = None,
    ):
        class FakeResponse:
            def __init__(self):
                self.text = text
                self.headers = headers or {}

            def raise_for_status(self):
                return None

            def json(self):
                if json_payload is None:
                    raise ValueError("No JSON payload")
                return json_payload

            def iter_content(self, chunk_size=8192):
                return iter(chunks or [])

        return FakeResponse()
