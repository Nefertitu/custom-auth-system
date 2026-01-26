from django.contrib import admin
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from authentication.apps import AuthenticationConfig


app_name = AuthenticationConfig.name

router = DefaultRouter()

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("authentication.urls", namespace="authentication")),
]
