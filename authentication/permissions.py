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

    def has_object_permission(self, request: Request, view: View, obj: HasOwner) -> bool:
        """Пользователь может читать/редактировать только свой профиль"""
        return obj == request.user


class CanViewAllUsers(permissions.BasePermission):
    """Право на просмотр всех пользователей"""

    def has_permission(self, request: Request, view: View) -> bool:
        """Проверка права на уровне запроса"""

        action = getattr(view, "action", None)

        if action == "list":
            if not request.user.has_perm("authentication.can_view_all_users"):
                raise PermissionDenied("Недостаточно прав для просмотра списка пользователей")

        return True

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Проверка права на уровне объекта"""

        action = getattr(view, "action", None)

        if action == "retrieve":
            return request.user.has_perm("authentication.can_view_all_users") or obj == request.user
        return True


class CanDeleteUser(permissions.BasePermission):
    """Право на удаление пользователей"""

    def has_permission(self, request: Request, view: View) -> bool:
        """Право на уровне запроса"""

        action = getattr(view, "action", None)

        if action == "destroy":
            if not request.user.has_perm("authentication.can_delete_user"):
                raise PermissionDenied("Недостаточно прав для удаления")

        return True

    def has_object_permission(self, request: Request, view: View, obj: Any) -> bool:
        """Право на уровне объекта"""

        if obj == request.user:
            raise PermissionDenied("Нельзя удалить свой собственный аккаунт")

        action = getattr(view, "action", None)
        if action == "destroy":
            return request.user.has_perm("authentication.can_delete_user")

        return True
