from django.contrib import admin
from .models import Column


@admin.register(Column)
class ColumnAdmin(admin.ModelAdmin):
    list_display = ('title', 'board', 'order')
    list_filter = ('board',)
    search_fields = ('title', 'board__title')
    ordering = ('board', 'order')
