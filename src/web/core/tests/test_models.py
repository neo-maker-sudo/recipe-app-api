from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model

from core import models


class ModelTests(TestCase):

    def test_create_user_with_email_successfully(self):
        email = "abc@example.com"
        password = "Aa1234567"

        user = get_user_model().objects.create_user(
            email=email, password=password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_email_normalization(self):
        sample_email = [
            ["test1@EXAMPLE.com", "test1@example.com"],
            ["Test2@Example.com", "Test2@example.com"],
            ["tESt3@EXAMPLE.COM", "tESt3@example.com"],
            ["test4@example.COM", "test4@example.com"],
        ]

        for email, expect_email in sample_email:
            user = get_user_model().objects.create_user(
                email=email, password="Aa1234567"
            )
            self.assertEqual(user.email, expect_email)

    def test_new_user_without_email_raises_error(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(
                email="", password="Aa1234567"
            )

    def test_create_superuser(self):

        user = get_user_model().objects.create_superuser(
            email="test1@example.com", password="Aa1234567"
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)

    def test_create_recipe(self):

        user = get_user_model().objects.create_superuser(
            email="test1@example.com", password="Aa1234567"
        )

        recipe = models.Recipe.objects.create(
            user=user,
            title="Sample recipe title",
            time_minutes=5,
            price=Decimal("5.50"),
            description="Sample recipe description",
        )

        self.assertEqual(str(recipe), recipe.title)

    def test_create_tag(self):
        user = get_user_model().objects.create_user(
            email="user@example.com", password="Aa1234567"
        )

        tag_name = "tag1"
        tag = models.Tag.objects.create(user=user, name=tag_name)
        self.assertEqual(str(tag), tag_name)

    def test_create_ingredient(self):
        user = get_user_model().objects.create_user(
            email="user@example.com", password="Aa1234567"
        )
        ingredient_name = "ingredient"
        ingredient = models.Ingredient.objects.create(
            user=user, name=ingredient_name
        )
        self.assertEqual(str(ingredient), ingredient_name)

    @patch("core.models.uuid.uuid4")
    def test_recipe_file_name_uuid(self, mock_uuid):

        uuid = "test-uuid"
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, "example.jpg")

        self.assertEqual(file_path, f"uploads/recipe/{uuid}.jpg")
