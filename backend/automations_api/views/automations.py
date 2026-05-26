from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_edit_board, get_board_or_404
from config.serializers import DetailSerializer
from ..models import AutomationRule, RuleAction, RuleCondition
from ..serializers import AutomationRuleCreateSerializer, AutomationRuleUpdateSerializer


def _serialize_rule(rule):
    return {
        "id": rule.pk,
        "name": rule.name,
        "board": rule.board_id,
        "trigger_type": rule.trigger_type,
        "trigger_config": rule.trigger_config,
        "conditions": [
            {"condition_type": c.condition_type, "config": c.config}
            for c in rule.conditions.all()
        ],
        "actions": [
            {"action_type": a.action_type, "config": a.config, "order": a.order}
            for a in rule.actions.all()
        ],
        "is_active": rule.is_active,
        "is_default": rule.is_default,
        "created_at": rule.created_at,
    }


@extend_schema(
    methods=["GET"],
    responses={200: None, 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request=AutomationRuleCreateSerializer,
    responses={201: None, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "POST"])
def rule_list(request, board_pk):
    board, err = get_board_or_404(board_pk, request.user)
    if err:
        return err

    if request.method == "GET":
        rules = AutomationRule.objects.filter(board=board).prefetch_related("conditions", "actions")
        return Response([_serialize_rule(r) for r in rules])

    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    serializer = AutomationRuleCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    with transaction.atomic():
        rule = AutomationRule.objects.create(
            board=board,
            created_by=request.user,
            name=data["name"],
            trigger_type=data["trigger_type"],
            trigger_config=data.get("trigger_config", {}),
        )
        for cond in data.get("conditions", []):
            RuleCondition.objects.create(
                rule=rule,
                condition_type=cond["condition_type"],
                config=cond.get("config", {}),
            )
        for i, action in enumerate(data["actions"]):
            RuleAction.objects.create(
                rule=rule,
                action_type=action["action_type"],
                config=action.get("config", {}),
                order=action.get("order", i),
            )

    rule = AutomationRule.objects.prefetch_related("conditions", "actions").get(pk=rule.pk)
    return Response(_serialize_rule(rule), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["GET"],
    responses={200: None, 404: DetailSerializer},
)
@extend_schema(
    methods=["PATCH"],
    request=AutomationRuleUpdateSerializer,
    responses={200: None, 400: DetailSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "PATCH", "DELETE"])
def rule_detail(request, board_pk, pk):
    board, err = get_board_or_404(board_pk, request.user)
    if err:
        return err

    try:
        rule = AutomationRule.objects.prefetch_related("conditions", "actions").get(pk=pk, board=board)
    except AutomationRule.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response(_serialize_rule(rule))

    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "DELETE":
        rule.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = AutomationRuleUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    data = serializer.validated_data

    with transaction.atomic():
        if "name" in data:
            rule.name = data["name"]
        if "trigger_type" in data:
            rule.trigger_type = data["trigger_type"]
        if "trigger_config" in data:
            rule.trigger_config = data["trigger_config"]
        if "is_active" in data:
            rule.is_active = data["is_active"]
        rule.save()

        if "conditions" in data:
            rule.conditions.all().delete()
            for cond in data["conditions"]:
                RuleCondition.objects.create(
                    rule=rule,
                    condition_type=cond["condition_type"],
                    config=cond.get("config", {}),
                )

        if "actions" in data:
            rule.actions.all().delete()
            for i, action in enumerate(data["actions"]):
                RuleAction.objects.create(
                    rule=rule,
                    action_type=action["action_type"],
                    config=action.get("config", {}),
                    order=action.get("order", i),
                )

    rule = AutomationRule.objects.prefetch_related("conditions", "actions").get(pk=rule.pk)
    return Response(_serialize_rule(rule))


@extend_schema(responses={200: None, 403: DetailSerializer, 404: DetailSerializer})
@api_view(["POST"])
def rule_toggle(request, board_pk, pk):
    board, err = get_board_or_404(board_pk, request.user)
    if err:
        return err

    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    try:
        rule = AutomationRule.objects.prefetch_related("conditions", "actions").get(pk=pk, board=board)
    except AutomationRule.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    rule.is_active = not rule.is_active
    rule.save(update_fields=["is_active"])
    return Response(_serialize_rule(rule))


@extend_schema(responses={200: None, 404: DetailSerializer})
@api_view(["GET"])
def automation_logs(request, board_pk):
    board, err = get_board_or_404(board_pk, request.user)
    if err:
        return err

    from ..models import AutomationLog
    logs = AutomationLog.objects.filter(board=board).select_related("rule", "task")[:100]
    return Response([
        {
            "id": log.pk,
            "rule_name": log.rule.name if log.rule else "Deleted rule",
            "task_title": log.task.title,
            "task_id": log.task_id,
            "trigger_type": log.trigger_type,
            "actions_executed": log.actions_executed,
            "executed_at": log.executed_at,
        }
        for log in logs
    ])
