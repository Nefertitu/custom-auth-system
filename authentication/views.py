import uuid
from datetime import datetime

import jwt
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from rest_framework import permissions
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from urllib3 import request

from .models import User
from config import settings
from .services import AuthService


class CustomLoginView(APIView):
    """
    Кастомный логин, возвращающий JWT токен.
    Заменяет TokenObtainPairView.
    """
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = AuthService.authenticate_user(email=email, password=password)

        tokens = AuthService.create_token_pair(user)

        user.last_login = datetime.now()
        user.save(update_fields=["last_login"])

        return Response({
            'user': {
                'id': user.pk,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
            },
            'tokens': tokens,
            'message': 'Вход выполнен успешно'
        })

        # return Response({
        #     'user': UserSerializer(user).data,
        #     'access': access_token,
        #     'refresh': refresh_token,
        #     'token_type': 'Bearer',
        #     'expires_in': settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME', 300)
        # })


class CustomRefreshTokenView(APIView):
    """Кастомное обновление access токена по refresh токену"""
    
    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        
        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]
        new_tokens = AuthService.refresh_access_token(refresh_token)

        return Response({
            "access": new_tokens["access"],
            "refresh": new_tokens["refresh"],
            "message": "Токен обновлен"
        })


class CustomLogoutView(APIView):
    """Эндпоинт для выхода из системы"""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:

        refresh_token = request.data.get("refresh")

        # 2. Вызываем сервис выхода
        AuthService.logout_user(refresh_token)

        # 3. Ответ
        return Response({
            'message': 'Выход выполнен успешно'
        })