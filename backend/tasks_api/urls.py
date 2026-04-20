from django.urls import path
from . import views

app_name = "tasks_api"

urlpatterns = [
    path("", views.task_list, name="task-list"),
    path("my/", views.my_tasks, name="my-tasks"),
    path("archive/", views.task_archive, name="task-archive"),
    path("reorder/", views.task_reorder, name="task-reorder"),
    path("<int:pk>/", views.task_detail, name="task-detail"),
    path("<int:pk>/restore/", views.task_restore, name="task-restore"),
    path("<int:task_pk>/subtasks/", views.subtask_list, name="subtask-list"),
    path("<int:task_pk>/subtasks/<int:pk>/", views.subtask_detail, name="subtask-detail"),
    path("<int:task_pk>/comments/", views.comment_list, name="comment-list"),
    path("<int:task_pk>/comments/<int:pk>/", views.comment_detail, name="comment-detail"),
    path("<int:task_pk>/attachments/", views.attachment_list, name="attachment-list"),
    path("<int:task_pk>/attachments/<int:pk>/", views.attachment_detail, name="attachment-detail"),
    path("<int:task_pk>/attachments/<int:pk>/download/", views.attachment_download, name="attachment-download"),
    path("<int:task_pk>/dependencies/", views.dependency_list, name="dependency-list"),
    path("<int:task_pk>/dependencies/<int:pk>/", views.dependency_detail, name="dependency-detail"),
    path("<int:task_pk>/fields/", views.task_field_values, name="task-field-values"),
]
