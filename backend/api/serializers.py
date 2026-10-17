
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
    purchase_cost = serializers.DecimalField(
        max_digits=24,
        decimal_places=2,
        read_only=True,
    )
    packaging_cost_total = serializers.DecimalField(
        max_digits=24,
        decimal_places=2,
        read_only=True,
    )
    gross_profit = serializers.DecimalField(
        max_digits=24,
        decimal_places=2,
        read_only=True,
    )
    net_result_after_delivery = serializers.DecimalField(
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
            "purchase_price",
            "packaging_cost",
            "delivery_cost",
            "status",
            "stock_deducted",
            "notes",
            "total_amount",
            "purchase_cost",
            "packaging_cost_total",
            "gross_profit",
            "net_result_after_delivery",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "product_name",
            "total_amount",
            "created_at",
            # Snapshots historiques des coûts produit : capturés par le
            # serveur à la création, jamais fournis ni modifiés par le client.
            "purchase_price",
            "packaging_cost",
            # Indicateurs de rentabilité dérivés des snapshots.
            "purchase_cost",
            "packaging_cost_total",
            "gross_profit",
            "net_result_after_delivery",
            # Marqueur de traçabilité du stock : géré exclusivement par le
            # serveur, jamais défini par le client.
            "stock_deducted",
        ]
        # La quantité doit être strictement positive et les montants de la
        # commande ne peuvent pas être négatifs. Les bornes max_digits /
        # decimal_places restent dérivées du modèle (aucun calcul flottant).
        extra_kwargs = {
            "quantity": {"min_value": 1},
            "unit_price": {"min_value": 0},
            "delivery_cost": {"min_value": 0},
        }
  