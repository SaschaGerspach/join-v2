import csv
import io

from drf_spectacular.utils import extend_schema
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.http import HttpResponse

from ..permissions import get_board_or_404


@extend_schema(responses={(200, "text/csv"): bytes})
@api_view(["GET"])
def board_export_csv(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    tasks = (
        board.tasks.filter(archived_at__isnull=True)
        .select_related("column")
        .prefetch_related("assignees", "labels")
        .order_by("column__order", "order")
    )

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Title", "Column", "Priority", "Assignees", "Due Date", "Labels", "Recurrence"])

    for task in tasks:
        assignees = ", ".join(
            f"{a.first_name} {a.last_name}".strip() for a in task.assignees.all()
        )
        labels = ", ".join(l.name for l in task.labels.all())
        writer.writerow([
            task.title,
            task.column.title if task.column else "",
            task.priority,
            assignees,
            task.due_date or "",
            labels,
            task.recurrence or "",
        ])

    response = HttpResponse(buf.getvalue(), content_type="text/csv; charset=utf-8")
    filename = f"{board.title.replace(' ', '_')}_export.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
