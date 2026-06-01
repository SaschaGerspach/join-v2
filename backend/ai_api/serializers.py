from rest_framework import serializers


class AIFeatureSerializer(serializers.Serializer):
    key = serializers.CharField()
    label = serializers.CharField()
    description = serializers.CharField()
    enabled = serializers.BooleanField()


class AIFeatureListSerializer(serializers.Serializer):
    provider = serializers.CharField()
    configured = serializers.BooleanField()
    features = AIFeatureSerializer(many=True)


class AIFeatureUpdateSerializer(serializers.Serializer):
    enabled = serializers.BooleanField()
