from typing import Any

from django.views import View
from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request

from .models import Product


class ProductPermissions:
    """Набор permissions для продуктов"""

    class IsOwnerOrReadOnly(permissions.BasePermission):
        """Владелец может редактировать, остальные только читать"""

        def has_object_permission(self, request: Request, view: View, obj: Product) -> Any:
            """Проверка права на уровне объекта"""

            if request.method in permissions.SAFE_METHODS:
                return True
            return obj.created_by == request.user

    class CanChangePrice(permissions.BasePermission):
        """Только менеджеры и админы могут менять цену"""

        def has_permission(self, request: Request, view: View) -> bool:
            """Проверка права на уровне запроса"""

            if request.method in ["PUT", "PATCH"]:
                if "price" in request.data:
                    return request.user.has_perm("products.can_change_price") or request.user.is_staff
            return True

        def has_object_permission(self, request: Request, view: View, obj: Product) -> bool:
            """Проверка права на уровне объекта"""

            if request.method in ["PUT", "PATCH"]:
                if "price" in request.data:
                    return request.user.has_perm("products.can_change_price") or request.user.is_staff
            return True

    class CanDeleteProduct(permissions.BasePermission):
        """Только админы могут удалять"""

        def has_permission(self, request: Request, view: View) -> bool:
            """Проверка прав на уровне запроса"""

            if request.method == "DELETE":
                if not request.user.has_perm("products.can_delete_product") or request.user.is_staff:
                    raise PermissionDenied("Недостаточно прав для удаления продукта")
            return True

    class CanViewAllProducts(permissions.BasePermission):
        """Просмотр всех продуктов (включая неактивные)"""

        def has_permission(self, request: Request, view: View) -> bool:
            """Проверка прав на уровне запроса"""

            action = getattr(view, "action", None)

            if action == "list":
                return True
            return True

        def has_object_permission(self, request: Request, view: View, obj: Product) -> bool:
            """Права на уровне конкретного продукта"""

            if request.user.is_staff:
                return True

            if request.user.has_perm("products.can_view_all_products"):
                return obj.is_active

            if obj.created_by == request.user:
                return True

            if obj.is_active:
                return True

            raise PermissionDenied("Доступ к продукту запрещен")
