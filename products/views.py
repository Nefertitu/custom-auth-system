from typing import Any, Optional

from django.db.models import Q, QuerySet
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer

from .models import Product
from .permissions import ProductPermissions
from .serializers import ProductSerializer


class ProductViewSet(viewsets.ModelViewSet):
    """ViewSet для продуктов с разграничением прав"""

    serializer_class = ProductSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["name", "price", "created_at"]
    filterset_fields = ["is_active"]

    def get_permissions(self) -> list[permissions.BasePermission]:
        """Динамические permissions"""

        if self.action == "create":
            # Создавать может любой аутентифицированный пользователь
            return [permissions.IsAuthenticated()]
        elif self.action == "list":
            # Список могут просматривать имеющие соответствующее право, либо владельцы
            return [permissions.IsAuthenticated(), ProductPermissions.CanViewAllProducts()]
        elif self.action == "destroy":
            # Удалять могут только админы
            return [permissions.IsAuthenticated(), ProductPermissions.CanDeleteProduct()]
        else:
            # Для остальных действий (retrieve, update, partial_update)
            return [
                permissions.IsAuthenticated(),
                ProductPermissions.IsOwnerOrReadOnly(),
                ProductPermissions.CanChangePrice(),
            ]

    def get_queryset(self) -> QuerySet:
        """Фильтрация queryset в зависимости от прав"""

        queryset = super().get_queryset()
        user = self.request.user
        # Админы видят все
        if user.is_staff:
            return queryset
        # Менеджеры (c правом просмотра) видят все активные продукты
        elif user.has_perm("products.can_view_all_products"):
            return queryset.filter(is_active=True)
        # Обычные пользователи видят:
        # 1. Свои продукты (активные и неактивные)
        # 2. Все активные продукты
        return queryset.filter(Q(is_active=True) | Q(created_by=user))

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Автоматически устанавливаем created_by при создании"""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def update_quantity(self, request: Request, pk: Optional[int] = None) -> Response:
        """Изменение количества (имитация продажи/поставки)"""

        product = self.get_object()

        if not (
            product.created_by == request.user
            or request.user.is_staff
            or request.user.has_perm("products.can_change_quantity")
        ):
            raise PermissionDenied("Недостаточно прав для изменения количества")

        change = request.data.get("change", 0)

        try:
            change = int(change)
            if product.quantity + change < 0:
                return Response({"error": "Недостаточно товара на складе"}, status=status.HTTP_400_BAD_REQUEST)

            product.quantity += change
            product.save()

            return Response({"message": f"Количество изменено на {change}", "new_quantity": product.quantity})

        except ValueError:
            return Response({"error": "Неверное значение изменения"}, status=status.HTTP_400_BAD_REQUEST)
