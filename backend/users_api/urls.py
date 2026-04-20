from django.urls import path
from . import views

app_name = "users_api"

urlpatterns = [
    path("", views.user_list, name="user-list"),
    path("export/", views.data_export, name="data-export"),
    path("<int:pk>/", views.user_detail, name="user-detail"),
]
