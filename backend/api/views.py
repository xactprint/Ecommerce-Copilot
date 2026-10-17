
from datetime import timedelta
from decimal import Decimal

from django.db import connection, transaction
from django.db.models import Count, DecimalField, ExpressionWrapper, F, Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
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


# --- Gestion du stock et des transitions de commande ----------------------
#
# Règle métier validée : le stock est décrémenté lorsque la commande passe de
# « pending » à « confirmed », et restitué si une commande confirmée est
# refusée ou si une commande expédiée/livrée est retournée. Le comportement
# dépend de la transition réellement demandée, jamais du statut final seul.

# Transitions autorisées : statut courant -> statuts cibles acceptés.
ORDER_TRANSITIONS = {
    Order.Status.PENDING: {Order.Status.CONFIRMED, Order.Status.REFUSED},
    Order.Status.CONFIRMED: {Order.Status.SHIPPED, Order.Status.REFUSED},
    Order.Status.SHIPPED: {
        Order.Status.DELIVERED,
        Order.Status.REFUSED,
        Order.Status.RETURNED,
    },
    Order.Status.DELIVERED: {Order.Status.RETURNED},
    Order.Status.REFUSED: set(),
    Order.Status.RETURNED: set(),
}

# Statuts pour lesquels le stock a déjà été décrémenté.
#
# Le marqueur persistant ``Order.stock_deducted`` est la seule preuve qu'une
# décrémentation a réellement eu lieu : le statut seul ne suffit pas, car des
# commandes historiques peuvent être ``confirmed``/``shipped``/``delivered``
# sans que leur stock ait jamais été déduit. Aucune restitution ne doit donc
# se fonder sur le statut sans vérifier ce marqueur.

# Statuts acceptés à la création : les autres s'obtiennent par transition.
ORDER_CREATABLE_STATUSES = {Order.Status.PENDING, Order.Status.REFUSED}

# Statuts supprimables : ni stock déduit à restituer, ni trace d'un retour.
ORDER_DELETABLE_STATUSES = {Order.Status.PENDING, Order.Status.REFUSED}

ORDER_FROZEN_FIELDS_MESSAGE = (
    "La quantité et le produit ne peuvent être modifiés que tant que la "
    "commande est en attente ('pending') : après confirmation, le stock a "
    "déjà été ajusté."
)


def _lock_products_for_update(product_ids) -> None:
    """Verrouille les lignes produit concernées quand le moteur le permet.

    SQLite ne supporte pas ``SELECT ... FOR UPDATE`` ; la garantie contre un
    stock négatif repose alors sur la mise à jour conditionnelle. L'ordre de
    verrouillage est trié pour éviter les interblocages sur les moteurs qui
    le supportent.
    """
    if not connection.features.has_select_for_update:
        return

    list(Product.objects.select_for_update().filter(pk__in=sorted(product_ids)))


def _lock_order_row(order_id: int):
    """Relit les valeurs courantes de la commande dans la transaction.

    Le verrou (``SELECT ... FOR UPDATE``) n'est posé que si le moteur le
    supporte ; sous SQLite, la relecture dans la transaction limite la fenêtre
    de course sans offrir de verrouillage ligne à ligne.
    """
    queryset = Order.objects.all()
    if connection.features.has_select_for_update:
        queryset = queryset.select_for_update()

    return (
        queryset.filter(pk=order_id)
        .values("status", "quantity", "product_id", "stock_deducted")
        .first()
    )


def _deduct_stock(product_id: int, quantity: int) -> None:
    """Décrémente le stock de façon conditionnelle (jamais de stock négatif).

    La condition ``stock_quantity__gte`` est évaluée au moment de l'UPDATE,
    dans la transaction en cours : la quantité disponible est donc vérifiée
    au moment de la modification, pas avant l'ouverture de la transaction.
    """
    updated = Product.objects.filter(
        pk=product_id,
        stock_quantity__gte=quantity,
    ).update(stock_quantity=F("stock_quantity") - quantity)

    if not updated:
        available = (
            Product.objects.filter(pk=product_id)
            .values_list("stock_quantity", flat=True)
            .first()
        )
        raise ValidationError(
            {
                "status": (
                    "Stock insuffisant pour confirmer la commande : "
                    f"{quantity} demandé(s), {available} disponible(s)."
                )
            }
        )


