from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient
from recipe.serializers import IngredientListSerializerOut


TOKEN_URL = reverse("user:token")
INGREDIENTS_URLS = reverse("recipe:ingredient-list")


def create_user(email, password):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicIngredientAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(INGREDIENTS_URLS)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientAPITests(TestCase):

    def setUp(self):
        self.email = "user@example.com"
        self.other_email = "user1@example.com"
        self.password = "Aa1234567"
        self.user = create_user(self.email, self.password)
        self.other_user = create_user(self.other_email, self.password)
        self.client = APIClient()

        self.login()
        self.headers = {
            "HTTP_AUTHORIZATION": f"{self.token_type} {self.access_token}"
        }

    def assert_200(self, status_code):
        self.assertEqual(status_code, status.HTTP_200_OK)

    def login(self):
        payload = dict(email=self.email, password=self.password)
        res = self.client.post(TOKEN_URL, payload)

        self.access_token = res.data["access_token"]
        self.token_type = res.data["token_type"]

    def test_retrieve_ingredients(self):
        order_by = "-name"

        Ingredient.objects.create(user=self.user, name="ingre1")
        Ingredient.objects.create(user=self.user, name="ingre2")

        res = self.client.get(INGREDIENTS_URLS, **self.headers)
        self.assert_200(res.status_code)

        ingredients = Ingredient.objects.all().order_by(order_by)
        serializer = IngredientListSerializerOut(ingredients, many=True)
        self.assertEqual(res.data, serializer.data)

    def test_ingredients_limited_to_user(self):
        ingredient = Ingredient.objects.create(user=self.user, name="ingre1")
        Ingredient.objects.create(user=self.other_user, name="ingre2")

        res = self.client.get(INGREDIENTS_URLS, **self.headers)
        self.assert_200(res.status_code)

        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], ingredient.name)
        self.assertEqual(res.data[0]["id"], ingredient.id)
