from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse, resolve
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import User


class UserTestCase(APITestCase):
    """Тест кейс для проверки CRUD представлений модели User"""

    def setUp(self) -> None:
        """Инициализация тестовых данных"""

        self.user = User.objects.create(
            email="testuser@example.com",
            first_name="Test User",
        )
        self.user.set_password("testpassword123")
        self.user.save()

        self.client.force_authenticate(user=self.user)

        self.user_manager = User.objects.create(
            email="usermanager@example.com",
            first_name="User Manager",
            is_staff=True
        )
        self.user_manager.set_password("123www")
        user_content_type = ContentType.objects.get_for_model(User)
        can_view_all_users = Permission.objects.get(codename="can_view_all_users", content_type=user_content_type)
        can_delete_user = Permission.objects.get(codename="can_delete_user", content_type=user_content_type)
        self.user_manager.user_permissions.add(can_view_all_users, can_delete_user)
        self.user_manager.save()

    def test_user_retrieve(self) -> None:
        """Тест получения деталей информации о пользователе"""

        url = reverse("authentication:authentication-detail", kwargs={"pk": self.user.pk})
        response = self.client.get(url)
        data = response.json()
        print(data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(data.get("email"), self.user.email)
        self.assertEqual(data.get("first_name"), self.user.first_name)
        self.assertEqual(True, self.user.is_active)
        self.assertEqual(True, self.user.is_authenticated)
        self.assertEqual(False, self.user.is_superuser)

    def test_real_authentication(self):
        """Тест реальной аутентификации с паролем"""

        response = self.client.post(
            reverse("authentication:login"),
            {"email": "testuser@example.com", "password": "testpassword123"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("tokens", response.json())

    def test_user_create(self) -> None:
        """Тест создания нового пользователя"""

        url = reverse("authentication:authentication-list")
        data = {
            "email": "newtestuser@example.com",
            "password": "123qqq",
            "password_confirm": "123qqq",
            "first_name": "New Test User",
        }
        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(data.get("first_name"), "New Test User")
        self.assertEqual(User.objects.all().count(), 3)

    def test_user_update(self) -> None:
        """Тест обновления деталей привычки"""

        url = reverse("authentication:authentication-detail", kwargs={"pk": self.user.pk})
        data = {
            "first_name": "First Test User",
        }
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(url, data, format="json")
        data = response.json()

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()

        self.assertEqual(self.user.first_name, "First Test User")
        self.assertEqual(data.get("first_name"), "First Test User")
        self.assertEqual(data.get("id"), self.user.pk)

        match = resolve(url)
        view = match.func

        if hasattr(view, "cls"):
            view_class = view.cls

            if hasattr(view_class, "get_serializer_class"):
                view_instance = view_class()
                view_instance.action = "partial_update"
                view_instance.request = self.client.request()
                view_instance.format_kwarg = None

                serializer_class = view_instance.get_serializer_class()
                self.assertEqual(serializer_class.__name__, "UserProfileSerializer")

    def test_user_delete(self) -> None:
        """Тест удаления пользователя"""

        user_manager = self.user_manager
        self.client.force_authenticate(user=user_manager)

        user_to_delete = User.objects.create(email="todelete@example.com", first_name="User to delete")
        user_to_delete.set_password("123delete")
        user_to_delete.save()

        url = reverse("authentication:authentication-detail", kwargs={"pk": user_to_delete.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(User.DoesNotExist):
            User.objects.get(pk=user_to_delete.pk)

        self.assertEqual(User.objects.all().count(), 2)

