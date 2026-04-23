from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from boards_api.permissions import get_board_or_404
from config.serializers import DetailSerializer
from .serializers import ActivityEntrySerializer


def serialize_entry(entry):
    user = entry.user
    if user:
        user_name = f"{user.first_name} {user.last_name}".strip() or user.email
    else:
        user_name = "Deleted user"
    return {
        "id": entry.pk,
        "user_name": user_name,
        "action": entry.action,
        "entity_type": entry.entity_type,
        "entity_title": entry.entity_title,
        "details": entry.details,
        "created_at": entry.created_at,
    }


@extend_schema(
    parameters=[OpenApiParameter(name="board", type=int, required=True, location=OpenApiParameter.QUERY)],
    responses={200: ActivityEntrySerializer(many=True), 400: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET"])
def activity_list(request):
    board_id = request.query_params.get("board")

    if not board_id:
        return Response({"detail": "board query parameter is required."}, status=status.HTTP_400_BAD_REQUEST)

    board, err = get_board_or_404(board_id, request.user)
    if err:
        return err

    PAGE_SIZE = 50
    before = request.query_params.get("before")
    qs = board.activity.select_related("user").order_by("-created_at")
    if before:
        qs = qs.filter(pk__lt=before)
    entries = list(qs[:PAGE_SIZE + 1])
    has_more = len(entries) > PAGE_SIZE
    entries = entries[:PAGE_SIZE]
    result = [serialize_entry(e) for e in entries]
    return Response({"results": result, "has_more": has_more})
