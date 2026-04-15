from rest_framework import serializers


class LabelSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    color = serializers.CharField()


class LabelCreateSerializer(serializers.Serializer):
    name = serializers.CharField()
    color = serializers.CharField(required=False)


class LabelUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(required=False)
    color = serializers.CharField(required=False)


class TaskSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    board = serializers.IntegerField()
    column = serializers.IntegerField(allow_null=True)
    title = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    priority = serializers.CharField()
    assigned_to = serializers.IntegerField(allow_null=True)
    due_date = serializers.DateField(allow_null=True)
    created_at = serializers.DateTimeField()
    order = serializers.IntegerField()
    subtask_count = serializers.IntegerField()
    subtask_done_count = serializers.IntegerField()
    attachment_count = serializers.IntegerField()
    labels = LabelSerializer(many=True)


class TaskCreateSerializer(serializers.Serializer):
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.CharField(required=False)
    column = serializers.IntegerField(required=False)
    assigned_to = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)


class TaskUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    description = serializers.CharField(required=False, allow_blank=True)
    priority = serializers.CharField(required=False)
    column = serializers.IntegerField(required=False)
    assigned_to = serializers.IntegerField(required=False, allow_null=True)
    due_date = serializers.DateField(required=False, allow_null=True)
    order = serializers.IntegerField(required=False)
    label_ids = serializers.ListField(child=serializers.IntegerField(), required=False)


class TaskReorderItemSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    order = serializers.IntegerField(required=False)
    column = serializers.IntegerField(required=False)
