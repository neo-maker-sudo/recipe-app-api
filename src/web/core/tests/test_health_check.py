from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient


HEALTH_CHECK_URL = reverse("health-check")


class HealthCheckTests(TestCase):

    def test_health_check(self):
        client = APIClient()

        res = client.get(HEALTH_CHECK_URL)
        self.assertEqual(res.status_code, status.HTTP_200_OK)
