from django.urls import path

from . import views

urlpatterns = [
    path("admin/features/", views.admin_features),
    path("admin/features/<str:key>/", views.admin_feature_detail),
    path("generate-description/", views.generate_description),
    path("suggest-subtasks/", views.suggest_subtasks),
    path("summarize/", views.summarize),
    path("categorize/", views.categorize),
]
