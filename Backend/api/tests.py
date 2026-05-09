from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from api.models import BlogPost


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
