from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from recipe.domain import model as domain_model
from recipe.adapters import repository


CREATE_USER_URL = reverse("user:create")


class PublicUserApiTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.email = "test@example.com"
        self.name = "test"
        self.password = "Aa1234567"

        self.repo = repository.UserRepository()

    def test_create_user_success(self):
        user = domain_model.User(
            email=self.email, name=self.name, password=self.password
        )

        res = self.client.post(
            CREATE_USER_URL,
            dict(email=user.email, name=user.name, password=user.password),
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", res.data)

        user_dto = self.repo.get(user.email)
        self.assertTrue(user_dto.check_password(user.password))

    def test_create_user_exist_error(self):
        user = domain_model.User(
            email=self.email, name=self.name, password=self.password
        )

        self.repo.add(user)

        res = self.client.post(
            CREATE_USER_URL,
            dict(email=user.email, name=user.name, password=user.password),
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short_error(self):
        user = domain_model.User(
            email=self.email, name=self.name, password="pw"
        )

        res = self.client.post(
            CREATE_USER_URL,
            dict(email=user.email, name=user.name, password=user.password),
        )

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

        with self.assertRaises(self.repo.model.DoesNotExist):
            self.repo.get(email=user.email)
