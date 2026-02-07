from django.contrib.auth.models import Permission
from rest_framework import serializers

from authentication.models import User


class UserPermissionSerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    permission_id = serializers.IntegerField()

    def validate(self, data: dict) -> dict:
        """Проверка существования пользователя и наличия у него прав"""
        try:
            user = User.objects.get(id=data["user_id"])
        except User.DoesNotExist:
            raise serializers.ValidationError({"user_id": "Пользователь не найден"})

        try:
            permission = Permission.objects.get(id=data["permission_id"])
        except Permission.DoesNotExist:
            raise serializers.ValidationError({"permission_id": "Право не найдено"})

        data["user"] = user
        data["permission"] = permission

        return data
