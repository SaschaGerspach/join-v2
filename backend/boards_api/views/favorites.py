from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from config.serializers import DetailSerializer
from ..models import BoardFavorite
from ..permissions import get_board_or_404


@extend_schema(
    methods=["POST"],
    responses={201: DetailSerializer, 404: DetailSerializer},
)
@extend_schema(
    methods=["DELETE"],
    responses={204: None, 404: DetailSerializer},
)
@api_view(["POST", "DELETE"])
def board_favorite(request, pk):
    board, err = get_board_or_404(pk, request.user)
    if err:
        return err

    if request.method == "POST":
        BoardFavorite.objects.get_or_create(board=board, user=request.user)
        return Response({"detail": "Board favorited."}, status=status.HTTP_201_CREATED)

    BoardFavorite.objects.filter(board=board, user=request.user).delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
