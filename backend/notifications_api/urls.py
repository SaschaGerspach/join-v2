from django.urls import path

from . import views

app_name = "notifications_api"

urlpatterns = [
    path("", views.notification_list, name="notification-list"),
    path("<int:pk>/read/", views.notification_read, name="notification-read"),
    path("read-all/", views.notification_read_all, name="notification-read-all"),
    path("preferences/", views.notification_preferences, name="notification-preferences"),
]
