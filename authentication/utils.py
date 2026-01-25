import uuid

import jwt
from django.utils import timezone
from rest_framework.exceptions import AuthenticationFailed

from authentication.models import User
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
            "token_type": "access",
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "is_manager": user.is_manager,
            "is_staff": user.is_staff,
            "is_superuser": user.is_superuser,
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm="HS256"
        )

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
            "token_type": "refresh",
            "email": user.email,
        }

        return jwt.encode(
            payload,
            settings.JWT_SECRET_KEY,
            algorithm=settings.JWT_ALGORITHM
        )

    @staticmethod
    def verify_token(token, token_type="access"):
        """Верификация токена"""

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
                    "verify_iss": True,
                    "verify_aud": True,
                }
            )

            if payload.get("type") != token_type:
                raise AuthenticationFailed(f"Неверный тип токена: {payload.get("type")}")

            return payload

        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed("Токен истек")
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f"Невалидный токен: {str(e)}")
