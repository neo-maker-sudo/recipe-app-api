from decimal import Decimal

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag, Recipe
from recipe.serializers import TagListSerializerOut


TOKEN_URL = reverse("user:token")
TAGS_URL = reverse("recipe:tag-list")


def detail_url(tag_id: int):
    return reverse("recipe:tag-detail", args=[tag_id])


def create_user(email, password):
    return get_user_model().objects.create_user(email=email, password=password)


class PublicTagsAPITest(TestCase):

    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(TAGS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsApiTests(TestCase):
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

    def login(self):
        payload = dict(email=self.email, password=self.password)
        res = self.client.post(TOKEN_URL, payload)

        self.access_token = res.data["access_token"]
        self.token_type = res.data["token_type"]

    def test_retrieve_tags(self):
        order_by = "-name"

        Tag.objects.create(user=self.user, name="tag1")
        Tag.objects.create(user=self.user, name="tag2")

        res = self.client.get(TAGS_URL, **self.headers)

        tags = Tag.objects.all().order_by(order_by)
        serializer = TagListSerializerOut(tags, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tags_limited_to_user(self):
        Tag.objects.create(user=self.other_user, name="other user tag")

        tag = Tag.objects.create(user=self.user, name="user tag")
        res = self.client.get(TAGS_URL, **self.headers)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]["name"], tag.name)
        self.assertEqual(res.data[0]["id"], tag.id)

    def test_update_tag(self):
        tag = Tag.objects.create(user=self.user, name="Hello")

        url = detail_url(tag.id)
        payload = {"name": "World"}
        res = self.client.patch(url, payload, **self.headers)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

        tag.refresh_from_db()

        self.assertEqual(tag.name, payload["name"])

    def test_delete_tag(self):
        tag = Tag.objects.create(user=self.user, name="Hello")

        url = detail_url(tag.id)
        res = self.client.delete(url, **self.headers)
        self.assertEqual(res.status_code, status.HTTP_204_NO_CONTENT)

        tags = Tag.objects.filter(user=self.user)
        self.assertFalse(tags.exists())

    def test_filter_tags_assigned_to_recipes(self):
        t1 = Tag.objects.create(user=self.user, name="tag1")
        t2 = Tag.objects.create(user=self.user, name="tag2")

        recipe = Recipe.objects.create(
            title="recipe",
            time_minutes=1,
            price=Decimal("1.00"),
            user=self.user,
        )
        recipe.tags.add(t1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1}, **self.headers)

        s1 = TagListSerializerOut(t1)
        s2 = TagListSerializerOut(t2)

        self.assertIn(s1.data, res.data)
        self.assertNotIn(s2.data, res.data)

    def test_filterd_tags_unique(self):
        t1 = Tag.objects.create(user=self.user, name="tag1")
        Tag.objects.create(user=self.user, name="tag2")
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
        r1.tags.add(t1)
        r2.tags.add(t1)

        res = self.client.get(TAGS_URL, {"assigned_only": 1}, **self.headers)
        self.assertEqual(len(res.data), 1)
