
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import Product, Order
from .serializers import ProductSerializer, OrderSerializer


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.select_related("product").all()
    serializer_class = OrderSerializer


@api_view(["GET"])
def dashboard(request):
    data = {
        "profit": 84500,
        "sales": 245000,
        "adSpend": 42000,
        "deliveryCosts": 18500,
        "currency": "DZD",
    }

    return Response(data)
