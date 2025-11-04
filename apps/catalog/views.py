from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from apps.accounts.permissions import RBACProductPermission
from .models import Product
from .serializers import ProductSerializer


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [IsAuthenticated, RBACProductPermission]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["name", "sku"]
    ordering_fields = ["created_at", "price", "stock"]
    ordering = ["-created_at"]
