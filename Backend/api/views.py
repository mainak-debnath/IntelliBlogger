import logging
import os
import time
from urllib.parse import parse_qs, urlparse

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.utils import DatabaseError
from django.http import HttpResponseForbidden, StreamingHttpResponse
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from api.models import BlogPost

from .repositories.blog_repo import BlogGenerationJobRepository, BlogRepository
from .serializers import (
    BlogGenerationJobSerializer,
    BlogPostSerializer,
    GenerateBlogRequestSerializer,
    SaveBlogRequestSerializer,
    SignupSerializer,
)
from .tasks import process_blog_generation_job
from .services.blog_generation import BlogGenerator
from .services.transcription import TranscriptionService
from .services.job_notifications import BlogGenerationJobNotifier
from .services.youtube import (
    AudioDownloadError,
    YouTubeAudioDownloader,
    YouTubeMetadataFetcher,
    YouTubeUrl,
)

logger = logging.getLogger(__name__)


class SignupThrottle(UserRateThrottle):
    """10 requests per minute per user/IP."""

    scope = "signup"


class LoginThrottle(UserRateThrottle):
    """10 login attempts per minute per user/IP."""

    scope = "login"


class GenerateBlogThrottle(UserRateThrottle):
    """3 blog generations per hour per authenticated user."""

    scope = "generate_blog"


class SignupView(generics.CreateAPIView):
    serializer_class = SignupSerializer
    permission_classes = [AllowAny]
    throttle_classes = [SignupThrottle]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Create JWT tokens for convenience (so client can auto-login)
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "success": True,
                "username": user.username,
                "access": str(refresh.access_token),
                "refresh": str(refresh),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(TokenObtainPairView):
    """
    JWT login with 10 attempts/minute throttle.
    """

    permission_classes = [AllowAny]
    throttle_classes = [LoginThrottle]


class NoThrottleTokenRefreshView(TokenRefreshView):
    throttle_classes: list = []


class NoThrottleTokenBlacklistView(TokenBlacklistView):
    throttle_classes: list = []


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get(self, request):
        return Response({"username": request.user.username})


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        health = {"status": "ok", "database": "ok", "cache": "ok"}

        try:
            BlogPost.objects.exists()
        except DatabaseError:
            health["status"] = "degraded"
            health["database"] = "error"

        try:
            cache.set("healthcheck", "ok", timeout=5)
            if cache.get("healthcheck") != "ok":
                raise RuntimeError("cache round-trip failed")
        except Exception:
            health["status"] = "degraded"
            health["cache"] = "error"

        status_code = (
            status.HTTP_200_OK
            if health["status"] == "ok"
            else status.HTTP_503_SERVICE_UNAVAILABLE
        )
        return Response(health, status=status_code)


