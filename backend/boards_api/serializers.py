from rest_framework import serializers


class BoardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    color = serializers.CharField()
    created_by = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    is_owner = serializers.BooleanField()


class BoardCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)


class BoardUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    color = serializers.RegexField(regex=r'^#[0-9a-fA-F]{6}$', required=False)


class BoardMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    invited_at = serializers.DateTimeField(required=False)


class BoardMemberInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()
