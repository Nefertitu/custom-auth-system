from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

from .models import User
from .utils import JWTUtils
from .models import User


class JWTAuthenticationBackend(authentication.BaseAuthentication):
    """
    Кастомный бэкенд аутентификации по JWT токену.
    Используется в settings.py: DEFAULT_AUTHENTICATION_CLASSES
    """

    def authenticate(self, request: Request) -> tuple[User, str] | None:
       """Аутентификация пользователя и передача данных в 'request'"""

       auth_header = request.headers.get("Authorization")

       if not auth_header:
            return None

       try:
           scheme, token = auth_header.split()
       except ValueError:
           return None

       if scheme.lower() != "bearer":
           return None

       try:
           payload = JWTUtils.verify_token(token, "access")

           user_id = payload.get("sub")
           user = User.objects.get(id=user_id, is_active=True)

           request.jwt_payload = payload

           return user, token

       except User.DoesNotExist:
           raise AuthenticationFailed("Пользователь не найден")
       except Exception:
           return None

    def authenticate_header(self, request):
        """Возвращает значение для заголовка WWW-Authenticate"""
        return 'Bearer realm="api"'