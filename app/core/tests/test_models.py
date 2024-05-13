from django.test import TestCase
from django.contrib.auth import get_user_model


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
