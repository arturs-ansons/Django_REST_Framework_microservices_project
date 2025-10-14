from unittest.mock import patch
from decimal import Decimal
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth.models import User
import pytest
from ..models import Order

@pytest.mark.django_db
def test_create_order_success_with_mock():
    client = APIClient()
    user = User.objects.create(id=16, username="rambo5")
    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzU5NzU0NTE4LCJpYXQiOjE3NTk3NTQyMTgsImp0aSI6IjA5NTNmYTE4ZWRiODQyNjU5NGU1ZWFiNmI4N2RhZjA5IiwidXNlcl9pZCI6IjE2In0.yAk-7E5zU0P8evhcOSZIu0RUbw7j4QKwNFb7PQHJQ_Y"

    # Patch requests.get to simulate user and product service
    def mock_requests_get(url, headers=None, timeout=None):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self._json = json_data
                self.status_code = status_code

            def json(self):
                return self._json

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise Exception("HTTP error")

        if "user_service" in url:
            return MockResponse({"id": 16, "username": "rambo5"}, 200)
        elif "product_service" in url:
            return MockResponse({"id": 1, "price": "10.50"}, 200)
        else:
            return MockResponse({}, 404)

    with patch("requests.get", side_effect=mock_requests_get):
        response = client.post(
            reverse("order-list"),
            data={"product_id": 1, "quantity": 2},
            format="json",
            HTTP_AUTHORIZATION=token
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert Decimal(str(response.data["total_price"])) == Decimal("21.00")
        order = Order.objects.get(id=response.data["id"])
        assert order.user_id == user.id
