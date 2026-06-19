from django.contrib.auth import get_user_model
from django.db.models import Count
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Team, TeamMember
from audit_api.helpers import log_audit
from .serializers import TeamSerializer, TeamCreateSerializer, TeamMemberSerializer, InviteSerializer

User = get_user_model()


def _is_team_member(team, user):
    return team.created_by_id == user.id or team.members.filter(user=user).exists()


def _get_team_or_404(pk, user):
    try:
        team = Team.objects.get(pk=pk)
    except (Team.DoesNotExist, ValueError, TypeError):
        return None, Response({"detail": "Team not found."}, status=status.HTTP_404_NOT_FOUND)
    # Only a superuser has a cross-team override; is_staff (platform admin) does not.
    if not (_is_team_member(team, user) or user.is_superuser):
        return None, Response({"detail": "Team not found."}, status=status.HTTP_404_NOT_FOUND)
    return team, None


def _is_team_admin(team, user):
    if user.is_superuser or team.created_by_id == user.id:
        return True
    return team.members.filter(user=user, role=TeamMember.Role.ADMIN).exists()


def _serialize_team(team, user):
    member_count = getattr(team, '_member_count', None)
    if member_count is None:
        member_count = team.members.count()
    return {
        "id": team.pk,
        "name": team.name,
        "created_by": team.created_by_id,
        "is_owner": team.created_by_id == user.id,
        "member_count": member_count + 1,
        "created_at": team.created_at,
    }


@extend_schema(methods=["GET"], responses={200: TeamSerializer(many=True)})
@extend_schema(methods=["POST"], request=TeamCreateSerializer, responses={201: TeamSerializer})
@api_view(["GET", "POST"])
def team_list(request):
    if request.method == "GET":
        owned = Team.objects.filter(created_by=request.user)
        member_of = Team.objects.filter(members__user=request.user)
        teams = (owned | member_of).distinct().annotate(_member_count=Count("members")).order_by("-created_at")
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
        # Audit the superuser cross-team override (emergency key, not a normal visit).
        if request.user.is_superuser and not _is_team_member(team, request.user):
            log_audit(
                "superuser_team_access",
                user=request.user,
                request=request,
                detail=f"Accessed team #{team.pk} '{team.name}'",
            )
        return Response(_serialize_team(team, request.user))

    if not _is_team_admin(team, request.user):
        return Response({"detail": "Permission denied."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == "PATCH":
        name = request.data.get("name", "").strip()
        if not name:
            return Response({"detail": "Name is required."}, status=status.HTTP_400_BAD_REQUEST)
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
        owner = team.created_by
        result = [{"user_id": owner.pk, "email": owner.email,
                    "first_name": owner.first_name, "last_name": owner.last_name,
                    "role": "owner",
                    "avatar_url": request.build_absolute_uri(owner.avatar.url) if owner.avatar else None}]
        for m in members:
            result.append({
                "user_id": m.user_id, "email": m.user.email,
                "first_name": m.user.first_name, "last_name": m.user.last_name,
                "role": m.role,
                "avatar_url": request.build_absolute_uri(m.user.avatar.url) if m.user.avatar else None,
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
    if created:
        log_audit("team_member_added", user=request.user, request=request, detail=f"team={team.pk} invited={user.email}")
    return Response({
        "user_id": member.user_id, "email": user.email,
        "first_name": user.first_name, "last_name": user.last_name,
        "role": member.role,
        "avatar_url": request.build_absolute_uri(user.avatar.url) if user.avatar else None,
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
            old_role = member.role
            member.role = role
            member.save(update_fields=["role"])
            log_audit("team_member_role_changed", user=request.user, request=request, detail=f"team={team.pk} user={member.user.email} {old_role}->{role}")
        return Response({
            "user_id": member.user_id, "email": member.user.email,
            "first_name": member.user.first_name, "last_name": member.user.last_name,
            "role": member.role,
            "avatar_url": request.build_absolute_uri(member.user.avatar.url) if member.user.avatar else None,
        })

    log_audit("team_member_removed", user=request.user, request=request, detail=f"team={team.pk} removed={member.user.email}")
    member.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
