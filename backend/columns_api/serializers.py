from rest_framework import serializers


class ColumnSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    board = serializers.IntegerField()
    title = serializers.CharField()
    order = serializers.IntegerField()


class ColumnCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)


class ColumnUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    order = serializers.IntegerField(required=False, min_value=0)
