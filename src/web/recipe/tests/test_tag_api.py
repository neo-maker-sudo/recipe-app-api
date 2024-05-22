from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag
from recipe.serializers import TagListSerializerOut


TOKEN_URL = reverse("user:token")
TAGS_URL = reverse("recipe:tag-list")


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
