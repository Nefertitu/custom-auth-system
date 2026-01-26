from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для модели Пользователь"""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "password",
            "password_confirm",
            "first_name",
            "last_name",
            "middle_name",
            "full_name",
            "created_at"
        )
        extra_kwargs = {
            "password": {"write_only": True},
            "first_name": {"required": True},
        }

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Проверка на совпадение паролей"""

        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Пароли не совпадают."}
            )
        # Удаляем password_confirm из данных
        attrs.pop("password_confirm")
        return attrs

    def create(self, validated_data: dict) -> User:
        """Хеширование пароля перед сохранением"""

        password = validated_data.pop("password")
        user = User.objects.create(
            email=validated_data["email"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            middle_name=validated_data.get("last_name", ""),
        )
        user.set_password(password)
        user.save()
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    """Сериализатор для просмотра и обновления профиля"""

    class Meta:
        model = User
        fields = (
            "id",
            "email",
            "first_name",
            "last_name",
            "middle_name",
            "created_at",
            "updated_at"
        )

        read_only_fields = [
            "id", "email", "password"
        ]
        extra_kwargs = {
            "email": {"required": False},
            "first_name": {"required": False},
        }

    def update(self, instance: User, validated_data: dict) -> User:
        """Если пароль в данных - удаляем его"""
        password = validated_data.pop("password", None)
        return super().update(instance, validated_data)


class ChangePasswordSerializer(serializers.Serializer):
    """Отдельный сериализатор для смены пароля"""

    old_password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"}
    )
    new_password = serializers.CharField(
        required=True,
        write_only=True,
        min_length=8,
        style={"input_type": "password"}
    )
    new_password_confirm = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"}
    )

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError({"new_password_confirm": "Пароли не совпадают."})
        return attrs


class LoginSerializer(serializers.Serializer):
    """Сериализатор для логина"""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"}
    )

    def validate(self, attrs):
        """Проверка наличия email и пароля в данных"""

        email = attrs.get("email")
        password = attrs.get("password")

        if not email or not password:
            raise serializers.ValidationError("Email и пароль обязательны")

        return attrs


class RefreshTokenSerializer(serializers.Serializer):
    """Сериализатор для обновления токена"""
    refresh = serializers.CharField(required=True)


class LogoutSerializer(serializers.Serializer):
    """Сериализатор для выхода"""

    refresh = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text="Refresh токен для добавления в черный список (опционально)"
    )

    def validate(self, attrs):
        """Дополнительная валидация"""
        refresh_token = attrs.get('refresh')

        if refresh_token:
            # Проверяем, что это похоже на JWT токен
            if not refresh_token.startswith('eyJ'):
                raise serializers.ValidationError({
                    'refresh': 'Неверный формат JWT токена'
                })

            # Обрезаем пробелы
            attrs['refresh'] = refresh_token.strip()

        return attrs
