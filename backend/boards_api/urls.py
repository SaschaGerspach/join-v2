from django.urls import path
from . import views
from tasks_api import views as task_views

app_name = "boards_api"

urlpatterns = [
    path("", views.board_list, name="board-list"),
    path("<int:pk>/", views.board_detail, name="board-detail"),
    path("<int:pk>/export/csv/", views.board_export_csv, name="board-export-csv"),
    path("<int:pk>/favorite/", views.board_favorite, name="board-favorite"),
    path("<int:pk>/members/", views.board_members, name="board-members"),
    path("<int:pk>/members/leave/", views.board_leave, name="board-leave"),
    path("<int:pk>/members/<int:user_pk>/", views.board_member_detail, name="board-member-detail"),
    path("<int:board_pk>/labels/", task_views.label_list, name="label-list"),
    path("<int:board_pk>/labels/<int:pk>/", task_views.label_detail, name="label-detail"),
]
