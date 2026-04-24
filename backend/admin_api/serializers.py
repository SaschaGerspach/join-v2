from rest_framework import serializers


class TrendSerializer(serializers.Serializer):
    total = serializers.IntegerField()
    this_week = serializers.IntegerField()
    last_week = serializers.IntegerField()


class WarnUserSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()


class WarnGroupSerializer(serializers.Serializer):
    count = serializers.IntegerField()
    list = WarnUserSerializer(many=True)


class AdminStatsSerializer(serializers.Serializer):
    users = TrendSerializer()
    boards = TrendSerializer()
    tasks = TrendSerializer()
    contacts = serializers.IntegerField()
    unverified_users = WarnGroupSerializer()
    inactive_users = WarnGroupSerializer()
    never_logged_in = WarnGroupSerializer()


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
