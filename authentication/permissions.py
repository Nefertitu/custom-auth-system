from typing import Any, Protocol

from django.views import View
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from .models import User


class HasOwner(Protocol):
    user: User


class IsSelfOnly(permissions.BasePermission):
    """Разрешение только для владельца объекта"""

    def has_object_permission(self, request: Request, view: Any, obj: HasOwner) -> bool:
        """ "Пользователь может читать/редактировать только свой профиль"""
        return obj == request.user


class CanViewAllUsers(permissions.BasePermission):
    """Право на просмотр всех пользователей"""

    def has_permission(self, request: Request, view: View) -> bool:
        """Проверка права на уровне запроса"""

        if not request.user.has_perm("users.can_view_all_users"):
            raise PermissionDenied("Недостаточно прав для просмотра списка пользователей")
        return True

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Проверка права на уровне объекта"""
        return request.user.has_perm("users.view_all_users")


class CanDeleteUsers(permissions.BasePermission):
    """Право на удаление пользователей"""

    def has_permission(self, request: Request, view: View) -> bool:
        """Право на уровне запроса"""

        action = getattr(view, "action", None)

        if action == "destroy":
            if not request.user.has_perm("users.can_delete_users"):
                raise PermissionDenied("Недостаточно прав для удаления")
        return True

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Право на уровне объекта"""

        if request.method == "DELETE":
            return request.user.has_perm("users.can_delete_users")
        return True
