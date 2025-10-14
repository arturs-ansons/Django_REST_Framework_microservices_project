# tests/test_ship.py
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from apps.shipping.models import Shipment
from unittest.mock import patch
from types import SimpleNamespace

User = get_user_model()

class ShipmentShipTests(TestCase):
    def setUp(self):
        # Create users
        self.admin_user = SimpleNamespace(
            id=1,
            is_authenticated=True,
            is_admin=True
        )
        self.normal_user = SimpleNamespace(
            id=2,
            is_authenticated=True,
            is_admin=False
        )

        # Create API client
        self.client = APIClient()

        # Create shipments
        self.shipment1 = Shipment.objects.create(
            user_id=self.normal_user.id,
            order_id=101,
            status='paid'  # ready to ship
        )
        self.shipment2 = Shipment.objects.create(
            user_id=self.normal_user.id,
            order_id=102,
            status='pending'  # cannot ship yet
        )
    @patch("apps.shipping.views.publish_event")  # mock RMQ publisher
    def test_admin_can_ship(self, mock_publish):
        # Authenticate as admin
        self.client.force_authenticate(user=self.admin_user)

        response = self.client.post(f'/api/shipments/{self.shipment1.id}/ship/')
        self.shipment1.refresh_from_db()

        print("\n[test_admin_can_ship] Response Data:", response.data)
        print("Shipment status after ship:", self.shipment1.status)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.shipment1.status, 'shipped')

    def test_normal_user_cannot_ship(self):
        # Authenticate as normal user
        self.client.force_authenticate(user=self.normal_user)

        response = self.client.post(f'/api/shipments/{self.shipment1.id}/ship/')
        self.shipment1.refresh_from_db()

        print("\n[test_normal_user_cannot_ship] Response Data:", response.data)
        print("Shipment status after attempt:", self.shipment1.status)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(self.shipment1.status, 'paid')
