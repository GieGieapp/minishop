from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes, authentication_classes
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Invitation
from .permissions import (
    IsAdminOrManager,
    RBACUserPermission,
)
from .serializers import (
    UserSerializer,
    InvitationSerializer,
    AcceptInvitationSerializer, UserMeSerializer,
)
from .utils import send_invitation_email

User = get_user_model()


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        return Response(UserMeSerializer(request.user).data)


class LogoutView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        return Response(status=204)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated,IsAdminOrManager]
    filter_backends = [SearchFilter, OrderingFilter]
    search_fields = ["username", "email", "first_name", "last_name"]
    ordering_fields = ["id", "username", "email"]


class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all().order_by("-created_at")
    serializer_class = InvitationSerializer
    authentication_classes = (JWTAuthentication,)
    permission_classes = [IsAuthenticated, RBACUserPermission]

    def perform_create(self, serializer):
        obj = serializer.save(invited_by=self.request.user)
        send_invitation_email(obj.email, obj.token)

    @action(detail=True, methods=["post"])
    def resend(self, request, pk=None):
        inv = self.get_object()
        if not inv.is_active():
            return Response({"detail": "Invitation is not active (revoked/used/expired)."}, status=400)
        send_invitation_email(inv.email, str(inv.token))
        return Response({"detail": "Resent."})

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        inv = self.get_object()
        if inv.revoked_at:
            return Response({"detail": "Already revoked."}, status=400)
        if inv.used_at:
            return Response({"detail": "Already accepted; cannot revoke."}, status=400)
        inv.revoked_at = timezone.now()
        inv.save(update_fields=["revoked_at"])
        return Response({"detail": "Revoked."}, status=200)


@api_view(["POST"])
@permission_classes([AllowAny])
@authentication_classes([])
def accept_invitation(request):
    ser = AcceptInvitationSerializer(data=request.data)
    ser.is_valid(raise_exception=True)

    token = ser.validated_data.get("token")
    try:
        inv = Invitation.objects.get(token=token)
    except Invitation.DoesNotExist:
        return Response({"detail": "Invalid invitation token."}, status=400)

    if not inv.is_active():
        return Response({"detail": "Invitation is not active."}, status=400)

    user = ser.save()
    return Response(
        {"id": user.id, "username": user.username, "email": user.email},
        status=status.HTTP_201_CREATED,
    )