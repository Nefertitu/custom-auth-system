from datetime import datetime
from typing import Any, Optional

import jwt
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from config import settings

from .models import BlacklistedToken, User
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
    def create_token_pair(user: User) -> dict[str, Any]:
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

        if BlacklistedToken.is_blacklisted(refresh_token):
            raise AuthenticationFailed("Токен отозван")

        try:
            payload: dict[str, Any] = JWTUtils.verify_refresh_token(refresh_token, "refresh")

            user_id = payload.get("sub")
            if not user_id:
                raise AuthenticationFailed("Токен не содержит идентификатор пользователя")

            user = User.objects.get(id=user_id, is_active=True)

            TokenBlacklistService.add_to_blacklist(refresh_token, user)

            new_tokens = AuthService.create_token_pair(user)

            return new_tokens

        except User.DoesNotExist:
            raise AuthenticationFailed("Пользователь не найден")
        except Exception as e:
            raise AuthenticationFailed(f"Ошибка обновления токена: {str(e)}")

    @staticmethod
    def logout_user(user: User, refresh_token: Optional[str] = None) -> bool:
        """Выход пользователя c записью refresh-токена в black list"""

        if refresh_token:
            TokenBlacklistService.add_to_blacklist(refresh_token, user)
            print(f"Выход выполнен, refresh токен {refresh_token} добавлен в черный список")

        return True


class TokenBlacklistService:
    """Сервис для управления черным списком токенов"""

    @staticmethod
    def add_to_blacklist(token: Optional[str], user: Optional["User"] = None) -> bool | Any:
        """Добавление токена в черный список"""

        if token is None:
            print("DEBUG: Token is None, cannot add to blacklist")
            return False

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=settings.JWT_ALGORITHM,
                audience=settings.JWT_AUDIENCE,
                issuer=settings.JWT_ISSUER,
                options={"verify_exp": False},  # НE проверять срок действия токена
            )

            expires_at = datetime.fromtimestamp(payload.get("exp", 0))

            BlacklistedToken.objects.create(
                token=token, user=user or User.objects.get(id=payload.get("sub")), expires_at=expires_at
            )

            return True

        except Exception as e:
            print(f"DEBUG: Error adding to blacklist: {e}")
            return False

    @staticmethod
    def cleanup_expired() -> int:
        """Очистка устаревших записей из blacklist и подсчет их количества"""

        expired_tokens = BlacklistedToken.objects.filter(expires_at__lt=timezone.now())

        count = expired_tokens.count()

        expired_tokens.delete()

        return count
