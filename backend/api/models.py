
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
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name="Statut",
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

    def __str__(self):
        return self.order_number
