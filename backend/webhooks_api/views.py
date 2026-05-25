from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import can_edit_board, get_board_or_404
from config.serializers import DetailSerializer
from .models import Webhook, WebhookDelivery, ALL_EVENTS
from .serializers import WebhookSerializer, WebhookUpdateSerializer, WebhookDeliverySerializer


@extend_schema(
    methods=["GET"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    responses={200: WebhookSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    request=WebhookSerializer,
    responses={201: WebhookSerializer, 400: DetailSerializer},
)
@api_view(["GET", "POST"])
def webhook_list(request):
    board_id = request.query_params.get("board")
    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    board, err = get_board_or_404(board_id, request.user)
    if err:
        return err

    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        webhooks = board.webhooks.all()
        return Response(WebhookSerializer(webhooks, many=True).data)

    serializer = WebhookSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    webhook = Webhook.objects.create(
        board=board,
        url=data["url"],
        secret=data.get("secret", ""),
        events=data["events"],
        is_active=data.get("is_active", True),
    )
    return Response(WebhookSerializer(webhook).data, status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["PATCH"],
    request=WebhookUpdateSerializer,
    responses={200: WebhookSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
@api_view(["PATCH", "DELETE"])
def webhook_detail(request, pk):
    try:
        webhook = Webhook.objects.select_related("board").get(pk=pk)
    except Webhook.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_edit_board(webhook.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "DELETE":
        webhook.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    serializer = WebhookUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    for field in ["url", "secret", "events", "is_active"]:
        if field in data:
            setattr(webhook, field, data[field])
    webhook.save()
    return Response(WebhookSerializer(webhook).data)


@extend_schema(responses={200: WebhookDeliverySerializer(many=True)})
@api_view(["GET"])
def webhook_deliveries(request, pk):
    try:
        webhook = Webhook.objects.select_related("board").get(pk=pk)
    except Webhook.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    if not can_edit_board(webhook.board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    deliveries = webhook.deliveries.all()[:50]
    return Response(WebhookDeliverySerializer(deliveries, many=True).data)


@extend_schema(responses={200: None})
@api_view(["GET"])
def webhook_events(request):
    return Response(ALL_EVENTS)
