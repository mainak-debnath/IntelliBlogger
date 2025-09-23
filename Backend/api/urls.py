# api/urls.py
from django.urls import path

# from rest_framework_simplejwt.views import (
#     #TokenBlacklistView,
#     # TokenObtainPairView,
#     #TokenRefreshView,
# )
from .views import (
    BlogDetailAPIView,
    BlogListAPIView,
    CurrentUserView,
    GenerateBlogView,
    LoginView,
    NoThrottleTokenBlacklistView,
    NoThrottleTokenRefreshView,
    SignupView,
)

urlpatterns = [
    path("signup/", SignupView.as_view(), name="signup"),
    path("login/", LoginView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", NoThrottleTokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", NoThrottleTokenBlacklistView.as_view(), name="token_blacklist"),
    path("generate-blog/", GenerateBlogView.as_view(), name="generate_blog"),
    path("me/", CurrentUserView.as_view(), name="current_user"),
    path("blogs", BlogListAPIView.as_view(), name="blog-list-api"),
    path("blogs/<int:pk>/", BlogDetailAPIView.as_view(), name="blog-detail"),
]
