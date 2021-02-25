from django.urls import path, include, re_path
from rest_auth.views import (
    LogoutView,
    UserDetailsView,
    PasswordChangeView,
    PasswordResetView,
    PasswordResetConfirmView,
)
from api.accounts.views import LoginAPI


urlpatterns = [
    path("login", LoginAPI.as_view(), name="login"),
    path("logout", LogoutView.as_view(), name="logout"),
    path("password/reset", PasswordResetView.as_view(), name="rest_password_reset"),
    path("user", UserDetailsView.as_view(), name="user"),
    path("password/change", PasswordChangeView.as_view(), name="rest_password_change"),
    path("password/reset", PasswordResetView.as_view(), name="rest_password_reset"),
    re_path(
        "password/reset/confirm/(?P<uidb64>[0-9A-Za-z]+)-(?P<token>.+)",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path("register", include("rest_auth.registration.urls")),
]
