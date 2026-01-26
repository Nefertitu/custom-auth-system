from django.contrib.auth.models import AbstractUser
from django.db import models

from config import settings


class User(AbstractUser):
    """
    Модель пользователя с кастомными полями.
    Заменяет стандартный `username` на `email`
    в качестве основного идентификатора
    """

    username = None  # type: ignore[assignment]
    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Укажите email",
    )
    first_name = models.CharField(
        max_length=30,
        verbose_name="Имя пользователя",
        help_text="Укажите Ваше имя",
    )
    last_name = models.CharField(
        max_length=100,
        verbose_name="Фамилия пользователя",
        help_text="Укажите Вашу фамилию",
        blank=True,
    )
    middle_name = models.CharField(
        max_length=30,
        verbose_name="Отчество пользователя",
        help_text="Укажите Ваше отчество",
        blank=True,
    )
    is_manager = models.BooleanField(
        default=False, null=True, blank=True, help_text="Добавление пользователю статуса 'менеджер'"
    )
    is_active = models.BooleanField(
        verbose_name="Активный",
        default=True,
        help_text="Активен/Удален (Снять отметку, сделав аккаунт пользователя неактивным)",
    )
    created_at = models.DateTimeField(
        verbose_name="Дата создания учетной записи",
        auto_now_add=True,
        help_text="Автоматически устанавливается при создании",
    )
    updated_at = models.DateTimeField(
        verbose_name="Дата обновления учетной записи",
        auto_now=True,
        help_text="Автоматически обновляется при каждом изменении",
    )
    last_login = models.DateTimeField(
        verbose_name="Последний вход", null=True, blank=True, help_text="Дата и время последнего входа в систему"
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    ordering = ["-created_at"]

    permissions = [
        ("can_view_all_users", "Может видеть всех пользователей"),
        ("can_delete_user", "Может удалять пользователей"),
    ]

    def get_full_name(self) -> str:
        """Возвращает полное имя пользователя"""

        if self.last_name or (self.last_name and self.middle_name):
            return f"{self.first_name} {self.middle_name} {self.last_name}"
        return f"{self.first_name}"

    def __str__(self) -> str:
        """Строковое представление объекта пользователя"""
        return f"{self.email} ({self.get_full_name()})"


class BlacklistedToken(models.Model):
    """Модель 'черный список' refresh токенов"""

    token = models.TextField(
        unique=True,
        db_index=True
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    blacklisted_at = models.DateTimeField(
        auto_now_add=True
    )
    expires_at = models.DateTimeField()

    class Meta:
        indexes = [
            models.Index(fields=["token"]),
            models.Index(fields=["user", "blacklisted_at"]),
        ]

    @classmethod
    def is_blacklisted(cls, token: str) -> bool:
        return cls.objects.filter(token=token).exists()