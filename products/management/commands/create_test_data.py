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

        manager_password = "123qwer1"
        manager = User.objects.create(
            email="manager@example.com", password=manager_password, first_name="Manager", is_staff=True
        )
        manager.set_password(manager_password)
        manager.save()

        user_manager_password = "123qwer1"
        user_manager = User.objects.create(
            email="usermanager@example.com", password=user_manager_password, first_name="UserManager", is_staff=True
        )
        user_manager.set_password(user_manager_password)
        user_manager.save()

        user1_password = "123qwer1"
        user1 = User.objects.create(email="user1@example.com", first_name="User1", password=user1_password)
        user1.set_password(user1_password)
        user1.save()

        user2_password = "123qwer1"
        user2 = User.objects.create(email="user2@example.com", first_name="User2", password=user2_password)
        user2.set_password(user2_password)
        user2.save()

        # Выдаем права менеджерам
        content_type = ContentType.objects.get_for_model(Product)
        user_content_type = ContentType.objects.get_for_model(User)

        can_change_price = Permission.objects.get(codename="can_change_price", content_type=content_type)
        can_view_all = Permission.objects.get(codename="can_view_all_products", content_type=content_type)
        can_delete_products = Permission.objects.get(codename="can_delete_product", content_type=content_type)

        manager.user_permissions.add(can_change_price, can_view_all, can_delete_products)

        can_view_all_users = Permission.objects.get(codename="can_view_all_users", content_type=user_content_type)
        can_delete_user = Permission.objects.get(codename="can_delete_user", content_type=user_content_type)

        user_manager.user_permissions.add(can_view_all_users, can_delete_user)

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
                "- Менеджер: manager/123qwer1 (может менять цены, удалять продукты, просматривать список is_active продуктов)\n"
                "- Менеджер пользователей: user_manager/123qwer1 (может удалять пользователей, просматривать список пользователей)\n"
                "- Пользователь 1: user1/123qwer1 (владелец ноутбука)\n"
                "- Пользователь 2: user2/123qwer1 (владелец смартфона)\n"
                "- Создано 4 продукта (3 активных, 1 неактивный)"
            )
        )
