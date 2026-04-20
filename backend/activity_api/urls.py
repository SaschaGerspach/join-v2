from django.urls import path

from . import views

app_name = "activity_api"

urlpatterns = [
    path("", views.activity_list, name="activity-list"),
]
