from django.db import IntegrityError
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.models import Board
from boards_api.permissions import can_access_board
from config.serializers import DetailSerializer
from ..models import Label
from ..serializers import (
    LabelCreateSerializer,
    LabelSerializer,
    LabelUpdateSerializer,
)
from ._helpers import serialize_label


@extend_schema(
    methods=["GET"],
    responses={200: LabelSerializer(many=True), 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request=LabelCreateSerializer,
    responses={201: LabelSerializer, 400: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "POST"])
def label_list(request, board_pk):
    try:
        board = Board.objects.get(pk=board_pk)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "GET":
        return Response([serialize_label(label) for label in board.labels.all()])

    serializer = LabelCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    label, created = Label.objects.get_or_create(
        board=board, name=serializer.validated_data["name"],
        defaults={"color": serializer.validated_data["color"]},
    )
    if not created:
        return Response({"detail": "Label already exists."}, status=status.HTTP_400_BAD_REQUEST)
    return Response(serialize_label(label), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=LabelUpdateSerializer,
    responses={200: LabelSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
@api_view(["PATCH", "DELETE"])
def label_detail(request, board_pk, pk):
    try:
        label = Label.objects.get(pk=pk, board_id=board_pk)
    except Label.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_access_board(label.board, request.user):
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PATCH":
        serializer = LabelUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        if "name" in data:
            label.name = data["name"]
        if "color" in data:
            label.color = data["color"]
        try:
            label.save()
        except IntegrityError:
            return Response({"detail": "Label name already exists."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serialize_label(label))

    label.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
