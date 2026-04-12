from django.urls import path
from . import views

app_name = "boards_api"

urlpatterns = [
    path("", views.board_list, name="board-list"),
    path("<int:pk>/", views.board_detail, name="board-detail"),
    path("<int:pk>/members/", views.board_members, name="board-members"),
    path("<int:pk>/members/<int:user_pk>/", views.board_member_detail, name="board-member-detail"),
]
