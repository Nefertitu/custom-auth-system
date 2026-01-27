from datetime import datetime
from typing import Any, List, Optional

from django.db.models import QuerySet
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.generics import CreateAPIView
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.serializers import BaseSerializer
from rest_framework.views import APIView

from .models import User
from .permissions import CanDeleteUsers, CanViewAllUsers, IsSelfOnly
from .serializers import (
    ChangePasswordSerializer,
    LoginSerializer,
    LogoutSerializer,
    RefreshTokenSerializer,
    UserCreateSerializer,
    UserProfileSerializer,
)
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

        user = self.request.user

        if not user.is_authenticated:
            return User.objects.none()
        if user.has_perm("users.view_all_users"):
            return User.objects.all()
        return User.objects.filter(pk=user.pk)

    @action(detail=True, methods=["post"], permission_classes=[permissions.IsAuthenticated, IsSelfOnly])
    def change_password(self, request: Request, pk: Optional[int] = None) -> Response:
        """Смена пароля пользователя"""

        user = self.get_object()
        serializer = ChangePasswordSerializer(data=request.data)

        if serializer.is_valid():
            if not user.check_password(serializer.validated_data["old_password"]):
                return Response({"old_password": ["Неверный текущий пароль"]}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(serializer.validated_data["new_password"])
            user.save()

            new_tokens = AuthService.create_token_pair(user=user)

            return Response(
                {
                    "message": "Пароль успешно изменен",
                    "access": new_tokens.get("access"),
                    "refresh": new_tokens.get("refresh"),
                }
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CustomLoginView(APIView):
    """
    Кастомный логин, возвращающий JWT токен.
    (Заменяет TokenObtainPairView)
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        """Аутентификация по email и паролю"""

        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        user = AuthService.authenticate_user(email=email, password=password)

        tokens = AuthService.create_token_pair(user)

        user.last_login = datetime.now()
        user.save(update_fields=["last_login"])

        return Response(
            {
                "user": {
                    "id": user.pk,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                },
                "tokens": tokens,
                "message": "Вход выполнен успешно",
            },
            status=status.HTTP_200_OK,
        )


class CustomRefreshTokenView(APIView):
    """
    Кастомный эндпоинт для обновления access токена.
    Принимает валидный refresh токен и возвращает новую пару access/refresh токенов.
    Старый refresh токен добавляется в черный список
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request: Request) -> Response:
        """Обновление access токена по валидному refresh токену"""

        serializer = RefreshTokenSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data["refresh"]

        try:
            new_tokens = AuthService.refresh_access_token(refresh_token)

            return Response(
                {"access": new_tokens["access"], "refresh": new_tokens["refresh"], "message": "Токен обновлен"},
                status=status.HTTP_200_OK,
            )

        except AuthenticationFailed as e:
            return Response({"error": str(e)}, status=status.HTTP_401_UNAUTHORIZED)
        except Exception as e:
            return Response(
                {"error": str(e), "code": "internal_error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class CustomLogoutView(APIView):
    """Эндпоинт для выхода из системы"""

    permission_classes = [permissions.IsAuthenticated]

    next_page = "/"

    def post(self, request: Request) -> Response:
        """
        Выход пользователя из системы.
        Если передан refresh токен, он добавляется в черный список
        """

        if not request.user.is_authenticated:
            raise AuthenticationFailed("Пользователь не аутентифицирован", code="not_authenticated")

        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh_token = serializer.validated_data.get("refresh")

        if refresh_token:
            TokenBlacklistService.add_to_blacklist(
                token=refresh_token,
                user=request.user,
            )

        AuthService.logout_user(refresh_token)

        return Response(
            {"message": f"Выход выполнен успешно{' refresh токен отозван' if refresh_token else ''}"},
            status=status.HTTP_200_OK,
        )
