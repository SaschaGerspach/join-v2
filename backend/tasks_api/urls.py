from django.urls import path
from . import views

app_name = "tasks_api"

urlpatterns = [
    path("", views.task_list, name="task-list"),
    path("<int:pk>/", views.task_detail, name="task-detail"),
    path("<int:task_pk>/subtasks/", views.subtask_list, name="subtask-list"),
    path("<int:task_pk>/subtasks/<int:pk>/", views.subtask_detail, name="subtask-detail"),
]
