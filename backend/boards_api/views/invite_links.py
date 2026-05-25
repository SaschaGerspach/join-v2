import secrets

from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from ..models import Board, BoardInviteLink, BoardMember
from ..permissions import get_board_or_404, can_manage_members


@api_view(["GET", "POST", "DELETE"])
def board_invite_link(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    if not can_manage_members(board, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "GET":
        try:
            link = board.invite_link
            return Response({"token": link.token})
        except BoardInviteLink.DoesNotExist:
            return Response({"token": None})

    if request.method == "POST":
        link, created = BoardInviteLink.objects.get_or_create(
            board=board,
            defaults={"token": secrets.token_urlsafe(32), "created_by": request.user},
        )
        if not created:
            link.token = secrets.token_urlsafe(32)
            link.save(update_fields=["token"])
        return Response({"token": link.token}, status=status.HTTP_201_CREATED)

    BoardInviteLink.objects.filter(board=board).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST"])
def board_join_via_link(request, token):
    try:
        link = BoardInviteLink.objects.select_related("board").get(token=token)
    except BoardInviteLink.DoesNotExist:
        return Response({"detail": "Invalid or expired invite link."}, status=status.HTTP_404_NOT_FOUND)

    board = link.board
    _, created = BoardMember.objects.get_or_create(board=board, user=request.user)
    return Response({
        "board_id": board.pk,
        "board_title": board.title,
        "already_member": not created,
    })
