from django.contrib import admin

from .models import Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """Администрирование продуктов. Включает отображение основных
    характеристик продуктов, фильтрацию по категориям и имени,
    а также поиск по названию и описанию."""

    list_display = ("id", "name", "price", "created_by", "description")
    list_filter = ("name",)
    search_fields = (
        "name",
        "created_by",
    )
