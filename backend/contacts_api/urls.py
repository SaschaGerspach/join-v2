from django.urls import path
from . import views

app_name = "contacts_api"

urlpatterns = [
    path("", views.contact_list, name="contact-list"),
    path("<int:pk>/", views.contact_detail, name="contact-detail"),
]
