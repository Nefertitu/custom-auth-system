from typing import Any

from django.apps import apps
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

User = get_user_model()


class Command(BaseCommand):
    help = "Создание тестовых данных для демонстрации системы прав"

    def handle(self, *args: Any, **kwargs: Any) -> None:
        """Создаем пользователей, менеджера, продукты, назначаем права"""

        Product = apps.get_model("products", "Product")

        manager = User.objects.create(
            email="manager@example.com", password="manager123", first_name="Manager", is_staff=True
        )

        user1 = User.objects.create(email="user1@example.com", first_name="User1", password="user123")

        user2 = User.objects.create(email="user2@example.com", first_name="User2", password="user123")

        # Выдаем права менеджеру
        content_type = ContentType.objects.get_for_model(Product)

        can_change_price = Permission.objects.get(codename="can_change_price", content_type=content_type)
        can_view_all = Permission.objects.get(codename="can_view_all_products", content_type=content_type)

        manager.user_permissions.add(can_change_price, can_view_all)

        # Создаем продукты
        products = [
            Product(
                name="Ноутбук",
                description="Мощный ноутбук",
                price=999.99,
                quantity=10,
                created_by=user1,
                is_active=True,
            ),
            Product(
                name="Смартфон",
                description="Флагманский смартфон",
                price=799.99,
                quantity=5,
                created_by=user2,
                is_active=True,
            ),
            Product(
                name="Наушники",
                description="Беспроводные наушники",
                price=199.99,
                quantity=20,
                created_by=manager,
                is_active=True,
            ),
            Product(
                name="Старый продукт",
                description="Неактивный продукт",
                price=50.00,
                quantity=0,
                created_by=user1,
                is_active=False,
            ),
        ]

        Product.objects.bulk_create(products)

        self.stdout.write(
            self.style.SUCCESS(
                "Тестовые данные созданы:\n"
                "- Менеджер: manager/manager123 (может менять цены)\n"
                "- Пользователь 1: user1/user123 (владелец ноутбука)\n"
                "- Пользователь 2: user2/user123 (владелец смартфона)\n"
                "- Создано 4 продукта (3 активных, 1 неактивный)"
            )
        )
