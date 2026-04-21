from django.urls import path
from . import views

app_name = "teams_api"

urlpatterns = [
    path("", views.team_list, name="team-list"),
    path("<int:pk>/", views.team_detail, name="team-detail"),
    path("<int:pk>/members/", views.team_members, name="team-members"),
    path("<int:pk>/members/<int:user_pk>/", views.team_member_detail, name="team-member-detail"),
]
