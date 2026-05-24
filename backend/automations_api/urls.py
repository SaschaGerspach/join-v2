from django.urls import path

from . import views

urlpatterns = [
    path("<int:board_pk>/automations/", views.rule_list, name="automation-list"),
    path("<int:board_pk>/automations/logs/", views.automation_logs, name="automation-logs"),
    path("<int:board_pk>/automations/<int:pk>/", views.rule_detail, name="automation-detail"),
    path("<int:board_pk>/automations/<int:pk>/toggle/", views.rule_toggle, name="automation-toggle"),
]
