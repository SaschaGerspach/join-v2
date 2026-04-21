from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Team, TeamMember
from .serializers import TeamSerializer, TeamCreateSerializer, TeamMemberSerializer, InviteSerializer

User = get_user_model()


def _get_team_or_404(pk, user):
    try:
        team = Team.objects.get(pk=pk)
    except (Team.DoesNotExist, ValueError, TypeError):
        return None, Response({"detail": "Team not found."}, status=status.HTTP_404_NOT_FOUND)
    if not (team.created_by_id == user.id or team.members.filter(user=user).exists() or user.is_staff):
        return None, Response({"detail": "Team not found."}, status=status.HTTP_404_NOT_FOUND)
    return team, None


def _is_team_admin(team, user):
    if user.is_staff or team.created_by_id == user.id:
        return True
    return team.members.filter(user=user, role=TeamMember.Role.ADMIN).exists()


def _serialize_team(team, user):
    return {
        "id": team.pk,
        "name": team.name,
        "created_by": team.created_by_id,
        "is_owner": team.created_by_id == user.id,
        "member_count": team.members.count() + 1,
        "created_at": team.created_at,
    }


@extend_schema(methods=["GET"], responses={200: TeamSerializer(many=True)})
@extend_schema(methods=["POST"], request=TeamCreateSerializer, responses={201: TeamSerializer})
@api_view(["GET", "POST"])
def team_list(request):
    if request.method == "GET":
        owned = Team.objects.filter(created_by=request.user)
        member_of = Team.objects.filter(members__user=request.user)
        teams = (owned | member_of).distinct().order_by("-created_at")
        return Response([_serialize_team(t, request.user) for t in teams])

    serializer = TeamCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    team = Team.objects.create(name=serializer.validated_data["name"], created_by=request.user)
    return Response(_serialize_team(team, request.user), status=status.HTTP_201_CREATED)


@extend_schema(methods=["GET"], responses={200: TeamSerializer})
@extend_schema(methods=["PATCH"], request=TeamCreateSerializer, responses={200: TeamSerializer})
@extend_schema(methods=["DELETE"], responses={204: None})
@api_view(["GET", "PATCH", "DELETE"])
def team_detail(request, pk):
    team, err = _get_team_or_404(pk, request.user)
    if err:
        return err

    if request.method == "GET":
        return Response(_serialize_team(team, request.user))

    if not _is_team_admin(team, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        name = request.data.get("name", "").strip()
        if name:
            team.name = name
            team.save(update_fields=["name"])
        return Response(_serialize_team(team, request.user))

    team.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(methods=["GET"], responses={200: TeamMemberSerializer(many=True)})
@extend_schema(methods=["POST"], request=InviteSerializer, responses={201: TeamMemberSerializer})
@api_view(["GET", "POST"])
def team_members(request, pk):
    team, err = _get_team_or_404(pk, request.user)
    if err:
        return err

    if request.method == "GET":
        members = team.members.select_related("user").all()
        result = [{"user_id": team.created_by_id, "email": team.created_by.email,
                    "first_name": team.created_by.first_name, "last_name": team.created_by.last_name,
                    "role": "owner"}]
        for m in members:
            result.append({
                "user_id": m.user_id, "email": m.user.email,
                "first_name": m.user.first_name, "last_name": m.user.last_name,
                "role": m.role,
            })
        return Response(result)

    if not _is_team_admin(team, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    serializer = InviteSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    email = serializer.validated_data["email"].strip().lower()
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

    if user == team.created_by:
        return Response({"detail": "User is the team owner."}, status=status.HTTP_400_BAD_REQUEST)

    member, created = TeamMember.objects.get_or_create(team=team, user=user, defaults={"role": TeamMember.Role.MEMBER})
    return Response({
        "user_id": member.user_id, "email": user.email,
        "first_name": user.first_name, "last_name": user.last_name,
        "role": member.role,
    }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@extend_schema(methods=["PATCH"], request=InviteSerializer, responses={200: TeamMemberSerializer})
@extend_schema(methods=["DELETE"], responses={204: None})
@api_view(["PATCH", "DELETE"])
def team_member_detail(request, pk, user_pk):
    team, err = _get_team_or_404(pk, request.user)
    if err:
        return err

    if not _is_team_admin(team, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    try:
        member = TeamMember.objects.select_related("user").get(team=team, user_id=user_pk)
    except TeamMember.DoesNotExist:
        return Response({"detail": "Member not found."}, status=status.HTTP_404_NOT_FOUND)

    if request.method == "PATCH":
        role = request.data.get("role", "").strip()
        if role in (TeamMember.Role.ADMIN, TeamMember.Role.MEMBER):
            member.role = role
            member.save(update_fields=["role"])
        return Response({
            "user_id": member.user_id, "email": member.user.email,
            "first_name": member.user.first_name, "last_name": member.user.last_name,
            "role": member.role,
        })

    member.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
