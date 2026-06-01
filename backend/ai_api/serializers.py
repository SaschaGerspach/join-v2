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


class GenerateDescriptionInput(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    keywords = serializers.CharField(max_length=500, required=False, allow_blank=True)


class DescriptionOutput(serializers.Serializer):
    description = serializers.CharField()


class SuggestSubtasksInput(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class SubtasksOutput(serializers.Serializer):
    subtasks = serializers.ListField(child=serializers.CharField())


class SummarizeInput(serializers.Serializer):
    items = serializers.ListField(
        child=serializers.CharField(max_length=500), min_length=1, max_length=100
    )


class SummaryOutput(serializers.Serializer):
    summary = serializers.CharField()


class CategorizeInput(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)


class CategorizeOutput(serializers.Serializer):
    priority = serializers.CharField()
    labels = serializers.ListField(child=serializers.CharField())
