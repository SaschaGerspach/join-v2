from rest_framework import serializers

from .models import ALL_EVENTS


class WebhookSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.URLField()
    secret = serializers.CharField(required=False, allow_blank=True, max_length=64, default="")
    events = serializers.ListField(child=serializers.CharField())
    is_active = serializers.BooleanField(default=True)
    created_at = serializers.DateTimeField(read_only=True)

    def validate_events(self, value):
        invalid = [e for e in value if e not in ALL_EVENTS]
        if invalid:
            raise serializers.ValidationError(f"Invalid events: {', '.join(invalid)}")
        return value


class WebhookUpdateSerializer(serializers.Serializer):
    url = serializers.URLField(required=False)
    secret = serializers.CharField(required=False, allow_blank=True, max_length=64)
    events = serializers.ListField(child=serializers.CharField(), required=False)
    is_active = serializers.BooleanField(required=False)

    def validate_events(self, value):
        invalid = [e for e in value if e not in ALL_EVENTS]
        if invalid:
            raise serializers.ValidationError(f"Invalid events: {', '.join(invalid)}")
        return value


class WebhookDeliverySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    event_type = serializers.CharField()
    payload = serializers.JSONField()
    response_status = serializers.IntegerField(allow_null=True)
    status = serializers.CharField()
    attempted_at = serializers.DateTimeField()
    delivery_id = serializers.UUIDField()
