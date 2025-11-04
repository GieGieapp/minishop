from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import CurrentUserView, UserViewSet, InvitationViewSet, accept_invitation, LogoutView

router = DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"invitations", InvitationViewSet, basename="invitation")

urlpatterns = [
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("logout/", LogoutView.as_view(), name="logout"),

    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("me/", CurrentUserView.as_view(), name="me"),
    path("invitations/accept/", accept_invitation, name="invitation-accept"),
    path("", include(router.urls)),
]
