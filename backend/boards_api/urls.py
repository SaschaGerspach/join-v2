from django.urls import path
from . import views

app_name = "boards_api"

urlpatterns = [
    path("", views.board_list, name="board-list"),
    path("<int:pk>/", views.board_detail, name="board-detail"),
]
