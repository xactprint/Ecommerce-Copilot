
from rest_framework import serializers
from .models import Product, Order


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "sku",
            "purchase_price",
            "selling_price",
            "packaging_cost",
            "stock_quantity",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class OrderSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(
        source="product.name",
        read_only=True,
    )
    total_amount = serializers.DecimalField(
        max_digits=24,
        decimal_places=2,
        read_only=True,
    )

    class Meta:
        model = Order
        fields = [
            "id",
            "order_number",
            "customer_name",
            "customer_phone",
            "product",
            "product_name",
            "quantity",
            "unit_price",
            "delivery_cost",
            "status",
            "notes",
            "total_amount",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "product_name",
            "total_amount",
            "created_at",
        ]
        # La quantité doit être strictement positive et les montants de la
        # commande ne peuvent pas être négatifs. Les bornes max_digits /
        # decimal_places restent dérivées du modèle (aucun calcul flottant).
        extra_kwargs = {
            "quantity": {"min_value": 1},
            "unit_price": {"min_value": 0},
            "delivery_cost": {"min_value": 0},
        }
  