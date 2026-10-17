from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from .models import Order, Product

User = get_user_model()

PASSWORD = "TestPass!12345"


class SecuredApiTestCase(APITestCase):
    """Base commune : un utilisateur, un jeton, un produit et une commande."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="tester",
            password=PASSWORD,
        )
        self.token = Token.objects.create(user=self.user)
        self.product = Product.objects.create(
            name="Produit de test",
            sku="SKU-TEST-1",
            purchase_price="1000.00",
            selling_price="1500.00",
        )
        self.order = Order.objects.create(
            order_number="CMD-TEST-1",
            customer_name="Client de test",
            product=self.product,
            quantity=2,
            unit_price="1500.00",
        )

    def authenticate(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def assertRefused(self, response):
        self.assertEqual(
            response.status_code,
            status.HTTP_401_UNAUTHORIZED,
            msg=f"Statut inattendu : {response.status_code}",
        )


class AnonymousAccessTests(SecuredApiTestCase):
    """Toutes les routes métier doivent refuser un visiteur anonyme."""

    def test_anonymous_dashboard_is_refused(self):
        self.assertRefused(self.client.get(reverse("dashboard")))

    def test_anonymous_product_list_is_refused(self):
        self.assertRefused(self.client.get(reverse("product-list")))

    def test_anonymous_order_list_is_refused(self):
        self.assertRefused(self.client.get(reverse("order-list")))

    def test_anonymous_product_write_is_refused(self):
        payload = {
            "name": "Intrusion",
            "purchase_price": "1.00",
            "selling_price": "2.00",
        }
        self.assertRefused(self.client.post(reverse("product-list"), payload))
        self.assertFalse(Product.objects.filter(name="Intrusion").exists())

    def test_anonymous_order_write_is_refused(self):
        payload = {
            "order_number": "CMD-INTRUSION",
            "customer_name": "Intrusion",
            "product": self.product.id,
            "quantity": 1,
            "unit_price": "1500.00",
        }
        self.assertRefused(self.client.post(reverse("order-list"), payload))
        self.assertFalse(Order.objects.filter(order_number="CMD-INTRUSION").exists())

    def test_anonymous_product_detail_methods_are_refused(self):
        detail = reverse("product-detail", args=[self.product.id])
        payload = {"name": "Modifié", "purchase_price": "1.00", "selling_price": "2.00"}

        self.assertRefused(self.client.get(detail))
        self.assertRefused(self.client.put(detail, payload))
        self.assertRefused(self.client.patch(detail, {"name": "Modifié"}))
        self.assertRefused(self.client.delete(detail))

        self.product.refresh_from_db()
        self.assertEqual(self.product.name, "Produit de test")

    def test_anonymous_order_detail_methods_are_refused(self):
        detail = reverse("order-detail", args=[self.order.id])

        self.assertRefused(self.client.get(detail))
        self.assertRefused(self.client.patch(detail, {"status": "delivered"}))
        self.assertRefused(self.client.delete(detail))

        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)


class TokenLoginTests(SecuredApiTestCase):
    """Endpoint de connexion par jeton."""

    def test_login_endpoint_is_reachable_anonymously(self):
        response = self.client.post(
            reverse("api-token-auth"),
            {"username": self.user.username, "password": PASSWORD},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_invalid_credentials_do_not_return_a_token(self):
        response = self.client.post(
            reverse("api-token-auth"),
            {"username": self.user.username, "password": "mauvais-mot-de-passe"},
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("token", response.data)

    def test_valid_credentials_return_a_token(self):
        response = self.client.post(
            reverse("api-token-auth"),
            {"username": self.user.username, "password": PASSWORD},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertEqual(response.data["token"], self.token.key)

    def test_invalid_token_is_refused(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid-token-value")
        self.assertRefused(self.client.get(reverse("product-list")))


class AuthenticatedAccessTests(SecuredApiTestCase):
    """Un utilisateur authentifié accède aux endpoints autorisés."""

    def test_authenticated_can_read_all_business_endpoints(self):
        self.authenticate()

        self.assertEqual(self.client.get(reverse("dashboard")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("product-list")).status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.get(reverse("order-list")).status_code, status.HTTP_200_OK)

    def test_authenticated_product_detail_is_accessible(self):
        self.authenticate()
        detail = reverse("product-detail", args=[self.product.id])
        response = self.client.get(detail)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.product.id)

    def test_authenticated_write_is_allowed(self):
        self.authenticate()
        payload = {
            "name": "Nouveau produit",
            "purchase_price": "500.00",
            "selling_price": "900.00",
        }
        response = self.client.post(reverse("product-list"), payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        detail = reverse("product-detail", args=[response.data["id"]])
        self.assertEqual(self.client.delete(detail).status_code, status.HTTP_204_NO_CONTENT)


class PaginationTests(SecuredApiTestCase):
    """Pagination explicite (50 éléments par page)."""

    def setUp(self):
        super().setUp()
        self.authenticate()
        Product.objects.bulk_create(
            [
                Product(
                    name=f"Produit {index:03d}",
                    sku=f"SKU-{index:03d}",
                    purchase_price="100.00",
                    selling_price="200.00",
                )
                for index in range(60)
            ]
        )

    def test_product_list_is_paginated_with_page_size_50(self):
        response = self.client.get(reverse("product-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 61)
        self.assertEqual(len(response.data["results"]), 50)
        self.assertIsNotNone(response.data["next"])

    def test_second_page_contains_remaining_items(self):
        response = self.client.get(reverse("product-list"), {"page": 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 11)
        self.assertIsNone(response.data["next"])

    def test_order_list_is_paginated(self):
        response = self.client.get(reverse("order-list"))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("count", response.data)
        self.assertIn("results", response.data)
        self.assertEqual(response.data["count"], 1)


class LogoutTests(SecuredApiTestCase):
    """Révocation du jeton via POST /api/logout/."""

    def setUp(self):
        super().setUp()
        self.other_user = User.objects.create_user(
            username="autre-utilisateur",
            password=PASSWORD,
        )
        self.other_token = Token.objects.create(user=self.other_user)

    def test_authenticated_user_can_logout(self):
        self.authenticate()
        response = self.client.post(reverse("api-logout"))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_logout_deletes_the_current_token(self):
        self.authenticate()
        self.assertTrue(Token.objects.filter(key=self.token.key).exists())

        self.client.post(reverse("api-logout"))

        self.assertFalse(Token.objects.filter(key=self.token.key).exists())

    def test_revoked_token_cannot_access_products(self):
        self.authenticate()
        self.client.post(reverse("api-logout"))

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")
        self.assertRefused(self.client.get(reverse("product-list")))

    def test_anonymous_cannot_logout(self):
        self.assertRefused(self.client.post(reverse("api-logout")))
        self.assertTrue(Token.objects.filter(key=self.token.key).exists())

    def test_invalid_token_cannot_logout(self):
        self.client.credentials(HTTP_AUTHORIZATION="Token invalid-token-value")
        self.assertRefused(self.client.post(reverse("api-logout")))

    def test_logout_does_not_delete_other_users_token(self):
        self.authenticate()
        self.client.post(reverse("api-logout"))

        self.assertTrue(Token.objects.filter(key=self.other_token.key).exists())

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.other_token.key}")
        self.assertEqual(
            self.client.get(reverse("product-list")).status_code,
            status.HTTP_200_OK,
        )

    def test_login_again_after_logout_returns_a_new_working_token(self):
        self.authenticate()
        self.client.post(reverse("api-logout"))

        self.client.credentials()
        response = self.client.post(
            reverse("api-token-auth"),
            {"username": self.user.username, "password": PASSWORD},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)
        self.assertNotEqual(response.data["token"], self.token.key)

        self.client.credentials(HTTP_AUTHORIZATION=f"Token {response.data['token']}")
        self.assertEqual(
            self.client.get(reverse("product-list")).status_code,
            status.HTTP_200_OK,
        )


class DashboardEmptyDatabaseTests(APITestCase):
    """Dashboard sur une base vide : des zéros réels, aucune donnée inventée."""

    def setUp(self):
        self.user = User.objects.create_user(username="base-vide", password=PASSWORD)
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def get_dashboard(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_empty_database_returns_zero_counts(self):
        data = self.get_dashboard()

        self.assertEqual(data["counts"]["products"], 0)
        self.assertEqual(data["counts"]["orders"], 0)
        self.assertEqual(data["counts"]["pendingOrders"], 0)
        self.assertEqual(data["counts"]["deliveredOrders"], 0)
        self.assertEqual(sum(data["counts"]["ordersByStatus"].values()), 0)

    def test_empty_database_returns_zero_amounts(self):
        data = self.get_dashboard()

        for key in ("realized", "inProgress", "cancelled", "allOrders"):
            self.assertEqual(data["revenue"][key], "0.00")

        self.assertEqual(data["deliveryCosts"]["allOrders"], "0.00")
        self.assertEqual(data["costs"]["realized"]["total"], "0.00")
        self.assertEqual(data["profit"]["realized"], "0.00")

    def test_empty_database_has_no_sales_series(self):
        self.assertEqual(self.get_dashboard()["salesSeries"], [])


class DashboardMetricsTests(SecuredApiTestCase):
    """Indicateurs du dashboard calculés depuis la base réelle.

    Fixture de base : produit (achat 1000, vente 1500, emballage 0) et une
    commande en attente (quantité 2, prix unitaire 1500, livraison 0).
    """

    def setUp(self):
        super().setUp()
        self.authenticate()

    def get_dashboard(self):
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        return response.data

    def test_anonymous_access_is_refused(self):
        self.client.credentials()
        self.assertRefused(self.client.get(reverse("dashboard")))

    def test_counts_reflect_the_database(self):
        data = self.get_dashboard()

        self.assertEqual(data["counts"]["products"], 1)
        self.assertEqual(data["counts"]["orders"], 1)
        self.assertEqual(data["counts"]["pendingOrders"], 1)
        self.assertEqual(data["counts"]["deliveredOrders"], 0)
        self.assertEqual(
            set(data["counts"]["ordersByStatus"]),
            {value for value, _ in Order.Status.choices},
        )
        self.assertEqual(data["counts"]["ordersByStatus"]["pending"], 1)

    def test_pending_order_is_not_counted_as_realized_revenue(self):
        data = self.get_dashboard()

        self.assertEqual(data["revenue"]["realized"], "0.00")
        self.assertEqual(data["revenue"]["inProgress"], "3000.00")
        self.assertEqual(data["revenue"]["allOrders"], "3000.00")

    def test_delivered_order_produces_realized_revenue_and_estimated_costs(self):
        self.product.packaging_cost = "50.00"
        self.product.save(update_fields=["packaging_cost"])
        self.order.status = Order.Status.DELIVERED
        self.order.save(update_fields=["status"])

        data = self.get_dashboard()

        self.assertEqual(data["revenue"]["realized"], "3000.00")
        self.assertEqual(data["revenue"]["inProgress"], "0.00")

        costs = data["costs"]["realized"]
        self.assertEqual(costs["purchase"], "2000.00")
        self.assertEqual(costs["packaging"], "100.00")
        self.assertEqual(costs["delivery"], "0.00")
        self.assertEqual(costs["total"], "2100.00")
        self.assertTrue(costs["estimated"])

        self.assertEqual(data["profit"]["realized"], "900.00")
        self.assertTrue(data["profit"]["estimated"])

    def test_refused_and_returned_orders_are_excluded_from_realized_revenue(self):
        self.order.status = Order.Status.REFUSED
        self.order.save(update_fields=["status"])
        Order.objects.create(
            order_number="CMD-RETOURNEE-2",
            customer_name="Client retour",
            product=self.product,
            quantity=1,
            unit_price="1500.00",
            status=Order.Status.RETURNED,
        )

        data = self.get_dashboard()

        self.assertEqual(data["revenue"]["realized"], "0.00")
        self.assertEqual(data["revenue"]["cancelled"], "4500.00")
        self.assertEqual(data["counts"]["cancelledOrders"], 2)
        self.assertEqual(data["counts"]["deliveredOrders"], 0)

    def test_delivery_costs_use_the_frozen_order_value(self):
        self.order.delivery_cost = "20.00"
        self.order.save(update_fields=["delivery_cost"])

        data = self.get_dashboard()
        self.assertEqual(data["deliveryCosts"]["allOrders"], "20.00")
        self.assertEqual(data["deliveryCosts"]["realized"], "0.00")

        self.order.status = Order.Status.DELIVERED
        self.order.save(update_fields=["status"])

        data = self.get_dashboard()
        self.assertEqual(data["deliveryCosts"]["realized"], "20.00")
        self.assertEqual(data["costs"]["realized"]["delivery"], "20.00")

    def test_sales_series_groups_revenue_by_day_and_ignores_other_statuses(self):
        self.order.status = Order.Status.DELIVERED
        self.order.save(update_fields=["status"])
        Order.objects.create(
            order_number="CMD-LIVREE-2",
            customer_name="Client livré",
            product=self.product,
            quantity=1,
            unit_price="1500.00",
            status=Order.Status.DELIVERED,
        )
        Order.objects.create(
            order_number="CMD-EN-ATTENTE-3",
            customer_name="Client en attente",
            product=self.product,
            quantity=5,
            unit_price="1500.00",
            status=Order.Status.PENDING,
        )

        series = self.get_dashboard()["salesSeries"]

        self.assertEqual(len(series), 1)
        self.assertEqual(series[0]["orders"], 2)
        self.assertEqual(series[0]["revenue"], "4500.00")
        self.assertEqual(len(series[0]["date"]), 10)

    def test_payload_contains_no_fictitious_indicators(self):
        data = self.get_dashboard()

        self.assertNotIn("adSpend", data)
        self.assertNotIn("sales", data)
        self.assertNotIn("deliveryCosts_", data)
        self.assertEqual(data["currency"], "DZD")
        self.assertIn("generatedAt", data)
        self.assertEqual(
            [metric["key"] for metric in data["unavailableMetrics"]],
            ["adSpend", "historicalUnitCosts"],
        )


class OrderValidationTests(SecuredApiTestCase):
    """Fiabilité de la gestion des commandes : validation et cohérence.

    Fixture de base : produit (achat 1000, vente 1500, stock 0) et une
    commande « CMD-TEST-1 » (quantité 2, prix unitaire 1500, en attente).
    """

    def setUp(self):
        super().setUp()
        self.authenticate()

    def order_payload(self, **overrides):
        payload = {
            "order_number": "CMD-VALIDE-1",
            "customer_name": "Client valide",
            "customer_phone": "0555000000",
            "product": self.product.id,
            "quantity": 3,
            "unit_price": "1500.00",
            "delivery_cost": "250.00",
        }
        payload.update(overrides)
        return payload

    def create_order(self, **overrides):
        return self.client.post(reverse("order-list"), self.order_payload(**overrides))

    def assertRejected(self, response, field):
        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
            msg=f"Statut inattendu : {response.status_code}",
        )
        self.assertIn(field, response.data)

    # --- 1. création valide ---------------------------------------------
    def test_valid_order_creation_succeeds(self):
        response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        order = Order.objects.get(order_number="CMD-VALIDE-1")
        self.assertEqual(order.quantity, 3)
        self.assertEqual(order.unit_price, Decimal("1500.00"))
        self.assertEqual(order.delivery_cost, Decimal("250.00"))
        self.assertEqual(order.status, Order.Status.PENDING)
        self.assertEqual(response.data["total_amount"], "4500.00")
        self.assertEqual(response.data["product_name"], self.product.name)

    def test_creation_does_not_modify_stock(self):
        before = self.product.stock_quantity

        self.create_order()

        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, before)

    # --- 2. quantité ------------------------------------------------------
    def test_zero_quantity_is_refused(self):
        self.assertRejected(self.create_order(quantity=0), "quantity")
        self.assertFalse(Order.objects.filter(order_number="CMD-VALIDE-1").exists())

    def test_negative_quantity_is_refused(self):
        self.assertRejected(self.create_order(quantity=-3), "quantity")

    def test_non_integer_quantity_is_refused(self):
        self.assertRejected(self.create_order(quantity="1.5"), "quantity")

    def test_omitted_quantity_falls_back_to_model_default(self):
        payload = self.order_payload()
        payload.pop("quantity")

        response = self.client.post(reverse("order-list"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["quantity"], 1)

    # --- 3. prix unitaire -------------------------------------------------
    def test_negative_unit_price_is_refused(self):
        self.assertRejected(self.create_order(unit_price="-10.00"), "unit_price")

    def test_non_numeric_unit_price_is_refused(self):
        self.assertRejected(self.create_order(unit_price="gratuit"), "unit_price")

    def test_unit_price_with_three_decimals_is_refused(self):
        self.assertRejected(self.create_order(unit_price="10.999"), "unit_price")

    def test_missing_unit_price_is_refused(self):
        payload = self.order_payload()
        payload.pop("unit_price")

        self.assertRejected(self.client.post(reverse("order-list"), payload), "unit_price")

    def test_zero_unit_price_is_allowed(self):
        response = self.create_order(unit_price="0.00")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["total_amount"], "0.00")

    # --- 4. frais de livraison -------------------------------------------
    def test_negative_delivery_cost_is_refused(self):
        self.assertRejected(self.create_order(delivery_cost="-5.00"), "delivery_cost")

    def test_missing_delivery_cost_falls_back_to_zero(self):
        payload = self.order_payload()
        payload.pop("delivery_cost")

        response = self.client.post(reverse("order-list"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["delivery_cost"], "0.00")

    # --- 5. produit -------------------------------------------------------
    def test_unknown_product_is_refused(self):
        self.assertRejected(self.create_order(product=999999), "product")

    def test_missing_product_is_refused(self):
        payload = self.order_payload()
        payload.pop("product")

        self.assertRejected(self.client.post(reverse("order-list"), payload), "product")

    # --- 6. statut --------------------------------------------------------
    def test_unknown_status_is_refused(self):
        self.assertRejected(self.create_order(status="inconnu"), "status")

    def test_creation_accepts_pending_and_refused(self):
        # Seuls ces deux statuts sont créables directement (aucun mouvement de
        # stock) ; les autres s'obtiennent par une transition contrôlée.
        for index, value in enumerate((Order.Status.PENDING, Order.Status.REFUSED)):
            response = self.create_order(
                order_number=f"CMD-STATUT-{index}",
                status=value,
            )
            self.assertEqual(
                response.status_code,
                status.HTTP_201_CREATED,
                msg=f"Statut refusé à tort : {value}",
            )
            self.assertEqual(response.data["status"], value)

    def test_creation_in_controlled_statuses_is_refused(self):
        controlled = (
            Order.Status.CONFIRMED,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
            Order.Status.RETURNED,
        )

        for index, value in enumerate(controlled):
            order_number = f"CMD-CONTROLE-{index}"
            response = self.create_order(order_number=order_number, status=value)

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                msg=f"Création acceptée à tort : {value}",
            )
            self.assertIn("status", response.data)
            self.assertFalse(Order.objects.filter(order_number=order_number).exists())

    # --- champs client ----------------------------------------------------
    def test_customer_name_is_required(self):
        self.assertRejected(self.create_order(customer_name=""), "customer_name")

    def test_customer_phone_remains_optional(self):
        payload = self.order_payload()
        payload.pop("customer_phone")

        response = self.client.post(reverse("order-list"), payload)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["customer_phone"], "")

    # --- 7. modification valide ------------------------------------------
    def test_valid_update_succeeds(self):
        detail = reverse("order-detail", args=[self.order.id])

        response = self.client.patch(
            detail,
            {"quantity": 5, "customer_name": "Client mis à jour"},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 5)
        self.assertEqual(self.order.customer_name, "Client mis à jour")
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(response.data["total_amount"], "7500.00")

    def test_update_refuses_negative_unit_price(self):
        detail = reverse("order-detail", args=[self.order.id])

        response = self.client.patch(detail, {"unit_price": "-1.00"})

        self.assertRejected(response, "unit_price")
        self.order.refresh_from_db()
        self.assertEqual(self.order.unit_price, Decimal("1500.00"))

    def test_update_without_status_change_does_not_modify_stock(self):
        before = self.product.stock_quantity
        detail = reverse("order-detail", args=[self.order.id])

        response = self.client.patch(detail, {"customer_name": "Autre nom"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.product.refresh_from_db()
        self.order.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, before)
        self.assertEqual(self.order.status, Order.Status.PENDING)

    # --- 8. prix historique ----------------------------------------------
    def test_changing_product_price_does_not_rewrite_existing_orders(self):
        self.product.selling_price = "1999.00"
        self.product.save(update_fields=["selling_price"])

        detail = reverse("order-detail", args=[self.order.id])
        response = self.client.get(detail)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["unit_price"], "1500.00")
        self.order.refresh_from_db()
        self.assertEqual(self.order.unit_price, Decimal("1500.00"))

    def test_order_keeps_the_price_provided_at_creation(self):
        response = self.create_order(unit_price="1234.56")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["unit_price"], "1234.56")

    def test_status_change_keeps_the_recorded_price(self):
        detail = reverse("order-detail", args=[self.order.id])

        response = self.client.patch(detail, {"status": Order.Status.REFUSED})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.REFUSED)
        self.assertEqual(self.order.unit_price, Decimal("1500.00"))

    # --- 10. suppression --------------------------------------------------
    def test_order_deletion_succeeds_without_touching_stock(self):
        before = self.product.stock_quantity
        detail = reverse("order-detail", args=[self.order.id])

        response = self.client.delete(detail)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(id=self.order.id).exists())
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock_quantity, before)

    # --- 9. authentification ---------------------------------------------
    def test_anonymous_write_is_refused_before_validation(self):
        self.client.credentials()

        response = self.client.post(reverse("order-list"), self.order_payload(quantity=0))

        self.assertRefused(response)
        self.assertNotIn("quantity", response.data)


class OrderStockTransitionTests(SecuredApiTestCase):
    """Stock et transitions de statut des commandes.

    Règle métier : décrément du stock à ``pending → confirmed`` ; restitution
    sur ``confirmed → refused``, ``shipped → refused``, ``shipped → returned``
    et ``delivered → returned``. La décision dépend de la transition
    réellement demandée, jamais du seul statut final.

    Fixture : produit à 10 en stock, commande « CMD-TEST-1 » en attente
    (quantité 2).
    """

    PENDING = Order.Status.PENDING
    CONFIRMED = Order.Status.CONFIRMED
    SHIPPED = Order.Status.SHIPPED
    DELIVERED = Order.Status.DELIVERED
    REFUSED = Order.Status.REFUSED
    RETURNED = Order.Status.RETURNED

    # Chemins de transitions valides pour atteindre un statut depuis pending.
    PATHS = {
        Order.Status.PENDING: [],
        Order.Status.CONFIRMED: [Order.Status.CONFIRMED],
        Order.Status.SHIPPED: [Order.Status.CONFIRMED, Order.Status.SHIPPED],
        Order.Status.DELIVERED: [
            Order.Status.CONFIRMED,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
        ],
        Order.Status.REFUSED: [Order.Status.REFUSED],
        Order.Status.RETURNED: [
            Order.Status.CONFIRMED,
            Order.Status.SHIPPED,
            Order.Status.RETURNED,
        ],
    }

    def setUp(self):
        super().setUp()
        self.authenticate()
        self.product.stock_quantity = 10
        self.product.save(update_fields=["stock_quantity"])

    # --- utilitaires ------------------------------------------------------
    def detail(self, order):
        return reverse("order-detail", args=[order.id])

    def patch_status(self, order, new_status):
        return self.client.patch(self.detail(order), {"status": new_status})

    def create_order(self, **overrides):
        payload = {
            "order_number": "CMD-STOCK-1",
            "customer_name": "Client stock",
            "product": self.product.id,
            "quantity": 3,
            "unit_price": "1500.00",
            "delivery_cost": "0.00",
        }
        payload.update(overrides)
        return self.client.post(reverse("order-list"), payload)

    def stock(self):
        self.product.refresh_from_db()
        return self.product.stock_quantity

    def reach(self, target, order=None):
        order = order or self.order
        for step in self.PATHS[target]:
            response = self.patch_status(order, step)
            self.assertEqual(
                response.status_code,
                status.HTTP_200_OK,
                msg=f"Étape de transition refusée : {step}",
            )
        order.refresh_from_db()
        self.assertEqual(order.status, target)
        return order

    def assertTransitionRefused(self, order, target):
        before_status = order.status
        before_stock = self.stock()

        response = self.patch_status(order, target)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)
        order.refresh_from_db()
        self.assertEqual(order.status, before_status)
        self.assertEqual(self.stock(), before_stock)

    def put_payload(self, order, **overrides):
        payload = {
            "order_number": order.order_number,
            "customer_name": order.customer_name,
            "customer_phone": order.customer_phone,
            "product": order.product_id,
            "quantity": order.quantity,
            "unit_price": str(order.unit_price),
            "delivery_cost": str(order.delivery_cost),
            "status": order.status,
            "notes": order.notes,
        }
        payload.update(overrides)
        return payload

    # --- confirmation -----------------------------------------------------
    def test_confirmation_deducts_exactly_the_ordered_quantity(self):
        response = self.patch_status(self.order, Order.Status.CONFIRMED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.stock(), 8)

    def test_insufficient_stock_blocks_confirmation(self):
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])

        response = self.patch_status(self.order, Order.Status.CONFIRMED)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("status", response.data)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.stock(), 1)

    def test_confirmation_uses_the_quantity_of_the_same_request(self):
        response = self.client.patch(
            self.detail(self.order),
            {"quantity": 4, "status": Order.Status.CONFIRMED},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 4)
        self.assertEqual(self.stock(), 6)

    def test_repeating_confirmed_does_not_deduct_twice(self):
        self.patch_status(self.order, Order.Status.CONFIRMED)
        self.assertEqual(self.stock(), 8)

        response = self.patch_status(self.order, Order.Status.CONFIRMED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.stock(), 8)

    def test_patch_without_status_change_keeps_stock(self):
        self.reach(Order.Status.CONFIRMED)
        before = self.stock()

        response = self.client.patch(
            self.detail(self.order), {"customer_name": "Nouveau nom"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), before)

    # --- création ---------------------------------------------------------
    def test_creation_in_pending_does_not_touch_stock(self):
        response = self.create_order()

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(self.stock(), 10)

    def test_creation_in_refused_is_allowed_without_stock_movement(self):
        response = self.create_order(status=Order.Status.REFUSED)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["status"], Order.Status.REFUSED)
        self.assertEqual(self.stock(), 10)

    def test_creation_in_controlled_statuses_is_refused(self):
        controlled = (
            Order.Status.CONFIRMED,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
            Order.Status.RETURNED,
        )

        for index, value in enumerate(controlled):
            order_number = f"CMD-DIRECT-{index}"
            response = self.create_order(order_number=order_number, status=value)

            self.assertEqual(
                response.status_code,
                status.HTTP_400_BAD_REQUEST,
                msg=f"Création acceptée à tort : {value}",
            )
            self.assertFalse(Order.objects.filter(order_number=order_number).exists())

        self.assertEqual(self.stock(), 10)

    # --- transitions autorisées / interdites ------------------------------
    def test_allowed_transitions_are_accepted(self):
        cases = (
            (Order.Status.PENDING, Order.Status.CONFIRMED),
            (Order.Status.PENDING, Order.Status.REFUSED),
            (Order.Status.CONFIRMED, Order.Status.SHIPPED),
            (Order.Status.CONFIRMED, Order.Status.REFUSED),
            (Order.Status.SHIPPED, Order.Status.DELIVERED),
            (Order.Status.SHIPPED, Order.Status.REFUSED),
            (Order.Status.SHIPPED, Order.Status.RETURNED),
            (Order.Status.DELIVERED, Order.Status.RETURNED),
        )
        self.product.stock_quantity = 100
        self.product.save(update_fields=["stock_quantity"])

        for index, (start, target) in enumerate(cases):
            with self.subTest(transition=f"{start} -> {target}"):
                response = self.create_order(order_number=f"CMD-OK-{index}")
                order = Order.objects.get(pk=response.data["id"])
                self.reach(start, order=order)

                result = self.patch_status(order, target)

                self.assertEqual(result.status_code, status.HTTP_200_OK)
                order.refresh_from_db()
                self.assertEqual(order.status, target)

    def test_forbidden_transitions_are_refused(self):
        cases = [
            (Order.Status.PENDING, Order.Status.SHIPPED),
            (Order.Status.PENDING, Order.Status.DELIVERED),
            (Order.Status.PENDING, Order.Status.RETURNED),
            (Order.Status.CONFIRMED, Order.Status.PENDING),
            (Order.Status.CONFIRMED, Order.Status.DELIVERED),
            (Order.Status.CONFIRMED, Order.Status.RETURNED),
            (Order.Status.SHIPPED, Order.Status.PENDING),
            (Order.Status.SHIPPED, Order.Status.CONFIRMED),
            (Order.Status.DELIVERED, Order.Status.PENDING),
            (Order.Status.DELIVERED, Order.Status.CONFIRMED),
            (Order.Status.DELIVERED, Order.Status.SHIPPED),
            (Order.Status.DELIVERED, Order.Status.REFUSED),
            (Order.Status.REFUSED, Order.Status.PENDING),
            (Order.Status.REFUSED, Order.Status.CONFIRMED),
            (Order.Status.REFUSED, Order.Status.RETURNED),
            (Order.Status.RETURNED, Order.Status.PENDING),
            (Order.Status.RETURNED, Order.Status.DELIVERED),
            (Order.Status.RETURNED, Order.Status.REFUSED),
        ]
        self.product.stock_quantity = 100
        self.product.save(update_fields=["stock_quantity"])

        for start, target in cases:
            with self.subTest(transition=f"{start}->{target}"):
                created = self.create_order(order_number=f"CMD-NO-{start}-{target}")
                order = Order.objects.get(pk=created.data["id"])
                self.reach(start, order=order)

                self.assertTransitionRefused(order, target)

    def test_terminal_statuses_cannot_be_left(self):
        targets = (
            Order.Status.PENDING,
            Order.Status.CONFIRMED,
            Order.Status.SHIPPED,
            Order.Status.DELIVERED,
            Order.Status.REFUSED,
            Order.Status.RETURNED,
        )

        for index, terminal in enumerate(
            (Order.Status.REFUSED, Order.Status.RETURNED)
        ):
            with self.subTest(terminal=terminal):
                created = self.create_order(order_number=f"CMD-TERM-{index}")
                order = Order.objects.get(pk=created.data["id"])
                self.reach(terminal, order=order)

                for target in targets:
                    if target == terminal:
                        continue
                    self.assertTransitionRefused(order, target)

    # --- refus et retours -------------------------------------------------
    def test_pending_to_refused_does_not_touch_stock(self):
        response = self.patch_status(self.order, Order.Status.REFUSED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.REFUSED)
        self.assertEqual(self.stock(), 10)

    def test_confirmed_to_refused_restores_stock_once(self):
        self.reach(Order.Status.CONFIRMED)
        self.assertEqual(self.stock(), 8)

        response = self.patch_status(self.order, Order.Status.REFUSED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 10)

        repeat = self.patch_status(self.order, Order.Status.REFUSED)

        self.assertEqual(repeat.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 10)

    def test_shipped_to_refused_restores_stock_once(self):
        self.reach(Order.Status.SHIPPED)
        self.assertEqual(self.stock(), 8)

        response = self.patch_status(self.order, Order.Status.REFUSED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 10)

    def test_shipped_to_returned_restores_stock_once(self):
        self.reach(Order.Status.SHIPPED)
        self.assertEqual(self.stock(), 8)

        response = self.patch_status(self.order, Order.Status.RETURNED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 10)

        repeat = self.patch_status(self.order, Order.Status.RETURNED)

        self.assertEqual(repeat.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 10)

    def test_delivered_to_returned_restores_stock_once(self):
        self.reach(Order.Status.DELIVERED)
        self.assertEqual(self.stock(), 8)

        response = self.patch_status(self.order, Order.Status.RETURNED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.stock(), 10)

    # --- intégrité (quantité / produit) -----------------------------------
    def test_quantity_change_is_refused_after_confirmation(self):
        self.reach(Order.Status.CONFIRMED)

        response = self.client.patch(self.detail(self.order), {"quantity": 5})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("quantity", response.data)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 2)
        self.assertEqual(self.stock(), 8)

    def test_product_change_is_refused_after_confirmation(self):
        other = Product.objects.create(
            name="Produit alternatif",
            purchase_price="100.00",
            selling_price="200.00",
            stock_quantity=7,
        )
        self.reach(Order.Status.SHIPPED)

        response = self.client.patch(self.detail(self.order), {"product": other.pk})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("product", response.data)
        self.order.refresh_from_db()
        other.refresh_from_db()
        self.assertEqual(self.order.product_id, self.product.id)
        self.assertEqual(self.stock(), 8)
        self.assertEqual(other.stock_quantity, 7)

    def test_quantity_and_product_changes_are_allowed_while_pending(self):
        other = Product.objects.create(
            name="Produit alternatif",
            purchase_price="100.00",
            selling_price="200.00",
            stock_quantity=7,
        )

        response = self.client.patch(
            self.detail(self.order),
            {"quantity": 4, "product": other.id},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.quantity, 4)
        self.assertEqual(self.order.product_id, other.id)
        self.assertEqual(self.stock(), 10)
        other.refresh_from_db()
        self.assertEqual(other.stock_quantity, 7)

    # --- suppression ------------------------------------------------------
    def test_order_deletion_is_refused_while_stock_is_deducted(self):
        for index, target in enumerate(
            (
                Order.Status.CONFIRMED,
                Order.Status.SHIPPED,
                Order.Status.DELIVERED,
            )
        ):
            with self.subTest(status=target):
                created = self.create_order(order_number=f"CMD-DEL-{index}")
                order = Order.objects.get(pk=created.data["id"])
                self.reach(target, order=order)
                before_stock = self.stock()

                response = self.client.delete(self.detail(order))

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("status", response.data)
                self.assertTrue(Order.objects.filter(pk=order.pk).exists())
                self.assertEqual(self.stock(), before_stock)

    def test_returned_order_deletion_is_refused(self):
        self.reach(Order.Status.RETURNED)

        response = self.client.delete(self.detail(self.order))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())
        self.assertEqual(self.stock(), 10)

    def test_pending_order_deletion_is_allowed_without_stock_change(self):
        response = self.client.delete(self.detail(self.order))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Order.objects.filter(pk=self.order.pk).exists())
        self.assertEqual(self.stock(), 10)

    def test_refused_order_deletion_is_allowed_without_stock_change(self):
        self.reach(Order.Status.REFUSED)

        response = self.client.delete(self.detail(self.order))

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(self.stock(), 10)

    # --- atomicité / modifications partielles -----------------------------
    def test_failed_confirmation_leaves_no_partial_change(self):
        self.product.stock_quantity = 1
        self.product.save(update_fields=["stock_quantity"])

        response = self.client.patch(
            self.detail(self.order),
            {"status": Order.Status.CONFIRMED, "customer_name": "Nom partiel"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.order.customer_name, "Client de test")
        self.assertEqual(self.stock(), 1)

    def test_failed_transition_leaves_no_partial_change(self):
        self.reach(Order.Status.CONFIRMED)

        response = self.client.patch(
            self.detail(self.order),
            {"status": Order.Status.PENDING, "notes": "note partielle"},
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.order.notes, "")
        self.assertEqual(self.stock(), 8)

    # --- données existantes (antérieures à la fonctionnalité) -------------
    def test_legacy_order_without_status_change_does_not_move_stock(self):
        legacy = Order.objects.create(
            order_number="CMD-LEGACY-1",
            customer_name="Ancienne commande",
            product=self.product,
            quantity=2,
            unit_price="1500.00",
            status=Order.Status.CONFIRMED,
        )

        response = self.client.patch(
            self.detail(legacy), {"customer_name": "Renommée"}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        legacy.refresh_from_db()
        self.assertEqual(legacy.status, Order.Status.CONFIRMED)
        self.assertEqual(legacy.customer_name, "Renommée")
        self.assertEqual(self.stock(), 10)

    def test_legacy_confirmed_order_refused_restores_stock_per_transition(self):
        # Comportement assumé : la restitution dépend de la transition réelle
        # (confirmed → refused), même pour une commande historique dont le
        # stock n'avait jamais été décrémenté.
        legacy = Order.objects.create(
            order_number="CMD-LEGACY-2",
            customer_name="Ancienne commande",
            product=self.product,
            quantity=2,
            unit_price="1500.00",
            status=Order.Status.CONFIRMED,
        )

        response = self.patch_status(legacy, Order.Status.REFUSED)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        legacy.refresh_from_db()
        self.assertEqual(legacy.status, Order.Status.REFUSED)
        self.assertEqual(self.stock(), 12)

    # --- mises à jour complètes (PUT) -------------------------------------
    def test_full_put_without_status_change_does_not_deduct_twice(self):
        self.reach(Order.Status.CONFIRMED)

        response = self.client.put(self.detail(self.order), self.put_payload(self.order))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.stock(), 8)

    def test_full_put_can_confirm_a_pending_order(self):
        response = self.client.put(
            self.detail(self.order),
            self.put_payload(self.order, status=Order.Status.CONFIRMED),
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.CONFIRMED)
        self.assertEqual(self.stock(), 8)

    def test_full_put_omitting_status_keeps_the_current_status(self):
        # DRF ne recopie pas les valeurs par défaut du modèle dans les champs
        # du serializer : un PUT qui omet `status` ne réinitialise donc pas la
        # commande à 'pending' et ne provoque aucun mouvement de stock.
        self.reach(Order.Status.DELIVERED)

        payload = self.put_payload(self.order)
        payload.pop("status")

        response = self.client.put(self.detail(self.order), payload)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.DELIVERED)
        self.assertEqual(self.stock(), 8)

    # --- authentification -------------------------------------------------
    def test_anonymous_transition_is_refused(self):
        self.client.credentials()

        response = self.patch_status(self.order, Order.Status.CONFIRMED)

        self.assertRefused(response)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PENDING)
        self.assertEqual(self.stock(), 10)
