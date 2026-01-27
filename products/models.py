from django.db import models

from config import settings


class Product(models.Model):
    """Модель продукта для демонстрации системы прав"""

    name = models.CharField(max_length=200, verbose_name="Название")
    description = models.TextField(verbose_name="Описание", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Цена")
    quantity = models.IntegerField(default=0, verbose_name="Количество на складе")
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="products", verbose_name="Владелец/создатель"
    )
    is_active = models.BooleanField(default=True, verbose_name="Активен")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Продукт"
        verbose_name_plural = "Продукты"

        permissions = [
            ("can_change_price", "Может изменять цену продукта"),
            ("can_delete_product", "Может удалять продукты"),
            ("can_view_all_products", "Может просматривать все продукты"),
        ]

    def __str__(self) -> str:
        """Строковое представление экземпляра продукта"""
        return f"{self.name} (${self.price})"
