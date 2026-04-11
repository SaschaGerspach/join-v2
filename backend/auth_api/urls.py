from django.urls import path
from . import views

app_name = "auth_api"

urlpatterns = [
    path("register", views.register, name="register"),
    path("login", views.login_view, name="login"),
]
