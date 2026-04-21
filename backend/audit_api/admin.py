from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("event_type", "user", "short_detail", "ip_address", "created_at")
    list_filter = ("event_type", "created_at")
    search_fields = ("user__email", "detail", "ip_address")
    readonly_fields = ("user", "event_type", "detail", "ip_address", "created_at")
    ordering = ("-created_at",)
    date_hierarchy = "created_at"
    list_per_page = 50

    def short_detail(self, obj):
        return obj.detail[:120] if obj.detail else "—"
    short_detail.short_description = "Detail"

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
