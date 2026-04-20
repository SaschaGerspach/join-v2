from rest_framework import serializers


class NotificationSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    type = serializers.CharField()
    message = serializers.CharField()
    board_id = serializers.IntegerField(allow_null=True)
    task_id = serializers.IntegerField(allow_null=True)
    is_read = serializers.BooleanField()
    created_at = serializers.DateTimeField()


class NotificationPreferenceSerializer(serializers.Serializer):
    disabled_types = serializers.ListField(child=serializers.CharField(), required=False)
    muted_boards = serializers.ListField(child=serializers.IntegerField(), required=False)
