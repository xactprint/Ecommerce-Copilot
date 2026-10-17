
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import dashboard, ProductViewSet, OrderViewSet


router = DefaultRouter()

router.register("products", ProductViewSet, basename="product")
router.register("orders", OrderViewSet, basename="order")


urlpatterns = [
    path("dashboard/", dashboard, name="dashboard"),
    path("", include(router.urls)),
]
