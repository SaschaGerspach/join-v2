from django.urls import path

from . import views

urlpatterns = [
    path("admin/features/", views.admin_features),
    path("admin/features/<str:key>/", views.admin_feature_detail),
]
