"""Analyses commerciales en lecture seule.

Ce module ne fait aucune écriture : il agrège les commandes existantes et
construit des payloads explicables. Les calculs financiers reposent
exclusivement sur les snapshots historiques de chaque commande.
"""

from decimal import Decimal

from django.db.models import Count, Q, Sum
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .finance import (
    CURRENCY,
    ORDER_NET_RESULT,
    ORDER_PACKAGING_COST,
    ORDER_PURCHASE_COST,
    ORDER_REVENUE,
    REALIZED_STATUSES,
    ZERO,
    money,
)
from .models import Order


DEFAULT_LIMIT = 20
MAX_LIMIT = 100

ESTIMATED_COSTS_WARNING = "estimated_costs"
FINANCIAL_FIELDS_MUTABLE_WARNING = "financial_fields_mutable"


def parse_limit(raw_limit) -> int:
    """Valide le paramètre d'affichage ``limit`` selon les conventions DRF."""
    if raw_limit in (None, ""):
        return DEFAULT_LIMIT

    try:
        limit = int(raw_limit)
    except (TypeError, ValueError) as exc:
        raise ValidationError(
            {
                "limit": (
                    "Le paramètre 'limit' doit être un entier compris "
                    "entre 1 et 100."
                )
            }
        ) from exc

    if not 1 <= limit <= MAX_LIMIT:
        raise ValidationError(
            {
                "limit": (
                    "Le paramètre 'limit' doit être un entier compris "
                    "entre 1 et 100."
                )
            }
        )

    return limit


def _negative_queryset():
    """Commandes livrées dont le résultat net est strictement négatif."""
    delivered = Order.objects.filter(status__in=REALIZED_STATUSES)

    return delivered.annotate(
        revenue=ORDER_REVENUE,
        purchase=ORDER_PURCHASE_COST,
        packaging=ORDER_PACKAGING_COST,
        net_result=ORDER_NET_RESULT,
    ).filter(net_result__lt=ZERO)


def negative_orders(limit: int = DEFAULT_LIMIT) -> dict:
    """Construit le payload des commandes livrées non rentables.

    Règle unique appliquée : ``net_result_after_delivery < 0``. Aucun seuil
    de marge n'est introduit. Les totaux sont séparés entre coûts capturés et
    coûts estimés afin de ne pas présenter une estimation comme certaine.
    """
    delivered_count = Order.objects.filter(
        status__in=REALIZED_STATUSES
    ).count()

    negative = _negative_queryset()
    totals = negative.aggregate(
        negative_count=Count("id"),
        captured_count=Count("id", filter=Q(costs_estimated=False)),
        estimated_count=Count("id", filter=Q(costs_estimated=True)),
        negative_total=Sum("net_result"),
        captured_total=Sum(
            "net_result",
            filter=Q(costs_estimated=False),
        ),
        estimated_total=Sum(
            "net_result",
            filter=Q(costs_estimated=True),
        ),
    )

    negative_count = totals["negative_count"] or 0
    estimated_count = totals["estimated_count"] or 0

    warnings = [FINANCIAL_FIELDS_MUTABLE_WARNING]
    if estimated_count:
        warnings.insert(0, ESTIMATED_COSTS_WARNING)

    rows = (
        negative.values(
            "id",
            "order_number",
            "product_id",
            "product__name",
            "quantity",
            "created_at",
            "costs_estimated",
            "revenue",
            "purchase",
            "packaging",
            "delivery_cost",
            "net_result",
        )
        .order_by("net_result", "created_at", "id")[:limit]
    )

    results = []
    for row in rows:
        revenue = row["revenue"] or ZERO
        net_result = row["net_result"] or ZERO

        margin_rate = None
        if revenue > ZERO:
            margin_rate = money(net_result / revenue * Decimal("100"))

        results.append(
            {
                "id": row["id"],
                "orderNumber": row["order_number"],
                "productId": row["product_id"],
                "productName": row["product__name"],
                "quantity": row["quantity"],
                "revenue": money(revenue),
                "purchase": money(row["purchase"]),
                "packaging": money(row["packaging"]),
                "delivery": money(row["delivery_cost"]),
                "netResult": money(net_result),
                "marginRate": margin_rate,
                "costsEstimated": row["costs_estimated"],
                "createdAt": row["created_at"].isoformat(),
            }
        )

    return {
        "currency": CURRENCY,
        "generatedAt": timezone.now().isoformat(),
        "scope": {
            "status": Order.Status.DELIVERED,
            "costBasis": "order_snapshots",
            "rule": "net_result_after_delivery < 0",
        },
        "summary": {
            "deliveredOrders": delivered_count,
            "negativeOrders": negative_count,
            "negativeOrdersWithCapturedCosts": totals["captured_count"] or 0,
            "negativeOrdersWithEstimatedCosts": estimated_count,
            "negativeNetTotal": money(totals["negative_total"]),
            "negativeNetTotalCaptured": money(totals["captured_total"]),
            "negativeNetTotalEstimated": money(totals["estimated_total"]),
        },
        "dataQuality": {
            "estimated": estimated_count > 0,
            "estimatedOrders": estimated_count,
            "warnings": warnings,
        },
        "count": negative_count,
        "limit": limit,
        "results": results,
    }
