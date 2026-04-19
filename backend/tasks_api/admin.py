from django.contrib import admin
from .models import Task, Subtask, Comment


class SubtaskInline(admin.TabularInline):
    model = Subtask
    extra = 0
    fields = ('title', 'done')


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'board', 'column', 'priority', 'due_date', 'created_at')
    list_filter = ('priority', 'due_date', 'board')
    search_fields = ('title', 'description', 'board__title')
    raw_id_fields = ('board', 'column')
    filter_horizontal = ('assignees',)
    date_hierarchy = 'created_at'
    inlines = [SubtaskInline]


@admin.register(Subtask)
class SubtaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'task', 'done')
    list_filter = ('done',)
    search_fields = ('title', 'task__title')


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('task', 'author', 'created_at')
    search_fields = ('text', 'author__email', 'task__title')
    raw_id_fields = ('task', 'author')
