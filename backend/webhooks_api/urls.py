from django.urls import path

from . import views

urlpatterns = [
    path("", views.webhook_list, name="webhook-list"),
    path("events/", views.webhook_events, name="webhook-events"),
    path("<int:pk>/", views.webhook_detail, name="webhook-detail"),
    path("<int:pk>/deliveries/", views.webhook_deliveries, name="webhook-deliveries"),
]
