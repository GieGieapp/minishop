from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Order
from .serializers import OrderSerializer
from ..accounts.permissions import RBACOrderPermission


class OrderViewSet(ModelViewSet):
    queryset = Order.objects.all().order_by("-id")
    serializer_class = OrderSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [IsAuthenticated, RBACOrderPermission]
    search_fields = ["id", "status"]
    ordering_fields = ["id", "created_at", "status"]
