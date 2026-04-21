import csv
import io
from datetime import datetime

from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, parser_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.response import Response

from columns_api.models import Column
from tasks_api.models import Label, Task

from ..permissions import can_edit_board, get_board_or_404


@extend_schema(request={"multipart/form-data": {"type": "object", "properties": {"file": {"type": "string", "format": "binary"}}}}, responses={200: None})
@api_view(["POST"])
@parser_classes([MultiPartParser])
def board_import_csv(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err
    if not can_edit_board(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    file = request.FILES.get("file")
    if not file:
        return Response({"detail": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        text = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return Response({"detail": "File must be UTF-8 encoded."}, status=status.HTTP_400_BAD_REQUEST)

    reader = csv.DictReader(io.StringIO(text))
    required = {"Title"}
    if not required.issubset(set(reader.fieldnames or [])):
        return Response({"detail": "CSV must contain a 'Title' column."}, status=status.HTTP_400_BAD_REQUEST)

    column_cache = {}
    for col in board.columns.all():
        column_cache[col.title.lower()] = col

    label_cache = {}
    for lb in board.labels.all():
        label_cache[lb.name.lower()] = lb

    max_order = Task.objects.filter(board=board).count()
    created = 0

    for row in reader:
        title = (row.get("Title") or "").strip()
        if not title:
            continue

        col_name = (row.get("Column") or "").strip()
        column = None
        if col_name:
            key = col_name.lower()
            if key not in column_cache:
                order = len(column_cache)
                column_cache[key] = Column.objects.create(board=board, title=col_name, order=order)
            column = column_cache[key]

        priority = (row.get("Priority") or "medium").strip().lower()
        if priority not in ("low", "medium", "high", "urgent"):
            priority = "medium"

        due_date = None
        raw_date = (row.get("Due Date") or "").strip()
        if raw_date:
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%m/%d/%Y"):
                try:
                    due_date = datetime.strptime(raw_date, fmt).date()
                    break
                except ValueError:
                    continue

        recurrence = (row.get("Recurrence") or "").strip().lower() or None
        if recurrence and recurrence not in ("daily", "weekly", "biweekly", "monthly"):
            recurrence = None

        task = Task.objects.create(
            board=board,
            column=column,
            title=title,
            priority=priority,
            due_date=due_date,
            recurrence=recurrence,
            order=max_order,
        )
        max_order += 1

        label_names = [n.strip() for n in (row.get("Labels") or "").split(",") if n.strip()]
        for name in label_names:
            key = name.lower()
            if key not in label_cache:
                label_cache[key] = Label.objects.create(board=board, name=name)
            task.labels.add(label_cache[key])

        created += 1

    return Response({"imported": created})
