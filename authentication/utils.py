import uuid
from typing import Any

import jwt
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from authentication.models import BlacklistedToken, User
from config import settings


class JWTUtils:
    """Утилиты для работы с JWT токенами"""

    @staticmethod
    def create_access_token(user: User) -> str:
        """Создание access токена"""

        # now = timezone.localtime()
        # print(now)

        payload = {
            # Стандартные claims
            "sub": str(user.pk),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "exp": timezone.now() + settings.JWT_ACCESS_TOKEN_LIFETIME,
            "iat": timezone.now(),
            "jti": str(uuid.uuid4()),
            # Кастомные claims
            "type": "access",
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_manager": user.is_manager,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        return token

    @staticmethod
    def create_refresh_token(user: User) -> str:
        """Создание refresh токена"""

        payload = {
            # Стандартные claims
            "sub": str(user.pk),
            "iss": settings.JWT_ISSUER,
            "aud": settings.JWT_AUDIENCE,
            "exp": timezone.now() + settings.JWT_ACCESS_TOKEN_LIFETIME,
            "iat": timezone.now(),
            "jti": str(uuid.uuid4()),
            # Кастомные claims
            "type": "refresh",
            "email": user.email,
        }

        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
        print(f"DEBUG: создан refresh токен {token}")

        return token

    @staticmethod
    def verify_access_token(token: str, token_type: str = "access") -> dict[str, Any] | Any:
        """Верификация access токена"""

        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
                options={
                    "require": ["exp", "iat", "sub", "jti", "type"],
                    "verify_exp": True,
                    "verify_iat": True,
                    "verify_iss": settings.JWT_ISSUER is not None,
                    "verify_aud": settings.JWT_AUDIENCE is not None,
                },
            )

            if payload.get("type") != token_type:
                raise AuthenticationFailed(f"Неверный тип токена: {payload.get("type")}")

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Access токен истек")
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f"Невалидный access токен: {str(e)}")

    @staticmethod
    def verify_refresh_token(refresh_token: str, token_type: str = "refresh") -> dict[str, str] | Any:
        """Верификация refresh токена"""

        if BlacklistedToken.is_blacklisted(refresh_token):
            raise AuthenticationFailed("Токен отозван")

        try:
            payload = jwt.decode(
                refresh_token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM],
                issuer=settings.JWT_ISSUER,
                audience=settings.JWT_AUDIENCE,
                options={"verify_exp": True},
            )

            if payload.get("type") != token_type:
                raise AuthenticationFailed(f"Неверный тип токена: {payload.get("type")}")

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Refresh токен истек")
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f"Невалидный refresh токен: {str(e)}")
