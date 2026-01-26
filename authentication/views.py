from datetime import datetime
from typing import Any, List

from django.db.models import QuerySet
from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from .models import User
from .permissions import IsSelfOnly, CanViewAllUsers, CanDeleteUsers
from .serializers import LoginSerializer, RefreshTokenSerializer, UserProfileSerializer, UserCreateSerializer, \
    ChangePasswordSerializer, LogoutSerializer
from .services import AuthService, TokenBlacklistService


class UserCreateApiView(CreateAPIView):
    """Класс для создания профиля пользователя"""

    serializer_class = UserCreateSerializer
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer: BaseSerializer[Any]) -> None:
        """Метод для создания профиля пользователя (POST /register/)"""

        serializer.save(is_active=True)


class UserProfileViewSet(viewsets.ModelViewSet):
    """Управление пользователями (требуется аутентификация)"""

    serializer_class = UserProfileSerializer
    queryset = User.objects.all()

    def get_permissions(self) -> List[permissions.BasePermission]:
        """
        Управление разрешениями:
        (GET /users/        # Список (общий только админы, аутентифицированные пользователи свой)
        GET /users/{id}/    # Просмотр (только владелец)
        PUT /users/{id}/    # Полное обновление (только владелец)
        PATCH /users/{id}/  # Частичное обновление (только владелец)
        DELETE /users/{id}/ # Удаление (только админы)
        )
        """

        if self.action == "create":
            return [permissions.AllowAny()]
        elif self.action in ["retrieve", "update", "partial_update"]:
            return [permissions.IsAuthenticated(), IsSelfOnly()]

        elif self.action == "list":
            return [permissions.IsAuthenticated(), CanViewAllUsers()]

        elif self.action == "destroy":
            return [permissions.IsAuthenticated(), CanDeleteUsers()]

        else:
            return [permissions.IsAuthenticated()]

    def get_queryset(self) -> QuerySet[User]:
        """Фильтрация - пользователь видит только себя, админ всех"""

        if self.request.user.has_perm("users.view_all_users"):
            return User.objects.all()
        return User.objects.filter(pk=self.request.user.id)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsSelfOnly])
    def change_password(self, request, pk=None):
        """Смена пароля пользователя"""

        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response(
                    {"old_password": ["Неверный текущий пароль"]},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            new_tokens = AuthService.create_token_pair(user=user)

            return Response({
                "message": "Пароль успешно изменен",
                "access": new_tokens.get("access"),
                "refresh": new_tokens.get("refresh")
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(APIView):
    """
    Кастомный логин, возвращающий JWT токен.
    (Заменяет TokenObtainPairView)
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
            "user": {
                "id": user.pk,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "tokens": tokens,
            "message": "Вход выполнен успешно"
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

        try:
            new_tokens = AuthService.refresh_access_token(refresh_token)

            return Response({
                "access": new_tokens["access"],
                "refresh": new_tokens["refresh"],
                "message": "Токен обновлен"
            })

        except AuthenticationFailed as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_401_UNAUTHORIZED
            )


class CustomLogoutView(APIView):
    """Эндпоинт для выхода из системы"""

    permission_classes = [permissions.IsAuthenticated]

    next_page = "/"

    def post(self, request: Request) -> Response:

        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get("refresh")

        if refresh_token:
            TokenBlacklistService.add_to_blacklist(
                token=refresh_token,
                user=request.user,
            )

        AuthService.logout_user(refresh_token)

        return Response({
            "message": "Выход выполнен успешно" +
                       (f" refresh токен ({refresh_token}) отозван" if refresh_token else "")
        })