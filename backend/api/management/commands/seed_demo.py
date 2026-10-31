import os
from collections import Counter
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
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
        "category": "Fashion",
        "name": "Sac en toile démo",
        "purchase_price": "1200.00",
        "selling_price": "2400.00",
        "packaging_cost": "150.00",
        "stock_quantity": 25,
    },
    {
        "sku": "DEMO-002",
        "category": "Home & Kitchen",
        "name": "Lampe de bureau démo",
        "purchase_price": "1800.00",
        "selling_price": "3300.00",
        "packaging_cost": "200.00",
        "stock_quantity": 18,
    },
    {
        "sku": "DEMO-003",
        "category": "Office & Productivity",
        "name": "Carnet de notes démo",
        "purchase_price": "450.00",
        "selling_price": "1100.00",
        "packaging_cost": "80.00",
        "stock_quantity": 40,
    },
    {
        "sku": "DEMO-ELEC-001",
        "category": "Electronics",
        "name": "Wireless Bluetooth Headphones",
        "purchase_price": "12500.00",
        "selling_price": "18900.00",
        "packaging_cost": "350.00",
        "stock_quantity": 120,
    },
    {
        "sku": "DEMO-ELEC-002",
        "category": "Electronics",
        "name": "Smart Watch",
        "purchase_price": "19500.00",
        "selling_price": "28900.00",
        "packaging_cost": "400.00",
        "stock_quantity": 64,
    },
    {
        "sku": "DEMO-ELEC-003",
        "category": "Electronics",
        "name": "Portable Bluetooth Speaker",
        "purchase_price": "6800.00",
        "selling_price": "9900.00",
        "packaging_cost": "300.00",
        "stock_quantity": 8,
    },
    {
        "sku": "DEMO-ELEC-004",
        "category": "Electronics",
        "name": "USB-C Fast Charger",
        "purchase_price": "750.00",
        "selling_price": "1500.00",
        "packaging_cost": "100.00",
        "stock_quantity": 3,
    },
    {
        "sku": "DEMO-ELEC-005",
        "category": "Electronics",
        "name": "Wireless Mouse",
        "purchase_price": "1400.00",
        "selling_price": "2400.00",
        "packaging_cost": "120.00",
        "stock_quantity": 0,
    },
    {
        "sku": "DEMO-FASH-001",
        "category": "Fashion",
        "name": "Classic Cotton T-Shirt",
        "purchase_price": "900.00",
        "selling_price": "1800.00",
        "packaging_cost": "80.00",
        "stock_quantity": 95,
    },
    {
        "sku": "DEMO-FASH-002",
        "category": "Fashion",
        "name": "Urban Hoodie",
        "purchase_price": "2600.00",
        "selling_price": "4500.00",
        "packaging_cost": "150.00",
        "stock_quantity": 12,
    },
    {
        "sku": "DEMO-FASH-003",
        "category": "Fashion",
        "name": "Running Sneakers",
        "purchase_price": "5200.00",
        "selling_price": "8500.00",
        "packaging_cost": "250.00",
        "stock_quantity": 2,
    },
    {
        "sku": "DEMO-HOME-001",
        "category": "Home & Kitchen",
        "name": "Stainless Steel Coffee Maker",
        "purchase_price": "7800.00",
        "selling_price": "12500.00",
        "packaging_cost": "450.00",
        "stock_quantity": 30,
    },
    {
        "sku": "DEMO-HOME-002",
        "category": "Home & Kitchen",
        "name": "Electric Kettle",
        "purchase_price": "2400.00",
        "selling_price": "4200.00",
        "packaging_cost": "200.00",
        "stock_quantity": 14,
    },
    {
        "sku": "DEMO-HOME-003",
        "category": "Home & Kitchen",
        "name": "Kitchen Storage Set",
        "purchase_price": "1500.00",
        "selling_price": "2900.00",
        "packaging_cost": "180.00",
        "stock_quantity": 6,
    },
    {
        "sku": "DEMO-BEAUTY-001",
        "category": "Beauty & Personal Care",
        "name": "Facial Cleansing Brush",
        "purchase_price": "2100.00",
        "selling_price": "3800.00",
        "packaging_cost": "120.00",
        "stock_quantity": 42,
    },
    {
        "sku": "DEMO-BEAUTY-002",
        "category": "Beauty & Personal Care",
        "name": "Hair Dryer",
        "purchase_price": "3600.00",
        "selling_price": "6200.00",
        "packaging_cost": "250.00",
        "stock_quantity": 9,
    },
    {
        "sku": "DEMO-BEAUTY-003",
        "category": "Beauty & Personal Care",
        "name": "Moisturizing Skin Cream",
        "purchase_price": "600.00",
        "selling_price": "1200.00",
        "packaging_cost": "60.00",
        "stock_quantity": 150,
    },
    {
        "sku": "DEMO-BEAUTY-004",
        "category": "Beauty & Personal Care",
        "name": "Electric Grooming Kit",
        "purchase_price": "4800.00",
        "selling_price": "7900.00",
        "packaging_cost": "300.00",
        "stock_quantity": 0,
    },
    {
        "sku": "DEMO-SPORT-001",
        "category": "Sports & Fitness",
        "name": "Yoga Mat",
        "purchase_price": "1800.00",
        "selling_price": "3200.00",
        "packaging_cost": "150.00",
        "stock_quantity": 55,
    },
    {
        "sku": "DEMO-SPORT-002",
        "category": "Sports & Fitness",
        "name": "Resistance Bands Set",
        "purchase_price": "800.00",
        "selling_price": "1600.00",
        "packaging_cost": "70.00",
        "stock_quantity": 22,
    },
    {
        "sku": "DEMO-SPORT-003",
        "category": "Sports & Fitness",
        "name": "Insulated Sports Bottle",
        "purchase_price": "1200.00",
        "selling_price": "2200.00",
        "packaging_cost": "100.00",
        "stock_quantity": 4,
    },
    {
        "sku": "DEMO-SPORT-004",
        "category": "Sports & Fitness",
        "name": "Adjustable Dumbbells",
        "purchase_price": "15000.00",
        "selling_price": "22500.00",
        "packaging_cost": "800.00",
        "stock_quantity": 24,
    },
    {
        "sku": "DEMO-OFFICE-001",
        "category": "Office & Productivity",
        "name": "Ergonomic Office Chair",
        "purchase_price": "32000.00",
        "selling_price": "45000.00",
        "packaging_cost": "1200.00",
        "stock_quantity": 28,
    },
    {
        "sku": "DEMO-OFFICE-002",
        "category": "Office & Productivity",
        "name": "Mechanical Keyboard",
        "purchase_price": "6500.00",
        "selling_price": "10500.00",
        "packaging_cost": "300.00",
        "stock_quantity": 26,
    },
    {
        "sku": "DEMO-OFFICE-003",
        "category": "Office & Productivity",
        "name": "Laptop Stand",
        "purchase_price": "2200.00",
        "selling_price": "3900.00",
        "packaging_cost": "180.00",
        "stock_quantity": 35,
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

PRODUCT_FIELDS = (
    "name",
    "purchase_price",
    "selling_price",
    "packaging_cost",
    "stock_quantity",
)

STOCK_STATE_LABELS = {
    "out_of_stock": "rupture",
    "very_low": "très faible",
    "low": "faible",
    "medium": "moyen",
    "healthy": "sain",
}


def stock_state(quantity):
    if quantity == 0:
        return "out_of_stock"
    if quantity <= 4:
        return "very_low"
    if quantity <= 19:
        return "low"
    if quantity <= 49:
        return "medium"
    return "healthy"


def _product_defaults(spec):
    return {field: spec[field] for field in PRODUCT_FIELDS}


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

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help=(
                "Confirme explicitement l'écriture des données de "
                "démonstration. Obligatoire lorsque DEBUG=False."
            ),
        )

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["confirm"]:
            raise CommandError(
                "Exécution refusée : l'environnement n'est pas en mode DEBUG. "
                "Relancez avec --confirm pour créer ou mettre à jour les "
                "données de démonstration."
            )

        skus = [spec["sku"] for spec in DEMO_PRODUCTS]
        if len(skus) != len(set(skus)):
            raise CommandError(
                "Le jeu de données de démonstration contient des SKU en double."
            )

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

        categories = Counter(spec["category"] for spec in DEMO_PRODUCTS)
        stock_states = Counter(
            stock_state(spec["stock_quantity"]) for spec in DEMO_PRODUCTS
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Données de démonstration prêtes pour "
                f"'{username}' : {len(DEMO_PRODUCTS)} produits, "
                f"{len(DEMO_ORDERS)} commandes."
            )
        )
        self.stdout.write(
            "Catégories : "
            + ", ".join(
                f"{category} ({count})"
                for category, count in sorted(categories.items())
            )
        )
        self.stdout.write(
            "Stock : "
            + ", ".join(
                f"{STOCK_STATE_LABELS[state]} ({stock_states[state]})"
                for state in STOCK_STATE_LABELS
                if stock_states[state]
            )
        )
