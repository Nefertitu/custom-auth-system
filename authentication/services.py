from django.contrib.auth.hashers import check_password

from rest_framework.exceptions import AuthenticationFailed

from .models import User
from .utils import JWTUtils


class AuthService:
    """Сервис для бизнес-логики аутентификации"""

    @staticmethod
    def authenticate_user(email: str, password: str) -> User:
        """Аутентификация пользователя по email и паролю"""

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            raise AuthenticationFailed("Неверные учетные данные")

        if not check_password(password, user.password):
            raise AuthenticationFailed("Неверные учетные данные")

        return user

    @staticmethod
    def create_token_pair(user: User) -> dict[str, str]:
        """Создание пары токенов (access + refresh)"""

        access_token = JWTUtils.create_access_token(user)
        refresh_token = JWTUtils.create_refresh_token(user)

        return {
            "access": access_token,
            "refresh": refresh_token,
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict[str, str]:
        """Обновление access токена по refresh токену"""

        try:
            payload = JWTUtils.verify_token(refresh_token, "refresh")

            user_id = payload.get("sub")
            user = User.objects.get(id=user_id, is_active=True)

            new_tokens = AuthService.create_token_pair(user)

            return new_tokens

        except User.DoesNotExist:
            raise AuthenticationFailed("Пользователь не найден")
        except Exception as e:
            raise AuthenticationFailed(f"Ошибка обновления токена: {str(e)}")

