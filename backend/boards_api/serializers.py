from rest_framework import serializers


class BoardSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    title = serializers.CharField()
    color = serializers.CharField()
    created_by = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    is_owner = serializers.BooleanField()
    is_favorite = serializers.BooleanField()
    is_member = serializers.BooleanField()
    team_id = serializers.IntegerField(allow_null=True)
    team_name = serializers.CharField(allow_null=True)


BOARD_TEMPLATES = {
    "kanban": ["To do", "In progress", "Await feedback", "Done"],
    "scrum": ["Backlog", "Sprint", "In progress", "Review", "Done"],
    "bug_tracking": ["New", "Confirmed", "In progress", "Fixed", "Closed"],
}


class BoardCreateSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255)
    template = serializers.ChoiceField(
        choices=list(BOARD_TEMPLATES.keys()),
        required=False,
        default="kanban",
    )
    team_id = serializers.IntegerField(required=False, allow_null=True)


class BoardUpdateSerializer(serializers.Serializer):
    title = serializers.CharField(required=False, max_length=255)
    color = serializers.RegexField(regex=r'^#[0-9a-fA-F]{6}$', required=False)
    team_id = serializers.IntegerField(required=False, allow_null=True)


class BoardMemberSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    role = serializers.CharField(required=False)
    invited_at = serializers.DateTimeField(required=False)


class BoardMemberInviteSerializer(serializers.Serializer):
    email = serializers.EmailField()


ROLE_CHOICES = [("admin", "Admin"), ("editor", "Editor"), ("viewer", "Viewer")]


class BoardMemberRoleSerializer(serializers.Serializer):
    role = serializers.ChoiceField(choices=ROLE_CHOICES)
