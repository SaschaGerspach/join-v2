from django.urls import path
from . import views

app_name = "columns_api"

urlpatterns = [
    path("", views.column_list, name="column-list"),
    path("reorder/", views.column_reorder, name="column-reorder"),
    path("<int:pk>/", views.column_detail, name="column-detail"),
]
