from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe

from recipe.serializers import (
    RecipeListSerializerOut,
    RecipeDetailSerializerOut,
)
from recipe_menu.adapters import repository

RECIPES_URL = reverse("recipe:recipe-list")
TOKEN_URL = reverse("user:token")


def detail_url(recipe_id: int):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def create_recipe(user, **params):
    default = {
        "title": "recipe title",
        "description": "recipe description",
        "time_minutes": 25,
        "price": Decimal("5.25"),
        "link": "https://example.com/recipe.pdf",
    }
    default.update(params)

    recipe = Recipe.objects.create(user=user, **default)
    return recipe


class PublicRecipeAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        order_by = "id"
        res = self.client.get(RECIPES_URL, **{"QUERY_STRING": f"o={order_by}"})
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeAPITests(TestCase):

    def setUp(self):
        self.client = APIClient()

        self.email = "user@example.com"
        self.password = "Aa1234567"
        self.user = get_user_model().objects.create_user(
            self.email,
            self.password,
        )
        self.other_user = get_user_model().objects.create_user(
            "other@example.com",
            "Aa1234567",
        )

        self.login()
        self.headers = {
            "HTTP_AUTHORIZATION": f"{self.token_type} {self.access_token}"
        }

        self.repo = repository.RecipeRepository()

    def login(self):
        payload = dict(email=self.email, password=self.password)
        res = self.client.post(TOKEN_URL, payload)

        self.access_token = res.data["access_token"]
        self.token_type = res.data["token_type"]

    def test_retrieve_recipes(self):
        order_by = "id"

        create_recipe(self.user)
        create_recipe(self.user)

        res = self.client.get(
            RECIPES_URL, **{"QUERY_STRING": f"o={order_by}"}, **self.headers
        )

        recipes = [
            recipe.to_domain()
            for recipe in Recipe.objects.all().order_by(order_by)
        ]

        data = RecipeListSerializerOut(recipes, many=True).data
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, data)

    def test_recipe_list_limited_to_user(self):
        order_by = "-id"

        create_recipe(self.user)
        create_recipe(self.other_user)

        res = self.client.get(
            RECIPES_URL, **{"QUERY_STRING": f"o={order_by}"}, **self.headers
        )

        recipes = Recipe.objects.filter(user=self.user).order_by(order_by)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(
            res.data, RecipeListSerializerOut(recipes, many=True).data
        )

    def test_retrieve_recipe_detail(self):
        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)

        res = self.client.get(url, **self.headers)

        self.assertEqual(res.data, RecipeDetailSerializerOut(recipe).data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_recipe(self):
        payload = {
            "title": "Sample Recipe",
            "time_minutes": 10,
            "price": Decimal("1.99"),
            "description": "",
            "link": "",
        }

        res = self.client.post(RECIPES_URL, payload, **self.headers)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data, "OK")

    def test_partial_update(self):
        link = "https://www.example.com/recipe.pdf"

        recipe = create_recipe(self.user, link=link)

        url = detail_url(recipe.id)
        payload = {"title": "123"}
        res = self.client.patch(url, payload, **self.headers)

        self.assertEqual(res.status_code, status.HTTP_200_OK)

        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload["title"])
        self.assertEqual(recipe.link, link)
        self.assertEqual(recipe.user, self.user)

    def test_update_user_return_errors(self):
        recipe = create_recipe(self.other_user)

        url = detail_url(recipe.id)
        payload = {"title": "123"}

        res = self.client.patch(url, payload, **self.headers)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)

    def test_delete_recipe(self):
        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        res = self.client.delete(url, **self.headers)

        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        with self.assertRaises(Recipe.DoesNotExist):
            Recipe.objects.get(id=recipe.id)

    def test_delete_other_users_recipe_errors(self):
        recipe = create_recipe(self.other_user)

        url = detail_url(recipe.id)
        res = self.client.delete(url, **self.headers)

        self.assertEqual(res.status_code, status.HTTP_404_NOT_FOUND)
