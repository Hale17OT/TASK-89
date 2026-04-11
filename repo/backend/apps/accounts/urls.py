"""Auth endpoints: login, logout, session, remember-device, guest profiles."""
from django.urls import path

from . import views

urlpatterns = [
    path("csrf/", views.csrf_cookie, name="auth-csrf"),
    path("login/", views.login_view, name="auth-login"),
    path("logout/", views.logout_view, name="auth-logout"),
    path("session/", views.session_info, name="auth-session"),
    path("session/refresh/", views.session_refresh, name="auth-session-refresh"),
    path("change-password/", views.change_password, name="auth-change-password"),
    path("remember-device/", views.remember_device, name="auth-remember-device"),
    path("remember-device/prefill/", views.remember_device_prefill, name="auth-remember-prefill"),
    path("guest-profiles/", views.guest_profile_list, name="auth-guest-profiles"),
    path("guest-profiles/<uuid:pk>/activate/", views.guest_profile_activate, name="auth-guest-activate"),
    path("guest-profiles/<uuid:pk>/recent-patients/", views.guest_recent_patients, name="auth-guest-recent"),
]
