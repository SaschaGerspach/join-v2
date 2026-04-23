from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_edit_board, get_board_or_404
from ..models import CustomField, TaskFieldValue
from ..serializers import (
    CustomFieldCreateSerializer,
    CustomFieldSerializer,
    CustomFieldUpdateSerializer,
    TaskFieldValuesUpdateSerializer,
)


@extend_schema(
    methods=["GET"],
    responses={200: CustomFieldSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    request=CustomFieldCreateSerializer,
    responses={201: CustomFieldSerializer},
)
@api_view(["GET", "POST"])
def custom_field_list(request, board_pk):
    board, err = get_board_or_404(board_pk, request.user)
    if err:
        return err

    if request.method == "GET":
        fields = board.custom_fields.all()
        return Response([
            {"id": f.pk, "name": f.name, "field_type": f.field_type, "options": f.options, "order": f.order}
            for f in fields
        ])

    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    serializer = CustomFieldCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    if CustomField.objects.filter(board=board, name=data["name"]).exists():
        return Response({"detail": "A field with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)

    options = data.get("options", [])
    if data["field_type"] == "select" and not options:
        return Response({"detail": "Select fields require at least one option."}, status=status.HTTP_400_BAD_REQUEST)

    field = CustomField.objects.create(
        board=board,
        name=data["name"],
        field_type=data["field_type"],
        options=options,
    )
    return Response(
        {"id": field.pk, "name": field.name, "field_type": field.field_type, "options": field.options, "order": field.order},
        status=status.HTTP_201_CREATED,
    )


@extend_schema(
    methods=["PATCH"],
    request=CustomFieldUpdateSerializer,
    responses={200: CustomFieldSerializer},
)
@extend_schema(methods=["DELETE"], responses={204: None})
@api_view(["PATCH", "DELETE"])
def custom_field_detail(request, board_pk, pk):
    board, err = get_board_or_404(board_pk, request.user)
    if err:
        return err

    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    try:
        field = CustomField.objects.get(pk=pk, board=board)
    except CustomField.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PATCH":
        serializer = CustomFieldUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if "name" in data:
            if CustomField.objects.filter(board=board, name=data["name"]).exclude(pk=pk).exists():
                return Response({"detail": "A field with this name already exists."}, status=status.HTTP_400_BAD_REQUEST)
            field.name = data["name"]
        if "options" in data:
            field.options = data["options"]
        if "order" in data:
            field.order = data["order"]
        field.save()
        return Response({"id": field.pk, "name": field.name, "field_type": field.field_type, "options": field.options, "order": field.order})

    field.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(
    methods=["GET"],
    responses={200: TaskFieldValuesUpdateSerializer},
)
@extend_schema(
    methods=["PUT"],
    request=TaskFieldValuesUpdateSerializer,
    responses={200: TaskFieldValuesUpdateSerializer},
)
@api_view(["GET", "PUT"])
def task_field_values(request, task_pk):
    from ..models import Task
    from boards_api.permissions import can_access_board

    try:
        task = Task.objects.select_related("board").get(pk=task_pk, archived_at__isnull=True)
    except Task.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(task.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        values = task.field_values.select_related("field").all()
        return Response({"values": [{"field_id": v.field_id, "value": v.value} for v in values]})

    if not can_edit_board(task.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    serializer = TaskFieldValuesUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    board_field_ids = set(task.board.custom_fields.values_list("pk", flat=True))
    result = []
    for item in serializer.validated_data["values"]:
        if item["field_id"] not in board_field_ids:
            continue
        obj, _ = TaskFieldValue.objects.update_or_create(
            task=task, field_id=item["field_id"],
            defaults={"value": item["value"]},
        )
        result.append({"field_id": obj.field_id, "value": obj.value})

    return Response({"values": result})
