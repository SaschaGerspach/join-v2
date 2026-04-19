from django.contrib import admin

from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "type", "message", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("message", "recipient__email")
    ordering = ("-created_at",)
