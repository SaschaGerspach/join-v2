from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from config.serializers import DetailSerializer
from .models import Notification
from .serializers import NotificationSerializer


def serialize_notification(n):
    return {
        "id": n.pk,
        "type": n.type,
        "message": n.message,
        "board_id": n.board_id,
        "task_id": n.task_id,
        "is_read": n.is_read,
        "created_at": n.created_at,
    }


@extend_schema(
    methods=["GET"],
    responses={200: NotificationSerializer(many=True)},
)
@api_view(["GET"])
def notification_list(request):
    notifications = request.user.notifications.all()[:50]
    return Response([serialize_notification(n) for n in notifications])


@extend_schema(
    methods=["PATCH"],
    responses={200: NotificationSerializer, 404: DetailSerializer},
)
@api_view(["PATCH"])
def notification_read(request, pk):
    try:
        notification = Notification.objects.get(pk=pk, recipient=request.user)
    except Notification.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    notification.is_read = True
    notification.save(update_fields=["is_read"])
    return Response(serialize_notification(notification))


@extend_schema(
    methods=["POST"],
    responses={200: DetailSerializer},
)
@api_view(["POST"])
def notification_read_all(request):
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return Response({"detail": "All notifications marked as read."})
