import ipaddress
import socket
from urllib.parse import urlparse

from rest_framework import serializers

from .models import ALL_EVENTS

_BLOCKED_NETS = [
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
]


def _validate_webhook_url(url):
    parsed = urlparse(url)
    hostname = parsed.hostname
    if not hostname:
        raise serializers.ValidationError("Invalid URL.")
    try:
        resolved = socket.getaddrinfo(hostname, None)
    except socket.gaierror:
        raise serializers.ValidationError("Cannot resolve hostname.")
    for _, _, _, _, addr in resolved:
        ip = ipaddress.ip_address(addr[0])
        for net in _BLOCKED_NETS:
            if ip in net:
                raise serializers.ValidationError("Internal or private URLs are not allowed.")
    return url


class WebhookSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    url = serializers.URLField()

    def validate_url(self, value):
        return _validate_webhook_url(value)
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

    def validate_url(self, value):
        return _validate_webhook_url(value)
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
