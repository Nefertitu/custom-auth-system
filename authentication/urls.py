from django.urls import include, path
from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter

from .apps import AuthenticationConfig
from .views import (
    CustomLoginView,
    CustomLogoutView,
    CustomRefreshTokenView,
    UserCreateApiView,
    UserProfileViewSet,
)

app_name = AuthenticationConfig.name


router = DefaultRouter()
router.register(r"", UserProfileViewSet, basename="authentication")

urlpatterns = [
    # path("", include(router.urls)),
    path("register/", UserCreateApiView.as_view(), name="register"),
    path("login/", CustomLoginView.as_view(permission_classes=(AllowAny,)), name="login"),
    path("token/refresh/", CustomRefreshTokenView.as_view(), name="token_refresh"),
    path("logout/", CustomLogoutView.as_view(next_page="authentication:login"), name="logout"),
] + router.urls
