from django.urls import path

from .views import register_view, profile_view, login_view, logout_view, refresh_token


app_name = "api"

urlpatterns = [
    path("register/", register_view, name="register"),
    path("me/", profile_view, name="detail"),
    path("login/", login_view, name="login"),
    path("logout/", logout_view, name="logout"),
    path("refresh/", refresh_token, name="refresh"),
]
