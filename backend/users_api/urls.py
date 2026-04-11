from django.urls import path
from . import views

app_name = "users_api"

urlpatterns = [
    path("", views.user_list, name="user-list"),
    path("<int:pk>/", views.user_detail, name="user-detail"),
]
