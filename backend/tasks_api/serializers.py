import re

from rest_framework import serializers

from .models import Task

PRIORITY_CHOICES = Task.Priority.choices
HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')


class LabelSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.CharField()


class LabelCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    color = serializers.CharField(max_length=7, default='#29abe2')

    def validate_color(self, value):
        if not HEX_COLOR_RE.match(value):
            raise serializers.ValidationError("Invalid hex color.")
        return value


class LabelUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False, max_length=50)
    color = serializers.CharField(required=False, max_length=7)

    def validate_color(self, value):
        if not HEX_COLOR_RE.match(value):
            raise serializers.ValidationError("Invalid hex color.")
        return value


class TaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    board = serializers.IntegerField()
    column = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    priority = serializers.CharField()
    assigned_to = serializers.ListField(child=serializers.IntegerField())
    due_date = serializers.DateField(allow_null=True)
    created_at = serializers.DateTimeField()
    order = serializers.IntegerField()
    subtask_count = serializers.IntegerField()
    subtask_done_count = serializers.IntegerField()
    attachment_count = serializers.IntegerField()
    labels = LabelSerializer(many=True)


class TaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default="", max_length=5000)
    priority = serializers.ChoiceField(choices=PRIORITY_CHOICES, required=False, default=Task.Priority.MEDIUM)
    column = serializers.IntegerField(required=False, allow_null=True)
    assigned_to = serializers.ListField(child=serializers.IntegerField(), required=False, default=list)
    due_date = serializers.DateField(required=False, allow_null=True)


class TaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, max_length=5000)
    priority = serializers.ChoiceField(choices=PRIORITY_CHOICES, required=False)
    column = serializers.IntegerField(required=False, allow_null=True)
    assigned_to = serializers.ListField(child=serializers.IntegerField(), required=False)
    due_date = serializers.DateField(required=False, allow_null=True)
    order = serializers.IntegerField(required=False, min_value=0)
    label_ids = serializers.ListField(child=serializers.IntegerField(), required=False)


class TaskReorderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField(required=False)
    column = serializers.IntegerField(required=False)


class SubtaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    task = serializers.IntegerField()
    title = serializers.CharField()
    done = serializers.BooleanField()


class SubtaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)


class SubtaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    done = serializers.BooleanField(required=False)


class CommentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    task = serializers.IntegerField()
    author_id = serializers.IntegerField()
    author_name = serializers.CharField()
    text = serializers.CharField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()


class CommentCreateSerializer(serializers.Serializer):
    text = serializers.CharField(max_length=5000)


class AttachmentSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    filename = serializers.CharField()
    url = serializers.URLField()
    size = serializers.IntegerField()
    uploaded_at = serializers.DateTimeField()


class AttachmentUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
