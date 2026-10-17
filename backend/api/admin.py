
from django.contrib import admin
from .models import Product, Order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "sku",
        "purchase_price",
        "selling_price",
        "packaging_cost",
        "stock_quantity",
        "created_at",
    )
    search_fields = ("name", "sku")
    list_filter = ("created_at",)
    ordering = ("name",)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "order_number",
        "customer_name",
        "product",
        "quantity",
        "total_amount",
        "delivery_cost",
        "status",
        "created_at",
    )
    search_fields = (
        "order_number",
        "customer_name",
        "customer_phone",
        "product__name",
    )
    list_filter = ("status", "created_at")
    list_select_related = ("product",)
    ordering = ("-created_at",)
