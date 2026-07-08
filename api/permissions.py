"""DRF permission classes mirroring the web app's role checks."""

from rest_framework.permissions import BasePermission


class IsSuperadmin(BasePermission):
    message = 'Super Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_superadmin)


class CanAddDarood(BasePermission):
    """Managers and super admins may record darood / review submissions."""

    message = 'Manager or Super Admin access required.'

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.can_add_darood)
