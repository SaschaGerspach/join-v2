from rest_framework import serializers

from .models import ActionType, ConditionType, TriggerType


class RuleConditionSerializer(serializers.Serializer):
    condition_type = serializers.ChoiceField(choices=ConditionType.choices)
    config = serializers.JSONField(default=dict)


class RuleActionSerializer(serializers.Serializer):
    action_type = serializers.ChoiceField(choices=ActionType.choices)
    config = serializers.JSONField(default=dict)
    order = serializers.IntegerField(required=False, default=0)


class AutomationRuleCreateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200)
    trigger_type = serializers.ChoiceField(choices=TriggerType.choices)
    trigger_config = serializers.JSONField(default=dict, required=False)
    conditions = RuleConditionSerializer(many=True, required=False, default=list)
    actions = RuleActionSerializer(many=True)

    def validate_actions(self, value):
        if not value:
            raise serializers.ValidationError("At least one action is required.")
        return value


class AutomationRuleUpdateSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=200, required=False)
    trigger_type = serializers.ChoiceField(choices=TriggerType.choices, required=False)
    trigger_config = serializers.JSONField(required=False)
    conditions = RuleConditionSerializer(many=True, required=False)
    actions = RuleActionSerializer(many=True, required=False)
    is_active = serializers.BooleanField(required=False)
