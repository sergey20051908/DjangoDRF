from rest_framework.permissions import BasePermission


class IsModer(BasePermission):
    """Разрешение для модераторов"""

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.groups.filter(name="moderators").exists()


class NotModer(IsModer):
    """Разрешение, запрещающее модераторам"""
    def has_permission(self, request, view):
        return not super().has_permission(request, view)