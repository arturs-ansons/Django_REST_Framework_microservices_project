# apps/shipping/permissions.py
from rest_framework.permissions import BasePermission

class IsJWTAdminUser(BasePermission):

    def has_permission(self, request, view):
        user = request.user
        return bool(getattr(user, "is_admin", False))
