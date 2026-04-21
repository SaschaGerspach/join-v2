from rest_framework import serializers


class TeamSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    name = serializers.CharField()
    created_by = serializers.IntegerField()
    is_owner = serializers.BooleanField()
    member_count = serializers.IntegerField()
    created_at = serializers.DateTimeField()


class TeamCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)


class TeamMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField()


class InviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
