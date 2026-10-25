import os
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from api.models import Order, Product


DEMO_ACCOUNT_GROUP = "seed_demo_account"
SYNTHETIC_NOTE = "Donnée synthétique de démonstration."

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


def _product_defaults(spec):
    return {
        "name": spec["name"],
        "purchase_price": spec["purchase_price"],
        "selling_price": spec["selling_price"],
        "packaging_cost": spec["packaging_cost"],
        "stock_quantity": spec["stock_quantity"],
    }


def _order_defaults(spec, product):
    return {
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
        "notes": SYNTHETIC_NOTE,
    }


def _is_seed_product(product, spec):
    return (
        product.sku == spec["sku"]
        and product.name == spec["name"]
        and product.purchase_price == Decimal(spec["purchase_price"])
        and product.selling_price == Decimal(spec["selling_price"])
        and product.packaging_cost == Decimal(spec["packaging_cost"])
        and product.stock_quantity == spec["stock_quantity"]
    )


def _is_seed_order(order, spec):
    return (
        order.order_number == spec["order_number"]
        and order.customer_name == spec["customer_name"]
        and order.notes == SYNTHETIC_NOTE
    )


class Command(BaseCommand):
    help = (
        "Crée ou met à jour le compte et les données de démonstration "
        "synthétiques, de façon idempotente, sans écraser de données non "
        "reconnues."
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

        with transaction.atomic():
            demo_group, _ = Group.objects.get_or_create(
                name=DEMO_ACCOUNT_GROUP
            )
            demo_user, created = user_model.objects.get_or_create(
                username=username
            )

            if created:
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
            else:
                if not demo_user.groups.filter(pk=demo_group.pk).exists():
                    raise CommandError(
                        f"Le compte '{username}' existe déjà et n'est pas "
                        "reconnu comme compte de démonstration. Aucune "
                        "modification n'a été effectuée."
                    )
                if demo_user.is_staff or demo_user.is_superuser:
                    raise CommandError(
                        f"Le compte de démonstration '{username}' est staff "
                        "ou superuser. Refus de le rétrograder "
                        "automatiquement."
                    )

                demo_user.set_password(password)
                demo_user.is_active = True
                demo_user.save(
                    update_fields=["password", "is_active"]
                )

            demo_user.groups.add(demo_group)

            products = {}
            for spec in DEMO_PRODUCTS:
                defaults = _product_defaults(spec)
                matches = list(Product.objects.filter(sku=spec["sku"]))

                if len(matches) > 1:
                    raise CommandError(
                        f"Plusieurs produits portent le SKU réservé "
                        f"'{spec['sku']}'. Aucun écrasement n'a été "
                        "effectué."
                    )

                if matches:
                    product = matches[0]
                    if not _is_seed_product(product, spec):
                        raise CommandError(
                            f"Le produit avec le SKU réservé "
                            f"'{spec['sku']}' n'est pas reconnu comme "
                            "donnée de démonstration. Aucun écrasement "
                            "n'a été effectué."
                        )
                    for field, value in defaults.items():
                        setattr(product, field, value)
                    product.save(update_fields=list(defaults))
                else:
                    product = Product.objects.create(
                        sku=spec["sku"], **defaults
                    )

                products[spec["sku"]] = product

            now = timezone.now()
            for spec in DEMO_ORDERS:
                product = products[spec["sku"]]
                defaults = _order_defaults(spec, product)
                matches = list(
                    Order.objects.filter(
                        order_number=spec["order_number"]
                    )
                )

                if len(matches) > 1:
                    raise CommandError(
                        f"Plusieurs commandes portent le numéro réservé "
                        f"'{spec['order_number']}'. Aucun écrasement n'a "
                        "été effectué."
                    )

                if matches:
                    order = matches[0]
                    if not _is_seed_order(order, spec):
                        raise CommandError(
                            f"La commande avec le numéro réservé "
                            f"'{spec['order_number']}' n'est pas reconnue "
                            "comme donnée de démonstration. Aucun "
                            "écrasement n'a été effectué."
                        )
                    for field, value in defaults.items():
                        setattr(order, field, value)
                    order.save(update_fields=list(defaults))
                else:
                    order = Order.objects.create(
                        order_number=spec["order_number"], **defaults
                    )
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
