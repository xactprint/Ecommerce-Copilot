
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
  