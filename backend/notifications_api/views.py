from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from config.serializers import DetailSerializer
from .models import Notification, NotificationPreference
from .serializers import NotificationSerializer, NotificationPreferenceSerializer


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


@extend_schema(
    methods=["GET"],
    responses={200: NotificationPreferenceSerializer},
)
@extend_schema(
    methods=["PUT"],
    request=NotificationPreferenceSerializer,
    responses={200: NotificationPreferenceSerializer},
)
@api_view(["GET", "PUT"])
def notification_preferences(request):
    prefs, _ = NotificationPreference.objects.get_or_create(user=request.user)

    if request.method == "GET":
        return Response({
            "disabled_types": prefs.disabled_types,
            "muted_boards": list(prefs.muted_boards.values_list("pk", flat=True)),
            "email_delivery": prefs.email_delivery,
        })

    serializer = NotificationPreferenceSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    if "disabled_types" in data:
        valid_types = {t.value for t in Notification.Type}
        prefs.disabled_types = [t for t in data["disabled_types"] if t in valid_types]
        prefs.save(update_fields=["disabled_types"])
    if "muted_boards" in data:
        from boards_api.models import Board
        from django.db.models import Q
        accessible = Board.objects.filter(
            Q(created_by=request.user) | Q(members__user=request.user),
            pk__in=data["muted_boards"],
        ).values_list("pk", flat=True)
        prefs.muted_boards.set(accessible)
    if "email_delivery" in data:
        prefs.email_delivery = data["email_delivery"]
        prefs.save(update_fields=["email_delivery"])

    return Response({
        "disabled_types": prefs.disabled_types,
        "muted_boards": list(prefs.muted_boards.values_list("pk", flat=True)),
        "email_delivery": prefs.email_delivery,
    })