def _restore_stock(product_id: int, quantity: int) -> None:
    """Restitue au stock une quantité précédemment décrémentée."""
    Product.objects.filter(pk=product_id).update(
        stock_quantity=F("stock_quantity") + quantity
    )


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class OrderViewSet(viewsets.ModelViewSet):
    """Commandes avec transitions de statut contrôlées et suivi du stock.

    - Création : seuls ``pending`` (défaut) et ``refused`` sont acceptés,
      aucun mouvement de stock.
    - Modification : la transition demandée est validée, puis le stock est
      ajusté et la commande enregistrée dans une même transaction.
    - Suppression : refusée dès que le stock a été déduit (ou pour une
      commande ``returned``), afin de ne jamais perdre la trace d'une
      quantité déduite.
    """

    queryset = Order.objects.select_related("product").all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        requested_status = serializer.validated_data.get(
            "status", Order.Status.PENDING
        )

        if requested_status not in ORDER_CREATABLE_STATUSES:
            raise ValidationError(
                {
                    "status": (
                        "Une commande ne peut être créée qu'aux statuts "
                        "'pending' ou 'refused' ; les autres statuts "
                        "s'obtiennent par une transition contrôlée."
                    )
                }
            )

        # Snapshots historiques des coûts : capturés depuis le produit au
        # moment de la création, jamais choisis par le client (champs en
        # lecture seule dans le serializer).
        product = serializer.validated_data["product"]
        serializer.save(
            purchase_price=product.purchase_price,
            packaging_cost=product.packaging_cost,
        )

    def perform_update(self, serializer):
        order = serializer.instance
        data = serializer.validated_data

        new_status = data.get("status", order.status)
        new_quantity = data.get("quantity", order.quantity)
        new_product = data.get("product", order.product)

        with transaction.atomic():
            # Relecture dans la transaction : la décision repose sur l'état
            # réel au moment de la modification, pas sur un état antérieur.
            current = _lock_order_row(order.pk)
            current_status = current["status"]
            current_quantity = current["quantity"]
            current_product_id = current["product_id"]
            current_deducted = current["stock_deducted"]

            if new_status != current_status:
                allowed = ORDER_TRANSITIONS.get(current_status, set())
                if new_status not in allowed:
                    raise ValidationError(
                        {
                            "status": (
                                "Transition non autorisée : "
                                f"{current_status} → {new_status}."
                            )
                        }
                    )

            if current_status != Order.Status.PENDING:
                frozen = {}
                if new_quantity != current_quantity:
                    frozen["quantity"] = ORDER_FROZEN_FIELDS_MESSAGE
                if new_product.pk != current_product_id:
                    frozen["product"] = ORDER_FROZEN_FIELDS_MESSAGE

                if frozen:
                    raise ValidationError(frozen)

            _lock_products_for_update({current_product_id, new_product.pk})

            # Le marqueur de traçabilité suit exactement les mouvements
            # réellement effectués : il n'est jamais déduit du seul statut.
            new_deducted = current_deducted

            if current_status == Order.Status.PENDING and (
                new_status == Order.Status.CONFIRMED
            ):
                if not current_deducted:
                    _deduct_stock(new_product.pk, new_quantity)
                    new_deducted = True

            elif new_status in (Order.Status.REFUSED, Order.Status.RETURNED):
                # Restitution uniquement si le stock avait réellement été
                # déduit ; une commande historique (marqueur à False) ne
                # restitue donc jamais rien.
                if current_deducted:
                    _restore_stock(current_product_id, current_quantity)
                    new_deducted = False

            order.stock_deducted = new_deducted
            serializer.save()

    def perform_destroy(self, instance):
        if instance.status not in ORDER_DELETABLE_STATUSES:
            raise ValidationError(
                {
                    "status": (
                        "Suppression impossible : la commande est au statut "
                        f"'{instance.status}'. Le stock déduit doit d'abord "
                        "être restitué (ou la traçabilité conservée)."
                    )
                }
            )

        instance.delete()


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
