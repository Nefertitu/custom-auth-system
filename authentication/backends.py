from rest_framework import authentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request

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
           parts = auth_header.split()
           if len(parts) != 2:
               print(f"DEBUG: Invalid header format: {auth_header}")
               return None

           scheme, token = parts
           if scheme.lower() != "bearer":
               print(f"DEBUG: Invalid scheme: {scheme}")
               return None
       except Exception as e:
            print(f"DEBUG: Error parsing header: {e}")
            return None

       try:
           payload = JWTUtils.verify_access_token(token, "access")

           user_id = payload.get("sub")
           if not user_id:
               print("DEBUG: No 'sub' in payload")
               return None

           user = User.objects.get(id=user_id, is_active=True)

           request.jwt_payload = payload

           return (user, token)

       except User.DoesNotExist:
           raise AuthenticationFailed("Пользователь не найден")
       except Exception as e:
           print(f"DEBUG: Unexpected error: {str(e)}")
           return None

    def authenticate_header(self, request: Request):
        """Возвращает значение для заголовка WWW-Authenticate"""
        return 'Bearer realm="api"'