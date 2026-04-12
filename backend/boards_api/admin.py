from django.contrib import admin
from .models import Board


@admin.register(Board)
class BoardAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_by', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('title', 'created_by__email')
    raw_id_fields = ('created_by',)
    date_hierarchy = 'created_at'
