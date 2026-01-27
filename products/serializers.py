from typing import Any

from rest_framework import serializers

from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    """Сериализатор для продуктов"""

    owner = serializers.CharField(source="created_by.username", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "name", "description", "price", "quantity", "owner", "is_active", "created_at", "updated_at"]
        read_only_fields = ["owner", "created_at", "updated_at", "quantity"]

    def create(self, validated_data: dict) -> Any:
        """При создании назначаем текущего пользователя владельцем"""
        validated_data["created_by"] = self.context["request"].user
        return super().create(validated_data)

    def update(self, instance: Product, validated_data: dict) -> Any:
        """Запрещаем менять владельца и количество"""

        validated_data.pop("created_by", None)
        validated_data.pop("quantity", None)
        return super().update(instance, validated_data)
