from django.contrib import admin

from .models import User, BlacklistedToken


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    """Администрирование пользователей. Позволяет управлять
    пользователями, с возможностью фильтрации и поиска."""

    list_display = (
        "id",
        "email",
        "first_name",
        "last_name",
        "middle_name",
    )
    list_filter = ("email",)
    search_fields = (
        "email",
        "first_name",
        "last_name",
    )

@admin.register(BlacklistedToken)
class BlackListedTokenAdmin(admin.ModelAdmin):
    """Администрирование черного списка токенов"""

    list_display = (
        "id",
        "token",
        "blacklisted_at",
    )
    list_filter = ("blacklisted_at",)
    search_fields = (
        "blacklisted_at",
    )
