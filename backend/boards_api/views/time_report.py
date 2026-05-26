from django.db.models import Sum, F
from django.db.models.functions import TruncDate
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..permissions import get_board_or_404
from tasks_api.models import TimeEntry


@extend_schema(responses={200: None})
@api_view(["GET"])
def board_time_report(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    entries = TimeEntry.objects.filter(
        task__board=board, task__archived_at__isnull=True
    ).select_related("user", "task")

    total_minutes = entries.aggregate(total=Sum("duration_minutes"))["total"] or 0

    by_user = (
        entries.values(user_id=F("user__id"))
        .annotate(
            total=Sum("duration_minutes"),
            name=F("user__first_name"),
            last=F("user__last_name"),
            email=F("user__email"),
        )
        .order_by("-total")
    )
    per_user = [
        {
            "user_id": row["user_id"],
            "name": f"{row['name']} {row['last']}".strip() or row["email"],
            "total_minutes": row["total"],
        }
        for row in by_user
    ]

    by_task = (
        entries.values(task_id=F("task__id"))
        .annotate(total=Sum("duration_minutes"), title=F("task__title"))
        .order_by("-total")[:20]
    )
    per_task = [
        {
            "task_id": row["task_id"],
            "title": row["title"],
            "total_minutes": row["total"],
        }
        for row in by_task
    ]

    by_day = (
        entries.annotate(day=TruncDate("logged_at"))
        .values("day")
        .annotate(total=Sum("duration_minutes"))
        .order_by("day")
    )
    per_day = [
        {"date": row["day"].isoformat(), "total_minutes": row["total"]}
        for row in by_day
    ]

    return Response({
        "total_minutes": total_minutes,
        "per_user": per_user,
        "per_task": per_task,
        "per_day": per_day,
    })
