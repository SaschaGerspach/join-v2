from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Count, Max
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle

from activity_api.models import ActivityEntry
from audit_api.models import AuditLog
from boards_api.models import Board
from contacts_api.models import Contact
from tasks_api.models import Task

from .serializers import (
    AdminBoardsResponseSerializer,
    AdminStatsSerializer,
    AuditLogResponseSerializer,
)

User = get_user_model()


class AdminThrottle(UserRateThrottle):
    rate = "30/minute"


def _trend(qs, date_field, now):
    one_week_ago = now - timedelta(days=7)
    two_weeks_ago = now - timedelta(days=14)
    return {
        "total": qs.count(),
        "this_week": qs.filter(**{f"{date_field}__gte": one_week_ago}).count(),
        "last_week": qs.filter(
            **{f"{date_field}__gte": two_weeks_ago, f"{date_field}__lt": one_week_ago}
        ).count(),
    }


@extend_schema(responses={200: AdminStatsSerializer})
@api_view(["GET"])
@permission_classes([IsAdminUser])
@throttle_classes([AdminThrottle])
def admin_stats(request):
    now = timezone.now()
    thirty_days_ago = now - timedelta(days=30)

    def _user_list(qs):
        return [
            {"id": u.pk, "email": u.email, "first_name": u.first_name, "last_name": u.last_name}
            for u in qs[:20]
        ]

    unverified_qs = User.objects.filter(is_verified=False)
    inactive_qs = User.objects.filter(last_login__lt=thirty_days_ago)
    never_qs = User.objects.filter(last_login__isnull=True).exclude(date_joined__gte=thirty_days_ago)

    return Response({
        "users": _trend(User.objects.all(), "date_joined", now),
        "boards": _trend(Board.objects.all(), "created_at", now),
        "tasks": _trend(Task.objects.all(), "created_at", now),
        "contacts": Contact.objects.count(),
        "unverified_users": {"count": unverified_qs.count(), "list": _user_list(unverified_qs)},
        "inactive_users": {"count": inactive_qs.count(), "list": _user_list(inactive_qs)},
        "never_logged_in": {"count": never_qs.count(), "list": _user_list(never_qs)},
    })


@extend_schema(
    parameters=[
        OpenApiParameter(name="event_type", required=False, type=str),
        OpenApiParameter(name="limit", required=False, type=int),
    ],
    responses={200: AuditLogResponseSerializer},
)
@api_view(["GET"])
@permission_classes([IsAdminUser])
@throttle_classes([AdminThrottle])
def admin_audit_log(request):
    qs = AuditLog.objects.select_related("user").order_by("-created_at")

    event_type = request.query_params.get("event_type")
    if event_type:
        qs = qs.filter(event_type=event_type)

    limit = min(int(request.query_params.get("limit", 20)), 100)
    entries = qs[:limit]

    return Response({
        "results": [
            {
                "id": e.pk,
                "timestamp": e.created_at,
                "user_email": e.user.email if e.user else None,
                "event_type": e.event_type,
                "ip_address": e.ip_address,
                "detail": e.detail,
            }
            for e in entries
        ],
        "event_types": [c[0] for c in AuditLog.EventType.choices],
    })


@extend_schema(responses={200: AdminBoardsResponseSerializer})
@api_view(["GET"])
@permission_classes([IsAdminUser])
@throttle_classes([AdminThrottle])
def admin_boards(request):
    seven_days_ago = timezone.now() - timedelta(days=7)

    active_ids = (
        ActivityEntry.objects.filter(created_at__gte=seven_days_ago)
        .values_list("board_id", flat=True)
        .distinct()
    )
    active_count = len(set(active_ids))
    total_count = Board.objects.count()

    top_boards = (
        Board.objects.annotate(task_count=Count("tasks"))
        .order_by("-task_count")[:5]
    )

    recent_boards = (
        Board.objects.filter(activity__created_at__gte=seven_days_ago)
        .annotate(last_activity=Max("activity__created_at"))
        .order_by("-last_activity")[:5]
    )

    return Response({
        "active_boards": active_count,
        "inactive_boards": total_count - active_count,
        "top_boards": [
            {
                "id": b.pk,
                "title": b.title,
                "color": b.color,
                "task_count": b.task_count,
            }
            for b in top_boards
        ],
        "recent_boards": [
            {
                "id": b.pk,
                "title": b.title,
                "color": b.color,
                "last_activity": b.last_activity,
            }
            for b in recent_boards
        ],
    })
