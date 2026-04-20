from django.conf import settings
from django.contrib.auth import get_user_model
from config.mail import send_mail_async
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from config.serializers import DetailSerializer
from ..models import Board, BoardMember
from ..permissions import get_board_or_404
from ..serializers import BoardMemberInviteSerializer, BoardMemberSerializer

User = get_user_model()


@extend_schema(
    methods=["GET"],
    responses={200: BoardMemberSerializer(many=True), 404: DetailSerializer},
)
@extend_schema(
    methods=["POST"],
    request=BoardMemberInviteSerializer,
    responses={
        201: BoardMemberSerializer,
        400: DetailSerializer,
        403: DetailSerializer,
        404: DetailSerializer,
    },
)
@api_view(["GET", "POST"])
def board_members(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    if request.method == "GET":
        members = board.members.select_related("user").all()
        return Response([{
            "user_id": m.user_id,
            "email": m.user.email,
            "first_name": m.user.first_name,
            "last_name": m.user.last_name,
            "invited_at": m.invited_at,
        } for m in members])

    if board.created_by != request.user:
        return Response({"detail": "Only the owner can invite members."}, status=status.HTTP_403_FORBIDDEN)

    serializer = BoardMemberInviteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    email = serializer.validated_data["email"].lower()

    if email == request.user.email:
        return Response({"detail": "You cannot invite yourself."}, status=status.HTTP_400_BAD_REQUEST)

    try:
        invitee = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "No user found with that email."}, status=status.HTTP_404_NOT_FOUND)

    _, created = BoardMember.objects.get_or_create(board=board, user=invitee)
    if not created:
        return Response({"detail": "User is already a member."}, status=status.HTTP_400_BAD_REQUEST)

    inviter = (request.user.first_name or request.user.email).replace('\n', '').replace('\r', '')
    board_title = board.title.replace('\n', '').replace('\r', '')
    send_mail_async(
        subject="You've been invited to a board — Join",
        message=(
            f"{inviter} invited you to the board "
            f'"{board_title}" on Join.\n\n'
            f"Log in to access it: {settings.FRONTEND_URL}/boards/{board.pk}"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitee.email],
    )

    return Response({
        "user_id": invitee.pk,
        "email": invitee.email,
        "first_name": invitee.first_name,
        "last_name": invitee.last_name,
    }, status=status.HTTP_201_CREATED)


@extend_schema(responses={204: None, 403: DetailSerializer, 404: DetailSerializer})
@api_view(["DELETE"])
def board_leave(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    if board.created_by == request.user:
        return Response({"detail": "The owner cannot leave the board."}, status=status.HTTP_403_FORBIDDEN)

    deleted, _ = BoardMember.objects.filter(board=board, user=request.user).delete()
    if not deleted:
        return Response({"detail": "Not a member."}, status=status.HTTP_404_NOT_FOUND)

    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(responses={204: None, 404: DetailSerializer})
@api_view(["DELETE"])
def board_member_detail(request, pk, user_pk):
    try:
        board = Board.objects.get(pk=pk, created_by=request.user)
    except Board.DoesNotExist:
        return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

    try:
        member = BoardMember.objects.get(board=board, user_id=user_pk)
    except BoardMember.DoesNotExist:
        return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

    member.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
