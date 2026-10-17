
from datetime import timedelta
from decimal import Decimal

from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer

CURRENCY = "DZD"

ZERO = Decimal("0.00")

MONEY_FIELD = DecimalField(max_digits=16, decimal_places=2)

ORDER_REVENUE = ExpressionWrapper(
    F("quantity") * F("unit_price"),
    output_field=MONEY_FIELD,
)
ORDER_PURCHASE_COST = ExpressionWrapper(
    F("quantity") * F("product__purchase_price"),
    output_field=MONEY_FIELD,
)
ORDER_PACKAGING_COST = ExpressionWrapper(
    F("quantity") * F("product__packaging_cost"),
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


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("product").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]


def _money(value) -> str:
    """Sérialise un montant en chaîne décimale à 2 décimales (aucune valeur inventée)."""
    if value is None:
        return str(ZERO)
    if not isinstance(value, Decimal):
        value = Decimal(str(value))
    return str(value.quantize(ZERO))


def _empty_totals() -> dict:
    return {
        "orders": 0,
        "revenue": ZERO,
        "purchase": ZERO,
        "packaging": ZERO,
        "delivery": ZERO,
    }


def _sum_statuses(by_status: dict, statuses) -> dict:
    """Additionne les agrégats déjà calculés pour un sous-ensemble de statuts."""
    totals = _empty_totals()

    for status_value in statuses:
        row = by_status[status_value]
        totals["orders"] += row["orders"]
        totals["revenue"] += row["revenue"]
        totals["purchase"] += row["purchase"]
        totals["packaging"] += row["packaging"]
        totals["delivery"] += row["delivery"]

    return totals


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def dashboard(request):
    """Indicateurs calculés depuis la base, sans aucune valeur codée en dur.

    - Une seule requête agrégée par statut (Count/Sum côté base de données).
    - Le chiffre d'affaires d'une commande est `quantity * unit_price` ;
      `unit_price` est figé au moment de la commande, donc fiable.
    - Les coûts d'achat et d'emballage utilisent les prix actuels du produit
      (non figés à la commande) : ils sont explicitement marqués « estimated ».
    - Aucune dépense publicitaire n'existe en base : l'indicateur est déclaré
      comme indisponible au lieu d'être inventé.
    """
    rows = Order.objects.values("status").annotate(
        orders=Count("id"),
        revenue=Sum(ORDER_REVENUE),
        purchase=Sum(ORDER_PURCHASE_COST),
        packaging=Sum(ORDER_PACKAGING_COST),
        delivery=Sum("delivery_cost"),
    )

    by_status = {
        value: _empty_totals() for value, _ in Order.Status.choices
    }
    for row in rows:
        by_status[row["status"]] = {
            "orders": row["orders"],
            "revenue": row["revenue"] or ZERO,
            "purchase": row["purchase"] or ZERO,
            "packaging": row["packaging"] or ZERO,
            "delivery": row["delivery"] or ZERO,
        }

    realized = _sum_statuses(by_status, REALIZED_STATUSES)
    in_progress = _sum_statuses(by_status, IN_PROGRESS_STATUSES)
    cancelled = _sum_statuses(by_status, CANCELLED_STATUSES)
    all_orders = _sum_statuses(by_status, [value for value, _ in Order.Status.choices])

    realized_costs_total = (
        realized["purchase"] + realized["packaging"] + realized["delivery"]
    )

    since = timezone.now() - timedelta(days=SALES_SERIES_DAYS - 1)
    series = (
        Order.objects.filter(status__in=REALIZED_STATUSES, created_at__gte=since)
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum(ORDER_REVENUE), orders=Count("id"))
        .order_by("day")
    )

    data = {
        "currency": CURRENCY,
        "generatedAt": timezone.now().isoformat(),
        "counts": {
            "products": Product.objects.count(),
            "orders": all_orders["orders"],
            "ordersByStatus": {
                value: by_status[value]["orders"]
                for value, _ in Order.Status.choices
            },
            "pendingOrders": by_status[Order.Status.PENDING]["orders"],
            "deliveredOrders": realized["orders"],
            "inProgressOrders": in_progress["orders"],
            "cancelledOrders": cancelled["orders"],
        },
        "revenue": {
            "realized": _money(realized["revenue"]),
            "inProgress": _money(in_progress["revenue"]),
            "cancelled": _money(cancelled["revenue"]),
            "allOrders": _money(all_orders["revenue"]),
        },
        "deliveryCosts": {
            "realized": _money(realized["delivery"]),
            "allOrders": _money(all_orders["delivery"]),
        },
        "costs": {
            "realized": {
                "estimated": True,
                "purchase": _money(realized["purchase"]),
                "packaging": _money(realized["packaging"]),
                "delivery": _money(realized["delivery"]),
                "total": _money(realized_costs_total),
            }
        },
        "profit": {
            "estimated": True,
            "realized": _money(realized["revenue"] - realized_costs_total),
        },
        "salesSeries": [
            {
                "date": row["day"].isoformat(),
                "revenue": _money(row["revenue"]),
                "orders": row["orders"],
            }
            for row in series
        ],
        "unavailableMetrics": [
            {
                "key": "adSpend",
                "reason": (
                    "Aucun modèle ni champ de dépense publicitaire n'existe "
                    "dans la base de données."
                ),
                "requiredData": (
                    "Un modèle AdSpend (date, montant, canal) pour agréger "
                    "les dépenses publicitaires."
                ),
            },
            {
                "key": "historicalUnitCosts",
                "reason": (
                    "purchase_price et packaging_cost proviennent du produit "
                    "actuel : ils ne sont pas figés au moment de la commande."
                ),
                "requiredData": (
                    "Copier les coûts d'achat et d'emballage sur Order à la "
                    "création pour un historique exact."
                ),
            },
        ],
    }

    return Response(data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout(request):
    Token.objects.filter(user=request.user).delete()

    return Response(status=status.HTTP_204_NO_CONTENT)
