from rest_framework import serializers


class TrendSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    this_week = serializers.IntegerField()
    last_week = serializers.IntegerField()


class AdminStatsSerializer(serializers.Serializer):
    users = TrendSerializer()
    boards = TrendSerializer()
    tasks = TrendSerializer()
    contacts = serializers.IntegerField()
    unverified_users = serializers.IntegerField()
    inactive_users = serializers.IntegerField()
    never_logged_in = serializers.IntegerField()


class AuditLogEntrySerializer(serializers.Serializer):
    id = serializers.IntegerField()
    timestamp = serializers.DateTimeField()
    user_email = serializers.CharField(allow_null=True)
    event_type = serializers.CharField()
    ip_address = serializers.CharField(allow_null=True)
    detail = serializers.CharField()


class AuditLogResponseSerializer(serializers.Serializer):
    results = AuditLogEntrySerializer(many=True)
    event_types = serializers.ListField(child=serializers.CharField())


class TopBoardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    color = serializers.CharField()
    task_count = serializers.IntegerField()


class RecentBoardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    color = serializers.CharField()
    last_activity = serializers.DateTimeField()


class AdminBoardsResponseSerializer(serializers.Serializer):
    active_boards = serializers.IntegerField()
    inactive_boards = serializers.IntegerField()
    top_boards = TopBoardSerializer(many=True)
    recent_boards = RecentBoardSerializer(many=True)
