from typing import Any

from django.core.management import BaseCommand

from authentication.services import TokenBlacklistService


class Command(BaseCommand):
    """Команда для очистки устаревших токенов из черного списка"""

    help = "Очистка устаревших токенов из черного списка"

    def handle(self, *args: Any, **options: Any) -> None:
        """Очищает черный список refresh токенов"""

        deleted_count = TokenBlacklistService.cleanup_expired()

        self.stdout.write(self.style.SUCCESS(f"Удалено {deleted_count} устаревших токенов из blacklist"))
