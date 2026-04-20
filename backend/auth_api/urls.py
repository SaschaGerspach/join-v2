from django.urls import path
from . import views

app_name = "auth_api"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    path("token/refresh/", views.token_refresh, name="token_refresh"),
    path("me/", views.me, name="me"),
    path("verify-email/", views.verify_email, name="verify_email"),
    path("resend-verification/", views.resend_verification, name="resend_verification"),
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path("password-reset/confirm/", views.password_reset_confirm, name="password_reset_confirm"),
    path("sessions/", views.session_list, name="session_list"),
    path("sessions/<int:pk>/", views.session_revoke, name="session_revoke"),
    path("sessions/revoke-all/", views.session_revoke_all, name="session_revoke_all"),
]
