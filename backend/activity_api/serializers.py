from rest_framework import serializers


class ActivityEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    user_name = serializers.CharField()
    action = serializers.CharField()
    entity_type = serializers.CharField()
    entity_title = serializers.CharField()
    details = serializers.CharField()
    created_at = serializers.DateTimeField()
