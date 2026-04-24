from django.urls import path

from . import views

urlpatterns = [
    path("stats/", views.admin_stats),
    path("audit-log/", views.admin_audit_log),
    path("boards/", views.admin_boards),
]
