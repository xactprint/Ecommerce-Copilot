import os
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from api.models import Order, Product


DEMO_PRODUCTS = (
    {
        "sku": "DEMO-001",
        "name": "Sac en toile démo",
        "purchase_price": "1200.00",
        "selling_price": "2400.00",
        "packaging_cost": "150.00",
        "stock_quantity": 25,
    },
    {
        "sku": "DEMO-002",
        "name": "Lampe de bureau démo",
        "purchase_price": "1800.00",
        "selling_price": "3300.00",
        "packaging_cost": "200.00",
        "stock_quantity": 18,
    },
    {
        "sku": "DEMO-003",
        "name": "Carnet de notes démo",
        "purchase_price": "450.00",
        "selling_price": "1100.00",
        "packaging_cost": "80.00",
        "stock_quantity": 40,
    },
)

DEMO_ORDERS = (
    {
        "order_number": "DEMO-1001",
        "customer_name": "Client Démo 01",
        "sku": "DEMO-001",
        "quantity": 2,
        "unit_price": "2400.00",
        "delivery_cost": "450.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 28,
    },
    {
        "order_number": "DEMO-1002",
        "customer_name": "Client Démo 02",
        "sku": "DEMO-002",
        "quantity": 1,
        "unit_price": "3300.00",
        "delivery_cost": "1200.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 25,
    },
    {
        "order_number": "DEMO-1003",
        "customer_name": "Client Démo 03",
        "sku": "DEMO-003",
        "quantity": 1,
        "unit_price": "1100.00",
        "delivery_cost": "900.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 21,
    },
    {
        "order_number": "DEMO-1004",
        "customer_name": "Client Démo 04",
        "sku": "DEMO-001",
        "quantity": 3,
        "unit_price": "2400.00",
        "delivery_cost": "2800.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 17,
    },
    {
        "order_number": "DEMO-1005",
        "customer_name": "Client Démo 05",
        "sku": "DEMO-002",
        "quantity": 1,
        "unit_price": "3300.00",
        "delivery_cost": "1500.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 14,
    },
    {
        "order_number": "DEMO-1006",
        "customer_name": "Client Démo 06",
        "sku": "DEMO-003",
        "quantity": 2,
        "unit_price": "1100.00",
        "delivery_cost": "300.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 10,
    },
    {
        "order_number": "DEMO-1007",
        "customer_name": "Client Démo 07",
        "sku": "DEMO-002",
        "quantity": 2,
        "unit_price": "3300.00",
        "delivery_cost": "2500.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 8,
    },
    {
        "order_number": "DEMO-1008",
        "customer_name": "Client Démo 08",
        "sku": "DEMO-003",
        "quantity": 4,
        "unit_price": "1100.00",
        "delivery_cost": "2100.00",
        "status": Order.Status.DELIVERED,
        "days_ago": 4,
    },
    {
        "order_number": "DEMO-1009",
        "customer_name": "Client Démo 09",
        "sku": "DEMO-001",
        "quantity": 1,
        "unit_price": "2400.00",
        "delivery_cost": "450.00",
        "status": Order.Status.PENDING,
        "days_ago": 2,
    },
    {
        "order_number": "DEMO-1010",
        "customer_name": "Client Démo 10",
        "sku": "DEMO-002",
        "quantity": 2,
        "unit_price": "3300.00",
        "delivery_cost": "600.00",
        "status": Order.Status.CONFIRMED,
        "days_ago": 2,
    },
    {
        "order_number": "DEMO-1011",
        "customer_name": "Client Démo 11",
        "sku": "DEMO-003",
        "quantity": 1,
        "unit_price": "1100.00",
        "delivery_cost": "500.00",
        "status": Order.Status.SHIPPED,
        "days_ago": 1,
    },
    {
        "order_number": "DEMO-1012",
        "customer_name": "Client Démo 12",
        "sku": "DEMO-001",
        "quantity": 1,
        "unit_price": "2400.00",
        "delivery_cost": "450.00",
        "status": Order.Status.REFUSED,
        "days_ago": 1,
    },
)


class Command(BaseCommand):
    help = (
        "Crée ou met à jour le compte et les données de démonstration "
        "synthétiques, de façon idempotente."
    )

    def handle(self, *args, **options):
        username = os.environ.get("DEMO_USERNAME", "demo").strip()
        password = os.environ.get("DEMO_PASSWORD")

        if not username:
            raise CommandError("DEMO_USERNAME ne peut pas être vide.")
        if not password:
            raise CommandError(
                "DEMO_PASSWORD doit être défini dans l'environnement."
            )
        if len(password) < 8:
            raise CommandError(
                "DEMO_PASSWORD doit contenir au moins 8 caractères."
            )

        user_model = get_user_model()
        demo_user, _ = user_model.objects.get_or_create(username=username)
        demo_user.set_password(password)
        demo_user.is_staff = False
        demo_user.is_superuser = False
        demo_user.is_active = True
        demo_user.save(
            update_fields=[
                "password",
                "is_staff",
                "is_superuser",
                "is_active",
            ]
        )

        products = {}
        for spec in DEMO_PRODUCTS:
            product, _ = Product.objects.update_or_create(
                sku=spec["sku"],
                defaults={
                    "name": spec["name"],
                    "purchase_price": spec["purchase_price"],
                    "selling_price": spec["selling_price"],
                    "packaging_cost": spec["packaging_cost"],
                    "stock_quantity": spec["stock_quantity"],
                },
            )
            products[spec["sku"]] = product

        now = timezone.now()
        for spec in DEMO_ORDERS:
            product = products[spec["sku"]]
            order, created = Order.objects.update_or_create(
                order_number=spec["order_number"],
                defaults={
                    "customer_name": spec["customer_name"],
                    "customer_phone": "",
                    "product": product,
                    "quantity": spec["quantity"],
                    "unit_price": spec["unit_price"],
                    "delivery_cost": spec["delivery_cost"],
                    "purchase_price": product.purchase_price,
                    "packaging_cost": product.packaging_cost,
                    "costs_estimated": False,
                    "status": spec["status"],
                    "stock_deducted": False,
                    "notes": "Donnée synthétique de démonstration.",
                },
            )
            if created:
                Order.objects.filter(pk=order.pk).update(
                    created_at=now - timedelta(days=spec["days_ago"])
                )

        self.stdout.write(
            self.style.SUCCESS(
                "Données de démonstration prêtes pour "
                f"'{username}' : {len(DEMO_PRODUCTS)} produits, "
                f"{len(DEMO_ORDERS)} commandes."
            )
        )
