import csv
import io
import re
from datetime import date

from django.http import HttpResponse
from django.template.loader import render_to_string
from django.utils.formats import date_format
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..permissions import get_board_or_404


def _board_tasks_qs(board):
    return (
        board.tasks.filter(archived_at__isnull=True)
        .select_related("column")
        .prefetch_related("assignees", "labels")
        .order_by("column__order", "order")
    )


@extend_schema(responses={(200, "text/csv"): bytes})
@api_view(["GET"])
def board_export_csv(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    tasks = _board_tasks_qs(board)

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["Title", "Column", "Priority", "Assignees", "Due Date", "Labels", "Recurrence"])

    for task in tasks:
        assignees = ", ".join(
            f"{a.first_name} {a.last_name}".strip() for a in task.assignees.all()
        )
        labels = ", ".join(lb.name for lb in task.labels.all())
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
    safe_title = re.sub(r'[^\w\-]', '_', board.title)
    filename = f"{safe_title}_export.csv"
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


PRIORITY_COLORS = {
    "urgent": "#ff3d00",
    "high": "#ff3d00",
    "medium": "#ffa800",
    "low": "#7ae229",
}


@extend_schema(responses={(200, "application/pdf"): bytes})
@api_view(["GET"])
def board_export_pdf(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    tasks = _board_tasks_qs(board)
    columns = board.columns.order_by("order")

    columns_data = []
    for col in columns:
        col_tasks = [t for t in tasks if t.column_id == col.pk]
        columns_data.append({
            "title": col.title,
            "tasks": [
                {
                    "title": t.title,
                    "priority": t.priority,
                    "priority_color": PRIORITY_COLORS.get(t.priority, "#999"),
                    "assignees": ", ".join(
                        f"{a.first_name} {a.last_name}".strip() for a in t.assignees.all()
                    ),
                    "labels": list(t.labels.all()),
                    "due_date": t.due_date,
                    "is_overdue": t.due_date is not None and t.due_date < date.today(),
                }
                for t in col_tasks
            ],
        })

    html_string = render_to_string("boards_api/board_export_pdf.html", {
        "board": board,
        "columns": columns_data,
        "exported_at": date_format(date.today(), "DATE_FORMAT"),
    })

    try:
        from weasyprint import HTML as WeasyHTML
    except OSError:
        return Response(
            {"detail": "PDF generation is not available on this server."},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )

    pdf = WeasyHTML(string=html_string).write_pdf()

    safe_title = re.sub(r'[^\w\-]', '_', board.title)
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{safe_title}_export.pdf"'
    return response
