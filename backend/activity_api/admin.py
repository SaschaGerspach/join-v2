from django.contrib import admin

from .models import ActivityEntry


@admin.register(ActivityEntry)
class ActivityEntryAdmin(admin.ModelAdmin):
    list_display = ("board", "user", "action", "entity_type", "entity_title", "created_at")
    list_filter = ("action", "entity_type", "board")
    search_fields = ("entity_title", "details")
    ordering = ("-created_at",)
