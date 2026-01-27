from django.urls import include, path
from rest_framework.routers import DefaultRouter

from permissionsapp.apps import PermissionsappConfig
from permissionsapp.views import PermissionManagementViewSet

app_name = PermissionsappConfig.name


router = DefaultRouter()
router.register(r"", PermissionManagementViewSet, basename="permissions")

urlpatterns = [
    path("", include(router.urls)),
]
