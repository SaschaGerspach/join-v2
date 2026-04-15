from rest_framework import serializers


class DetailSerializer(serializers.Serializer):
    detail = serializers.CharField()


class AdminStatsSerializer(serializers.Serializer):
    users = serializers.IntegerField()
    boards = serializers.IntegerField()
    tasks = serializers.IntegerField()
    contacts = serializers.IntegerField()
