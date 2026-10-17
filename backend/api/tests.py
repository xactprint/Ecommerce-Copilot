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
