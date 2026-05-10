# api/urls.py
from django.urls import path

from .views import (
    BlogGenerationJobCreateAPIView,
    BlogGenerationJobDetailAPIView,
    BlogGenerationJobListAPIView,
    BlogGenerationJobProcessAPIView,
    BlogDetailAPIView,
    BlogListAPIView,
    CurrentUserView,
    GenerateBlogView,
    HealthCheckView,
    LoginView,
    NoThrottleTokenBlacklistView,
    NoThrottleTokenRefreshView,
    SaveBlogView,
    SignupView,
)

urlpatterns = [
    path("health/", HealthCheckView.as_view(), name="health"),
    path(
        "generation-jobs/list/",
        BlogGenerationJobListAPIView.as_view(),
        name="generation-job-list",
    ),
    path(
        "generation-jobs/",
        BlogGenerationJobCreateAPIView.as_view(),
        name="generation-job-create",
    ),
    path(
        "generation-jobs/<int:pk>/",
        BlogGenerationJobDetailAPIView.as_view(),
        name="generation-job-detail",
    ),
    path(
        "generation-jobs/<int:pk>/process/",
        BlogGenerationJobProcessAPIView.as_view(),
        name="generation-job-process",
    ),
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", NoThrottleTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", NoThrottleTokenBlacklistView.as_view(), name="token_blacklist"),
    path("generate-blog/", GenerateBlogView.as_view(), name="generate_blog"),
    path("save-blog/", SaveBlogView.as_view(), name="save-blog"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("blogs", BlogListAPIView.as_view(), name="blog-list-api"),
    path("blogs/<int:pk>/", BlogDetailAPIView.as_view(), name="blog-detail"),
]
