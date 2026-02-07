from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

router = DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/auth/", include("authentication.urls", namespace="authentication")),
    path("api/products/", include("products.urls", namespace="products")),
    path("api/permissions/", include("permissionsapp.urls", namespace="permissionsapp")),
] + router.urls
