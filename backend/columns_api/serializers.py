from rest_framework import serializers


class ColumnSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    board = serializers.IntegerField()
    title = serializers.CharField()
    order = serializers.IntegerField()


class ColumnCreateSerializer(serializers.Serializer):
    title = serializers.CharField()


class ColumnUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False)
    order = serializers.IntegerField(required=False)
