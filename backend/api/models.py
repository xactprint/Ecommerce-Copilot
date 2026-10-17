
from django.db import models


class Product(models.Model):
    name = models.CharField(
        max_length=200,
        verbose_name="Nom du produit",
    )
    sku = models.CharField(
        max_length=50,
        blank=True,
        verbose_name="Référence produit",
    )
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Prix d'achat (DZD)",
    )
    selling_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Prix de vente (DZD)",
    )
    packaging_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Coût d'emballage (DZD)",
    )
    stock_quantity = models.PositiveIntegerField(
        default=0,
        verbose_name="Quantité en stock",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
    )

    class Meta:
        ordering = ["name"]
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return self.name


class Order(models.Model):

    class Status(models.TextChoices):
        PENDING = "pending", "En attente"
        CONFIRMED = "confirmed", "Confirmée"
        SHIPPED = "shipped", "Expédiée"
        DELIVERED = "delivered", "Livrée"
        REFUSED = "refused", "Refusée"
        RETURNED = "returned", "Retournée"

    order_number = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="Numéro de commande",
    )
    customer_name = models.CharField(
        max_length=200,
        verbose_name="Nom du client",
    )
    customer_phone = models.CharField(
        max_length=30,
        blank=True,
        verbose_name="Téléphone du client",
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name="orders",
        verbose_name="Produit",
    )
    quantity = models.PositiveIntegerField(
        default=1,
        verbose_name="Quantité commandée",
    )
    unit_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Prix de vente unitaire au moment de la commande (DZD)",
    )
    delivery_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Coût de livraison (DZD)",
    )
    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name="Prix d'achat unitaire historique (DZD)",
    )
    packaging_cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        verbose_name="Coût d'emballage unitaire historique (DZD)",
    )
    costs_estimated = models.BooleanField(
        default=False,
        verbose_name="Coûts estimés",
        help_text=(
            "Vrai lorsque purchase_price / packaging_cost ont été reconstruits "
            "(commandes antérieures au snapshot) et ne reflètent donc pas le "
            "coût réel au moment de la commande."
        ),
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
    )
    stock_deducted = models.BooleanField(
        default=False,
        verbose_name="Stock déduit",
        help_text=(
            "Vrai lorsque la quantité de cette commande a été effectivement "
            "déduite du stock et n'a pas encore été restituée."
        ),
    )
    notes = models.TextField(
        blank=True,
        verbose_name="Notes",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Date de création",
    )

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"

    @property
    def total_amount(self):
        return self.unit_price * self.quantity

    @property
    def purchase_cost(self):
        """Coût d'achat total, calculé depuis le snapshot historique."""
        return self.purchase_price * self.quantity

    @property
    def packaging_cost_total(self):
        """Coût d'emballage total, calculé depuis le snapshot historique."""
        return self.packaging_cost * self.quantity

    @property
    def gross_profit(self):
        """Marge brute : revenus - achat - emballage (hors livraison)."""
        return self.total_amount - self.purchase_cost - self.packaging_cost_total

    @property
    def net_result_after_delivery(self):
        """Résultat net : marge brute - coût de livraison historique."""
        return self.gross_profit - self.delivery_cost

    def __str__(self):
        return self.order_number
