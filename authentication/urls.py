from rest_framework.routers import DefaultRouter

from authentication.apps import AuthenticationConfig
# from authentication.views import (
#     UserCreateApiView,
#     UserProfileViewSet,
# )

app_name = AuthenticationConfig.name


router = DefaultRouter()
#router.register(r"", UserProfileViewSet, basename="user")