class GenerateBlogView(APIView):
    """
    POST /api/generate-blog/
    Body: { "link": "https://youtube.com/..." }
    Requires: Authorization: Bearer <access_token>
    """

    throttle_classes = [GenerateBlogThrottle]
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = GenerateBlogRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        link = serializer.validated_data["link"]
        tone = serializer.validated_data["tone"]
        length = serializer.validated_data["length"]
        normalized_link = YouTubeUrl.normalize(link)
        parsed = urlparse(normalized_link)
        query = parse_qs(parsed.query)
        video_id = query.get("v", [""])[0]
        if not video_id:
            return Response(
                {"detail": "Invalid YouTube link."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        blog_cache_key = f"generated_blog:{request.user.id}:{video_id}:{tone}:{length}"
        cached_blog = cache.get(blog_cache_key)
        if cached_blog:
            return Response(cached_blog, status=status.HTTP_200_OK)

        transcript_cache_key = f"youtube_transcript:{video_id}"
        transcription = cache.get(transcript_cache_key)

        try:
            audio_path = None
            if not transcription:
                audio_path = YouTubeAudioDownloader().download_mp3(normalized_link)
                transcription = TranscriptionService().transcribe_file(audio_path)
                cache.set(transcript_cache_key, transcription, timeout=60 * 60 * 24)

            title = YouTubeMetadataFetcher().get_title(normalized_link).title
            blog_content = BlogGenerator().from_transcript(
                transcription=transcription, tone=tone, length=length
            )
            payload = {
                "content": blog_content,
                "title": title,
                "tone": tone,
                "length": length,
            }
            cache.set(blog_cache_key, payload, timeout=60 * 60 * 24)  # cache for 24h
            return Response(payload, status=status.HTTP_201_CREATED)

        except AudioDownloadError as exc:
            logger.warning("Audio download failed for user=%s: %s", request.user.id, exc)
            return Response(
                {"detail": "Unable to download audio for this YouTube link."},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )
        except Exception:
            logger.exception("Blog generation failed for user=%s", request.user.id)
            return Response(
                {"detail": "Generation failed. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        finally:
            if "audio_path" in locals() and audio_path and os.path.exists(audio_path):
                try:
                    os.remove(audio_path)
                except OSError:
                    logger.warning("Failed to remove temporary audio file: %s", audio_path)


class BlogGenerationJobCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = [GenerateBlogThrottle]

    def post(self, request, *args, **kwargs):
        serializer = GenerateBlogRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        normalized_link = YouTubeUrl.normalize(serializer.validated_data["link"])
        repo = BlogGenerationJobRepository()

        duplicate_job = repo.get_active_duplicate(
            user=request.user,
            normalized_youtube_link=normalized_link,
            tone=serializer.validated_data["tone"],
            length=serializer.validated_data["length"],
        )
        if duplicate_job:
            response_serializer = BlogGenerationJobSerializer(duplicate_job)
            return Response(response_serializer.data, status=status.HTTP_200_OK)

        max_active_jobs = getattr(settings, "MAX_ACTIVE_GENERATION_JOBS_PER_USER", 3)
        active_jobs = repo.count_active_for_user(user=request.user)
        if active_jobs >= max_active_jobs:
            return Response(
                {
                    "detail": (
                        f"You already have {max_active_jobs} active generation jobs. "
                        "Please wait for one to finish before starting another."
                    )
                },
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        job = repo.create(
            user=request.user,
            youtube_link=serializer.validated_data["link"],
            normalized_youtube_link=normalized_link,
            tone=serializer.validated_data["tone"],
            length=serializer.validated_data["length"],
        )

        response_serializer = BlogGenerationJobSerializer(job)
        return Response(response_serializer.data, status=status.HTTP_202_ACCEPTED)


class BlogGenerationJobListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get(self, request):
        jobs = BlogGenerationJobRepository().list_for_user(user=request.user)
        serializer = BlogGenerationJobSerializer(jobs, many=True)
        return Response(serializer.data)


class BlogGenerationJobDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get(self, request, pk):
        job = BlogGenerationJobRepository().get_for_user(pk=pk, user=request.user)
        serializer = BlogGenerationJobSerializer(job)
        return Response(serializer.data)


class BlogGenerationJobStreamView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = []

    def get(self, request):
        token = request.GET.get("token")
        if not token:
            return HttpResponseForbidden("Missing token.")

        try:
            validated = JWTAuthentication().get_validated_token(token)
            user = JWTAuthentication().get_user(validated)
        except (InvalidToken, TokenError):
            return HttpResponseForbidden("Invalid token.")

        notifier = BlogGenerationJobNotifier()
        pubsub = notifier.get_pubsub(user.id)

        def event_stream():
            last_heartbeat = time.monotonic()
            try:
                yield ": connected\n\n"
                while True:
                    message = pubsub.get_message(
                        ignore_subscribe_messages=True, timeout=1.0
                    )
                    if message and message.get("type") == "message":
                        payload = message.get("data")
                        if isinstance(payload, bytes):
                            payload = payload.decode("utf-8")
                        yield f"event: job_update\ndata: {payload}\n\n"

                    now = time.monotonic()
                    if now - last_heartbeat >= 15:
                        yield ": heartbeat\n\n"
                        last_heartbeat = now
            finally:
                pubsub.close()

        response = StreamingHttpResponse(
            event_stream(),
            content_type="text/event-stream",
        )
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response


class BlogGenerationJobProcessAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def post(self, request, pk):
        job = BlogGenerationJobRepository().get_for_user(pk=pk, user=request.user)
        if job.status in {
            job.Status.QUEUED,
            job.Status.FAILED,
        }:
            if job.status == job.Status.FAILED:
                job.status = job.Status.QUEUED
                job.error_message = ""
                job.started_at = None
                job.completed_at = None
                job.save(
                    update_fields=[
                        "status",
                        "error_message",
                        "started_at",
                        "completed_at",
                        "updated_at",
                    ]
                )
            process_blog_generation_job.delay(job.id)

        serializer = BlogGenerationJobSerializer(job)
        return Response(serializer.data, status=status.HTTP_202_ACCEPTED)


class SaveBlogView(APIView):
    """
    POST /api/save-blog/
    Body: { "title": "...", "content": "...", "link": "https://youtube.com/..." }
    Requires: Authorization: Bearer <access_token>

    This endpoint saves a generated blog to the database.
    """

    permission_classes = [IsAuthenticated]
    throttle_classes = []

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        serializer = SaveBlogRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.validated_data["title"]
        content = serializer.validated_data["content"]
        link = YouTubeUrl.normalize(serializer.validated_data["link"])
        tone = serializer.validated_data["tone"]
        length = serializer.validated_data["length"]
        force_update = serializer.validated_data["force_update"]

        try:
            repo = BlogRepository()
            existing_blog = repo.get_by_params(
                user=request.user, youtube_link=link, tone=tone, length=length
            )

            if existing_blog:
                if force_update:
                    updated_blog = repo.update_content(
                        blog_post=existing_blog, new_content=content
                    )
                    return Response(
                        {
                            "status": "updated",
                            "message": "Blog updated successfully!",
                            "id": updated_blog.id,
                        },
                        status=status.HTTP_200_OK,
                    )
                else:
                    return Response(
                        {
                            "status": "exists",
                            "message": "A blog for this video with the same settings already exists.",
                            "id": existing_blog.id,
                        },
                        status=status.HTTP_200_OK,
                    )

            # Save to database
            post = BlogRepository().create(
                user=request.user,
                youtube_title=title,
                youtube_link=link,
                generated_content=content,
                tone=tone,
                length=length,
            )

            return Response(
                {
                    "id": post.id,
                    "status": "created",
                    "title": post.youtube_title,
                    "tone": post.tone,
                    "length": post.length,
                    "message": "Blog saved successfully!",
                },
                status=status.HTTP_201_CREATED,
            )

        except Exception:
            logger.exception("Blog save failed for user=%s", request.user.id)
            return Response(
                {"detail": "Save failed. Please try again later."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class BlogListAPIView(APIView):
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get(self, request):
        query = request.query_params.get("q")
        repo = BlogRepository()
        blog_qs = repo.list_for_user(request.user, query=query)
        serializer = BlogPostSerializer(blog_qs, many=True)
        return Response(serializer.data)


class BlogDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET  /blogs/<id>   -> Retrieve a single blog post (only for the owner)
    DELETE /blogs/<id> -> Delete the blog post (only for the owner)
    PUT    /blogs/<id>/   -> Update the entire blog post
    """

    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get_queryset(self):
        return BlogPost.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)

    def partial_update(self, request, *args, **kwargs):
        """Handle PATCH requests for partial updates"""
        instance = self.get_object()

        # Only allow updating these fields
        allowed_fields = ["youtube_title", "generated_content"]
        filtered_data = {
            key: value for key, value in request.data.items() if key in allowed_fields
        }

        serializer = self.get_serializer(instance, data=filtered_data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data)
