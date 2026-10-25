"""Constantes et expressions financières partagées par l'API.

Les montants sont toujours calculés côté base à partir des snapshots portés
par la commande. Ce module ne contient aucune logique d'écriture : il est
utilisé par le dashboard et par les endpoints analytiques en lecture seule.
"""

from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F

from .models import Order


CURRENCY = "DZD"

ZERO = Decimal("0.00")

MONEY_FIELD = DecimalField(max_digits=16, decimal_places=2)

ORDER_REVENUE = ExpressionWrapper(
    F("quantity") * F("unit_price"),
    output_field=MONEY_FIELD,
)
# Les coûts proviennent des snapshots historiques portés par la commande
# elle-même : modifier le produit n'affecte plus la rentabilité passée.
ORDER_PURCHASE_COST = ExpressionWrapper(
    F("quantity") * F("purchase_price"),
    output_field=MONEY_FIELD,
)
ORDER_PACKAGING_COST = ExpressionWrapper(
    F("quantity") * F("packaging_cost"),
    output_field=MONEY_FIELD,
)
ORDER_NET_RESULT = ExpressionWrapper(
    F("quantity") * F("unit_price")
    - F("quantity") * F("purchase_price")
    - F("quantity") * F("packaging_cost")
    - F("delivery_cost"),
    output_field=MONEY_FIELD,
)

# Ventes réalisées : uniquement les commandes livrées.
REALIZED_STATUSES = (Order.Status.DELIVERED,)
# Commandes en cours : ni réalisées, ni annulées.
IN_PROGRESS_STATUSES = (
    Order.Status.PENDING,
    Order.Status.CONFIRMED,
    Order.Status.SHIPPED,
)
# Commandes annulées : refusées ou retournées, jamais comptées comme ventes.
CANCELLED_STATUSES = (Order.Status.REFUSED, Order.Status.RETURNED)

SALES_SERIES_DAYS = 30


def money(value) -> str:
    """Sérialise un montant en chaîne décimale à 2 décimales.

    Aucune valeur n'est inventée : un montant absent est rendu comme zéro.
    """
    if value is None:
        return str(ZERO)
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(value.quantize(ZERO))
