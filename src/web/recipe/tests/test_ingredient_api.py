from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe
from recipe.serializers import IngredientListSerializerOut


TOKEN_URL = reverse("user:token")
INGREDIENTS_URLS = reverse("recipe:ingredient-list")


def detail_url(ingredient_id: int):
    return reverse("recipe:ingredient-detail", args=[ingredient_id])


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

    def test_update_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="ingre1")

        payload = {"name": "ingre2"}
        url = detail_url(ingredient.id)
        res = self.client.patch(url, payload, **self.headers)
        self.assert_200(res.status_code)

        ingredient.refresh_from_db()
        self.assertEqual(ingredient.name, payload["name"])

    def test_delete_ingredient(self):
        ingredient = Ingredient.objects.create(user=self.user, name="ingre1")

        url = detail_url(ingredient.id)
        res = self.client.delete(url, **self.headers)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        ingredients = Ingredient.objects.filter(user=self.user)
        self.assertFalse(ingredients.exists())

    def test_filter_ingredients_assigned_to_recipes(self):
        i1 = Ingredient.objects.create(user=self.user, name="ingre1")
        i2 = Ingredient.objects.create(user=self.user, name="ingre2")

        recipe = Recipe.objects.create(
            title="recipe",
            time_minutes=1,
            price=Decimal("1.00"),
            user=self.user,
        )
        recipe.ingredients.add(i1)

        res = self.client.get(
            INGREDIENTS_URLS, {"assigned_only": 1}, **self.headers
        )

        s1 = IngredientListSerializerOut(i1)
        s2 = IngredientListSerializerOut(i2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filterd_ingredients_unique(self):
        i1 = Ingredient.objects.create(user=self.user, name="ingre1")
        Ingredient.objects.create(user=self.user, name="ingre2")
        r1 = Recipe.objects.create(
            title="recipe1",
            time_minutes=1,
            price=Decimal("1.00"),
            user=self.user,
        )
        r2 = Recipe.objects.create(
            title="recipe2",
            time_minutes=1,
            price=Decimal("1.00"),
            user=self.user,
        )
        r1.ingredients.add(i1)
        r2.ingredients.add(i1)

        res = self.client.get(
            INGREDIENTS_URLS, {"assigned_only": 1}, **self.headers
        )
        self.assertEqual(len(res.data), 1)
