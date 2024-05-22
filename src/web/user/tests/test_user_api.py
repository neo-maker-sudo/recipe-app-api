from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from recipe_menu.domain import model as domain_model
from recipe_menu.adapters import repository


CREATE_USER_URL = reverse("user:create")
TOKEN_URL = reverse("user:token")
ME_URL = reverse("user:me")


def create_user(
    email: str, name: str, password: str, repo: repository.UserRepository
):
    user = domain_model.User(email=email, name=name, password=password)
    return repo.add(user)


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

        user_dto = self.repo.get({"email": user.email})
        self.assertTrue(user_dto.check_password(user.password))

    def test_create_user_exist_error(self):
        user = create_user(
            email=self.email,
            name=self.name,
            password=self.password,
            repo=self.repo,
        )

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
            self.repo.get({"email": user.email})

    def test_create_token_for_user(self):
        user = create_user(
            email=self.email,
            name=self.name,
            password=self.password,
            repo=self.repo,
        )

        payload = dict(email=user.email, password=self.password)
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access_token", res.data)

    def test_create_token_bad_credentials(self):
        user = create_user(
            email=self.email,
            name=self.name,
            password=self.password,
            repo=self.repo,
        )

        payload = dict(email=user.email, password="pw")
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access_token", res.data)

    def test_create_token_blank_password(self):
        payload = dict(email=self.email, password="")
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access_token", res.data)

    def test_create_token_user_not_exist(self):
        payload = dict(email=self.email, password=self.password)
        res = self.client.post(TOKEN_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn("access_token", res.data)

    def test_retrieve_user_unauthorized(self):
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.email = "test@example.com"
        self.name = "test"
        self.password = "Aa1234567"

        self.update_name = "update test"
        self.update_password = "Update Aa1234567"

        self.repo = repository.UserRepository()

        self.user = create_user(
            email=self.email,
            name=self.name,
            password=self.password,
            repo=self.repo,
        )

        self.login()
        self.headers = {
            "HTTP_AUTHORIZATION": f"{self.token_type} {self.access_token}"
        }

    def login(self):
        payload = dict(email=self.email, password=self.password)
        res = self.client.post(TOKEN_URL, payload)

        self.access_token = res.data["access_token"]
        self.token_type = res.data["token_type"]

    def test_retrieve_profile_success(self):
        res = self.client.get(ME_URL, **self.headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data,
            {
                "id": self.user.id,
                "email": self.email,
                "name": self.name,
            },
        )

    def test_post_me_not_allowed(self):
        res = self.client.post(ME_URL, {}, **self.headers)
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        res = self.client.patch(
            ME_URL,
            {
                "name": self.update_name,
                "password": self.update_password,
            },
            **self.headers,
        )

        self.user.refresh_from_db()

        self.assertEqual(self.user.name, self.update_name)
        self.assertTrue(self.user.check_password(self.update_password))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
