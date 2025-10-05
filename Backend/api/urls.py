# api/urls.py
from django.urls import path

from .views import (
    BlogDetailAPIView,
    BlogListAPIView,
    CurrentUserView,
    GenerateBlogView,
    LoginView,
    NoThrottleTokenBlacklistView,
    NoThrottleTokenRefreshView,
    SaveBlogView,
    SignupView,
)

urlpatterns = [
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
