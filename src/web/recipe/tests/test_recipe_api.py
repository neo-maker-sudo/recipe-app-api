import tempfile
import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from PIL import Image

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Tag, Ingredient

from recipe.serializers import (
    RecipeListSerializerOut,
    RecipeDetailSerializerOut,
)
from recipe_menu.adapters import repository

RECIPES_URL = reverse("recipe:recipe-list")
TOKEN_URL = reverse("user:token")


def detail_url(recipe_id: int):
    return reverse("recipe:recipe-detail", args=[recipe_id])


def image_upload_url(recipe_id: int):
    return reverse("recipe:recipe-upload-image", args=[recipe_id])


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

        data = RecipeListSerializerOut(
            recipes, many=True, context={"request": res.wsgi_request}
        ).data
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
            res.data,
            RecipeListSerializerOut(
                recipes, many=True, context={"request": res.wsgi_request}
            ).data,
        )

    def test_retrieve_recipe_detail(self):
        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)

        res = self.client.get(url, **self.headers)

        self.assertEqual(
            res.data,
            RecipeDetailSerializerOut(
                recipe, context={"request": res.wsgi_request}
            ).data,
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_recipe(self):
        price = "1.99"
        payload = {
            "title": "Sample Recipe",
            "time_minutes": 10,
            "price": Decimal(price),
            "description": "",
            "link": "",
        }

        res = self.client.post(RECIPES_URL, payload, **self.headers)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data["title"], payload["title"])
        self.assertEqual(res.data["time_minutes"], payload["time_minutes"])
        self.assertEqual(res.data["price"], price)
        self.assertEqual(res.data["description"], payload["description"])
        self.assertEqual(res.data["link"], payload["link"])

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

    def test_create_recipe_with_new_tags(self):
        tags = [{"name": "Hello"}, {"name": "World"}]
        payload = {
            "title": "recipe",
            "time_minutes": 1,
            "price": Decimal("1.00"),
            "description": "",
            "link": "",
            "tags": tags,
        }

        res = self.client.post(
            RECIPES_URL, payload, **self.headers, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), len(tags))

    def test_create_recipe_with_existing_tag(self):
        Tag.objects.create(user=self.user, name="tag1")

        tags = [{"name": "tag1"}, {"name": "tag2"}]
        payload = {
            "title": "recipe",
            "time_minutes": 1,
            "price": Decimal("1.00"),
            "description": "",
            "link": "",
            "tags": tags,
        }

        res = self.client.post(
            RECIPES_URL, payload, **self.headers, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].tags.count(), len(tags))
        self.assertEqual(Recipe.objects.all()[0].tags.count(), 2)

    def test_create_tag_on_update(self):
        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        payload = {"tags": [{"name": "tag3"}]}
        res = self.client.patch(url, payload, **self.headers, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        tag = Tag.objects.get(user=self.user, name="tag3")
        self.assertIn(tag, recipe.tags.all())

    def test_update_recipe_assign_tag(self):
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        recipe = create_recipe(self.user)
        recipe.tags.add(tag1)

        tag2 = Tag.objects.create(user=self.user, name="tag2")
        payload = {"tags": [{"name": "tag2"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, **self.headers, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(tag2, recipe.tags.all())
        self.assertNotIn(tag1, recipe.tags.all())

    def test_clear_recipe_tags(self):
        tag1 = Tag.objects.create(user=self.user, name="tag1")
        recipe = create_recipe(self.user)
        recipe.tags.add(tag1)

        payload = {"tags": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, **self.headers, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.tags.count(), 0)

    def test_create_recipe_with_ingredients(self):
        ingredients = [{"name": "ingre1"}, {"name": "ingre2"}]
        payload = {
            "title": "recipe",
            "time_minutes": 1,
            "price": Decimal("1.00"),
            "description": "",
            "link": "",
            "ingredients": ingredients,
        }

        res = self.client.post(
            RECIPES_URL, payload, **self.headers, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for index, ingredient in enumerate(res.data["ingredients"]):
            self.assertEqual(ingredient["name"], ingredients[index]["name"])

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].ingredients.count(), len(ingredients))

    def test_create_recipe_with_existing_ingredients(self):
        Ingredient.objects.create(user=self.user, name="ingre1")

        ingredients = [{"name": "ingre1"}, {"name": "ingre2"}]
        payload = {
            "title": "recipe",
            "time_minutes": 1,
            "price": Decimal("1.00"),
            "description": "",
            "link": "",
            "ingredients": ingredients,
        }

        res = self.client.post(
            RECIPES_URL, payload, **self.headers, format="json"
        )

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        for index, ingredient in enumerate(res.data["ingredients"]):
            self.assertEqual(ingredient["name"], ingredients[index]["name"])

        recipes = Recipe.objects.filter(user=self.user)
        self.assertEqual(recipes.count(), 1)
        self.assertEqual(recipes[0].ingredients.count(), len(ingredients))
        self.assertEqual(Recipe.objects.all()[0].ingredients.count(), 2)

    def test_create_ingredient_on_update(self):
        recipe = create_recipe(self.user)

        url = detail_url(recipe.id)
        payload = {"ingredients": [{"name": "ingre1"}]}
        res = self.client.patch(url, payload, **self.headers, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        ingredient = Ingredient.objects.get(
            user=self.user, name=payload["ingredients"][0]["name"]
        )
        self.assertIn(ingredient, recipe.ingredients.all())

    def test_update_recipe_assign_ingredient(self):
        ingre1 = Ingredient.objects.create(user=self.user, name="ingre1")
        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingre1)

        ingre2 = Ingredient.objects.create(user=self.user, name="ingre2")
        payload = {"ingredients": [{"name": "ingre2"}]}

        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, **self.headers, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn(ingre2, recipe.ingredients.all())
        self.assertNotIn(ingre1, recipe.ingredients.all())

    def test_clear_recipe_ingredients(self):
        ingre1 = Ingredient.objects.create(user=self.user, name="ingre1")
        recipe = create_recipe(self.user)
        recipe.ingredients.add(ingre1)

        payload = {"ingredients": []}
        url = detail_url(recipe.id)
        res = self.client.patch(url, payload, **self.headers, format="json")

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(recipe.ingredients.count(), 0)


class ImageUploadTests(TestCase):
    def setUp(self):
        self.client = APIClient()

        self.email = "user@example.com"
        self.password = "Aa1234567"
        self.user = get_user_model().objects.create_user(
            self.email,
            self.password,
        )
        self.recipe = create_recipe(user=self.user)

        self.login()
        self.headers = {
            "HTTP_AUTHORIZATION": f"{self.token_type} {self.access_token}"
        }

    def tearDown(self):
        self.recipe.image.delete()

    def login(self):
        payload = dict(email=self.email, password=self.password)
        res = self.client.post(TOKEN_URL, payload)

        self.access_token = res.data["access_token"]
        self.token_type = res.data["token_type"]

    def test_upload_image(self):
        url = image_upload_url(self.recipe.id)

        with tempfile.NamedTemporaryFile(suffix=".jpg") as file:
            img = Image.new("RGB", (10, 10))
            img.save(file, format="JPEG")
            file.seek(0)

            res = self.client.patch(
                url, {"image": file}, **self.headers, format="multipart"
            )

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("image", res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):

        url = image_upload_url(self.recipe.id)

        res = self.client.patch(
            url, {"image": "noimage"}, **self.headers, format="multipart"
        )
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
