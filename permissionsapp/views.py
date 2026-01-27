from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response

from authentication.models import User
from permissionsapp.serializers import UserPermissionSerializer


class PermissionManagementViewSet(viewsets.ViewSet):
    """API для управления правами пользователей (только для админов)"""

    permission_classes = [permissions.IsAdminUser]

    def list(self, request: Request) -> Response:
        """Отображает доступные методы API"""
        return Response(
            {
                "available_methods": {
                    "GET": {
                        "available_permissions": "/api/permissions/available_permissions/",
                        "user_permissions": "/api/permissions/user_permissions/?user_id={id}",
                    },
                    "POST": {
                        "grant_permission": "/api/permissions/grant_permission/",
                        "revoke_permission": "/api/permissions/revoke_permission/",
                    },
                }
            }
        )

    @action(detail=False, methods=["get"])
    def available_permissions(self, request: Request) -> Response:
        """Список всех доступных прав в системе"""

        content_types = ContentType.objects.filter(model__in=["product", "user"])
        permissions = Permission.objects.filter(content_type__in=content_types)

        data = []
        for perm in permissions:
            data.append(
                {"id": perm.pk, "name": perm.name, "codename": perm.codename, "content_type": perm.content_type.model}
            )

        return Response(data)

    @action(detail=False, methods=["get"])
    def user_permissions(self, request: Request) -> Response:
        """Получить права конкретного пользователя"""

        user_id = request.query_params.get("user_id")
        if not user_id:
            return Response({"error": "Укажите user_id"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
            permissions = user.user_permissions.all()

            data = []
            for perm in permissions:
                data.append({"id": perm.id, "name": perm.name, "codename": perm.codename})

            return Response({"user_id": user.pk, "email": user.email, "permissions": data})

        except User.DoesNotExist:
            return Response({"error": "Пользователь не найден"}, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["post"])
    def grant_permission(self, request: Request) -> Response:
        """Назначить право пользователю"""

        serializer = UserPermissionSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            permission = serializer.validated_data["permission"]

            user.user_permissions.add(permission)
            user.save()

            return Response({"message": f"Право '{permission.name}' выдано пользователю {user.email}"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"])
    def revoke_permission(self, request: Request) -> Response:
        """Отозвать право у пользователя"""

        serializer = UserPermissionSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data["user"]
            permission = serializer.validated_data["permission"]

            user.user_permissions.remove(permission)
            user.save()

            return Response({"message": f"Право '{permission.name}' отозвано у пользователя {user.email}"})

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
