# from django.contrib.auth import authenticate
from urllib.parse import parse_qs, urlparse

from django.core.cache import cache
from django.db import transaction
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import (
    TokenBlacklistView,
    TokenObtainPairView,
    TokenRefreshView,
)

from api.models import BlogPost

from .repositories.blog_repo import BlogRepository
from .serializers import BlogPostSerializer, SignupSerializer
from .services.blog_generation import BlogGenerator
from .services.transcription import TranscriptionService
from .services.youtube import YouTubeAudioDownloader, YouTubeMetadataFetcher, YouTubeUrl


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


class GenerateBlogView(APIView):
    """
    POST /api/generate-blog/
    Body: { "link": "https://youtube.com/..." }
    Requires: Authorization: Bearer <access_token>
    """

    throttle_classes = [GenerateBlogThrottle]
    permission_classes = [IsAuthenticated]

    @transaction.atomic
    def post(self, request, *args, **kwargs):
        link = request.data.get("link")
        tone = request.data.get("tone", "professional")
        length = request.data.get("length", "medium")
        if not link:
            return Response(
                {"detail": "Missing 'link' field."}, status=status.HTTP_400_BAD_REQUEST
            )
        ALLOWED_TONES = ["professional", "casual", "witty", "technical"]
        ALLOWED_LENGTHS = ["short", "medium", "long"]

        if tone not in ALLOWED_TONES or length not in ALLOWED_LENGTHS:
            return Response(
                {"detail": "Invalid tone or length specified."},
                status=status.HTTP_400_BAD_REQUEST,
            )
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
            if not transcription:
                audio_path = YouTubeAudioDownloader().download_mp3(link)
                transcription = TranscriptionService().transcribe_file(audio_path)
                cache.set(transcript_cache_key, transcription, timeout=60 * 60 * 24)

            title = YouTubeMetadataFetcher().get_title(link).title
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

        except Exception as e:
            # Log for debugging
            return Response(
                {"detail": f"Generation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
        title = request.data.get("title")
        content = request.data.get("content")
        link = request.data.get("link")
        tone = request.data.get("tone", "professional")
        length = request.data.get("length", "medium")
        force_update = request.data.get("force_update", False)

        if not all([title, content, link]):
            return Response(
                {"detail": "Missing required fields: title, content, or link."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # Check if this blog already exists for this user
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

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Blog save failed for user {request.user.id}: {str(e)}")

            return Response(
                {"detail": f"Save failed: {str(e)}"},
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
