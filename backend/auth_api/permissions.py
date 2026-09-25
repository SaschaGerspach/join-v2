from rest_framework.permissions import BasePermission

GUEST_FORBIDDEN_DETAIL = "This feature is not available in the guest demo."


# Guests are anonymous and unaccountable, so features that cost money, store files,
# reach external systems or reveal other users' accounts are closed to them.
class IsNotGuest(BasePermission):
    message = GUEST_FORBIDDEN_DETAIL

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and not request.user.is_guest)
