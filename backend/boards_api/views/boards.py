from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

from columns_api.models import Column
from config.serializers import DetailSerializer
from ..models import Board, BoardFavorite
from ..permissions import get_board_or_404, is_board_owner
from ..serializers import (
    BOARD_TEMPLATES,
    BoardCreateSerializer,
    BoardSerializer,
    BoardUpdateSerializer,
)


class _BoardPagination(PageNumberPagination):
    page_size = 50
    page_size_query_param = "page_size"
    max_page_size = 200


def serialize_board(board, *, is_favorite=False):
    return {
        "id": board.pk,
        "title": board.title,
        "color": board.color,
        "created_by": board.created_by_id,
        "created_at": board.created_at,
        "is_owner": True,
        "is_favorite": is_favorite,
    }


def serialize_shared_board(board, user, *, is_favorite=False, is_member=True):
    return {
        "id": board.pk,
        "title": board.title,
        "color": board.color,
        "created_by": board.created_by_id,
        "created_at": board.created_at,
        "is_owner": board.created_by == user,
        "is_favorite": is_favorite,
        "is_member": is_member,
        "team_id": board.team_id,
        "team_name": board.team.name if board.team_id else None,
    }


@extend_schema(
    methods=["GET"],
    responses={200: BoardSerializer(many=True)},
)
@extend_schema(
    methods=["POST"],
    request=BoardCreateSerializer,
    responses={201: BoardSerializer, 400: DetailSerializer},
)
@api_view(["GET", "POST"])
def board_list(request):
    if request.method == "GET":
        owned = Board.objects.filter(created_by=request.user)
        shared = Board.objects.filter(members__user=request.user)
        team_boards = Board.objects.filter(team__members__user=request.user)
        team_owned = Board.objects.filter(team__created_by=request.user)
        member_boards = (owned | shared | team_boards | team_owned).distinct()
        if request.user.is_staff:
            boards = Board.objects.select_related("team").all().order_by("-created_at")
            member_ids = set(member_boards.values_list("pk", flat=True))
        else:
            boards = member_boards.select_related("team").order_by("-created_at")
            member_ids = None
        fav_ids = set(
            BoardFavorite.objects.filter(user=request.user).values_list("board_id", flat=True)
        )
        paginator = _BoardPagination()
        page = paginator.paginate_queryset(boards, request)
        result = [
            serialize_shared_board(
                b, request.user,
                is_favorite=b.pk in fav_ids,
                is_member=member_ids is None or b.pk in member_ids,
            )
            for b in page
        ]
        return paginator.get_paginated_response(result)

    serializer = BoardCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    team_id = serializer.validated_data.get("team_id")
    team = None
    if team_id:
        from teams_api.models import Team
        try:
            team = Team.objects.get(pk=team_id)
            from teams_api.views import _is_team_admin
            if not _is_team_admin(team, request.user):
                team = None
        except Team.DoesNotExist:
            pass
    with transaction.atomic():
        board = Board.objects.create(title=serializer.validated_data["title"], created_by=request.user, team=team)
        template = serializer.validated_data.get("template", "kanban")
        columns = BOARD_TEMPLATES.get(template, BOARD_TEMPLATES["kanban"])
        Column.objects.bulk_create([
            Column(board=board, title=t, order=i) for i, t in enumerate(columns)
        ])
    return Response(serialize_board(board), status=status.HTTP_201_CREATED)


@extend_schema(
    methods=["GET"],
    responses={200: BoardSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["PATCH"],
    request=BoardUpdateSerializer,
    responses={200: BoardSerializer, 403: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 403: DetailSerializer, 404: DetailSerializer},
)
@api_view(["GET", "PATCH", "DELETE"])
def board_detail(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    is_fav = BoardFavorite.objects.filter(board=board, user=request.user).exists()

    if request.method == "GET":
        return Response(serialize_shared_board(board, request.user, is_favorite=is_fav))

    if not is_board_owner(board, request.user):
        return Response({"detail": "Only the owner can modify this board."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        serializer = BoardUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        data = serializer.validated_data
        changed_fields = []
        if "title" in data:
            board.title = data["title"]
            changed_fields.append("title")
        if "color" in data:
            board.color = data["color"]
            changed_fields.append("color")
        if "team_id" in data:
            if data["team_id"] is None:
                board.team = None
            else:
                from teams_api.models import Team
                try:
                    t = Team.objects.get(pk=data["team_id"])
                    from teams_api.views import _is_team_admin
                    if _is_team_admin(t, request.user):
                        board.team = t
                    else:
                        return Response({"detail": "Not a member of this team."}, status=status.HTTP_403_FORBIDDEN)
                except Team.DoesNotExist:
                    return Response({"detail": "Team not found."}, status=status.HTTP_404_NOT_FOUND)
            changed_fields.append("team")
        if changed_fields:
            board.save(update_fields=changed_fields)
        return Response(serialize_shared_board(board, request.user, is_favorite=is_fav))

    board.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
