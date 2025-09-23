# from django.contrib.auth import authenticate
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
from .services.youtube import YouTubeAudioDownloader, YouTubeMetadataFetcher


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
        if not link:
            return Response(
                {"detail": "Missing 'link' field."}, status=status.HTTP_400_BAD_REQUEST
            )
        cache_key = f"generated_blog:{request.user.id}:{link}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached, status=status.HTTP_200_OK)
        try:
            title = YouTubeMetadataFetcher().get_title(link).title
            audio_path = YouTubeAudioDownloader().download_mp3(link)
            transcription = TranscriptionService().transcribe_file(audio_path)
            blog_content = BlogGenerator().from_transcript(transcription)

            post = BlogRepository().create(
                user=request.user,
                youtube_title=title,
                youtube_link=link,
                generated_content=blog_content,
            )
            payload = {"id": post.id, "content": blog_content, "title": title}
            cache.set(cache_key, payload, timeout=60 * 60 * 24)  # cache for 24h
            return Response(payload, status=status.HTTP_201_CREATED)

        except Exception as e:
            # Log for debugging
            return Response(
                {"detail": f"Generation failed: {str(e)}"},
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


class BlogDetailAPIView(generics.RetrieveDestroyAPIView):
    """
    GET  /blogs/<id>   -> Retrieve a single blog post (only for the owner)
    DELETE /blogs/<id> -> Delete the blog post (only for the owner)
    """

    serializer_class = BlogPostSerializer
    permission_classes = [IsAuthenticated]
    throttle_classes = []

    def get_queryset(self):
        return BlogPost.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response({"success": True}, status=status.HTTP_204_NO_CONTENT)
