from django.urls import path
from . import views

app_name = "columns_api"

urlpatterns = [
    path("", views.column_list, name="column-list"),
    path("<int:pk>/", views.column_detail, name="column-detail"),
]
